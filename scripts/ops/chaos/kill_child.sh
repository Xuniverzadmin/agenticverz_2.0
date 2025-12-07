#!/usr/bin/env bash
# =============================================================================
# Chaos Experiment: Kill Backend Child Process
# =============================================================================
# Simulates a process crash. Backend should auto-recover.
# Usage: ./kill_child.sh
# =============================================================================

set -uo pipefail

echo "=== Chaos: Kill Backend Child Process ==="
echo "Timestamp: $(date -Iseconds)"
echo ""

# Get backend container
CONTAINER="nova_agent_manager"

# Check container exists
if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER"; then
    echo "[ERROR] Container $CONTAINER not running"
    exit 1
fi

# Get current health
echo "[INFO] Pre-chaos health check..."
if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "[OK] Backend healthy before chaos"
else
    echo "[WARN] Backend not healthy - aborting chaos"
    exit 1
fi

# Record metrics before
AUDIT_BEFORE=$(curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="success"}' | awk '{print $NF}')
echo "[INFO] RBAC audit writes before: $AUDIT_BEFORE"

# Kill a uvicorn worker (not the main process)
echo "[INFO] Sending SIGTERM to uvicorn worker..."
docker exec "$CONTAINER" pkill -f "uvicorn.*worker" 2>/dev/null || true

# Wait for recovery
echo "[INFO] Waiting 10s for recovery..."
sleep 10

# Check recovery
echo "[INFO] Post-chaos health check..."
RECOVERED=false
for i in {1..6}; do
    if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
        RECOVERED=true
        break
    fi
    echo "[INFO] Attempt $i/6 - waiting..."
    sleep 5
done

if $RECOVERED; then
    echo "[OK] Backend recovered successfully"

    # Check metrics
    AUDIT_AFTER=$(curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="success"}' | awk '{print $NF}')
    echo "[INFO] RBAC audit writes after: $AUDIT_AFTER"

    # Trigger a test request
    curl -sf -H "X-Machine-Token: ${MACHINE_SECRET_TOKEN:-}" \
        http://127.0.0.1:8000/api/v1/rbac/info > /dev/null 2>&1 || true

    echo ""
    echo "[PASS] Chaos experiment completed - system recovered"
    exit 0
else
    echo "[FAIL] Backend did not recover within 30 seconds"
    echo "[INFO] Check: docker logs $CONTAINER --tail 50"
    exit 1
fi
