# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: worker (run lifecycle events)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via L4 engines
#   Writes: via L4 engines
# Role: Run Governance Facade - Centralized access to governance operations for runs
# Callers: L5 runner (worker runtime)
# Allowed Imports: L4 domain engines (lessons, policy), L4 audit, L6, L7 (models)
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-454 (Cross-Domain Orchestration Audit), FIX-002

"""
Run Governance Facade (L4 Domain Logic)

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
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import get_run_governance_facade

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

from app.hoc.cus.hoc_spine.schemas.protocols import LessonsEnginePort, PolicyEvaluationPort

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

    def __init__(
        self,
        lessons_engine: Optional[LessonsEnginePort] = None,
        policy_evaluator: Optional[PolicyEvaluationPort] = None,
    ):
        """Initialize facade with injected engines (PIN-513 L1 re-wiring).

        Args:
            lessons_engine: Injected lessons engine (LessonsLearnedEngine).
            policy_evaluator: Injected policy evaluation callable.
        """
        self._lessons_engine = lessons_engine
        self._policy_evaluator = policy_evaluator

    @property
    def _lessons(self):
        """Return injected LessonsLearnedEngine."""
        if self._lessons_engine is None:
            raise NotImplementedError(
                "Lessons engine not injected. Wire via RunGovernanceFacade(lessons_engine=...)"
            )
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
            if self._policy_evaluator is None:
                raise NotImplementedError(
                    "Policy evaluator not injected. Wire via RunGovernanceFacade(policy_evaluator=...)"
                )
            policy_evaluation_id = self._policy_evaluator(
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
            # L5 imports (V2.0.0 - hoc_spine)
            from app.hoc.cus.hoc_spine.schemas.rac_models import AuditAction, AuditDomain, DomainAck
            from app.hoc.cus.hoc_spine.services.audit_store import get_audit_store

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


def wire_run_governance_facade() -> RunGovernanceFacade:
    """
    Wire the RunGovernanceFacade singleton with real L5 engines.

    Called once from bootstrap_hoc_spine() at application startup.
    After this call, get_run_governance_facade() returns a facade
    with live lessons_engine and policy_evaluator — no silent no-ops.

    Engines injected:
        - lessons_engine: LessonsLearnedEngine (policies/L5_engines)
        - policy_evaluator: create_policy_evaluation_sync (incidents/L5_engines)

    Returns:
        The wired RunGovernanceFacade singleton
    """
    global _facade_instance

    from app.hoc.cus.policies.L5_engines.lessons_engine import get_lessons_learned_engine
    from app.hoc.cus.incidents.L5_engines.policy_violation_engine import create_policy_evaluation_sync

    def _l4_policy_evaluator(
        run_id: str,
        tenant_id: str,
        run_status: str,
        policies_checked: int = 0,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """L4 transaction wrapper for policy evaluation.

        Creates psycopg2 connection, delegates to L5 engine, commits.
        L4 owns the transaction boundary (PIN-520).
        """
        import psycopg2

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("policy_eval_sync_no_database_url")
            return None

        conn = psycopg2.connect(database_url)
        try:
            result = create_policy_evaluation_sync(
                run_id=run_id,
                tenant_id=tenant_id,
                run_status=run_status,
                policies_checked=policies_checked,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
                conn=conn,
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    _facade_instance = RunGovernanceFacade(
        lessons_engine=get_lessons_learned_engine(),
        policy_evaluator=_l4_policy_evaluator,
    )

    logger.info("run_governance_facade wired with real engines")
    return _facade_instance


def get_run_governance_facade() -> RunGovernanceFacade:
    """
    Get the run governance facade instance.

    This is the recommended way to access governance operations from
    the L5 worker runtime.

    Returns:
        RunGovernanceFacade instance (wired at startup via wire_run_governance_facade)

    Raises:
        RuntimeError: If called before wire_run_governance_facade() at startup
    """
    global _facade_instance
    if _facade_instance is None:
        raise RuntimeError(
            "RunGovernanceFacade not wired. "
            "bootstrap_hoc_spine() must run before get_run_governance_facade() is called."
        )
    return _facade_instance
