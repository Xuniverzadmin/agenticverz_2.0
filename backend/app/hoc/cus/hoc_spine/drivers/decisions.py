# capability_id: CAP-012
# Layer: L4 — HOC Spine (Driver)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: decision_records (SQL)
# Database:
#   Scope: hoc_spine
#   Models: decision_records (via raw SQL)
# Role: Decision contract enforcement — pure driver (no transaction ownership)
# Callers: L4 handlers, L5 engines (via app.contracts.decisions bridge)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Contract System
# Transaction: Driver NEVER commits/rollbacks — L4 caller owns transaction boundaries.

"""Phase 4B: Decision Record Models and Service

Implements DECISION_RECORD_CONTRACT v0.2.

Contract-mandated fields:
- decision_source: human | system | hybrid
- decision_trigger: explicit | autonomous | reactive

Rule: Emit records where decisions already happen. No logic changes.

Transaction ownership: All functions accept a connection parameter.
The caller (L4 handler) owns the connection lifecycle and commits.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from sqlalchemy import text
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
    BUDGET_ENFORCEMENT = "budget_enforcement"  # Phase 5A: Hard budget halted execution
    POLICY_PRE_CHECK = "policy_pre_check"  # Phase 5B: Pre-execution policy check
    RECOVERY_EVALUATION = "recovery_evaluation"  # Phase 5C: Post-failure recovery evaluation
    CARE_ROUTING_OPTIMIZED = "care_routing_optimized"  # Phase 5D: Optimization changed routing


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

    SELECTED = "selected"  # Positive selection made
    REJECTED = "rejected"  # All options rejected
    SKIPPED = "skipped"  # Decision point bypassed
    BLOCKED = "blocked"  # Decision blocked by constraint
    NONE = "none"  # No decision needed
    EXECUTION_HALTED = "execution_halted"  # Phase 5A: Hard budget halted execution
    POLICY_BLOCKED = "policy_blocked"  # Phase 5B: Pre-check failed (strict mode)
    POLICY_UNAVAILABLE = "policy_unavailable"  # Phase 5B: Policy service down (strict mode)
    # NOTE: No POLICY_ALLOWED - success is not a decision, it's the default path
    # Phase 5C: Recovery outcomes
    RECOVERY_APPLIED = "recovery_applied"  # R1: Safe auto-recovery executed
    RECOVERY_SUGGESTED = "recovery_suggested"  # R2: Risky, human approval needed
    RECOVERY_SKIPPED = "recovery_skipped"  # R3: Forbidden or not applicable
    # Phase 5D: CARE optimization outcomes
    BASELINE_SELECTED = "baseline_selected"  # Optimization agreed with baseline
    OPTIMIZED_SELECTED = "optimized_selected"  # Optimization changed selection


class CausalRole(str, Enum):
    """When in the lifecycle this decision occurred."""

    PRE_RUN = "pre_run"  # Before run exists (routing, policy pre-check)
    IN_RUN = "in_run"  # During run execution
    POST_RUN = "post_run"  # After run completion (reconciliation)


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
# Decision Record Service (Append-Only Sink) — Pure Driver
# =============================================================================


class DecisionRecordService:
    """
    Append-only sink for decision records.

    Emits to contracts.decision_records table.
    Non-blocking - failures are logged but don't affect callers.

    Evidence Architecture v1.0: Also bridges to governance.policy_decisions for taxonomy evidence.

    Transaction ownership: All methods accept a connection parameter.
    The service NEVER creates engines, connections, or commits.
    L4 caller owns the transaction lifecycle.
    """

    def __init__(self) -> None:
        self._enabled = os.environ.get("DATABASE_URL") is not None

    def _bridge_to_taxonomy(self, connection: Any, record: DecisionRecord) -> None:
        """
        Evidence Architecture v1.0: Bridge decision to governance taxonomy.

        Mirrors operational decisions to governance.policy_decisions table for
        cross-domain evidence correlation. This is the D (Decision) evidence bridge.

        Note: This is best-effort and non-blocking.
        """
        # Only bridge policy-related decisions
        policy_types = {
            DecisionType.POLICY,
            DecisionType.POLICY_PRE_CHECK,
            DecisionType.BUDGET,
            DecisionType.BUDGET_ENFORCEMENT,
        }

        if record.decision_type not in policy_types:
            return

        try:
            # Map operational decision to taxonomy format
            policy_type = record.decision_type.value
            decision = "allowed" if record.decision_outcome in {
                DecisionOutcome.SELECTED,
                DecisionOutcome.NONE,
            } else "denied"

            connection.execute(
                text(
                    """
                    INSERT INTO governance.policy_decisions (
                        id, run_id, policy_type, decision, rationale,
                        is_synthetic, synthetic_scenario_id, capture_confidence_score, created_at
                    ) VALUES (
                        :id, :run_id, :policy_type, :decision, :rationale,
                        :is_synthetic, :synthetic_scenario_id, :capture_confidence_score, :created_at
                    ) ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": record.decision_id,
                    "run_id": record.run_id,
                    "policy_type": policy_type,
                    "decision": decision,
                    "rationale": record.decision_reason or "",
                    "is_synthetic": False,  # Operational decisions are never synthetic
                    "synthetic_scenario_id": None,
                    "capture_confidence_score": 1.0,
                    "created_at": record.decided_at,
                },
            )
            logger.debug(
                "decision_bridged_to_taxonomy",
                extra={"decision_id": record.decision_id, "policy_type": policy_type},
            )
        except Exception as e:
            # Non-blocking - log and continue
            logger.debug(
                "taxonomy_bridge_failed",
                extra={"decision_id": record.decision_id, "error": str(e)},
            )

    def emit(self, connection: Any, record: DecisionRecord) -> bool:
        """
        Emit a decision record to the sink.

        Returns True if emission succeeded, False otherwise.
        Non-blocking - failures don't propagate.

        Args:
            connection: SQLAlchemy Connection (caller owns lifecycle and commit)
            record: DecisionRecord to emit
        """
        if not self._enabled:
            logger.debug(f"Decision record emission disabled: {record.decision_id}")
            return False

        try:
            connection.execute(
                text(
                    """
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
                """
                ),
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

            logger.debug(
                "decision_record_emitted",
                extra={
                    "decision_id": record.decision_id,
                    "decision_type": record.decision_type.value,
                    "decision_outcome": record.decision_outcome.value,
                    "causal_role": record.causal_role.value,
                },
            )

            # Evidence Architecture v1.0: Bridge to governance taxonomy
            self._bridge_to_taxonomy(connection, record)

            return True

        except SQLAlchemyError as e:
            logger.warning(f"Failed to emit decision record: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error emitting decision record: {e}")
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
#
# These are pure driver functions — they accept a connection, build a record,
# emit via the service, and return the record. They NEVER commit.
# The caller (L4 handler) owns the transaction lifecycle.
# =============================================================================


def emit_routing_decision(
    connection: Any,
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
            DecisionOutcome.SELECTED
            if routed and selected_agent
            else DecisionOutcome.REJECTED
            if not routed and rejection_reason
            else DecisionOutcome.NONE
        ),
        decision_reason=rejection_reason if not routed else f"Selected {selected_agent}",
        run_id=run_id,
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=causal_role,
        details=details or {},
    )

    get_decision_service().emit(connection, record)
    return record


