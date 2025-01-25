# Milvus-Spark Integration for Document Embeddings

This notebook demonstrates how to integrate Milvus vector database with Apache Spark to process and store document embeddings at scale. The implementation uses the Ollama API for generating embeddings and Milvus for efficient vector similarity search.

## Prerequisites

- Python 3.x
- Apache Spark
- Milvus
- Ollama
- Required Python packages (see `requirements.txt`)
- Environment variables set up (see `.env.example`)

## System Architecture

The system consists of three main components:

1. **Apache Spark**: Handles distributed processing of documents
2. **Ollama**: Generates embeddings using the snowflake-arctic-embed2 model
3. **Milvus**: Stores and indexes the document embeddings for similarity search

## Implementation Details

### 1. Milvus and Spark Setup

```python
def setup_milvus_and_spark():
    # Initializes Milvus server and creates Spark session
    # Sets up collection with appropriate schema and index
```

Key configurations:
- Collection name: "emb"
- Vector dimension: 1024
- Index type: IVF_FLAT
- Metric type: IP (Inner Product)

### 2. Document Processing

```python
def get_document_embedding(file_path):
    # Generates embeddings for individual documents
```

Features:
- Reads markdown documents
- Generates embeddings using Ollama API
- Returns document ID, embedding vector, and content

### 3. Batch Processing

```python
def process_and_store_embeddings(folder_path, spark):
    # Processes documents in batches of 50
```

Benefits:
- Efficient batch processing
- Error handling for individual documents
- Progress tracking with tqdm

## Usage

1. Set up environment variables:
   ```bash
   SPARK_MILVUS_PATH=/path/to/spark-milvus-jar
   ```

2. Prepare markdown documents in the `md_docs` directory

3. Run the notebook cells in sequence

## Output

The system creates a Milvus collection with the following schema:
- `id`: VARCHAR (primary key)
- `text`: VARCHAR
- `vec`: FLOAT_VECTOR (1024 dimensions)

## Error Handling

The implementation includes comprehensive error handling for:
- Missing environment variables
- Document processing failures
- Milvus connection issues
- Spark execution errors

## Performance Considerations

- Batch size of 50 documents for optimal performance
- Vector normalization for consistent similarity scores
- Efficient index parameters for fast similarity search

## Next Steps

1. Tune index parameters for your specific use case
2. Implement similarity search queries
3. Add monitoring and logging
4. Scale the system with larger document collections 