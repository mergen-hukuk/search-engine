import ollama
import os
from pathlib import Path
from typing import List, Dict, Tuple
import json
from tqdm import tqdm
from milvus import default_server
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, FloatType
from pymilvus import connections, utility, Collection

def setup_milvus_and_spark():
    default_server.stop()
    default_server.start()
    
    # Define index parameters
    index_params = {
        "metric_type": "IP",  # Use IP with normalized vectors for cosine similarity
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    
    # Create collection with index
    from pymilvus import Collection, FieldSchema, CollectionSchema, DataType
    
    connections.connect(host='localhost', port=default_server.listen_port)
    
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="vec", dtype=DataType.FLOAT_VECTOR, dim=1024)
    ]
    
    schema = CollectionSchema(fields=fields, description="Document embeddings")
    collection = Collection(name="emb", schema=schema)
    
    # Create index on vector field
    collection.create_index(
        field_name="vec",
        index_params=index_params
    )
    
    spark = SparkSession.builder \
        .appName("Milvus-Spark-Integration") \
        .config("spark.jars", "/Users/emircan/spark-milvus-1.0.0-SNAPSHOT.jar") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
        
    return spark

def normalize_vector(vector):
    import numpy as np
    norm = np.linalg.norm(vector)
    return (np.array(vector) / norm).tolist() if norm != 0 else vector

def get_document_embedding(file_path: str) -> Tuple[str, List[float], str]:
    client = ollama.Client()
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    response = client.embeddings(
        model="snowflake-arctic-embed2",
        prompt=str(content)
    )
    
    doc_id = Path(file_path).stem
    embedding = response["embedding"]
    # embedding = normalize_vector(response["embedding"])  # Normalize the embedding
    return doc_id, embedding, content

def process_and_store_embeddings(folder_path: str, spark: SparkSession):
    md_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.md')]
    
    for i in range(0, len(md_files), 100):
        md_files_batch = md_files[i:i+100]
    
        embeddings_data = []
        for file_path in tqdm(md_files_batch, desc="Processing files"):
            try:
                doc_id, embedding, content = get_document_embedding(file_path)
                embeddings_data.append((doc_id, content, embedding))
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
        
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("text", StringType(), True),
            StructField("vec", ArrayType(FloatType()), False)
        ])
        
        df = spark.createDataFrame(embeddings_data, schema)
        
        df.write \
            .mode("append") \
            .option("milvus.host", "localhost") \
            .option("milvus.port", default_server.listen_port) \
            .option("milvus.timeout", "5") \
            .option("milvus.database.name", "default") \
            .option("milvus.collection.name", "emb") \
            .option("milvus.collection.vectorField", "vec") \
            .option("milvus.collection.vectorDim", str(len(embeddings_data[0][2]))) \
            .option("milvus.collection.primaryKeyField", "id") \
            .format("milvus") \
            .save()

def main():
    spark = None
    try:
        spark = setup_milvus_and_spark()
        process_and_store_embeddings("md_docs", spark)
        print("Processing completed successfully")
    finally:
        if spark:
            spark.stop()
        default_server.stop()

if __name__ == "__main__":
    main()
