#!/bin/bash

set -euo pipefail

NAMESPACE="event-monitoring"

echo "Starting Kubernetes playground deployment..."

kubectl apply -f infrastructure/kubernetes/namespaces/

echo "Creating application secrets..."
kubectl create secret generic db-secret \
  --namespace "$NAMESPACE" \
  --from-literal=username=postgres \
  --from-literal=password=postgres123 \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic redis-secret \
  --namespace "$NAMESPACE" \
  --from-literal=password=redis123 \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic rabbitmq-secret \
  --namespace "$NAMESPACE" \
  --from-literal=username=admin \
  --from-literal=password=admin123 \
  --from-literal=erlang-cookie=event-monitoring-cookie \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic dashboard-secret \
  --namespace "$NAMESPACE" \
  --from-literal=secret-key=dashboard-secret-key \
  --from-literal=session-key=dashboard-session-key \
  --from-literal=csrf-key=dashboard-csrf-key \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Applying ConfigMaps..."
kubectl apply -f infrastructure/kubernetes/configmaps/

echo "Deploying stateful services..."
kubectl apply -f infrastructure/kubernetes/deployments/postgresql-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/deployments/redis-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/rabbitmq-deployment.yaml

echo "Waiting for stateful services..."
kubectl rollout status statefulset/event-db-postgresql -n "$NAMESPACE" --timeout=300s
kubectl rollout status statefulset/event-redis-master -n "$NAMESPACE" --timeout=300s
kubectl rollout status statefulset/event-rabbitmq -n "$NAMESPACE" --timeout=300s

echo "Initializing database schema..."
kubectl delete job db-init -n "$NAMESPACE" --ignore-not-found=true
kubectl apply -f infrastructure/kubernetes/jobs/db-init-job.yaml
kubectl wait --for=condition=complete job/db-init -n "$NAMESPACE" --timeout=180s

echo "Deploying application microservices..."
kubectl apply -f infrastructure/kubernetes/deployments/event-ingestor-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/event-processor-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/event-query-api-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/notification-service-deployment.yaml
kubectl apply -f infrastructure/kubernetes/deployments/dashboard-deployment.yaml

echo "Waiting for application rollouts..."
kubectl rollout status deployment/event-ingestor -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/event-processor -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/event-query-api -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/notification-service -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/dashboard -n "$NAMESPACE" --timeout=300s

echo "Applying optional ingress if an ingress controller exists..."
kubectl apply -f infrastructure/kubernetes/ingress/ || true

echo
echo "Deployment completed."
kubectl get pods,svc -n "$NAMESPACE"

echo
echo "Playground access options:"
echo "Dashboard NodePort: http://<node-ip>:30080"
echo "Ingestor NodePort:  http://<node-ip>:30081/api/events"
echo "Dashboard port-forward: kubectl port-forward -n $NAMESPACE svc/dashboard-service 8080:80"
echo "API port-forward:       kubectl port-forward -n $NAMESPACE svc/event-ingestor-service 8081:80"
