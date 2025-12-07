#!/usr/bin/env bash
# =============================================================================
# RBAC Enablement Smoke Test Script
# =============================================================================
# Purpose: Verify RBAC enforcement is working correctly before production
# Usage: ./rbac_enable_smoke.sh [--base-url URL] [--token TOKEN]
#
# This script covers Section A of the RBAC enablement plan:
# - A1: Verify machine token allows access
# - A2: (manual) RBAC_ENFORCE=true in env
# - A3: Verify unauthorized access is blocked
# - A4: Pre-condition checks
# =============================================================================

set -uo pipefail

# Configuration
BASE_URL="${1:-http://127.0.0.1:8000}"
MACHINE_TOKEN="${MACHINE_SECRET_TOKEN:-}"
DATABASE_URL="${DATABASE_URL:-postgresql://nova:novapass@localhost:6432/nova_aos}"

# Helper to run psql with proper password
run_psql() {
    PGPASSWORD=novapass psql -h localhost -p 6432 -U nova -d nova_aos "$@" 2>/dev/null
}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
}

# =============================================================================
# Section A1: Verify Machine Token Access
# =============================================================================
test_machine_token_access() {
    log_section "A1: Verify Machine Token Access"

    if [[ -z "$MACHINE_TOKEN" ]]; then
        log_warn "MACHINE_SECRET_TOKEN not set - skipping machine token test"
        log_info "Set MACHINE_SECRET_TOKEN to test machine authentication"
        return
    fi

    # Test POST with machine token
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${BASE_URL}/api/v1/memory/pins" \
        -H "X-Machine-Token: ${MACHINE_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"tenant_id":"rbac-test","key":"smoke:machine_token","value":{"test":true}}')

    if [[ "$STATUS" == "200" ]] || [[ "$STATUS" == "201" ]]; then
        log_pass "Machine token write: HTTP $STATUS"
    else
        log_fail "Machine token write failed: HTTP $STATUS (expected 200/201)"
    fi

    # Cleanup test pin
    curl -s -o /dev/null -X DELETE \
        "${BASE_URL}/api/v1/memory/pins/smoke:machine_token?tenant_id=rbac-test" \
        -H "X-Machine-Token: ${MACHINE_TOKEN}" || true
}

# =============================================================================
# Section A3: Verify Unauthorized Access is Blocked
# =============================================================================
test_unauthorized_blocked() {
    log_section "A3: Verify Unauthorized Access Blocked"

    # Test POST without any token (should be blocked when RBAC_ENFORCE=true)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${BASE_URL}/api/v1/memory/pins" \
        -H "Content-Type: application/json" \
        -d '{"tenant_id":"rbac-test","key":"smoke:unauthorized","value":{}}')

    if [[ "$STATUS" == "403" ]]; then
        log_pass "Unauthorized write blocked: HTTP 403"
    elif [[ "$STATUS" == "200" ]] || [[ "$STATUS" == "201" ]]; then
        log_warn "Unauthorized write allowed: HTTP $STATUS - RBAC may not be enforced"
    else
        log_warn "Unexpected response: HTTP $STATUS"
    fi
}

