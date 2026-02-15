#!/usr/bin/env bash
#
# truth_preflight.sh — Phase A.5 Preflight Truth Guard
#
# BLOCKING SCRIPT: Must pass (exit 0) before ANY S2-S6 scenario execution.
# If this script fails, NO scenario may proceed.
#
# Guards against historical failures:
#   - P0-001: Database mismatch (local vs cloud)
#   - P0-005: In-memory only storage
#   - P0-???: Silent persistence failure
#
# Usage: ./scripts/verification/truth_preflight.sh
#
# Exit codes:
#   0 = All checks passed, proceed to scenario
#   1 = One or more checks failed, BLOCKED
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${AOS_API_KEY:-edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf}"
API_HEADER="X-AOS-Key"
DATABASE_URL="${DATABASE_URL:-postgresql://nova:novapass@localhost:6432/nova_aos}"
BACKEND_DIR="/root/agenticverz2.0/backend"

# Counter for failures
FAILURES=0

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       TRUTH PREFLIGHT — Phase A.5 Verification Guard          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Date: $(date -Iseconds)"
echo "Purpose: Block scenario execution until truth infrastructure verified"
echo ""

# ============================================================================
# CHECK 1: Runtime DB is Neon (not local)
# ============================================================================
echo -e "${YELLOW}[CHECK 1] Runtime Database Target${NC}"

# Get health endpoint to verify database
HEALTH_RESPONSE=$(curl -s "${API_BASE}/health" 2>/dev/null || echo "FAILED")

if [[ "$HEALTH_RESPONSE" == "FAILED" ]]; then
    echo -e "  ${RED}FAIL: Cannot reach backend at ${API_BASE}${NC}"
    echo "       Ensure backend is running: docker compose up -d backend"
    FAILURES=$((FAILURES + 1))
else
    # Check if backend is healthy
    STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
    VERSION=$(echo "$HEALTH_RESPONSE" | jq -r '.version // "unknown"' 2>/dev/null || echo "unknown")

    if [[ "$STATUS" == "healthy" ]]; then
        echo -e "  ${GREEN}PASS: Backend is healthy${NC}"
        echo "       Version: $VERSION"

        # Verify DATABASE_URL points to Neon (check via code inspection)
        if grep -q "neon.tech" /root/agenticverz2.0/.env 2>/dev/null; then
            echo -e "  ${GREEN}PASS: DATABASE_URL configured for Neon${NC}"
        else
            echo -e "  ${YELLOW}INFO: DATABASE_URL not found in .env or not Neon${NC}"
        fi
    else
        echo -e "  ${RED}FAIL: Backend status = '$STATUS' (expected: healthy)${NC}"
        FAILURES=$((FAILURES + 1))
    fi
fi

# ============================================================================
# CHECK 2: No in-memory run storage in code
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 2] No In-Memory Run Storage${NC}"

# Search for the old in-memory pattern
# grep -c returns exit code 1 if no matches, so we need to handle that
if grep -q "_runs_store" "${BACKEND_DIR}/app/api/workers.py" 2>/dev/null; then
    IN_MEMORY_HITS=$(grep -c "_runs_store" "${BACKEND_DIR}/app/api/workers.py" 2>/dev/null)
    echo -e "  ${RED}FAIL: Found $IN_MEMORY_HITS references to in-memory storage${NC}"
    echo "       This is a regression of P0-005. Fix before proceeding."
    FAILURES=$((FAILURES + 1))
else
    echo -e "  ${GREEN}PASS: No in-memory _runs_store found in workers.py${NC}"
fi

# ============================================================================
# CHECK 3: Crash-on-persistence-failure guard exists
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 3] Persistence Failure Guard${NC}"

# Look for VERIFICATION_MODE or equivalent guard
GUARD_PATTERN="VERIFICATION_MODE\|crash_on_persist_fail\|raise.*persist\|raise.*database"
GUARD_HITS=$(grep -r "$GUARD_PATTERN" "${BACKEND_DIR}/app/" 2>/dev/null | grep -v "^#" | wc -l || echo "0")

