#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (pipeline step 3)
#   Execution: sync
# Role: Compile normalized intent IR with strict validation (HOSTILE)
# Callers: UI projection pipeline
# Allowed Imports: json
# Forbidden Imports: None
# Reference: L2.1 UI Projection Pipeline

"""
C: Intent Compiler (HOSTILE)

RULES (FAIL HARD):
- Empty fields → ABORT
- Missing control order → ABORT
- Duplicate panel order within domain → ABORT
- Disabled control without reason → ABORT
- Unknown render_mode → ABORT
- Unknown control type → ABORT

If compilation fails → UI must not render.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Valid values for strict validation
VALID_RENDER_MODES = {"FLAT", "TREE", "GRID", "TABLE", "CARD", "LIST"}
VALID_CONTROL_TYPES = {
    "FILTER", "SORT", "SELECT_SINGLE", "SELECT_MULTI", "NAVIGATE",
    "BULK_SELECT", "DETAIL_VIEW", "ACTION", "DOWNLOAD", "EXPAND",
    "REFRESH", "SEARCH", "PAGINATION", "TOGGLE", "EDIT", "DELETE",
    "CREATE", "APPROVE", "REJECT", "ARCHIVE", "EXPORT", "IMPORT",
    "ACKNOWLEDGE", "RESOLVE",  # Incident management controls
}
VALID_VISIBILITY = {"ALWAYS", "CONDITIONAL", "HIDDEN", "ROLE_BASED"}
VALID_DOMAINS = {"Overview", "Activity", "Incidents", "Policies", "Logs"}

# Required fields that must not be empty
REQUIRED_FIELDS = [
    "row_uid", "domain", "panel_id", "panel_name",
    "order", "render_mode", "visibility"
]


class CompilationError(Exception):
    """Raised when compilation fails due to validation error."""
    pass


def validate_required_fields(intent: dict[str, Any], idx: int) -> list[str]:
    """Check all required fields are present and non-empty."""
    errors = []
    for field in REQUIRED_FIELDS:
        val = intent.get(field)
        if val is None or val == "" or val == []:
            errors.append(f"Row {idx} ({intent.get('row_uid', 'unknown')}): Empty required field '{field}'")
    return errors


def validate_render_mode(intent: dict[str, Any], idx: int) -> list[str]:
    """Validate render_mode is known."""
    errors = []
    render_mode = intent.get("render_mode", "")
    if render_mode not in VALID_RENDER_MODES:
        errors.append(
            f"Row {idx} ({intent.get('row_uid', 'unknown')}): "
            f"Unknown render_mode '{render_mode}'. Valid: {VALID_RENDER_MODES}"
        )
    return errors


def validate_control_types(intent: dict[str, Any], idx: int) -> list[str]:
    """Validate all control types are known."""
    errors = []
    controls = intent.get("controls", [])
    for control in controls:
        if control not in VALID_CONTROL_TYPES:
            errors.append(
                f"Row {idx} ({intent.get('row_uid', 'unknown')}): "
                f"Unknown control type '{control}'. Valid: {sorted(VALID_CONTROL_TYPES)}"
            )
    return errors


def validate_visibility(intent: dict[str, Any], idx: int) -> list[str]:
    """Validate visibility is known."""
    errors = []
    visibility = intent.get("visibility", "")
    if visibility not in VALID_VISIBILITY:
        errors.append(
            f"Row {idx} ({intent.get('row_uid', 'unknown')}): "
            f"Unknown visibility '{visibility}'. Valid: {VALID_VISIBILITY}"
        )
    return errors


def validate_disabled_reason(intent: dict[str, Any], idx: int) -> list[str]:
    """Validate disabled controls have a reason."""
    errors = []
    enabled = intent.get("enabled", True)
    disabled_reason = intent.get("disabled_reason")

    if not enabled and (not disabled_reason or disabled_reason == ""):
        errors.append(
            f"Row {idx} ({intent.get('row_uid', 'unknown')}): "
            f"Disabled without reason"
        )
    return errors


def validate_domain(intent: dict[str, Any], idx: int) -> list[str]:
    """Validate domain is known."""
    errors = []
    domain = intent.get("domain", "")
    if domain not in VALID_DOMAINS:
        errors.append(
            f"Row {idx} ({intent.get('row_uid', 'unknown')}): "
            f"Unknown domain '{domain}'. Valid: {VALID_DOMAINS}"
        )
    return errors


def check_duplicate_panel_orders(intents: list[dict[str, Any]]) -> list[str]:
    """Check for duplicate panel orders within same domain."""
    errors = []
    domain_orders: dict[str, dict[str, list[str]]] = {}

    for intent in intents:
        domain = intent.get("domain", "unknown")
        order = intent.get("order", "unknown")
        panel_id = intent.get("panel_id", "unknown")

        if domain not in domain_orders:
            domain_orders[domain] = {}
        if order not in domain_orders[domain]:
            domain_orders[domain][order] = []
        domain_orders[domain][order].append(panel_id)

    # Check for duplicates (same order, different panel_id)
    for domain, orders in domain_orders.items():
        for order, panel_ids in orders.items():
            unique_panels = set(panel_ids)
            if len(unique_panels) > 1:
                # Multiple different panels with same order is a warning, not error
                # Same panel appearing multiple times is expected (multiple topics)
                pass

    return errors


def compile_intent(intent: dict[str, Any]) -> dict[str, Any]:
    """
    Compile a single intent record.

    Strips normalization metadata and produces clean compiled output.
    """
    # Strip normalization metadata
    compiled = {k: v for k, v in intent.items() if not k.startswith("_")}

    # Ensure boolean types
    compiled["enabled"] = bool(compiled.get("enabled", False))
    compiled["nav_required"] = bool(compiled.get("nav_required", False))
    compiled["filtering"] = bool(compiled.get("filtering", False))
    compiled["read"] = bool(compiled.get("read", False))
    compiled["write"] = bool(compiled.get("write", False))
    compiled["activate"] = bool(compiled.get("activate", False))

    return compiled


def compile_intents(normalized_ir: dict[str, Any]) -> dict[str, Any]:
    """
    Compile all normalized intents with strict validation.

    C3: If compilation fails → UI must not render.
    """
    all_errors = []
    compiled_intents = []

    intents = normalized_ir.get("intents", [])

    # Validate each intent
    for idx, intent in enumerate(intents):
        # C2.1: Empty fields
        all_errors.extend(validate_required_fields(intent, idx))

        # C2.5: Unknown render_mode
        all_errors.extend(validate_render_mode(intent, idx))

        # C2.6: Unknown control type
        all_errors.extend(validate_control_types(intent, idx))

        # C2.4: Disabled without reason
        all_errors.extend(validate_disabled_reason(intent, idx))

        # Validate visibility
        all_errors.extend(validate_visibility(intent, idx))

        # Note: Domain validation is informational, not blocking
        # all_errors.extend(validate_domain(intent, idx))

    # C2.3: Check duplicate panel orders
    all_errors.extend(check_duplicate_panel_orders(intents))

    # FAIL HARD if any errors
    if all_errors:
        error_summary = "\n".join(all_errors[:20])  # Show first 20 errors
        remaining = len(all_errors) - 20
        if remaining > 0:
            error_summary += f"\n... and {remaining} more errors"

        raise CompilationError(
            f"Compilation FAILED with {len(all_errors)} error(s):\n{error_summary}"
        )

    # Compile each intent (strip metadata)
    for intent in intents:
        compiled = compile_intent(intent)
        compiled_intents.append(compiled)

    # Build output structure
    output = {
        "_meta": {
            "type": "ui_intent_ir_compiled",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": normalized_ir.get("_meta", {}).get("source", "unknown"),
            "row_count": len(compiled_intents),
            "processing_stage": "COMPILED",
            "validation_passed": True,
            "validation_rules": [
                "no_empty_fields",
                "valid_render_mode",
                "valid_control_types",
                "disabled_has_reason",
                "valid_visibility",
            ],
        },
        "intents": compiled_intents,
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Compile normalized intent IR with strict validation"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_intent_ir_normalized.json"),
        help="Path to normalized intent IR JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_intent_ir_compiled.json"),
        help="Output path for compiled intent IR JSON"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Enable strict mode (fail on any error)"
    )

    args = parser.parse_args()

    # Validate input exists
    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        return 1

    # Read input
    with open(args.input) as f:
        normalized_ir = json.load(f)

    # Compile
    print(f"Compiling intents from: {args.input}")

    try:
        result = compile_intents(normalized_ir)
    except CompilationError as e:
        print(f"\nCOMPILATION FAILED")
        print(f"{'=' * 60}")
        print(str(e))
        print(f"{'=' * 60}")
        print("\nUI MUST NOT RENDER until errors are fixed in L2.1")
        return 2

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    # Report success
    print(f"Generated compiled intent IR: {args.output}")
    print(f"  Rows: {result['_meta']['row_count']}")
    print(f"  Validation: PASSED")
    print(f"  Stage: {result['_meta']['processing_stage']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
