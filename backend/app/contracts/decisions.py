"""Phase 4B: Decision Record Models and Service

Implements DECISION_RECORD_CONTRACT v0.2.

Contract-mandated fields:
- decision_source: human | system | hybrid
- decision_trigger: explicit | autonomous | reactive

Rule: Emit records where decisions already happen. No logic changes.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("nova.contracts.decisions")


# =============================================================================
# Contract Enums (DECISION_RECORD_CONTRACT v0.2)
# =============================================================================


class DecisionType(str, Enum):
    """Types of decisions that must be recorded."""
    ROUTING = "routing"
    RECOVERY = "recovery"
    MEMORY = "memory"
    POLICY = "policy"
    BUDGET = "budget"


class DecisionSource(str, Enum):
    """Who originated the decision authority."""
    HUMAN = "human"
    SYSTEM = "system"
    HYBRID = "hybrid"


class DecisionTrigger(str, Enum):
    """Why the decision occurred."""
    EXPLICIT = "explicit"
    AUTONOMOUS = "autonomous"
    REACTIVE = "reactive"


class DecisionOutcome(str, Enum):
    """Result of the decision."""
    SELECTED = "selected"      # Positive selection made
    REJECTED = "rejected"      # All options rejected
    SKIPPED = "skipped"        # Decision point bypassed
    BLOCKED = "blocked"        # Decision blocked by constraint
    NONE = "none"              # No decision needed


class CausalRole(str, Enum):
    """When in the lifecycle this decision occurred."""
    PRE_RUN = "pre_run"        # Before run exists (routing, policy pre-check)
    IN_RUN = "in_run"          # During run execution
    POST_RUN = "post_run"      # After run completion (reconciliation)


# =============================================================================
# Decision Record Model
# =============================================================================


class DecisionRecord(BaseModel):
    """
    Contract-aligned decision record.

    Every decision (routing, recovery, memory, policy, budget) emits one of these.
    Append-only. No business logic.
    """
    # Identity
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:16])

    # Contract-mandated metadata
    decision_type: DecisionType
    decision_source: DecisionSource
    decision_trigger: DecisionTrigger

    # Decision content
    decision_inputs: Dict[str, Any] = Field(default_factory=dict)
    decision_outcome: DecisionOutcome
    decision_reason: Optional[str] = None

    # Context
    run_id: Optional[str] = None
    workflow_id: Optional[str] = None
    tenant_id: str = "default"

    # Causal binding (Phase 4B extension)
    # request_id: First-class causal key - present for pre-run decisions
    # causal_role: When in lifecycle this decision occurred
    request_id: Optional[str] = None
    causal_role: CausalRole = CausalRole.IN_RUN

    # Timing
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Extended details (type-specific)
    details: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/logging."""
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "decision_source": self.decision_source.value,
            "decision_trigger": self.decision_trigger.value,
            "decision_inputs": self.decision_inputs,
            "decision_outcome": self.decision_outcome.value,
            "decision_reason": self.decision_reason,
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "causal_role": self.causal_role.value,
            "decided_at": self.decided_at.isoformat(),
            "details": self.details,
        }


# =============================================================================
# Decision Record Service (Append-Only Sink)
# =============================================================================


