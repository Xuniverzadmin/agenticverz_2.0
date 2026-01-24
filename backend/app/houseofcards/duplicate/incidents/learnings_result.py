# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   houseofcards/customer/incidents/engines/postmortem_service.py
#   Class: PostMortemResult
#
# Superseding Type:
#   houseofcards/customer/incidents/facades/incidents_facade.py
#   Class: LearningsResult (QUARANTINED)
#
# Reason for Quarantine:
#   INC-DUP-007 — 100% field overlap with engine DTO
#   (Different name, same structure)
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
# ============================================================

from dataclasses import dataclass
from datetime import datetime

from .learning_insight_result import LearningInsightResult
from .resolution_summary_result import ResolutionSummaryResult


@dataclass
class LearningsResult:
    """
    QUARANTINED — Use PostMortemResult from postmortem_service.py instead.

    Incident learnings response.
    """

    incident_id: str
    resolution_summary: ResolutionSummaryResult
    similar_incidents: list[ResolutionSummaryResult]
    insights: list[LearningInsightResult]
    generated_at: datetime
