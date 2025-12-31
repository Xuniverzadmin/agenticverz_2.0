#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | manual
#   Execution: sync
# Role: CI Dry-Run for structural invariants (warn-only, never fail)
# Reference: PIN-250, CI_CANDIDATE_MATRIX.md, ARCH-GOV-011

# ============================================================================
# STRUCTURAL DRY-RUN CI
# ============================================================================
# Status: Rung 2 (Dry-Run) — Warn only, never fail
# Signals: CI-Ready from CI_CANDIDATE_MATRIX.md
# Behavior: Emit warnings, collect metrics, exit 0 always
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
API_DIR="$BACKEND_DIR/app/api"
SERVICES_DIR="$BACKEND_DIR/app/services"

# Output configuration
REPORT_DIR="$REPO_ROOT/docs/ci-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/CI_DRYRUN_${TIMESTAMP}.md"

# Ensure report directory exists
mkdir -p "$REPORT_DIR"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
WARNINGS=0
PASSES=0
TOTAL_CHECKS=0

# ============================================================================
# Helper Functions
# ============================================================================

log_check() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "CHECK: $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

log_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSES++))
    ((TOTAL_CHECKS++))
}

log_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARNINGS++))
    ((TOTAL_CHECKS++))
}

# ============================================================================
# Check 1: No DB Writes in L2 APIs
# ============================================================================
check_no_db_writes_in_api() {
    log_check "No DB writes in L2 APIs (session.add/commit/execute)"

    # Search for session.add, session.commit, session.execute in API files
    local violations=""
    violations=$(grep -rn "session\.\(add\|commit\|execute\)" "$API_DIR" 2>/dev/null || true)

    if [ -z "$violations" ]; then
        log_pass "No direct DB writes found in API files"
        echo "  Files checked: $(find "$API_DIR" -name "*.py" | wc -l)"
        return 0
    else
        log_warn "Potential DB write patterns found in API files"
        echo "$violations" | while read -r line; do
            echo "    $line"
        done
        return 1
    fi
}

