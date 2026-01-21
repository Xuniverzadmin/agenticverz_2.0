#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: AURORA L2 Pipeline - Phase A validation + Aurora compilation
# Reference: PIN-420, SEMANTIC_VALIDATOR.md, AURORA_L2.md
#
# This is the SINGLE GATE for UI projection generation.
# It enforces the two-phase validation architecture:
#   Phase A: Intent Guardrails (design-time) → MUST pass
#   Aurora:  Compilation → Only runs if Phase A passes
#
# Usage:
#   ./scripts/tools/run_aurora_l2_pipeline.sh [--skip-phase-a] [--dry-run]
#
# Options:
#   --skip-phase-a  Skip Phase A validation (DANGEROUS - for debugging only)
#   --dry-run       Show what would be done without executing
#
# Environment:
#   DB_AUTHORITY    Required. Must be 'neon' or 'local'.
#
# Exit Codes:
#   0   Pipeline completed successfully
#   1   Phase A blocked (design-time violations)
#   2   Aurora compilation failed
#   3   Configuration error
#

set -e

# =============================================================================
# V2 CONSTITUTION DEPRECATION GUARD (2026-01-20)
# =============================================================================
# The AURORA L2 pipeline is DEPRECATED for customer console projection.
# V2 Constitution is now the authoritative source.
# Source: design/v2_constitution/ui_projection_lock.json
# Scaffolding: src/contracts/ui_plan_scaffolding.ts
#
# This pipeline would overwrite the V2 Constitution structure with old AURORA output.
# To re-enable, remove this guard. But you probably don't want to do that.
# =============================================================================

echo ""
echo -e "\033[1;33m================================================================\033[0m"
echo -e "\033[1;33m  AURORA L2 PIPELINE - DEPRECATED\033[0m"
echo -e "\033[1;33m================================================================\033[0m"
echo ""
echo "The AURORA L2 pipeline is DEPRECATED for customer console projection."
echo ""
echo "V2 Constitution is now the authoritative source:"
echo "  - Projection: design/v2_constitution/ui_projection_lock.json"
echo "  - Scaffolding: src/contracts/ui_plan_scaffolding.ts"
echo ""
echo "Running this pipeline would overwrite V2 Constitution with old AURORA output."
echo ""
echo "If you REALLY need to run AURORA pipeline, use:"
echo "  ALLOW_AURORA_OVERRIDE=1 ./scripts/tools/run_aurora_l2_pipeline.sh"
echo ""

if [ "$ALLOW_AURORA_OVERRIDE" != "1" ]; then
    echo -e "\033[0;31mABORTED: AURORA pipeline is deprecated.\033[0m"
    exit 0
fi

echo -e "\033[1;33m[WARNING] AURORA override enabled - proceeding...\033[0m"
echo ""

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Backend directory for Python imports
BACKEND_DIR="$REPO_ROOT/backend"

# Output directories
UI_CONTRACT_DIR="$REPO_ROOT/design/l2_1/ui_contract"
PUBLIC_PROJECTION_DIR="$REPO_ROOT/website/app-shell/public/projection"

# Canonical projection file
PROJECTION_FILE="ui_projection_lock.json"

# Phase A validation script
PHASE_A_SCRIPT="$SCRIPT_DIR/validate_all_intents.py"

# Aurora compiler
AURORA_COMPILER="$BACKEND_DIR/aurora_l2/SDSR_UI_AURORA_compiler.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

SKIP_PHASE_A=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-phase-a)
            SKIP_PHASE_A=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown option: $1${NC}"
            exit 3
            ;;
    esac
done

