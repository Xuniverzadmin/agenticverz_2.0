#!/bin/bash
# Guard Console Health & Prevention System Test
# Tests all detection and prevention mechanisms

set -e

API_KEY="edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf"
BASE_URL="https://agenticverz.com"
TENANT_ID="tenant_demo"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     GUARD CONSOLE - HEALTH & PREVENTION SYSTEM TEST          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. ENDPOINT HEALTH CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

endpoints=(
    "/guard/status"
    "/guard/snapshot/today"
    "/guard/incidents"
)

for endpoint in "${endpoints[@]}"; do
    response=$(curl -s -w "\n%{http_code}\n%{time_total}" \
        -H "X-API-Key: $API_KEY" \
        "${BASE_URL}${endpoint}?tenant_id=${TENANT_ID}")

    http_code=$(echo "$response" | tail -2 | head -1)
    time_total=$(echo "$response" | tail -1)

    if [ "$http_code" = "200" ]; then
        pass "$endpoint - HTTP $http_code (${time_total}s)"
    else
        fail "$endpoint - HTTP $http_code"
    fi
done

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. CIRCUIT BREAKER SIMULATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test with invalid endpoint (should fail gracefully)
echo "Testing circuit breaker with invalid endpoint..."
invalid_response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/nonexistent?tenant_id=${TENANT_ID}")

if [ "$invalid_response" = "404" ] || [ "$invalid_response" = "422" ]; then
    pass "Invalid endpoint returns expected error ($invalid_response)"
else
    warn "Unexpected response for invalid endpoint: $invalid_response"
fi

# Test with missing tenant_id (should fail with 422)
missing_tenant=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/status")

if [ "$missing_tenant" = "422" ]; then
    pass "Missing tenant_id correctly returns 422"
else
    fail "Missing tenant_id should return 422, got $missing_tenant"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. API RESPONSE VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test status response structure
