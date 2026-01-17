#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Preflight check orchestrator
# Reference: docs/architecture/contracts/PREFLIGHT_CI_CHECKLIST.md

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║               PREFLIGHT CHECKS                             ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Navigate to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

FAILED=0
PASSED=0
SKIPPED=0

run_check() {
    local name=$1
    local cmd=$2
    local required=${3:-true}

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶ Running: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if eval "$cmd"; then
        echo ""
        echo "✓ $name: PASSED"
        ((PASSED++))
    else
        if [ "$required" = true ]; then
            echo ""
            echo "✗ $name: FAILED"
            FAILED=1
        else
            echo ""
            echo "⚠ $name: SKIPPED (optional)"
            ((SKIPPED++))
        fi
    fi
}

# Core contract checks
run_check "Naming Contract" \
    "python3 $SCRIPT_DIR/check_naming_contract.py"

run_check "Migration Lineage" \
    "python3 $SCRIPT_DIR/check_alembic_parent.py --all"

run_check "Runtime/API Boundary" \
    "python3 $SCRIPT_DIR/check_runtime_api_boundary.py"

run_check "Router Wiring" \
    "python3 $SCRIPT_DIR/check_router_registry.py"

# Layer validation (BLCA)
if [ -f "$REPO_ROOT/scripts/ops/layer_validator.py" ]; then
    run_check "Layer Violations (BLCA)" \
        "python3 $REPO_ROOT/scripts/ops/layer_validator.py --backend --ci"
else
    echo ""
    echo "⚠ Layer Violations (BLCA): SKIPPED (layer_validator.py not found)"
    ((SKIPPED++))
fi

# Domain-specific checks
run_check "Activity Domain Contract" \
    "python3 $SCRIPT_DIR/check_activity_domain.py"

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
echo "                       SUMMARY                              "
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Passed:  $PASSED"
echo "  Skipped: $SKIPPED"
echo "  Failed:  $((FAILED > 0 ? 1 : 0))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         ✓ ALL PREFLIGHT CHECKS PASSED                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         ✗ PREFLIGHT CHECKS FAILED                         ║"
    echo "║                                                            ║"
    echo "║   Fix violations before merging.                          ║"
    echo "║   See: docs/architecture/contracts/                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 1
fi
