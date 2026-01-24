# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   houseofcards/customer/incidents/engines/postmortem_service.py
#   Class: ResolutionSummary
#
# Superseding Type:
#   houseofcards/customer/incidents/facades/incidents_facade.py
#   Class: ResolutionSummaryResult (QUARANTINED)
#
# Reason for Quarantine:
#   INC-DUP-005 — 100% field overlap with engine DTO
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
# ============================================================

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResolutionSummaryResult:
    """
    QUARANTINED — Use ResolutionSummary from postmortem_service.py instead.

    Summary of incident resolution.
    """

    incident_id: str
    title: str
    category: Optional[str]
    severity: str
    resolution_method: Optional[str]
    time_to_resolution_ms: Optional[int]
    evidence_count: int
    recovery_attempted: bool
