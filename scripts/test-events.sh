#!/bin/bash

set -euo pipefail

API_URL="${API_URL:-http://localhost:8081/api/events}"

echo "Sending sample events to $API_URL"

curl -sS -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"application_log","source":"demo-app","severity":"info","message":"Application started"}'
echo

curl -sS -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"security_alert","source":"auth-service","severity":"critical","message":"Multiple failed login attempts"}'
echo

curl -sS -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"performance_metric","source":"checkout-api","severity":"medium","message":"CPU sample","metrics":{"cpu_percent":95,"memory_percent":71}}'
echo
