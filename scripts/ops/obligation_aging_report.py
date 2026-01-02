#!/usr/bin/env python3
"""
Obligation Aging Reporter (PIN-265 Enforcement)

Tracks how long infra obligations have been unfulfilled and creates
pressure for resolution.

Features:
- Shows age of each UNFULFILLED obligation in days
- Identifies stale obligations (>30 days unfulfilled)
- Supports DEFERRED status with expiry dates
- CI mode fails if obligations exceed max age without deferral

Rules:
1. UNFULFILLED obligations older than MAX_AGE_DAYS must be either:
   - PROMOTED (infra exists)
   - DEFERRED with reason + expiry
2. DEFERRED obligations past expiry automatically become CRITICAL
3. PROMOTED obligations that lose infra become REGRESSION alerts

Usage:
    python scripts/ops/obligation_aging_report.py
    python scripts/ops/obligation_aging_report.py --ci  # Exit 1 on stale
    python scripts/ops/obligation_aging_report.py --max-age 45

Exit codes:
    0 - All obligations within acceptable age
    1 - Stale obligations found (CI mode)
"""

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MAX_AGE_DAYS = 30
CRITICAL_AGE_DAYS = 60
REGISTRY_PATH = "docs/infra/INFRA_OBLIGATION_REGISTRY.yaml"


@dataclass
class ObligationAge:
    """Age analysis for an obligation."""

    id: str
    title: str
    status: str
    created_date: Optional[datetime]
    age_days: int
    deferred_until: Optional[datetime] = None
    deferred_reason: Optional[str] = None
    is_stale: bool = False
    is_critical: bool = False
    test_count: int = 0