class DecisionRecordService:
    """
    Append-only sink for decision records.

    Emits to contracts.decision_records table.
    Non-blocking - failures are logged but don't affect callers.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._enabled = self._db_url is not None

    async def emit(self, record: DecisionRecord) -> bool:
        """
        Emit a decision record to the sink.

        Returns True if emission succeeded, False otherwise.
        Non-blocking - failures don't propagate.
        """
        if not self._enabled:
            logger.debug(f"Decision record emission disabled: {record.decision_id}")
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO contracts.decision_records (
                            decision_id, decision_type, decision_source, decision_trigger,
                            decision_inputs, decision_outcome, decision_reason,
                            run_id, workflow_id, tenant_id, request_id, causal_role,
                            decided_at, details
                        ) VALUES (
                            :decision_id, :decision_type, :decision_source, :decision_trigger,
                            :decision_inputs, :decision_outcome, :decision_reason,
                            :run_id, :workflow_id, :tenant_id, :request_id, :causal_role,
                            :decided_at, :details
                        )
                    """),
                    {
                        "decision_id": record.decision_id,
                        "decision_type": record.decision_type.value,
                        "decision_source": record.decision_source.value,
                        "decision_trigger": record.decision_trigger.value,
                        "decision_inputs": json.dumps(record.decision_inputs),
                        "decision_outcome": record.decision_outcome.value,
                        "decision_reason": record.decision_reason,
                        "run_id": record.run_id,
                        "workflow_id": record.workflow_id,
                        "tenant_id": record.tenant_id,
                        "request_id": record.request_id,
                        "causal_role": record.causal_role.value,
                        "decided_at": record.decided_at,
                        "details": json.dumps(record.details),
                    },
                )
                conn.commit()
            engine.dispose()

            logger.debug(
                f"decision_record_emitted",
                extra={
                    "decision_id": record.decision_id,
                    "decision_type": record.decision_type.value,
                    "decision_outcome": record.decision_outcome.value,
                    "causal_role": record.causal_role.value,
                },
            )
            return True

        except SQLAlchemyError as e:
            logger.warning(f"Failed to emit decision record: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error emitting decision record: {e}")
            return False

    def emit_sync(self, record: DecisionRecord) -> bool:
        """Synchronous version of emit for non-async contexts."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context - can't use run_until_complete
                # Fall back to sync implementation
                return self._emit_sync_impl(record)
            return loop.run_until_complete(self.emit(record))
        except RuntimeError:
            return self._emit_sync_impl(record)

    def _emit_sync_impl(self, record: DecisionRecord) -> bool:
        """Synchronous implementation of emit."""
        if not self._enabled:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO contracts.decision_records (
                            decision_id, decision_type, decision_source, decision_trigger,
                            decision_inputs, decision_outcome, decision_reason,
                            run_id, workflow_id, tenant_id, request_id, causal_role,
                            decided_at, details
                        ) VALUES (
                            :decision_id, :decision_type, :decision_source, :decision_trigger,
                            :decision_inputs, :decision_outcome, :decision_reason,
                            :run_id, :workflow_id, :tenant_id, :request_id, :causal_role,
                            :decided_at, :details
                        )
                    """),
                    {
                        "decision_id": record.decision_id,
                        "decision_type": record.decision_type.value,
                        "decision_source": record.decision_source.value,
                        "decision_trigger": record.decision_trigger.value,
                        "decision_inputs": json.dumps(record.decision_inputs),
                        "decision_outcome": record.decision_outcome.value,
                        "decision_reason": record.decision_reason,
                        "run_id": record.run_id,
                        "workflow_id": record.workflow_id,
                        "tenant_id": record.tenant_id,
                        "request_id": record.request_id,
                        "causal_role": record.causal_role.value,
                        "decided_at": record.decided_at,
                        "details": json.dumps(record.details),
                    },
                )
                conn.commit()
            engine.dispose()
            return True
        except Exception as e:
            logger.warning(f"Failed to emit decision record (sync): {e}")
            return False


# =============================================================================
# Singleton
# =============================================================================

_service: Optional[DecisionRecordService] = None


def get_decision_service() -> DecisionRecordService:
    """Get singleton decision record service."""
    global _service
    if _service is None:
        _service = DecisionRecordService()
    return _service


# =============================================================================
# Helper Functions for Common Decision Patterns
# =============================================================================


