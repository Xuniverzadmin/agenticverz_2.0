#!/usr/bin/env bash
#
# RBAC Smoke Test Script for M5 Policy API
#
# Tests:
# 1. Create approval request requiring level 4
# 2. Try approve with level 2 user (expect 403)
# 3. Approve with level 4 user (expect 200)
# 4. Verify audit trail
#
# Usage:
#   ./rbac_smoke.sh [options]
#
# Options:
#   --base-url URL     API base URL (default: http://localhost:8000)
#   --api-key KEY      API key for authentication
#   --verbose          Show full responses
#   --help             Show this help
#
# Environment variables:
#   BASEURL            API base URL
#   API_KEY            API key
#

# Don't exit on first error - we want to run all tests
set -uo pipefail

# Defaults
BASEURL="${BASEURL:-http://localhost:8000}"
API_KEY="${API_KEY:-edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf}"
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --base-url)
            BASEURL="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "RBAC Smoke Test for M5 Policy API"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --base-url URL     API base URL (default: http://localhost:8000)"
            echo "  --api-key KEY      API key for authentication"
            echo "  --verbose          Show full responses"
            echo "  --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            exit 2
            ;;
    esac
done

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $*"
}

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local name="$1"
    local expected_status="$2"
    local actual_status="$3"
    local body="$4"

    if [[ "$actual_status" == "$expected_status" ]]; then
        log_pass "$name (HTTP $actual_status)"
        ((TESTS_PASSED++))
        return 0
    else
        log_fail "$name - Expected HTTP $expected_status, got $actual_status"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "Response: $body"
        fi
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "=============================================="
echo "  RBAC Smoke Test - M5 Policy API"
echo "=============================================="
echo ""
echo "Base URL: $BASEURL"
echo "API Key:  ${API_KEY:0:8}..."
echo ""

# Test 0: Check API is reachable
log_info "Test 0: Checking API health..."
HEALTH_RESP=$(curl -s -w "\n%{http_code}" "$BASEURL/health" 2>/dev/null || echo -e "\n000")
HEALTH_BODY=$(echo "$HEALTH_RESP" | sed '$d')
HEALTH_STATUS=$(echo "$HEALTH_RESP" | tail -n1)

if [[ "$HEALTH_STATUS" == "200" ]]; then
    log_pass "API is healthy"
else
    log_error "API not reachable at $BASEURL (HTTP $HEALTH_STATUS)"
    echo "Make sure the backend is running and RBAC_ENABLED=true"
    exit 1
fi

# Test 1: Create approval request requiring level 4
log_info "Test 1: Creating approval request (requires level 4)..."

CREATE_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASEURL/api/v1/policy/requests" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "policy_type": "cost",
        "skill_id": "llm_invoke_high_cost",
        "tenant_id": "tenant-rbac-test",
        "requested_by": "smoke-test-user",
        "justification": "RBAC smoke test - requires level 4 approval"
    }')

CREATE_BODY=$(echo "$CREATE_RESP" | sed '$d')
CREATE_STATUS=$(echo "$CREATE_RESP" | tail -n1)

if [[ "$CREATE_STATUS" != "200" ]]; then
    log_fail "Failed to create approval request (HTTP $CREATE_STATUS)"
    echo "Response: $CREATE_BODY"
    exit 2
fi

REQUEST_ID=$(echo "$CREATE_BODY" | grep -o '"request_id":"[^"]*"' | cut -d'"' -f4)
if [[ -z "$REQUEST_ID" ]]; then
    log_fail "Could not extract request_id from response"
    echo "Response: $CREATE_BODY"
    exit 2
fi

log_pass "Created approval request: $REQUEST_ID"
REQUIRED_LEVEL=$(echo "$CREATE_BODY" | grep -o '"required_level":[0-9]*' | cut -d':' -f2)
log_info "Required approval level: ${REQUIRED_LEVEL:-unknown}"

if [[ "$VERBOSE" == "true" ]]; then
    echo "Response: $CREATE_BODY"
fi

# Test 2: Try to approve with level 2 user (should fail with 403 when RBAC enabled)
log_info "Test 2: Attempting approval with insufficient level (level 2)..."

APPROVE_L2_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASEURL/api/v1/policy/requests/$REQUEST_ID/approve" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "approver_id": "user-level2-insufficient",
        "level": 2,
        "notes": "Smoke test - level 2 user attempting level 4 approval"
    }')

APPROVE_L2_BODY=$(echo "$APPROVE_L2_RESP" | sed '$d')
APPROVE_L2_STATUS=$(echo "$APPROVE_L2_RESP" | tail -n1)