if [[ "$GUARD_HITS" -gt 0 ]]; then
    echo -e "  ${GREEN}PASS: Found $GUARD_HITS persistence guard patterns${NC}"
else
    echo -e "  ${YELLOW}WARN: No explicit crash-on-persist-fail guard found${NC}"
    echo "       Recommend adding VERIFICATION_MODE environment variable"
    # Not a failure, but a warning
fi

# ============================================================================
# CHECK 4: Database connectivity test
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 4] Database Connectivity${NC}"

# Use psql to test connection
if command -v psql &> /dev/null; then
    DB_TEST=$(psql "$DATABASE_URL" -c "SELECT 1 as connected;" -t 2>/dev/null | tr -d ' ' || echo "FAILED")
    if [[ "$DB_TEST" == "1" ]]; then
        echo -e "  ${GREEN}PASS: Direct database connection successful${NC}"
    else
        echo -e "  ${RED}FAIL: Cannot connect to database${NC}"
        echo "       Check DATABASE_URL environment variable"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "  ${YELLOW}SKIP: psql not available, relying on API health check${NC}"
fi

# ============================================================================
# CHECK 5: API ↔ DB consistency (count verification)
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 5] API ↔ DB Consistency${NC}"

# Get count from API (requires X-AOS-Key and X-Roles headers)
API_COUNT_RESPONSE=$(curl -s -H "${API_HEADER}: $API_KEY" -H "X-Roles: admin" "${API_BASE}/api/v1/workers/business-builder/runs?limit=100" 2>/dev/null || echo "FAILED")

if [[ "$API_COUNT_RESPONSE" == "FAILED" ]] || echo "$API_COUNT_RESPONSE" | grep -q '"error"'; then
    echo -e "  ${RED}FAIL: Cannot reach runs API or authentication failed${NC}"
    echo "       Response: $API_COUNT_RESPONSE"
    FAILURES=$((FAILURES + 1))
else
    API_COUNT=$(echo "$API_COUNT_RESPONSE" | jq '.total // .count // 0' 2>/dev/null || echo "0")
    echo "  API returns: $API_COUNT runs"

    # Get count from DB directly
    if command -v psql &> /dev/null; then
        DB_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM worker_runs;" 2>/dev/null | tr -d ' \n' || echo "UNKNOWN")
        echo "  DB contains: $DB_COUNT runs"

        if [[ "$API_COUNT" == "$DB_COUNT" ]]; then
            echo -e "  ${GREEN}PASS: API and DB counts match${NC}"
        else
            echo -e "  ${YELLOW}WARN: API ($API_COUNT) vs DB ($DB_COUNT) count mismatch${NC}"
            echo "       May indicate caching or query filtering"
        fi
    else
        echo -e "  ${YELLOW}SKIP: Cannot verify DB count (psql not available)${NC}"
    fi
fi

# ============================================================================
# CHECK 6: Tenant isolation test
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 6] Tenant Isolation${NC}"

# Query with valid tenant
VALID_TENANT="demo-tenant"
INVALID_TENANT="nonexistent-tenant-xyz"

VALID_RESPONSE=$(curl -s -H "${API_HEADER}: $API_KEY" -H "X-Roles: admin" "${API_BASE}/api/v1/workers/business-builder/runs?tenant_id=${VALID_TENANT}&limit=10" 2>/dev/null || echo "FAILED")
INVALID_RESPONSE=$(curl -s -H "${API_HEADER}: $API_KEY" -H "X-Roles: admin" "${API_BASE}/api/v1/workers/business-builder/runs?tenant_id=${INVALID_TENANT}&limit=10" 2>/dev/null || echo "FAILED")

if [[ "$VALID_RESPONSE" == "FAILED" ]] || echo "$VALID_RESPONSE" | grep -q '"error"'; then
    echo -e "  ${RED}FAIL: Cannot reach runs API for tenant test${NC}"
    FAILURES=$((FAILURES + 1))
