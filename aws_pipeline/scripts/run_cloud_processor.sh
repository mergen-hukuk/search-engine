#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f ../.env ]; then
    source ../.env
fi

# Check if port-forward is running, if not start it
if ! nc -z localhost 19530 2>/dev/null; then
    echo "Starting port-forward to Milvus..."
    kubectl port-forward service/milvus-proxy 19530:19530 -n milvus &
    sleep 5  # Wait for port-forward to establish
fi

# Install required Python packages if not already installed
pip install -q pymilvus ollama tqdm numpy

# Set additional environment variables
export MILVUS_HOST="localhost"  # Using port-forward
export MILVUS_PORT="19530"
export SPARK_MILVUS_JAR="$(pwd)/spark-milvus-1.0.0-SNAPSHOT.jar"

# Download Spark-Milvus connector if not exists
if [ ! -f "$SPARK_MILVUS_JAR" ]; then
    echo "Downloading Spark-Milvus connector..."
    wget -q https://github.com/zilliztech/spark-milvus/raw/1.0.0-SNAPSHOT/output/spark-milvus-1.0.0-SNAPSHOT.jar
fi

echo "Starting document processing..."
python cloud_processor.py

# Clean up port-forward
pkill -f "kubectl port-forward.*milvus-proxy" || true 