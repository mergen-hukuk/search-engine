# AWS Pipeline for Vector Search

This guide helps you deploy a scalable vector search pipeline on AWS using EKS and Milvus. Based on the official Milvus documentation, this setup enables:

- Efficient batch loading of vector data into Milvus
- Data movement between Milvus and other storage systems
- Vector data analysis using Spark MLlib and AI tools
- High-availability cluster deployment

## Directory Structure

```
aws_pipeline/
├── k8s/                    # Kubernetes manifests
├── helm/                   # Helm values for Milvus
├── scripts/               # Deployment and utility scripts
│   ├── cloud_processor.py  # Cloud version of document processor
│   ├── deploy_milvus.sh   # Milvus deployment script
│   ├── setup_monitoring.sh # Monitoring setup script
│   └── run_cloud_processor.sh # Runner for cloud processing
└── terraform/             # Infrastructure as Code
```

## Prerequisites

Before you begin, ensure you have:

1. **Apache Spark** (version >= 3.3.0):
   ```bash
   # Download Spark
   wget https://archive.apache.org/dist/spark/spark-3.3.0/spark-3.3.0-bin-hadoop3.tgz
   tar -xzf spark-3.3.0-bin-hadoop3.tgz
   mv spark-3.3.0-bin-hadoop3 /usr/local/spark
   ```

2. **AWS CLI and other tools**:
   ```bash
   # macOS (using Homebrew)
   brew install awscli kubectl helm terraform
   
   # Configure AWS
   aws configure
   ```

3. **Python Dependencies**:
   ```bash
   pip install pymilvus ollama tqdm numpy
   ```

## Deployment Guide

### 1. Environment Setup

Create a `.env` file with required configurations:

```bash
# AWS Configuration
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"

# Milvus Configuration
export MILVUS_USER="your-milvus-username"
export MILVUS_PASSWORD="your-secure-password"
export MILVUS_BUCKET_NAME="your-unique-bucket-name"

# Document Processing Configuration
export DOCS_FOLDER="path/to/your/md_docs"  # Folder containing markdown files
export OLLAMA_HOST="http://localhost:11434"  # Ollama API endpoint
```

### 2. Infrastructure Deployment

Deploy the AWS infrastructure:
```bash
cd terraform
terraform init && terraform apply
```

### 3. Milvus Deployment

Deploy Milvus with high availability:
```bash
cd ../scripts
./deploy_milvus.sh
```

### 4. Document Processing

The cloud processor supports two main workflows:

1. **Direct Processing to Cloud**:
   ```bash
   cd scripts
   ./run_cloud_processor.sh
   ```
   This will:
   - Set up port-forwarding to Milvus
   - Process documents using Ollama
   - Store embeddings in cloud Milvus
   - Clean up connections when done

2. **Custom Processing Pipeline**:
   ```python
   from scripts.cloud_processor import setup_spark_and_milvus, process_and_store_embeddings
   
   # Setup connections
   spark = setup_spark_and_milvus(
       milvus_host="your-milvus-host",
       milvus_port="19530",
       milvus_user="your-user",
       milvus_password="your-password",
       spark_milvus_jar_path="path/to/spark-milvus.jar"
   )
   
   # Process documents
   process_and_store_embeddings(
       folder_path="your/docs/folder",
       spark=spark,
       milvus_host="your-milvus-host",
       milvus_port="19530"
   )
   ```

### 5. Monitoring Setup

Deploy Prometheus and Grafana:
```bash
./setup_monitoring.sh
```

## Features & Concepts

### Document Processing Features

1. **Batch Processing**:
   - Processes documents in configurable batches
   - Automatic error handling and recovery
   - Progress tracking with tqdm

2. **Vector Operations**:
   - Automatic vector normalization
   - Cosine similarity support (IP metric type)
   - Configurable vector dimensions

3. **Cloud Integration**:
   - Automatic port-forwarding
   - Connection management
   - Proper cleanup

### Storage Options

1. **Standard Storage** (gp3):
   - Suitable for general workloads
   - 3000 IOPS baseline
   - 125 MB/s throughput

2. **High-Performance Storage** (io2):
   - For intensive workloads
   - 5000 IOPS
   - 500 MB/s throughput

## Maintenance

### Backup and Restore
```bash
# Create backup
./scripts/backup_milvus.sh

# Monitor backup status
kubectl get backup -n milvus
```

### Scaling

1. **Horizontal Scaling**:
   ```bash
   kubectl scale deployment milvus-proxy -n milvus --replicas=5
   ```

2. **Storage Scaling**:
   ```bash
   kubectl patch pvc milvus-data -n milvus -p '{"spec": {"resources": {"requests": {"storage": "100Gi"}}}}'
   ```

## Troubleshooting

1. **Collection Issues**:
   ```python
   from pymilvus import utility
   utility.list_collections()  # List all collections
   ```

2. **Connection Issues**:
   ```bash
   # Check if port-forward is running
   nc -z localhost 19530
   
   # Check Milvus pods
   kubectl get pods -n milvus
   kubectl describe pod -l app=milvus-proxy -n milvus
   ```

3. **Processing Issues**:
   - Check Ollama server is running
   - Verify document folder permissions
   - Check available memory for Spark

## Need Help?

- [Milvus Documentation](https://milvus.io/docs)
- [Spark-Milvus Connector Guide](https://github.com/zilliztech/spark-milvus)
- [Milvus Discord Community](https://discord.gg/8uyFbECzPX) 