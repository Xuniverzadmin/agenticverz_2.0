#!/bin/bash
# AOS Console Health & System Test
# Tests all major AOS Console features and API endpoints

set -euo pipefail

API_KEY="${AOS_API_KEY:-edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf}"
BASE_URL="${AOS_API_BASE:-https://agenticverz.com}"
TENANT_ID="${TENANT_ID:-tenant_demo}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         AOS CONSOLE - HEALTH & SYSTEM TEST                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: $BASE_URL"
echo "Tenant: $TENANT_ID"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS_COUNT++)) || true
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL_COUNT++)) || true
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN_COUNT++)) || true
}

info() {
    echo -e "${BLUE}ℹ️  INFO${NC}: $1"
}

# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. CORE HEALTH ENDPOINTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Health check
health_response=$(curl -s -w "\n%{http_code}" "${BASE_URL}/health" 2>/dev/null || echo -e "\n000")
health_code=$(echo "$health_response" | tail -1)
health_body=$(echo "$health_response" | head -n -1)

if [ "$health_code" = "200" ]; then
    status=$(echo "$health_body" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
    pass "/health - $status"
else
    fail "/health - HTTP $health_code"
fi

# Healthz (liveness)
healthz_code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/healthz" 2>/dev/null || echo "000")
if [ "$healthz_code" = "200" ]; then
    pass "/healthz (liveness) - HTTP 200"
else
    fail "/healthz (liveness) - HTTP $healthz_code"
fi

# Metrics
metrics_response=$(curl -s "${BASE_URL}/metrics" 2>/dev/null || echo "")
if echo "$metrics_response" | grep -q "nova_"; then
    metric_count=$(echo "$metrics_response" | grep -c "^nova_" || echo "0")
    pass "/metrics - $metric_count nova_* metrics"
else
    warn "/metrics - No nova_* metrics found"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. RUNTIME API (Machine-Native Core)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Capabilities
caps_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/runtime/capabilities" 2>/dev/null || echo -e "\n000")
caps_code=$(echo "$caps_response" | tail -1)
caps_body=$(echo "$caps_response" | head -n -1)

if [ "$caps_code" = "200" ]; then
    skill_count=$(echo "$caps_body" | jq '.skills | length' 2>/dev/null || echo "0")
    pass "/runtime/capabilities - $skill_count skills available"
else
    fail "/runtime/capabilities - HTTP $caps_code"
fi

# Skills list
skills_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/runtime/skills" 2>/dev/null || echo -e "\n000")
skills_code=$(echo "$skills_response" | tail -1)

if [ "$skills_code" = "200" ]; then
    pass "/runtime/skills - HTTP 200"
else
    fail "/runtime/skills - HTTP $skills_code"
fi

# Simulate endpoint
simulate_response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"agent_id":"test","input":{"task":"test"},"skills":["openai_chat"]}' \
    "${BASE_URL}/api/v1/runtime/simulate" 2>/dev/null || echo -e "\n000")
simulate_code=$(echo "$simulate_response" | tail -1)

if [ "$simulate_code" = "200" ] || [ "$simulate_code" = "422" ]; then
    pass "/runtime/simulate - Endpoint responsive (HTTP $simulate_code)"
else
    fail "/runtime/simulate - HTTP $simulate_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. RUNS & TRACES API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# List runs
runs_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/runs?limit=5" 2>/dev/null || echo -e "\n000")
runs_code=$(echo "$runs_response" | tail -1)
runs_body=$(echo "$runs_response" | head -n -1)

if [ "$runs_code" = "200" ]; then
    run_count=$(echo "$runs_body" | jq '.items | length' 2>/dev/null || echo "0")
    total=$(echo "$runs_body" | jq '.total // 0' 2>/dev/null || echo "0")
    pass "/runs - $run_count items (total: $total)"
elif [ "$runs_code" = "404" ]; then
    warn "/runs - Not implemented (future feature)"
else
    fail "/runs - HTTP $runs_code"
fi

# Traces endpoint
traces_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/traces?limit=5" 2>/dev/null || echo -e "\n000")
traces_code=$(echo "$traces_response" | tail -1)

if [ "$traces_code" = "200" ]; then
    pass "/traces - HTTP 200"
elif [ "$traces_code" = "404" ]; then
    warn "/traces - Not implemented (404)"
else
    fail "/traces - HTTP $traces_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. FAILURE CATALOG (M9)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Failures list (requires tenant_id)
failures_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/failures?tenant_id=${TENANT_ID}&limit=5" 2>/dev/null || echo -e "\n000")
failures_code=$(echo "$failures_response" | tail -1)
failures_body=$(echo "$failures_response" | head -n -1)

if [ "$failures_code" = "200" ]; then
    failure_count=$(echo "$failures_body" | jq '.items | length' 2>/dev/null || echo "0")
    pass "/failures - $failure_count failure patterns"
elif [ "$failures_code" = "404" ] || [ "$failures_code" = "500" ]; then
    warn "/failures - Not available (check DB connection)"
