from markitdown import MarkItDown
import tempfile
import json
import openai
from openai import OpenAI
from sparknlp.pretrained import PretrainedPipeline
import sparknlp
from sparknlp.annotator import DocumentAssembler, Tokenizer, BertEmbeddings
from pyspark.ml import Pipeline
import os
import sys
import numpy as np

# read as json and then convert to temp html file using tempfile
with open('sample_data/100002100.json', 'r') as file:
    data = json.load(file)

with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
    temp_file.write(data['data'].encode('utf-8'))
    temp_file_path = temp_file.name

md = MarkItDown()
md_result = md.convert(temp_file_path)
print(md_result.text_content)


client = OpenAI()


chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant that summarizes the text.",
        },
        {
            "role": "user",
            "content": md_result.text_content,
        }
    ],
    model="gpt-4o-mini",
)

summary = chat_completion.choices[0].message.content
print("########################## SUMMARY ##########################")
print(summary)
print("############################################################")


# alakasız bir yazı üret

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "bir paragraflık doğa ile alakalı bir yazı üret.",
        }
    ],
    model="gpt-4o-mini",
)
other = chat_completion.choices[0].message.content




os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# Start Spark session
spark = sparknlp.start(apple_silicon=True)

documentAssembler = DocumentAssembler() \
      .setInputCol("text") \
      .setOutputCol("document")
    
tokenizer = Tokenizer() \
      .setInputCols("document") \
      .setOutputCol("token")

embeddings = BertEmbeddings.pretrained("berturk_legal","tr") \
      .setInputCols(["document", "token"]) \
      .setOutputCol("embeddings")    
        
pipeline = Pipeline().setStages([documentAssembler, tokenizer, embeddings])


# get the embeddings of the summary and other using pipeline
data = spark.createDataFrame([
    [md_result.text_content],
    [summary],
    [other],
]).toDF("text")

emb_pipeline = Pipeline().setStages([documentAssembler, tokenizer, embeddings])
emb_pipelineModel = emb_pipeline.fit(data)
emb_data = emb_pipelineModel.transform(data)

# convert to pandas
df_pandas = emb_data.toPandas()



# a column that takes the average of the embeddings
df_pandas['average_embedding'] = df_pandas['embeddings'].apply(lambda embeddings: np.mean([embeddings[i]['embeddings'] for i in range(len(embeddings))], axis=0))
print("########################## AVERAGE EMBEDDING ##########################")
print(df_pandas['average_embedding'])
print("############################################################")

average_embedding_np = np.array(df_pandas['average_embedding'])

print("########################## AVERAGE EMBEDDING NPY ##########################")
print(average_embedding_np)
print("############################################################")

# compare the cosine similarity of the docume with the summary
cosine_similarity = np.dot(average_embedding_np[0], average_embedding_np[1]) / (np.linalg.norm(average_embedding_np[0]) * np.linalg.norm(average_embedding_np[1]))

print(f"Cosine similarity between document and summary: {cosine_similarity}")

# compare the cosine similarity of the document with the other
cosine_similarity_summary_other = np.dot(average_embedding_np[0], average_embedding_np[2]) / (np.linalg.norm(average_embedding_np[0]) * np.linalg.norm(average_embedding_np[2]))

print(f"Cosine similarity between document and other: {cosine_similarity_summary_other}")