# =============================================================================
# Section A4: Pre-condition Checks
# =============================================================================
test_preconditions() {
    log_section "A4: Pre-condition Checks"

    # Check API health
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
    if [[ "$HEALTH_STATUS" == "200" ]]; then
        log_pass "API health check: HTTP 200"
    else
        log_fail "API health check failed: HTTP $HEALTH_STATUS"
    fi

    # Check RBAC info endpoint (use machine token if available, since endpoint requires auth when RBAC enforced)
    if [[ -n "$MACHINE_TOKEN" ]]; then
        RBAC_INFO=$(curl -s -H "X-Machine-Token: ${MACHINE_TOKEN}" "${BASE_URL}/api/v1/rbac/info" 2>/dev/null || echo '{}')
    else
        RBAC_INFO=$(curl -s "${BASE_URL}/api/v1/rbac/info" 2>/dev/null || echo '{}')
    fi
    ENFORCE_MODE=$(echo "$RBAC_INFO" | jq -r '.enforce_mode' 2>/dev/null || echo "unknown")

    if [[ "$ENFORCE_MODE" == "true" ]]; then
        log_pass "RBAC enforcement: ENABLED"
    elif [[ "$ENFORCE_MODE" == "false" ]]; then
        log_info "RBAC enforcement: DISABLED (safe mode)"
    else
        log_warn "RBAC enforcement: UNKNOWN ($ENFORCE_MODE)"
    fi

    # Check policy hash
    POLICY_HASH=$(echo "$RBAC_INFO" | jq -r '.hash // "none"' 2>/dev/null || echo "none")
    if [[ "$POLICY_HASH" != "none" ]] && [[ "$POLICY_HASH" != "null" ]]; then
        log_pass "RBAC policy loaded: hash=$POLICY_HASH"
    else
        log_warn "RBAC policy not loaded or hash unavailable"
    fi
}

# =============================================================================
# Section B: Verify RBAC Audit Entries
# =============================================================================
test_rbac_audit() {
    log_section "B: Verify RBAC Audit Entries"

    if ! command -v psql &> /dev/null; then
        log_warn "psql not found - skipping database checks"
        return 0
    fi

    # Note: Table is system.rbac_audit, not auth.rbac_audit
    COUNT=$(run_psql -t -c "SELECT count(*) FROM system.rbac_audit" | tr -d ' ' || echo "0")

    if [[ "$COUNT" -gt 0 ]]; then
        log_pass "RBAC audit entries found: $COUNT"
    else
        log_warn "No RBAC audit entries found (may be expected if RBAC disabled)"
    fi

    # Check for denied entries (only if RBAC enforced)
    DENIED=$(run_psql -t -c "SELECT count(*) FROM system.rbac_audit WHERE allowed = false" | tr -d ' ' || echo "0")

    if [[ "$DENIED" -gt 0 ]]; then
        log_pass "RBAC denials logged: $DENIED"
    else
        log_info "No RBAC denials logged (normal if no unauthorized attempts)"
    fi
}

# =============================================================================
# Section C: Verify Memory Audit Correctness
# =============================================================================
test_memory_audit() {
    log_section "C: Verify Memory Audit Entries"

    if ! command -v psql &> /dev/null; then
        log_warn "psql not found - skipping database checks"
        return 0
    fi

    # Check memory audit entries exist
    COUNT=$(run_psql -t -c "SELECT count(*) FROM system.memory_audit" | tr -d ' ' || echo "0")

    if [[ "$COUNT" -gt 0 ]]; then
        log_pass "Memory audit entries found: $COUNT"
    else
        log_warn "No memory audit entries found"
    fi

    # Check value_hash is being stored (not full values)
    HASH_CHECK=$(run_psql -t -c \
        "SELECT count(*) FROM system.memory_audit WHERE new_value_hash IS NOT NULL AND length(new_value_hash) = 16" | tr -d ' ' || echo "0")

    if [[ "$HASH_CHECK" -gt 0 ]]; then
        log_pass "Value hashes stored correctly (16-char SHA256 prefix): $HASH_CHECK entries"
    else
        log_info "No value hashes found (may be expected for read operations)"
    fi
}

