# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Shadow decision comparator — compares current vs candidate decision outcomes
# Product: system-wide
# Temporal:
#   Trigger: operation dispatch (shadow mode)
#   Execution: sync
# Callers: L4 operation_registry (when shadow mode enabled)
# Allowed Imports: stdlib only
# Forbidden Imports: FastAPI, Starlette, DB, ORM
# Reference: BA-24 Business Assurance Guardrails
# artifact_class: CODE

"""
Shadow decision comparator for canary/shadow execution.

Compares current vs candidate decision outcomes during shadow mode,
producing structured comparison results with severity classification.
Used by the operation registry to evaluate candidate decision paths
before promotion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

__all__ = [
    "DecisionOutcome",
    "ShadowComparisonResult",
    "compare_decisions",
    "format_comparison_report",
]


@dataclass
class DecisionOutcome:
    """Represents the outcome of a single decision evaluation."""

    operation: str
    outcome: str  # "ALLOW" | "DENY" | "DEFERRED"
    reason: str
    invariants_checked: List[str]
    timestamp: str

    def __post_init__(self) -> None:
        valid_outcomes = ("ALLOW", "DENY", "DEFERRED")
        if self.outcome not in valid_outcomes:
            raise ValueError(
                f"outcome must be one of {valid_outcomes}, got {self.outcome!r}"
            )


@dataclass
class ShadowComparisonResult:
    """Result of comparing current vs candidate decision outcomes."""

    operation: str
    current: DecisionOutcome
    candidate: DecisionOutcome
    match: bool
    diffs: List[str]
    severity: str  # "NONE" | "LOW" | "HIGH" | "CRITICAL"

    def __post_init__(self) -> None:
        valid_severities = ("NONE", "LOW", "HIGH", "CRITICAL")
        if self.severity not in valid_severities:
            raise ValueError(
                f"severity must be one of {valid_severities}, got {self.severity!r}"
            )


def compare_decisions(
    current: DecisionOutcome,
    candidate: DecisionOutcome,
) -> ShadowComparisonResult:
    """
    Compare current and candidate decision outcomes.

    Severity classification:
      - CRITICAL: outcomes differ (ALLOW vs DENY, etc.)
      - HIGH: invariants_checked differ
      - LOW: only reasons differ
      - NONE: full match

    When multiple differences exist, the highest severity wins.

    Args:
        current: The decision outcome from the current (production) path.
        candidate: The decision outcome from the candidate path.

    Returns:
        ShadowComparisonResult with match status, diffs, and severity.
    """
    diffs: List[str] = []
    operation = current.operation

    # --- Compare outcome ---
    outcome_differs = current.outcome != candidate.outcome
    if outcome_differs:
        diffs.append(
            f"outcome: current={current.outcome!r}, candidate={candidate.outcome!r}"
        )

    # --- Compare invariants_checked ---
    current_invariants = sorted(current.invariants_checked)
    candidate_invariants = sorted(candidate.invariants_checked)
    invariants_differ = current_invariants != candidate_invariants

    if invariants_differ:
        missing_from_candidate = sorted(
            set(current.invariants_checked) - set(candidate.invariants_checked)
        )
        extra_in_candidate = sorted(
            set(candidate.invariants_checked) - set(current.invariants_checked)
        )
        parts: List[str] = []
        if missing_from_candidate:
            parts.append(f"missing_from_candidate={missing_from_candidate}")
        if extra_in_candidate:
            parts.append(f"extra_in_candidate={extra_in_candidate}")
        diffs.append(f"invariants_checked: {'; '.join(parts)}")

    # --- Compare reason ---
    reason_differs = current.reason != candidate.reason
    if reason_differs:
        diffs.append(
            f"reason: current={current.reason!r}, candidate={candidate.reason!r}"
        )

    # --- Determine severity (highest wins) ---
    if outcome_differs:
        severity = "CRITICAL"
    elif invariants_differ:
        severity = "HIGH"
    elif reason_differs:
        severity = "LOW"
    else:
        severity = "NONE"

    match = severity == "NONE"

    return ShadowComparisonResult(
        operation=operation,
        current=current,
        candidate=candidate,
        match=match,
        diffs=diffs,
        severity=severity,
    )


def format_comparison_report(results: List[ShadowComparisonResult]) -> str:
    """
    Format a list of shadow comparison results as a markdown report.

    Args:
        results: List of ShadowComparisonResult from compare_decisions().

    Returns:
        A markdown-formatted string summarizing all comparisons.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines: List[str] = [
        "# Shadow Comparison Report",
        "",
        f"**Generated:** {now}",
        f"**Total comparisons:** {len(results)}",
    ]

    # --- Summary counts ---
    severity_counts = {"NONE": 0, "LOW": 0, "HIGH": 0, "CRITICAL": 0}
    for r in results:
        severity_counts[r.severity] += 1

    match_count = sum(1 for r in results if r.match)
    mismatch_count = len(results) - match_count

    lines.extend([
        f"**Matches:** {match_count}",
        f"**Mismatches:** {mismatch_count}",
        "",
        "## Severity Summary",
        "",
        "| Severity | Count |",
        "|----------|-------|",
        f"| CRITICAL | {severity_counts['CRITICAL']} |",
        f"| HIGH | {severity_counts['HIGH']} |",
        f"| LOW | {severity_counts['LOW']} |",
        f"| NONE | {severity_counts['NONE']} |",
        "",
    ])

    # --- Detail per comparison ---
    if results:
        lines.extend([
            "## Comparison Details",
            "",
        ])

        for i, r in enumerate(results, 1):
            lines.extend([
                f"### {i}. `{r.operation}` — {r.severity}",
                "",
                f"- **Match:** {r.match}",
                f"- **Current outcome:** {r.current.outcome} ({r.current.reason})",
                f"- **Candidate outcome:** {r.candidate.outcome} ({r.candidate.reason})",
                f"- **Current invariants:** {', '.join(r.current.invariants_checked) or '(none)'}",
                f"- **Candidate invariants:** {', '.join(r.candidate.invariants_checked) or '(none)'}",
            ])

            if r.diffs:
                lines.append("- **Diffs:**")
                for diff in r.diffs:
                    lines.append(f"  - {diff}")
            else:
                lines.append("- **Diffs:** (none)")

            lines.append("")

    # --- Footer ---
    lines.extend([
        "---",
        "",
        "_Report generated by `shadow_compare.py` (BA-24)_",
    ])

    return "\n".join(lines)
