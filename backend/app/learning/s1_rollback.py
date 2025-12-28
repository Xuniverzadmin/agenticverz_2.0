"""
C5-S1: Learning from Rollback Frequency.

This module observes envelope rollback patterns and produces
advisory suggestions for humans to consider.

CRITICAL BOUNDARIES (CI-C5-3, CI-C5-6):
- This module MUST NOT import kill-switch modules
- This module MUST NOT import coordinator core paths
- This module ONLY reads from coordination audit records (metadata)

ADVISORY ONLY (CI-C5-1):
- All outputs are suggestions, never directives
- No direct envelope modification
- No coordinator.apply() calls

Reference: C5_S1_LEARNING_SCENARIO.md, C5_S1_ACCEPTANCE_CRITERIA.md
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.learning.config import learning_enabled, require_learning_enabled
from app.learning.suggestions import (
    FORBIDDEN_LANGUAGE_PATTERNS,
    LearningSuggestion,
    RollbackObservation,
    SuggestionConfidence,
    SuggestionStatus,
    validate_suggestion_text,
)

# NOTE: We import from envelope.py for TYPE DEFINITIONS ONLY
# We do NOT import coordinator or killswitch
from app.optimization.envelope import (
    CoordinationAuditRecord,
    CoordinationDecisionType,
)

logger = logging.getLogger("nova.learning.s1_rollback")


# Thresholds for suggestion generation
# These are metadata, not runtime parameters
ROLLBACK_RATE_THRESHOLD = 0.3  # 30% rollback rate triggers suggestion
MINIMUM_ENVELOPES_FOR_ANALYSIS = 3  # Need at least 3 envelopes to analyze
DEFAULT_OBSERVATION_WINDOW_HOURS = 24  # Default 24-hour window


@dataclass
class RollbackStats:
    """
    Aggregated rollback statistics for a parameter.

    This is computed from audit records, not runtime state.
    """

    envelope_class: str
    target_parameter: str
    rollback_count: int
    total_envelopes: int
    rollback_rate: float
    avg_time_to_rollback_seconds: float
    trend: str  # "increasing", "stable", "decreasing"
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class RollbackObserver:
    """
    C5-S1 Rollback Observer.

    Observes envelope rollback patterns from coordination audit records
    and generates advisory suggestions.

    BOUNDARIES:
    - Reads ONLY from CoordinationAuditRecord (passed in, not queried directly)
    - Never imports killswitch or coordinator core logic
    - All suggestions are advisory only
    """

    def __init__(self) -> None:
        """Initialize the rollback observer."""
        self._suggestions: List[LearningSuggestion] = []

    def get_suggestions(self) -> List[LearningSuggestion]:
        """Get all generated suggestions (read-only copy)."""
        return list(self._suggestions)

    @require_learning_enabled
    def observe(
        self,
        audit_records: List[CoordinationAuditRecord],
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> Optional[List[LearningSuggestion]]:
        """
        Observe rollback patterns and generate suggestions.

        Args:
            audit_records: List of coordination audit records to analyze.
                          These are passed in, not queried directly.
            window_start: Start of observation window (default: 24h ago).
            window_end: End of observation window (default: now).

        Returns:
            List of generated suggestions, or None if learning is disabled.

        CI-C5-5: Guarded by @require_learning_enabled.
        AC-S1-O1: No rollbacks -> no suggestion.
        AC-S1-O2: Below threshold -> no suggestion.
        AC-S1-O3: Above threshold -> advisory suggestion.
        AC-S1-O4: Window boundaries respected.
        """
        # Set default window
        if window_end is None:
            window_end = datetime.now(timezone.utc)
        if window_start is None:
            window_start = window_end - timedelta(hours=DEFAULT_OBSERVATION_WINDOW_HOURS)

        logger.info(
            "s1_observation_start",
            extra={
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "total_records": len(audit_records),
            },
        )

        # Filter records to window (AC-S1-O4)
        window_records = self._filter_to_window(audit_records, window_start, window_end)

        # If no records in window, no suggestion
        if not window_records:
            logger.info(
                "s1_no_records_in_window",
                extra={
                    "window_start": window_start.isoformat(),
                    "window_end": window_end.isoformat(),
                },
            )
            return []

        # Compute rollback statistics
        stats = self._compute_rollback_stats(window_records)

        # Generate suggestions for high rollback rates
        suggestions = []
        for param_key, stat in stats.items():
            suggestion = self._maybe_generate_suggestion(stat, window_start, window_end)
            if suggestion:
                suggestions.append(suggestion)
                self._suggestions.append(suggestion)

        logger.info(
            "s1_observation_complete",
            extra={
                "records_analyzed": len(window_records),
                "parameters_observed": len(stats),
                "suggestions_generated": len(suggestions),
            },
        )

        return suggestions

    def _filter_to_window(
        self,
        records: List[CoordinationAuditRecord],
        window_start: datetime,
        window_end: datetime,
    ) -> List[CoordinationAuditRecord]:
        """
        Filter audit records to the observation window.

        AC-S1-O4: Only records inside window are counted.
        """
        return [r for r in records if window_start <= r.timestamp <= window_end]

    def _compute_rollback_stats(self, records: List[CoordinationAuditRecord]) -> Dict[str, RollbackStats]:
        """
        Compute rollback statistics per parameter.

        Groups records by target parameter and computes:
        - rollback_count (REJECTED decisions indicate rollback)
        - total_envelopes (all decisions for that parameter)
        - rollback_rate (rollback_count / total_envelopes)
        """
        # Group by parameter
        # Note: We don't have direct access to envelope scope from audit record
        # In production, we'd need to join with envelope metadata
        # For now, we group by envelope_class as a proxy
        by_class: Dict[str, List[CoordinationAuditRecord]] = defaultdict(list)

        for record in records:
            key = record.envelope_class.value if record.envelope_class else "UNKNOWN"
            by_class[key].append(record)

        stats: Dict[str, RollbackStats] = {}

        for class_name, class_records in by_class.items():
            # Count rollbacks (REJECTED decisions indicate rollback)
            rollback_count = sum(1 for r in class_records if r.decision == CoordinationDecisionType.REJECTED)

            total_envelopes = len(class_records)

            # Skip if not enough data
            if total_envelopes < MINIMUM_ENVELOPES_FOR_ANALYSIS:
                continue

            rollback_rate = rollback_count / total_envelopes if total_envelopes > 0 else 0.0

            # Compute average time to rollback (simplified)
            # In production, we'd track apply→revert time from envelope lifecycle
            avg_time = 60.0  # Placeholder

            # Compute trend (simplified)
            # In production, we'd compare to previous windows
            trend = "stable"

            timestamps = [r.timestamp for r in class_records]
            first_seen = min(timestamps) if timestamps else None
            last_seen = max(timestamps) if timestamps else None

            stats[class_name] = RollbackStats(
                envelope_class=class_name,
                target_parameter=f"{class_name.lower()}_parameter",  # Placeholder
                rollback_count=rollback_count,
                total_envelopes=total_envelopes,
                rollback_rate=rollback_rate,
                avg_time_to_rollback_seconds=avg_time,
                trend=trend,
                first_seen=first_seen,
                last_seen=last_seen,
            )

        return stats

    def _maybe_generate_suggestion(
        self,
        stats: RollbackStats,
        window_start: datetime,
        window_end: datetime,
    ) -> Optional[LearningSuggestion]:
        """
        Maybe generate a suggestion based on rollback stats.

        AC-S1-O1: No rollbacks -> no suggestion.
        AC-S1-O2: Below threshold -> no suggestion.
        AC-S1-O3: Above threshold -> advisory suggestion.
        """
        # No rollbacks -> no suggestion (AC-S1-O1)
        if stats.rollback_count == 0:
            return None

        # Below threshold -> no suggestion (AC-S1-O2)
        if stats.rollback_rate < ROLLBACK_RATE_THRESHOLD:
            return None

        # Above threshold -> generate advisory suggestion (AC-S1-O3)
        confidence = self._compute_confidence(stats)
        suggestion_text = self._generate_suggestion_text(stats)

        # Validate text uses observational language (AC-S1-B4)
        if not validate_suggestion_text(suggestion_text):
            logger.error(
                "s1_forbidden_language_detected",
                extra={
                    "text": suggestion_text,
                    "patterns": FORBIDDEN_LANGUAGE_PATTERNS,
                },
            )
            # Generate safe fallback text
            suggestion_text = (
                f"Rollback frequency observed for {stats.envelope_class} class. " f"Rate: {stats.rollback_rate:.1%}."
            )

        observation = RollbackObservation(
            envelope_class=stats.envelope_class,
            target_parameter=stats.target_parameter,
            rollback_count=stats.rollback_count,
            total_envelopes=stats.total_envelopes,
            rollback_rate=stats.rollback_rate,
            avg_time_to_rollback_seconds=stats.avg_time_to_rollback_seconds,
            trend=stats.trend,
        )

        suggestion = LearningSuggestion(
            scenario="C5-S1",
            observation_window_start=window_start,
            observation_window_end=window_end,
            observation=observation.__dict__,
            suggestion_type="advisory",  # Always advisory (CI-C5-1)
            suggestion_confidence=confidence,
            suggestion_text=suggestion_text,
            status=SuggestionStatus.PENDING_REVIEW,  # Always pending (CI-C5-2)
            applied=False,  # Always False by default (CI-C5-2)
        )

        logger.info(
            "s1_suggestion_generated",
            extra={
                "suggestion_id": suggestion.id,
                "envelope_class": stats.envelope_class,
                "rollback_rate": stats.rollback_rate,
                "confidence": confidence.value,
            },
        )

        return suggestion

    def _compute_confidence(self, stats: RollbackStats) -> SuggestionConfidence:
        """
        Compute confidence level based on data quality.

        More data and higher rates -> higher confidence.
        """
        if stats.total_envelopes >= 10 and stats.rollback_rate >= 0.5:
            return SuggestionConfidence.HIGH
        elif stats.total_envelopes >= 5 and stats.rollback_rate >= 0.4:
            return SuggestionConfidence.MEDIUM
        else:
            return SuggestionConfidence.LOW

    def _generate_suggestion_text(self, stats: RollbackStats) -> str:
        """
        Generate observational suggestion text.

        MUST use observational language only (CI-C5-1, AC-S1-B4):
        - "suggests", "may want to review", "observed"
        - NEVER "should", "must", "will improve", "recommends"
        """
        rate_pct = stats.rollback_rate * 100

        # Use ONLY observational language
        if stats.trend == "increasing":
            return (
                f"Rollback frequency for {stats.envelope_class} class "
                f"suggests an increasing pattern. "
                f"Observed rate: {rate_pct:.1f}% over {stats.total_envelopes} envelopes. "
                f"You may want to review the bounds configuration."
            )
        elif rate_pct >= 50:
            return (
                f"High rollback rate observed for {stats.envelope_class} class: "
                f"{rate_pct:.1f}% ({stats.rollback_count}/{stats.total_envelopes}). "
                f"This pattern suggests bounds may be too aggressive."
            )
        else:
            return (
                f"Moderate rollback rate observed for {stats.envelope_class} class: "
                f"{rate_pct:.1f}% ({stats.rollback_count}/{stats.total_envelopes}). "
                f"You may want to review if this aligns with expectations."
            )


# Module-level singleton
_observer: Optional[RollbackObserver] = None


def get_rollback_observer() -> RollbackObserver:
    """Get the module-level rollback observer instance."""
    global _observer
    if _observer is None:
        _observer = RollbackObserver()
    return _observer


@require_learning_enabled
def observe_rollback_frequency(
    audit_records: List[CoordinationAuditRecord],
    window_hours: int = DEFAULT_OBSERVATION_WINDOW_HOURS,
) -> Optional[List[LearningSuggestion]]:
    """
    Convenience function to observe rollback frequency.

    Args:
        audit_records: List of coordination audit records.
        window_hours: Observation window in hours (default 24).

    Returns:
        List of generated suggestions, or None if learning is disabled.

    CI-C5-5: Guarded by @require_learning_enabled.
    """
    if not learning_enabled():
        logger.info("learning_disabled_skip", extra={"function": "observe_rollback_frequency"})
        return None

    observer = get_rollback_observer()
    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(hours=window_hours)

    return observer.observe(audit_records, window_start, window_end)
