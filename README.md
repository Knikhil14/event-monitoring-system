# Event Monitoring System

A Kubernetes-focused microservices project for practicing DevOps, CI/CD, Python services, observability, and troubleshooting.

## Architecture

```text
Client or test script
  |
  v
event-ingestor
  |
  v
RabbitMQ event_queue
  |
  v
event-processor ---> PostgreSQL
  |
  v
RabbitMQ notification_queue ---> notification-service

dashboard ---> event-query-api ---> PostgreSQL

Prometheus scrapes service metrics.
Grafana visualizes service health and event metrics.
```

## Microservices

- `event-ingestor`: Flask API that receives events on `POST /api/events`.
- `event-processor`: FastAPI service with a background RabbitMQ consumer.
- `event-query-api`: FastAPI read API for recent events and stats.
- `notification-service`: Worker that simulates alert notifications for high-severity events.
- `dashboard`: Flask dashboard for recent processed events.

## Kubernetes Objects Practiced

- Namespace
- Deployments
- StatefulSets
- Services
- NodePort Services
- ConfigMaps
- Secrets
- PersistentVolumeClaims
- Probes
- HorizontalPodAutoscalers
- PodDisruptionBudgets
- Ingress
- Job

## KodeKloud Playground Flow

1. Confirm Kubernetes access:

```bash
kubectl get nodes
```

2. Build and push images to a registry your playground cluster can pull, then deploy:

```bash
docker login
bash scripts/setup.sh docker.io/your-dockerhub-user
```

3. Or run the build and deploy steps separately:

```bash
bash scripts/build-and-push.sh docker.io/your-dockerhub-user
bash scripts/set-image-registry.sh docker.io/your-dockerhub-user
bash scripts/deploy.sh
```

4. Port-forward the ingestor API:

```bash
kubectl port-forward -n event-monitoring svc/event-ingestor-service 8081:80
```

5. Send test events from another terminal:

```bash
bash scripts/test-events.sh
```

6. Port-forward the dashboard:

```bash
kubectl port-forward -n event-monitoring svc/dashboard-service 8080:80
```

Open:

```text
http://localhost:8080
```

## Useful Troubleshooting Commands

```bash
kubectl get pods -n event-monitoring
kubectl get svc -n event-monitoring
kubectl logs -n event-monitoring deployment/event-ingestor
kubectl logs -n event-monitoring deployment/event-processor
kubectl logs -n event-monitoring deployment/event-query-api
kubectl logs -n event-monitoring deployment/notification-service
kubectl describe pod -n event-monitoring <pod-name>
kubectl exec -n event-monitoring -it statefulset/event-rabbitmq -- rabbitmqctl list_queues
```

## Interview Story

This project demonstrates an end-to-end DevOps workflow:

- Built Python microservices with queue-based async processing.
- Containerized each service with Docker.
- Deployed stateful and stateless workloads on Kubernetes.
- Used ConfigMaps and Secrets for runtime configuration.
- Added readiness/liveness probes and resource limits.
- Exposed services through NodePort, port-forward, and optional Ingress.
- Added Prometheus metrics endpoints for observability.
- Created Jenkins CI/CD pipeline for image build, push, deploy, and rollback.

## Next Production Phase

After the playground version works, the same app can be productionized on AWS:

- EKS managed node groups
- ECR image registry
- RDS PostgreSQL
- ElastiCache Redis
- AWS Load Balancer Controller
- Route 53 DNS
- cert-manager TLS
- Terraform remote state
