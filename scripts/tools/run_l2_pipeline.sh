#!/usr/bin/env bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (manual)
#   Execution: sync
# Role: Run full L2.1 UI projection pipeline
# Reference: L2.1 UI Projection Pipeline, PIN-365 (STEP 2A)

set -euo pipefail

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
