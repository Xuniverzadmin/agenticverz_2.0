#!/usr/bin/env python3
"""
Mypy Type Safety Zones Validator (PIN-121)

Validates mypy errors against zone-based thresholds:
- Zone A (Critical): Blocks on ANY new errors
- Zone B (Standard): Warns only
- Zone C (Flexible): Baseline freeze, no enforcement

Usage:
    python scripts/mypy_zones.py           # Full check
    python scripts/mypy_zones.py --zone-a  # Zone A only (for pre-commit)
    python scripts/mypy_zones.py --report  # Generate zone report
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# =============================================================================
# ZONE DEFINITIONS
# =============================================================================

ZONE_A_CRITICAL = [
    "app/policy/ir/",
    "app/policy/ast/",
    "app/policy/runtime/deterministic_engine.py",
    "app/workflow/engine.py",
    "app/workflow/canonicalize.py",
    "app/services/certificate.py",
    "app/services/evidence_report.py",
    "app/traces/pg_store.py",
    "app/utils/deterministic.py",
    "app/utils/canonical_json.py",
]

ZONE_B_STANDARD = [
    "app/api/",
    "app/skills/",
    "app/agents/",
    "app/services/",
    "app/planner/",
    "app/planners/",
    "app/integrations/",
    "app/memory/",
    "app/storage/",
    "app/auth/",
    "app/policy/validators/",
    "app/policy/optimizer/",
    "app/traces/redact.py",
]

ZONE_C_FLEXIBLE = [
    "app/workflow/",  # All workflow (metrics, logging, etc.)
    "app/traces/",  # All traces (except pg_store in Zone A)
    "app/utils/",  # All utils (except deterministic/canonical in Zone A)
    "app/config/",
    "app/logging_config.py",
    "app/worker/",
    "app/workers/",
    "app/cli.py",
    "app/schemas/",
    "app/main.py",  # Lifecycle globals
    "app/models/",  # SQLModel definitions
    "app/routing/",  # CARE routing
    "app/policy/",  # Catch-all for policy (Zone A has specific overrides)
    "app/budgetllm/",  # BudgetLLM
    "app/costsim/",  # Cost simulation
    "app/db",  # Database connections
    "app/runtime/",  # Runtime replay
    "app/tasks/",  # Background tasks
    "app/database",  # Database utilities
]

# Baseline error counts per zone (frozen as of M29, 2025-12-24)
BASELINE = {
    "zone_a": 38,  # IR builder, evidence report, pg_store, canonicalize
    "zone_b": 630,  # API, skills, integrations, agents, validators
    "zone_c": 400,  # Workflow, traces, utils, workers, main.py, models, tasks (with buffer)
}


@dataclass
class ZoneResult:
    zone: str
    errors: list[str]
    baseline: int
    passed: bool


def get_zone(filepath: str) -> str:
    """Determine which zone a file belongs to.

    Zone priority: A (critical) > B (standard) > C (flexible) > fallback to C
    Any app/ file not explicitly zoned goes to Zone C (flexible).
    """
    for pattern in ZONE_A_CRITICAL:
        if filepath.startswith(pattern):
            return "zone_a"
    for pattern in ZONE_B_STANDARD:
        if filepath.startswith(pattern):
            return "zone_b"
    for pattern in ZONE_C_FLEXIBLE:
        if filepath.startswith(pattern):
            return "zone_c"
    # Fallback: any app/ file goes to Zone C (flexible)
    if filepath.startswith("app/"):
        return "zone_c"
    return "unzoned"


def run_mypy() -> list[str]:
    """Run mypy and capture output."""
    result = subprocess.run(
        ["mypy", "app/", "--ignore-missing-imports", "--show-error-codes"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.stdout.strip().split("\n") if result.stdout else []


def parse_errors(lines: list[str]) -> dict[str, list[str]]:
    """Parse mypy output into zone-categorized errors."""
    zones = {"zone_a": [], "zone_b": [], "zone_c": [], "unzoned": []}

    for line in lines:
        if ": error:" in line:
            # Extract filepath from error line
            filepath = line.split(":")[0] if ":" in line else ""
            zone = get_zone(filepath)
            zones[zone].append(line)

    return zones


def check_zones(zone_errors: dict[str, list[str]], zone_a_only: bool = False) -> list[ZoneResult]:
    """Check each zone against its baseline."""
    results = []

    # Zone A: Critical - block on ANY increase
    zone_a_count = len(zone_errors["zone_a"])
    zone_a_passed = zone_a_count <= BASELINE["zone_a"]
    results.append(
        ZoneResult(
            zone="Zone A (Critical)",
            errors=zone_errors["zone_a"],
            baseline=BASELINE["zone_a"],
            passed=zone_a_passed,
        )
    )

    if zone_a_only:
        return results

    # Zone B: Standard - warn but don't block
    results.append(
        ZoneResult(
            zone="Zone B (Standard)",
            errors=zone_errors["zone_b"],
            baseline=BASELINE["zone_b"],
            passed=True,  # Never blocks
        )
    )

    # Zone C: Flexible - baseline freeze only
    results.append(
        ZoneResult(
            zone="Zone C (Flexible)",
            errors=zone_errors["zone_c"],
            baseline=BASELINE["zone_c"],
            passed=True,  # Never blocks
        )
    )

    # Unzoned
    if zone_errors["unzoned"]:
        results.append(
            ZoneResult(
                zone="Unzoned",
                errors=zone_errors["unzoned"],
                baseline=0,
                passed=True,
            )
        )

    return results


def print_report(results: list[ZoneResult], verbose: bool = False) -> None:
    """Print zone validation report."""
    print("=" * 70)
    print("  MYPY TYPE SAFETY ZONES REPORT (PIN-121)")
    print("=" * 70)
    print()

    total_errors = sum(len(r.errors) for r in results)
    all_passed = all(r.passed for r in results)

    for result in results:
        count = len(result.errors)
        delta = count - result.baseline

        if result.passed:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(f"  {result.zone}")
        print(f"    Errors:   {count:>4} (baseline: {result.baseline})")
        print(f"    Delta:    {delta_str:>4}")
        print(f"    Status:   {status}")
        print()

        if verbose and result.errors:
            print("    Sample errors:")
            for err in result.errors[:5]:
                print(f"      {err[:80]}...")
            if len(result.errors) > 5:
                print(f"      ... and {len(result.errors) - 5} more")
            print()

    print("-" * 70)
    print(f"  Total Errors: {total_errors}")
    print(f"  Overall:      {'✅ PASS' if all_passed else '❌ FAIL'}")
    print("=" * 70)


def generate_baseline() -> None:
    """Generate new baseline from current state."""
    lines = run_mypy()
    zone_errors = parse_errors(lines)

    baseline = {
        "zone_a": len(zone_errors["zone_a"]),
        "zone_b": len(zone_errors["zone_b"]),
        "zone_c": len(zone_errors["zone_c"]),
    }

    print("New baseline (update BASELINE dict in this script):")
    print(json.dumps(baseline, indent=2))


def main() -> int:
    args = sys.argv[1:]

    if "--generate-baseline" in args:
        generate_baseline()
        return 0

    zone_a_only = "--zone-a" in args
    verbose = "--report" in args or "-v" in args

    print("Running mypy...")
    lines = run_mypy()
    zone_errors = parse_errors(lines)
    results = check_zones(zone_errors, zone_a_only=zone_a_only)

    print_report(results, verbose=verbose)

    # Exit code: 1 if any zone failed
    if not all(r.passed for r in results):
        print("\n❌ Zone A exceeded baseline - blocking commit")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
