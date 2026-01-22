# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: worker (run events), incident_engine (failure events)
#   Execution: sync
# Role: Lessons learned creation and management (domain logic)
# Authority: Lesson generation from system events (SDSR pattern)
# Callers: IncidentEngine, Worker runtime, API endpoints
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Contract: SDSR (PIN-370), PB-S4 (Policy Proposals)
# Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11
#
# GOVERNANCE NOTE: This L4 engine owns LESSON CREATION logic.
# Scenarios inject causes (events), this engine creates lessons.
# PolicyProposalEngine converts lessons to drafts (separate authority).

"""
Lessons Learned Engine (L4 Domain Logic)

This engine implements the learning-driven governance pattern:
- Failures (all severities) → Lesson created
- Near-threshold events → Lesson created
- Critical success events → Lesson created

Lessons are the memory substrate for policy evolution.
Only human action (via PolicyProposalEngine) converts lessons to drafts.

Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from prometheus_client import Counter
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("nova.services.lessons_learned_engine")

# =============================================================================
# Metrics (Prometheus)
# =============================================================================

LESSONS_CREATION_FAILED = Counter(
    "lessons_creation_failed_total",
    "Total number of lesson creation failures by type",
    ["lesson_type"],
)


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# Lesson Type Constants
# =============================================================================

LESSON_TYPE_FAILURE = "failure"
LESSON_TYPE_NEAR_THRESHOLD = "near_threshold"
LESSON_TYPE_CRITICAL_SUCCESS = "critical_success"

LESSON_STATUS_PENDING = "pending"
LESSON_STATUS_CONVERTED = "converted_to_draft"
LESSON_STATUS_DEFERRED = "deferred"
LESSON_STATUS_DISMISSED = "dismissed"

# =============================================================================
# State Machine Transitions (INVARIANT - enforce in engine, not API)
# =============================================================================
# pending → converted_to_draft (TERMINAL)
# pending → deferred → pending (via reactivation when time expires)
# pending → dismissed (TERMINAL)
# deferred → pending (only via reactivate_deferred_lesson)
# converted_to_draft → (no transitions - terminal)
# dismissed → (no transitions - terminal)
# =============================================================================

VALID_TRANSITIONS: dict[str, set[str]] = {
    LESSON_STATUS_PENDING: {LESSON_STATUS_CONVERTED, LESSON_STATUS_DEFERRED, LESSON_STATUS_DISMISSED},
    LESSON_STATUS_DEFERRED: {LESSON_STATUS_PENDING},  # Only reactivation
    LESSON_STATUS_CONVERTED: set(),  # Terminal
    LESSON_STATUS_DISMISSED: set(),  # Terminal
}


def is_valid_transition(from_status: str, to_status: str) -> bool:
    """Check if a state transition is valid."""
    allowed = VALID_TRANSITIONS.get(from_status, set())
    return to_status in allowed


# Severity thresholds for lesson generation
# All failures generate lessons, but severity determines proposed action
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITY_NONE = "NONE"

# =============================================================================
# Worker Wiring Configuration (Playbook Defaults)
# =============================================================================
# Near-threshold: 85% (not 80%) - last safe signal before behavior changes
# Debounce: 24-hour rolling window per (tenant × metric)
# Critical success: rare event (< 1 per tenant per week)
# =============================================================================

NEAR_THRESHOLD_PERCENT = 85.0  # Fire at >= 85% utilization
DEBOUNCE_WINDOW_HOURS = 24  # One lesson per (tenant, metric, band, window)

# Threshold bands for debounce granularity
# Allows escalation visibility: 85% → 98% within 24h creates NEW lesson
THRESHOLD_BANDS = [
    (85, 90, "85-90"),
    (90, 95, "90-95"),
    (95, 100, "95-100"),
]


def get_threshold_band(utilization: float) -> str:
    """Get the threshold band for a utilization percentage."""
    for low, high, label in THRESHOLD_BANDS:
        if low <= utilization < high:
            return label
    # Above 100% or edge case
    return "95-100"


class LessonsLearnedEngine:
    """
    L4 Domain Engine for lesson creation and management.

    This engine implements the learning-driven governance pattern:
    - Detect learning opportunities from system events
    - Create lesson records (memory substrate)
    - Support human-driven conversion to draft proposals

    SDSR Contract (PIN-370):
    - This engine is called when events occur
    - It creates lesson records automatically
    - Lessons are NEVER created by scenarios directly
    - If lessons don't appear for events, THIS ENGINE is broken

    Callers:
    - IncidentEngine (on failures)
    - Worker runtime (on near-threshold, success)
    - API endpoints (for queries)
    """

    def __init__(self, db_url: Optional[str] = None):
        """Initialize the lessons learned engine."""
        self._db_url = db_url or os.environ.get("DATABASE_URL")

    def _get_engine(self):
        """Get SQLAlchemy engine."""
        if not self._db_url:
            raise RuntimeError("DATABASE_URL not configured")
        return create_engine(self._db_url)

    # =========================================================================
    # Lesson Detection (called by other engines)
    # =========================================================================

    def detect_lesson_from_failure(
        self,
        run_id: UUID,
        tenant_id: str,
        error_code: Optional[str],
        error_message: Optional[str],
        severity: str,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Detect and create a lesson from a failure event.

        This is called by IncidentEngine for ALL failure severities.
        Previously only HIGH/CRITICAL created proposals directly.
        Now all failures create lessons first.

        Args:
            run_id: The failed run's ID
            tenant_id: Tenant identifier
            error_code: Error code if available
            error_message: Error message if available
            severity: CRITICAL, HIGH, MEDIUM, LOW
            is_synthetic: Whether from SDSR scenario
            synthetic_scenario_id: Scenario ID if synthetic

        Returns:
            Lesson ID if created, None if skipped
        """
        # Generate lesson content
        title = f"Failure: {error_code or 'Unknown Error'}"
        description = self._generate_failure_description(
            error_code=error_code,
            error_message=error_message,
            severity=severity,
        )
        proposed_action = self._generate_failure_proposed_action(
            error_code=error_code,
            severity=severity,
        )

        return self._create_lesson(
            tenant_id=tenant_id,
            lesson_type=LESSON_TYPE_FAILURE,
            severity=severity,
            source_event_id=run_id,
            source_event_type="run",
            source_run_id=run_id,
            title=title,
            description=description,
            proposed_action=proposed_action,
            detected_pattern={"error_code": error_code, "severity": severity},
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    def detect_lesson_from_near_threshold(
        self,
        run_id: UUID,
        tenant_id: str,
        threshold_type: str,
        current_value: float,
        threshold_value: float,
        utilization_percent: float,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Detect and create a lesson from a near-threshold event.

        Called when a run approaches but doesn't breach a limit.
        Threshold: >= 85% utilization (not 80% - that's operational noise).

        Debounce: One lesson per (tenant, metric, 24h window).

        Args:
            run_id: The run's ID
            tenant_id: Tenant identifier
            threshold_type: Type of threshold (cost, tokens, rate)
            current_value: Current metric value
            threshold_value: Configured threshold
            utilization_percent: Percentage of threshold used
            is_synthetic: Whether from SDSR scenario
            synthetic_scenario_id: Scenario ID if synthetic

        Returns:
            Lesson ID if created, None if skipped (below threshold or debounced)
        """
        if utilization_percent < NEAR_THRESHOLD_PERCENT:
            # Not near enough to threshold (85% minimum)
            return None

        # Calculate threshold band for granular debounce
        # This allows escalation visibility: 85% → 98% creates NEW lesson
        threshold_band = get_threshold_band(utilization_percent)

        # Check debounce: has a near-threshold lesson been created
        # for this tenant + metric + band in the last 24 hours?
        if self._is_debounced(
            tenant_id, threshold_type, LESSON_TYPE_NEAR_THRESHOLD, threshold_band
        ):
            logger.debug(
                f"Near-threshold lesson debounced for {tenant_id}/{threshold_type}/{threshold_band} "
                f"(already created in last {DEBOUNCE_WINDOW_HOURS}h)"
            )
            return None

        title = f"Near-Threshold: {threshold_type} at {utilization_percent:.1f}%"
        description = (
            f"Run approached {threshold_type} threshold without breaching.\n"
            f"Current: {current_value}, Threshold: {threshold_value}\n"
            f"Utilization: {utilization_percent:.1f}%\n\n"
            f"This pattern indicates potential future breaches. "
            f"Consider adjusting thresholds or adding preventive policies."
        )
        proposed_action = (
            f"Consider creating a warning policy for {threshold_type} "
            f"at {utilization_percent * 0.9:.0f}% threshold to provide earlier alerts."
        )

        return self._create_lesson(
            tenant_id=tenant_id,
            lesson_type=LESSON_TYPE_NEAR_THRESHOLD,
            severity=None,  # Near-threshold has no severity
            source_event_id=run_id,
            source_event_type="run",
            source_run_id=run_id,
            title=title,
            description=description,
            proposed_action=proposed_action,
            detected_pattern={
                "threshold_type": threshold_type,
                "current_value": current_value,
                "threshold_value": threshold_value,
                "utilization_percent": utilization_percent,
                "threshold_band": threshold_band,  # For debounce granularity
            },
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    def detect_lesson_from_critical_success(
        self,
        run_id: UUID,
        tenant_id: str,
        success_type: str,
        metrics: dict[str, Any],
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Detect and create a lesson from a critical success event.

        Called when a run succeeds under challenging conditions:
        - High-risk run completed safely
        - Efficient resource usage (well under budget)
        - Fast completion for complex task

        Args:
            run_id: The run's ID
            tenant_id: Tenant identifier
            success_type: Type of success (efficient_completion, safe_high_risk, etc.)
            metrics: Success metrics
            is_synthetic: Whether from SDSR scenario
            synthetic_scenario_id: Scenario ID if synthetic

        Returns:
            Lesson ID if created, None if skipped
        """
        title = f"Critical Success: {success_type}"
        description = (
            f"Run completed successfully under notable conditions.\n"
            f"Success type: {success_type}\n"
            f"Metrics: {metrics}\n\n"
            f"This pattern indicates effective behavior that could inform "
            f"best practices or positive reinforcement policies."
        )
        proposed_action = (
            f"Consider documenting this success pattern for {success_type} "
            f"and creating policies that encourage similar behavior."
        )

        return self._create_lesson(
            tenant_id=tenant_id,
            lesson_type=LESSON_TYPE_CRITICAL_SUCCESS,
            severity=SEVERITY_NONE,
            source_event_id=run_id,
            source_event_type="run",
            source_run_id=run_id,
            title=title,
            description=description,
            proposed_action=proposed_action,
            detected_pattern={"success_type": success_type, "metrics": metrics},
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    # =========================================================================
    # Worker APIs (safe wrappers for worker integration)
    # =========================================================================
    # These methods are designed for worker use:
    # - Never raise exceptions (log + metric only)
    # - Never block the run on lesson creation failure
    # - Handle debounce internally
    # =========================================================================

    def emit_near_threshold(
        self,
        tenant_id: str,
        metric: str,
        utilization: float,
        threshold_value: float,
        current_value: float,
        source_event_id: UUID,
        window: str = "24h",
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Worker-safe method to emit a near-threshold lesson.

        This is the canonical entry point for workers. It:
        - Never raises exceptions
        - Handles debounce internally
        - Logs failures without blocking the run

        Args:
            tenant_id: Tenant identifier
            metric: Metric type (budget, tokens, rate)
            utilization: Current utilization percentage (0-100)
            threshold_value: The configured threshold
            current_value: Current metric value
            source_event_id: Run ID or event ID
            window: Debounce window identifier (default "24h")
            is_synthetic: Whether from SDSR scenario
            synthetic_scenario_id: Scenario ID if synthetic

        Returns:
            Lesson ID if created, None if skipped or failed
        """
        try:
            return self.detect_lesson_from_near_threshold(
                run_id=source_event_id,
                tenant_id=tenant_id,
                threshold_type=metric,
                current_value=current_value,
                threshold_value=threshold_value,
                utilization_percent=utilization,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )
        except Exception as e:
            # Never fail the run because lesson creation failed
            logger.error(f"Failed to emit near-threshold lesson: {e}")
            LESSONS_CREATION_FAILED.labels(lesson_type=LESSON_TYPE_NEAR_THRESHOLD).inc()
            return None

    def emit_critical_success(
        self,
        tenant_id: str,
        success_type: str,
        metrics: dict[str, Any],
        source_event_id: UUID,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Worker-safe method to emit a critical success lesson.

        This is the canonical entry point for workers. It:
        - Never raises exceptions
        - Logs failures without blocking the run
        - Should be called rarely (< 1 per tenant per week target)

        Args:
            tenant_id: Tenant identifier
            success_type: Type of success (cost_efficiency, performance, reliability)
            metrics: Success metrics (baseline, delta, sample_size)
            source_event_id: Run ID or event ID
            is_synthetic: Whether from SDSR scenario
            synthetic_scenario_id: Scenario ID if synthetic

        Returns:
            Lesson ID if created, None if skipped or failed
        """
        try:
            return self.detect_lesson_from_critical_success(
                run_id=source_event_id,
                tenant_id=tenant_id,
                success_type=success_type,
                metrics=metrics,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )
        except Exception as e:
            # Never fail the run because lesson creation failed
            logger.error(f"Failed to emit critical success lesson: {e}")
            LESSONS_CREATION_FAILED.labels(lesson_type=LESSON_TYPE_CRITICAL_SUCCESS).inc()
            return None

    # =========================================================================
    # Lesson Management (called by API endpoints)
    # =========================================================================

    def list_lessons(
        self,
        tenant_id: str,
        lesson_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        include_synthetic: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List lessons for a tenant with optional filters.

        Args:
            tenant_id: Tenant identifier
            lesson_type: Filter by type (failure, near_threshold, critical_success)
            status: Filter by status (pending, converted_to_draft, deferred, dismissed)
            severity: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
            include_synthetic: Include synthetic lessons (default False - hide them)
            limit: Max results
            offset: Pagination offset

        Returns:
            List of lesson summaries
        """
        engine = self._get_engine()

        filters = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

        # Default: hide synthetic lessons from production view
        if not include_synthetic:
            filters.append("is_synthetic = false")

        if lesson_type:
            filters.append("lesson_type = :lesson_type")
            params["lesson_type"] = lesson_type

        if status:
            filters.append("status = :status")
            params["status"] = status

        if severity:
            filters.append("severity = :severity")
            params["severity"] = severity

        where_clause = " AND ".join(filters)

        query = f"""
            SELECT
                id,
                tenant_id,
                lesson_type,
                severity,
                title,
                status,
                source_event_type,
                created_at,
                proposed_action IS NOT NULL as has_proposed_action
            FROM lessons_learned
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """

        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()

        return [
            {
                "id": str(row[0]),
                "tenant_id": row[1],
                "lesson_type": row[2],
                "severity": row[3],
                "title": row[4],
                "status": row[5],
                "source_event_type": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "has_proposed_action": row[8],
            }
            for row in rows
        ]

    def get_lesson(self, lesson_id: UUID, tenant_id: str) -> Optional[dict[str, Any]]:
        """
        Get a specific lesson by ID.

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant identifier (for isolation)

        Returns:
            Lesson detail or None if not found
        """
        engine = self._get_engine()

        query = """
            SELECT
                id, tenant_id, lesson_type, severity,
                source_event_id, source_event_type, source_run_id,
                title, description, proposed_action, detected_pattern,
                status, draft_proposal_id,
                created_at, converted_at, deferred_until,
                dismissed_at, dismissed_by, dismissed_reason
            FROM lessons_learned
            WHERE id = :lesson_id AND tenant_id = :tenant_id
        """

        with engine.connect() as conn:
            result = conn.execute(text(query), {"lesson_id": str(lesson_id), "tenant_id": tenant_id})
            row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row[0]),
            "tenant_id": row[1],
            "lesson_type": row[2],
            "severity": row[3],
            "source_event_id": str(row[4]) if row[4] else None,
            "source_event_type": row[5],
            "source_run_id": str(row[6]) if row[6] else None,
            "title": row[7],
            "description": row[8],
            "proposed_action": row[9],
            "detected_pattern": row[10],
            "status": row[11],
            "draft_proposal_id": str(row[12]) if row[12] else None,
            "created_at": row[13].isoformat() if row[13] else None,
            "converted_at": row[14].isoformat() if row[14] else None,
            "deferred_until": row[15].isoformat() if row[15] else None,
            "dismissed_at": row[16].isoformat() if row[16] else None,
            "dismissed_by": row[17],
            "dismissed_reason": row[18],
        }

    def convert_lesson_to_draft(
        self,
        lesson_id: UUID,
        tenant_id: str,
        converted_by: str = "system",
    ) -> Optional[UUID]:
        """
        Convert a lesson to a draft policy proposal.

        This delegates to PolicyProposalEngine for actual proposal creation.
        Updates the lesson status to 'converted_to_draft'.

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant identifier
            converted_by: User/system that initiated conversion

        Returns:
            Draft proposal ID if created, None if failed
        """
        engine = self._get_engine()

        # Get the lesson
        lesson = self.get_lesson(lesson_id, tenant_id)
        if not lesson:
            logger.warning(f"Lesson not found: {lesson_id}")
            return None

        current_status = lesson["status"]
        if not is_valid_transition(current_status, LESSON_STATUS_CONVERTED):
            logger.warning(
                f"Invalid transition for lesson {lesson_id}: "
                f"{current_status} → converted_to_draft (only pending lessons can be converted)"
            )
            return None

        # Create draft proposal via PolicyProposalEngine pattern
        # This uses the same pattern as _maybe_create_policy_proposal in IncidentEngine
        proposal_id = uuid4()
        now = utc_now()

        try:
            with engine.connect() as conn:
                # Insert draft proposal
                conn.execute(
                    text("""
                        INSERT INTO policy_proposals (
                            id, tenant_id, title, description,
                            proposed_action, status, source_type, source_id,
                            created_at, created_by
                        ) VALUES (
                            :id, :tenant_id, :title, :description,
                            :proposed_action, 'draft', 'lesson', :source_id,
                            :created_at, :created_by
                        )
                    """),
                    {
                        "id": str(proposal_id),
                        "tenant_id": tenant_id,
                        "title": f"Policy from Lesson: {lesson['title']}",
                        "description": lesson["description"],
                        "proposed_action": lesson["proposed_action"],
                        "source_id": str(lesson_id),
                        "created_at": now,
                        "created_by": converted_by,
                    },
                )

                # Update lesson status
                conn.execute(
                    text("""
                        UPDATE lessons_learned
                        SET status = :status,
                            draft_proposal_id = :proposal_id,
                            converted_at = :converted_at
                        WHERE id = :lesson_id AND tenant_id = :tenant_id
                    """),
                    {
                        "status": LESSON_STATUS_CONVERTED,
                        "proposal_id": str(proposal_id),
                        "converted_at": now,
                        "lesson_id": str(lesson_id),
                        "tenant_id": tenant_id,
                    },
                )

                conn.commit()

            logger.info(f"Converted lesson {lesson_id} to draft proposal {proposal_id}")
            return proposal_id

        except IntegrityError as e:
            logger.error(f"Failed to convert lesson {lesson_id}: {e}")
            return None

    def defer_lesson(
        self,
        lesson_id: UUID,
        tenant_id: str,
        defer_until: datetime,
    ) -> bool:
        """
        Defer a lesson until a future date.

        State Machine Rule:
            pending → deferred (allowed)
            converted_to_draft → deferred (FORBIDDEN - terminal)
            dismissed → deferred (FORBIDDEN - terminal)

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant identifier
            defer_until: When to resurface the lesson

        Returns:
            True if deferred, False if failed or invalid transition
        """
        engine = self._get_engine()

        # Validate transition at engine level (defense in depth)
        lesson = self.get_lesson(lesson_id, tenant_id)
        if not lesson:
            logger.warning(f"Lesson not found for deferral: {lesson_id}")
            return False

        current_status = lesson["status"]
        if not is_valid_transition(current_status, LESSON_STATUS_DEFERRED):
            logger.warning(
                f"Invalid transition for lesson {lesson_id}: "
                f"{current_status} → deferred (only pending lessons can be deferred)"
            )
            return False

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        UPDATE lessons_learned
                        SET status = :status, deferred_until = :defer_until
                        WHERE id = :lesson_id
                          AND tenant_id = :tenant_id
                          AND status = 'pending'
                    """),
                    {
                        "status": LESSON_STATUS_DEFERRED,
                        "defer_until": defer_until,
                        "lesson_id": str(lesson_id),
                        "tenant_id": tenant_id,
                    },
                )
                conn.commit()

                if result.rowcount > 0:
                    logger.info(f"Deferred lesson {lesson_id} until {defer_until}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Failed to defer lesson {lesson_id}: {e}")
            return False

    def dismiss_lesson(
        self,
        lesson_id: UUID,
        tenant_id: str,
        dismissed_by: str,
        reason: str,
    ) -> bool:
        """
        Dismiss a lesson (mark as not actionable).

        State Machine Rule:
            pending → dismissed (TERMINAL - cannot be undone)
            converted_to_draft → dismissed (FORBIDDEN - terminal)
            deferred → dismissed (FORBIDDEN - must reactivate first)

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant identifier
            dismissed_by: User who dismissed
            reason: Reason for dismissal

        Returns:
            True if dismissed, False if failed or invalid transition
        """
        engine = self._get_engine()
        now = utc_now()

        # Validate transition at engine level (defense in depth)
        lesson = self.get_lesson(lesson_id, tenant_id)
        if not lesson:
            logger.warning(f"Lesson not found for dismissal: {lesson_id}")
            return False

        current_status = lesson["status"]
        if not is_valid_transition(current_status, LESSON_STATUS_DISMISSED):
            logger.warning(
                f"Invalid transition for lesson {lesson_id}: "
                f"{current_status} → dismissed (only pending lessons can be dismissed)"
            )
            return False

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        UPDATE lessons_learned
                        SET status = :status,
                            dismissed_at = :dismissed_at,
                            dismissed_by = :dismissed_by,
                            dismissed_reason = :reason
                        WHERE id = :lesson_id
                          AND tenant_id = :tenant_id
                          AND status = 'pending'
                    """),
                    {
                        "status": LESSON_STATUS_DISMISSED,
                        "dismissed_at": now,
                        "dismissed_by": dismissed_by,
                        "reason": reason,
                        "lesson_id": str(lesson_id),
                        "tenant_id": tenant_id,
                    },
                )
                conn.commit()

                if result.rowcount > 0:
                    logger.info(f"Dismissed lesson {lesson_id} by {dismissed_by}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Failed to dismiss lesson {lesson_id}: {e}")
            return False

    def get_lesson_stats(self, tenant_id: str) -> dict[str, Any]:
        """
        Get lesson statistics for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Statistics dictionary
        """
        engine = self._get_engine()

        query = """
            SELECT
                lesson_type,
                status,
                COUNT(*) as count
            FROM lessons_learned
            WHERE tenant_id = :tenant_id
            GROUP BY lesson_type, status
        """

        with engine.connect() as conn:
            result = conn.execute(text(query), {"tenant_id": tenant_id})
            rows = result.fetchall()

        stats = {
            "by_type": {},
            "by_status": {},
            "total": 0,
        }

        for row in rows:
            lesson_type, status, count = row
            stats["total"] += count

            if lesson_type not in stats["by_type"]:
                stats["by_type"][lesson_type] = 0
            stats["by_type"][lesson_type] += count

            if status not in stats["by_status"]:
                stats["by_status"][status] = 0
            stats["by_status"][status] += count

        return stats

    def reactivate_deferred_lesson(
        self,
        lesson_id: UUID,
        tenant_id: str,
    ) -> bool:
        """
        Reactivate a deferred lesson back to pending status.

        This is the ONLY valid way to transition from deferred → pending.
        Called when deferral period expires or manually by human action.

        State Machine Rule:
            deferred → pending (allowed)
            converted_to_draft → pending (FORBIDDEN - terminal)
            dismissed → pending (FORBIDDEN - terminal)

        Args:
            lesson_id: Lesson UUID
            tenant_id: Tenant identifier

        Returns:
            True if reactivated, False if failed or invalid transition
        """
        engine = self._get_engine()

        # Get current status first to validate transition
        lesson = self.get_lesson(lesson_id, tenant_id)
        if not lesson:
            logger.warning(f"Lesson not found for reactivation: {lesson_id}")
            return False

        current_status = lesson["status"]
        if not is_valid_transition(current_status, LESSON_STATUS_PENDING):
            logger.warning(
                f"Invalid transition for lesson {lesson_id}: "
                f"{current_status} → pending (terminal states cannot be reactivated)"
            )
            return False

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        UPDATE lessons_learned
                        SET status = :status,
                            deferred_until = NULL
                        WHERE id = :lesson_id
                          AND tenant_id = :tenant_id
                          AND status = :from_status
                    """),
                    {
                        "status": LESSON_STATUS_PENDING,
                        "from_status": LESSON_STATUS_DEFERRED,
                        "lesson_id": str(lesson_id),
                        "tenant_id": tenant_id,
                    },
                )
                conn.commit()

                if result.rowcount > 0:
                    logger.info(f"Reactivated lesson {lesson_id} (deferred → pending)")
                    return True
                return False

        except Exception as e:
            logger.error(f"Failed to reactivate lesson {lesson_id}: {e}")
            return False

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _is_debounced(
        self,
        tenant_id: str,
        metric_type: str,
        lesson_type: str,
        threshold_band: Optional[str] = None,
    ) -> bool:
        """
        Check if a lesson of this type has been created recently (debounce).

        Uses a rolling window to prevent oscillation flooding.
        Default window: 24 hours.

        Debounce key: (tenant_id, metric_type, threshold_band, window)
        This allows escalation visibility: 85% → 98% creates a NEW lesson
        even within the same 24h window.

        Args:
            tenant_id: Tenant identifier
            metric_type: Type of metric (budget, tokens, rate)
            lesson_type: Lesson type (near_threshold, critical_success)
            threshold_band: Band label (e.g., "85-90", "90-95") for granular debounce

        Returns:
            True if debounced (lesson already exists in window), False otherwise
        """
        engine = self._get_engine()

        # Build query with optional threshold band filter
        query = """
            SELECT COUNT(*) as count
            FROM lessons_learned
            WHERE tenant_id = :tenant_id
              AND lesson_type = :lesson_type
              AND detected_pattern->>'threshold_type' = :metric_type
              AND created_at >= NOW() - INTERVAL ':hours hours'
        """

        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "lesson_type": lesson_type,
            "metric_type": metric_type,
        }

        # Add threshold band filter for near-threshold debounce
        # This allows escalation (85% → 98%) to create new lessons
        if threshold_band:
            query = query.rstrip() + """
              AND detected_pattern->>'threshold_band' = :threshold_band
            """
            params["threshold_band"] = threshold_band

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(query.replace(":hours", str(DEBOUNCE_WINDOW_HOURS))),
                    params,
                )
                row = result.fetchone()
                return row[0] > 0 if row else False

        except Exception as e:
            logger.warning(f"Debounce check failed: {e}")
            # On error, don't debounce (fail open for learning)
            return False

    def _create_lesson(
        self,
        tenant_id: str,
        lesson_type: str,
        severity: Optional[str],
        source_event_id: UUID,
        source_event_type: str,
        source_run_id: Optional[UUID],
        title: str,
        description: str,
        proposed_action: Optional[str],
        detected_pattern: Optional[dict[str, Any]],
        is_synthetic: bool,
        synthetic_scenario_id: Optional[str],
    ) -> Optional[UUID]:
        """Create a lesson record in the database."""
        engine = self._get_engine()
        lesson_id = uuid4()
        now = utc_now()

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO lessons_learned (
                            id, tenant_id, lesson_type, severity,
                            source_event_id, source_event_type, source_run_id,
                            title, description, proposed_action, detected_pattern,
                            status, created_at,
                            is_synthetic, synthetic_scenario_id
                        ) VALUES (
                            :id, :tenant_id, :lesson_type, :severity,
                            :source_event_id, :source_event_type, :source_run_id,
                            :title, :description, :proposed_action, :detected_pattern::jsonb,
                            'pending', :created_at,
                            :is_synthetic, :synthetic_scenario_id
                        )
                    """),
                    {
                        "id": str(lesson_id),
                        "tenant_id": tenant_id,
                        "lesson_type": lesson_type,
                        "severity": severity,
                        "source_event_id": str(source_event_id),
                        "source_event_type": source_event_type,
                        "source_run_id": str(source_run_id) if source_run_id else None,
                        "title": title,
                        "description": description,
                        "proposed_action": proposed_action,
                        "detected_pattern": str(detected_pattern) if detected_pattern else None,
                        "created_at": now,
                        "is_synthetic": is_synthetic,
                        "synthetic_scenario_id": synthetic_scenario_id,
                    },
                )
                conn.commit()

            logger.info(f"Created lesson {lesson_id} (type={lesson_type}, tenant={tenant_id})")
            return lesson_id

        except IntegrityError as e:
            logger.error(f"Failed to create lesson: {e}")
            return None

    def _generate_failure_description(
        self,
        error_code: Optional[str],
        error_message: Optional[str],
        severity: str,
    ) -> str:
        """Generate description for a failure lesson."""
        return (
            f"A {severity.lower()} severity failure occurred.\n\n"
            f"Error Code: {error_code or 'Unknown'}\n"
            f"Error Message: {error_message or 'No message available'}\n\n"
            f"This failure may indicate a recurring issue that should be "
            f"addressed through policy updates."
        )

    def _generate_failure_proposed_action(
        self,
        error_code: Optional[str],
        severity: str,
    ) -> str:
        """Generate proposed action for a failure lesson."""
        if severity in (SEVERITY_CRITICAL, SEVERITY_HIGH):
            return (
                f"Consider creating a blocking policy to prevent similar "
                f"failures. Review the error pattern '{error_code or 'unknown'}' "
                f"and determine if pre-execution validation could catch this."
            )
        else:
            return (
                f"Consider creating a warning policy to flag similar patterns. "
                f"The error '{error_code or 'unknown'}' may benefit from monitoring."
            )

    # =========================================================================
    # Scheduler Support (PIN-411)
    # =========================================================================

    def get_expired_deferred_lessons(self, limit: int = 100) -> list[tuple[UUID, str]]:
        """
        Get deferred lessons whose deferred_until has passed.

        This is used by the background scheduler to find lessons
        that need to be reactivated back to pending status.

        Args:
            limit: Maximum number of lessons to return (default 100)

        Returns:
            List of (lesson_id, tenant_id) tuples ready for reactivation
        """
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, tenant_id
                        FROM lessons_learned
                        WHERE status = :status
                          AND deferred_until IS NOT NULL
                          AND deferred_until <= NOW()
                        ORDER BY deferred_until ASC
                        LIMIT :limit
                    """),
                    {"status": LESSON_STATUS_DEFERRED, "limit": limit},
                )
                rows = result.fetchall()
                return [(UUID(str(row[0])), str(row[1])) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get expired deferred lessons: {e}")
            return []

    def reactivate_expired_deferred_lessons(self) -> int:
        """
        Reactivate all deferred lessons whose deferred_until has passed.

        This is the main entry point for the background scheduler.
        It finds expired deferred lessons and reactivates them.

        Returns:
            Number of lessons successfully reactivated
        """
        expired_lessons = self.get_expired_deferred_lessons()

        if not expired_lessons:
            return 0

        reactivated_count = 0
        for lesson_id, tenant_id in expired_lessons:
            if self.reactivate_deferred_lesson(lesson_id, tenant_id):
                reactivated_count += 1

        if reactivated_count > 0:
            logger.info(
                f"Reactivated {reactivated_count} expired deferred lessons "
                f"(out of {len(expired_lessons)} candidates)"
            )

        return reactivated_count


# =============================================================================
# Singleton accessor
# =============================================================================

_lessons_engine: Optional[LessonsLearnedEngine] = None


def get_lessons_learned_engine() -> LessonsLearnedEngine:
    """Get the singleton LessonsLearnedEngine instance."""
    global _lessons_engine
    if _lessons_engine is None:
        _lessons_engine = LessonsLearnedEngine()
    return _lessons_engine