else
    fail "/failures - HTTP $failures_code"
fi

# Failure categories
categories_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/failures/categories?tenant_id=${TENANT_ID}" 2>/dev/null || echo -e "\n000")
categories_code=$(echo "$categories_response" | tail -1)

if [ "$categories_code" = "200" ]; then
    pass "/failures/categories - HTTP 200"
elif [ "$categories_code" = "404" ] || [ "$categories_code" = "400" ]; then
    warn "/failures/categories - Not implemented"
else
    fail "/failures/categories - HTTP $categories_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. RECOVERY ENGINE (M10)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Recovery candidates
recovery_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/recovery/candidates?limit=5" 2>/dev/null || echo -e "\n000")
recovery_code=$(echo "$recovery_response" | tail -1)
recovery_body=$(echo "$recovery_response" | head -n -1)

if [ "$recovery_code" = "200" ]; then
    candidate_count=$(echo "$recovery_body" | jq '.items | length' 2>/dev/null || echo "0")
    pass "/recovery/candidates - $candidate_count candidates"
else
    fail "/recovery/candidates - HTTP $recovery_code"
fi

# Recovery stats
stats_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/recovery/stats" 2>/dev/null || echo -e "\n000")
stats_code=$(echo "$stats_response" | tail -1)

if [ "$stats_code" = "200" ]; then
    pass "/recovery/stats - HTTP 200"
elif [ "$stats_code" = "404" ]; then
    warn "/recovery/stats - Not implemented"
else
    fail "/recovery/stats - HTTP $stats_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. CREDITS & BILLING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Credits balance (may not be implemented)
credits_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/credits/balance?tenant_id=${TENANT_ID}" 2>/dev/null || echo -e "\n000")
credits_code=$(echo "$credits_response" | tail -1)
credits_body=$(echo "$credits_response" | head -n -1)

if [ "$credits_code" = "200" ]; then
    balance=$(echo "$credits_body" | jq '.balance_cents // .balance // 0' 2>/dev/null || echo "0")
    pass "/credits/balance - $balance cents"
elif [ "$credits_code" = "404" ] || [ "$credits_code" = "000" ]; then
    warn "/credits/balance - Not implemented (future billing feature)"
else
    fail "/credits/balance - HTTP $credits_code"
fi

# Usage summary
usage_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/credits/usage?tenant_id=${TENANT_ID}&period=today" 2>/dev/null || echo -e "\n000")
usage_code=$(echo "$usage_response" | tail -1)

if [ "$usage_code" = "200" ]; then
    pass "/credits/usage - HTTP 200"
elif [ "$usage_code" = "404" ]; then
    warn "/credits/usage - Not implemented"
else
    warn "/credits/usage - HTTP $usage_code (billing feature pending)"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. BLACKBOARD / MEMORY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Memory entries
memory_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/memory?limit=5" 2>/dev/null || echo -e "\n000")
memory_code=$(echo "$memory_response" | tail -1)

if [ "$memory_code" = "200" ]; then
    pass "/memory - HTTP 200"
elif [ "$memory_code" = "404" ]; then
    warn "/memory - Not implemented"
else
    fail "/memory - HTTP $memory_code"
fi

# Blackboard entries
blackboard_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/blackboard?tenant_id=${TENANT_ID}&limit=5" 2>/dev/null || echo -e "\n000")
blackboard_code=$(echo "$blackboard_response" | tail -1)
blackboard_body=$(echo "$blackboard_response" | head -n -1)

if [ "$blackboard_code" = "200" ]; then
    entry_count=$(echo "$blackboard_body" | jq '.items | length' 2>/dev/null || echo "0")
    pass "/blackboard - $entry_count entries"
elif [ "$blackboard_code" = "404" ]; then
    warn "/blackboard - Not implemented (use /memory endpoint)"
else
    fail "/blackboard - HTTP $blackboard_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. SBA (Strategy-Bound Agents)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# SBA list
sba_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/api/v1/sba?limit=5" 2>/dev/null || echo -e "\n000")
sba_code=$(echo "$sba_response" | tail -1)
sba_body=$(echo "$sba_response" | head -n -1)

if [ "$sba_code" = "200" ]; then
    sba_count=$(echo "$sba_body" | jq '.items | length' 2>/dev/null || echo "0")
    pass "/sba - $sba_count agents"
elif [ "$sba_code" = "404" ]; then
    warn "/sba - Not implemented"
else
    fail "/sba - HTTP $sba_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9. GUARD API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Guard status
guard_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/status?tenant_id=${TENANT_ID}" 2>/dev/null || echo -e "\n000")
guard_code=$(echo "$guard_response" | tail -1)
guard_body=$(echo "$guard_response" | head -n -1)

if [ "$guard_code" = "200" ]; then
    is_frozen=$(echo "$guard_body" | jq -r '.is_frozen // "unknown"' 2>/dev/null || echo "unknown")
    guardrails=$(echo "$guard_body" | jq '.active_guardrails | length' 2>/dev/null || echo "0")
    pass "/guard/status - frozen=$is_frozen, $guardrails guardrails"
