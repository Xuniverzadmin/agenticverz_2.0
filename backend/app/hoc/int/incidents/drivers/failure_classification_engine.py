# capability_id: CAP-001
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api|worker (called by L5)
#   Execution: sync (REQUIRED - async forbidden)
# Role: Failure pattern classification and aggregation logic
# Callers: failure_aggregation.py (L5)
# Allowed Imports: L4 only (stdlib, dataclasses, typing, enum, other L4 engines)
# Forbidden Imports: L5, L6, L7, L8
# Reference: PIN-256 Phase E FIX-01
#
# Extraction Source: app/jobs/failure_aggregation.py
# Semantic Promotion: Failure signature computation, pattern aggregation, summary statistics
# BLCA Violations Resolved: L5 domain classification authority
#
# GOVERNANCE NOTE: This engine OWNS all classification decisions.
# L5 passes data. L4 returns decisions. No callbacks. No dependency injection.

from app.infra import FeatureIntent

# Phase-2.3: Feature Intent Declaration
# Pure domain logic - computes signatures, aggregates patterns, returns decisions
# No DB access, no filesystem, no network calls - purely computational
FEATURE_INTENT = FeatureIntent.PURE_QUERY

"""
Failure Classification Engine (L4)

Pure domain logic for failure pattern classification:
1. compute_signature() - Deterministic error signature for grouping
2. aggregate_patterns() - Group similar errors by signature (owns classification)
3. get_summary_stats() - Compute summary statistics

This engine contains NO:
- Database access
- Filesystem operations
- Network calls
- Time-dependent operations (timestamps passed as data)
- External state
- Callback/function injection from L5 (FORBIDDEN)
"""

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# L5 engine import (migrated to HOC per SWEEP-09)
# Classification authority from RecoveryRuleEngine - L5 owns it.
from app.hoc.cus.incidents.L5_engines.recovery_rule_engine import (
    classify_error_category,
    suggest_recovery_mode,
)


@dataclass
class FailurePattern:
    """Input: Raw failure pattern from database query."""

    error_code: str
    error_message: Optional[str]
    occurrence_count: int
    last_seen: Optional[str]  # ISO format string
    first_seen: Optional[str]  # ISO format string
    affected_skills: List[str] = field(default_factory=list)
    affected_tenants: List[str] = field(default_factory=list)
    sample_run_ids: List[str] = field(default_factory=list)


@dataclass
class AggregatedPattern:
    """Output: Aggregated failure pattern with classification."""

    signature: str
    primary_error_code: str
    all_error_codes: List[str]
    total_occurrences: int
    affected_skills: List[str]
    affected_tenants: List[str]
    examples: List[Dict[str, Any]]
    last_seen: Optional[str]
    first_seen: Optional[str]
    suggested_category: str
    suggested_recovery: str


@dataclass
class SummaryStats:
    """Output: Summary statistics for patterns."""

    total_patterns: int
    total_occurrences: int
    top_error_codes: List[Dict[str, Any]]
    most_affected_skills: List[Dict[str, Any]]


def compute_signature(error_code: str, error_message: Optional[str]) -> str:
    """
    Compute deterministic signature for error grouping.

    Uses SHA256 of normalized error code + message prefix.
    This is pure domain classification logic.

    Args:
        error_code: Error code string
        error_message: Optional error message

    Returns:
        16-character hex signature
    """
    normalized_code = (error_code or "unknown").upper().strip()
    # Take first 100 chars of message for grouping
    normalized_msg = (error_message or "")[:100].lower().strip()

    content = f"{normalized_code}:{normalized_msg}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# Local heuristics REMOVED - classification authority is in recovery_rule_engine.py (L4)
# No _suggest_category or _suggest_recovery functions here.
# No callback parameters. L4 owns the decision completely.


def aggregate_patterns(raw_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate patterns by signature for deduplication.

    Groups similar errors that may have slightly different messages.
    Classification decisions are made by THIS L4 engine using
    imported L4 authority from recovery_rule_engine.py.

    GOVERNANCE: This function receives DATA, returns DECISIONS.
    No callbacks. No function injection. L4 owns classification.

    Args:
        raw_patterns: List of raw pattern dicts from database (DATA ONLY)

    Returns:
        List of aggregated pattern dicts with classification decisions
    """
    grouped: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "signatures": [],
            "error_codes": set(),
            "total_occurrences": 0,
            "affected_skills": set(),
            "affected_tenants": set(),
            "examples": [],
            "last_seen": None,
            "first_seen": None,
        }
    )

    for pattern in raw_patterns:
        sig = compute_signature(pattern.get("error_code", ""), pattern.get("error_message"))
        group = grouped[sig]

        group["signatures"].append(sig)
        group["error_codes"].add(pattern.get("error_code", "UNKNOWN"))
        group["total_occurrences"] += pattern.get("occurrence_count", 0)
        group["affected_skills"].update(pattern.get("affected_skills", []))
        group["affected_tenants"].update(pattern.get("affected_tenants", []))

        # Track examples
        if len(group["examples"]) < 3:
            group["examples"].append(
                {
                    "error_code": pattern.get("error_code"),
                    "error_message": pattern.get("error_message"),
                    "occurrence_count": pattern.get("occurrence_count"),
                }
            )

        # Update timestamps
        last_seen = pattern.get("last_seen")
        first_seen = pattern.get("first_seen")

        if last_seen:
            if not group["last_seen"] or last_seen > group["last_seen"]:
                group["last_seen"] = last_seen
        if first_seen:
            if not group["first_seen"] or first_seen < group["first_seen"]:
                group["first_seen"] = first_seen

    # Convert to list
    result = []
    for sig, group in grouped.items():
        error_codes_list = list(group["error_codes"])
        result.append(
            {
                "signature": sig,
                "primary_error_code": error_codes_list[0] if error_codes_list else "UNKNOWN",
                "all_error_codes": error_codes_list,
                "total_occurrences": group["total_occurrences"],
                "affected_skills": list(group["affected_skills"]),
                "affected_tenants": list(group["affected_tenants"]),
                "examples": group["examples"],
                "last_seen": group["last_seen"],
                "first_seen": group["first_seen"],
                # L4 domain classification - authority from recovery_rule_engine.py (L4)
                # NO callbacks, NO injection - L4 owns these decisions completely
                "suggested_category": classify_error_category(error_codes_list),
                "suggested_recovery": suggest_recovery_mode(error_codes_list),
            }
        )

    # Sort by occurrences
    result.sort(key=lambda x: x["total_occurrences"], reverse=True)
    return result


def get_summary_stats(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics for logging/alerting.

    This is pure domain summarization logic.

    Args:
        patterns: List of aggregated patterns

    Returns:
        Summary statistics dict
    """
    if not patterns:
        return {
            "total_patterns": 0,
            "total_occurrences": 0,
            "top_error_codes": [],
            "most_affected_skills": [],
        }

    total_occurrences = sum(p.get("total_occurrences", 0) for p in patterns)

    # Top error codes
    code_counts: Dict[str, int] = defaultdict(int)
    for p in patterns:
        for code in p.get("all_error_codes", []):
            code_counts[code] += p.get("total_occurrences", 0)
    top_codes = sorted(code_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Most affected skills
    skill_counts: Dict[str, int] = defaultdict(int)
    for p in patterns:
        for skill in p.get("affected_skills", []):
            skill_counts[skill] += p.get("total_occurrences", 0)
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_patterns": len(patterns),
        "total_occurrences": total_occurrences,
        "top_error_codes": [{"code": c, "count": n} for c, n in top_codes],
        "most_affected_skills": [{"skill": s, "count": n} for s, n in top_skills],
    }
