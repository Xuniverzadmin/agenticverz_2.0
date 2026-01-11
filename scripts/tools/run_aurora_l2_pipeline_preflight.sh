#!/bin/bash
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: Compile Aurora L2 and deploy to PREFLIGHT environment only
# Reference: SDSR → Aurora → UI Canonical Design
#
# =============================================================================
# DEPLOYMENT PIPELINE RULE (LOCKED)
# =============================================================================
# This script deploys to PREFLIGHT only. Never to production.
#
# Flow:
#   1. Aurora compile → public/projection/
#   2. VITE_PREFLIGHT_MODE=true npm run build → dist/ (with /precus/* routes)
#   2.5. Route verification guard (fail if /cus/* detected)
#   3. cp dist → dist-preflight/
#   4. Verify projection
#   5. STOP (manual promotion required)
#
# CRITICAL: VITE_PREFLIGHT_MODE=true produces /precus/* routes
#           Production uses /cus/* routes (no flag)
#
# Production deployment requires: promote_projection.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/website/app-shell"

# =============================================================================
# PREFLIGHT RECOMPILE SIGNAL (Phase 1 Automation)
# =============================================================================
# This file is created by AURORA_L2_apply_sdsr_observations.py when capability
# status changes. Its presence indicates Aurora recompile is needed.
PREFLIGHT_SIGNAL="$REPO_ROOT/.aurora_needs_preflight_recompile"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     AURORA L2 Pipeline → PREFLIGHT Deployment                ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Target: preflight-console.agenticverz.com                   ║"
echo "║  Production: NOT TOUCHED                                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =============================================================================
# CHECK FOR AUTO-TRIGGER SIGNAL
# =============================================================================
if [ -f "$PREFLIGHT_SIGNAL" ]; then
    echo -e "${GREEN}  ✓ Auto-trigger signal detected: $PREFLIGHT_SIGNAL${NC}"
    echo "    $(cat "$PREFLIGHT_SIGNAL" | head -2)"
    echo ""
fi

# =============================================================================
# PHASE 1: Run Aurora L2 Compiler
# =============================================================================
echo -e "${BLUE}[1/5] Running Aurora L2 Compiler${NC}"

# Check DB_AUTHORITY
if [ -z "$DB_AUTHORITY" ]; then
    echo -e "${RED}ERROR: DB_AUTHORITY not set${NC}"
    echo "Set DB_AUTHORITY=neon or DB_AUTHORITY=local"
    exit 1
fi

cd "$REPO_ROOT"

# Run the base pipeline (compiles and copies to public/projection/)
# Note: Base pipeline stops at public/projection/, does NOT touch dist/
./scripts/tools/run_aurora_l2_pipeline.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Aurora L2 compilation failed${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Aurora L2 compiled to public/projection/${NC}"

# =============================================================================
# PHASE 2: Build Frontend (PREFLIGHT MODE)
# =============================================================================
echo -e "${BLUE}[2/5] Building Frontend (VITE_PREFLIGHT_MODE=true)${NC}"

cd "$FRONTEND_DIR"

# CRITICAL: Build with VITE_PREFLIGHT_MODE=true for /precus/* routes
# The frontend reads: import.meta.env.VITE_PREFLIGHT_MODE === 'true'
# Note: Must export for Vite to pick it up during build
export VITE_PREFLIGHT_MODE=true
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Frontend build failed${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Frontend built to dist/ with VITE_PREFLIGHT_MODE=true${NC}"

# =============================================================================
# PHASE 2.5: Route Verification Guard
# =============================================================================
echo -e "${BLUE}[2.5/5] Verifying Preflight Routes${NC}"

# Check for concrete production routes (like /cus/overview, /cus/policies)
# Note: /cus/* patterns are OK (used in routing definitions), but concrete routes like /cus/overview are NOT OK
PROD_ROUTES_FOUND=$(grep -ohE '"/cus/(overview|activity|incidents|policies|logs|keys|integrations|settings|account)"' dist/assets/*.js 2>/dev/null | head -1)

if [ -n "$PROD_ROUTES_FOUND" ]; then
    echo -e "${RED}ERROR: Production routes detected in preflight build${NC}"
    echo -e "${RED}Build was NOT compiled with VITE_PREFLIGHT_MODE=true${NC}"
    echo ""
    echo "Expected: /precus/* routes"
    echo "Found:    $PROD_ROUTES_FOUND"
    echo ""
    echo "This is a build configuration error."
    echo "Ensure 'export VITE_PREFLIGHT_MODE=true' is set before npm run build."
    exit 1
fi

# Verify preflight routes are present
if grep -q '"/precus/overview"' dist/assets/*.js 2>/dev/null; then
    echo -e "${GREEN}  ✓ Preflight routes (/precus/*) verified${NC}"
else
    echo -e "${YELLOW}  ⚠ Could not verify route prefix in build artifacts${NC}"
    echo -e "${YELLOW}    Manual verification recommended${NC}"
fi

# =============================================================================
# PHASE 3: Deploy to Preflight
# =============================================================================
echo -e "${BLUE}[3/5] Deploying to Preflight${NC}"

# Remove old preflight
rm -rf dist-preflight

# Copy dist to dist-preflight
cp -r dist dist-preflight

echo -e "${GREEN}  ✓ Deployed to dist-preflight/${NC}"

# =============================================================================
# PHASE 4: Verify Deployment
# =============================================================================
echo -e "${BLUE}[4/5] Verifying Preflight Deployment${NC}"

PREFLIGHT_PROJECTION="$FRONTEND_DIR/dist-preflight/projection/ui_projection_lock.json"

if [ ! -f "$PREFLIGHT_PROJECTION" ]; then
    echo -e "${RED}ERROR: Preflight projection not found${NC}"
    exit 1
fi

# Extract stats
GENERATED_AT=$(python3 -c "import json; d=json.load(open('$PREFLIGHT_PROJECTION')); print(d['_meta']['generated_at'])")
BOUND_COUNT=$(python3 -c "import json; d=json.load(open('$PREFLIGHT_PROJECTION')); print(d['_statistics']['bound_panels'])")
DRAFT_COUNT=$(python3 -c "import json; d=json.load(open('$PREFLIGHT_PROJECTION')); print(d['_statistics']['draft_panels'])")

echo -e "${GREEN}  ✓ Preflight projection verified${NC}"
echo ""
echo "  Generated at: $GENERATED_AT"
echo "  BOUND panels: $BOUND_COUNT"
echo "  DRAFT panels: $DRAFT_COUNT"

# =============================================================================
# DONE - Manual Promotion Required
# =============================================================================
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PREFLIGHT DEPLOYMENT COMPLETE${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Verify at: https://preflight-console.agenticverz.com/precus/policies"
echo "     (URL MUST contain /precus/, NOT /cus/)"
echo "  2. Check POL-PR-PP-O2 panel has APPROVE + REJECT enabled"
echo "  3. If verified, promote to production:"
echo ""
echo -e "     ${GREEN}./scripts/tools/promote_projection.sh${NC}"
echo ""
echo -e "${YELLOW}WARNING: Production (console.agenticverz.com) is NOT updated.${NC}"
echo ""

# =============================================================================
# CLEANUP AUTO-TRIGGER SIGNAL
# =============================================================================
if [ -f "$PREFLIGHT_SIGNAL" ]; then
    rm -f "$PREFLIGHT_SIGNAL"
    echo -e "${GREEN}  ✓ Cleared auto-trigger signal${NC}"
fi
