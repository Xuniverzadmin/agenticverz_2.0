#!/usr/bin/env bash
# ================================================================================
# DEPRECATED — DO NOT USE
# ================================================================================
#
# This script is part of the LEGACY L2.1 CSV-based pipeline.
# It has been replaced by the AURORA L2 SDSR-driven pipeline.
#
# REPLACEMENT: scripts/tools/run_aurora_l2_pipeline.sh
# REFERENCE: design/l2_1/AURORA_L2.md, PIN-370, PIN-379
#
# This file is preserved for historical reference only.
# ================================================================================

# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Status: DEPRECATED (2026-01-14)
# Replacement: scripts/tools/run_aurora_l2_pipeline.sh
# Reference: PIN-365 (STEP 2A) - SUPERSEDED by PIN-370

set -euo pipefail

echo "=========================================="
echo "WARNING: DEPRECATED SCRIPT"
echo "Use run_aurora_l2_pipeline.sh instead"
echo "=========================================="
echo ""
echo "This legacy pipeline is no longer maintained."
echo "The current AURORA L2 pipeline uses:"
echo "  - SDSR scenario YAML files for intent entry"
echo "  - backend/aurora_l2/SDSR_UI_AURORA_compiler.py for compilation"
echo "  - Capability observation for binding status"
echo ""
echo "To run the current pipeline:"
echo "  ./scripts/tools/run_aurora_l2_pipeline.sh"
echo ""
exit 1

# Legacy code below (disabled)
: '
echo "=========================================="
echo "L2.1 UI Projection Pipeline"
echo "Reference: PIN-365 (STEP 2A)"
echo "=========================================="

# Change to repo root
cd "$(dirname "$0")/../.."

echo ""
echo "Step 1/5: Parsing L2.1 supertable..."
python3 scripts/tools/l2_raw_intent_parser.py

echo ""
echo "Step 2/5: Normalizing intents..."
python3 scripts/tools/intent_normalizer.py

echo ""
echo "Step 2A/5: Resolving surfaces to slots (PIN-365)..."
python3 scripts/tools/surface_to_slot_resolver.py

echo ""
echo "Step 3/5: Compiling intents..."
# Input from slotted IR (STEP 2A output) instead of normalized IR
python3 scripts/tools/intent_compiler.py \
    --input design/l2_1/ui_contract/ui_intent_ir_slotted.json

echo ""
echo "Step 4/5: Building projection lock..."
python3 scripts/tools/ui_projection_builder.py

echo ""
echo "=========================================="
echo "Pipeline complete!"
echo "=========================================="
echo ""
echo "Generated artifacts:"
echo "  - design/l2_1/ui_contract/ui_intent_ir_raw.json"
echo "  - design/l2_1/ui_contract/ui_intent_ir_normalized.json"
echo "  - design/l2_1/ui_contract/ui_intent_ir_slotted.json (STEP 2A)"
echo "  - design/l2_1/ui_contract/ui_intent_ir_compiled.json"
echo "  - design/l2_1/ui_contract/ui_projection_lock.json"
