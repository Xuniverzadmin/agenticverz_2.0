#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (pipeline step 1)
#   Execution: sync
# Role: Parse L2.1 supertable to raw UI intent IR (NO validation, NO defaults)
# Callers: UI projection pipeline
# Allowed Imports: pandas, json
# Forbidden Imports: None
# Reference: L2.1 UI Projection Pipeline

"""
A1: Parse L2.1 Table to Raw Intent IR

RULES:
- Do NOT validate
- Do NOT default
- Do NOT infer
- Preserve all raw values including empty cells
"""

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def parse_control_set(control_set_str: str) -> list[str]:
    """Parse control set string to list, preserving raw value."""
    if pd.isna(control_set_str) or control_set_str == "":
        return []
    if isinstance(control_set_str, list):
        return control_set_str
    # Handle string format: "[FILTER,SORT,SELECT_SINGLE]" (unquoted items)
    s = str(control_set_str).strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        # Split by comma, strip whitespace
        return [item.strip() for item in inner.split(",") if item.strip()]
    try:
        # Try parsing as Python list literal (quoted items)
        parsed = ast.literal_eval(control_set_str)
        if isinstance(parsed, list):
            return parsed
        return []
    except (ValueError, SyntaxError):
        return []


def row_to_intent(row: pd.Series, idx: int) -> dict[str, Any]:
    """
    Convert a single row to raw intent record.

    Preserves ALL values including empty/null - no defaults applied.
    """
    # Parse control set
    controls = parse_control_set(row.get("Control Set (Explicit)", ""))

    # Build raw intent - preserve nulls as None
    intent = {
        "row_uid": row.get("row_uid")
        if pd.notna(row.get("row_uid"))
        else f"auto_{idx}",
        "domain": row.get("Domain") if pd.notna(row.get("Domain")) else None,
        "subdomain": row.get("Subdomain") if pd.notna(row.get("Subdomain")) else None,
        "topic": row.get("Topic") if pd.notna(row.get("Topic")) else None,
        "topic_id": row.get("Topic ID") if pd.notna(row.get("Topic ID")) else None,
        "panel_id": row.get("Panel ID") if pd.notna(row.get("Panel ID")) else None,
        "panel_name": row.get("Panel Name")
        if pd.notna(row.get("Panel Name"))
        else None,
        "order": row.get("Order") if pd.notna(row.get("Order")) else None,
        "controls": controls,
        "control_count": len(controls),
        "visible_by_default": row.get("Visible by Default")
        if pd.notna(row.get("Visible by Default"))
        else None,
        "nav_required": row.get("Nav Required")
        if pd.notna(row.get("Nav Required"))
        else None,
        "filtering": row.get("Filtering") if pd.notna(row.get("Filtering")) else None,
        "selection_mode": row.get("Selection Mode")
        if pd.notna(row.get("Selection Mode"))
        else None,
        "ranking_dimension": row.get("Ranking Dimension")
        if pd.notna(row.get("Ranking Dimension"))
        else None,
        # Read/Write/Activate permissions
        "read": row.get("Read") if pd.notna(row.get("Read")) else None,
        "write": row.get("Write") if pd.notna(row.get("Write")) else None,
        "activate": row.get("Activate") if pd.notna(row.get("Activate")) else None,
        # Additional context (for traceability)
        "action_layer": row.get("Action Layer")
        if pd.notna(row.get("Action Layer"))
        else None,
        "notes": row.get("Notes") if pd.notna(row.get("Notes")) else None,
    }

    return intent


def parse_l2_to_raw_intent(
    xlsx_path: Path, sheet_name: str = "SUPERTABLE"
) -> dict[str, Any]:
    """
    Parse L2.1 supertable to raw UI intent IR.

    NO validation, NO defaults, NO inference.
    """
    # Read Excel
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    # Convert each row to intent
    intents = []
    for idx, row in df.iterrows():
        intent = row_to_intent(row, idx)
        intents.append(intent)

    # Build output structure
    output = {
        "_meta": {
            "type": "ui_intent_ir_raw",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_file": str(xlsx_path),
            "source_sheet": sheet_name,
            "row_count": len(intents),
            "processing_stage": "RAW",
            "validation_applied": False,
            "defaults_applied": False,
        },
        "intents": intents,
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Parse L2.1 supertable to raw UI intent IR"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("design/l2_1/supertable/l2_supertable_v3_cap_expanded.xlsx"),
        help="Path to L2.1 supertable Excel file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_intent_ir_raw.json"),
        help="Output path for raw intent IR JSON",
    )
    parser.add_argument(
        "--sheet", default="SUPERTABLE", help="Sheet name to read (default: SUPERTABLE)"
    )

    args = parser.parse_args()

    # Validate input exists
    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        return 1

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Parse
    print(f"Parsing L2.1 from: {args.input}")
    result = parse_l2_to_raw_intent(args.input, args.sheet)

    # Write output
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Generated raw intent IR: {args.output}")
    print(f"  Rows: {result['_meta']['row_count']}")
    print(f"  Stage: {result['_meta']['processing_stage']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