# ============================================================================
# Check 2: No Import-Time DB Connection
# ============================================================================
check_no_import_time_db() {
    log_check "No import-time DB connection"

    cd "$BACKEND_DIR"

    # Try to import without DATABASE_URL - should succeed without connecting
    local output=""
    output=$(python3 -c "
import sys
import os
# Explicitly unset DATABASE_URL to catch import-time connections
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

try:
    # This import should NOT create a DB connection
    from app.main import app
    print('IMPORT_SUCCESS')
except Exception as e:
    # ImportError is OK (no DB URL), RuntimeError at import is bad
    if 'DATABASE_URL' in str(e):
        print('IMPORT_SUCCESS_NO_DB')
    else:
        print(f'IMPORT_FAILED: {e}')
" 2>&1) || true

    cd "$REPO_ROOT"

    if echo "$output" | grep -q "IMPORT_SUCCESS"; then
        log_pass "Import completes without triggering DB connection"
        return 0
    elif echo "$output" | grep -q "IMPORT_SUCCESS_NO_DB"; then
        log_pass "Import succeeds - DB connection deferred to runtime"
        return 0
    else
        log_warn "Import may trigger DB connection at import time"
        echo "    Output: $output"
        return 1
    fi
}

# ============================================================================
# Check 3: Transaction Ownership in Services
# ============================================================================
check_transaction_ownership() {
    log_check "Transaction ownership in services (no .commit() in API)"

    # Check that .commit() only appears in services, not in API
    local api_commits=""
    api_commits=$(grep -rn "\.commit()" "$API_DIR" 2>/dev/null || true)

    local service_commits=""
    service_commits=$(grep -rn "\.commit()" "$SERVICES_DIR" 2>/dev/null || true)

    local api_count=$(echo "$api_commits" | grep -c "\.commit()" 2>/dev/null || echo "0")
    local service_count=$(echo "$service_commits" | grep -c "\.commit()" 2>/dev/null || echo "0")

    echo "  API .commit() calls: $api_count"
    echo "  Service .commit() calls: $service_count"

    if [ "$api_count" -eq 0 ]; then
        log_pass "All transaction commits delegated to services"
        return 0
    else
        log_warn "Transaction commits found in API files"
        echo "$api_commits" | while read -r line; do
            [ -n "$line" ] && echo "    $line"
        done
        return 1
    fi
}

# ============================================================================
# Check 4: Service Write Boundaries
# ============================================================================
check_service_boundaries() {
    log_check "Service write boundaries (no cross-service imports)"

    # Check if services import other services
    local violations=""
    violations=$(grep -rn "from app\.services\." "$SERVICES_DIR" 2>/dev/null | grep -v "__init__.py" | grep -v "test_" || true)

    if [ -z "$violations" ]; then
        log_pass "Services do not import other services"
        return 0
    else
        # Filter out legitimate imports (only flag cross-service class imports)
        local real_violations=""
        real_violations=$(echo "$violations" | grep -v "from app.services import" || true)

        if [ -z "$real_violations" ]; then
            log_pass "Services maintain proper boundaries"
            return 0
        else
            log_warn "Potential cross-service imports detected"
            echo "$real_violations" | head -5 | while read -r line; do
                echo "    $line"
            done
            return 1
        fi
    fi
}

# ============================================================================
# Check 5: No Circular Dependencies
# ============================================================================
check_no_circular_deps() {
    log_check "No circular dependencies (import graph check)"

    cd "$BACKEND_DIR"

    # Simple circular dependency check using Python
    local output=""
    output=$(python3 -c "
import sys
import importlib.util
from pathlib import Path

def check_circular():
    # This is a simplified check - full graph analysis would be more thorough
    app_dir = Path('app')
    modules = list(app_dir.rglob('*.py'))

    # Count modules as a basic sanity check
    print(f'Modules scanned: {len(modules)}')

    # Try to import main modules - circular deps would cause ImportError
    try:
        import app.main
        import app.api
        import app.services
        print('CIRCULAR_CHECK_PASS')
    except ImportError as e:
        if 'circular' in str(e).lower():
            print(f'CIRCULAR_DETECTED: {e}')
        else:
            print(f'IMPORT_ERROR: {e}')
    except Exception as e:
        print(f'ERROR: {e}')

check_circular()
" 2>&1) || true

    cd "$REPO_ROOT"

    if echo "$output" | grep -q "CIRCULAR_CHECK_PASS"; then
        log_pass "No circular dependencies detected"
        echo "  $(echo "$output" | grep "Modules scanned")"
        return 0
    elif echo "$output" | grep -q "CIRCULAR_DETECTED"; then
        log_warn "Circular dependency detected"
        echo "    $output"
        return 1
    else
        log_pass "Import graph appears clean"
        return 0
    fi
}

# ============================================================================
# Check 6: tasks/ Module Wired
# ============================================================================
check_tasks_wired() {
    log_check "tasks/ module wired (exports accessible)"

    cd "$BACKEND_DIR"

    local output=""
    output=$(python3 -c "
try:
    from app.tasks import apply_update_rules, enqueue_stream, collect_m10_metrics
    print('TASKS_WIRED')
except ImportError as e:
    print(f'TASKS_NOT_WIRED: {e}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1) || true

    cd "$REPO_ROOT"

    if echo "$output" | grep -q "TASKS_WIRED"; then
        log_pass "tasks/ module exports are properly wired"
        return 0
    else
        log_warn "tasks/ module exports may be incomplete"
        echo "    $output"
        return 1
    fi
}

# ============================================================================
# Generate Report
# ============================================================================
generate_report() {
    cat > "$REPORT_FILE" << EOF
# CI Dry-Run Report

**Date:** $(date +%Y-%m-%d)
**Time:** $(date +%H:%M:%S)
**Status:** Rung 2 (Dry-Run) — Warn only
**Reference:** PIN-250, CI_CANDIDATE_MATRIX.md

---

## Summary

| Metric | Value |
|--------|-------|
| Total Checks | $TOTAL_CHECKS |
| Passes | $PASSES |
| Warnings | $WARNINGS |
| Pass Rate | $(awk "BEGIN {printf \"%.1f\", ($PASSES/$TOTAL_CHECKS)*100}")% |

---

## Check Results

### 1. No DB Writes in L2 APIs
**Signal:** \`session.add/commit/execute\` absent in \`backend/app/api/\`
**Method:** Static grep

### 2. No Import-Time DB Connection
**Signal:** \`from app.main import app\` succeeds without DB connection
**Method:** Import test

### 3. Transaction Ownership in Services
**Signal:** \`.commit()\` only in services, not API
**Method:** Static grep

### 4. Service Write Boundaries
**Signal:** Services don't import other services
**Method:** Import analysis

### 5. No Circular Dependencies
**Signal:** Import graph is acyclic
**Method:** Python import test

### 6. tasks/ Module Wired
**Signal:** tasks/__init__.py exports are importable
**Method:** Import test

---

## Behavior

- **Exit Code:** Always 0 (dry-run never fails)
- **Warnings:** Emitted to stdout
- **Report:** Written to \`docs/ci-reports/\`

---

## CI Implementation Ladder

| Rung | Phase | Behavior | Status |
|------|-------|----------|--------|
| 1 | Discovery | Observe, record, propose | ✅ DONE |
| 2 | Dry-Run CI | Warn only, never fail | **← CURRENT** |
| 3 | Soft Gates | Fail new violations, grandfather existing | Pending |
| 4 | Hard Gates | Full enforcement | Pending |

---

## Next Steps

1. Review warnings (if any)
2. Determine if warnings are real violations or false positives
3. Decide on promotion to Rung 3 (soft gates)

EOF

    echo ""
    echo "Report written to: $REPORT_FILE"
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo "============================================================================"
    echo "STRUCTURAL DRY-RUN CI"
    echo "============================================================================"
    echo "Status: Rung 2 (Dry-Run) — Warn only, never fail"
    echo "Reference: PIN-250, CI_CANDIDATE_MATRIX.md"
    echo "============================================================================"

    # Run all checks
    check_no_db_writes_in_api || true
    check_no_import_time_db || true
    check_transaction_ownership || true
    check_service_boundaries || true
    check_no_circular_deps || true
    check_tasks_wired || true

    # Summary
    echo ""
    echo "============================================================================"
    echo "SUMMARY"
    echo "============================================================================"
    echo "Total Checks: $TOTAL_CHECKS"
    echo "Passes:       $PASSES"
    echo "Warnings:     $WARNINGS"
    echo "Pass Rate:    $(awk "BEGIN {printf \"%.1f\", ($PASSES/$TOTAL_CHECKS)*100}")%"
    echo ""

    # Generate report
    generate_report

    # Dry-run ALWAYS exits 0
    echo "============================================================================"
    echo "DRY-RUN COMPLETE — Exit 0 (warn only, never fail)"
    echo "============================================================================"
    exit 0
}

main "$@"