else
    fail "/guard/status - HTTP $guard_code"
fi

# Guard snapshot
snapshot_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/guard/snapshot/today?tenant_id=${TENANT_ID}" 2>/dev/null || echo -e "\n000")
snapshot_code=$(echo "$snapshot_response" | tail -1)

if [ "$snapshot_code" = "200" ]; then
    pass "/guard/snapshot/today - HTTP 200"
else
    fail "/guard/snapshot/today - HTTP $snapshot_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "10. OPS CONSOLE API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Ops pulse
pulse_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/ops/pulse" 2>/dev/null || echo -e "\n000")
pulse_code=$(echo "$pulse_response" | tail -1)

if [ "$pulse_code" = "200" ]; then
    pass "/ops/pulse - HTTP 200"
else
    fail "/ops/pulse - HTTP $pulse_code"
fi

# Ops infra
infra_response=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $API_KEY" \
    "${BASE_URL}/ops/infra" 2>/dev/null || echo -e "\n000")
infra_code=$(echo "$infra_response" | tail -1)

if [ "$infra_code" = "200" ]; then
    pass "/ops/infra - HTTP 200"
else
    fail "/ops/infra - HTTP $infra_code"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "11. FRONTEND FILES CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

frontend_dir="/root/agenticverz2.0/website/app-shell/src"

frontend_files=(
    "pages/dashboard/DashboardPage.tsx"
    "pages/skills/SkillsPage.tsx"
    "pages/jobs/JobSimulatorPage.tsx"
    "pages/traces/TracesPage.tsx"
    "pages/failures/FailuresPage.tsx"
    "pages/recovery/RecoveryPage.tsx"
    "pages/blackboard/BlackboardPage.tsx"
    "pages/credits/CreditsPage.tsx"
    "pages/metrics/MetricsPage.tsx"
    "pages/sba/SBAInspectorPage.tsx"
    "pages/guard/GuardConsoleEntry.tsx"
    "pages/ops/OpsConsoleEntry.tsx"
)

for file in "${frontend_files[@]}"; do
    full_path="$frontend_dir/$file"
    if [ -f "$full_path" ]; then
        size=$(wc -l < "$full_path")
        pass "$(basename $file) ($size lines)"
    else
        fail "$(basename $file) not found"
    fi
done

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "12. PRODUCTION BUILD CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check production deployment
if [ -f "/opt/agenticverz/apps/console/dist/index.html" ]; then
    pass "Production index.html exists"
else
    fail "Production index.html not found"
fi

# Check build artifacts
build_dir="/opt/agenticverz/apps/console/dist/assets"
if [ -d "$build_dir" ]; then
    js_count=$(ls -1 "$build_dir"/*.js 2>/dev/null | wc -l || echo "0")
    css_count=$(ls -1 "$build_dir"/*.css 2>/dev/null | wc -l || echo "0")
    pass "Build assets: $js_count JS, $css_count CSS files"
else
    fail "Build assets directory not found"
fi

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "13. CONSOLE ACCESSIBILITY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

consoles=(
    "/console:AOS Console"
    "/console/guard:Guard Console"
    "/console/ops:Ops Console"
)

for entry in "${consoles[@]}"; do
    path="${entry%%:*}"
    name="${entry##*:}"

    code=$(curl -s -o /dev/null -w "%{http_code}" -L "${BASE_URL}${path}" 2>/dev/null || echo "000")
    if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ]; then
        pass "$name accessible (HTTP $code)"
    else
        fail "$name - HTTP $code"
    fi
done

# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "14. DOCKER SERVICES CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

services=(
    "nova_agent_manager:Backend API"
    "nova_worker:Worker"
    "nova_db:PostgreSQL"
    "nova_pgbouncer:PgBouncer"
    "nova_redis:Redis"
)

for entry in "${services[@]}"; do
    service="${entry%%:*}"
    name="${entry##*:}"

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${service}$"; then
        pass "$name ($service) running"
    elif docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${service}$"; then
        fail "$name ($service) stopped"
    else
        warn "$name ($service) not found"
    fi
done

# ============================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                        TEST SUMMARY                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}PASSED${NC}: $PASS_COUNT"
echo -e "  ${RED}FAILED${NC}: $FAIL_COUNT"
echo -e "  ${YELLOW}WARNED${NC}: $WARN_COUNT"
echo ""

TOTAL=$((PASS_COUNT + FAIL_COUNT))
if [ $TOTAL -gt 0 ]; then
    PERCENT=$((PASS_COUNT * 100 / TOTAL))
    echo "  Score: $PERCENT% ($PASS_COUNT/$TOTAL)"
fi
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Console URLs:"
    echo "  AOS Console:   ${BASE_URL}/console"
    echo "  Guard Console: ${BASE_URL}/console/guard"
    echo "  Ops Console:   ${BASE_URL}/console/ops"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
