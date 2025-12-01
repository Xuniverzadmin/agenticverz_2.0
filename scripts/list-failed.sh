#!/bin/bash
# NOVA Agent Manager - List Failed Runs
# Usage: ./list-failed.sh [limit]
#
# Environment variables:
#   API_KEY    - Required: API key for authentication
#   API_HOST   - Optional: API host (default: http://127.0.0.1:8000)

set -e

API_KEY="${API_KEY:?Error: API_KEY environment variable is required}"
API_HOST="${API_HOST:-http://127.0.0.1:8000}"
LIMIT="${1:-50}"

echo "Fetching failed runs (limit: $LIMIT)..."
echo ""

curl -s "${API_HOST}/admin/failed-runs?limit=${LIMIT}" \
    -H "X-AOS-Key: ${API_KEY}" | jq .