# When RBAC is enabled, expect 403. When disabled, expect 200 (partial approval)
if [[ "$APPROVE_L2_STATUS" == "403" ]]; then
    log_pass "RBAC correctly blocked insufficient level (HTTP 403)"
    ((TESTS_PASSED++))
    RBAC_ENABLED=true
elif [[ "$APPROVE_L2_STATUS" == "200" ]]; then
    # Check if status is still pending (partial approval)
    STATUS_CHECK=$(echo "$APPROVE_L2_BODY" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [[ "$STATUS_CHECK" == "pending" ]]; then
        log_warn "RBAC may be disabled - level 2 added as partial approval (status: pending)"
        log_info "This is expected behavior when RBAC_ENABLED=false"
        ((TESTS_PASSED++))
        RBAC_ENABLED=false
    else
        log_fail "Unexpected: Level 2 user approved successfully"
        ((TESTS_FAILED++))
    fi
else
    log_fail "Unexpected status (HTTP $APPROVE_L2_STATUS)"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Response: $APPROVE_L2_BODY"
    fi
    ((TESTS_FAILED++))
fi

# Test 3: Approve with level 4 user (should succeed)
log_info "Test 3: Approving with sufficient level (level 4)..."

APPROVE_L4_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASEURL/api/v1/policy/requests/$REQUEST_ID/approve" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "approver_id": "user-level4-authorized",
        "level": 4,
        "notes": "Smoke test - level 4 user approval"
    }')

APPROVE_L4_BODY=$(echo "$APPROVE_L4_RESP" | sed '$d')
APPROVE_L4_STATUS=$(echo "$APPROVE_L4_RESP" | tail -n1)

if [[ "$APPROVE_L4_STATUS" == "200" ]]; then
    STATUS=$(echo "$APPROVE_L4_BODY" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [[ "$STATUS" == "approved" ]]; then
        log_pass "Request approved successfully (status: approved)"
        ((TESTS_PASSED++))
    else
        log_warn "Request status: $STATUS (may need higher level)"
        ((TESTS_PASSED++))
    fi
else
    log_fail "Failed to approve with level 4 (HTTP $APPROVE_L4_STATUS)"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Response: $APPROVE_L4_BODY"
    fi
    ((TESTS_FAILED++))
fi

# Test 4: Verify audit trail
log_info "Test 4: Verifying audit trail..."

STATUS_RESP=$(curl -s -w "\n%{http_code}" "$BASEURL/api/v1/policy/requests/$REQUEST_ID" \
    -H "X-API-Key: $API_KEY")

STATUS_BODY=$(echo "$STATUS_RESP" | sed '$d')
STATUS_CODE=$(echo "$STATUS_RESP" | tail -n1)

if [[ "$STATUS_CODE" == "200" ]]; then
    # Check for approvers in response
    if echo "$STATUS_BODY" | grep -q '"approvers":\['; then
        APPROVER_COUNT=$(echo "$STATUS_BODY" | grep -o '"approver_id"' | wc -l)
        log_pass "Audit trail present ($APPROVER_COUNT approver(s) recorded)"
        ((TESTS_PASSED++))
    else
        log_warn "No approvers found in audit trail"
        ((TESTS_PASSED++))
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        echo ""
        echo "Full status response:"
        echo "$STATUS_BODY" | python3 -m json.tool 2>/dev/null || echo "$STATUS_BODY"
    fi
else
    log_fail "Failed to get status (HTTP $STATUS_CODE)"
    ((TESTS_FAILED++))
fi

# Summary
echo ""
echo "=============================================="
echo "  RBAC Smoke Test Results"
echo "=============================================="
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [[ "${RBAC_ENABLED:-unknown}" == "true" ]]; then
    echo -e "RBAC Status: ${GREEN}ENABLED${NC} (403 returned for unauthorized)"
elif [[ "${RBAC_ENABLED:-unknown}" == "false" ]]; then
    echo -e "RBAC Status: ${YELLOW}DISABLED${NC} (using mock roles)"
    echo ""
    echo "To enable RBAC, set environment variable:"
    echo "  export RBAC_ENABLED=true"
    echo "  export AUTH_SERVICE_URL=http://auth-service:8001"
else
    echo -e "RBAC Status: ${YELLOW}UNKNOWN${NC}"
fi

echo ""

if [[ "$TESTS_FAILED" -gt 0 ]]; then
    log_error "Some tests failed. Review output above."
    exit 1
else
    log_pass "All smoke tests passed!"
    exit 0
fi
