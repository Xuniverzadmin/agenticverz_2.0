# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   hoc/cus/incidents/L5_engines/incident_pattern_service.py
#   Class: PatternResult
#
# Superseding Type:
#   hoc/cus/incidents/facades/incidents_facade.py
#   Class: PatternDetectionResult (QUARANTINED)
#
# Reason for Quarantine:
#   INC-DUP-004 — 90% field overlap with engine DTO
#   (Facade adds window_hours field)
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
#   Note: Consider adding window_hours to canonical PatternResult
# ============================================================

from dataclasses import dataclass
from datetime import datetime

from .pattern_match_result import PatternMatchResult


@dataclass
class PatternDetectionResult:
    """
    QUARANTINED — Use PatternResult from incident_pattern_service.py instead.

    Pattern detection response.
    Note: This has window_hours which is not in the engine DTO.
    """

    patterns: list[PatternMatchResult]
    window_hours: int  # Additional field not in engine DTO
    window_start: datetime
    window_end: datetime
    incidents_analyzed: int
