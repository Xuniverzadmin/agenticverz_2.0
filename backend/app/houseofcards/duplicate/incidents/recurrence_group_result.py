# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   houseofcards/customer/incidents/engines/recurrence_analysis_service.py
#   Class: RecurrenceGroup
#
# Superseding Type:
#   houseofcards/customer/incidents/facades/incidents_facade.py
#   Class: RecurrenceGroupResult (QUARANTINED)
#
# Reason for Quarantine:
#   INC-DUP-001 — 100% field overlap with engine DTO
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
# ============================================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RecurrenceGroupResult:
    """
    QUARANTINED — Use RecurrenceGroup from recurrence_analysis_service.py instead.

    A group of recurring incidents.
    """

    category: str
    resolution_method: Optional[str]
    total_occurrences: int
    distinct_days: int
    occurrences_per_day: float
    first_occurrence: datetime
    last_occurrence: datetime
    recent_incident_ids: list[str]
