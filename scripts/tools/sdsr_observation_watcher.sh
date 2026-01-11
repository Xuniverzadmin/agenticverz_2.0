#!/bin/bash
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: manual | cron | CI
#   Execution: sync
# Role: Orchestrate SDSR observation → Aurora apply → Preflight compile
# Reference: SDSR-Aurora Capability Proof Pipeline v1.0
#
# =============================================================================
# ONE-WAY CAUSALITY ARCHITECTURE
# =============================================================================
# This script is the DOWNSTREAM orchestrator in the clean architecture:
#
#   inject_synthetic.py (upstream)
#      └─ emits .sdsr_observation_ready signal
#
#   sdsr_observation_watcher.sh (this script - downstream)
#      ├─ detects signal
#      ├─ applies observation (AURORA_L2_apply_sdsr_observations.py)
#      ├─ triggers preflight compile (run_aurora_l2_pipeline_preflight.sh)
#      └─ clears signals
#
# CRITICAL: inject_synthetic.py does NOT call Aurora scripts directly.
#           This watcher is the ONLY script that orchestrates downstream.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# =============================================================================
# SIGNAL FILES
# =============================================================================
# Input signal (from inject_synthetic.py)
SDSR_READY_SIGNAL="$REPO_ROOT/.sdsr_observation_ready"

# Output signal (from AURORA_L2_apply_sdsr_observations.py)
PREFLIGHT_RECOMPILE_SIGNAL="$REPO_ROOT/.aurora_needs_preflight_recompile"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# =============================================================================
# BANNER
# =============================================================================
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     SDSR Observation Watcher                                 ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Role: Downstream orchestrator (one-way causality)          ║"
echo "║  Flow: signal → apply → compile → clear                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================
DRY_RUN=""
SKIP_PREFLIGHT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            echo -e "${YELLOW}Mode: DRY RUN (no files will be modified)${NC}"
            shift
            ;;
        --skip-preflight)
            SKIP_PREFLIGHT="true"
            echo -e "${YELLOW}Mode: Skip preflight compile${NC}"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# =============================================================================
# PHASE 1: Check for SDSR Ready Signal
# =============================================================================
echo ""
echo -e "${BLUE}[1/4] Checking for SDSR observation signal${NC}"

if [ ! -f "$SDSR_READY_SIGNAL" ]; then
    echo -e "${YELLOW}  No signal found: $SDSR_READY_SIGNAL${NC}"
    echo ""
    echo "Nothing to process. Either:"
    echo "  - No SDSR scenario has been run recently"
    echo "  - Signal was already processed"
    echo ""
    echo "To manually trigger SDSR:"
    echo "  python3 backend/scripts/sdsr/inject_synthetic.py --scenario <scenario_id>"
    exit 0
fi

echo -e "${GREEN}  ✓ Signal detected: $SDSR_READY_SIGNAL${NC}"
echo ""
echo "Signal contents:"
cat "$SDSR_READY_SIGNAL" | sed 's/^/    /'
echo ""

# Parse signal file
OBSERVATION_PATH=$(grep "^observation_path=" "$SDSR_READY_SIGNAL" | cut -d'=' -f2-)
SCENARIO_ID=$(grep "^scenario_id=" "$SDSR_READY_SIGNAL" | cut -d'=' -f2-)
OBSERVATION_CLASS=$(grep "^observation_class=" "$SDSR_READY_SIGNAL" | cut -d'=' -f2-)
CAPABILITIES_COUNT=$(grep "^capabilities_count=" "$SDSR_READY_SIGNAL" | cut -d'=' -f2-)

if [ -z "$OBSERVATION_PATH" ]; then
    echo -e "${RED}ERROR: Signal file missing observation_path${NC}"
    exit 1
fi

echo "Parsed signal:"
echo "  Scenario ID:       $SCENARIO_ID"
echo "  Observation class: $OBSERVATION_CLASS"
echo "  Capabilities:      $CAPABILITIES_COUNT"
echo "  Observation path:  $OBSERVATION_PATH"