def emit_recovery_decision(
    connection: Any,
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

    get_decision_service().emit(connection, record)
    return record


def emit_memory_decision(
    connection: Any,
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

    get_decision_service().emit(connection, record)
    return record


def emit_policy_decision(
    connection: Any,
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

    get_decision_service().emit(connection, record)
    return record


def emit_budget_decision(
    connection: Any,
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

    get_decision_service().emit(connection, record)
    return record


def _check_budget_enforcement_exists(connection: Any, run_id: str) -> bool:
    """
    Check if a budget_enforcement decision already exists for this run.

    Idempotency guard: prevents double emission on retry/restart.
    """
    svc = get_decision_service()
    if not svc._enabled:
        return False  # Can't check, allow emission

    try:
        result = connection.execute(
            text(
                """
                SELECT 1 FROM contracts.decision_records
                WHERE run_id = :run_id
                  AND decision_type = :decision_type
                LIMIT 1
            """
            ),
            {
                "run_id": run_id,
                "decision_type": DecisionType.BUDGET_ENFORCEMENT.value,
            },
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.warning(f"Failed to check budget_enforcement existence: {e}")
        return False  # On error, allow emission (fail-open for observability)


def emit_budget_enforcement_decision(
    connection: Any,
    run_id: str,
    budget_limit_cents: int,
    budget_consumed_cents: int,
    step_cost_cents: int,
    completed_steps: int,
    total_steps: int,
    tenant_id: str = "default",
) -> Optional[DecisionRecord]:
    """
    Emit a budget enforcement decision record when hard limit halts execution.

    Phase 5A: This is the ONLY decision type for hard budget halts.
    Called immediately when execution is halted due to hard budget limit.

    IDEMPOTENT: If already emitted for this run_id, returns None.

    Contract alignment:
    - decision_type: budget_enforcement
    - decision_source: system
    - decision_trigger: reactive
    - decision_outcome: execution_halted
    """
    # Idempotency guard: check if already emitted for this run
    if _check_budget_enforcement_exists(connection, run_id):
        logger.debug(
            "budget_enforcement_already_emitted",
            extra={"run_id": run_id},
        )
        return None

    record = DecisionRecord(
        decision_type=DecisionType.BUDGET_ENFORCEMENT,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.REACTIVE,
        decision_inputs={
            "budget_limit_cents": budget_limit_cents,
            "budget_consumed_cents": budget_consumed_cents,
            "step_cost_cents": step_cost_cents,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
        },
        decision_outcome=DecisionOutcome.EXECUTION_HALTED,
        decision_reason=f"Hard budget limit reached: {budget_consumed_cents}c consumed >= {budget_limit_cents}c limit",
        run_id=run_id,
        tenant_id=tenant_id,
        causal_role=CausalRole.IN_RUN,
        details={
            "enforcement_mode": "hard",
            "halt_point": f"after_step_{completed_steps}",
            "remaining_steps": total_steps - completed_steps,
        },
    )

    get_decision_service().emit(connection, record)
    return record


# =============================================================================
# Phase 5B: Policy Pre-Check Decision Emission
# =============================================================================


def _check_policy_precheck_exists(connection: Any, request_id: str, outcome: str) -> bool:
    """
    Check if a policy_pre_check decision already exists for this request+outcome.

    Idempotency guard: prevents double emission on retry/restart.
    """
    svc = get_decision_service()
    if not svc._enabled:
        return False  # Can't check, allow emission

    try:
        result = connection.execute(
            text(
                """
                SELECT 1 FROM contracts.decision_records
                WHERE request_id = :request_id
                  AND decision_type = :decision_type
                  AND decision_outcome = :outcome
                LIMIT 1
            """
            ),
            {
                "request_id": request_id,
                "decision_type": DecisionType.POLICY_PRE_CHECK.value,
                "outcome": outcome,
            },
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.warning(f"Failed to check policy_pre_check existence: {e}")
        return False  # On error, allow emission (fail-open for observability)


def emit_policy_precheck_decision(
    connection: Any,
    request_id: str,
    posture: str,
    passed: bool,
    service_available: bool,
    violations: Optional[list] = None,
    tenant_id: str = "default",
) -> Optional[DecisionRecord]:
    """
    Emit a policy pre-check decision record.

    Phase 5B: Pre-execution policy check.

    EMISSION RULE (FROZEN):
      - EMIT IFF (posture == strict AND (failed OR unavailable))
      - DO NOT EMIT if passed or posture == advisory

    Contract alignment:
    - decision_type: policy_pre_check
    - decision_source: system
    - decision_trigger: explicit (pre-check is proactive)
    - causal_role: pre_run (always - run doesn't exist yet)
    - run_id: None (run not created on block)

    IDEMPOTENT: If already emitted for this request_id+outcome, returns None.
    """
    # Rule: Advisory mode NEVER emits decisions
    if posture != "strict":
        logger.debug(
            "policy_precheck_no_emit_advisory",
            extra={"request_id": request_id, "posture": posture},
        )
        return None

    # Rule: Success does NOT emit decisions
    if passed and service_available:
        logger.debug(
            "policy_precheck_no_emit_success",
            extra={"request_id": request_id},
        )
        return None

    # Determine outcome
    if not service_available:
        outcome = DecisionOutcome.POLICY_UNAVAILABLE
        reason = "Policy service unavailable (strict mode blocks execution)"
    else:
        outcome = DecisionOutcome.POLICY_BLOCKED
        reason = f"Policy pre-check failed: {', '.join(violations or ['Unknown violation'])}"

    # Idempotency guard
    if _check_policy_precheck_exists(connection, request_id, outcome.value):
        logger.debug(
            "policy_precheck_already_emitted",
            extra={"request_id": request_id, "outcome": outcome.value},
        )
        return None

    record = DecisionRecord(
        decision_type=DecisionType.POLICY_PRE_CHECK,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.EXPLICIT,  # Pre-check is proactive, not reactive
        decision_inputs={
            "posture": posture,
            "violations": violations or [],
            "service_available": service_available,
        },
        decision_outcome=outcome,
        decision_reason=reason,
        run_id=None,  # Run not created on block
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=CausalRole.PRE_RUN,  # Always pre-run
        details={
            "posture": posture,
            "blocked": True,
            "passed": passed,
            "service_available": service_available,
        },
    )

    get_decision_service().emit(connection, record)

    logger.info(
        "policy_precheck_decision_emitted",
        extra={
            "request_id": request_id,
            "decision_id": record.decision_id,
            "outcome": outcome.value,
            "posture": posture,
        },
    )

    return record


# =============================================================================
# Phase 5C: Recovery Evaluation Decision Emission
# =============================================================================


def _check_recovery_evaluation_exists(connection: Any, run_id: str, failure_type: str) -> bool:
    """
    Check if a recovery_evaluation decision already exists for this run+failure.

    Idempotency guard: prevents double emission on retry/restart.
    """
    svc = get_decision_service()
    if not svc._enabled:
        return False  # Can't check, allow emission

    try:
        result = connection.execute(
            text(
                """
                SELECT 1 FROM contracts.decision_records
                WHERE run_id = :run_id
                  AND decision_type = :decision_type
                  AND decision_inputs::text LIKE :failure_pattern
                LIMIT 1
            """
            ),
            {
                "run_id": run_id,
                "decision_type": DecisionType.RECOVERY_EVALUATION.value,
                "failure_pattern": f'%"failure_type": "{failure_type}"%',
            },
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.warning(f"Failed to check recovery_evaluation existence: {e}")
        return False  # On error, allow emission (fail-open for observability)


def emit_recovery_evaluation_decision(
    connection: Any,
    run_id: str,
    request_id: str,
    recovery_class: str,  # R1, R2, R3
    recovery_action: Optional[str],
    failure_type: str,
    failure_context: Optional[Dict[str, Any]] = None,
    tenant_id: str = "default",
) -> Optional[DecisionRecord]:
    """
    Emit a recovery evaluation decision record.

    Phase 5C: Post-failure recovery evaluation.

    EMISSION RULE (FROZEN per PIN-174):
      - ALWAYS emit exactly one RECOVERY_EVALUATION decision after any:
        - execution_halted
        - execution_failed

      Outcome mapping:
        - R1 and applied → recovery_applied
        - R2 and suggested → recovery_suggested
        - R3 or no applicable recovery → recovery_skipped

    Contract alignment:
    - decision_type: recovery_evaluation
    - decision_source: system
    - decision_trigger: reactive (recovery is always reactive to failure)
    - causal_role: post_run (always - recovery evaluates after failure)

    IDEMPOTENT: If already emitted for this run_id+failure_type, returns None.
    """
    # Idempotency guard
    if _check_recovery_evaluation_exists(connection, run_id, failure_type):
        logger.debug(
            "recovery_evaluation_already_emitted",
            extra={"run_id": run_id, "failure_type": failure_type},
        )
        return None

    # Map recovery_class to outcome
    if recovery_class == "R1":
        outcome = DecisionOutcome.RECOVERY_APPLIED
        reason = f"R1: Auto-recovery applied - {recovery_action}"
    elif recovery_class == "R2":
        outcome = DecisionOutcome.RECOVERY_SUGGESTED
        reason = f"R2: Recovery suggested (requires approval) - {recovery_action}"
    else:  # R3 or unknown
        outcome = DecisionOutcome.RECOVERY_SKIPPED
        reason = f"R3: Recovery skipped - {failure_type}"

    record = DecisionRecord(
        decision_type=DecisionType.RECOVERY_EVALUATION,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.REACTIVE,  # Recovery is always reactive
        decision_inputs={
            "recovery_class": recovery_class,
            "recovery_action": recovery_action,
            "failure_type": failure_type,
        },
        decision_outcome=outcome,
        decision_reason=reason,
        run_id=run_id,
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=CausalRole.POST_RUN,  # Always post-failure
        details={
            "failure_context": failure_context or {},
            "recovery_bounded": recovery_class == "R1",
            "requires_approval": recovery_class == "R2",
        },
    )

    get_decision_service().emit(connection, record)

    logger.info(
        "recovery_evaluation_decision_emitted",
        extra={
            "run_id": run_id,
            "decision_id": record.decision_id,
            "outcome": outcome.value,
            "recovery_class": recovery_class,
        },
    )

    return record


# =============================================================================
# Causal Binding: Backfill run_id for Pre-Run Decisions
# =============================================================================


def backfill_run_id_for_request(connection: Any, request_id: str, run_id: str) -> int:
    """
    Backfill run_id for all decisions with matching request_id.

    Called from run creation to bind pre-run decisions (routing, policy, budget)
    to the newly created run. This is context enrichment, not mutation.

    Returns the number of records updated.
    """
    if not request_id or not run_id:
        return 0

    svc = get_decision_service()
    if not svc._enabled:
        logger.debug("backfill_run_id skipped: DATABASE_URL not set")
        return 0

    try:
        result = connection.execute(
            text(
                """
                UPDATE contracts.decision_records
                SET run_id = :run_id
                WHERE request_id = :request_id
                  AND run_id IS NULL
                  AND causal_role = 'pre_run'
            """
            ),
            {"request_id": request_id, "run_id": run_id},
        )
        updated = result.rowcount

        if updated > 0:
            logger.debug(
                "backfill_run_id_completed",
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


# =============================================================================
# Phase 5D: CARE Optimization - Signal Isolation & Decision Emission
# =============================================================================

# Allowed signals (PIN-176 frozen list)
CARE_ALLOWED_SIGNALS = frozenset(
    [
        "latency_p50",
        "latency_p95",
        "cost_per_run",
        "success_rate",  # Binary execution success only
        "recovery_occurred",  # Boolean only
        "agent_availability",
        "context_size_bucket",
    ]
)

# Forbidden signals (PIN-176 frozen list)
CARE_FORBIDDEN_SIGNALS = frozenset(
    [
        "policy_outcome",
        "budget_halt_reason",
        "recovery_class",
        "customer_content",
        "safety_events",
        "founder_overrides",
        "failure_details",
        "user_feedback",
    ]
)

# Kill-switch state (runtime toggle)
_care_optimization_kill_switch = False

# Confidence threshold for optimization selection
CARE_CONFIDENCE_THRESHOLD = 0.50


class CARESignalAccessError(Exception):
    """Raised when attempting to access a forbidden CARE signal."""

    pass


def check_signal_access(signal_name: str) -> bool:
    """
    Check if a signal is allowed for CARE optimization.

    Phase 5D: Hard guard on signal access.

    Raises:
        CARESignalAccessError: If signal is forbidden

    Returns:
        True if signal is allowed
    """
    if signal_name in CARE_FORBIDDEN_SIGNALS:
        raise CARESignalAccessError(f"Forbidden signal access: '{signal_name}' is not allowed for CARE optimization")

    if signal_name not in CARE_ALLOWED_SIGNALS:
        raise CARESignalAccessError(f"Unknown signal: '{signal_name}' is not in the allowed signal list")

    return True


def activate_care_kill_switch() -> bool:
    """
    Activate the CARE optimization kill-switch.

    When activated:
    - Forces baseline selection
    - Prevents decision emission
    - Takes effect within 1 request cycle

    Returns:
        True on successful activation
    """
    global _care_optimization_kill_switch
    _care_optimization_kill_switch = True
    logger.warning("care_kill_switch_activated")
    return True


def deactivate_care_kill_switch() -> bool:
    """
    Deactivate the CARE optimization kill-switch.

    Returns:
        True on successful deactivation
    """
    global _care_optimization_kill_switch
    _care_optimization_kill_switch = False
    logger.info("care_kill_switch_deactivated")
    return True


def is_care_kill_switch_active() -> bool:
    """Check if CARE kill-switch is currently active."""
    return _care_optimization_kill_switch


def _check_care_optimization_exists(connection: Any, request_id: str) -> bool:
    """
    Check if a care_routing_optimized decision already exists for this request.

    Idempotency guard: prevents double emission.
    """
    svc = get_decision_service()
    if not svc._enabled:
        return False

    try:
        result = connection.execute(
            text(
                """
                SELECT 1 FROM contracts.decision_records
                WHERE request_id = :request_id
                  AND decision_type = :decision_type
                LIMIT 1
            """
            ),
            {
                "request_id": request_id,
                "decision_type": DecisionType.CARE_ROUTING_OPTIMIZED.value,
            },
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.warning(f"Failed to check care_routing_optimized existence: {e}")
        return False


def emit_care_optimization_decision(
    connection: Any,
    request_id: str,
    baseline_agent: str,
    optimized_agent: str,
    confidence_score: float,
    signals_used: list,
    optimization_enabled: bool = True,
    shadow_mode: bool = False,
    tenant_id: str = "default",
) -> Optional[DecisionRecord]:
    """
    Emit a CARE routing optimization decision record.

    Phase 5D: Optimization-driven routing decision.

    EMISSION RULE (FROZEN per PIN-176):
      - EMIT CARE_ROUTING_OPTIMIZED decision IF AND ONLY IF:
        - optimization_enabled = true
        - AND NOT shadow_mode
        - AND optimized_agent != baseline_agent

      - DO NOT EMIT if:
        - optimization_disabled
        - shadow_mode (log only, no decision record)
        - baseline == optimized (silence allowed)
        - kill_switch active

    Contract alignment:
    - decision_type: care_routing_optimized
    - decision_source: system
    - decision_trigger: autonomous (learning-driven)
    - causal_role: pre_run (always - before run exists)

    IDEMPOTENT: If already emitted for this request_id, returns None.
    """
    # Kill-switch check - forces baseline, no emission
    if is_care_kill_switch_active():
        logger.debug(
            "care_optimization_kill_switch_active",
            extra={"request_id": request_id},
        )
        return None

    # Optimization disabled - no emission
    if not optimization_enabled:
        logger.debug(
            "care_optimization_disabled",
            extra={"request_id": request_id},
        )
        return None

    # Shadow mode - log only, no decision record
    if shadow_mode:
        logger.info(
            "care_optimization_shadow_comparison",
            extra={
                "request_id": request_id,
                "baseline_agent": baseline_agent,
                "optimized_agent": optimized_agent,
                "diverged": baseline_agent != optimized_agent,
                "confidence_score": confidence_score,
            },
        )
        return None

    # Low confidence - use baseline (conservative)
    if confidence_score < CARE_CONFIDENCE_THRESHOLD:
        logger.debug(
            "care_optimization_low_confidence",
            extra={
                "request_id": request_id,
                "confidence_score": confidence_score,
                "threshold": CARE_CONFIDENCE_THRESHOLD,
            },
        )
        return None

    # No divergence - silence is correct
    if baseline_agent == optimized_agent:
        logger.debug(
            "care_optimization_no_divergence",
            extra={"request_id": request_id, "agent": baseline_agent},
        )
        return None

    # Idempotency guard
    if _check_care_optimization_exists(connection, request_id):
        logger.debug(
            "care_optimization_already_emitted",
            extra={"request_id": request_id},
        )
        return None

    # Validate signals used are all allowed
    for signal in signals_used:
        check_signal_access(signal)  # Raises on forbidden

    record = DecisionRecord(
        decision_type=DecisionType.CARE_ROUTING_OPTIMIZED,
        decision_source=DecisionSource.SYSTEM,
        decision_trigger=DecisionTrigger.AUTONOMOUS,  # Learning-driven
        decision_inputs={
            "baseline_agent": baseline_agent,
            "optimized_agent": optimized_agent,
            "confidence_score": confidence_score,
            "signals_used": signals_used,
        },
        decision_outcome=DecisionOutcome.OPTIMIZED_SELECTED,
        decision_reason=f"Optimization selected {optimized_agent} over baseline {baseline_agent}",
        run_id=None,  # Pre-run decision
        tenant_id=tenant_id,
        request_id=request_id,
        causal_role=CausalRole.PRE_RUN,  # Always pre-run
        details={
            "baseline_agent": baseline_agent,
            "optimized_agent": optimized_agent,
            "confidence_score": confidence_score,
            "signals_used": signals_used,
        },
    )

    get_decision_service().emit(connection, record)

    logger.info(
        "care_optimization_decision_emitted",
        extra={
            "request_id": request_id,
            "decision_id": record.decision_id,
            "baseline_agent": baseline_agent,
            "optimized_agent": optimized_agent,
            "confidence_score": confidence_score,
        },
    )

    return record
