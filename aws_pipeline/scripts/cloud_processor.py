import ollama
import os
from pathlib import Path
from typing import List, Dict, Tuple
import json
from tqdm import tqdm
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, FloatType
from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType

def setup_spark_and_milvus(
    milvus_host: str,
    milvus_port: str,
    milvus_user: str,
    milvus_password: str,
    spark_milvus_jar_path: str
):
    """Setup Spark session and Milvus connection for cloud deployment"""
    
    # Connect to Milvus
    connections.connect(
        host=milvus_host,
        port=milvus_port,
        user=milvus_user,
        password=milvus_password
    )
    
    # Define index parameters
    index_params = {
        "metric_type": "IP",  # Use IP with normalized vectors for cosine similarity
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    
    # Check if collection exists, if not create it
    if "emb" not in utility.list_collections():
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
    
    # Create SparkSession
    spark = SparkSession.builder \
        .appName("Milvus-Cloud-Integration") \
        .config("spark.jars", spark_milvus_jar_path) \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
        
    return spark

def normalize_vector(vector):
    """Normalize vector for cosine similarity"""
    import numpy as np
    norm = np.linalg.norm(vector)
    return (np.array(vector) / norm).tolist() if norm != 0 else vector

def get_document_embedding(file_path: str, ollama_host: str = "http://localhost:11434") -> Tuple[str, List[float], str]:
    """Get document embedding using Ollama"""
    client = ollama.Client(host=ollama_host)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    response = client.embeddings(
        model="snowflake-arctic-embed2",
        prompt=str(content)
    )
    
    doc_id = Path(file_path).stem
    embedding = response["embedding"]
    return doc_id, embedding, content

def process_and_store_embeddings(
    folder_path: str,
    spark: SparkSession,
    milvus_host: str,
    milvus_port: str,
    batch_size: int = 100
):
    """Process documents and store embeddings in cloud Milvus"""
    md_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.md')]
    
    for i in range(0, len(md_files), batch_size):
        md_files_batch = md_files[i:i+batch_size]
    
        embeddings_data = []
        for file_path in tqdm(md_files_batch, desc="Processing files"):
            try:
                doc_id, embedding, content = get_document_embedding(file_path)
                embeddings_data.append((doc_id, content, embedding))
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
        
        if embeddings_data:
            schema = StructType([
                StructField("id", StringType(), False),
                StructField("text", StringType(), True),
                StructField("vec", ArrayType(FloatType()), False)
            ])
            
            df = spark.createDataFrame(embeddings_data, schema)
            
            df.write \
                .mode("append") \
                .option("milvus.host", milvus_host) \
                .option("milvus.port", milvus_port) \
                .option("milvus.timeout", "10") \
                .option("milvus.database.name", "default") \
                .option("milvus.collection.name", "emb") \
                .option("milvus.collection.vectorField", "vec") \
                .option("milvus.collection.vectorDim", str(len(embeddings_data[0][2]))) \
                .option("milvus.collection.primaryKeyField", "id") \
                .format("milvus") \
                .save()

def main():
    # Load environment variables
    milvus_host = os.getenv("MILVUS_HOST", "localhost")
    milvus_port = os.getenv("MILVUS_PORT", "19530")
    milvus_user = os.getenv("MILVUS_USER", "root")
    milvus_password = os.getenv("MILVUS_PASSWORD", "Milvus")
    spark_milvus_jar = os.getenv("SPARK_MILVUS_JAR", "spark-milvus-1.0.0-SNAPSHOT.jar")
    docs_folder = os.getenv("DOCS_FOLDER", "md_docs")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    spark = None
    try:
        # Setup connections
        spark = setup_spark_and_milvus(
            milvus_host=milvus_host,
            milvus_port=milvus_port,
            milvus_user=milvus_user,
            milvus_password=milvus_password,
            spark_milvus_jar_path=spark_milvus_jar
        )
        
        # Process and store embeddings
        process_and_store_embeddings(
            folder_path=docs_folder,
            spark=spark,
            milvus_host=milvus_host,
            milvus_port=milvus_port
        )
        
        print("✅ Processing completed successfully")
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        raise
    
    finally:
        if spark:
            spark.stop()
        connections.disconnect("default")

if __name__ == "__main__":
    main() 