# =============================================================================
# PREFLIGHT CHECKS
# =============================================================================

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  AURORA L2 PIPELINE${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Check DB_AUTHORITY
if [ -z "$DB_AUTHORITY" ]; then
    echo -e "${RED}[FATAL] DB_AUTHORITY not declared.${NC}"
    echo "        Authority is declared, not inferred."
    echo "        Set DB_AUTHORITY=neon or DB_AUTHORITY=local before running."
    echo "        Reference: docs/governance/DB_AUTH_001_INVARIANT.md"
    exit 3
fi

if [ "$DB_AUTHORITY" != "neon" ] && [ "$DB_AUTHORITY" != "local" ]; then
    echo -e "${RED}[FATAL] Invalid DB_AUTHORITY: $DB_AUTHORITY${NC}"
    echo "        Must be 'neon' or 'local'."
    exit 3
fi

echo -e "${GREEN}[OK]${NC} DB_AUTHORITY=$DB_AUTHORITY"

# Check Phase A script exists
if [ ! -f "$PHASE_A_SCRIPT" ]; then
    echo -e "${RED}[FATAL] Phase A script not found: $PHASE_A_SCRIPT${NC}"
    exit 3
fi

echo -e "${GREEN}[OK]${NC} Phase A script found"

# Check Aurora compiler exists
if [ ! -f "$AURORA_COMPILER" ]; then
    echo -e "${RED}[FATAL] Aurora compiler not found: $AURORA_COMPILER${NC}"
    exit 3
fi

echo -e "${GREEN}[OK]${NC} Aurora compiler found"

echo ""

# =============================================================================
# PHASE A: INTENT GUARDRAILS
# =============================================================================

if [ "$SKIP_PHASE_A" = true ]; then
    echo -e "${YELLOW}[WARN] Skipping Phase A validation (--skip-phase-a)${NC}"
    echo -e "${YELLOW}       This is DANGEROUS and should only be used for debugging.${NC}"
    echo ""
else
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  PHASE A: INTENT GUARDRAILS${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] Would run: python3 $PHASE_A_SCRIPT --blocking"
    else
        # Run Phase A validation
        cd "$BACKEND_DIR"

        if ! python3 "$PHASE_A_SCRIPT" --blocking; then
            echo ""
            echo -e "${RED}================================================================${NC}"
            echo -e "${RED}  PIPELINE BLOCKED${NC}"
            echo -e "${RED}================================================================${NC}"
            echo ""
            echo -e "${RED}Phase A validation failed with BLOCKING violations.${NC}"
            echo "Fix the violations listed above before proceeding."
            echo ""
            echo "Fix Owners:"
            echo "  - INT-001, INT-003, INT-004, INT-005, INT-007: Product"
            echo "  - INT-002, INT-006, INT-008: Architecture"
            echo ""
            echo "Reference: docs/architecture/pipeline/SEMANTIC_VALIDATOR.md"
            echo ""
            exit 1
        fi

        echo ""
        echo -e "${GREEN}[PHASE A] PASSED${NC}"
        echo ""
    fi
fi

# =============================================================================
# AURORA COMPILATION
# =============================================================================

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  AURORA COMPILATION${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "[DRY-RUN] Would run: DB_AUTHORITY=$DB_AUTHORITY python3 -m backend.aurora_l2.SDSR_UI_AURORA_compiler --output-projection"
else
    cd "$REPO_ROOT"

    # Run Aurora compiler
    if ! DB_AUTHORITY="$DB_AUTHORITY" python3 -m backend.aurora_l2.SDSR_UI_AURORA_compiler --output-projection; then
        echo ""
        echo -e "${RED}[ERROR] Aurora compilation failed${NC}"
        exit 2
    fi

    echo ""
    echo -e "${GREEN}[AURORA] Compilation complete${NC}"
    echo ""
fi

# =============================================================================
# COPY PROJECTION TO PUBLIC
# =============================================================================

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  COPY PROJECTION TO PUBLIC${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

SOURCE_FILE="$UI_CONTRACT_DIR/$PROJECTION_FILE"
DEST_FILE="$PUBLIC_PROJECTION_DIR/$PROJECTION_FILE"

if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}[ERROR] Projection file not found: $SOURCE_FILE${NC}"
    exit 2
fi

if [ "$DRY_RUN" = true ]; then
    echo "[DRY-RUN] Would copy: $SOURCE_FILE -> $DEST_FILE"
else
    # Create destination directory if needed
    mkdir -p "$PUBLIC_PROJECTION_DIR"

    # Copy projection
    cp "$SOURCE_FILE" "$DEST_FILE"

    echo -e "${GREEN}[OK]${NC} Copied projection to: $DEST_FILE"
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  PIPELINE COMPLETE${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo "  Phase A:     $([ "$SKIP_PHASE_A" = true ] && echo 'SKIPPED' || echo 'PASSED')"
echo "  Aurora:      COMPILED"
echo "  Projection:  COPIED"
echo ""
echo "  Output:"
echo "    - Validation: $UI_CONTRACT_DIR/phase_a_validation.json"
echo "    - Projection: $UI_CONTRACT_DIR/$PROJECTION_FILE"
echo "    - Public:     $PUBLIC_PROJECTION_DIR/$PROJECTION_FILE"
echo ""

exit 0
