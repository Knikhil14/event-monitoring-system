#!/bin/bash

# Kubernetes Deployment Script

set -e  # Exit on error

echo "Starting Kubernetes deployment..."

# Apply namespace
kubectl apply -f infrastructure/kubernetes/namespaces/

# Create secrets
kubectl create secret generic db-secret \
  --namespace event-monitoring \
  --from-literal=username=postgres \
  --from-literal=password=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply config maps
kubectl apply -f infrastructure/kubernetes/configmaps/

# Deploy databases
kubectl apply -f infrastructure/kubernetes/deployments/postgresql-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/deployments/redis-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/rabbitmq-deployment.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=event-db-postgresql \
  --namespace event-monitoring --timeout=300s

# Initialize database schema
kubectl run db-init --rm -it \
  --namespace event-monitoring \
  --image=postgres:14-alpine \
  --restart=Never \
  --env="PGPASSWORD=\$(kubectl get secret db-secret -n event-monitoring -o jsonpath='{.data.password}' | base64 --decode)" \
  --command -- psql -h event-db-postgresql -U postgres -d eventdb -c "
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    metadata JSONB,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processed_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    metadata JSONB,
    original_timestamp TIMESTAMP NOT NULL,
    processed_timestamp TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_severity ON events(severity);
CREATE INDEX idx_processed_events_status ON processed_events(status);
"

# Deploy applications
kubectl apply -f infrastructure/kubernetes/deployments/event-ingestor-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/event-processor-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/dashboard-deployment.yaml

# Deploy monitoring stack
kubectl apply -f monitoring/prometheus/
kubectl apply -f monitoring/grafana/

# Deploy ingress
kubectl apply -f infrastructure/kubernetes/ingress/

echo "Deployment completed!"
echo "Checking pod status..."
kubectl get pods -n event-monitoring

echo -e "\nAccess URLs:"
echo "Dashboard: http://events.yourdomain.com"
echo "API: http://events.yourdomain.com/api/events"
echo "Grafana: http://grafana.events.yourdomain.com"