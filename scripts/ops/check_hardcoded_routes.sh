#!/usr/bin/env bash
# =============================================================================
# Hardcoded Routes Enforcement Script
# =============================================================================
#
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI pipeline / pre-commit
#   Execution: sync
# Role: Enforce routing authority - no hardcoded paths in navigation
# Reference: PIN-352, Routing Authority Model
#
# INVARIANTS:
# - Navigation paths MUST come from @/routing module
# - No string literals for /guard, /overview, /activity, etc. in navigate()
# - No hardcoded paths in Link/href for customer routes
# - Comments and documentation are exempt
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEBSITE_DIR="$REPO_ROOT/website"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "PIN-352: Hardcoded Routes Enforcement Check"
echo "=============================================="

VIOLATIONS=0

# -----------------------------------------------------------------------------
# Check 1: navigate() calls with hardcoded customer paths
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[1/4] Checking navigate() calls...${NC}"

# Patterns to detect (exclude comments and imports)
NAVIGATE_VIOLATIONS=$(grep -rn "navigate(['\`]/guard" "$WEBSITE_DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "^.*//.*navigate" | grep -v "\.d\.ts" || true)
NAVIGATE_VIOLATIONS+=$(grep -rn "navigate(['\`]/overview" "$WEBSITE_DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "^.*//.*navigate" | grep -v "\.d\.ts" || true)
NAVIGATE_VIOLATIONS+=$(grep -rn "navigate(['\`]/activity" "$WEBSITE_DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "^.*//.*navigate" | grep -v "\.d\.ts" || true)
NAVIGATE_VIOLATIONS+=$(grep -rn "navigate(['\`]/incidents" "$WEBSITE_DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "^.*//.*navigate" | grep -v "\.d\.ts" || true)
NAVIGATE_VIOLATIONS+=$(grep -rn "navigate(['\`]/policies" "$WEBSITE_DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "^.*//.*navigate" | grep -v "\.d\.ts" || true)

if [ -n "$NAVIGATE_VIOLATIONS" ]; then
    echo -e "${RED}FAIL: Found hardcoded paths in navigate() calls:${NC}"
    echo "$NAVIGATE_VIOLATIONS"
    VIOLATIONS=$((VIOLATIONS + $(echo "$NAVIGATE_VIOLATIONS" | wc -l)))
else
    echo -e "${GREEN}PASS: No hardcoded paths in navigate() calls${NC}"
fi

# -----------------------------------------------------------------------------
# Check 2: path: literals in breadcrumbs
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[2/4] Checking breadcrumb paths...${NC}"

BREADCRUMB_VIOLATIONS=$(grep -rn "path:\s*['\`]/guard" "$WEBSITE_DIR" --include="*.tsx" 2>/dev/null | grep -v "^.*//.*path" || true)
BREADCRUMB_VIOLATIONS+=$(grep -rn "path:\s*['\`]/overview" "$WEBSITE_DIR" --include="*.tsx" 2>/dev/null | grep -v "^.*//.*path" || true)

if [ -n "$BREADCRUMB_VIOLATIONS" ]; then
    echo -e "${RED}FAIL: Found hardcoded paths in breadcrumbs:${NC}"
    echo "$BREADCRUMB_VIOLATIONS"
    VIOLATIONS=$((VIOLATIONS + $(echo "$BREADCRUMB_VIOLATIONS" | wc -l)))
else
    echo -e "${GREEN}PASS: No hardcoded paths in breadcrumbs${NC}"
fi

# -----------------------------------------------------------------------------
# Check 3: Link to= with hardcoded paths
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[3/4] Checking Link components...${NC}"

LINK_VIOLATIONS=$(grep -rn "to=['\`]/guard" "$WEBSITE_DIR" --include="*.tsx" 2>/dev/null | grep -v "^.*//.*to=" | grep -v "routes/index.tsx" || true)

if [ -n "$LINK_VIOLATIONS" ]; then
    echo -e "${RED}FAIL: Found hardcoded paths in Link components:${NC}"
    echo "$LINK_VIOLATIONS"
    VIOLATIONS=$((VIOLATIONS + $(echo "$LINK_VIOLATIONS" | wc -l)))
else
    echo -e "${GREEN}PASS: No hardcoded paths in Link components${NC}"
fi

# -----------------------------------------------------------------------------
# Check 4: Route definitions (exempt: routes/index.tsx, routing/*.ts)
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[4/4] Checking for @/routing imports in navigation files...${NC}"

# Files that should import from @/routing if they use navigation
NAV_FILES=$(grep -rl "useNavigate\|<Navigate\|<Link" "$WEBSITE_DIR" --include="*.tsx" 2>/dev/null | grep -v "routes/index.tsx" | grep -v "__tests__" | grep -v ".test." || true)

IMPORT_MISSING=0
for file in $NAV_FILES; do
    # Check if file uses CUSTOMER_ROUTES or similar patterns
    if grep -q "navigate(" "$file" && ! grep -q "@/routing\|from.*routing" "$file"; then
        # Check if it actually navigates to customer routes
        if grep -qE "navigate\(['\`]/" "$file"; then
            echo -e "${YELLOW}WARNING: $file uses navigate() but may not import from @/routing${NC}"
            IMPORT_MISSING=$((IMPORT_MISSING + 1))
        fi
    fi
done

if [ $IMPORT_MISSING -eq 0 ]; then
    echo -e "${GREEN}PASS: Navigation files import from @/routing${NC}"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo -e "\n=============================================="
if [ $VIOLATIONS -gt 0 ]; then
    echo -e "${RED}FAILED: $VIOLATIONS hardcoded route violation(s) found${NC}"
    echo ""
    echo "Fix: Import routes from @/routing and use CUSTOMER_ROUTES.* instead of string literals"
    echo "Reference: PIN-352, docs/routing/ROUTING_AUTHORITY.md"
    exit 1
else
    echo -e "${GREEN}PASSED: No hardcoded route violations${NC}"
    echo ""
    echo "All navigation paths correctly use the routing authority module."
    exit 0
fi
