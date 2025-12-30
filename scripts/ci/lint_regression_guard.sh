#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Lint regression guard - fail if new errors introduced
# Callers: CI workflow
# Allowed Imports: -
# Forbidden Imports: -
# Reference: docs/contracts/PROTECTIVE_GOVERNANCE_CONTRACT.md

# =============================================================================
# LINT REGRESSION GUARD (Protective Governance)
# =============================================================================
# This script implements the "no-regression" rule for housekeeping.
# It compares current lint error counts against the frozen baseline.
# Any INCREASE in errors fails the build.
#
# Usage:
#   ./scripts/ci/lint_regression_guard.sh
#
# Exit codes:
#   0 - Success (errors <= baseline)
#   1 - Regression detected (errors > baseline)
#   2 - Error running checks
# =============================================================================

set -euo pipefail

# Frozen baseline (captured 2025-12-30)
# These numbers should only DECREASE, never increase
BASELINE_RUFF=164
BASELINE_MYPY=1274  # From mypy.ini quarantine strategy

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "LINT REGRESSION GUARD"
echo "=============================================="
echo ""

cd /root/agenticverz2.0/backend

# Run ruff and count errors
echo "Running ruff check..."
RUFF_OUTPUT=$(ruff check . 2>&1 || true)
RUFF_COUNT=$(echo "$RUFF_OUTPUT" | grep -E "^Found [0-9]+ errors" | grep -oE "[0-9]+" | head -1 || echo "0")
if [ -z "$RUFF_COUNT" ] || [ "$RUFF_COUNT" = "" ]; then
    RUFF_COUNT=0
fi
# Remove any whitespace
RUFF_COUNT=$(echo "$RUFF_COUNT" | tr -d '[:space:]')

# Run mypy and count errors (optional, can be slow)
if [ "${SKIP_MYPY:-false}" != "true" ]; then
    echo "Running mypy..."
    MYPY_OUTPUT=$(cd .. && python3 -m mypy backend/ --config-file mypy.ini 2>&1 || true)
    MYPY_COUNT=$(echo "$MYPY_OUTPUT" | grep -oE "Found [0-9]+ errors" | grep -oE "[0-9]+" | head -1 || echo "0")
    if [ -z "$MYPY_COUNT" ] || [ "$MYPY_COUNT" = "" ]; then
        MYPY_COUNT=0
    fi
    MYPY_COUNT=$(echo "$MYPY_COUNT" | tr -d '[:space:]')
else
    echo "Skipping mypy (SKIP_MYPY=true)"
    MYPY_COUNT=0
fi

echo ""
echo "=============================================="
echo "RESULTS"
echo "=============================================="
echo ""

# Check ruff regression
if [ "$RUFF_COUNT" -gt "$BASELINE_RUFF" ]; then
    echo -e "${RED}REGRESSION:${NC} Ruff errors increased!"
    echo "  Current:  $RUFF_COUNT"
    echo "  Baseline: $BASELINE_RUFF"
    echo "  Delta:    +$((RUFF_COUNT - BASELINE_RUFF))"
    RUFF_PASS=false
elif [ "$RUFF_COUNT" -lt "$BASELINE_RUFF" ]; then
    echo -e "${GREEN}IMPROVEMENT:${NC} Ruff errors decreased!"
    echo "  Current:  $RUFF_COUNT"
    echo "  Baseline: $BASELINE_RUFF"
    echo "  Delta:    -$((BASELINE_RUFF - RUFF_COUNT))"
    echo -e "${YELLOW}NOTE:${NC} Update BASELINE_RUFF to $RUFF_COUNT to lock in improvement"
    RUFF_PASS=true
else
    echo -e "${GREEN}PASS:${NC} Ruff errors at baseline"
    echo "  Current:  $RUFF_COUNT"
    echo "  Baseline: $BASELINE_RUFF"
    RUFF_PASS=true
fi

echo ""

# Check mypy regression (if enabled)
if [ "${SKIP_MYPY:-false}" != "true" ]; then
    if [ "$MYPY_COUNT" -gt "$BASELINE_MYPY" ]; then
        echo -e "${RED}REGRESSION:${NC} Mypy errors increased!"
        echo "  Current:  $MYPY_COUNT"
        echo "  Baseline: $BASELINE_MYPY"
        echo "  Delta:    +$((MYPY_COUNT - BASELINE_MYPY))"
        MYPY_PASS=false
    elif [ "$MYPY_COUNT" -lt "$BASELINE_MYPY" ]; then
        echo -e "${GREEN}IMPROVEMENT:${NC} Mypy errors decreased!"
        echo "  Current:  $MYPY_COUNT"
        echo "  Baseline: $BASELINE_MYPY"
        echo "  Delta:    -$((BASELINE_MYPY - MYPY_COUNT))"
        echo -e "${YELLOW}NOTE:${NC} Update BASELINE_MYPY to $MYPY_COUNT to lock in improvement"
        MYPY_PASS=true
    else
        echo -e "${GREEN}PASS:${NC} Mypy errors at baseline"
        echo "  Current:  $MYPY_COUNT"
        echo "  Baseline: $BASELINE_MYPY"
        MYPY_PASS=true
    fi
else
    MYPY_PASS=true
fi

echo ""

# =============================================================================
# QUARANTINE CEILING CHECK
# =============================================================================
# Counts quarantined modules in mypy.ini to ensure ceiling isn't breached

QUARANTINE_CEILING=15  # Max quarantined modules (15% of ~100 runtime modules)
QUARANTINE_COUNT=$(grep -c "ignore_errors = True" /root/agenticverz2.0/mypy.ini 2>/dev/null || echo "0")
QUARANTINE_COUNT=$(echo "$QUARANTINE_COUNT" | tr -d '[:space:]')

echo "=============================================="
echo "QUARANTINE CEILING"
echo "=============================================="
echo ""

if [ "$QUARANTINE_COUNT" -gt "$QUARANTINE_CEILING" ]; then
    echo -e "${RED}CEILING BREACH:${NC} Too many quarantined modules!"
    echo "  Current:  $QUARANTINE_COUNT"
    echo "  Ceiling:  $QUARANTINE_CEILING"
    echo ""
    echo "To fix: Pay existing debt before adding new quarantines."
    echo "Reference: docs/technical-debt/QUARANTINE_LEDGER.md"
    CEILING_PASS=false
else
    echo -e "${GREEN}PASS:${NC} Quarantine count under ceiling"
    echo "  Current:  $QUARANTINE_COUNT"
    echo "  Ceiling:  $QUARANTINE_CEILING"
    CEILING_PASS=true
fi

echo ""
echo "=============================================="

# Final verdict
if [ "$RUFF_PASS" = true ] && [ "$MYPY_PASS" = true ] && [ "$CEILING_PASS" = true ]; then
    echo -e "${GREEN}PROTECTIVE GOVERNANCE: PASSED${NC}"
    echo ""
    echo "All guards satisfied:"
    echo "  - Ruff monotonicity: PASS"
    echo "  - Mypy monotonicity: PASS"
    echo "  - Quarantine ceiling: PASS"
    exit 0
else
    echo -e "${RED}PROTECTIVE GOVERNANCE: FAILED${NC}"
    echo ""
    echo "To fix:"
    echo "  1. Run: ruff check . --statistics"
    echo "  2. Fix the new errors you introduced"
    echo "  3. Or pay existing debt to make room"
    echo "  4. Re-run this script"
    echo ""
    echo "Reference: docs/contracts/PROTECTIVE_GOVERNANCE_CONTRACT.md"
    exit 1
fi
