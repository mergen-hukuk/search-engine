import sparknlp
from sparknlp.base import DocumentAssembler
from sparknlp.annotator import SentenceDetector, Tokenizer, YakeKeywordExtraction, Stemmer
from pyspark.ml import Pipeline
from markitdown import MarkItDown
import json
import glob
import tempfile
from pathlib import Path

# Start Spark NLP session
spark = sparknlp.start()

# Function to extract text using MarkItDown
def extract_text_from_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Update file reading section
markdown_files = glob.glob('md_docs/*.md')  # Change path to md_docs

# get the first 50 files
markdown_files = markdown_files[:50]
texts = [extract_text_from_markdown(file) for file in markdown_files]
# Create DataFrame with the legal texts
data = spark.createDataFrame([(text,) for text in texts]).toDF("text")

# Define the stages of the pipeline
document_assembler = DocumentAssembler() \
    .setInputCol("text") \
    .setOutputCol("document")

sentence_detector = SentenceDetector() \
    .setInputCols(["document"]) \
    .setOutputCol("sentence")

tokenizer = Tokenizer() \
    .setInputCols(["sentence"]) \
    .setOutputCol("token") \
    .setContextChars(["(", ")", "?", "!", ".", ","])

# Add Stemmer annotator
stemmer = Stemmer() \
    .setInputCols(["token"]) \
    .setOutputCol("stemmed") \
    .setLanguage("turkish")

# Update YAKE to use stemmed tokens
yake = YakeKeywordExtraction() \
    .setInputCols(["stemmed"]) \
    .setOutputCol("keywords") \
    .setMinNGrams(2) \
    .setMaxNGrams(5) \
    .setStopWords(YakeKeywordExtraction.loadDefaultStopWords("turkish")) \
    .setThreshold(0.6) \
    .setNKeywords(20)

# Create the pipeline
pipeline = Pipeline(stages=[
    document_assembler,
    sentence_detector,
    tokenizer,
    stemmer,
    yake
])

# Fit and transform the data
model = pipeline.fit(data)
result = model.transform(data)

# Extract and display the keywords with their scores
keywords_df = result.selectExpr("explode(arrays_zip(keywords.result, keywords.metadata)) as resultTuples") \
    .selectExpr("resultTuples.result as keyword", "resultTuples.metadata.score as score") \
    .dropDuplicates(["keyword"]) \
    .orderBy("score")

keywords_df.show(truncate=False)
