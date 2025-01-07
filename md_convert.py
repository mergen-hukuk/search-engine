from pyspark.sql import SparkSession
from markitdown import MarkItDown
import tempfile
import os
import json

# Initialize SparkSession
spark = SparkSession.builder \
    .appName("Batch HTML to Markdown Conversion") \
    .getOrCreate()

# Function to process each file
def process_file(file_path):
    try:
        # Read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Write the HTML content to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
            temp_file.write(data['data'].encode('utf-8'))
            temp_file_path = temp_file.name
        
        # Convert HTML to Markdown
        md = MarkItDown()
        md_result = md.convert(temp_file_path)
        
        # Clean up temporary file
        os.remove(temp_file_path)
        
        return {"file": file_path, "markdown": md_result.text_content}
    except Exception as e:
        return {"file": file_path, "error": str(e)}

# Define the folder containing the JSON files
sample_data_folder = "docs"

# Get the list of files in the folder
file_paths = [os.path.join(sample_data_folder, file) for file in os.listdir(sample_data_folder) if file.endswith(".json")]

# Parallelize file paths
file_rdd = spark.sparkContext.parallelize(file_paths)

# Process each file
results_rdd = file_rdd.map(process_file)

# Collect results
results = results_rdd.collect()

# Print results
for result in results:
    if "error" in result:
        print(f"Error processing {result['file']}: {result['error']}")
    else:
        print(f"File: {result['file']}\nMarkdown:\n{result['markdown']}\n")

# Stop SparkSession
spark.stop()