# =============================================================================
# PHASE 2: Apply SDSR Observation to Aurora
# =============================================================================
echo ""
echo -e "${BLUE}[2/4] Applying SDSR observation to Aurora capability registry${NC}"

# Check if observation file exists
if [ ! -f "$OBSERVATION_PATH" ]; then
    echo -e "${RED}ERROR: Observation file not found: $OBSERVATION_PATH${NC}"
    exit 1
fi

cd "$REPO_ROOT"

# Run the observation applier
python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py \
    --observation "$OBSERVATION_PATH" \
    $DRY_RUN

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Observation application failed${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Observation applied successfully${NC}"

# =============================================================================
# PHASE 3: Trigger Preflight Compile (if not skipped)
# =============================================================================
echo ""
echo -e "${BLUE}[3/4] Triggering preflight compile${NC}"

if [ -n "$SKIP_PREFLIGHT" ]; then
    echo -e "${YELLOW}  Skipped (--skip-preflight flag)${NC}"
elif [ -n "$DRY_RUN" ]; then
    echo -e "${YELLOW}  [DRY RUN] Would trigger preflight compile${NC}"
    echo "  Command: ./scripts/tools/run_aurora_l2_pipeline_preflight.sh"
else
    # Check DB_AUTHORITY
    if [ -z "$DB_AUTHORITY" ]; then
        echo -e "${YELLOW}  ⚠ DB_AUTHORITY not set, skipping preflight compile${NC}"
        echo "  Set DB_AUTHORITY=neon or DB_AUTHORITY=local to enable"
    else
        echo "  Running preflight pipeline..."
        ./scripts/tools/run_aurora_l2_pipeline_preflight.sh

        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Preflight compile failed${NC}"
            exit 1
        fi

        echo -e "${GREEN}  ✓ Preflight compile complete${NC}"
    fi
fi

# =============================================================================
# PHASE 4: Clear Signals
# =============================================================================
echo ""
echo -e "${BLUE}[4/4] Clearing signals${NC}"

if [ -n "$DRY_RUN" ]; then
    echo -e "${YELLOW}  [DRY RUN] Would clear signals:${NC}"
    [ -f "$SDSR_READY_SIGNAL" ] && echo "    - $SDSR_READY_SIGNAL"
    [ -f "$PREFLIGHT_RECOMPILE_SIGNAL" ] && echo "    - $PREFLIGHT_RECOMPILE_SIGNAL"
else
    if [ -f "$SDSR_READY_SIGNAL" ]; then
        rm -f "$SDSR_READY_SIGNAL"
        echo -e "${GREEN}  ✓ Cleared: .sdsr_observation_ready${NC}"
    fi

    if [ -f "$PREFLIGHT_RECOMPILE_SIGNAL" ]; then
        rm -f "$PREFLIGHT_RECOMPILE_SIGNAL"
        echo -e "${GREEN}  ✓ Cleared: .aurora_needs_preflight_recompile${NC}"
    fi
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}SDSR OBSERVATION WATCHER COMPLETE${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Processed:"
echo "  Scenario:    $SCENARIO_ID"
echo "  Class:       $OBSERVATION_CLASS"
echo "  Observation: $OBSERVATION_PATH"

if [ -n "$DRY_RUN" ]; then
    echo ""
    echo -e "${YELLOW}DRY RUN: No changes were made${NC}"
else
    echo ""
    echo -e "${GREEN}Pipeline chain complete:${NC}"
    echo "  [1] inject_synthetic.py   → materialized truth"
    echo "  [2] observation watcher   → detected signal"
    echo "  [3] apply_observations.py → updated capability registry"
    if [ -z "$SKIP_PREFLIGHT" ] && [ -n "$DB_AUTHORITY" ]; then
        echo "  [4] preflight pipeline    → compiled Aurora + deployed"
    fi
fi

echo ""