def load_registry(base_path: Path) -> Dict[str, Any]:
    """Load the obligation registry."""
    registry_path = base_path / REGISTRY_PATH

    if not registry_path.exists():
        return {"obligations": []}

    with open(registry_path, "r") as f:
        return yaml.safe_load(f) or {"obligations": []}


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string."""
    if not date_str:
        return None

    # Handle various date formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue

    return None


def analyze_obligation(obligation: Dict[str, Any], max_age_days: int) -> ObligationAge:
    """
    Analyze a single obligation for age and staleness.
    """
    ob_id = obligation.get("id", "UNKNOWN")
    title = obligation.get("title", "")
    status = obligation.get("status", "UNFULFILLED")
    # Support both 'created_date' and 'created' field names
    created = parse_date(obligation.get("created_date") or obligation.get("created"))
    deferred_until = parse_date(obligation.get("deferred_until"))
    deferred_reason = obligation.get("deferred_reason")
    test_count = len(obligation.get("tests", []))

    # Calculate age
    if created:
        age_days = (datetime.now() - created).days
    else:
        # Assume worst case if no created date
        age_days = max_age_days + 1

    # Determine staleness
    is_stale = False
    is_critical = False

    if status == "UNFULFILLED":
        is_stale = age_days > max_age_days
        is_critical = age_days > CRITICAL_AGE_DAYS
    elif status == "PARTIAL":
        is_stale = age_days > max_age_days
        is_critical = age_days > CRITICAL_AGE_DAYS
    elif status == "DEFERRED":
        # Deferred obligations expire
        if deferred_until and datetime.now() > deferred_until:
            is_stale = True
            is_critical = True
    # PROMOTED obligations are never stale

    return ObligationAge(
        id=ob_id,
        title=title,
        status=status,
        created_date=created,
        age_days=age_days,
        deferred_until=deferred_until,
        deferred_reason=deferred_reason,
        is_stale=is_stale,
        is_critical=is_critical,
        test_count=test_count,
    )


def print_report(analyses: List[ObligationAge], max_age_days: int):
    """
    Print the aging report.
    """
    print("\n" + "=" * 70)
    print("INFRA OBLIGATION AGING REPORT")
    print("=" * 70)
    print(f"\nMax acceptable age: {max_age_days} days")
    print(f"Critical threshold: {CRITICAL_AGE_DAYS} days")
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Group by status
    by_status: Dict[str, List[ObligationAge]] = {}
    for a in analyses:
        if a.status not in by_status:
            by_status[a.status] = []
        by_status[a.status].append(a)

    # Summary
    print("\n" + "-" * 70)
    print("STATUS SUMMARY")
    print("-" * 70)

    status_order = [
        "CRITICAL",
        "UNFULFILLED",
        "PARTIAL",
        "DEFERRED",
        "PROMOTED",
        "DEPRECATED",
    ]
    for status in status_order:
        if status in by_status:
            items = by_status[status]
            stale_count = sum(1 for a in items if a.is_stale)
            test_count = sum(a.test_count for a in items)

            icon = {
                "PROMOTED": "✅",
                "UNFULFILLED": "⚠️ ",
                "PARTIAL": "🔶",
                "DEFERRED": "⏸️ ",
                "DEPRECATED": "🗑️ ",
            }.get(status, "❓")

            stale_note = f" ({stale_count} STALE)" if stale_count > 0 else ""
            print(
                f"  {icon} {status}: {len(items)} obligations, {test_count} tests{stale_note}"
            )

    # Critical alerts
    critical = [a for a in analyses if a.is_critical]
    if critical:
        print("\n" + "-" * 70)
        print("🚨 CRITICAL ALERTS")
        print("-" * 70)
        for a in sorted(critical, key=lambda x: -x.age_days):
            print(f"\n  [{a.id}] {a.title}")
            print(f"    Status: {a.status}")
            print(f"    Age: {a.age_days} days (CRITICAL > {CRITICAL_AGE_DAYS})")
            print(f"    Tests blocked: {a.test_count}")
            if a.status == "DEFERRED" and a.deferred_until:
                print(f"    Deferral expired: {a.deferred_until.strftime('%Y-%m-%d')}")

    # Stale (but not critical)
    stale = [a for a in analyses if a.is_stale and not a.is_critical]
    if stale:
        print("\n" + "-" * 70)
        print("⚠️  STALE OBLIGATIONS")
        print("-" * 70)
        for a in sorted(stale, key=lambda x: -x.age_days):
            print(f"\n  [{a.id}] {a.title}")
            print(f"    Status: {a.status}")
            print(f"    Age: {a.age_days} days (threshold: {max_age_days})")
            print(f"    Tests blocked: {a.test_count}")

    # Full obligation list
    print("\n" + "-" * 70)
    print("ALL OBLIGATIONS BY AGE")
    print("-" * 70)

    sorted_analyses = sorted(
        analyses, key=lambda x: (-x.age_days if x.status != "PROMOTED" else 0)
    )

    for a in sorted_analyses:
        status_icon = {
            "PROMOTED": "✅",
            "UNFULFILLED": "⚠️ " if a.is_stale else "📋",
            "PARTIAL": "🔶",
            "DEFERRED": "⏸️ ",
            "DEPRECATED": "🗑️ ",
        }.get(a.status, "❓")

        age_str = f"{a.age_days}d" if a.status != "PROMOTED" else "N/A"
        stale_marker = " [STALE]" if a.is_stale else ""
        critical_marker = " [CRITICAL]" if a.is_critical else ""

        print(
            f"  {status_icon} {a.id}: {a.status} ({age_str}){stale_marker}{critical_marker}"
        )
        print(f"      {a.title[:50]}{'...' if len(a.title) > 50 else ''}")
        if a.status == "DEFERRED" and a.deferred_reason:
            print(f"      Reason: {a.deferred_reason[:40]}...")

    print("\n" + "=" * 70)

    # Return counts
    return len(critical), len(stale)


def generate_action_items(
    analyses: List[ObligationAge], max_age_days: int
) -> List[str]:
    """
    Generate actionable items for stale obligations.
    """
    actions = []

    for a in analyses:
        if a.is_critical:
            actions.append(
                f"CRITICAL: [{a.id}] unfulfilled for {a.age_days} days - IMMEDIATE action required"
            )
        elif a.is_stale:
            actions.append(
                f"STALE: [{a.id}] requires resolution within {CRITICAL_AGE_DAYS - a.age_days} days"
            )

    return actions


def main():
    parser = argparse.ArgumentParser(description="Generate obligation aging report")
    parser.add_argument(
        "--ci", action="store_true", help="CI mode - exit 1 on stale obligations"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        help=f"Max acceptable age in days (default: {DEFAULT_MAX_AGE_DAYS})",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Resolve base path
    base_path = Path(__file__).parent.parent.parent

    # Load registry
    registry = load_registry(base_path)
    obligations = registry.get("obligations", [])

    if not obligations:
        print("No obligations found in registry")
        print(f"Expected path: {base_path / REGISTRY_PATH}")
        sys.exit(0)

    # Analyze each obligation
    analyses = [analyze_obligation(ob, args.max_age) for ob in obligations]

    # Generate report
    if args.json:
        import json

        output = {
            "generated_at": datetime.now().isoformat(),
            "max_age_days": args.max_age,
            "obligations": [
                {
                    "id": a.id,
                    "title": a.title,
                    "status": a.status,
                    "age_days": a.age_days,
                    "is_stale": a.is_stale,
                    "is_critical": a.is_critical,
                    "test_count": a.test_count,
                }
                for a in analyses
            ],
        }
        print(json.dumps(output, indent=2))
        critical_count = sum(1 for a in analyses if a.is_critical)
    else:
        critical_count, stale_count = print_report(analyses, args.max_age)

        # Action items
        actions = generate_action_items(analyses, args.max_age)
        if actions:
            print("\n📋 ACTION ITEMS:")
            for action in actions:
                print(f"  • {action}")

    # CI mode exit
    if args.ci:
        stale_or_critical = [a for a in analyses if a.is_stale or a.is_critical]
        if stale_or_critical:
            print(
                f"\n❌ CI FAILURE: {len(stale_or_critical)} stale/critical obligations found"
            )
            sys.exit(1)
        else:
            print("\n✅ All obligations within acceptable age")


if __name__ == "__main__":
    main()
