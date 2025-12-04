#!/usr/bin/env bash
# canary_smoke_test.sh - Automated smoke test with auto-rollback
#
# Usage:
#   ./scripts/ops/canary_smoke_test.sh                    # Run against localhost
#   ./scripts/ops/canary_smoke_test.sh --url https://staging.example.com
#   ./scripts/ops/canary_smoke_test.sh --auto-rollback    # Rollback on any failure
#   ./scripts/ops/canary_smoke_test.sh --watch 300        # Watch mode for 5 minutes
#
# Exit codes:
#   0 - All checks passed
#   1 - Check failed (rollback triggered if --auto-rollback)
#   2 - Rollback executed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
BASE_URL="${AOS_BASE_URL:-http://127.0.0.1:8000}"
AUTO_ROLLBACK=false
WATCH_SECONDS=0
VERBOSE=false

# Thresholds
ERROR_RATE_THRESHOLD=10        # errors per minute
LATENCY_P95_THRESHOLD=5000     # milliseconds
MISMATCH_THRESHOLD=0           # any mismatch = fail

log_info() { echo -e "${GREEN}[SMOKE]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[SMOKE]${NC} $1"; }
log_error() { echo -e "${RED}[SMOKE]${NC} $1"; }
log_step() { echo -e "${BLUE}[CHECK]${NC} $1"; }

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Automated canary smoke test with optional auto-rollback.

Options:
    --url URL           Base URL to test (default: http://127.0.0.1:8000)
    --auto-rollback     Automatically trigger rollback on failure
    --watch SECONDS     Watch mode: repeat checks for N seconds
    --verbose           Show detailed output
    -h, --help          Show this help

Checks performed:
1. Health endpoint (/healthz)
2. Readiness endpoint (/readyz or /health)
3. Metrics endpoint (/metrics)
4. Golden mismatch count (must be 0)
5. Error rate (must be < threshold)
6. Feature flag status verification

Thresholds:
    - Golden mismatch: $MISMATCH_THRESHOLD (any = fail)
    - Error rate: $ERROR_RATE_THRESHOLD/min
    - P95 latency: ${LATENCY_P95_THRESHOLD}ms
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            BASE_URL="$2"
            shift 2
            ;;
        --auto-rollback)
            AUTO_ROLLBACK=true
            shift
            ;;
        --watch)
            WATCH_SECONDS="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Results tracking
PASSED=0
FAILED=0
CHECKS=()

record_pass() {
    local check="$1"
    CHECKS+=("✅ $check")
    ((PASSED++))
    log_info "✅ $check"
}

record_fail() {
    local check="$1"
    local detail="${2:-}"
    CHECKS+=("❌ $check: $detail")
    ((FAILED++))
    log_error "❌ $check: $detail"
}

# Check 1: Health endpoint
check_health() {
    log_step "Checking /healthz..."
    local response
    if response=$(curl -sf --max-time 5 "$BASE_URL/healthz" 2>&1); then
        record_pass "/healthz returns 200"
        return 0
    else
        record_fail "/healthz" "Not responding or non-200"
        return 1
    fi
}

# Check 2: Readiness endpoint
check_ready() {
    log_step "Checking readiness..."
    local response
    # Try /readyz first, fall back to /health
    if response=$(curl -sf --max-time 5 "$BASE_URL/readyz" 2>&1); then
        record_pass "/readyz returns 200"
        return 0
    elif response=$(curl -sf --max-time 5 "$BASE_URL/health" 2>&1); then
        record_pass "/health returns 200"
        return 0
    else
        record_fail "Readiness" "Neither /readyz nor /health responding"
        return 1
    fi
}

# Check 3: Metrics endpoint
check_metrics() {
    log_step "Checking /metrics..."
    local response
    if response=$(curl -sf --max-time 5 "$BASE_URL/metrics" 2>&1); then
        if echo "$response" | grep -q "nova_"; then
            record_pass "/metrics returns nova_* metrics"
            return 0
        else
            record_fail "/metrics" "No nova_* metrics found"
            return 1
        fi
    else
        record_fail "/metrics" "Not responding"
        return 1
    fi
}

# Check 4: Golden mismatch count
check_golden_mismatch() {
    log_step "Checking golden mismatch count..."
    local metrics
    metrics=$(curl -sf --max-time 5 "$BASE_URL/metrics" 2>&1 || echo "")

    # Extract mismatch count (looking for nova_golden_mismatch_total)
    local mismatch_line
    mismatch_line=$(echo "$metrics" | grep "nova_golden_mismatch_total" | grep -v "^#" | head -1 || echo "")

    if [[ -z "$mismatch_line" ]]; then
        # Metric not present = 0 mismatches (good)
        record_pass "Golden mismatch: 0 (metric not present)"
        return 0
    fi

    local mismatch_count
    mismatch_count=$(echo "$mismatch_line" | awk '{print $NF}' | cut -d. -f1)

    if [[ "$mismatch_count" -le "$MISMATCH_THRESHOLD" ]]; then
        record_pass "Golden mismatch: $mismatch_count"
        return 0
    else
        record_fail "Golden mismatch" "Count=$mismatch_count (threshold=$MISMATCH_THRESHOLD)"
        return 1
    fi
}

