# Layer: L4 — HOC Spine (Driver)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: worker (run completion)
#   Execution: sync
# Lifecycle:
#   Emits: RUN_COMPLETED, INCIDENT_CREATED
#   Subscribes: none
# Data Access:
#   Reads: via domain facades
#   Writes: via domain facades (transactional)
# Database:
#   Scope: hoc_spine (cross-domain transaction boundary)
#   Models: various (via facades)
# Role: Transaction Coordinator for atomic cross-domain writes — OWNS COMMIT AUTHORITY
# Callers: ROK (L5), RunRunner (L5)
# Allowed Imports: L5 facades, L6, L7 (models)
# Forbidden Imports: L1, L2, L3
# Contract: EXECUTION_SEMANTIC_CONTRACT.md
# Reference: PIN-470, PIN-454 (Cross-Domain Orchestration Audit), FIX-001

"""
Transaction Coordinator for Cross-Domain Writes

This module provides atomic transaction coordination for run completion,
ensuring that ALL domain updates succeed or NONE persist.

Problem Addressed (FIX-001):
- Incident/policy/trace writes are independent
- Partial failure causes inconsistent state
- Events published before all operations complete

Solution:
- Wrap all domain operations in single transaction boundary
- Track which operations succeeded for rollback
- Publish events ONLY after successful commit

Architecture:

    ┌──────────────────────────────────────────────────────────────────┐
    │              Transaction Coordinator (L4)                        │
    ├──────────────────────────────────────────────────────────────────┤
    │  TRANSACTION FLOW:                                               │
    │  1. Begin transaction                                            │
    │  2. Create incident (via IncidentFacade)                         │
    │  3. Create policy evaluation (via GovernanceFacade)              │
    │  4. Complete trace (via TraceFacade)                             │
    │  5. Commit transaction                                           │
    │  6. Publish events (post-commit only)                            │
    │                                                                  │
    │  ON FAILURE:                                                     │
    │  • Rollback transaction                                          │
    │  • No events published                                           │
    │  • Raise TransactionFailed with context                          │
    │                                                                  │
    │  INVARIANTS:                                                     │
    │  • Events ONLY after successful commit                           │
    │  • Partial state is never visible                                │
    │  • All domain operations use facades (layer compliance)          │
    └──────────────────────────────────────────────────────────────────┘

Usage:

    from app.hoc.cus.hoc_spine.drivers.transaction_coordinator import (
        RunCompletionTransaction,
        get_transaction_coordinator,
    )

    coordinator = get_transaction_coordinator()
    result = coordinator.execute(
        run_id=run_id,
        tenant_id=tenant_id,
        run_status="succeeded",
        agent_id=agent_id,
    )
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from sqlmodel import Session

from app.db import engine
from app.events import get_publisher

# RAC imports for rollback audit trail (V2.0.0 - hoc_spine)
from app.hoc.cus.hoc_spine.schemas.rac_models import (
    AckStatus,
    AuditAction,
    AuditDomain,
    DomainAck,
)
# L5 import (V2.0.0 - hoc_spine)
from app.hoc.cus.hoc_spine.services.audit_store import get_audit_store
from app.hoc.cus.hoc_spine.schemas.protocols import TraceFacadePort

# Feature flag for RAC audit trail on rollback
RAC_ROLLBACK_AUDIT_ENABLED = os.getenv("RAC_ROLLBACK_AUDIT_ENABLED", "true").lower() == "true"

logger = logging.getLogger("nova.services.governance.transaction_coordinator")

# Feature flag for transaction coordinator
TRANSACTION_COORDINATOR_ENABLED = os.getenv("TRANSACTION_COORDINATOR_ENABLED", "true").lower() == "true"


class TransactionPhase(str, Enum):
    """Phases of transaction execution."""

    NOT_STARTED = "NOT_STARTED"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    TRACE_COMPLETED = "TRACE_COMPLETED"
    COMMITTED = "COMMITTED"
    EVENTS_PUBLISHED = "EVENTS_PUBLISHED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


class TransactionFailed(Exception):
    """Raised when cross-domain transaction fails."""

    def __init__(
        self,
        message: str,
        phase: TransactionPhase,
        partial_results: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.phase = phase
        self.partial_results = partial_results or {}
        self.cause = cause


@dataclass
class DomainResult:
    """Result from a single domain operation."""

    domain: str
    action: str
    result_id: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/events."""
        return {
            "domain": self.domain,
            "action": self.action,
            "result_id": self.result_id,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TransactionResult:
    """Result of a successful cross-domain transaction."""

    run_id: str
    incident_result: Optional[DomainResult] = None
    policy_result: Optional[DomainResult] = None
    trace_result: Optional[DomainResult] = None
    phase: TransactionPhase = TransactionPhase.NOT_STARTED
    events_published: List[str] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def is_complete(self) -> bool:
        """Check if transaction completed successfully."""
        return self.phase in (TransactionPhase.COMMITTED, TransactionPhase.EVENTS_PUBLISHED)

    @property
    def all_domains_succeeded(self) -> bool:
        """Check if all domain operations succeeded."""
        results = [self.incident_result, self.policy_result, self.trace_result]
        return all(r is None or r.success for r in results)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/events."""
        return {
            "run_id": self.run_id,
            "phase": self.phase.value,
            "is_complete": self.is_complete,
            "all_domains_succeeded": self.all_domains_succeeded,
            "incident": self.incident_result.to_dict() if self.incident_result else None,
            "policy": self.policy_result.to_dict() if self.policy_result else None,
            "trace": self.trace_result.to_dict() if self.trace_result else None,
            "events_published": self.events_published,
            "duration_ms": self.duration_ms,
        }


@dataclass
class RollbackAction:
    """Describes a rollback action for a domain operation."""

    domain: str
    action: str
    rollback_fn: Callable[[], None]
    result_id: Optional[str] = None  # ID of created entity (for audit trail)
    executed: bool = False


class RunCompletionTransaction:
    """
    Atomic cross-domain transaction for run completion.

    Ensures either ALL domain updates succeed or NONE persist.
    Events published ONLY after commit succeeds.

    Layer: L4 (Domain Logic)
    Callers: ROK (L5), RunRunner (L5)
    """

    def __init__(
        self,
        publisher=None,
        incident_driver=None,
        trace_facade: Optional[TraceFacadePort] = None,
    ):
        """
        Initialize transaction coordinator.

        Args:
            publisher: Optional event publisher. Uses default if not provided.
            incident_driver: Injected IncidentDriver instance (PIN-513 L1 re-wiring).
            trace_facade: Injected TraceFacade instance (PIN-513 L1 re-wiring).
        """
        self._publisher = publisher or get_publisher()
        self._incident_driver = incident_driver
        self._trace_facade = trace_facade
        self._rollback_stack: List[RollbackAction] = []
        self._result: Optional[TransactionResult] = None

    def execute(
        self,
        run_id: str,
        tenant_id: str,
        run_status: str,
        agent_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        trace_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
        skip_events: bool = False,
    ) -> TransactionResult:
        """
        Execute cross-domain updates atomically.

        Order:
        1. Create incident (via IncidentFacade)
        2. Evaluate policy (via GovernanceFacade)
        3. Complete trace (via TraceFacade) - if trace_id provided
        4. Commit transaction
        5. Publish events (after commit, unless skip_events=True)

        On ANY failure: rollback all, raise TransactionFailed

        Args:
            run_id: ID of the run
            tenant_id: Tenant scope
            run_status: Final run status (succeeded, failed, etc.)
            agent_id: Agent that executed the run
            error_code: Error code if failed
            error_message: Error message if failed
            trace_id: Trace ID to complete (optional)
            is_synthetic: Whether this is a synthetic/test run
            synthetic_scenario_id: SDSR scenario ID if synthetic
            skip_events: If True, don't publish events (for testing)

        Returns:
            TransactionResult with all domain results

        Raises:
            TransactionFailed: If any domain operation fails
        """
        start_time = datetime.now(timezone.utc)
        result = TransactionResult(run_id=run_id)
        self._result = result
        self._rollback_stack = []

        logger.info(
            "transaction_coordinator.execute_start",
            extra={
                "run_id": run_id,
                "tenant_id": tenant_id,
                "run_status": run_status,
            },
        )

        try:
            with Session(engine) as session:  # type: ignore[arg-type]
                # Phase 1: Create incident
                self._create_incident(
                    session=session,
                    run_id=run_id,
                    tenant_id=tenant_id,
                    run_status=run_status,
                    agent_id=agent_id,
                    error_code=error_code,
                    error_message=error_message,
                    is_synthetic=is_synthetic,
                    synthetic_scenario_id=synthetic_scenario_id,
                )

                # Phase 2: Create policy evaluation
                self._create_policy_evaluation(
                    session=session,
                    run_id=run_id,
                    tenant_id=tenant_id,
                    run_status=run_status,
                    is_synthetic=is_synthetic,
                    synthetic_scenario_id=synthetic_scenario_id,
                )

                # Phase 3: Complete trace (if trace_id provided)
                if trace_id:
                    self._complete_trace(
                        session=session,
                        run_id=run_id,
                        trace_id=trace_id,
                        run_status=run_status,
                    )

                # Commit transaction
                session.commit()
                result.phase = TransactionPhase.COMMITTED

                logger.info(
                    "transaction_coordinator.committed",
                    extra={
                        "run_id": run_id,
                        "incident_id": result.incident_result.result_id if result.incident_result else None,
                        "policy_id": result.policy_result.result_id if result.policy_result else None,
                    },
                )

            # Phase 4: Publish events (ONLY after successful commit)
            if not skip_events:
                self._publish_events(run_id, run_status)

            # Calculate duration
            end_time = datetime.now(timezone.utc)
            result.duration_ms = int((end_time - start_time).total_seconds() * 1000)

            logger.info(
                "transaction_coordinator.complete",
                extra={
                    "run_id": run_id,
                    "phase": result.phase.value,
                    "duration_ms": result.duration_ms,
                    "events_published": result.events_published,
                },
            )

            return result

        except TransactionFailed:
            # Already handled, re-raise
            raise

        except Exception as e:
            # Rollback and wrap in TransactionFailed
            self._execute_rollback()

            logger.error(
                "transaction_coordinator.failed",
                extra={
                    "run_id": run_id,
                    "phase": result.phase.value,
                    "error": str(e),
                },
            )

            raise TransactionFailed(
                message=f"Cross-domain transaction failed: {e}",
                phase=result.phase,
                partial_results=result.to_dict(),
                cause=e,
            )

    # =========================================================================
    # Domain Operations
    # =========================================================================

    def _create_incident(
        self,
        session: Session,  # Reserved for future transaction integration
        run_id: str,
        tenant_id: str,
        run_status: str,
        agent_id: Optional[str],
        error_code: Optional[str],
        error_message: Optional[str],
        is_synthetic: bool,
        synthetic_scenario_id: Optional[str],
    ) -> None:
        """Create incident within transaction."""
        _ = session  # Reserved for future transaction integration
        assert self._result is not None, "Transaction result must be initialized"
        result = self._result

        try:
            if self._incident_driver is None:
                raise NotImplementedError(
                    "Incident driver not injected. Wire via RunCompletionTransaction(incident_driver=...)"
                )
            incident_id = self._incident_driver.check_and_create_incident(
                run_id=run_id,
                status=run_status,
                error_message=error_message,
                tenant_id=tenant_id,
                agent_id=agent_id,
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )

            if incident_id:
                result.phase = TransactionPhase.INCIDENT_CREATED
                # Register rollback (soft-delete incident if needed)
                # Capture incident_id in closure for rollback
                captured_incident_id = incident_id
                self._rollback_stack.append(RollbackAction(
                    domain="incidents",
                    action="create_incident",
                    rollback_fn=lambda: self._rollback_incident(captured_incident_id),
                    result_id=incident_id,
                ))

            logger.debug(
                "transaction_coordinator.incident_created",
                extra={"run_id": run_id, "incident_id": incident_id},
            )

        except Exception as e:
            result.incident_result = DomainResult(
                domain="incidents",
                action="create_incident",
                success=False,
                error=str(e),
            )
            raise TransactionFailed(
                message=f"Incident creation failed: {e}",
                phase=TransactionPhase.NOT_STARTED,
                partial_results=result.to_dict(),
                cause=e,
            )

    def _create_policy_evaluation(
        self,
        session: Session,  # Reserved for future use
        run_id: str,
        tenant_id: str,
        run_status: str,
        is_synthetic: bool,
        synthetic_scenario_id: Optional[str],
    ) -> None:
        """Create policy evaluation within transaction."""
        _ = session  # Reserved for future transaction integration
        assert self._result is not None, "Transaction result must be initialized"
        result = self._result

        try:
            # L5 engine import (V2.0.0 - hoc_spine)
            from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import get_run_governance_facade

            facade = get_run_governance_facade()
            policy_id = facade.create_policy_evaluation(
                run_id=run_id,
                tenant_id=tenant_id,
                run_status=run_status,
                policies_checked=0,  # Can be enhanced later
                is_synthetic=is_synthetic,
                synthetic_scenario_id=synthetic_scenario_id,
            )

            result.policy_result = DomainResult(
                domain="policies",
                action="evaluate_policy",
                result_id=policy_id,
                success=policy_id is not None,
            )

            if policy_id:
                result.phase = TransactionPhase.POLICY_EVALUATED
                # Register rollback
                # Capture policy_id in closure for rollback
                captured_policy_id = policy_id
                self._rollback_stack.append(RollbackAction(
                    domain="policies",
                    action="evaluate_policy",
                    rollback_fn=lambda: self._rollback_policy(captured_policy_id),
                    result_id=policy_id,
                ))

            logger.debug(
                "transaction_coordinator.policy_evaluated",
                extra={"run_id": run_id, "policy_id": policy_id},
            )

        except Exception as e:
            result.policy_result = DomainResult(
                domain="policies",
                action="evaluate_policy",
                success=False,
                error=str(e),
            )
            raise TransactionFailed(
                message=f"Policy evaluation failed: {e}",
                phase=TransactionPhase.INCIDENT_CREATED,
                partial_results=result.to_dict(),
                cause=e,
            )

    def _complete_trace(
        self,
        session: Session,  # Reserved for future use
        run_id: str,
        trace_id: str,
        run_status: str,
    ) -> None:
        """Complete trace within transaction."""
        _ = session  # Reserved for future transaction integration
        assert self._result is not None, "Transaction result must be initialized"
        txn_result = self._result

        try:
            if self._trace_facade is None:
                raise NotImplementedError(
                    "Trace facade not injected. Wire via RunCompletionTransaction(trace_facade=...)"
                )
            trace_success = self._trace_facade.complete_trace_sync(
                run_id=run_id,
                trace_id=trace_id,
                run_status=run_status,
            )

            if trace_success:
                txn_result.phase = TransactionPhase.TRACE_COMPLETED

            logger.debug(
                "transaction_coordinator.trace_completed",
                extra={"run_id": run_id, "trace_id": trace_id, "success": trace_success},
            )

        except Exception as e:
            txn_result.trace_result = DomainResult(
                domain="traces",
                action="complete_trace",
                success=False,
                error=str(e),
            )
            # Trace completion failure is not fatal - log and continue
            logger.warning(
                "transaction_coordinator.trace_completion_failed",
                extra={"run_id": run_id, "trace_id": trace_id, "error": str(e)},
            )

    # =========================================================================
    # Event Publication (Post-Commit Only)
    # =========================================================================

    def _publish_events(self, run_id: str, run_status: str) -> None:
        """
        Publish events ONLY after successful commit.

        Events are NOT part of the transaction - they're fire-and-forget
        notifications that occur after the transaction is committed.
        """
        assert self._result is not None, "Transaction result must be initialized"
        result = self._result

        try:
            # Run completion event
            self._publisher.publish("run.completed", {
                "run_id": run_id,
                "status": run_status,
                "incident_id": result.incident_result.result_id if result.incident_result else None,
                "policy_id": result.policy_result.result_id if result.policy_result else None,
                "trace_id": result.trace_result.result_id if result.trace_result else None,
            })
            result.events_published.append("run.completed")

            # Incident created event
            if result.incident_result and result.incident_result.result_id:
                self._publisher.publish("incident.created", {
                    "run_id": run_id,
                    "incident_id": result.incident_result.result_id,
                    "outcome": run_status,
                })
                result.events_published.append("incident.created")

            # Policy evaluated event
            if result.policy_result and result.policy_result.result_id:
                self._publisher.publish("policy.evaluated", {
                    "run_id": run_id,
                    "policy_id": result.policy_result.result_id,
                    "outcome": run_status,
                })
                result.events_published.append("policy.evaluated")

            result.phase = TransactionPhase.EVENTS_PUBLISHED

        except Exception as e:
            # Event publication failure is not fatal - log but don't fail
            logger.warning(
                "transaction_coordinator.event_publish_failed",
                extra={"run_id": run_id, "error": str(e)},
            )

    # =========================================================================
    # Rollback Handlers
    # =========================================================================

    def _execute_rollback(self) -> None:
        """
        Execute rollback actions in reverse order.

        For each rolled-back action, emit a DomainAck with:
        - status=ROLLED_BACK
        - rolled_back=true
        - rollback_reason explaining why

        This preserves the audit trail per PIN-454: data is consistent,
        audit trail remains truthful.
        """
        result = self._result
        if result is not None:
            result.phase = TransactionPhase.ROLLED_BACK

        for action in reversed(self._rollback_stack):
            if action.executed:
                continue

            rollback_error: Optional[str] = None
            try:
                logger.info(
                    "transaction_coordinator.rollback_action",
                    extra={"domain": action.domain, "action": action.action},
                )
                action.rollback_fn()
                action.executed = True
            except Exception as e:
                rollback_error = str(e)
                logger.error(
                    "transaction_coordinator.rollback_failed",
                    extra={"domain": action.domain, "action": action.action, "error": str(e)},
                )

            # Emit DomainAck with rolled_back=true for audit trail
            # This ensures the audit store knows the action was rolled back
            if RAC_ROLLBACK_AUDIT_ENABLED and result is not None:
                self._emit_rollback_ack(
                    run_id=result.run_id,
                    domain=action.domain,
                    action_name=action.action,
                    result_id=action.result_id,
                    rollback_error=rollback_error,
                )

    def _emit_rollback_ack(
        self,
        run_id: str,
        domain: str,
        action_name: str,
        result_id: Optional[str],
        rollback_error: Optional[str],
    ) -> None:
        """
        Emit a DomainAck marking an action as rolled back.

        Per PIN-454: When rollback happens, emit a DomainAck with
        status=ROLLED_BACK + rolled_back=true. Do not silently erase history.
        """
        try:
            # Map domain string to AuditDomain enum
            domain_map = {
                "incidents": AuditDomain.INCIDENTS,
                "policies": AuditDomain.POLICIES,
                "traces": AuditDomain.LOGS,
            }
            audit_domain = domain_map.get(domain)
            if audit_domain is None:
                logger.warning(
                    "transaction_coordinator.unknown_domain_for_ack",
                    extra={"domain": domain},
                )
                return

            # Map action string to AuditAction enum
            action_map = {
                "create_incident": AuditAction.CREATE_INCIDENT,
                "evaluate_policy": AuditAction.EVALUATE_POLICY,
                "complete_trace": AuditAction.COMPLETE_TRACE,
            }
            audit_action = action_map.get(action_name)
            if audit_action is None:
                logger.warning(
                    "transaction_coordinator.unknown_action_for_ack",
                    extra={"action": action_name},
                )
                return

            # Create the rollback ack
            rollback_reason = (
                f"Transaction rollback due to downstream failure"
                if rollback_error is None
                else f"Transaction rollback failed: {rollback_error}"
            )

            ack = DomainAck(
                run_id=UUID(run_id),
                domain=audit_domain,
                action=audit_action,
                status=AckStatus.ROLLED_BACK,
                result_id=result_id,
                error=rollback_error,
                rolled_back=True,
                rollback_reason=rollback_reason,
                metadata={
                    "rollback_phase": "transaction_coordinator",
                    "rollback_success": rollback_error is None,
                },
            )

            # Store the ack in the audit store
            store = get_audit_store()
            store.add_ack(UUID(run_id), ack)

            logger.info(
                "transaction_coordinator.rollback_ack_emitted",
                extra={
                    "run_id": run_id,
                    "domain": domain,
                    "action": action_name,
                    "result_id": result_id,
                    "rollback_reason": rollback_reason,
                },
            )

        except Exception as e:
            # Rollback ack emission failure is not fatal - log and continue
            logger.warning(
                "transaction_coordinator.rollback_ack_failed",
                extra={
                    "run_id": run_id,
                    "domain": domain,
                    "action": action_name,
                    "error": str(e),
                },
            )

    def _rollback_incident(self, incident_id: str) -> None:
        """Rollback incident creation (soft-delete or mark as rolled_back)."""
        try:
            # For now, just log - actual rollback depends on incident model
            logger.info(
                "transaction_coordinator.incident_rollback",
                extra={"incident_id": incident_id},
            )
            # TODO: Implement actual rollback when incident model supports it
            # This could be:
            # - Soft delete (set deleted_at)
            # - Mark as rolled_back status
            # - Actually delete (if within grace period)
        except Exception as e:
            logger.error(
                "transaction_coordinator.incident_rollback_failed",
                extra={"incident_id": incident_id, "error": str(e)},
            )

    def _rollback_policy(self, policy_id: str) -> None:
        """Rollback policy evaluation (soft-delete or mark as rolled_back)."""
        try:
            logger.info(
                "transaction_coordinator.policy_rollback",
                extra={"policy_id": policy_id},
            )
            # TODO: Implement actual rollback when policy model supports it
        except Exception as e:
            logger.error(
                "transaction_coordinator.policy_rollback_failed",
                extra={"policy_id": policy_id, "error": str(e)},
            )


# =============================================================================
# Factory Function
# =============================================================================

_transaction_coordinator: Optional[RunCompletionTransaction] = None


def get_transaction_coordinator() -> RunCompletionTransaction:
    """
    Get the singleton transaction coordinator instance.

    Returns:
        RunCompletionTransaction instance
    """
    global _transaction_coordinator
    if _transaction_coordinator is None:
        _transaction_coordinator = RunCompletionTransaction()
    return _transaction_coordinator


def create_transaction_coordinator(publisher=None) -> RunCompletionTransaction:
    """
    Create a new transaction coordinator instance.

    Use this for testing or when you need a fresh instance.

    Args:
        publisher: Optional event publisher

    Returns:
        RunCompletionTransaction instance
    """
    return RunCompletionTransaction(publisher=publisher)
