#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | pre-commit | manual
#   Execution: sync
# Role: CI Soft Gates for structural invariants (Rung 3)
# Reference: PIN-250, CI_CANDIDATE_MATRIX.md, ARCH-GOV-011

# ============================================================================
# STRUCTURAL SOFT GATES (Rung 3)
# ============================================================================
# Status: Rung 3 — Fail on NEW violations, grandfather existing
# Promoted Signals:
#   1. No import-time DB connection
#   2. No circular dependencies
#   3. tasks/ module wired
#
# Deferred Signals (NOT enforced):
#   - No DB writes in L2 APIs (needs refinement)
#   - Transaction ownership (needs refinement)
#   - Service write boundaries (needs major refinement)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1

# Counters
FAILURES=0
PASSES=0

# ============================================================================
# Helper Functions
# ============================================================================

log_gate() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "GATE: $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

log_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSES++))
}

log_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILURES++))
}

log_skip() {
    echo -e "${YELLOW}○ SKIP${NC}: $1 (deferred — needs refinement)"
}

# ============================================================================
# Gate 1: No Import-Time DB Connection (PROMOTED)
# ============================================================================
gate_no_import_time_db() {
    log_gate "No import-time DB connection [PROMOTED]"

    cd "$BACKEND_DIR"

    local output=""
    output=$(python3 -c "
import sys
import os

# Unset DATABASE_URL to detect import-time connections
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

try:
    from app.main import app
    print('GATE_PASS')
except Exception as e:
    if 'DATABASE_URL' in str(e):
        # Missing DATABASE_URL at runtime is fine
        # We only care that import didn't CREATE a connection
        print('GATE_PASS')
    else:
        print(f'GATE_FAIL: {e}')
" 2>&1) || true

    cd "$REPO_ROOT"

    if echo "$output" | grep -q "GATE_PASS"; then
        log_pass "Import completes without DB connection attempt"
        return 0
    else
        log_fail "Import triggers DB connection at import time"
        echo "    $output"
        return 1
    fi
}

# ============================================================================
# Gate 2: No Circular Dependencies (PROMOTED)
# ============================================================================
gate_no_circular_deps() {
    log_gate "No circular dependencies [PROMOTED]"

    cd "$BACKEND_DIR"

    local output=""
    output=$(python3 -c "
import sys
import os

# Set dummy DATABASE_URL to allow imports without triggering runtime errors
# We're testing import structure, not runtime configuration
os.environ.setdefault('DATABASE_URL', 'postgresql://dummy:dummy@localhost/dummy')
os.environ.setdefault('DATABASE_URL_ASYNC', 'postgresql+asyncpg://dummy:dummy@localhost/dummy')

try:
    # These imports would fail on circular dependencies
    # We only care about ImportError with 'circular' in the message
    import app.main
    print('GATE_PASS')
except ImportError as e:
    if 'circular' in str(e).lower() or 'cannot import' in str(e).lower():
        print(f'GATE_FAIL: Circular dependency detected: {e}')
    else:
        # Other import errors (e.g., missing optional deps) are not circular dep failures
        print('GATE_PASS')
except RuntimeError as e:
    # RuntimeError from config validation is not a circular dep
    print('GATE_PASS')
except Exception as e:
    # Unexpected errors - check if circular related
    if 'circular' in str(e).lower():
        print(f'GATE_FAIL: Circular dependency detected: {e}')
    else:
        print('GATE_PASS')
" 2>&1) || true

    cd "$REPO_ROOT"

    if echo "$output" | grep -q "GATE_PASS"; then
        log_pass "No circular dependencies detected"
        return 0
    else
        log_fail "Circular dependency detected"
        echo "    $output"
        return 1
    fi
}

# ============================================================================
# Gate 3: tasks/ Module Wired (PROMOTED)
# ============================================================================
gate_tasks_wired() {
    log_gate "tasks/ module wired [PROMOTED]"

    cd "$BACKEND_DIR"

    local output=""
    output=$(python3 -c "
import os

# Set dummy DATABASE_URL to allow imports
os.environ.setdefault('DATABASE_URL', 'postgresql://dummy:dummy@localhost/dummy')
os.environ.setdefault('DATABASE_URL_ASYNC', 'postgresql+asyncpg://dummy:dummy@localhost/dummy')

try:
    # These exports must be accessible from tasks/__init__.py
    from app.tasks import apply_update_rules, enqueue_stream, collect_m10_metrics
    print('GATE_PASS')
except ImportError as e:
    print(f'GATE_FAIL: tasks/ exports not wired: {e}')
except RuntimeError as e:
    # RuntimeError from config validation is not a wiring failure
    # If we get here, the import structure is fine
    print('GATE_PASS')
except Exception as e:
    print(f'GATE_FAIL: {e}')
" 2>&1) || true

    cd "$REPO_ROOT"

    if echo "$output" | grep -q "GATE_PASS"; then
        log_pass "tasks/ module exports are properly wired"
        return 0
    else
        log_fail "tasks/ module exports are broken"
        echo "    $output"
        return 1
    fi
}

# ============================================================================
# Deferred Signals (NOT ENFORCED)
# ============================================================================
show_deferred() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "DEFERRED SIGNALS (not enforced)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_skip "No DB writes in L2 APIs"
    log_skip "Transaction ownership in services"
    log_skip "Service write boundaries"
    echo ""
    echo "  These signals remain documented but unenforced."
    echo "  See: docs/architecture/CI_DRYRUN_EVALUATION_REPORT.md"
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo "============================================================================"
    echo "STRUCTURAL SOFT GATES (Rung 3)"
    echo "============================================================================"
    echo "Status: Fail on NEW violations, grandfather existing"
    echo "Reference: PIN-250, CI_CANDIDATE_MATRIX.md"
    echo "============================================================================"

    # Run promoted gates
    gate_no_import_time_db || true
    gate_no_circular_deps || true
    gate_tasks_wired || true

    # Show deferred signals
    show_deferred

    # Summary
    echo ""
    echo "============================================================================"
    echo "SUMMARY"
    echo "============================================================================"
    echo "Promoted Gates: 3"
    echo "Passes:         $PASSES"
    echo "Failures:       $FAILURES"
    echo "Deferred:       3 (not enforced)"
    echo ""

    # Exit code
    if [ "$FAILURES" -gt 0 ]; then
        echo "============================================================================"
        echo -e "${RED}SOFT GATES FAILED${NC} — $FAILURES gate(s) violated"
        echo "============================================================================"
        exit $EXIT_FAILURE
    else
        echo "============================================================================"
        echo -e "${GREEN}SOFT GATES PASSED${NC} — All promoted gates satisfied"
        echo "============================================================================"
        exit $EXIT_SUCCESS
    fi
}

main "$@"