def emit_routing_decision(
    run_id: Optional[str],
    routed: bool,
    selected_agent: Optional[str],
    eligible_agents: list,
    rejection_reason: Optional[str] = None,
    tenant_id: str = "default",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    causal_role: CausalRole = CausalRole.PRE_RUN,  # Routing is typically pre-run
) -> DecisionRecord:
    """
    Emit a routing decision record.

    Called from CARE engine after every route() call.
    Note: Routing typically happens BEFORE run exists, so causal_role=PRE_RUN.
    """
    record = DecisionRecord(
        decision_type=DecisionType.ROUTING,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.EXPLICIT,
        decision_inputs={
            "eligible_agents": eligible_agents,
            "agents_count": len(eligible_agents),
        },
        decision_outcome=(
            DecisionOutcome.SELECTED if routed and selected_agent
            else DecisionOutcome.REJECTED if not routed and rejection_reason
            else DecisionOutcome.NONE
        ),
        decision_reason=rejection_reason if not routed else f"Selected {selected_agent}",
        run_id=run_id,
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=causal_role,
        details=details or {},
    )

    get_decision_service().emit_sync(record)
    return record


def emit_recovery_decision(
    run_id: Optional[str],
    evaluated: bool,
    triggered: bool,
    action: Optional[str] = None,
    candidates_count: int = 0,
    reason: Optional[str] = None,
    tenant_id: str = "default",
    request_id: Optional[str] = None,
    causal_role: CausalRole = CausalRole.IN_RUN,  # Recovery is during run execution
) -> DecisionRecord:
    """
    Emit a recovery decision record.

    Called from recovery engine after every evaluation.
    Note: Recovery happens DURING run execution, so causal_role=IN_RUN.
    """
    if not evaluated:
        outcome = DecisionOutcome.SKIPPED
        reason = reason or "Recovery not evaluated (success path)"
    elif triggered:
        outcome = DecisionOutcome.SELECTED
        reason = reason or f"Recovery action: {action}"
    else:
        outcome = DecisionOutcome.NONE
        reason = reason or "Recovery evaluated but not triggered"

    record = DecisionRecord(
        decision_type=DecisionType.RECOVERY,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.REACTIVE,
        decision_inputs={
            "evaluated": evaluated,
            "candidates_count": candidates_count,
        },
        decision_outcome=outcome,
        decision_reason=reason,
        run_id=run_id,
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=causal_role,
        details={"action": action} if action else {},
    )

    get_decision_service().emit_sync(record)
    return record


def emit_memory_decision(
    run_id: Optional[str],
    queried: bool,
    matched: bool,
    injected: bool,
    sources: Optional[list] = None,
    reason: Optional[str] = None,
    tenant_id: str = "default",
    request_id: Optional[str] = None,
    causal_role: CausalRole = CausalRole.IN_RUN,  # Memory can be pre-run or in-run
) -> DecisionRecord:
    """
    Emit a memory injection decision record.

    Called after every memory query attempt.
    Note: Memory injection can happen pre-run or in-run. Default is IN_RUN.
    """
    if not queried:
        outcome = DecisionOutcome.SKIPPED
        reason = reason or "Memory not queried (injection disabled)"
    elif not matched:
        outcome = DecisionOutcome.NONE
        reason = reason or "Memory queried but no matches"
    elif injected:
        outcome = DecisionOutcome.SELECTED
        reason = reason or f"Memory injected from {len(sources or [])} sources"
    else:
        outcome = DecisionOutcome.BLOCKED
        reason = reason or "Memory matched but injection blocked"

    record = DecisionRecord(
        decision_type=DecisionType.MEMORY,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.EXPLICIT,
        decision_inputs={
            "queried": queried,
            "matched": matched,
            "injected": injected,
        },
        decision_outcome=outcome,
        decision_reason=reason,
        run_id=run_id,
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=causal_role,
        details={"sources": sources} if sources else {},
    )

    get_decision_service().emit_sync(record)
    return record


