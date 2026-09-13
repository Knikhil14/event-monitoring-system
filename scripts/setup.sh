#!/bin/bash

set -euo pipefail

echo "Event Monitoring System - KodeKloud Playground Setup"
echo "===================================================="
echo
echo "This setup assumes kubectl is already connected to your playground cluster."
echo "Usage: bash scripts/setup.sh <registry-prefix>"
echo "Example: bash scripts/setup.sh docker.io/your-dockerhub-user"
echo
echo "Required images:"
echo "- event-ingestor:latest"
echo "- event-processor:latest"
echo "- event-query-api:latest"
echo "- notification-service:latest"
echo "- dashboard:latest"
echo
if [ "$#" -eq 1 ]; then
  REGISTRY="$1"
  echo "Building and pushing images to $REGISTRY..."
  bash scripts/build-and-push.sh "$REGISTRY"
  bash scripts/set-image-registry.sh "$REGISTRY"
else
  echo "No registry prefix supplied, so existing manifest image names will be used."
fi

echo "Deploying Kubernetes resources..."
bash scripts/deploy.sh
