#!/usr/bin/env bash
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: developer (manual, with approval)
#   Execution: sync
# Role: Promote preflight console to production with governance gates
# Reference: docs/governance/PREFLIGHT_PROMOTION_CHECKPOINT.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_SHELL="$REPO_ROOT/website/app-shell"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
VALIDATE_ONLY=false
ROLLBACK=false
SKIP_APPROVAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --validate)
            VALIDATE_ONLY=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --skip-approval)
            SKIP_APPROVAL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--validate] [--rollback] [--skip-approval]"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Preflight → Production Promotion"
echo "=========================================="
echo ""

# Rollback mode
if [ "$ROLLBACK" = true ]; then
    echo -e "${YELLOW}ROLLBACK MODE${NC}"
    if [ -d "$APP_SHELL/dist-backup" ]; then
        rm -rf "$APP_SHELL/dist"
        mv "$APP_SHELL/dist-backup" "$APP_SHELL/dist"
        echo -e "${GREEN}ROLLBACK COMPLETE${NC}"
        echo "Restored previous production build from backup."
        exit 0
    else
        echo -e "${RED}ERROR: No backup found at $APP_SHELL/dist-backup${NC}"
        exit 1
    fi
fi

# Track gate results
GATES_PASSED=0
GATES_TOTAL=7

gate_result() {
    local gate=$1
    local status=$2
    local message=$3

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ GATE-$gate: PASS${NC} - $message"
        ((GATES_PASSED++))
    else
        echo -e "${RED}✗ GATE-$gate: BLOCKED${NC} - $message"
    fi
}

echo "Running governance gates..."
echo ""

# ============================================================================
# GATE 1: Pipeline Integrity
# ============================================================================
echo "GATE-1: Pipeline Integrity"
if python3 "$REPO_ROOT/scripts/ci/validate_projection_lock.py" --skip-regenerate > /dev/null 2>&1; then
    gate_result 1 "PASS" "Projection lock schema valid"
else
    gate_result 1 "BLOCKED" "Projection lock validation failed"
fi

# ============================================================================
# GATE 2: Preflight Build Exists
# ============================================================================
echo ""
echo "GATE-2: Preflight Build Exists"
if [ -d "$APP_SHELL/dist-preflight" ] && [ -f "$APP_SHELL/dist-preflight/index.html" ]; then
    gate_result 2 "PASS" "Preflight build found"
else
    gate_result 2 "BLOCKED" "No preflight build. Run ./scripts/ops/build_preflight_console.sh first"
fi

# ============================================================================
# GATE 3: Preflight Accessibility
# ============================================================================
echo ""
echo "GATE-3: Preflight Accessibility"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://preflight-console.agenticverz.com 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    gate_result 3 "PASS" "Preflight console accessible (HTTP 200)"
elif [ "$HTTP_STATUS" = "000" ]; then
    gate_result 3 "BLOCKED" "Preflight console not reachable (DNS or Apache not configured)"
else
    gate_result 3 "BLOCKED" "Preflight console returned HTTP $HTTP_STATUS"
fi

# ============================================================================
# GATE 4: Domain/Panel Integrity
# ============================================================================
echo ""
echo "GATE-4: Domain/Panel Integrity"
DOMAIN_COUNT=$(jq '._statistics.domain_count' "$REPO_ROOT/design/l2_1/ui_contract/ui_projection_lock.json" 2>/dev/null || echo "0")
PANEL_COUNT=$(jq '._statistics.panel_count' "$REPO_ROOT/design/l2_1/ui_contract/ui_projection_lock.json" 2>/dev/null || echo "0")
if [ "$DOMAIN_COUNT" = "5" ] && [ "$PANEL_COUNT" -gt "0" ]; then
    gate_result 4 "PASS" "5 domains, $PANEL_COUNT panels in projection"
else
    gate_result 4 "BLOCKED" "Expected 5 domains, got $DOMAIN_COUNT"
fi

# ============================================================================
# GATE 5: Auth Configuration
# ============================================================================
echo ""
echo "GATE-5: Auth Configuration"
# Check if Clerk env vars are set (basic check)
if [ -f "$REPO_ROOT/.env" ]; then
    if grep -q "CLERK" "$REPO_ROOT/.env" 2>/dev/null || grep -q "AUTH" "$REPO_ROOT/.env" 2>/dev/null; then
        gate_result 5 "PASS" "Auth configuration found"
    else
        gate_result 5 "BLOCKED" "No auth configuration in .env"
    fi
else
    gate_result 5 "BLOCKED" "No .env file found"
fi

# ============================================================================
# GATE 6: UI Consumes Projection Lock
# ============================================================================
echo ""
echo "GATE-6: UI Consumes Projection Lock"
UI_CONSUMPTION_PASS=true
UI_ISSUES=""

# Check 1: ProjectionSidebar exists
if [ -f "$APP_SHELL/src/components/layout/ProjectionSidebar.tsx" ]; then
    echo "  ✓ ProjectionSidebar component exists"
else
    UI_CONSUMPTION_PASS=false
    UI_ISSUES+="Missing ProjectionSidebar.tsx, "
fi

# Check 2: DomainPage component exists
if [ -f "$APP_SHELL/src/pages/domains/DomainPage.tsx" ]; then
    echo "  ✓ DomainPage component exists"
else
    UI_CONSUMPTION_PASS=false
    UI_ISSUES+="Missing DomainPage.tsx, "
