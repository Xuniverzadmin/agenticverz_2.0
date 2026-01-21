#!/bin/bash
# HTTP Tests for Three-Mode Authority System (PIN-440)
#
# Tests the actual HTTP responses from the backend with different auth headers.

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
ENDPOINT="/api/v1/cus/integrations"

echo "======================================================================"
echo "HTTP THREE-MODE AUTHORITY TEST (PIN-440)"
echo "======================================================================"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Test endpoint: $ENDPOINT"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

run_test() {
    local description="$1"
    local expected_status="$2"
    shift 2
    local curl_args=("$@")

    echo "Testing: $description"
    echo "  Command: curl ${curl_args[*]}"

    # Run curl and capture status code
    HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" "${curl_args[@]}")
    RESPONSE=$(cat /tmp/response.json 2>/dev/null || echo "{}")

    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "  ${GREEN}✅ PASS${NC} - Got HTTP $HTTP_CODE (expected $expected_status)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC} - Got HTTP $HTTP_CODE (expected $expected_status)"
        echo "  Response: $RESPONSE"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

echo "======================================================================"
echo "TEST 1: No Authentication (should fail)"
echo "======================================================================"
run_test "No auth header" "401" \
    "${BACKEND_URL}${ENDPOINT}"

echo "======================================================================"
echo "TEST 2: Sandbox Auth (depends on environment)"
echo "======================================================================"
echo "Note: This will succeed if AOS_MODE=local/test AND CUSTOMER_SANDBOX_ENABLED=true"
echo ""

# Test sandbox auth - expected to fail in current prod environment
HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" \
    -H "X-AOS-Customer-Key: cus_sandbox_demo" \
    "${BACKEND_URL}${ENDPOINT}")

RESPONSE=$(cat /tmp/response.json 2>/dev/null || echo "{}")

echo "Sandbox auth test:"
echo "  HTTP Code: $HTTP_CODE"
echo "  Response: $RESPONSE"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "  ${GREEN}✅ Sandbox auth ACCEPTED${NC} - Environment allows sandbox mode"
elif [ "$HTTP_CODE" = "401" ]; then
    echo -e "  ${YELLOW}⚠️ Sandbox auth REJECTED${NC} - Environment is PROD or sandbox disabled"
else
    echo -e "  ${RED}❓ Unexpected response${NC}"
fi
echo ""

echo "======================================================================"
echo "TEST 3: Machine Auth (X-AOS-Key)"
echo "======================================================================"

# Load API key from env if available
if [ -n "$AOS_API_KEY" ]; then
    run_test "Machine auth with AOS_API_KEY" "200" \
        -H "X-AOS-Key: $AOS_API_KEY" \
        "${BACKEND_URL}${ENDPOINT}"
else
    echo "Skipping machine auth test - AOS_API_KEY not set"
    echo "Set AOS_API_KEY environment variable to test machine auth"
fi
echo ""

echo "======================================================================"
echo "TEST 4: Health Endpoint (PUBLIC - always works)"
echo "======================================================================"
run_test "Health endpoint (no auth needed)" "200" \
    "${BACKEND_URL}/health"

echo "======================================================================"
echo "SUMMARY"
echo "======================================================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

# Check current environment
echo "======================================================================"
echo "CURRENT BACKEND ENVIRONMENT"
echo "======================================================================"
echo "Checking backend env via /health and logs..."

# Try to get environment info from backend if available
HEALTH=$(curl -s "${BACKEND_URL}/health")
echo "Health response: $HEALTH"

echo ""
echo "To enable sandbox mode, restart backend with:"
echo "  AOS_MODE=local CUSTOMER_SANDBOX_ENABLED=true"
echo "Or:"
echo "  AOS_MODE=test CUSTOMER_SANDBOX_ENABLED=true DB_AUTHORITY=neon"
echo ""

if [ $FAILED -gt 0 ]; then
    exit 1
fi
exit 0