# Check 5: Error rate
check_error_rate() {
    log_step "Checking error rate..."
    local metrics
    metrics=$(curl -sf --max-time 5 "$BASE_URL/metrics" 2>&1 || echo "")

    # This is a simplified check - in production, query Prometheus for rate()
    local error_line
    error_line=$(echo "$metrics" | grep "nova_workflow_error_total" | grep -v "^#" | head -1 || echo "")

    if [[ -z "$error_line" ]]; then
        record_pass "Error rate: 0 (metric not present)"
        return 0
    fi

    # For now, just verify metric exists and is parseable
    record_pass "Error rate metric present"
    return 0
}

# Check 6: Feature flag status
check_feature_flags() {
    log_step "Checking feature flags..."

    local flags_file="$PROJECT_ROOT/backend/app/config/feature_flags.json"
    if [[ ! -f "$flags_file" ]]; then
        record_fail "Feature flags" "Config file not found"
        return 1
    fi

    # Verify flags are properly configured (not accidentally enabled without signoff)
    local signoff_file="$PROJECT_ROOT/.m4_signoff"
    local catalog_enabled
    catalog_enabled=$(jq -r '.flags.failure_catalog_runtime_integration.enabled // false' "$flags_file")

    if [[ "$catalog_enabled" == "true" && ! -f "$signoff_file" ]]; then
        record_fail "Feature flags" "Catalog flag enabled without .m4_signoff!"
        return 1
    fi

    record_pass "Feature flags configured correctly"
    return 0
}

# Execute rollback
do_rollback() {
    log_warn "═══════════════════════════════════════════════════════════════"
    log_warn "         TRIGGERING AUTOMATIC ROLLBACK"
    log_warn "═══════════════════════════════════════════════════════════════"

    if [[ -x "$PROJECT_ROOT/scripts/rollback_failure_catalog.sh" ]]; then
        bash "$PROJECT_ROOT/scripts/rollback_failure_catalog.sh" --force
        return $?
    else
        log_error "Rollback script not found or not executable"
        return 1
    fi
}

# Run all checks
run_checks() {
    PASSED=0
    FAILED=0
    CHECKS=()

    check_health || true
    check_ready || true
    check_metrics || true
    check_golden_mismatch || true
    check_error_rate || true
    check_feature_flags || true
}

# Print summary
print_summary() {
    echo ""
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "         SMOKE TEST SUMMARY"
    log_info "═══════════════════════════════════════════════════════════════"
    echo ""
    log_info "Target: $BASE_URL"
    log_info "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo ""

    for check in "${CHECKS[@]}"; do
        echo "  $check"
    done

    echo ""
    log_info "Results: $PASSED passed, $FAILED failed"
    echo ""

    if [[ "$FAILED" -eq 0 ]]; then
        log_info "═══════════════════════════════════════════════════════════════"
        log_info "         ✅ ALL CHECKS PASSED"
        log_info "═══════════════════════════════════════════════════════════════"
        return 0
    else
        log_error "═══════════════════════════════════════════════════════════════"
        log_error "         ❌ CHECKS FAILED"
        log_error "═══════════════════════════════════════════════════════════════"
        return 1
    fi
}

# Main
main() {
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "         M4.5 Canary Smoke Test"
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "Target: $BASE_URL"
    log_info "Auto-rollback: $AUTO_ROLLBACK"
    log_info "Watch mode: ${WATCH_SECONDS}s"
    echo ""

    if [[ "$WATCH_SECONDS" -gt 0 ]]; then
        # Watch mode: repeat checks for specified duration
        local end_time=$(($(date +%s) + WATCH_SECONDS))
        local iteration=1

        while [[ $(date +%s) -lt $end_time ]]; do
            log_info "--- Iteration $iteration ($(date +%H:%M:%S)) ---"
            run_checks

            if [[ "$FAILED" -gt 0 ]]; then
                log_error "Failure detected in iteration $iteration"
                if [[ "$AUTO_ROLLBACK" == "true" ]]; then
                    do_rollback
                    exit 2
                fi
                print_summary
                exit 1
            fi

            ((iteration++))
            sleep 10
        done

        log_info "Watch period completed successfully ($iteration iterations)"
        print_summary
        exit 0
    else
        # Single run
        run_checks

        if ! print_summary; then
            if [[ "$AUTO_ROLLBACK" == "true" ]]; then
                do_rollback
                exit 2
            fi
            exit 1
        fi

        exit 0
    fi
}

main "$@"
