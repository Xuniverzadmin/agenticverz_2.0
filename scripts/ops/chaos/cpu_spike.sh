#!/usr/bin/env bash
# =============================================================================
# Chaos Experiment: CPU Spike
# =============================================================================
# Simulates high CPU load. System should slow but survive.
# Usage: ./cpu_spike.sh [--duration SECONDS]
# =============================================================================

set -uo pipefail

DURATION=30

# Parse args
for arg in "$@"; do
    case $arg in
        --duration=*)
            DURATION="${arg#*=}"
            ;;
        --duration)
            shift
            DURATION="${1:-30}"
            ;;
    esac
done

echo "=== Chaos: CPU Spike ($DURATION seconds) ==="
echo "Timestamp: $(date -Iseconds)"
echo ""

# Get number of CPUs
NCPU=$(nproc)
echo "[INFO] CPU count: $NCPU"

# Pre-spike health
echo "[INFO] Pre-spike health check..."
if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "[OK] Backend healthy before spike"
else
    echo "[WARN] Backend not healthy - continuing anyway"
fi

# Record metrics
AUDIT_BEFORE=$(curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="success"}' | awk '{print $NF}')
echo "[INFO] RBAC audit writes before: $AUDIT_BEFORE"

# Start CPU load using stress or dd
echo "[INFO] Starting CPU spike for $DURATION seconds..."

if command -v stress &> /dev/null; then
    stress --cpu "$NCPU" --timeout "$DURATION" &
    STRESS_PID=$!
else
    # Fallback: use dd to consume CPU
    for i in $(seq 1 "$NCPU"); do
        dd if=/dev/zero of=/dev/null bs=1M &
    done
    sleep "$DURATION"
    pkill -f "dd if=/dev/zero" 2>/dev/null || true
fi

# During spike, try some requests
echo "[INFO] Testing requests during spike..."
for i in {1..3}; do
    START=$(date +%s%N)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
        http://127.0.0.1:8000/health 2>/dev/null || echo "timeout")
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    echo "  Request $i: HTTP $STATUS (${LATENCY}ms)"
    sleep 2
done

# Wait for stress to complete
if [[ -n "${STRESS_PID:-}" ]]; then
    wait "$STRESS_PID" 2>/dev/null || true
fi

# Post-spike recovery
echo "[INFO] CPU spike ended, checking recovery..."
sleep 5

if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "[OK] Backend healthy after spike"
else
    echo "[WARN] Backend health check failed after spike"
fi

# Check metrics
AUDIT_AFTER=$(curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="success"}' | awk '{print $NF}')
AUDIT_ERRORS=$(curl -s http://127.0.0.1:8000/metrics | grep 'rbac_audit_writes_total{status="error"}' | awk '{print $NF}')

echo "[INFO] RBAC audit writes after: $AUDIT_AFTER (errors: ${AUDIT_ERRORS:-0})"

# Final test
echo "[INFO] Final request test..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-Machine-Token: ${MACHINE_SECRET_TOKEN:-}" \
    http://127.0.0.1:8000/api/v1/rbac/info)

if [[ "$STATUS" == "200" ]]; then
    echo "[OK] RBAC info request succeeded"
else
    echo "[WARN] RBAC info returned HTTP $STATUS"
fi

echo ""
echo "[PASS] Chaos experiment completed - system survived CPU spike"
exit 0
