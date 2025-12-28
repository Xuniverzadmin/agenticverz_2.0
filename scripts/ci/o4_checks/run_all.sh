#!/usr/bin/env bash
# =============================================================================
# O4 Re-Certification Checks - Run All
# =============================================================================
# Runs all automated O4 compliance checks.
#
# Usage:
#   ./scripts/ci/o4_checks/run_all.sh
#
# Exit codes:
#   0 = All checks passed
#   1 = One or more checks failed
#
# Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md
# =============================================================================

# Note: Not using set -e because arithmetic expressions can return non-zero

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILED=0
PASSED=0
SKIPPED=0

echo "============================================================"
echo "O4 RE-CERTIFICATION CHECKS"
echo "============================================================"
echo ""
echo "Running all automated checks..."
echo ""

# Run each check
CHECKS=(
    "rc1_language.sh"
    "rc2_routes.sh"
    "rc3_imports.sh"
    "rc4_api.sh"
    "rc5_banner.sh"
    "rc6_colors.sh"
)

for check in "${CHECKS[@]}"; do
    echo ""
    echo "────────────────────────────────────────────────────────────"

    if [ -f "$SCRIPT_DIR/$check" ]; then
        if bash "$SCRIPT_DIR/$check"; then
            PASSED=$((PASSED + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    else
        echo "⚠️  Check not found: $check"
        SKIPPED=$((SKIPPED + 1))
    fi
done

echo ""
echo "============================================================"
echo "O4 RE-CERTIFICATION SUMMARY"
echo "============================================================"
echo ""
echo "PASSED:  $PASSED"
echo "FAILED:  $FAILED"
echo "SKIPPED: $SKIPPED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "============================================================"
    echo "❌ O4 RE-CERTIFICATION FAILED"
    echo "============================================================"
    echo ""
    echo "Fix all failures before proceeding."
    echo "Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md"
    exit 1
else
    echo "============================================================"
    echo "✅ O4 RE-CERTIFICATION PASSED (Automated Checks)"
    echo "============================================================"
    echo ""
    echo "NOTE: Manual checks still required:"
    echo "  - RC-7: Ordering (chronological default)"
    echo "  - RC-8: Human semantic verification"
    echo ""
    echo "Complete manual checklist before deployment."
    exit 0
fi
