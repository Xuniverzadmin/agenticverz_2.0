#!/usr/bin/env bash
# =============================================================================
# M7 RBAC/Memory Monitoring Check Script
# =============================================================================
# Run at: 0h, 1h, 6h, 12h, 24h during stabilization period
# Usage: ./m7_monitoring_check.sh [--alert-on-anomaly]
#
# Checks:
# - RBAC decision metrics (allowed/denied ratio)
# - RBAC audit write success/error
# - Memory pin operations
# - Recent audit entries
# - Container health
# =============================================================================

set -uo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"
ALERT_ON_ANOMALY=false
LOG_FILE="/var/log/aos/m7_monitoring_$(date +%Y%m%d).log"

# Parse args
for arg in "$@"; do
    case $arg in
        --alert-on-anomaly)
            ALERT_ON_ANOMALY=true
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Thresholds (note: during testing, denial ratio may be higher due to test traffic)
DENIAL_RATIO_WARN=0.10
DENIAL_RATIO_CRIT=0.50
AUDIT_ERROR_WARN=1
AUDIT_ERROR_CRIT=10

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_ok() { log "${GREEN}[OK]${NC} $1"; }
log_warn() { log "${YELLOW}[WARN]${NC} $1"; }
log_crit() { log "${RED}[CRIT]${NC} $1"; }
log_info() { log "${BLUE}[INFO]${NC} $1"; }

# Helper: Run psql
run_psql() {
    PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos "$@" 2>/dev/null
}

# =============================================================================
# Checks
# =============================================================================

check_metrics() {
    log_info "=== RBAC & Memory Metrics ==="

    local metrics
    metrics=$(curl -sS "$BASE_URL/metrics" 2>/dev/null || echo "")

    if [[ -z "$metrics" ]]; then
        log_crit "Cannot fetch metrics from $BASE_URL/metrics"
        return 1
    fi

    # Extract key metrics
    local allowed denied audit_success audit_error mem_success mem_error

    allowed=$(echo "$metrics" | grep 'rbac_decisions_total.*decision="allowed"' | grep -v "^#" | awk '{sum+=$NF} END {print sum+0}')
    denied=$(echo "$metrics" | grep 'rbac_decisions_total.*decision="denied"' | grep -v "^#" | awk '{sum+=$NF} END {print sum+0}')
    audit_success=$(echo "$metrics" | grep 'rbac_audit_writes_total{status="success"}' | awk '{print $NF}')
    audit_error=$(echo "$metrics" | grep 'rbac_audit_writes_total{status="error"}' | awk '{print $NF}')
    mem_success=$(echo "$metrics" | grep 'memory_pins_operations_total.*status="success"' | grep -v "^#" | awk '{sum+=$NF} END {print sum+0}')
    mem_error=$(echo "$metrics" | grep 'memory_pins_operations_total.*status="error"' | grep -v "^#" | awk '{print $NF}')

    # Default values
    audit_success=${audit_success:-0}
    audit_error=${audit_error:-0}
    mem_error=${mem_error:-0}

    log_info "RBAC Decisions: allowed=$allowed, denied=$denied"
    log_info "RBAC Audit: success=$audit_success, error=$audit_error"
    log_info "Memory Ops: success=$mem_success, error=$mem_error"

    # Calculate denial ratio
    local total=$((allowed + denied))
    local denial_ratio=0
    if [[ $total -gt 0 ]]; then
        denial_ratio=$(echo "scale=4; $denied / $total" | bc)
    fi

    # Check thresholds
    local status=0

    if (( $(echo "$denial_ratio > $DENIAL_RATIO_CRIT" | bc -l) )); then
        log_crit "Denial ratio $denial_ratio exceeds critical threshold $DENIAL_RATIO_CRIT"
        status=2
    elif (( $(echo "$denial_ratio > $DENIAL_RATIO_WARN" | bc -l) )); then
        log_warn "Denial ratio $denial_ratio exceeds warning threshold $DENIAL_RATIO_WARN"
        [[ $status -lt 1 ]] && status=1
    else
        log_ok "Denial ratio $denial_ratio is healthy"
    fi

    if [[ "${audit_error%.*}" -ge $AUDIT_ERROR_CRIT ]]; then
        log_crit "Audit errors ${audit_error%.*} exceeds critical threshold $AUDIT_ERROR_CRIT"
        status=2
    elif [[ "${audit_error%.*}" -ge $AUDIT_ERROR_WARN ]]; then
        log_warn "Audit errors ${audit_error%.*} exceeds warning threshold $AUDIT_ERROR_WARN"
        [[ $status -lt 1 ]] && status=1
    else
        log_ok "Audit errors ${audit_error%.*} is acceptable"
    fi

    if [[ "${mem_error%.*}" -gt 0 ]]; then
        log_warn "Memory operation errors: ${mem_error%.*}"
        [[ $status -lt 1 ]] && status=1
    else
        log_ok "No memory operation errors"
    fi

    return $status
}

