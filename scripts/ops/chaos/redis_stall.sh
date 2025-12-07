#!/usr/bin/env bash
# =============================================================================
# Chaos Experiment: Redis Stall
# =============================================================================
# Simulates Redis becoming unresponsive. System should degrade gracefully.
# Usage: ./redis_stall.sh [--duration SECONDS]
# =============================================================================

set -uo pipefail

DURATION=15

# Parse args
for arg in "$@"; do
    case $arg in
        --duration=*)
            DURATION="${arg#*=}"
            ;;
        --duration)
            shift
            DURATION="${1:-15}"
            ;;
    esac
done

echo "=== Chaos: Redis Stall ($DURATION seconds) ==="
echo "Timestamp: $(date -Iseconds)"
echo ""

# Check Redis container
REDIS_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E "redis|nova_redis" | head -1)

if [[ -z "$REDIS_CONTAINER" ]]; then
    echo "[WARN] No Redis container found - checking if Redis is external..."
    REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
    echo "[INFO] Redis URL: $REDIS_URL"

    # Try to pause Redis via CLI if available
    if command -v redis-cli &> /dev/null; then
        echo "[INFO] Using redis-cli to simulate stall with DEBUG SLEEP..."
        redis-cli -u "$REDIS_URL" DEBUG SLEEP "$DURATION" &
        REDIS_PID=$!
    else
        echo "[SKIP] No Redis container or redis-cli available"
        echo "[INFO] Manual test: Stop Redis for $DURATION seconds, then restart"
        exit 0
    fi
else
    echo "[INFO] Redis container: $REDIS_CONTAINER"

    # Pause the container (freezes all processes)
    echo "[INFO] Pausing Redis container for $DURATION seconds..."
    docker pause "$REDIS_CONTAINER"
fi

# Record pre-stall metrics
AUDIT_BEFORE=$(curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="success"}' | awk '{print $NF}')
MEM_BEFORE=$(curl -s http://127.0.0.1:8000/metrics | grep 'memory_pins_operations_total.*status="success"' | awk '{sum+=$NF} END {print sum+0}')

echo "[INFO] Pre-stall: audit_writes=$AUDIT_BEFORE, memory_ops=$MEM_BEFORE"

# Wait for stall duration
echo "[INFO] Redis stalled - waiting $DURATION seconds..."
sleep "$DURATION"

# Unpause
if [[ -n "${REDIS_CONTAINER:-}" ]]; then
    echo "[INFO] Unpausing Redis container..."
    docker unpause "$REDIS_CONTAINER"
fi

# Wait for recovery
echo "[INFO] Waiting 5s for system to stabilize..."
sleep 5

# Check system health
echo "[INFO] Post-stall health check..."
if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "[OK] Backend healthy after Redis stall"
else
    echo "[WARN] Backend health check failed"
fi

# Check metrics
AUDIT_AFTER=$(curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="success"}' | awk '{print $NF}')
MEM_AFTER=$(curl -s http://127.0.0.1:8000/metrics | grep 'memory_pins_operations_total.*status="success"' | awk '{sum+=$NF} END {print sum+0}')
MEM_ERRORS=$(curl -s http://127.0.0.1:8000/metrics | grep 'memory_pins_operations_total.*status="error"' | awk '{sum+=$NF} END {print sum+0}')

echo "[INFO] Post-stall: audit_writes=$AUDIT_AFTER, memory_ops=$MEM_AFTER, memory_errors=$MEM_ERRORS"

# Trigger test request
echo "[INFO] Testing memory pin read (should fallback to DB if cache miss)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-Machine-Token: ${MACHINE_SECRET_TOKEN:-}" \
    "http://127.0.0.1:8000/api/v1/memory/pins?tenant_id=chaos-test&limit=1")

if [[ "$STATUS" == "200" ]]; then
    echo "[OK] Memory pin read succeeded (HTTP $STATUS)"
else
    echo "[WARN] Memory pin read returned HTTP $STATUS"
fi

echo ""
if [[ "${MEM_ERRORS:-0}" == "0" ]]; then
    echo "[PASS] Chaos experiment completed - system degraded gracefully"
    exit 0
else
    echo "[WARN] Memory errors detected during stall - review logs"
    exit 1
fi
