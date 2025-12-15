#!/bin/bash
# M10 48h Pager Window Health Check
#
# Monitors critical services during the 48h production validation window.
# Designed to be run every 15 minutes via systemd timer.
#
# Checks:
#   1. Backend API health
#   2. Worker container status
#   3. Neon PostgreSQL connectivity
#   4. Upstash Redis connectivity
#   5. Prometheus metrics availability
#   6. Critical M10 table health
#
# Usage:
#   ./scripts/ops/m10_48h_health_check.sh
#   ./scripts/ops/m10_48h_health_check.sh --json    # JSON output
#
# Exit codes:
#   0 - All checks passed
#   1 - At least one check failed
#   2 - Critical failure (DB/Redis unreachable)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Load environment
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
fi

# Parse arguments
JSON_OUTPUT=false
for arg in "$@"; do
    case $arg in
        --json)
            JSON_OUTPUT=true
            ;;
    esac
done

# Results
declare -A RESULTS
OVERALL_STATUS="healthy"
CRITICAL_FAIL=false

log_check() {
    local name="$1"
    local status="$2"
    local details="${3:-}"

    RESULTS["$name"]="$status"

    if [ "$JSON_OUTPUT" = false ]; then
        if [ "$status" = "pass" ]; then
            echo "[OK] $name"
        elif [ "$status" = "warn" ]; then
            echo "[WARN] $name: $details"
        else
            echo "[FAIL] $name: $details"
        fi
    fi
}

# 1. Backend API Health
check_backend() {
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
    if [ "$response" = "200" ]; then
        log_check "backend_api" "pass"
    else
        log_check "backend_api" "fail" "HTTP $response"
        OVERALL_STATUS="degraded"
    fi
}

# 2. Worker Container Status
check_worker() {
    local status
    status=$(docker inspect --format='{{.State.Status}}' nova_worker 2>/dev/null || echo "not_found")
    if [ "$status" = "running" ]; then
        log_check "worker_container" "pass"
    else
        log_check "worker_container" "fail" "Status: $status"
        OVERALL_STATUS="degraded"
    fi
}

# 3. Neon PostgreSQL Connectivity
check_neon_db() {
    if [ -z "${DATABASE_URL:-}" ]; then
        log_check "neon_db" "fail" "DATABASE_URL not set"
        CRITICAL_FAIL=true
        return
    fi

    # Extract host from DATABASE_URL
    local host
    host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:\/]*\).*/\1/p')

    local result
    result=$(PGSSLMODE=require psql "$DATABASE_URL" -c "SELECT 1" -t 2>&1)
    if echo "$result" | grep -q "1"; then
        log_check "neon_db" "pass"
    else
        log_check "neon_db" "fail" "Connection failed"
        CRITICAL_FAIL=true
    fi
}

# 4. Upstash Redis Connectivity
check_redis() {
    if [ -z "${REDIS_URL:-}" ]; then
        log_check "upstash_redis" "warn" "REDIS_URL not set"
        return
    fi

    # Use Python for TLS Redis URLs (redis-cli doesn't handle rediss:// well)
    local result
    result=$(python3 -c "
import redis
import os
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    print(r.ping())
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)
    if [ "$result" = "True" ]; then
        log_check "upstash_redis" "pass"
    else
        log_check "upstash_redis" "fail" "Ping failed: $result"
        OVERALL_STATUS="degraded"
    fi
}

# 5. Prometheus Metrics
check_prometheus() {
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy 2>/dev/null)
    if [ "$response" = "200" ]; then
        log_check "prometheus" "pass"
    else
        log_check "prometheus" "warn" "Not accessible"
    fi
}

# 6. M10 Table Health
check_m10_tables() {
    if [ -z "${DATABASE_URL:-}" ]; then
        log_check "m10_tables" "skip" "No database connection"
        return
    fi

    # Core M10 tables (migration 022 creates these)
    local count
    count=$(PGSSLMODE=require psql "$DATABASE_URL" -t -c "
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN (
            'recovery_candidates', 'recovery_candidates_audit',
            'failure_matches', 'failure_pattern_exports',
            'failure_match_metrics', 'failure_pattern_candidates'
        )" 2>/dev/null | tr -d ' ')

    if [ "${count:-0}" -ge 4 ]; then
        log_check "m10_tables" "pass" "$count/6 core M10 tables present"
    else
        log_check "m10_tables" "warn" "Only $count/6 core M10 tables found"
        OVERALL_STATUS="degraded"
    fi
}

# 7. Recent Error Rate (from Prometheus)
check_error_rate() {
    local result
    result=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{status=~"5.."}[5m]))' 2>/dev/null | jq -r '.data.result[0].value[1] // "0"')

    if [ "$result" = "null" ] || [ -z "$result" ]; then
        log_check "error_rate" "pass" "No 5xx errors"
    elif (( $(echo "$result > 0.1" | bc -l) )); then
        log_check "error_rate" "warn" "Error rate: $result/s"
    else
        log_check "error_rate" "pass" "Error rate: $result/s"
    fi
}

# Run all checks
main() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo "=== M10 48h Health Check ==="
        echo "Time: $(date -Iseconds)"
        echo ""
    fi

    check_backend
    check_worker
    check_neon_db
    check_redis
    check_prometheus
    check_m10_tables
    check_error_rate

    # Determine final status
    if [ "$CRITICAL_FAIL" = true ]; then
        OVERALL_STATUS="critical"
    fi

    if [ "$JSON_OUTPUT" = true ]; then
        # Output JSON
        echo "{"
        echo "  \"timestamp\": \"$(date -Iseconds)\","
        echo "  \"status\": \"$OVERALL_STATUS\","
        echo "  \"checks\": {"
        local first=true
        for key in "${!RESULTS[@]}"; do
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            echo -n "    \"$key\": \"${RESULTS[$key]}\""
        done
        echo ""
        echo "  }"
        echo "}"
    else
        echo ""
        echo "=== Summary ==="
        echo "Overall Status: $OVERALL_STATUS"

        if [ "$OVERALL_STATUS" = "healthy" ]; then
            echo "All checks passed."
        elif [ "$OVERALL_STATUS" = "critical" ]; then
            echo "CRITICAL: Database or Redis unreachable!"
        else
            echo "WARNING: Some checks failed. Review above."
        fi
    fi

    # Exit code based on status
    case "$OVERALL_STATUS" in
        healthy) exit 0 ;;
        critical) exit 2 ;;
        *) exit 1 ;;
    esac
}

main