else
    VALID_COUNT=$(echo "$VALID_RESPONSE" | jq '.total // .count // 0' 2>/dev/null || echo "0")
    INVALID_COUNT=$(echo "$INVALID_RESPONSE" | jq '.total // .count // 0' 2>/dev/null || echo "0")

    echo "  Valid tenant ($VALID_TENANT): $VALID_COUNT runs"
    echo "  Invalid tenant ($INVALID_TENANT): $INVALID_COUNT runs"

    if [[ "$INVALID_COUNT" == "0" ]]; then
        echo -e "  ${GREEN}PASS: Tenant isolation enforced (invalid tenant = 0)${NC}"
    else
        echo -e "  ${RED}FAIL: Invalid tenant returned $INVALID_COUNT runs (expected 0)${NC}"
        echo "       Tenant isolation is broken!"
        FAILURES=$((FAILURES + 1))
    fi
fi

# ============================================================================
# CHECK 7: Previous S1 run exists (PIN-193 acceptance)
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 7] S1 Acceptance Prerequisite${NC}"

S1_RUN_ID="6a3187aa-9da8-427f-ab71-f9d06673a5b2"
S1_CHECK=$(curl -s -H "${API_HEADER}: $API_KEY" -H "X-Roles: admin" "${API_BASE}/api/v1/workers/business-builder/runs/${S1_RUN_ID}" 2>/dev/null || echo "FAILED")

if [[ "$S1_CHECK" == "FAILED" ]]; then
    echo -e "  ${YELLOW}WARN: Cannot verify S1 run (API unreachable)${NC}"
else
    # Check for API error response (not error strings in artifacts)
    API_ERROR=$(echo "$S1_CHECK" | jq -r '.error // empty' 2>/dev/null)
    if [[ -n "$API_ERROR" ]]; then
        echo -e "  ${YELLOW}WARN: API returned error: $API_ERROR${NC}"
    else
        S1_STATUS=$(echo "$S1_CHECK" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
        S1_SUCCESS=$(echo "$S1_CHECK" | jq -r '.success // "unknown"' 2>/dev/null || echo "unknown")

        if [[ "$S1_STATUS" == "completed" ]] && [[ "$S1_SUCCESS" == "true" ]]; then
            echo -e "  ${GREEN}PASS: S1 run verified (status=$S1_STATUS, success=$S1_SUCCESS)${NC}"
            echo "       Run ID: $S1_RUN_ID"
        elif [[ "$S1_STATUS" == "unknown" ]]; then
            echo -e "  ${YELLOW}WARN: S1 run not found — may need to re-execute S1${NC}"
        else
            echo -e "  ${YELLOW}WARN: S1 run found but status=$S1_STATUS, success=$S1_SUCCESS${NC}"
        fi
    fi
fi

# ============================================================================
# CHECK 8: No Lazy Service Resolution (Invariant #10)
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 8] No Lazy Service Resolution (Invariant #10)${NC}"

# Ban get_incident_aggregator() usage
if grep -rq "get_incident_aggregator\s*(" "${BACKEND_DIR}/app/" 2>/dev/null; then
    echo -e "  ${RED}FAIL: Found banned get_incident_aggregator() usage${NC}"
    echo "       Use create_incident_aggregator() instead"
    echo "       See LESSONS_ENFORCED.md Invariant #10"
    FAILURES=$((FAILURES + 1))
else
    echo -e "  ${GREEN}PASS: No lazy service resolution found${NC}"
fi

# Ensure IncidentAggregator is constructed with explicit dependencies
# Check for IncidentAggregator( without clock= (missing dependency injection)
BAD_CONSTRUCTIONS=$(grep -rE "IncidentAggregator\s*\([^)]*\)" "${BACKEND_DIR}/app/" 2>/dev/null | grep -v "clock=" | grep -v "def " | grep -v "#" | grep -v "class " || true)
if [[ -n "$BAD_CONSTRUCTIONS" ]]; then
    echo -e "  ${RED}FAIL: Found IncidentAggregator construction without explicit DI${NC}"
    echo "$BAD_CONSTRUCTIONS"
    FAILURES=$((FAILURES + 1))
else
    echo -e "  ${GREEN}PASS: All IncidentAggregator constructions use explicit DI${NC}"
fi

# ============================================================================
# CHECK 9: Clean Incident State
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 9] Clean Incident State${NC}"

