# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   hoc/cus/incidents/L5_engines/postmortem_service.py
#   Class: LearningInsight
#
# Superseding Type:
#   hoc/cus/incidents/facades/incidents_facade.py
#   Class: LearningInsightResult (QUARANTINED)
#
# Reason for Quarantine:
#   INC-DUP-006 — 100% field overlap with engine DTO
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
# ============================================================

from dataclasses import dataclass


@dataclass
class LearningInsightResult:
    """
    QUARANTINED — Use LearningInsight from postmortem_service.py instead.

    A learning insight from incident analysis.
    """

    insight_type: str  # prevention, detection, response, communication
    description: str
    confidence: float
    supporting_incident_ids: list[str]
