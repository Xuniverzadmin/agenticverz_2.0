#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Role: Static checker — validates every critical operation has complete spec fields
# artifact_class: CODE

"""
Operation Spec Registry Checker (BA-07)

Reads OPERATION_SPEC_REGISTRY_V1.md, extracts each operation spec from the YAML
code blocks, and validates that every spec has all required fields populated.

Required fields per spec:
  - operation_name
  - domain
  - preconditions (at least 1)
  - postconditions (at least 1)
  - forbidden_states (at least 1)
  - idempotency
  - owner

Usage:
    PYTHONPATH=. python3 scripts/verification/check_operation_specs.py
    PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict

In --strict mode, advisory checks also cause a non-zero exit code.
Without --strict, only blocking failures cause exit 1.
"""

import argparse
import os
import re
import sys
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
REGISTRY_PATH = os.path.join(
    BACKEND_ROOT,
    "app/hoc/docs/architecture/usecases/OPERATION_SPEC_REGISTRY_V1.md",
)

REQUIRED_FIELDS = [
    "operation_name",
    "domain",
    "preconditions",
    "postconditions",
    "forbidden_states",
    "idempotency",
    "owner",
]

LIST_FIELDS = {"preconditions", "postconditions", "forbidden_states"}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def extract_yaml_blocks(content: str) -> list[str]:
    """Extract YAML code blocks from the markdown content."""
    pattern = r"```yaml\s*\n(.*?)```"
    return re.findall(pattern, content, re.DOTALL)


def parse_yaml_block(block: str) -> dict[str, Any]:
    """
    Parse a YAML-like code block into a dict.

    This is a lightweight parser that handles the specific format used in
    the spec registry: key-value lines and list items (prefixed with '- ').
    It does not require PyYAML.
    """
    spec: dict[str, Any] = {}
    current_key: str | None = None

    for line in block.split("\n"):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # List item (belongs to current_key)
        if stripped.startswith("- ") and current_key:
            value = stripped[2:].strip().strip('"').strip("'")
            if current_key not in spec:
                spec[current_key] = []
            if isinstance(spec[current_key], list):
                spec[current_key].append(value)
            continue

        # Key-value pair
        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value = stripped[colon_idx + 1:].strip().strip('"').strip("'")

            if value:
                spec[key] = value
            else:
                # Value on next lines (list or multiline)
                spec[key] = []

            current_key = key

    return spec


def load_specs() -> tuple[list[dict[str, Any]], str | None]:
    """
    Load and parse all operation specs from the registry markdown file.

    Returns:
        (specs, error_message) -- list of spec dicts, or None + error string.
    """
    if not os.path.isfile(REGISTRY_PATH):
        return [], f"Registry file not found: {REGISTRY_PATH}"

    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError as exc:
        return [], f"Failed to read registry file: {exc}"

    yaml_blocks = extract_yaml_blocks(content)
    if not yaml_blocks:
        return [], "No YAML code blocks found in registry file"

    specs = []
    for block in yaml_blocks:
        spec = parse_yaml_block(block)
        # Only include blocks that look like real operation specs (have spec_id
        # with a concrete SPEC-NNN value, not the template placeholder).
        spec_id = spec.get("spec_id", "")
        if spec_id and "NNN" not in spec_id and (
            spec_id.startswith("SPEC-") or "operation_name" in spec
        ):
            specs.append(spec)

    if not specs:
        return [], "No valid operation specs found in YAML blocks"

    return specs, None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_spec(spec: dict[str, Any], strict: bool = False) -> tuple[list[str], list[str]]:
    """
    Validate a single spec against required fields.

    Returns:
        (failures, warnings) -- lists of failure/warning messages.
    """
    failures: list[str] = []
    warnings: list[str] = []
    op_name = spec.get("operation_name", spec.get("spec_id", "<unknown>"))

    # Check required scalar fields
    for field in REQUIRED_FIELDS:
        if field in LIST_FIELDS:
            # Must be a non-empty list
            value = spec.get(field)
            if not value or (isinstance(value, list) and len(value) == 0):
                failures.append(f"missing or empty: {field}")
            elif isinstance(value, list):
                # Check that each entry is a non-empty string
                empty_entries = [i for i, v in enumerate(value) if not v or not v.strip()]
                if empty_entries:
                    failures.append(
                        f"{field} has empty entries at index(es): {empty_entries}"
                    )
        else:
            value = spec.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                failures.append(f"missing or empty: {field}")

    # Advisory: check idempotency value
    idempotency = spec.get("idempotency", "")
    if idempotency and idempotency.lower() not in ("yes", "no"):
        msg = f"idempotency should be 'yes' or 'no', got '{idempotency}'"
        if strict:
            failures.append(msg)
        else:
            warnings.append(msg)

    # Advisory: check domain is recognized
    recognized_domains = {
        "account", "api_keys", "integrations", "policies", "controls",
        "incidents", "logs", "activity", "analytics", "onboarding",
    }
    domain = spec.get("domain", "")
    if domain and domain.lower() not in recognized_domains:
        msg = f"domain '{domain}' is not in recognized domains: {sorted(recognized_domains)}"
        if strict:
            failures.append(msg)
        else:
            warnings.append(msg)

    # Advisory: owner path exists on disk
    owner = spec.get("owner", "")
    if owner:
        owner_path = os.path.join(BACKEND_ROOT, owner)
        if not os.path.isfile(owner_path):
            msg = f"owner file not found: {owner}"
            warnings.append(msg)

    return failures, warnings


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate operation spec registry (BA-07)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat advisory checks as failures (exit 1 on warnings).",
    )
    args = parser.parse_args()

    specs, err = load_specs()
    if err:
        print(f"[FAIL] load_registry — {err}")
        sys.exit(1)

    print(f"Loaded {len(specs)} operation specs from registry")
    print()

    total_pass = 0
    total_fail = 0
    total_warn = 0

    for spec in specs:
        op_name = spec.get("operation_name", spec.get("spec_id", "<unknown>"))
        failures, warnings = validate_spec(spec, strict=args.strict)

        if failures:
            missing_str = ", ".join(failures)
            print(f"[FAIL] {op_name} — missing: {missing_str}")
            total_fail += 1
        elif warnings:
            warn_str = ", ".join(warnings)
            print(f"[WARN] {op_name} — {warn_str}")
            total_warn += 1
            if args.strict:
                total_fail += 1
            else:
                total_pass += 1
        else:
            print(f"[PASS] {op_name} — all fields present")
            total_pass += 1

    print()
    print(
        f"Summary: {len(specs)} ops total, "
        f"{total_pass} passed, {total_fail} failed, {total_warn} warnings"
        + (" [strict]" if args.strict else "")
    )

    if total_fail > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
