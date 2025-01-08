#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check required environment variables
required_vars=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "MILVUS_USER"
    "MILVUS_PASSWORD"
    "MILVUS_BUCKET_NAME"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set"
        exit 1
    fi
done

echo "📦 Installing Milvus on EKS..."

# Add Milvus Helm repository
echo "Adding Milvus Helm repository..."
helm repo add milvus https://milvus-io.github.io/milvus-helm/
helm repo update

# Create namespace
echo "Creating milvus namespace..."
kubectl create namespace milvus --dry-run=client -o yaml | kubectl apply -f -

# Apply storage class
echo "Applying storage class..."
kubectl apply -f ../k8s/storage-class.yaml

# Install Milvus backup operator
echo "Installing Milvus backup operator..."
helm upgrade --install milvus-backup milvus/milvus-backup \
    --namespace milvus \
    --set s3.enabled=true \
    --set s3.accessKey=$AWS_ACCESS_KEY_ID \
    --set s3.secretKey=$AWS_SECRET_ACCESS_KEY \
    --set s3.bucket=$MILVUS_BUCKET_NAME \
    --set s3.endpoint=s3.amazonaws.com

# Install Milvus using Helm
echo "Installing Milvus..."
helm upgrade --install milvus milvus/milvus \
    --namespace milvus \
    -f ../helm/milvus-values.yaml \
    --set externalS3.accessKey=$AWS_ACCESS_KEY_ID \
    --set externalS3.secretKey=$AWS_SECRET_ACCESS_KEY \
    --set externalS3.bucketName=$MILVUS_BUCKET_NAME \
    --set security.credentials.username=$MILVUS_USER \
    --set security.credentials.password=$MILVUS_PASSWORD \
    --set storage.minio.accessKey=$AWS_ACCESS_KEY_ID \
    --set storage.minio.secretKey=$AWS_SECRET_ACCESS_KEY

# Wait for deployment
echo "Waiting for Milvus deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/milvus-proxy -n milvus

# Create default collection using Python script
echo "Creating default collection..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: create-collection
  namespace: milvus
data:
  create_collection.py: |
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
    
    # Connect to Milvus
    connections.connect(
        host='milvus-proxy',
        port='19530',
        user='${MILVUS_USER}',
        password='${MILVUS_PASSWORD}'
    )
    
    # Define fields
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="vec", dtype=DataType.FLOAT_VECTOR, dim=1024)
    ]
    
    # Create collection schema
    schema = CollectionSchema(fields=fields, description="Document embeddings")
    collection = Collection(name="emb", schema=schema)
    
    # Create IVF_FLAT index
    index_params = {
        "metric_type": "IP",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index(field_name="vec", index_params=index_params)
EOF

# Run the Python script in a pod
kubectl run create-collection --namespace milvus \
    --image=python:3.8 \
    --restart=Never \
    --command -- /bin/bash -c \
    "pip install pymilvus && python /scripts/create_collection.py"

echo "✅ Milvus deployment completed successfully!"
echo "🔍 To verify the deployment, run:"
echo "kubectl get pods -n milvus"
echo "To port-forward the Milvus service:"
echo "kubectl port-forward service/milvus-proxy 19530:19530 -n milvus" 