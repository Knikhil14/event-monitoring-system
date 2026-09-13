#!/bin/bash

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <registry-prefix>"
  echo "Example: $0 docker.io/your-user"
  exit 1
fi

REGISTRY="$1"

for service in event-ingestor event-processor event-query-api notification-service dashboard; do
  echo "Setting image for $service to $REGISTRY/$service:latest"
  find infrastructure/kubernetes/deployments -name "*.yaml" -print0 \
    | xargs -0 sed -i "s|image: .*\\/$service:latest|image: $REGISTRY/$service:latest|g; s|image: $service:latest|image: $REGISTRY/$service:latest|g"
done
