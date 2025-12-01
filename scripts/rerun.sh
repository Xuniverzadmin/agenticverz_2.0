#!/bin/bash
# NOVA Agent Manager - Rerun Failed Runs
# Usage: ./rerun.sh <run_id> [reason]
#
# Environment variables:
#   API_KEY    - Required: API key for authentication
#   API_HOST   - Optional: API host (default: http://127.0.0.1:8000)

set -e

API_KEY="${API_KEY:?Error: API_KEY environment variable is required}"
API_HOST="${API_HOST:-http://127.0.0.1:8000}"

if [ -z "$1" ]; then
    echo "Usage: $0 <run_id> [reason]"
    echo ""
    echo "Environment variables:"
    echo "  API_KEY    - Required: API key for authentication"
    echo "  API_HOST   - Optional: API host (default: http://127.0.0.1:8000)"
    echo ""
    echo "Examples:"
    echo "  API_KEY=your_key $0 abc-123"
    echo "  API_KEY=your_key $0 abc-123 'retry after fix'"
    exit 1
fi

RUN_ID="$1"
REASON="${2:-manual_retry}"

echo "Rerunning run: $RUN_ID"
echo "Reason: $REASON"
echo "API Host: $API_HOST"
echo ""

RESPONSE=$(curl -s -X POST "${API_HOST}/admin/rerun" \
    -H "Content-Type: application/json" \
    -H "X-AOS-Key: ${API_KEY}" \
    -d "{\"run_id\":\"${RUN_ID}\",\"reason\":\"${REASON}\"}")

# Check for error
if echo "$RESPONSE" | grep -q '"detail"'; then
    echo "Error:"
    echo "$RESPONSE" | jq .
    exit 1
fi

echo "Success:"
echo "$RESPONSE" | jq .
