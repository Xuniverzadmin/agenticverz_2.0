#!/usr/bin/env bash
# =============================================================================
# RC-2: Route Compliance Check
# =============================================================================
# Ensures predictions are only exposed on allowed routes.
#
# Allowed:
#   - /insights/predictions (customer consoles)
#   - /oversight/predictions (FOPS consoles)
#
# Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md
# =============================================================================

set -e

echo "=== RC-2: Route Compliance Check ==="

# Define router paths (adjust for actual frontend structure)
ROUTER_PATHS=(
    "frontend/src/routes"
    "frontend/src/router"
    "frontend/src/app"
)

# Check if paths exist
EXISTING_PATHS=()
for path in "${ROUTER_PATHS[@]}"; do
    if [ -d "$path" ]; then
        EXISTING_PATHS+=("$path")
    fi
done

if [ ${#EXISTING_PATHS[@]} -eq 0 ]; then
    echo "⚠️  No router paths found. Skipping check."
    echo "    (This is expected before UI implementation)"
    exit 0
fi

# Find prediction routes NOT in allowed paths
echo "Scanning for prediction routes..."

FORBIDDEN=$(grep -riE "prediction" "${EXISTING_PATHS[@]}" 2>/dev/null | \
            grep -iE "path|route" | \
            grep -vE "(insights|oversight)" | \
            grep -vE "\.test\.|\.spec\.|\.md$" || true)

if [ -n "$FORBIDDEN" ]; then
    echo "❌ PREDICTIONS ON FORBIDDEN ROUTES:"
    echo "$FORBIDDEN"
    echo ""
    echo "============================================================"
    echo "❌ RC-2 FAILED: Predictions exposed on forbidden route"
    echo "============================================================"
    echo ""
    echo "Allowed routes:"
    echo "  - /insights/predictions (customer)"
    echo "  - /oversight/predictions (FOPS)"
    exit 1
else
    echo "✅ No predictions on forbidden routes"
    echo ""
    echo "============================================================"
    echo "✅ RC-2 PASSED: Route compliance verified"
    echo "============================================================"
    exit 0
fi
