#!/bin/bash
# Emergency workflow disable script
# Sets WORKFLOW_EMERGENCY_STOP flag and stops new workflow executions

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ACTION="${1:-status}"

STOP_FILE="/var/lib/aos/.workflow_emergency_stop"

case "$ACTION" in
    enable|stop)
        echo -e "${RED}[EMERGENCY] Disabling workflow execution${NC}"
        touch "$STOP_FILE"
        echo "$(date -Iseconds) - Emergency stop enabled by $(whoami)" >> "$STOP_FILE"
        export WORKFLOW_EMERGENCY_STOP=true
        echo -e "  Stop file created: $STOP_FILE"
        echo -e "  Environment: WORKFLOW_EMERGENCY_STOP=true"
        echo ""
        echo -e "${YELLOW}NOTE: Restart services to fully apply${NC}"
        ;;
    disable|start)
        echo -e "${GREEN}[RECOVERY] Re-enabling workflow execution${NC}"
        rm -f "$STOP_FILE"
        unset WORKFLOW_EMERGENCY_STOP 2>/dev/null || true
        echo -e "  Stop file removed"
        echo -e "  Environment: WORKFLOW_EMERGENCY_STOP unset"
        ;;
    status)
        echo "Workflow Emergency Stop Status"
        echo "=============================="
        if [ -f "$STOP_FILE" ]; then
            echo -e "  Status: ${RED}STOPPED${NC}"
            echo "  Stop file: $STOP_FILE"
            echo "  Contents:"
            cat "$STOP_FILE" | sed 's/^/    /'
        else
            echo -e "  Status: ${GREEN}RUNNING${NC}"
            echo "  No stop file present"
        fi
        ;;
    *)
        echo "Usage: $0 {enable|disable|status}"
        echo ""
        echo "  enable/stop   - Create emergency stop flag"
        echo "  disable/start - Remove emergency stop flag"
        echo "  status        - Check current status"
        exit 1
        ;;
esac
