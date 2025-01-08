import sparknlp
from sparknlp.base import DocumentAssembler
from sparknlp.annotator import SentenceDetector, Tokenizer, YakeKeywordExtraction, Stemmer
from pyspark.ml import Pipeline
from markitdown import MarkItDown
import json
import glob
import tempfile

# Start Spark NLP session
spark = sparknlp.start()

# Function to extract text using MarkItDown
def extract_text_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
            temp_file.write(data['data'].encode('utf-8'))
            temp_file_path = temp_file.name
        
        # Convert using MarkItDown
        md = MarkItDown()
        md_result = md.convert(temp_file_path)
        return md_result.text_content

# Read all JSON files from sample_data directory
json_files = glob.glob('sample_data/*.json')
texts = [extract_text_from_json(file) for file in json_files]
print(texts)
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
    .setMinNGrams(1) \
    .setMaxNGrams(3) \
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
