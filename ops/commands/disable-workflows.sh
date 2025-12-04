#!/bin/bash
# Emergency Workflow Engine Stop
# Usage: ./ops/commands/disable-workflows.sh [--enable]

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [[ "${1:-}" == "--enable" ]]; then
    echo -e "${GREEN}[INFO]${NC} Re-enabling workflow engine..."
    export WORKFLOW_EMERGENCY_STOP=false
    docker compose restart backend worker 2>/dev/null || systemctl restart nova-backend nova-worker 2>/dev/null || echo "Manual restart required"
    echo -e "${GREEN}[INFO]${NC} Workflow engine re-enabled"
else
    echo -e "${RED}[EMERGENCY]${NC} Disabling workflow engine..."
    export WORKFLOW_EMERGENCY_STOP=true
    docker compose restart backend worker 2>/dev/null || systemctl restart nova-backend nova-worker 2>/dev/null || echo "Manual restart required"

    # Also try API endpoint if available
    curl -sf -X POST "${BACKEND_URL}/admin/engine/disable" 2>/dev/null || true

    echo -e "${RED}[EMERGENCY]${NC} Workflow engine DISABLED"
    echo ""
    echo "To re-enable: $0 --enable"
fi