# =============================================================================
# Section D: Verify TTL Expiration
# =============================================================================
test_ttl_expiration() {
    log_section "D: Verify TTL Expiration"

    if ! command -v psql &> /dev/null; then
        log_warn "psql not found - skipping database checks"
        return 0
    fi

    # Check for expired pins that should have been cleaned up
    EXPIRED=$(run_psql -t -c \
        "SELECT count(*) FROM system.memory_pins WHERE expires_at IS NOT NULL AND expires_at < now()" | tr -d ' ' || echo "0")

    if [[ "$EXPIRED" == "0" ]]; then
        log_pass "No expired pins pending cleanup"
    else
        log_warn "Expired pins pending cleanup: $EXPIRED"
    fi

    # Check if TTL cleanup script exists
    if [[ -f "/root/agenticverz2.0/scripts/ops/expire_memory_pins.sh" ]]; then
        log_pass "TTL cleanup script exists"
    else
        log_fail "TTL cleanup script not found"
    fi

    # Check cron job
    if crontab -l 2>/dev/null | grep -q "expire_memory_pins"; then
        log_pass "TTL cleanup cron job installed"
    else
        log_warn "TTL cleanup cron job not installed"
    fi
}

# =============================================================================
# Section E: CostSim Memory Integration Test
# =============================================================================
test_costsim_memory() {
    log_section "E: CostSim Memory Integration Test"

    # Check if CostSim endpoint is available
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/costsim/v2/status")

    if [[ "$STATUS" == "200" ]]; then
        log_pass "CostSim V2 status endpoint: HTTP 200"

        # Get sandbox status
        SANDBOX_INFO=$(curl -s "${BASE_URL}/costsim/v2/status" 2>/dev/null || echo '{}')
        SANDBOX_ENABLED=$(echo "$SANDBOX_INFO" | jq -r '.sandbox_enabled // false' 2>/dev/null || echo "false")

        if [[ "$SANDBOX_ENABLED" == "true" ]]; then
            log_pass "CostSim V2 sandbox: ENABLED"
        else
            log_info "CostSim V2 sandbox: DISABLED (expected in production)"
        fi
    else
        log_warn "CostSim V2 status endpoint unavailable: HTTP $STATUS"
    fi
}

# =============================================================================
# Section H: Prometheus Metrics Check
# =============================================================================
test_prometheus_metrics() {
    log_section "H: Prometheus Metrics Check"

    METRICS=$(curl -s "${BASE_URL}/metrics" 2>/dev/null || echo "")

    if [[ -z "$METRICS" ]]; then
        log_warn "Could not fetch metrics endpoint"
        return
    fi

    # Check RBAC metrics
    if echo "$METRICS" | grep -q "rbac_engine_decisions_total"; then
        log_pass "RBAC decisions metric found"
    else
        log_warn "RBAC decisions metric not found"
    fi

    # Check memory pins metrics
    if echo "$METRICS" | grep -q "memory_pins_operations_total"; then
        log_pass "Memory pins operations metric found"
    else
        log_warn "Memory pins operations metric not found"
    fi

    # Check RBAC policy loads
    if echo "$METRICS" | grep -q "rbac_policy_loads_total"; then
        log_pass "RBAC policy loads metric found"
    else
        log_info "RBAC policy loads metric not found (may not have reloaded yet)"
    fi
}

# =============================================================================
# Summary
# =============================================================================
print_summary() {
    log_section "SUMMARY"

    echo ""
    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""

    if [[ $FAILED -gt 0 ]]; then
        echo -e "${RED}RESULT: FAILED - Fix issues before enabling RBAC${NC}"
        exit 1
    elif [[ $WARNINGS -gt 3 ]]; then
        echo -e "${YELLOW}RESULT: WARNINGS - Review before production${NC}"
        exit 0
    else
        echo -e "${GREEN}RESULT: PASSED - Safe to proceed with RBAC enablement${NC}"
        exit 0
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo ""
    echo "RBAC Enablement Smoke Test"
    echo "Base URL: $BASE_URL"
    echo "Timestamp: $(date -Iseconds)"
    echo ""

    test_preconditions
    test_machine_token_access
    test_unauthorized_blocked
    test_rbac_audit
    test_memory_audit
    test_ttl_expiration
    test_costsim_memory
    test_prometheus_metrics

    print_summary
}

main "$@"
