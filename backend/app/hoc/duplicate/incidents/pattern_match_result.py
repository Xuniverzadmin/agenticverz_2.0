# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   hoc/cus/incidents/L5_engines/incident_pattern_service.py
#   Class: PatternMatch
#
# Superseding Type:
#   hoc/cus/incidents/facades/incidents_facade.py
#   Class: PatternMatchResult (QUARANTINED)
#
# Reason for Quarantine:
#   INC-DUP-003 — 100% field overlap with engine DTO
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
# ============================================================

from dataclasses import dataclass


@dataclass
class PatternMatchResult:
    """
    QUARANTINED — Use PatternMatch from incident_pattern_service.py instead.

    A detected incident pattern.
    """

    pattern_type: str  # category_cluster, severity_spike, cascade_failure
    dimension: str  # category name, severity level, or source_run_id
    count: int
    incident_ids: list[str]
    confidence: float
