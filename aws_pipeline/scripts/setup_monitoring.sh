#!/bin/bash

# Exit on error
set -e

echo "🔍 Setting up monitoring for Milvus..."

# Add Prometheus Helm repository
echo "Adding Prometheus Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create monitoring namespace
echo "Creating monitoring namespace..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus Stack
echo "Installing Prometheus Stack..."
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --set grafana.enabled=true \
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
    --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false

# Wait for deployment
echo "Waiting for Prometheus and Grafana to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-grafana -n monitoring
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-kube-prometheus-operator -n monitoring

# Get Grafana admin password
echo "Retrieving Grafana admin password..."
GRAFANA_PASSWORD=$(kubectl get secret prometheus-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 --decode)

echo "✅ Monitoring setup completed successfully!"
echo "🔐 Grafana admin password: $GRAFANA_PASSWORD"
echo "To access Grafana dashboard:"
echo "kubectl port-forward service/prometheus-grafana 3000:80 -n monitoring"
echo "Then visit: http://localhost:3000"
echo "Username: admin"
echo "Password: $GRAFANA_PASSWORD"

# Import Milvus dashboard
echo "Importing Milvus dashboard..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: milvus-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "true"
data:
  milvus-dashboard.json: |
    {
      "annotations": {
        "list": []
      },
      "editable": true,
      "fiscalYearStartMonth": 0,
      "graphTooltip": 0,
      "links": [],
      "liveNow": false,
      "panels": [],
      "refresh": "",
      "schemaVersion": 38,
      "style": "dark",
      "tags": [],
      "templating": {
        "list": []
      },
      "time": {
        "from": "now-6h",
        "to": "now"
      },
      "timepicker": {},
      "timezone": "",
      "title": "Milvus Dashboard",
      "version": 0,
      "weekStart": ""
    }
EOF

echo "✨ Milvus dashboard has been imported to Grafana" 