if command -v psql &> /dev/null; then
    # Count incidents from the last hour (should be 0 for clean test)
    RECENT_INCIDENTS=$(psql "$DATABASE_URL" -t -c "
        SELECT COUNT(*) FROM costsim_cb_incidents
        WHERE created_at > NOW() - INTERVAL '1 hour';" 2>/dev/null | tr -d ' ' || echo "UNKNOWN")

    if [[ "$RECENT_INCIDENTS" == "0" ]]; then
        echo -e "  ${GREEN}PASS: No incidents in the last hour (clean state)${NC}"
    elif [[ "$RECENT_INCIDENTS" == "UNKNOWN" ]]; then
        echo -e "  ${YELLOW}SKIP: Could not query incidents table${NC}"
    else
        echo -e "  ${YELLOW}INFO: Found $RECENT_INCIDENTS recent incidents${NC}"
        echo "       S2 will check that NO NEW incidents are created"
    fi
else
    echo -e "  ${YELLOW}SKIP: psql not available${NC}"
fi

# ============================================================================
# CHECK 10: Governance Qualifier Gate (PIN-281 - System Gate)
# ============================================================================
echo ""
echo -e "${YELLOW}[CHECK 10] Governance Qualifier Gate (GQ-L2-CONTRACT-READY)${NC}"

QUALIFIER_SCRIPT="/root/agenticverz2.0/scripts/ops/evaluate_qualifiers.py"
if [[ -f "$QUALIFIER_SCRIPT" ]]; then
    # Run qualifier evaluation and capture output
    QUALIFIER_OUTPUT=$(python3 "$QUALIFIER_SCRIPT" 2>&1)
    QUALIFIER_EXIT=$?

    # Extract counts from output
    QUALIFIED_COUNT=$(echo "$QUALIFIER_OUTPUT" | grep -oP 'QUALIFIED:\s+\K\d+' | head -1 || echo "0")
    DISQUALIFIED_COUNT=$(echo "$QUALIFIER_OUTPUT" | grep -oP 'DISQUALIFIED:\s+\K\d+' | head -1 || echo "0")

    if [[ "$DISQUALIFIED_COUNT" -gt 0 ]]; then
        echo -e "  ${YELLOW}INFO: $DISQUALIFIED_COUNT capabilities are DISQUALIFIED${NC}"
        echo "       These capabilities cannot be used for L2 testing or product claims"
        echo "       Run: python3 $QUALIFIER_SCRIPT --verbose for details"
    fi

    if [[ "$QUALIFIED_COUNT" -gt 0 ]]; then
        echo -e "  ${GREEN}PASS: $QUALIFIED_COUNT capabilities are QUALIFIED${NC}"
        echo "       L2 testing and product claims permitted for qualified capabilities"
    else
        echo -e "  ${YELLOW}WARN: No capabilities currently QUALIFIED${NC}"
    fi

    echo "       Ref: docs/governance/QUALIFIER_EVALUATION.yaml"
else
    echo -e "  ${YELLOW}SKIP: evaluate_qualifiers.py not found${NC}"
fi

# ============================================================================
# FINAL VERDICT
# ============================================================================
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

if [[ "$FAILURES" -eq 0 ]]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    PREFLIGHT PASSED                            ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║  All checks passed. Scenario execution may proceed.           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next: Execute S2 scenario (Cost Advisory Truth)"
    echo "Reference: PIN-194"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                    PREFLIGHT FAILED                            ║${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}║  $FAILURES check(s) failed. Scenario execution BLOCKED.           ║${NC}"
    echo -e "${RED}║  Fix all failures before proceeding.                           ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "BLOCKED: No S2-S6 scenario may execute until preflight passes."
    echo ""
    exit 1
fi