check_recent_denials() {
    log_info "=== Recent RBAC Denials (last 1h) ==="

    local result
    result=$(run_psql -t -c "
        SELECT subject, resource, action, reason, COUNT(*)
        FROM system.rbac_audit
        WHERE allowed = false AND ts > now() - interval '1 hour'
        GROUP BY 1,2,3,4 ORDER BY 5 DESC LIMIT 5;
    " | grep -v "^$")

    if [[ -z "$result" ]]; then
        log_ok "No RBAC denials in last hour"
    else
        log_info "Denial summary:"
        echo "$result" | while read -r line; do
            echo "  $line"
        done
    fi
}

check_audit_entries() {
    log_info "=== Recent Audit Activity ==="

    local rbac_count mem_count
    rbac_count=$(run_psql -t -c "SELECT COUNT(*) FROM system.rbac_audit WHERE ts > now() - interval '1 hour'" | tr -d ' ')
    mem_count=$(run_psql -t -c "SELECT COUNT(*) FROM system.memory_audit WHERE ts > now() - interval '1 hour'" | tr -d ' ')

    log_info "RBAC audit entries (1h): $rbac_count"
    log_info "Memory audit entries (1h): $mem_count"
}

check_containers() {
    log_info "=== Container Health ==="

    local unhealthy
    unhealthy=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null | grep -c "nova" 2>/dev/null || echo "0")
    unhealthy=$(echo "$unhealthy" | tr -d '\n' | head -c 10)

    if [[ "$unhealthy" =~ ^[0-9]+$ ]] && [[ "$unhealthy" -gt 0 ]]; then
        log_crit "Unhealthy containers detected:"
        docker ps --filter "health=unhealthy" --format "{{.Names}}: {{.Status}}" | grep nova
        return 1
    else
        log_ok "All nova containers healthy"
    fi

    # Check backend specifically
    if curl -sf "$BASE_URL/health" > /dev/null 2>&1; then
        log_ok "Backend health endpoint OK"
    else
        log_crit "Backend health check failed"
        return 1
    fi
}

check_rbac_status() {
    log_info "=== RBAC Status ==="

    # Try with machine token if available
    local info
    if [[ -n "${MACHINE_SECRET_TOKEN:-}" ]]; then
        info=$(curl -sf -H "X-Machine-Token: $MACHINE_SECRET_TOKEN" "$BASE_URL/api/v1/rbac/info" 2>/dev/null || echo "{}")
    else
        info=$(curl -sf "$BASE_URL/api/v1/rbac/info" 2>/dev/null || echo "{}")
    fi

    local enforce_mode hash
    enforce_mode=$(echo "$info" | jq -r '.enforce_mode // "unknown"')
    hash=$(echo "$info" | jq -r '.hash // "unknown"')

    log_info "RBAC enforce_mode: $enforce_mode"
    log_info "RBAC policy hash: $hash"

    if [[ "$enforce_mode" == "true" ]]; then
        log_ok "RBAC enforcement is ENABLED"
    else
        log_warn "RBAC enforcement is $enforce_mode"
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    mkdir -p /var/log/aos 2>/dev/null || true

    echo ""
    log_info "========================================"
    log_info "M7 RBAC/Memory Monitoring Check"
    log_info "Timestamp: $(date -Iseconds)"
    log_info "========================================"
    echo ""

    local overall_status=0

    check_containers || overall_status=1
    echo ""

    check_rbac_status
    echo ""

    check_metrics || overall_status=$?
    echo ""

    check_recent_denials
    echo ""

    check_audit_entries
    echo ""

    log_info "========================================"
    if [[ $overall_status -eq 0 ]]; then
        log_ok "Overall status: HEALTHY"
    elif [[ $overall_status -eq 1 ]]; then
        log_warn "Overall status: WARNINGS - Review above"
    else
        log_crit "Overall status: CRITICAL - Action required"
        if $ALERT_ON_ANOMALY; then
            log_crit "ALERT: Consider rollback if issues persist"
            log_info "Rollback command: ./scripts/ops/rbac_enable.sh disable"
        fi
    fi
    log_info "========================================"

    return $overall_status
}

main "$@"
