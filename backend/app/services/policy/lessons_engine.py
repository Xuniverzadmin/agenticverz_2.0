# Layer: L7 — Legacy Shim (DEPRECATED)
# AUDIENCE: INTERNAL
# Role: Backward-compatible re-export for lessons engine
# Status: DEPRECATED - Will be deleted when callers migrate to direct HOC imports
#
# MIGRATION PATH:
#   Current:  from app.services.policy.lessons_engine import get_lessons_learned_engine
#   Future:   from app.hoc.cus.incidents.L5_engines.lessons_engine import get_lessons_learned_engine
#
# This shim exists for Phase-2.5 migration. Delete when all callers are updated.
# Reference: PIN-468, POLICIES_CROSS_DOMAIN_OWNERSHIP.md
#
# CANONICAL SOURCE: app/hoc/cus/incidents/L5_engines/lessons_engine.py

"""
Lessons Engine - DEPRECATED SHIM

This file re-exports from the canonical incidents domain engine.
Do not add logic here. All implementation is in:
    app.hoc.cus.incidents.L5_engines.lessons_engine

Migration: Update imports to use the canonical path directly.
"""

# Re-export everything from canonical source
from app.hoc.cus.incidents.L5_engines.lessons_engine import (
    # Constants
    DEBOUNCE_WINDOW_HOURS,
    LESSON_STATUS_CONVERTED,
    LESSON_STATUS_DEFERRED,
    LESSON_STATUS_DISMISSED,
    LESSON_STATUS_PENDING,
    LESSON_TYPE_CRITICAL_SUCCESS,
    LESSON_TYPE_FAILURE,
    LESSON_TYPE_NEAR_THRESHOLD,
    LESSONS_CREATION_FAILED,
    NEAR_THRESHOLD_PERCENT,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_NONE,
    THRESHOLD_BANDS,
    # Functions
    get_lessons_learned_engine,
    get_threshold_band,
    is_valid_transition,
    utc_now,
    # Classes
    LessonsLearnedEngine,
)

__all__ = [
    # Constants
    "DEBOUNCE_WINDOW_HOURS",
    "LESSON_STATUS_CONVERTED",
    "LESSON_STATUS_DEFERRED",
    "LESSON_STATUS_DISMISSED",
    "LESSON_STATUS_PENDING",
    "LESSON_TYPE_CRITICAL_SUCCESS",
    "LESSON_TYPE_FAILURE",
    "LESSON_TYPE_NEAR_THRESHOLD",
    "LESSONS_CREATION_FAILED",
    "NEAR_THRESHOLD_PERCENT",
    "SEVERITY_CRITICAL",
    "SEVERITY_HIGH",
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "SEVERITY_NONE",
    "THRESHOLD_BANDS",
    # Functions
    "get_lessons_learned_engine",
    "get_threshold_band",
    "is_valid_transition",
    "utc_now",
    # Classes
    "LessonsLearnedEngine",
]
