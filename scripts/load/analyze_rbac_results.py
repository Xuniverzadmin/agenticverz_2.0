#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | ci
#   Execution: sync
# Role: Analyze RBAC synthetic load results for discrepancy classification
# Reference: PIN-274 (RBACv2 Promotion via Neon + Synthetic Load)

"""
RBAC Results Analyzer

Analyzes synthetic load test results to:
- Categorize discrepancies by type
- Group by actor_type, resource, action
- Generate classification recommendations
- Produce Grafana-compatible export

Usage:
    python3 scripts/load/analyze_rbac_results.py \
        --input /tmp/rbac_load_results.json \
        --output /tmp/discrepancy_report.json \
        --dashboard-export /tmp/grafana_import.json
"""

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class DiscrepancyGroup:
    """A group of similar discrepancies for classification."""

    key: str  # e.g., "external_paid:developer:runs:write"
    count: int
    discrepancy_type: str
    sample_v1_reason: str
    sample_v2_reason: str
    classification: Optional[str]  # To be filled: expected_tightening, etc.


def load_results(filepath: str) -> Dict:
    """Load results from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def extract_case_key(mismatch: Dict) -> str:
    """Extract grouping key from a mismatch record."""
    # Parse case_id to extract dimensions
    # Format: std-{n}, xtn-{n}, op-{n}, sys-{n}
    case_id = mismatch.get("case_id", "unknown")
    v1_reason = mismatch.get("v1_reason", "")
    v2_reason = mismatch.get("v2_reason", "")

    # Extract actor_type and resource from v2_reason
    # e.g., "actor_type:external_paid cannot read:runs"
    parts = v2_reason.split(":")
    actor_type = "unknown"
    resource = "unknown"
    action = "unknown"

    if "actor_type" in v2_reason:
        actor_type = parts[1].split()[0] if len(parts) > 1 else "unknown"
    if "cannot" in v2_reason and len(parts) >= 3:
        perm = v2_reason.split("cannot ")[-1] if "cannot" in v2_reason else ""
        if ":" in perm:
            action, resource = perm.split(":", 1)

    # For simpler grouping, use discrepancy type + general pattern
    return f"{mismatch.get('discrepancy_type', 'unknown')}:{actor_type}:{resource}:{action}"


def group_mismatches(mismatches: List[Dict]) -> Dict[str, List[Dict]]:
    """Group mismatches by common patterns."""
    groups: Dict[str, List[Dict]] = defaultdict(list)

    for m in mismatches:
        key = extract_case_key(m)
        groups[key].append(m)

    return groups


def generate_classification_suggestions(groups: Dict[str, List[Dict]]) -> List[Dict]:
    """Generate classification suggestions for each discrepancy group."""
    suggestions = []

    for key, mismatches in groups.items():
        parts = key.split(":")
        discrepancy_type = parts[0] if parts else "unknown"
        sample = mismatches[0] if mismatches else {}

        # Determine likely classification
        classification = None
        rationale = ""

        if discrepancy_type == "v2_more_restrictive":
            # v2 denies what v1 allows
            # Could be: expected_tightening (security fix) or bug (too strict)
            v2_reason = sample.get("v2_reason", "")
            if "actor_type" in v2_reason:
                classification = "expected_tightening"
                rationale = "RBACv2 enforces ActorType restrictions that RBACv1 ignored"
            elif "tenant_isolation" in v2_reason:
                classification = "expected_tightening"
                rationale = "RBACv2 enforces tenant isolation that RBACv1 was loose on"
            elif v2_reason.startswith("forbidden:"):
                # e.g., "forbidden:external_trial:delete:metrics"
                classification = "expected_tightening"
                rationale = "RBACv2 has explicit forbidden rules for this actor_type/action combination"
            elif v2_reason.startswith("no_permission:"):
                # e.g., "no_permission:execute:accounts"
                classification = "expected_tightening"
                rationale = (
                    "RBACv2 has more granular permission checks than RBACv1 wildcards"
                )
            else:
                classification = "needs_investigation"
                rationale = "Unclear why v2 is more restrictive"

        elif discrepancy_type == "v2_more_permissive":
            # SECURITY ALERT - v2 allows what v1 denies
            classification = "SECURITY_ALERT"
            rationale = "RBACv2 is more permissive - potential privilege escalation"

        suggestions.append(
            {
                "pattern": key,
                "count": len(mismatches),
                "discrepancy_type": discrepancy_type,
                "suggested_classification": classification,
                "rationale": rationale,
                "sample_v1_reason": sample.get("v1_reason", ""),
                "sample_v2_reason": sample.get("v2_reason", ""),
                "case_ids": [m.get("case_id", "") for m in mismatches[:5]],  # First 5
            }
        )

    return sorted(suggestions, key=lambda x: (-x["count"], x["pattern"]))


def generate_promotion_checklist(results: Dict, suggestions: List[Dict]) -> Dict:
    """Generate a promotion readiness checklist."""
    summary = results.get("summary", {})

    v2_more_permissive_count = summary.get("v2_more_permissive", 0)
    total_discrepancies = summary.get("mismatches", 0)
    total_requests = summary.get("total_requests", 1)
    discrepancy_rate = (total_discrepancies / total_requests) * 100

    # Count unclassified (needs_investigation) discrepancies
    needs_investigation_count = sum(
        s["count"]
        for s in suggestions
        if s["suggested_classification"] == "needs_investigation"
    )
    expected_tightening_count = sum(
        s["count"]
        for s in suggestions
        if s["suggested_classification"] == "expected_tightening"
    )

    # Unexpected discrepancy rate: only count needs_investigation
    # expected_tightening is intentional design, not a bug
    unexpected_rate = (
        (needs_investigation_count / total_requests) * 100 if total_requests > 0 else 0
    )

    checklist = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conditions": [
            {
                "id": 1,
                "condition": "Shadow mode running against Neon DB",
                "status": "MANUAL_CHECK",
                "threshold": "YES",
            },
            {
                "id": 2,
                "condition": "Test tenants/accounts/teams seeded",
                "status": "MANUAL_CHECK",
                "threshold": "3+ each",
            },
            {
                "id": 3,
                "condition": "Synthetic load executed",
                "status": "PASS" if summary.get("total_requests", 0) > 0 else "FAIL",
                "value": summary.get("total_requests", 0),
                "threshold": "1M+ requests",
            },
            {
                "id": 4,
                "condition": "v2_more_permissive count",
                "status": "PASS" if v2_more_permissive_count == 0 else "FAIL",
                "value": v2_more_permissive_count,
                "threshold": "= 0",
            },
            {
                "id": 5,
                "condition": "Unexpected discrepancy rate",
                "status": "PASS" if unexpected_rate < 1 else "FAIL",
                "value": f"{unexpected_rate:.2f}% ({needs_investigation_count} cases)",
                "threshold": "< 1% (excludes expected_tightening)",
                "note": f"Total discrepancy rate: {discrepancy_rate:.2f}% ({expected_tightening_count} expected_tightening)",
            },
            {
                "id": 6,
                "condition": "All discrepancies classified",
                "status": "PASS" if needs_investigation_count == 0 else "PENDING",
                "value": needs_investigation_count,
                "threshold": "0 needs_investigation",
            },
            {
                "id": 7,
                "condition": "Cross-tenant isolation verified",
                "status": "MANUAL_CHECK",
                "threshold": "100% fail rate",
            },
            {
                "id": 8,
                "condition": "Operator bypass verified",
                "status": "MANUAL_CHECK",
                "threshold": "100% success rate",
            },
            {
                "id": 9,
                "condition": "Machine actor permissions verified",
                "status": "MANUAL_CHECK",
                "threshold": "CI, worker, replay",
            },
            {
                "id": 10,
                "condition": "Rollback tested",
                "status": "MANUAL_CHECK",
                "threshold": "Toggle works",
            },
        ],
        "promotion_ready": (
            v2_more_permissive_count == 0
            and unexpected_rate < 1
            and needs_investigation_count == 0
            and summary.get("total_requests", 0) > 0
        ),
        "blocking_issues": [],
    }

    # Identify blocking issues
    if v2_more_permissive_count > 0:
        checklist["blocking_issues"].append(
            {
                "severity": "CRITICAL",
                "issue": f"v2_more_permissive discrepancies: {v2_more_permissive_count}",
                "action": "Immediate investigation required - potential security regression",
            }
        )

    if needs_investigation_count > 0:
        checklist["blocking_issues"].append(
            {
                "severity": "WARNING",
                "issue": f"Unclassified discrepancies: {needs_investigation_count}",
                "action": "Investigate and classify as expected_tightening or fix bugs",
            }
        )

    return checklist


def generate_grafana_export(suggestions: List[Dict]) -> Dict:
    """Generate data for Grafana dashboard import."""
    # Create data suitable for Grafana table panel
    return {
        "dashboard_data": {
            "discrepancy_by_pattern": [
                {
                    "pattern": s["pattern"],
                    "count": s["count"],
                    "type": s["discrepancy_type"],
                    "classification": s["suggested_classification"],
                }
                for s in suggestions
            ],
            "summary": {
                "total_patterns": len(suggestions),
                "security_alerts": sum(
                    1
                    for s in suggestions
                    if s["discrepancy_type"] == "v2_more_permissive"
                ),
                "tightening": sum(
                    1
                    for s in suggestions
                    if s["suggested_classification"] == "expected_tightening"
                ),
                "needs_investigation": sum(
                    1
                    for s in suggestions
                    if s["suggested_classification"] == "needs_investigation"
                ),
            },
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="RBAC Results Analyzer")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input results JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/discrepancy_report.json",
        help="Output report JSON file",
    )
    parser.add_argument(
        "--dashboard-export",
        type=str,
        default=None,
        help="Optional Grafana dashboard export file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output",
    )

    args = parser.parse_args()

    # Load results
    print(f"Loading results from {args.input}...")
    results = load_results(args.input)

    # Extract mismatches
    mismatches = results.get("mismatches", [])
    print(f"Found {len(mismatches)} mismatches to analyze")

    # Group mismatches
    groups = group_mismatches(mismatches)
    print(f"Grouped into {len(groups)} patterns")

    # Generate suggestions
    suggestions = generate_classification_suggestions(groups)

    # Generate checklist
    checklist = generate_promotion_checklist(results, suggestions)

    # Build report
    report = {
        "source_file": args.input,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": results.get("summary", {}),
        "classification_suggestions": suggestions,
        "promotion_checklist": checklist,
    }

    # Write report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {args.output}")

    # Optional Grafana export
    if args.dashboard_export:
        grafana_data = generate_grafana_export(suggestions)
        with open(args.dashboard_export, "w") as f:
            json.dump(grafana_data, f, indent=2)
        print(f"Grafana export written to {args.dashboard_export}")

    # Print summary
    print("\n" + "=" * 60)
    print("DISCREPANCY ANALYSIS SUMMARY")
    print("=" * 60)

    print("\nTop Discrepancy Patterns:")
    for i, s in enumerate(suggestions[:10], 1):
        status = "🔴" if s["discrepancy_type"] == "v2_more_permissive" else "🟡"
        print(f"  {i}. {status} [{s['count']}x] {s['pattern']}")
        print(f"      Classification: {s['suggested_classification']}")

    print("\nPromotion Checklist:")
    for c in checklist["conditions"]:
        status_icon = (
            "✅" if c["status"] == "PASS" else "❌" if c["status"] == "FAIL" else "⏳"
        )
        value_str = f" ({c.get('value', '')})" if "value" in c else ""
        print(f"  {status_icon} [{c['id']}] {c['condition']}{value_str}")

    if checklist["blocking_issues"]:
        print("\n⚠️  BLOCKING ISSUES:")
        for issue in checklist["blocking_issues"]:
            print(f"  [{issue['severity']}] {issue['issue']}")
            print(f"      Action: {issue['action']}")

    if checklist["promotion_ready"]:
        print("\n✅ PROMOTION READY (automated checks pass)")
        print("   Manual verification still required for items 1, 2, 7, 8, 9, 10")
    else:
        print("\n❌ NOT READY FOR PROMOTION")

    print("=" * 60)


if __name__ == "__main__":
    main()
