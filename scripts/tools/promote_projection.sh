#!/bin/bash
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: manual (explicit human decision)
#   Execution: sync
# Role: Promote verified preflight projection to production
# Reference: SDSR → Aurora → UI Canonical Design
#
# =============================================================================
# PROMOTION RULE (LOCKED)
# =============================================================================
# This script ONLY copies dist-preflight → dist
# No compile. No build. No logic.
#
# Precondition: Preflight must be verified by human inspection.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/website/app-shell"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     PROJECTION PROMOTION: Preflight → Production             ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Source: dist-preflight/ (preflight-console)                 ║"
echo "║  Target: dist/ (console.agenticverz.com)                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

cd "$FRONTEND_DIR"

# =============================================================================
# PHASE 1: Verify Preflight Exists
# =============================================================================
echo -e "${BLUE}[1/4] Verifying Preflight Exists${NC}"

PREFLIGHT_PROJECTION="dist-preflight/projection/ui_projection_lock.json"
PROD_PROJECTION="dist/projection/ui_projection_lock.json"

if [ ! -f "$PREFLIGHT_PROJECTION" ]; then
    echo -e "${RED}ERROR: Preflight projection not found${NC}"
    echo "Run ./scripts/tools/run_aurora_l2_pipeline_preflight.sh first"
    exit 1
fi

echo -e "${GREEN}  ✓ Preflight exists${NC}"

# =============================================================================
# PHASE 2: Show Diff
# =============================================================================
echo -e "${BLUE}[2/4] Comparing Projections${NC}"

PREFLIGHT_GEN=$(python3 -c "import json; d=json.load(open('$PREFLIGHT_PROJECTION')); print(d['_meta']['generated_at'])")
PREFLIGHT_BOUND=$(python3 -c "import json; d=json.load(open('$PREFLIGHT_PROJECTION')); print(d['_statistics']['bound_panels'])")

if [ -f "$PROD_PROJECTION" ]; then
    PROD_GEN=$(python3 -c "import json; d=json.load(open('$PROD_PROJECTION')); print(d['_meta']['generated_at'])")
    PROD_BOUND=$(python3 -c "import json; d=json.load(open('$PROD_PROJECTION')); print(d['_statistics']['bound_panels'])")
else
    PROD_GEN="(none)"
    PROD_BOUND="0"
fi

echo ""
echo "  Preflight:  generated=$PREFLIGHT_GEN  BOUND=$PREFLIGHT_BOUND"
echo "  Production: generated=$PROD_GEN  BOUND=$PROD_BOUND"
echo ""

# =============================================================================
# PHASE 3: Confirm Promotion
# =============================================================================
echo -e "${BLUE}[3/4] Confirming Promotion${NC}"

if [ "$1" != "--yes" ]; then
    echo -e "${YELLOW}This will overwrite production with preflight.${NC}"
    echo ""
    read -p "Promote preflight to production? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Promotion cancelled${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}  ✓ Promotion confirmed${NC}"

# =============================================================================
# PHASE 4: Promote
# =============================================================================
echo -e "${BLUE}[4/4] Promoting to Production${NC}"

# Backup current production
if [ -d "dist" ]; then
    BACKUP_NAME="dist-backup-$(date +%Y%m%d-%H%M%S)"
    mv dist "$BACKUP_NAME"
    echo "  Backed up dist/ → $BACKUP_NAME/"
fi

# Copy preflight to production
cp -r dist-preflight dist

echo -e "${GREEN}  ✓ Promoted to dist/${NC}"

# =============================================================================
# DONE
# =============================================================================
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PRODUCTION PROMOTION COMPLETE${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Production: https://console.agenticverz.com"
echo "  Projection: $PREFLIGHT_GEN"
echo "  BOUND:      $PREFLIGHT_BOUND panels"
echo ""
echo -e "${GREEN}Apache is already configured to serve dist/.${NC}"
echo -e "${GREEN}Changes are now live.${NC}"
echo ""
