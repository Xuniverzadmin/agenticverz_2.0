#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (pipeline step 2)
#   Execution: sync
# Role: Normalize raw intent IR by applying safe defaults (GAP-BUILDER)
# Callers: UI projection pipeline
# Allowed Imports: json
# Forbidden Imports: None
# Reference: L2.1 UI Projection Pipeline

"""
B: Intent Normalizer / Gap-Builder

RULES (DETERMINISTIC):
- Empty `order` → set to `999`
- Empty `enabled` (visible_by_default) → set to `false`
- Disabled without reason → `disabled_reason = "unspecified in L2.1"`
- Missing `render_mode` → `FLAT`
- Missing `visibility` → `ALWAYS`

For every auto-filled field, record normalization metadata.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Normalization policy version
NORMALIZATION_POLICY = "safe-defaults-v1"

# Default values for gap-filling
DEFAULTS = {
    "order": "999",  # Default order for unspecified
    "enabled": False,  # Default enabled state
    "disabled_reason": "unspecified in L2.1",
    "render_mode": "FLAT",
    "visibility": "ALWAYS",
}


def normalize_intent(intent: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    Normalize a single intent record, returning normalized intent and list of filled fields.
    """
    filled_fields = []
    normalized = intent.copy()

    # B2.1: Empty order → 999
    if normalized.get("order") is None or normalized.get("order") == "":
        normalized["order"] = DEFAULTS["order"]
        filled_fields.append("order")

    # B2.2: Empty enabled (visible_by_default) → false
    visible = normalized.get("visible_by_default")
    if visible is None or visible == "":
        normalized["enabled"] = DEFAULTS["enabled"]
        filled_fields.append("enabled")
    else:
        # Convert YES/NO to boolean
        normalized["enabled"] = str(visible).upper() == "YES"

    # B2.3: Disabled without reason
    if not normalized.get("enabled", True):
        if not normalized.get("disabled_reason"):
            normalized["disabled_reason"] = DEFAULTS["disabled_reason"]
            filled_fields.append("disabled_reason")

    # B2.4: Missing render_mode → FLAT
    if not normalized.get("render_mode"):
        normalized["render_mode"] = DEFAULTS["render_mode"]
        filled_fields.append("render_mode")

    # B2.5: Missing visibility → ALWAYS
    if not normalized.get("visibility"):
        normalized["visibility"] = DEFAULTS["visibility"]
        filled_fields.append("visibility")

    # Normalize other boolean fields
    for bool_field in ["nav_required", "filtering", "read", "write", "activate"]:
        val = normalized.get(bool_field)
        if val is not None and isinstance(val, str):
            normalized[bool_field] = val.upper() == "YES"

    # Ensure controls is always a list
    if not isinstance(normalized.get("controls"), list):
        normalized["controls"] = []

    # B3: Add normalization annotation
    normalized["_normalization"] = {
        "filled_fields": filled_fields,
        "policy": NORMALIZATION_POLICY,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return normalized, filled_fields


def validate_no_empty_fields(intent: dict[str, Any], required_fields: list[str]) -> list[str]:
    """
    Check for empty fields after normalization.
    Returns list of still-empty required fields.
    """
    empty_fields = []
    for field in required_fields:
        val = intent.get(field)
        if val is None or val == "" or val == []:
            empty_fields.append(field)
    return empty_fields


def normalize_intents(raw_ir: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize all intents in raw IR.

    B4: After this step, no empty fields allowed in required set.
    """
    normalized_intents = []
    total_filled = 0
    fill_stats = {}

    required_fields = [
        "row_uid", "domain", "panel_id", "panel_name",
        "order", "enabled", "render_mode", "visibility"
    ]

    for intent in raw_ir.get("intents", []):
        normalized, filled_fields = normalize_intent(intent)

        # Track statistics
        total_filled += len(filled_fields)
        for field in filled_fields:
            fill_stats[field] = fill_stats.get(field, 0) + 1

        # Validate no empty required fields
        empty = validate_no_empty_fields(normalized, required_fields)
        if empty:
            # Still has empty fields - record for error reporting
            normalized["_validation_errors"] = {
                "empty_required_fields": empty
            }

        normalized_intents.append(normalized)

    # Build output structure
    output = {
        "_meta": {
            "type": "ui_intent_ir_normalized",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": raw_ir.get("_meta", {}).get("source_file", "unknown"),
            "row_count": len(normalized_intents),
            "processing_stage": "NORMALIZED",
            "normalization_policy": NORMALIZATION_POLICY,
            "fill_statistics": {
                "total_fields_filled": total_filled,
                "by_field": fill_stats,
            },
        },
        "intents": normalized_intents,
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Normalize raw intent IR with safe defaults"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_intent_ir_raw.json"),
        help="Path to raw intent IR JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_intent_ir_normalized.json"),
        help="Output path for normalized intent IR JSON"
    )

    args = parser.parse_args()

    # Validate input exists
    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        return 1

    # Read input
    with open(args.input) as f:
        raw_ir = json.load(f)

    # Normalize
    print(f"Normalizing intents from: {args.input}")
    result = normalize_intents(raw_ir)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    # Report
    stats = result["_meta"]["fill_statistics"]
    print(f"Generated normalized intent IR: {args.output}")
    print(f"  Rows: {result['_meta']['row_count']}")
    print(f"  Total fields filled: {stats['total_fields_filled']}")
    print(f"  By field: {stats['by_field']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
