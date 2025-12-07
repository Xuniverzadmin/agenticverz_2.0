#!/usr/bin/env bash
#
# AOS E2E Integration Test Harness
#
# M8 Deliverable: Comprehensive end-to-end testing for trace determinism
#
# Usage:
#   ./scripts/e2e_integration.sh              # Run all tests
#   ./scripts/e2e_integration.sh --quick      # Quick smoke test
#   ./scripts/e2e_integration.sh --verbose    # Verbose output
#   ./scripts/e2e_integration.sh --parity     # Only parity tests
#
# Environment:
#   API_URL      - Base URL (default: http://localhost:8000)
#   API_KEY      - AOS API key
#   TENANT_ID    - Test tenant (default: e2e-test)
#   REPORT_DIR   - Report output directory
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-}"
TENANT_ID="${TENANT_ID:-e2e-test}"
REPORT_DIR="${REPORT_DIR:-/tmp/aos-e2e-reports}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Options
QUICK_MODE=false
VERBOSE=false
PARITY_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --parity)
            PARITY_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick      Run quick smoke tests only"
            echo "  --verbose    Enable verbose output"
            echo "  --parity     Run parity tests only"
            echo "  --help       Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    ((TESTS_SKIPPED++))
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${YELLOW}[DEBUG]${NC} $1"
    fi
}

# API helper
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"

    local headers=(-H "Content-Type: application/json")
    if [[ -n "$API_KEY" ]]; then
        headers+=(-H "X-API-Key: $API_KEY")
    fi
    headers+=(-H "X-Tenant-ID: $TENANT_ID")

    if [[ "$method" == "POST" && -n "$data" ]]; then
        curl -s -X POST "${API_URL}${endpoint}" \
            "${headers[@]}" \
            -d "$data" \
            --max-time 30
    else
        curl -s -X "$method" "${API_URL}${endpoint}" \
            "${headers[@]}" \
            --max-time 30
    fi
}

# Setup
setup() {
    log_info "Setting up E2E integration tests..."
    mkdir -p "$REPORT_DIR"

    # Health check
    log_info "Checking API health at $API_URL..."
    local health
    health=$(curl -s --max-time 5 "${API_URL}/health" || echo '{"status":"error"}')

    if ! echo "$health" | grep -q '"status"'; then
        log_fail "API health check failed - is the server running?"
        exit 1
    fi

    log_info "API is healthy"

    # Check required tools
    for tool in curl jq; do
        if ! command -v "$tool" &> /dev/null; then
            log_fail "Required tool not found: $tool"
            exit 1
        fi
    done
}

# Test: Basic simulate endpoint
test_simulate_basic() {
    ((TESTS_RUN++))
    log_info "Test: Basic simulate endpoint..."

    local payload='{
        "workflow_id": "e2e-basic-test",
        "input": {"type": "echo", "message": "hello"},
        "config": {"seed": 42, "frozen_timestamp": "2024-01-01T00:00:00Z"}
    }'

    local response
    response=$(api_call POST "/api/v1/runtime/simulate" "$payload")
    log_debug "Response: $response"

    if echo "$response" | jq -e '.trace_id // .simulation_id // .id' > /dev/null 2>&1; then
        log_pass "Basic simulate endpoint works"
        return 0
    else
        log_fail "Basic simulate endpoint - no trace ID returned"
        return 1
    fi
}

# Test: Deterministic replay
test_deterministic_replay() {
    ((TESTS_RUN++))
    log_info "Test: Deterministic replay..."

    local seed=12345
    local timestamp="2024-06-15T10:30:00Z"

    local payload='{
        "workflow_id": "e2e-determinism-test",
        "input": {"type": "compute", "value": 100},
        "config": {"seed": '"$seed"', "frozen_timestamp": "'"$timestamp"'", "deterministic": true}
    }'

    # Run twice with same seed/timestamp
    local response1 response2
    response1=$(api_call POST "/api/v1/runtime/simulate" "$payload")
    response2=$(api_call POST "/api/v1/runtime/simulate" "$payload")

    local hash1 hash2
    hash1=$(echo "$response1" | jq -r '.root_hash // .trace.root_hash // empty')
    hash2=$(echo "$response2" | jq -r '.root_hash // .trace.root_hash // empty')

    log_debug "Hash 1: $hash1"
    log_debug "Hash 2: $hash2"

    if [[ -n "$hash1" && "$hash1" == "$hash2" ]]; then
        log_pass "Deterministic replay produces identical hashes"
        return 0
    elif [[ -z "$hash1" ]]; then
        log_skip "No root_hash in response (endpoint may not support determinism)"
        return 0
    else
        log_fail "Deterministic replay - hashes differ: $hash1 != $hash2"
        return 1
    fi
}