def emit_policy_decision(
    run_id: Optional[str],
    policy_id: str,
    evaluated: bool,
    violated: bool,
    severity: str = "warning",
    reason: Optional[str] = None,
    tenant_id: str = "default",
    request_id: Optional[str] = None,
    causal_role: CausalRole = CausalRole.IN_RUN,  # Policy can be pre-run or in-run
) -> DecisionRecord:
    """
    Emit a policy enforcement decision record.

    Called after every policy check.
    Note: Policy checks can happen pre-run or in-run. Default is IN_RUN.
    """
    if not evaluated:
        outcome = DecisionOutcome.SKIPPED
    elif violated and severity == "error":
        outcome = DecisionOutcome.BLOCKED
    elif violated:
        outcome = DecisionOutcome.REJECTED
    else:
        outcome = DecisionOutcome.SELECTED

    record = DecisionRecord(
        decision_type=DecisionType.POLICY,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.EXPLICIT,
        decision_inputs={
            "policy_id": policy_id,
            "severity": severity,
        },
        decision_outcome=outcome,
        decision_reason=reason or f"Policy {policy_id}: {severity}",
        run_id=run_id,
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=causal_role,
        details={"violated": violated, "severity": severity},
    )

    get_decision_service().emit_sync(record)
    return record


def emit_budget_decision(
    run_id: Optional[str],
    budget_requested: int,
    budget_available: int,
    enforcement: str = "soft",  # hard | soft
    simulation_feasible: Optional[bool] = None,
    proceeded: bool = True,
    reason: Optional[str] = None,
    tenant_id: str = "default",
    request_id: Optional[str] = None,
    causal_role: CausalRole = CausalRole.PRE_RUN,  # Budget checks are typically pre-run
) -> DecisionRecord:
    """
    Emit a budget handling decision record.

    Called after every budget check.
    Note: Budget checks typically happen pre-run to verify resource availability.
    """
    exceeded = budget_requested > budget_available

    if enforcement == "hard" and exceeded:
        outcome = DecisionOutcome.BLOCKED
        reason = reason or f"Budget exceeded: {budget_requested} > {budget_available} (hard limit)"
    elif exceeded and not proceeded:
        outcome = DecisionOutcome.REJECTED
        reason = reason or f"Budget exceeded: {budget_requested} > {budget_available}"
    elif exceeded and proceeded:
        outcome = DecisionOutcome.SELECTED
        reason = reason or f"Budget exceeded but proceeded (advisory): {budget_requested} > {budget_available}"
    else:
        outcome = DecisionOutcome.SELECTED
        reason = reason or f"Budget within limits: {budget_requested} <= {budget_available}"

    record = DecisionRecord(
        decision_type=DecisionType.BUDGET,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.EXPLICIT,
        decision_inputs={
            "budget_requested": budget_requested,
            "budget_available": budget_available,
            "enforcement": enforcement,
        },
        decision_outcome=outcome,
        decision_reason=reason,
        run_id=run_id,
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=causal_role,
        details={
            "exceeded": exceeded,
            "simulation_feasible": simulation_feasible,
            "proceeded": proceeded,
        },
    )

    get_decision_service().emit_sync(record)
    return record


# =============================================================================
# Causal Binding: Backfill run_id for Pre-Run Decisions
# =============================================================================


def backfill_run_id_for_request(request_id: str, run_id: str) -> int:
    """
    Backfill run_id for all decisions with matching request_id.

    Called from run creation to bind pre-run decisions (routing, policy, budget)
    to the newly created run. This is context enrichment, not mutation.

    Returns the number of records updated.
    """
    if not request_id or not run_id:
        return 0

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.debug("backfill_run_id skipped: DATABASE_URL not set")
        return 0

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    UPDATE contracts.decision_records
                    SET run_id = :run_id
                    WHERE request_id = :request_id
                      AND run_id IS NULL
                      AND causal_role = 'pre_run'
                """),
                {"request_id": request_id, "run_id": run_id},
            )
            conn.commit()
            updated = result.rowcount
        engine.dispose()

        if updated > 0:
            logger.debug(
                f"backfill_run_id_completed",
                extra={
                    "request_id": request_id,
                    "run_id": run_id,
                    "records_updated": updated,
                },
            )
        return updated

    except SQLAlchemyError as e:
        logger.warning(f"Failed to backfill run_id: {e}")
        return 0
    except Exception as e:
        logger.warning(f"Unexpected error backfilling run_id: {e}")
        return 0
