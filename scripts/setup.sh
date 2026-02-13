#!/bin/bash

# Complete Setup Script for Event Monitoring System

set -e

echo "Starting Event Monitoring System Setup..."
echo "=========================================="

# Step 1: Clone repository
echo "Cloning repository..."
git clone https://github.com/Knikhil14/event-monitoring-system.git
cd event-monitoring-system

# Step 2: Setup AWS credentials
echo "Setting up AWS credentials..."
aws configure

# Step 3: Initialize and apply Terraform
echo "Deploying AWS infrastructure..."
cd infrastructure/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Get outputs
EKS_CLUSTER_NAME=$(terraform output -raw eks_cluster_name)
AWS_REGION=$(terraform output -raw aws_region)

# Step 4: Configure kubectl for EKS
echo "Configuring kubectl..."
aws eks update-kubeconfig \
  --region $AWS_REGION \
  --name $EKS_CLUSTER_NAME

# Step 5: Setup Kubernetes
echo "Setting up Kubernetes..."
cd ../kubernetes
kubectl apply -f namespaces/
kubectl apply -f configmaps/

# Step 6: Build and push Docker images
echo "Building Docker images..."
cd ../../applications

for app in event-ingestor event-processor dashboard; do
  echo "Building $app..."
  docker build -t $app:latest $app/
  # Tag and push to your registry
  # docker tag $app:latest your-registry.io/$app:latest
  # docker push your-registry.io/$app:latest
done

# Step 7: Deploy to Kubernetes
echo "Deploying applications..."
cd ../scripts
chmod +x deploy.sh
./deploy.sh

# Step 8: Setup monitoring
echo "Setting up monitoring..."
cd ../monitoring
kubectl apply -f prometheus/
kubectl apply -f grafana/

# Step 9: Get access URLs
echo "Getting access URLs..."
INGRESS_HOST=$(kubectl get ingress event-monitoring-ingress \
  -n event-monitoring \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo -e "\n Setup Complete!"
echo "=================="
echo "Access URLs:"
echo "• Dashboard: http://$INGRESS_HOST"
echo "• API Endpoint: http://$INGRESS_HOST/api/events"
echo "• Grafana: http://$INGRESS_HOST/grafana"
echo -e "\nTo send test events:"
echo "curl -X POST http://$INGRESS_HOST/api/events \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"event_type\":\"test\",\"source\":\"cli\",\"severity\":\"info\",\"message\":\"System test\"}'"