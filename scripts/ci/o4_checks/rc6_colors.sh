#!/usr/bin/env bash
# =============================================================================
# RC-6: Color Token Check
# =============================================================================
# Ensures O4 UI does not use severity colors.
#
# Forbidden:
#   - red, danger, error
#   - yellow, amber, warning
#   - critical severity colors
#
# Allowed:
#   - gray, grey, neutral
#   - light blue
#   - white, black
#
# Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md
# =============================================================================

set -e

echo "=== RC-6: Color Token Check ==="

# Define O4 paths
O4_PATHS=(
    "frontend/src/insights"
    "frontend/src/oversight"
    "frontend/src/components/predictions"
    "frontend/src/components/advisory"
)

# Check if paths exist
EXISTING_PATHS=()
for path in "${O4_PATHS[@]}"; do
    if [ -d "$path" ]; then
        EXISTING_PATHS+=("$path")
    fi
done

if [ ${#EXISTING_PATHS[@]} -eq 0 ]; then
    echo "⚠️  No O4 UI paths exist yet. Skipping check."
    echo "    (This is expected before UI implementation)"
    exit 0
fi

# Forbidden color patterns
# Note: These patterns need to be context-aware to avoid false positives
FORBIDDEN_PATTERNS=(
    "color:.*red"
    "color:.*#ff0000"
    "color:.*#f00"
    "bg-red"
    "text-red"
    "border-red"
    "color:.*yellow"
    "color:.*amber"
    "color:.*#ff9"
    "bg-yellow"
    "bg-amber"
    "text-yellow"
    "text-amber"
    "danger"
    "error-color"
    "warning-color"
    "critical-color"
    "severity-high"
    "severity-critical"
    "priority-urgent"
)

FOUND=0

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    echo "Checking for: '$pattern'"

    MATCHES=$(grep -riE "$pattern" "${EXISTING_PATHS[@]}" 2>/dev/null | \
              grep -vE "\.test\.|\.spec\.|\.md$|// RC-6 allowed|# RC-6 allowed" || true)

    if [ -n "$MATCHES" ]; then
        echo "❌ SEVERITY COLOR DETECTED:"
        echo "$MATCHES"
        FOUND=1
    fi
done

echo ""

if [ $FOUND -eq 1 ]; then
    echo "============================================================"
    echo "❌ RC-6 FAILED: Severity color detected in O4 UI"
    echo "============================================================"
    echo ""
    echo "Fix: Use neutral colors only (gray, light blue, white, black)"
    echo "Allowed Tailwind classes: gray-*, slate-*, blue-100, blue-200"
    exit 1
else
    echo "✅ No severity colors in O4"
    echo ""
    echo "============================================================"
    echo "✅ RC-6 PASSED: Color token compliance verified"
    echo "============================================================"
    exit 0
fi
