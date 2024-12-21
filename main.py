from sparknlp.pretrained import PretrainedPipeline
import sparknlp
from sparknlp.annotator import DocumentAssembler, Tokenizer, BertEmbeddings
from pyspark.ml import Pipeline
import os
import sys
import numpy as np


os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# Start Spark session
spark = sparknlp.start(apple_silicon=True)

# Document Assembler
documentAssembler = DocumentAssembler() \
    .setInputCol("text") \
    .setOutputCol("document")

# Tokenizer
tokenizer = Tokenizer() \
    .setInputCols("document") \
    .setOutputCol("token")

# Bert Embeddings
embeddings = BertEmbeddings.pretrained("bert_base_turkish_cased","tr") \
.setInputCols(["document", "token"]) \
.setOutputCol("embeddings")

# Pipeline
pipeline = Pipeline(stages=[documentAssembler, tokenizer, embeddings])

# Input Data
data = spark.createDataFrame([
    ["The cat drinks milk"],
    ["The kitten likes dairy"],
    ["The computer runs fast"]
]).toDF("text")

# Transform
result = pipeline.fit(data).transform(data)

result.show()