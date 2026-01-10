#!/bin/bash
# SDSR E2E Preflight Checks
# Reference: docs/governance/SDSR_E2E_TESTING_PROTOCOL.md
#
# This script performs mandatory pre-checks before any SDSR E2E scenario execution.
# Exit codes:
#   0 = All checks passed
#   1 = SR-1 failed (migration mismatch)
#   2 = SR-2 failed (missing required columns)
#   3 = SR-3 failed (worker container outdated)
#   4 = Environment error (database not reachable, etc.)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=============================================="
echo "SDSR E2E Preflight Checks"
echo "Reference: SDSR_E2E_TESTING_PROTOCOL.md"
echo "=============================================="
echo ""

# Load environment
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
else
    echo -e "${RED}ERROR: .env file not found at $REPO_ROOT/.env${NC}"
    exit 4
fi

# Verify DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL not set${NC}"
    exit 4
fi

# ============================================
# SR-1: Migration Consistency Check
# ============================================
echo "SR-1: Migration Consistency Check"
echo "-------------------------------------------"

# Use canonical Python implementation (no regex parsing of CLI output)
# Reference: backend/scripts/preflight/sr1_migration_check.py
cd "$REPO_ROOT/backend"
if python3 scripts/preflight/sr1_migration_check.py; then
    echo ""
else
    # Python script already printed failure reason
    exit 1
fi

# ============================================
# SR-2: Required Columns Assertion
# ============================================
echo "SR-2: Required Columns Assertion"
echo "-------------------------------------------"

# Use psql to check columns
check_column() {
    local table=$1
    local column=$2

    result=$(psql "$DATABASE_URL" -t -c "
        SELECT column_name FROM information_schema.columns
        WHERE table_name = '$table' AND column_name = '$column'
    " 2>/dev/null | tr -d ' ')

    if [ -z "$result" ]; then
        echo -e "${RED}FAIL: $table.$column missing${NC}"
        return 1
    else
        echo -e "${GREEN}  ✓ $table.$column${NC}"
        return 0
    fi
}

SR2_FAILED=0

echo "Checking: runs"
check_column "runs" "is_synthetic" || SR2_FAILED=1
check_column "runs" "synthetic_scenario_id" || SR2_FAILED=1

echo "Checking: incidents"
check_column "incidents" "source_run_id" || SR2_FAILED=1
check_column "incidents" "is_synthetic" || SR2_FAILED=1
check_column "incidents" "synthetic_scenario_id" || SR2_FAILED=1

echo "Checking: policy_proposals"
check_column "policy_proposals" "status" || SR2_FAILED=1
check_column "policy_proposals" "triggering_feedback_ids" || SR2_FAILED=1

echo "Checking: aos_traces"
check_column "aos_traces" "run_id" || SR2_FAILED=1
check_column "aos_traces" "incident_id" || SR2_FAILED=1
check_column "aos_traces" "is_synthetic" || SR2_FAILED=1
check_column "aos_traces" "synthetic_scenario_id" || SR2_FAILED=1
check_column "aos_traces" "status" || SR2_FAILED=1

echo "Checking: aos_trace_steps"
check_column "aos_trace_steps" "trace_id" || SR2_FAILED=1
check_column "aos_trace_steps" "level" || SR2_FAILED=1
check_column "aos_trace_steps" "source" || SR2_FAILED=1

if [ $SR2_FAILED -eq 1 ]; then
    echo ""
    echo -e "${RED}SR-2 FAILED: Missing required columns${NC}"
    echo "Create a migration to add missing columns before proceeding."
    exit 2
fi

echo -e "${GREEN}PASS: All required columns present${NC}"
echo ""

# ============================================
# SR-3: Worker Version Check (Capability-Based)
# ============================================
echo "SR-3: Worker Version Check"
echo "-------------------------------------------"

cd "$REPO_ROOT"

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}SKIP: Docker not available (running outside container environment)${NC}"
else
    # Check if worker container is running
    WORKER_RUNNING=$(docker compose ps --status running 2>/dev/null | grep -c "worker" || echo "0")

    if [ "$WORKER_RUNNING" -eq 0 ]; then
        echo -e "${YELLOW}WARNING: Worker container not running${NC}"
        echo "Run: docker compose up -d worker"
        # Not a hard failure - worker might be started separately
    else
        # SR-3 Rule: Capability presence must be validated semantically.
        # Path-specific checks are prohibited unless the path is itself contractual.
        # Check for TraceStore integration anywhere in worker code (not path-specific)
        if ! docker compose exec -T worker \
             sh -c 'grep -R "PostgresTraceStore" /app/app/worker >/dev/null 2>&1'; then
            echo -e "${RED}[SR-3 FAIL] TraceStore integration not found in worker code${NC}"
            echo "Rebuild container: docker compose up -d --build worker"
            exit 3
        fi

        echo -e "${GREEN}[SR-3 PASS] TraceStore integration present${NC}"
    fi
fi
echo ""

# ============================================
# Summary
# ============================================
echo "=============================================="
echo -e "${GREEN}ALL PREFLIGHT CHECKS PASSED${NC}"
echo "=============================================="
echo ""
echo "You may proceed with SDSR E2E scenario execution."
echo ""
echo "Next steps:"
echo "  1. Run inject_synthetic.py to set up scenario"
echo "  2. Trigger worker execution"
echo "  3. Verify backend assertions"
echo "  4. Observe UI (read-only)"
echo ""

exit 0