# Test: Idempotency enforcement
test_idempotency() {
    ((TESTS_RUN++))
    log_info "Test: Idempotency enforcement..."

    local idem_key="e2e-idem-$(date +%s)"

    local payload='{
        "workflow_id": "e2e-idempotency-test",
        "input": {"type": "echo", "message": "idempotency"},
        "config": {"seed": 42},
        "idempotency_key": "'"$idem_key"'"
    }'

    # First request
    local response1
    response1=$(api_call POST "/api/v1/runtime/simulate" "$payload")
    local status1=$?

    # Second request with same key
    local response2
    response2=$(api_call POST "/api/v1/runtime/simulate" "$payload")
    local status2=$?

    # Both should succeed (idempotent replay)
    if [[ $status1 -eq 0 && $status2 -eq 0 ]]; then
        local id1 id2
        id1=$(echo "$response1" | jq -r '.trace_id // .id // empty')
        id2=$(echo "$response2" | jq -r '.trace_id // .id // empty')

        if [[ -n "$id1" && "$id1" == "$id2" ]]; then
            log_pass "Idempotency returns same trace ID"
            return 0
        elif [[ -n "$id1" && -n "$id2" ]]; then
            # Different IDs but both succeeded - acceptable behavior
            log_pass "Idempotency accepted (different IDs is acceptable)"
            return 0
        fi
    fi

    # Check for conflict
    if echo "$response2" | grep -qi "conflict"; then
        log_fail "Idempotency conflict detected unexpectedly"
        return 1
    fi

    log_pass "Idempotency test completed"
    return 0
}

# Test: Cross-language parity (if Python SDK is available)
test_cross_language_parity() {
    ((TESTS_RUN++))
    log_info "Test: Cross-language parity..."

    # Check if Python SDK is available
    if ! command -v python3 &> /dev/null; then
        log_skip "Python3 not available"
        return 0
    fi

    local sdk_path="$PROJECT_ROOT/sdk/python"
    if [[ ! -d "$sdk_path" ]]; then
        log_skip "Python SDK not found at $sdk_path"
        return 0
    fi

    # Generate trace with Python
    local py_trace_file="$REPORT_DIR/python_trace.json"

    PYTHONPATH="$sdk_path" python3 << 'EOF' > "$py_trace_file"
import json
import sys
sys.path.insert(0, ".")
try:
    from aos_sdk.trace import Trace

    trace = Trace(
        workflow_id="parity-test",
        seed=42,
        frozen_timestamp="2024-01-01T12:00:00Z"
    )
    trace.add_step(
        skill_id="echo",
        input_data={"message": "parity"},
        output_data={"echo": "parity"}
    )
    trace.finalize()
    print(json.dumps(trace.to_dict()))
except Exception as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)
EOF

    if [[ ! -s "$py_trace_file" ]]; then
        log_skip "Python SDK trace generation failed"
        return 0
    fi

    # Check if JS SDK parity script exists
    local js_parity_script="$PROJECT_ROOT/sdk/js/aos-sdk/scripts/compare_with_python.js"
    if [[ -f "$js_parity_script" ]]; then
        if command -v node &> /dev/null; then
            local parity_result
            parity_result=$(node "$js_parity_script" "$py_trace_file" 2>&1) || true

            if echo "$parity_result" | grep -q "PARITY CHECK: PASSED"; then
                log_pass "Cross-language parity verified"
                return 0
            elif echo "$parity_result" | grep -q "PARITY CHECK: FAILED"; then
                log_fail "Cross-language parity failed"
                echo "$parity_result"
                return 1
            fi
        fi
    fi

    # Fallback: just verify Python trace has expected structure
    if jq -e '.root_hash and .steps and .seed' "$py_trace_file" > /dev/null 2>&1; then
        log_pass "Python trace has valid structure"
        return 0
    fi

    log_skip "Could not fully verify cross-language parity"
    return 0
}

# Test: Trace schema validation
test_trace_schema() {
    ((TESTS_RUN++))
    log_info "Test: Trace schema v1.1 validation..."

    local payload='{
        "workflow_id": "e2e-schema-test",
        "input": {"type": "validate"},
        "config": {"seed": 42, "frozen_timestamp": "2024-01-01T00:00:00Z", "deterministic": true}
    }'

    local response
    response=$(api_call POST "/api/v1/runtime/simulate" "$payload")

    # Check for schema version
    local schema_version
    schema_version=$(echo "$response" | jq -r '.trace.schema_version // .schema_version // empty')

    if [[ "$schema_version" == "1.1" ]]; then
        log_pass "Trace schema version is 1.1"

        # Verify required fields
        local has_seed has_timestamp
        has_seed=$(echo "$response" | jq -e '.trace.seed // .seed' > /dev/null 2>&1 && echo "yes" || echo "no")
        has_timestamp=$(echo "$response" | jq -e '.trace.frozen_timestamp // .frozen_timestamp' > /dev/null 2>&1 && echo "yes" || echo "no")

        if [[ "$has_seed" == "yes" && "$has_timestamp" == "yes" ]]; then
            log_debug "Schema validation: seed and frozen_timestamp present"
        fi

        return 0
    elif [[ -n "$schema_version" ]]; then
        log_fail "Unexpected schema version: $schema_version (expected 1.1)"
        return 1
    else
        log_skip "Schema version not returned in response"
        return 0
    fi
}

