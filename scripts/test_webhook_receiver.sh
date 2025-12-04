#!/bin/bash
# Test script for webhook receiver
#
# Usage:
#   ./scripts/test_webhook_receiver.sh [BASE_URL]
#
# Examples:
#   ./scripts/test_webhook_receiver.sh                    # Uses localhost:8081
#   ./scripts/test_webhook_receiver.sh http://staging:80  # Custom URL

set -e

BASE_URL="${1:-http://localhost:8081}"
TOKEN="${WEBHOOK_TOKEN:-aos-staging-token}"

echo "=========================================="
echo "Testing Webhook Receiver at: $BASE_URL"
echo "=========================================="

# Health check
echo -e "\n1. Health Check..."
curl -sf "$BASE_URL/health" | jq .
echo "✓ Health check passed"

# Post a simple webhook
echo -e "\n2. POST simple webhook..."
RESPONSE=$(curl -sf -X POST "$BASE_URL/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: $TOKEN" \
  -d '{"event": "test", "value": 42}')
echo "$RESPONSE" | jq .
WEBHOOK_ID=$(echo "$RESPONSE" | jq -r '.id')
echo "✓ Webhook created with ID: $WEBHOOK_ID"

# Post an Alertmanager-style webhook
echo -e "\n3. POST Alertmanager webhook..."
RESPONSE=$(curl -sf -X POST "$BASE_URL/webhook/alertmanager" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: $TOKEN" \
  -d '[{
    "labels": {
      "alertname": "CostSimV2Disabled",
      "severity": "P1",
      "instance": "aos-test"
    },
    "annotations": {
      "summary": "Test alert"
    },
    "status": "firing"
  }]')
echo "$RESPONSE" | jq .
echo "✓ Alertmanager webhook created"

# List webhooks
echo -e "\n4. List webhooks..."
curl -sf "$BASE_URL/webhooks?limit=5" \
  -H "X-Webhook-Token: $TOKEN" | jq '.webhooks | length'
echo "✓ Listed webhooks"

# Get specific webhook
echo -e "\n5. Get webhook by ID..."
curl -sf "$BASE_URL/webhooks/$WEBHOOK_ID" \
  -H "X-Webhook-Token: $TOKEN" | jq '.id, .path, .body'
echo "✓ Retrieved webhook"

# Get stats
echo -e "\n6. Get stats..."
curl -sf "$BASE_URL/stats" | jq .
echo "✓ Stats retrieved"

# Filter by alertname
echo -e "\n7. Filter by alertname..."
curl -sf "$BASE_URL/webhooks?alertname=CostSimV2Disabled" \
  -H "X-Webhook-Token: $TOKEN" | jq '.total'
echo "✓ Filtered webhooks"

# Get metrics
echo -e "\n8. Get Prometheus metrics..."
curl -sf "$BASE_URL/metrics" | head -10
echo "..."
echo "✓ Metrics endpoint working"

echo -e "\n=========================================="
echo "All tests passed! ✓"
echo "=========================================="
