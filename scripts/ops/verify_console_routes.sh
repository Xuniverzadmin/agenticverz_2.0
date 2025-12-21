#!/bin/bash
#
# Console Route Verification Script
#
# Verifies that the console routes are correctly configured:
# - Guard Console: /console/guard (standalone, own auth)
# - Ops Console: /console/ops (standalone, own auth)
# - AOS Console: /console (requires login)
#
# Note: This is an SPA, so all routes return 200 from the server.
# The script checks if the correct entry point components exist in the build.
#
# Usage: ./scripts/ops/verify_console_routes.sh
#

BASE_URL="${BASE_URL:-https://agenticverz.com}"
BUILD_DIR="/root/agenticverz2.0/website/aos-console/console/dist"
ROUTES_FILE="/root/agenticverz2.0/website/aos-console/console/src/routes/index.tsx"
PASS=0
FAIL=0

echo "======================================"
echo "Console Route Verification"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "--- Route Configuration Check ---"
echo ""

# Check 1: GuardConsoleEntry exists in routes
if grep -q "GuardConsoleEntry" "$ROUTES_FILE"; then
    echo -e "${GREEN}[PASS]${NC} GuardConsoleEntry imported in routes"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} GuardConsoleEntry NOT found in routes"
    FAIL=$((FAIL + 1))
fi

# Check 2: OpsConsoleEntry exists in routes
if grep -q "OpsConsoleEntry" "$ROUTES_FILE"; then
    echo -e "${GREEN}[PASS]${NC} OpsConsoleEntry imported in routes"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} OpsConsoleEntry NOT found in routes"
    FAIL=$((FAIL + 1))
fi

# Check 3: /guard route uses GuardConsoleEntry (standalone)
if grep -q 'path="/guard".*GuardConsoleEntry\|GuardConsoleEntry.*path="/guard"' "$ROUTES_FILE" || \
   (grep -q 'path="/guard"' "$ROUTES_FILE" && grep -q "GuardConsoleEntry" "$ROUTES_FILE"); then
    echo -e "${GREEN}[PASS]${NC} /guard uses GuardConsoleEntry (standalone)"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} /guard not properly configured"
    FAIL=$((FAIL + 1))
fi

# Check 4: /ops route uses OpsConsoleEntry (standalone)
if grep -q 'path="/ops".*OpsConsoleEntry\|OpsConsoleEntry.*path="/ops"' "$ROUTES_FILE" || \
   (grep -q 'path="/ops"' "$ROUTES_FILE" && grep -q "OpsConsoleEntry" "$ROUTES_FILE"); then
    echo -e "${GREEN}[PASS]${NC} /ops uses OpsConsoleEntry (standalone)"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} /ops not properly configured"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "--- Build Output Check ---"
echo ""

# Check 5: GuardConsoleEntry chunk exists in build
if ls "$BUILD_DIR/assets/" 2>/dev/null | grep -q "GuardConsoleEntry"; then
    echo -e "${GREEN}[PASS]${NC} GuardConsoleEntry chunk exists in build"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} GuardConsoleEntry chunk NOT found in build"
    echo "       Run: cd website/aos-console/console && npm run build"
    FAIL=$((FAIL + 1))
fi

# Check 6: OpsConsoleEntry chunk exists in build
if ls "$BUILD_DIR/assets/" 2>/dev/null | grep -q "OpsConsoleEntry"; then
    echo -e "${GREEN}[PASS]${NC} OpsConsoleEntry chunk exists in build"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} OpsConsoleEntry chunk NOT found in build"
    echo "       Run: cd website/aos-console/console && npm run build"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "--- HTTP Accessibility Check ---"
echo ""

# Check 7: Guard console is accessible
HTTP_GUARD=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/console/guard")
if [ "$HTTP_GUARD" = "200" ]; then
    echo -e "${GREEN}[PASS]${NC} Guard Console accessible (HTTP $HTTP_GUARD)"
    echo "       URL: $BASE_URL/console/guard"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} Guard Console NOT accessible (HTTP $HTTP_GUARD)"
    FAIL=$((FAIL + 1))
fi

# Check 8: Ops console is accessible
HTTP_OPS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/console/ops")
if [ "$HTTP_OPS" = "200" ]; then
    echo -e "${GREEN}[PASS]${NC} Ops Console accessible (HTTP $HTTP_OPS)"
    echo "       URL: $BASE_URL/console/ops"
    PASS=$((PASS + 1))
else
    echo -e "${RED}[FAIL]${NC} Ops Console NOT accessible (HTTP $HTTP_OPS)"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "======================================"
echo "Summary: $PASS passed, $FAIL failed"
echo "======================================"

if [ $FAIL -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}PREVENTION CHECKLIST:${NC}"
    echo ""
    echo "1. Verify routes in website/aos-console/console/src/routes/index.tsx"
    echo "   - /guard and /ops should be PUBLIC routes (outside ProtectedRoute)"
    echo "   - They should use GuardConsoleEntry and OpsConsoleEntry components"
    echo ""
    echo "2. Verify entry components exist:"
    echo "   - website/aos-console/console/src/pages/guard/GuardConsoleEntry.tsx"
    echo "   - website/aos-console/console/src/pages/ops/OpsConsoleEntry.tsx"
    echo ""
    echo "3. Rebuild and deploy:"
    echo "   cd website/aos-console/console && npm run build"
    echo "   sudo cp -r dist/* /opt/agenticverz/apps/console/dist/"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}All console routes are correctly configured.${NC}"
echo ""
echo "Access URLs:"
echo "  Guard Console: $BASE_URL/console/guard"
echo "  Ops Console:   $BASE_URL/console/ops"
echo "  AOS Console:   $BASE_URL/console (requires login)"
exit 0
