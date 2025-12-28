#!/bin/bash
# =============================================================================
# C2 Guardrails - Master Runner
# =============================================================================
# Runs all C2 guardrails in sequence. Stops on first BLOCKER failure.
# WARNING-level checks run but don't block.
#
# Reference: PIN-222, C2 Implementation Specification
# Usage: ./run_all.sh [backend_dir] [frontend_dir]
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${1:-/root/agenticverz2.0/backend}"
FRONTEND_DIR="${2:-/root/agenticverz2.0/frontend}"

echo "=============================================="
echo "C2 GUARDRAILS - CI ENFORCEMENT"
echo "=============================================="
echo "Backend: $BACKEND_DIR"
echo "Frontend: $FRONTEND_DIR"
echo "Time: $(date -Iseconds)"
echo ""

# Track results
BLOCKERS_FAILED=0
WARNINGS_COUNT=0

# Function to run a guardrail
run_guardrail() {
    local script="$1"
    local level="$2"
    local name="$(basename "$script" .sh)"

    echo "----------------------------------------------"
    echo "Running: $name ($level)"
    echo "----------------------------------------------"

    if bash "$script" "$BACKEND_DIR" "$FRONTEND_DIR"; then
        echo ""
    else
        if [ "$level" = "BLOCKER" ]; then
            echo ">>> $name FAILED (BLOCKER) <<<"
            BLOCKERS_FAILED=$((BLOCKERS_FAILED + 1))
        else
            echo ">>> $name has warnings (non-blocking) <<<"
            WARNINGS_COUNT=$((WARNINGS_COUNT + 1))
        fi
        echo ""
    fi
}

# Run BLOCKER guardrails (order matters - most critical first)
run_guardrail "$SCRIPT_DIR/gr1_import_isolation.sh" "BLOCKER"
run_guardrail "$SCRIPT_DIR/gr2_advisory_enforcement.sh" "BLOCKER"
run_guardrail "$SCRIPT_DIR/gr3_replay_blindness.sh" "BLOCKER"
run_guardrail "$SCRIPT_DIR/gr5_redis_authority.sh" "BLOCKER"

# Run WARNING guardrails
run_guardrail "$SCRIPT_DIR/gr4_semantic_lint.sh" "WARNING"

# Summary
echo "=============================================="
echo "C2 GUARDRAILS - SUMMARY"
echo "=============================================="

if [ $BLOCKERS_FAILED -gt 0 ]; then
    echo "RESULT: FAILED"
    echo "Blockers failed: $BLOCKERS_FAILED"
    echo "Warnings: $WARNINGS_COUNT"
    echo ""
    echo "CI must not proceed until blockers are resolved."
    exit 1
fi

if [ $WARNINGS_COUNT -gt 0 ]; then
    echo "RESULT: PASSED WITH WARNINGS"
    echo "Warnings: $WARNINGS_COUNT"
    echo ""
    echo "Human review required for warnings before merge."
    exit 0
fi

echo "RESULT: PASSED"
echo "All C2 guardrails passed without issues."
exit 0
