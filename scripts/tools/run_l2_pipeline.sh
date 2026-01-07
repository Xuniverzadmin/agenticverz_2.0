#!/usr/bin/env bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (manual)
#   Execution: sync
# Role: Run full L2.1 UI projection pipeline
# Reference: L2.1 UI Projection Pipeline

set -euo pipefail

echo "=========================================="
echo "L2.1 UI Projection Pipeline"
echo "=========================================="

# Change to repo root
cd "$(dirname "$0")/../.."

echo ""
echo "Step 1/4: Parsing L2.1 supertable..."
python3 scripts/tools/l2_raw_intent_parser.py

echo ""
echo "Step 2/4: Normalizing intents..."
python3 scripts/tools/intent_normalizer.py

echo ""
echo "Step 3/4: Compiling intents..."
python3 scripts/tools/intent_compiler.py

echo ""
echo "Step 4/4: Building projection lock..."
python3 scripts/tools/ui_projection_builder.py

echo ""
echo "=========================================="
echo "Pipeline complete!"
echo "=========================================="
echo ""
echo "Generated artifacts:"
echo "  - design/l2_1/ui_contract/ui_intent_ir_raw.json"
echo "  - design/l2_1/ui_contract/ui_intent_ir_normalized.json"
echo "  - design/l2_1/ui_contract/ui_intent_ir_compiled.json"
echo "  - design/l2_1/ui_contract/ui_projection_lock.json"
