#!/bin/bash

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <registry-prefix>"
  echo "Example: $0 docker.io/kollurinikhil"
  exit 1
fi

REGISTRY="$1"
SERVICES=(
  event-ingestor
  event-processor
  event-query-api
  notification-service
  dashboard
)

for service in "${SERVICES[@]}"; do
  echo "Building $REGISTRY/$service:latest"
  docker build -t "$REGISTRY/$service:latest" "applications/$service"
  docker push "$REGISTRY/$service:latest"
done

echo "Images pushed. Update manifests with:"
echo "./scripts/set-image-registry.sh $REGISTRY"
