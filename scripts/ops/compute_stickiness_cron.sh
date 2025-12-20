#!/bin/bash
# Compute Stickiness Cron Job
# Runs every 15 minutes to refresh customer segment cache

set -e

API_BASE="${AOS_API_BASE:-http://localhost:8000}"
API_KEY="${AOS_API_KEY:-edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf}"
LOG_FILE="/var/log/aos/compute-stickiness.log"

# Ensure log directory exists
mkdir -p /var/log/aos

log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

log "Starting compute-stickiness job..."

# Run compute-stickiness
RESPONSE=$(curl -s -X POST "$API_BASE/ops/jobs/compute-stickiness" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}" \
    --max-time 60)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    STATUS=$(echo "$BODY" | jq -r '.status // "unknown"')
    MESSAGE=$(echo "$BODY" | jq -r '.message // "no message"')
    log "SUCCESS: status=$STATUS, message=$MESSAGE"
else
    log "ERROR: HTTP $HTTP_CODE - $BODY"
    exit 1
fi

# Also run silent churn detection
log "Running silent churn detection..."

RESPONSE=$(curl -s -X POST "$API_BASE/ops/jobs/detect-silent-churn" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}" \
    --max-time 60)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    STATUS=$(echo "$BODY" | jq -r '.status // "unknown"')
    MESSAGE=$(echo "$BODY" | jq -r '.message // "no message"')
    log "SUCCESS: status=$STATUS, message=$MESSAGE"
else
    log "ERROR: HTTP $HTTP_CODE - $BODY"
    exit 1
fi

log "Compute-stickiness job completed."