fi

# Check 3: Routes use domain pages
if grep -q "OverviewPage\|ActivityPage\|IncidentsPage\|PoliciesPage\|LogsPage" "$APP_SHELL/src/routes/index.tsx" 2>/dev/null; then
    echo "  ✓ Routes configured for L2.1 domains"
else
    UI_CONSUMPTION_PASS=false
    UI_ISSUES+="Domain routes not configured, "
fi

# Check 4: AppLayout uses ProjectionSidebar in preflight mode
if grep -q "ProjectionSidebar" "$APP_SHELL/src/components/layout/AppLayout.tsx" 2>/dev/null; then
    echo "  ✓ AppLayout imports ProjectionSidebar"
else
    UI_CONSUMPTION_PASS=false
    UI_ISSUES+="AppLayout not using ProjectionSidebar, "
fi

# Check 5: Projection loader is used by components
if grep -q "loadProjection\|getEnabledPanels" "$APP_SHELL/src/components/layout/ProjectionSidebar.tsx" 2>/dev/null; then
    echo "  ✓ ProjectionSidebar uses projection loader"
else
    UI_CONSUMPTION_PASS=false
    UI_ISSUES+="ProjectionSidebar not using loader, "
fi

# Check 6: Projection file in dist-preflight
if [ -f "$APP_SHELL/dist-preflight/projection/ui_projection_lock.json" ]; then
    echo "  ✓ Projection lock in dist-preflight"
else
    UI_CONSUMPTION_PASS=false
    UI_ISSUES+="Projection lock not in dist-preflight, "
fi

if [ "$UI_CONSUMPTION_PASS" = true ]; then
    gate_result 6 "PASS" "UI correctly consumes projection lock"
else
    gate_result 6 "BLOCKED" "UI not consuming projection: ${UI_ISSUES%%, }"
fi

# ============================================================================
# GATE 7: Human Approval
# ============================================================================
echo ""
echo "GATE-7: Human Approval"
if [ "$VALIDATE_ONLY" = true ]; then
    echo -e "${YELLOW}SKIPPED (--validate mode)${NC}"
elif [ "$SKIP_APPROVAL" = true ]; then
    gate_result 7 "PASS" "Approval skipped (--skip-approval flag)"
else
    echo ""
    echo "=========================================="
    echo -e "${YELLOW}PROMOTION REQUIRES HUMAN APPROVAL${NC}"
    echo "=========================================="
    echo ""
    echo "You are about to promote preflight to production."
    echo ""
    echo "Preflight URL: https://preflight-console.agenticverz.com"
    echo "Production URL: https://console.agenticverz.com"
    echo ""
    read -p "Have you tested the preflight console? (yes/no): " TESTED
    if [ "$TESTED" != "yes" ]; then
        gate_result 7 "BLOCKED" "User has not tested preflight"
    else
        read -p "Type 'PROMOTE' to confirm promotion: " CONFIRM
        if [ "$CONFIRM" = "PROMOTE" ]; then
            read -p "Enter your name for audit trail: " APPROVER
            gate_result 7 "PASS" "Approved by $APPROVER"

            # Log approval
            echo "$(date -Iseconds) | PROMOTION | Approved by: $APPROVER" >> "$REPO_ROOT/logs/promotion_audit.log" 2>/dev/null || true
        else
            gate_result 7 "BLOCKED" "Confirmation not provided"
        fi
    fi
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=========================================="
echo "GATE SUMMARY"
echo "=========================================="
echo "Passed: $GATES_PASSED / $GATES_TOTAL"
echo ""

if [ "$VALIDATE_ONLY" = true ]; then
    echo -e "${YELLOW}VALIDATION ONLY MODE${NC}"
    echo "No promotion performed."
    if [ "$GATES_PASSED" -ge 6 ]; then
        echo -e "${GREEN}Ready for promotion (pending human approval).${NC}"
        exit 0
    else
        echo -e "${RED}Not ready for promotion. Fix blocking gates.${NC}"
        exit 1
    fi
fi

if [ "$GATES_PASSED" -lt "$GATES_TOTAL" ]; then
    echo -e "${RED}PROMOTION BLOCKED${NC}"
    echo "All gates must pass before promotion."
    exit 1
fi

# ============================================================================
# Perform Promotion
# ============================================================================
echo ""
echo -e "${GREEN}ALL GATES PASSED${NC}"
echo ""
echo "Promoting preflight to production..."

# Backup current production
if [ -d "$APP_SHELL/dist" ]; then
    echo "Creating backup of current production build..."
    rm -rf "$APP_SHELL/dist-backup"
    mv "$APP_SHELL/dist" "$APP_SHELL/dist-backup"
fi

# Copy preflight to production
echo "Copying preflight build to production..."
cp -r "$APP_SHELL/dist-preflight" "$APP_SHELL/dist"

# Log promotion
mkdir -p "$REPO_ROOT/logs"
echo "$(date -Iseconds) | PROMOTED | From: dist-preflight | To: dist" >> "$REPO_ROOT/logs/promotion_audit.log"

echo ""
echo "=========================================="
echo -e "${GREEN}PROMOTION COMPLETE${NC}"
echo "=========================================="
echo ""
echo "Production console updated: https://console.agenticverz.com"
echo ""
echo "If issues are found, rollback with:"
echo "  ./scripts/ops/promote_to_production.sh --rollback"