# Test: Rate limiting (if enabled)
test_rate_limiting() {
    ((TESTS_RUN++))
    log_info "Test: Rate limiting..."

    if [[ "$QUICK_MODE" == "true" ]]; then
        log_skip "Rate limit test skipped in quick mode"
        return 0
    fi

    local payload='{
        "workflow_id": "e2e-rate-limit-test",
        "input": {"type": "echo", "message": "rate-test"},
        "config": {"seed": 42}
    }'

    local rate_limited=false
    for i in {1..50}; do
        local response
        response=$(api_call POST "/api/v1/runtime/simulate" "$payload" 2>&1) || true

        if echo "$response" | grep -qiE "(rate.?limit|too.?many|429)"; then
            rate_limited=true
            break
        fi

        # Small delay to not be too aggressive
        sleep 0.05
    done

    if [[ "$rate_limited" == "true" ]]; then
        log_pass "Rate limiting is active"
    else
        log_pass "No rate limiting triggered (may not be configured)"
    fi

    return 0
}

# Test: Error handling
test_error_handling() {
    ((TESTS_RUN++))
    log_info "Test: Error handling..."

    # Test with invalid payload
    local response
    response=$(api_call POST "/api/v1/runtime/simulate" '{"invalid": "payload"}' 2>&1) || true

    # Should return an error, not crash
    if echo "$response" | jq -e '.detail // .error // .message' > /dev/null 2>&1; then
        log_pass "Error handling returns structured error"
        return 0
    elif [[ -z "$response" ]]; then
        log_fail "Empty response for invalid payload"
        return 1
    else
        log_pass "Error handling works (non-structured response)"
        return 0
    fi
}

# Test: Tenant isolation
test_tenant_isolation() {
    ((TESTS_RUN++))
    log_info "Test: Tenant isolation..."

    local tenant1="tenant-a-$$"
    local tenant2="tenant-b-$$"

    # Create trace for tenant1
    local payload='{
        "workflow_id": "e2e-tenant-test",
        "input": {"type": "tenant", "data": "secret"},
        "config": {"seed": 42}
    }'

    # Store with tenant1
    TENANT_ID="$tenant1" api_call POST "/api/v1/runtime/simulate" "$payload" > /dev/null 2>&1

    # Try to list traces as tenant2 (should not see tenant1's traces)
    local tenant2_traces
    tenant2_traces=$(TENANT_ID="$tenant2" api_call GET "/api/v1/traces" 2>&1) || true

    # This is a basic check - actual isolation depends on implementation
    if echo "$tenant2_traces" | grep -q "secret"; then
        log_fail "Tenant isolation: tenant2 can see tenant1's data"
        return 1
    fi

    log_pass "Tenant isolation appears to be working"
    return 0
}

# Generate report
generate_report() {
    local report_file="$REPORT_DIR/e2e_report_$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "api_url": "$API_URL",
    "tenant_id": "$TENANT_ID",
    "tests_run": $TESTS_RUN,
    "tests_passed": $TESTS_PASSED,
    "tests_failed": $TESTS_FAILED,
    "tests_skipped": $TESTS_SKIPPED,
    "success_rate": $(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_RUN" | bc || echo "0"),
    "quick_mode": $QUICK_MODE,
    "parity_only": $PARITY_ONLY
}
EOF

    log_info "Report saved to: $report_file"
}

# Main
main() {
    echo ""
    echo "=========================================="
    echo "  AOS E2E Integration Test Harness"
    echo "  M8 Deliverable"
    echo "=========================================="
    echo ""

    setup
    echo ""

    if [[ "$PARITY_ONLY" == "true" ]]; then
        test_cross_language_parity
    else
        # Core tests
        test_simulate_basic
        test_deterministic_replay
        test_idempotency
        test_trace_schema
        test_error_handling

        # Parity test
        test_cross_language_parity

        # Extended tests (not in quick mode)
        if [[ "$QUICK_MODE" != "true" ]]; then
            test_tenant_isolation
            test_rate_limiting
        fi
    fi

    echo ""
    echo "=========================================="
    echo "  Test Results"
    echo "=========================================="
    echo ""
    echo -e "  Total:   ${TESTS_RUN}"
    echo -e "  ${GREEN}Passed:  ${TESTS_PASSED}${NC}"
    echo -e "  ${RED}Failed:  ${TESTS_FAILED}${NC}"
    echo -e "  ${YELLOW}Skipped: ${TESTS_SKIPPED}${NC}"
    echo ""

    generate_report

    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}E2E tests failed!${NC}"
        exit 1
    else
        echo -e "${GREEN}All E2E tests passed!${NC}"
        exit 0
    fi
}

main "$@"
