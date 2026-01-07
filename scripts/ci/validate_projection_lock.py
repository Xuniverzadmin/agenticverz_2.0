#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI (pre-merge)
#   Execution: sync
# Role: Validate ui_projection_lock.json integrity (NO manual edits)
# Callers: CI pipeline
# Allowed Imports: json, hashlib
# Forbidden Imports: None
# Reference: L2.1 UI Projection Pipeline

"""
F1: CI Validation for UI Projection Lock

RULES:
- Projection lock must exist
- Projection lock must be valid JSON
- Projection lock must have LOCKED stage
- Projection lock must have frozen=true
- Projection lock must have editable=false
- Checksum must match regenerated output (no manual edits)

F2: Edit Prevention
- If checksum mismatch detected, fail CI
- Manual edits to ui_projection_lock.json are FORBIDDEN
- All changes must go through the pipeline
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def compute_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of file contents."""
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def validate_schema(data: dict) -> list[str]:
    """Validate projection lock schema."""
    errors = []

    # Check _meta
    meta = data.get("_meta", {})
    if meta.get("type") != "ui_projection_lock":
        errors.append(f"Invalid type: expected 'ui_projection_lock', got '{meta.get('type')}'")
    if meta.get("processing_stage") != "LOCKED":
        errors.append(f"Invalid stage: expected 'LOCKED', got '{meta.get('processing_stage')}'")
    if meta.get("frozen") is not True:
        errors.append(f"Invalid frozen: expected true, got {meta.get('frozen')}")
    if meta.get("editable") is not False:
        errors.append(f"Invalid editable: expected false, got {meta.get('editable')}")

    # Check _contract
    contract = data.get("_contract", {})
    required_contract_fields = [
        "renderer_must_consume_only_this_file",
        "no_optional_fields",
        "explicit_ordering_everywhere",
        "all_controls_have_type",
        "all_panels_have_render_mode",
        "all_items_have_visibility",
    ]
    for field in required_contract_fields:
        if not contract.get(field):
            errors.append(f"Contract violation: {field} must be true")

    # Check domains exist
    domains = data.get("domains", [])
    if not domains:
        errors.append("No domains found in projection lock")

    return errors


def regenerate_and_compare(lock_path: Path) -> tuple[bool, str]:
    """
    Regenerate projection lock and compare with current.

    Returns (match, message).
    """
    # Create temp file for regenerated output
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # Run the full pipeline
        result = subprocess.run(
            [
                "python3", "scripts/tools/l2_raw_intent_parser.py",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, f"Parser failed: {result.stderr}"

        result = subprocess.run(
            [
                "python3", "scripts/tools/intent_normalizer.py",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, f"Normalizer failed: {result.stderr}"

        result = subprocess.run(
            [
                "python3", "scripts/tools/intent_compiler.py",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, f"Compiler failed: {result.stderr}"

        result = subprocess.run(
            [
                "python3", "scripts/tools/ui_projection_builder.py",
                "--output", str(temp_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, f"Builder failed: {result.stderr}"

        # Compare checksums (ignoring generated_at timestamp)
        with open(lock_path) as f:
            current_data = json.load(f)
        with open(temp_path) as f:
            regenerated_data = json.load(f)

        # Remove timestamp for comparison
        current_data["_meta"]["generated_at"] = ""
        regenerated_data["_meta"]["generated_at"] = ""

        current_json = json.dumps(current_data, sort_keys=True)
        regenerated_json = json.dumps(regenerated_data, sort_keys=True)

        if current_json != regenerated_json:
            return False, "Projection lock has been manually edited! Regenerate via pipeline."

        return True, "Projection lock matches pipeline output"

    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Validate UI projection lock integrity"
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_projection_lock.json"),
        help="Path to projection lock JSON"
    )
    parser.add_argument(
        "--skip-regenerate",
        action="store_true",
        help="Skip regeneration comparison (schema validation only)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    print(f"Validating projection lock: {args.lock}")
    print("=" * 60)

    # Check file exists
    if not args.lock.exists():
        print(f"FAIL: Projection lock not found: {args.lock}")
        return 1

    # Load and parse JSON
    try:
        with open(args.lock) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON: {e}")
        return 1

    # Schema validation
    print("\n1. Schema Validation")
    schema_errors = validate_schema(data)
    if schema_errors:
        print("   FAIL: Schema errors found:")
        for error in schema_errors:
            print(f"     - {error}")
        return 2
    print("   PASS: Schema valid")

    # Statistics
    print("\n2. Statistics")
    stats = data.get("_statistics", {})
    print(f"   Domains: {stats.get('domain_count', 0)}")
    print(f"   Panels: {stats.get('panel_count', 0)}")
    print(f"   Controls: {stats.get('control_count', 0)}")

    # Regeneration comparison
    if not args.skip_regenerate:
        print("\n3. Integrity Check (regenerate & compare)")
        match, message = regenerate_and_compare(args.lock)
        if not match:
            print(f"   FAIL: {message}")
            print("\n   To fix: Run the full pipeline to regenerate the lock:")
            print("   python3 scripts/tools/l2_raw_intent_parser.py && \\")
            print("   python3 scripts/tools/intent_normalizer.py && \\")
            print("   python3 scripts/tools/intent_compiler.py && \\")
            print("   python3 scripts/tools/ui_projection_builder.py")
            return 3
        print(f"   PASS: {message}")
    else:
        print("\n3. Integrity Check: SKIPPED (--skip-regenerate)")

    print("\n" + "=" * 60)
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