status_response=$(curl -s -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/status?tenant_id=${TENANT_ID}")

# Check if is_frozen exists (value can be true or false)
if echo "$status_response" | jq -e 'has("is_frozen")' > /dev/null 2>&1; then
    is_frozen=$(echo "$status_response" | jq -r '.is_frozen')
    pass "Status response has 'is_frozen' field (value: $is_frozen)"
else
    fail "Status response missing 'is_frozen' field"
fi

if echo "$status_response" | jq -e '.active_guardrails' > /dev/null 2>&1; then
    guardrail_count=$(echo "$status_response" | jq '.active_guardrails | length')
    pass "Status has $guardrail_count active guardrails"
else
    fail "Status response missing 'active_guardrails' field"
fi

# Test snapshot response structure
snapshot_response=$(curl -s -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/snapshot/today?tenant_id=${TENANT_ID}")

if echo "$snapshot_response" | jq -e '.requests_today' > /dev/null 2>&1; then
    pass "Snapshot response has 'requests_today' field"
else
    fail "Snapshot response missing 'requests_today' field"
fi

if echo "$snapshot_response" | jq -e '.incidents_prevented' > /dev/null 2>&1; then
    incidents=$(echo "$snapshot_response" | jq '.incidents_prevented')
    pass "Snapshot shows $incidents incidents prevented"
else
    fail "Snapshot response missing 'incidents_prevented' field"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. DEMO INCIDENT SEEDING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

seed_response=$(curl -s -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"scenario":"prompt_injection"}' \
    "${BASE_URL}/guard/demo/seed-incident?tenant_id=${TENANT_ID}")

if echo "$seed_response" | jq -e '.incident_id' > /dev/null 2>&1; then
    incident_id=$(echo "$seed_response" | jq -r '.incident_id')
    pass "Demo incident created: $incident_id"
else
    fail "Failed to seed demo incident"
    echo "$seed_response" | jq .
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. INCIDENTS LIST CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

incidents_response=$(curl -s -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/incidents?tenant_id=${TENANT_ID}&limit=5")

if echo "$incidents_response" | jq -e '.items' > /dev/null 2>&1; then
    incident_count=$(echo "$incidents_response" | jq '.items | length')
    total=$(echo "$incidents_response" | jq '.total')
    pass "Incidents list returned $incident_count items (total: $total)"
else
    fail "Failed to fetch incidents list"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. PDF EXPORT TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get a valid incident ID first
incidents_for_export=$(curl -s -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/incidents?tenant_id=${TENANT_ID}&limit=1")
export_incident_id=$(echo "$incidents_for_export" | jq -r '.items[0].id // empty')

if [ -n "$export_incident_id" ]; then
    export_response=$(curl -s -o /tmp/guard_export_test.pdf -w "%{http_code}" -X POST \
        -H "X-API-Key: $API_KEY" \
        "${BASE_URL}/guard/incidents/${export_incident_id}/export?tenant_id=${TENANT_ID}&is_demo=true")

    if [ "$export_response" = "200" ]; then
        file_type=$(file /tmp/guard_export_test.pdf | grep -c "PDF document")
        if [ "$file_type" -gt 0 ]; then
            pass "PDF export works (incident: $export_incident_id)"
        else
            fail "PDF export returned 200 but file is not valid PDF"
        fi
    else
        fail "PDF export failed with HTTP $export_response"
    fi
else
    warn "No incidents available for PDF export test"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. PYTHON DEPENDENCY CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check critical Python imports in container
critical_imports=(
    "reportlab"
    "app.services.evidence_report"
    "app.api.guard"
)

for module in "${critical_imports[@]}"; do
    if docker exec nova_agent_manager python3 -c "import $module" 2>/dev/null; then
        pass "Python module '$module' importable"
    else
        fail "Python module '$module' NOT importable - missing dependency!"
    fi
done

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. FRONTEND FILES CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

frontend_files=(
    "/root/agenticverz2.0/website/app-shell/src/lib/healthCheck.ts"
    "/root/agenticverz2.0/website/app-shell/src/components/ErrorBoundary.tsx"
    "/root/agenticverz2.0/website/app-shell/src/components/HealthIndicator.tsx"
    "/root/agenticverz2.0/website/app-shell/src/pages/guard/GuardDashboard.tsx"
)

for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        size=$(wc -l < "$file")
        pass "$(basename $file) exists ($size lines)"
    else
        fail "$(basename $file) not found"
    fi
done

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9. PRODUCTION DEPLOYMENT CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "/opt/agenticverz/apps/console/dist/index.html" ]; then
    pass "Production index.html exists"
else
    fail "Production index.html not found"
fi

console_response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/console/guard")
if [ "$console_response" = "200" ]; then
    pass "Console page accessible (HTTP $console_response)"
else
    fail "Console page not accessible (HTTP $console_response)"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "10. APACHE PROXY CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if grep -q "/guard" /etc/apache2/sites-enabled/agenticverz.com.conf 2>/dev/null; then
    pass "Apache has /guard proxy route configured"
else
    fail "Apache missing /guard proxy route"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "11. BROWSER SIMULATION TEST (CLI vs Browser)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test CORS preflight (simulates browser OPTIONS request)
echo "Testing CORS preflight requests..."
for endpoint in "/guard/status" "/guard/snapshot/today" "/guard/incidents"; do
    cors_response=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
        -H "Origin: https://agenticverz.com" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: X-API-Key,Content-Type" \
        "${BASE_URL}${endpoint}?tenant_id=${TENANT_ID}" 2>/dev/null)

    if [ "$cors_response" = "200" ]; then
        pass "CORS preflight $endpoint - HTTP 200"
    else
        fail "CORS preflight $endpoint - HTTP $cors_response (browser requests will fail!)"
    fi
done

# Test with Origin header (simulates browser request)
echo ""
echo "Testing browser-like requests with Origin header..."
for endpoint in "/guard/status" "/guard/snapshot/today"; do
    browser_response=$(curl -s -w "\n%{http_code}" \
        -H "X-API-Key: $API_KEY" \
        -H "Origin: https://agenticverz.com" \
        -H "Referer: https://agenticverz.com/console/guard" \
        "${BASE_URL}${endpoint}?tenant_id=${TENANT_ID}" 2>/dev/null)

    browser_code=$(echo "$browser_response" | tail -1)

    if [ "$browser_code" = "200" ]; then
        pass "Browser request $endpoint - HTTP 200"
    else
        fail "Browser request $endpoint - HTTP $browser_code (works in CLI but fails in browser!)"
    fi
done

# Test CORS response headers are present
echo ""
echo "Verifying CORS response headers..."
cors_headers=$(curl -s -I -H "X-API-Key: $API_KEY" -H "Origin: https://agenticverz.com" \
    "${BASE_URL}/guard/status?tenant_id=${TENANT_ID}" 2>/dev/null)

if echo "$cors_headers" | grep -qi "access-control-allow-origin"; then
    pass "CORS Access-Control-Allow-Origin header present"
else
    fail "Missing Access-Control-Allow-Origin header (browser CORS error!)"
fi

if echo "$cors_headers" | grep -qi "access-control-allow-credentials"; then
    pass "CORS Access-Control-Allow-Credentials header present"
else
    warn "Missing Access-Control-Allow-Credentials header"
fi

# Test without API key (simulates unauthenticated browser state)
echo ""
echo "Testing unauthenticated requests (simulates browser before login)..."
unauth_response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: https://agenticverz.com" \
    "${BASE_URL}/guard/status?tenant_id=${TENANT_ID}" 2>/dev/null)

# Should return 200 (demo mode) or 401/403 (auth required) - not 500
if [ "$unauth_response" = "200" ] || [ "$unauth_response" = "401" ] || [ "$unauth_response" = "403" ]; then
    pass "Unauthenticated request handled gracefully (HTTP $unauth_response)"
else
    fail "Unauthenticated request returns unexpected HTTP $unauth_response (potential browser error source!)"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "12. FRONTEND INITIALIZATION CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check that health check waits for auth
if grep -q "isAuthenticated" /root/agenticverz2.0/website/app-shell/src/pages/guard/GuardLayout.tsx 2>/dev/null; then
    pass "GuardLayout checks authentication before health monitor"
else
    fail "GuardLayout may start health monitor before auth (causes circuit breaker errors!)"
fi

# Check for timing delays in health monitor startup
if grep -q "setTimeout\|delay" /root/agenticverz2.0/website/app-shell/src/pages/guard/GuardLayout.tsx 2>/dev/null; then
    pass "Health monitor has startup delay for auth propagation"
else
    warn "No explicit delay in health monitor startup (potential race condition)"
fi

# Check for duplicate health monitor starts
dashboard_health=$(grep -c "startPeriodicCheck" /root/agenticverz2.0/website/app-shell/src/pages/guard/GuardDashboard.tsx 2>/dev/null | head -1 || echo "0")
layout_health=$(grep -c "startPeriodicCheck" /root/agenticverz2.0/website/app-shell/src/pages/guard/GuardLayout.tsx 2>/dev/null | head -1 || echo "0")

# Ensure we have valid integers
dashboard_health=${dashboard_health:-0}
layout_health=${layout_health:-0}

if [ "$dashboard_health" -eq 0 ] 2>/dev/null && [ "$layout_health" -gt 0 ] 2>/dev/null; then
    pass "Health monitor started only in GuardLayout (no duplicates)"
elif [ "$dashboard_health" -gt 0 ] 2>/dev/null && [ "$layout_health" -gt 0 ] 2>/dev/null; then
    fail "Health monitor started in both GuardLayout and GuardDashboard (duplicate starts!)"
else
    warn "Health monitor configuration unclear (dashboard: $dashboard_health, layout: $layout_health)"
fi

# Check API client has auth interceptor
if grep -q "X-API-Key\|Authorization" /root/agenticverz2.0/website/app-shell/src/api/client.ts 2>/dev/null; then
    pass "API client has authentication interceptor"
else
    fail "API client missing authentication interceptor (browser requests will be unauthenticated!)"
fi

# ============================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                        TEST SUMMARY                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}PASSED${NC}: $PASS_COUNT"
echo -e "  ${RED}FAILED${NC}: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Console URL: https://agenticverz.com/console/guard"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
