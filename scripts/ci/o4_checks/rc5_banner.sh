#!/usr/bin/env bash
# =============================================================================
# RC-5: Containment Banner Check (FOPS)
# =============================================================================
# Ensures FOPS oversight pages have the required containment banner.
#
# Required text:
#   "Advisory Signals Only"
#   "do not trigger, justify, or recommend"
#   "situational awareness only"
#
# Banner must NOT be dismissable.
#
# Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md
# =============================================================================

set -e

echo "=== RC-5: Containment Banner Check (FOPS) ==="

# Define FOPS oversight paths
FOPS_PATHS=(
    "frontend/src/oversight"
    "frontend/src/fops/oversight"
    "frontend/src/components/oversight"
)

# Check if paths exist
EXISTING_PATHS=()
for path in "${FOPS_PATHS[@]}"; do
    if [ -d "$path" ]; then
        EXISTING_PATHS+=("$path")
    fi
done

if [ ${#EXISTING_PATHS[@]} -eq 0 ]; then
    echo "⚠️  No FOPS oversight paths exist yet. Skipping check."
    echo "    (This is expected before UI implementation)"
    exit 0
fi

# Check for required banner text
echo "Checking for required banner text..."

BANNER_FOUND=0
BANNER_TEXT_1=$(grep -riE "Advisory Signals Only" "${EXISTING_PATHS[@]}" 2>/dev/null || true)
BANNER_TEXT_2=$(grep -riE "do not trigger, justify, or recommend" "${EXISTING_PATHS[@]}" 2>/dev/null || true)
BANNER_TEXT_3=$(grep -riE "situational awareness only" "${EXISTING_PATHS[@]}" 2>/dev/null || true)

if [ -n "$BANNER_TEXT_1" ] && [ -n "$BANNER_TEXT_2" ] && [ -n "$BANNER_TEXT_3" ]; then
    echo "✅ All banner text found"
    BANNER_FOUND=1
else
    echo "❌ Missing banner text:"
    [ -z "$BANNER_TEXT_1" ] && echo "   - 'Advisory Signals Only'"
    [ -z "$BANNER_TEXT_2" ] && echo "   - 'do not trigger, justify, or recommend'"
    [ -z "$BANNER_TEXT_3" ] && echo "   - 'situational awareness only'"
fi

# Check for dismissable patterns (forbidden)
echo ""
echo "Checking for forbidden dismiss handlers..."

DISMISS_FOUND=$(grep -riE "onDismiss|onClose|dismissable|closeable|setShowBanner.*false|hideBanner" \
                "${EXISTING_PATHS[@]}" 2>/dev/null | \
                grep -iE "banner|containment|advisory" || true)

if [ -n "$DISMISS_FOUND" ]; then
    echo "❌ DISMISSABLE BANNER DETECTED:"
    echo "$DISMISS_FOUND"
    echo ""
    echo "============================================================"
    echo "❌ RC-5 FAILED: Containment banner is dismissable"
    echo "============================================================"
    echo ""
    echo "Fix: Banner must be permanent, non-dismissable"
    exit 1
fi

echo "✅ No dismiss handlers found on banner"

if [ $BANNER_FOUND -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "❌ RC-5 FAILED: Missing containment banner text"
    echo "============================================================"
    echo ""
    echo "Required text:"
    echo "  - 'Advisory Signals Only'"
    echo "  - 'do not trigger, justify, or recommend actions'"
    echo "  - 'situational awareness only'"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ RC-5 PASSED: Containment banner compliant"
echo "============================================================"
echo ""
echo "NOTE: Manual verification still required:"
echo "  - Banner is visually at top of page"
echo "  - Banner does not scroll away"
exit 0
