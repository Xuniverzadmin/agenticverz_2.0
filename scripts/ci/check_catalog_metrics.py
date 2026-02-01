#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Verify failure catalog metric labels match expected Prometheus format.
# artifact_class: CODE
"""
Verify failure catalog metric labels match expected Prometheus format.

Usage:
    python scripts/ci/check_catalog_metrics.py
    python scripts/ci/check_catalog_metrics.py --staging-url https://staging.example.com

Exit codes:
    0 - All checks passed
    1 - Validation errors found
"""

import argparse
import json
import re
import sys
from pathlib import Path

CATALOG_PATH = (
    Path(__file__).parent.parent.parent / "backend/app/data/failure_catalog.json"
)

# Prometheus label naming rules
LABEL_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
LABEL_VALUE_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def validate_label_name(name: str) -> bool:
    """Validate Prometheus label name format."""
    return bool(LABEL_REGEX.match(name))


def validate_label_value(value: str) -> bool:
    """Validate Prometheus label value format (basic check)."""
    # Allow alphanumeric, underscore, hyphen, dot
    return bool(LABEL_VALUE_REGEX.match(value))


def check_catalog_labels(catalog_path: Path) -> list:
    """Check all metric labels in catalog for validity."""
    errors = []

    with open(catalog_path) as f:
        catalog = json.load(f)

    for code, entry in catalog.get("errors", {}).items():
        labels = entry.get("metrics_labels", {})

        if not labels:
            errors.append(f"{code}: missing metrics_labels")
            continue

        for label_name, label_value in labels.items():
            if not validate_label_name(label_name):
                errors.append(f"{code}: invalid label name '{label_name}'")

            if not validate_label_value(str(label_value)):
                errors.append(
                    f"{code}: invalid label value '{label_value}' for '{label_name}'"
                )

    return errors


def check_required_labels(catalog_path: Path) -> list:
    """Ensure all entries have required labels."""
    errors = []
    required = {"error_type", "category"}

    with open(catalog_path) as f:
        catalog = json.load(f)

    for code, entry in catalog.get("errors", {}).items():
        labels = set(entry.get("metrics_labels", {}).keys())
        missing = required - labels
        if missing:
            errors.append(f"{code}: missing required labels {missing}")

    return errors


def check_label_consistency(catalog_path: Path) -> list:
    """Check that category labels match entry categories."""
    errors = []

    with open(catalog_path) as f:
        catalog = json.load(f)

    for code, entry in catalog.get("errors", {}).items():
        declared_category = entry.get("category", "").lower()
        label_category = entry.get("metrics_labels", {}).get("category", "")

        if declared_category != label_category:
            errors.append(
                f"{code}: category mismatch - entry={declared_category}, label={label_category}"
            )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate failure catalog metric labels"
    )
    parser.add_argument(
        "--staging-url", help="Optional staging URL to compare against live metrics"
    )
    parser.add_argument(
        "--catalog", type=Path, default=CATALOG_PATH, help="Path to catalog JSON"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("FAILURE CATALOG METRIC LABEL VALIDATION")
    print("=" * 60)

    all_errors = []

    # Check 1: Label format validity
    print("\n[1/3] Checking label format validity...")
    errors = check_catalog_labels(args.catalog)
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All labels have valid format")

    # Check 2: Required labels present
    print("\n[2/3] Checking required labels...")
    errors = check_required_labels(args.catalog)
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All required labels present")

    # Check 3: Category consistency
    print("\n[3/3] Checking label/entry consistency...")
    errors = check_label_consistency(args.catalog)
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ Labels consistent with entries")

    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ VALIDATION FAILED - {len(all_errors)} errors")
        print("=" * 60)
        return 1
    else:
        print("✅ VALIDATION PASSED")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
