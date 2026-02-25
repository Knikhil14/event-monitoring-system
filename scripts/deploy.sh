#!/bin/bash

# Kubernetes Deployment Script

set -e  # Exit on error

echo "Starting Kubernetes deployment..."

# Apply namespace
kubectl apply -f infrastructure/kubernetes/namespaces/

# Create secrets (using command line for better security)
echo "Creating secrets..."
kubectl create secret generic db-secret \
  --namespace event-monitoring \
  --from-literal=username=postgres \
  --from-literal=password=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Create redis secret
kubectl create secret generic redis-secret \
  --namespace event-monitoring \
  --from-literal=password=$(openssl rand -base64 16) \
  --dry-run=client -o yaml | kubectl apply -f -

# Create rabbitmq secret
kubectl create secret generic rabbitmq-secret \
  --namespace event-monitoring \
  --from-literal=username=admin \
  --from-literal=password=$(openssl rand -base64 16) \
  --from-literal=erlang-cookie=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Create dashboard secret
kubectl create secret generic dashboard-secret \
  --namespace event-monitoring \
  --from-literal=secret-key=$(openssl rand -base64 32) \
  --from-literal=session-key=$(openssl rand -base64 32) \
  --from-literal=csrf-key=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply config maps
echo "Applying ConfigMaps..."
kubectl apply -f infrastructure/kubernetes/configmaps/

# Deploy databases
echo "Deploying databases..."
kubectl apply -f infrastructure/kubernetes/deployments/postgresql-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/deployments/redis-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/rabbitmq-deployment.yaml

# Wait for databases to be ready
echo "Waiting for PostgreSQL..."
kubectl wait --for=condition=ready pod -l app=event-db-postgresql \
  --namespace event-monitoring --timeout=300s || true

echo "Waiting for Redis..."
kubectl wait --for=condition=ready pod -l app=redis,role=master \
  --namespace event-monitoring --timeout=300s || true

echo "Waiting for RabbitMQ..."
kubectl wait --for=condition=ready pod -l app=rabbitmq \
  --namespace event-monitoring --timeout=300s || true

# Initialize database schema
echo "Initializing database schema..."
kubectl run db-init --rm -it \
  --namespace event-monitoring \
  --image=postgres:14-alpine \
  --restart=Never \
  --env="PGPASSWORD=$(kubectl get secret db-secret -n event-monitoring -o jsonpath='{.data.password}' | base64 --decode)" \
  --command -- psql -h event-db-postgresql -U postgres -d postgres -c "
CREATE DATABASE eventdb;
\c eventdb;
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
" || echo "Database initialization may have partially failed, continuing..."

# Deploy applications
echo "Deploying applications..."
kubectl apply -f infrastructure/kubernetes/deployments/event-ingestor-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/event-processor-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/dashboard-deployment.yaml

# Wait for applications
echo "Waiting for applications..."
kubectl wait --for=condition=ready pod -l app=event-ingestor \
  --namespace event-monitoring --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=event-processor \
  --namespace event-monitoring --timeout=300s || true

# Deploy monitoring stack (if exists)
echo "Deploying monitoring..."
if [ -d "monitoring/prometheus" ]; then
  kubectl apply -f monitoring/prometheus/ 2>/dev/null || echo "Prometheus manifests not found"
fi
if [ -d "monitoring/grafana" ]; then
  kubectl apply -f monitoring/grafana/ 2>/dev/null || echo "Grafana manifests not found"
fi

# Deploy ingress
echo "Deploying ingress..."
kubectl apply -f infrastructure/kubernetes/ingress/ 2>/dev/null || echo "Ingress manifests not found"

echo "Deployment completed!"
echo "Checking pod status..."
kubectl get pods -n event-monitoring

echo -e "\nServices:"
kubectl get svc -n event-monitoring

echo -e "\nTo access RabbitMQ Management UI:"
echo "kubectl port-forward -n event-monitoring svc/event-rabbitmq 15672:15672"
echo "Username: admin"
echo "Password: Get it with: kubectl get secret rabbitmq-secret -n event-monitoring -o jsonpath='{.data.password}' | base64 --decode"

echo -e "\nTo test Redis:"
echo "kubectl run redis-test --rm -it --restart=Never --namespace event-monitoring --image=redis:7-alpine -- redis-cli -h event-redis ping"