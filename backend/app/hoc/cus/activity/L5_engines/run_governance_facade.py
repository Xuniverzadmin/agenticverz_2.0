# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Run Governance Facade - Centralized access to governance operations for runs
# Product: system-wide
# Location: hoc/cus/activity/L5_engines/run_governance_facade.py
# Temporal:
#   Trigger: worker (run lifecycle events)
#   Execution: sync
# Lifecycle:
#   Emits: none (facade only)
#   Subscribes: RUN_STARTED, RUN_COMPLETED
# Data Access:
#   Reads: Policy, Limit (via L5 engines)
#   Writes: none (delegates to engines)
# Callers: L5 runner (worker runtime)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-454, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.

"""
Run Governance Facade (L5 Domain Engine)

This facade provides the external interface for governance operations
during run execution. The L5 runner MUST use this facade instead of
directly importing L4 engines.

Why This Facade Exists (PIN-454):
- Prevents L5→L4 layer violations (runner importing engines directly)
- Centralizes governance logic for run lifecycle
- Provides RAC (Runtime Audit Contract) acknowledgment emission
- Single point for audit expectation/acknowledgment emission

Wrapped Services:
- LessonsLearnedEngine: Learning from run outcomes
- PolicyViolationService: Policy evaluation for runs

RAC Integration (PIN-454):
- Emits acknowledgments after policy evaluation
- Domain: POLICIES
- Action: EVALUATE_POLICY

Usage:
    from app.hoc.cus.activity.L5_engines.run_governance_facade import get_run_governance_facade

    facade = get_run_governance_facade()

    # Policy evaluation (emits RAC ack automatically)
    policy_id = facade.create_policy_evaluation(
        run_id=run_id,
        tenant_id=tenant_id,
        run_status="succeeded",
    )

    # Lesson emission
    lesson_id = facade.emit_near_threshold_lesson(
        tenant_id=tenant_id,
        metric="budget",
        utilization=87.5,
        ...
    )
"""

import logging
import os
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger("nova.services.governance.run_facade")

# RAC integration flag (PIN-454)
RAC_ENABLED = os.getenv("RAC_ENABLED", "true").lower() == "true"


