# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   hoc/cus/incidents/L5_engines/recurrence_analysis_service.py
#   Class: RecurrenceResult
#
# Superseding Type:
#   hoc/cus/incidents/facades/incidents_facade.py
#   Class: RecurrenceAnalysisResult (QUARANTINED)
#
# Reason for Quarantine:
#   INC-DUP-002 — 100% field overlap with engine DTO
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
# ============================================================

from dataclasses import dataclass
from datetime import datetime

from .recurrence_group_result import RecurrenceGroupResult


@dataclass
class RecurrenceAnalysisResult:
    """
    QUARANTINED — Use RecurrenceResult from recurrence_analysis_service.py instead.

    Recurrence analysis response.
    """

    groups: list[RecurrenceGroupResult]
    baseline_days: int
    total_recurring: int
    generated_at: datetime
