#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Layer Compliance CI Check
# artifact_class: CODE
"""
Layer Compliance CI Check

Enforces layer architecture rules to prevent drift.

Exit codes:
  0 - All checks pass
  1 - Violations found (blocking)

Usage:
  python scripts/migration/layer_compliance_check.py
  python scripts/migration/layer_compliance_check.py --baseline docs/architecture/migration/layer_fit_report.json
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def load_report(path: Path) -> dict[str, Any]:
    """Load layer fit report."""
    with open(path) as f:
        return json.load(f)


def load_allowed_violations(path: Path) -> dict[str, Any]:
    """Load allowed violations registry."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def check_no_regression(current: dict, baseline: dict) -> list[str]:
    """Check that FIT files have not become MISFIT."""
    violations = []

    baseline_fit = {
        f["relative_path"]
        for f in baseline["files"]
        if f["classification"]["layer_fit"]
    }

    current_fit = {
        f["relative_path"]
        for f in current["files"]
        if f["classification"]["layer_fit"]
    }

    # Files that were FIT but are now MISFIT
    regressions = baseline_fit - current_fit
    for path in sorted(regressions):
        violations.append(f"REGRESSION: {path} was FIT, now MISFIT")

    return violations


def check_misfit_increase(current: dict, baseline: dict) -> list[str]:
    """Check that total MISFIT count has not increased."""
    violations = []

    baseline_misfit = baseline["meta"]["misfit_count"]
    current_misfit = current["meta"]["misfit_count"]

    if current_misfit > baseline_misfit:
        violations.append(
            f"MISFIT_INCREASE: Count increased from {baseline_misfit} to {current_misfit} "
            f"(+{current_misfit - baseline_misfit})"
        )

    return violations


def check_engine_purity(current: dict) -> list[str]:
    """Check that engine files don't import SQLAlchemy."""
    violations = []

    for f in current["files"]:
        path = f["relative_path"]
        if "/engines/" not in path:
            continue

        # Check for L6_DRIVER signals in engine files
        detected = f["classification"].get("detected_layers", {})
        if "L6" in detected and detected["L6"] > 0:
            action = f.get("refactor_action", "UNKNOWN")
            if action not in ["NO_ACTION", "HEADER_FIX_ONLY"]:
                # This is expected until Phase 2 completes
                # Check if it's in allowed violations
                violations.append(
                    f"ENGINE_IMPURE: {path} has {detected['L6']} L6 signals (action: {action})"
                )

    return violations


def check_new_file_layer(current: dict, baseline: dict) -> list[str]:
    """Check that new files have declared layers."""
    violations = []

    baseline_paths = {f["relative_path"] for f in baseline["files"]}
    current_paths = {f["relative_path"]: f for f in current["files"]}

    new_files = set(current_paths.keys()) - baseline_paths
    for path in sorted(new_files):
        f = current_paths[path]
        declared = f["classification"].get("declared_layer")
        if not declared or declared == "?":
            violations.append(f"NO_LAYER: New file {path} has no declared layer")

    return violations


def check_expiry(allowed: dict) -> list[str]:
    """Check for expired allowed violations."""
    violations = []
    today = datetime.now().date()

    for category in ["extract_authority", "split_file", "phase_2_deferrals", "phase_1_deferrals"]:
        entries = allowed.get(category, [])
        if not entries:
            continue
        for entry in entries:
            expires_raw = entry["expires"]
            # YAML may parse as date or string
            if isinstance(expires_raw, str):
                expiry = datetime.strptime(expires_raw, "%Y-%m-%d").date()
            else:
                expiry = expires_raw
            if expiry < today:
                violations.append(
                    f"EXPIRED: {entry['file']} ({entry['action']}) expired on {entry['expires']}"
                )

    return violations


def main():
    parser = argparse.ArgumentParser(description="Layer compliance check")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("docs/architecture/migration/layer_fit_report.json"),
        help="Baseline report to compare against"
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=None,
        help="Current report (if different from baseline)"
    )
    parser.add_argument(
        "--allowed",
        type=Path,
        default=Path("docs/architecture/migration/ALLOWED_VIOLATIONS.yaml"),
        help="Allowed violations registry"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on engine impurity (normally just warns until Phase 2)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("HOC LAYER COMPLIANCE CHECK")
    print("=" * 60)

    # Load reports
    if not args.baseline.exists():
        print(f"❌ Baseline not found: {args.baseline}")
        sys.exit(1)

    baseline = load_report(args.baseline)
    current = load_report(args.current) if args.current else baseline

    # Load allowed violations
    allowed = {}
    if args.allowed.exists():
        allowed = load_allowed_violations(args.allowed)

    all_violations = []

    # Run checks
    print("\n1. Checking for regressions (FIT → MISFIT)...")
    regressions = check_no_regression(current, baseline)
    all_violations.extend(regressions)
    print(f"   {'❌' if regressions else '✅'} {len(regressions)} regressions")

    print("\n2. Checking MISFIT count increase...")
    misfit_increase = check_misfit_increase(current, baseline)
    all_violations.extend(misfit_increase)
    print(f"   {'❌' if misfit_increase else '✅'} {len(misfit_increase)} issues")

    print("\n3. Checking new files have layers...")
    new_file_issues = check_new_file_layer(current, baseline)
    all_violations.extend(new_file_issues)
    print(f"   {'❌' if new_file_issues else '✅'} {len(new_file_issues)} issues")

    print("\n4. Checking engine purity...")
    engine_issues = check_engine_purity(current)
    if args.strict:
        all_violations.extend(engine_issues)
    # Non-strict: just report, don't fail (until Phase 2)
    print(f"   {'⚠️' if engine_issues else '✅'} {len(engine_issues)} impure engines")
    if not args.strict and engine_issues:
        print("   (warning only - use --strict to enforce)")

    print("\n5. Checking allowed violations expiry...")
    expiry_issues = check_expiry(allowed)
    all_violations.extend(expiry_issues)
    print(f"   {'❌' if expiry_issues else '✅'} {len(expiry_issues)} expired")

    # Summary
    print("\n" + "=" * 60)
    if all_violations:
        print(f"❌ FAILED: {len(all_violations)} violations")
        print("=" * 60)
        for v in all_violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print("✅ PASSED: All checks pass")
        print("=" * 60)

        # Print stats
        meta = current["meta"]
        print(f"\nStats:")
        print(f"  - Total files: {meta['files_classified']}")
        print(f"  - FIT: {meta['layer_fit_count']} ({meta['layer_fit_count'] * 100 / meta['files_classified']:.1f}%)")
        print(f"  - MISFIT: {meta['misfit_count']} ({meta['misfit_count'] * 100 / meta['files_classified']:.1f}%)")
        print(f"  - Work items: {meta['total_work_items']}")

        sys.exit(0)


if __name__ == "__main__":
    main()