class RunGovernanceFacade:
    """
    Facade for run governance operations.

    This is the ONLY entry point for L5 worker code to interact with
    lessons learned and policy evaluation services.

    Layer: L4 (Domain Logic)
    Callers: RunRunner (L5)
    """

    def __init__(self):
        """Initialize facade with lazy-loaded engines."""
        self._lessons_engine = None
        self._policy_service_loaded = False

    @property
    def _lessons(self):
        """Lazy-load LessonsLearnedEngine."""
        if self._lessons_engine is None:
            from app.hoc.cus.incidents.L5_engines.lessons_engine import get_lessons_learned_engine
            self._lessons_engine = get_lessons_learned_engine()
        return self._lessons_engine

    # =========================================================================
    # Policy Evaluation Operations
    # =========================================================================

    def create_policy_evaluation(
        self,
        run_id: str,
        tenant_id: str,
        run_status: str,
        policies_checked: int = 0,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a policy evaluation record for a run (PIN-407).

        Every run produces a policy evaluation record with explicit outcome.
        This is called from the runner after run completion.

        PIN-454: Emits RAC acknowledgment after creation.

        Args:
            run_id: ID of the run
            tenant_id: Tenant scope
            run_status: Run outcome (succeeded, failed, halted, etc.)
            policies_checked: Number of policies evaluated
            is_synthetic: Whether this is a synthetic/test run
            synthetic_scenario_id: SDSR scenario ID if synthetic

        Returns:
            policy_evaluation_id if created, None otherwise
        """
        logger.debug(
            "facade.create_policy_evaluation",
            extra={"run_id": run_id, "run_status": run_status}
        )

        policy_evaluation_id = None
        error = None

        try:
            # Import here to avoid circular imports and maintain lazy loading
            from app.hoc.cus.incidents.L5_engines.policy_violation_service import create_policy_evaluation_sync

            policy_evaluation_id = create_policy_evaluation_sync(
                run_id=run_id,
                tenant_id=tenant_id,
                run_status=run_status,
                policies_checked=policies_checked,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )
        except Exception as e:
            error = str(e)
            logger.error(
                "facade.create_policy_evaluation failed",
                extra={"run_id": run_id, "error": error}
            )

        # PIN-454: Emit RAC acknowledgment
        if RAC_ENABLED:
            self._emit_ack(run_id, policy_evaluation_id, error)

        return policy_evaluation_id

    def _emit_ack(
        self,
        run_id: str,
        result_id: Optional[str],
        error: Optional[str],
    ) -> None:
        """
        Emit RAC acknowledgment for policy evaluation.

        PIN-454: Facades emit acks after domain operations.
        """
        try:
            # L5 imports (migrated to HOC per SWEEP-04)
            from app.hoc.cus.logs.L5_schemas.audit_models import AuditAction, AuditDomain, DomainAck
            from app.hoc.cus.general.L5_engines.audit_store import get_audit_store

            ack = DomainAck(
                run_id=UUID(run_id),
                domain=AuditDomain.POLICIES,
                action=AuditAction.EVALUATE_POLICY,
                result_id=result_id,
                error=error,
            )

            store = get_audit_store()
            store.add_ack(UUID(run_id), ack)

            logger.debug(
                "facade.emit_ack",
                extra={
                    "run_id": run_id,
                    "domain": "policies",
                    "action": "evaluate_policy",
                    "success": error is None,
                }
            )
        except Exception as e:
            # RAC failures should not block the facade
            logger.warning(f"Failed to emit RAC ack: {e}")

    # =========================================================================
    # Lessons Learned Operations
    # =========================================================================

    def emit_near_threshold_lesson(
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
        Emit a near-threshold lesson for proactive governance.

        Called when a metric approaches its limit (e.g., 85% budget utilization).

        Args:
            tenant_id: Tenant scope
            metric: Name of the metric (e.g., "budget", "rate_limit")
            utilization: Current utilization percentage (0-100)
            threshold_value: The configured limit
            current_value: The current consumption value
            source_event_id: Run ID that triggered this lesson
            window: Time window for the metric (e.g., "24h")
            is_synthetic: Whether this is from a synthetic run
            synthetic_scenario_id: SDSR scenario ID if synthetic

        Returns:
            lesson_id if created, None otherwise
        """
        logger.debug(
            "facade.emit_near_threshold_lesson",
            extra={
                "tenant_id": tenant_id,
                "metric": metric,
                "utilization": utilization,
            }
        )

        try:
            return self._lessons.emit_near_threshold(
                tenant_id=tenant_id,
                metric=metric,
                utilization=utilization,
                threshold_value=threshold_value,
                current_value=current_value,
                source_event_id=source_event_id,
                window=window,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )
        except Exception as e:
            logger.error(
                "facade.emit_near_threshold_lesson failed",
                extra={"tenant_id": tenant_id, "error": str(e)}
            )
            return None

    def emit_critical_success_lesson(
        self,
        tenant_id: str,
        success_type: str,
        metrics: Dict[str, Any],
        source_event_id: UUID,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Emit a critical success lesson for positive reinforcement.

        Called when a run achieves notable efficiency or success metrics.

        Args:
            tenant_id: Tenant scope
            success_type: Type of success (e.g., "cost_efficiency")
            metrics: Success metrics (e.g., {"under_budget_pct": 50.0})
            source_event_id: Run ID that triggered this lesson
            is_synthetic: Whether this is from a synthetic run
            synthetic_scenario_id: SDSR scenario ID if synthetic

        Returns:
            lesson_id if created, None otherwise
        """
        logger.debug(
            "facade.emit_critical_success_lesson",
            extra={
                "tenant_id": tenant_id,
                "success_type": success_type,
            }
        )

        try:
            return self._lessons.emit_critical_success(
                tenant_id=tenant_id,
                success_type=success_type,
                metrics=metrics,
                source_event_id=source_event_id,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )
        except Exception as e:
            logger.error(
                "facade.emit_critical_success_lesson failed",
                extra={"tenant_id": tenant_id, "error": str(e)}
            )
            return None


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[RunGovernanceFacade] = None


def get_run_governance_facade() -> RunGovernanceFacade:
    """
    Get the run governance facade instance.

    This is the recommended way to access governance operations from
    the L5 worker runtime.

    Returns:
        RunGovernanceFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = RunGovernanceFacade()
    return _facade_instance
