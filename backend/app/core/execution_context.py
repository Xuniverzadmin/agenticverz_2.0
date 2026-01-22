# Layer: L6 — Platform Substrate
# AUDIENCE: INTERNAL
# PHASE: W0
# Product: system-wide
# Temporal:
#   Trigger: api | worker | sdk
#   Execution: sync
# Role: ExecutionContext - authoritative execution identity and causality carrier
# Callers: runner, skills, adapters, policy engine, evidence capture
# Allowed Imports: None (pure value object)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: ExecutionContext Specification v1.1

"""
ExecutionContext Specification v1.1

The ExecutionContext is the single source of truth for execution identity
and causality across the system.

Architecture (v1.1 - Structural Authority):
- ExecutionContext: Read-only execution identity (consumed by evidence writers)
- ExecutionCursor: Step advancement authority (owned only by executor)

Rules:
- Created once at intent acceptance / run creation
- Propagated everywhere (never reconstructed)
- Step advancement is structurally restricted to ExecutionCursor
- Evidence writers receive read-only context snapshots
- Evidence capture MUST fail if context is missing or invalid

Authority Model:
- Executor creates ExecutionCursor (owns step advancement)
- Executor advances steps via cursor.advance()
- Evidence writers receive ctx from cursor.context (read-only)
- No string-based caller checks - authority by construction

Canonical Law:
    ExecutionContext is the spine of execution truth.
    ExecutionCursor is the heartbeat of execution progress.
    Without them, evidence is noise.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# =========================
# Enums (Closed Sets)
# =========================


class ExecutionPhase(str, Enum):
    """Execution lifecycle phases."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    RECONNECTED = "RECONNECTED"
    TERMINAL = "TERMINAL"


class EvidenceSource(str, Enum):
    """Origin of evidence emission."""

    SDK = "sdk"
    WORKER = "worker"
    PROVIDER = "provider"
    RECONCILER = "reconciler"


# =========================
# ExecutionContext
# =========================


@dataclass(frozen=True)
class ExecutionContext:
    """
    Authoritative execution identity and causality carrier.

    Rules:
    - Created once at run creation
    - Propagated everywhere
    - Never reconstructed
    - Only step_index and execution_phase may change (via copy)

    Prohibited Patterns:
    - Deriving trace_id from run_id
    - Inferring run_id from thread state
    - Writing evidence without ExecutionContext
    - Having multiple ExecutionContexts for one run
    - Mutating is_synthetic or synthetic_scenario_id
    """

    # ---- Identity (IMMUTABLE) ----
    run_id: str
    trace_id: str

    is_synthetic: bool
    synthetic_scenario_id: Optional[str]

    source: EvidenceSource
    created_at: datetime

    # ---- Governance Context (INV-W0-001) ----
    tenant_id: Optional[str] = field(default=None)
    policy_snapshot_id: Optional[str] = field(default=None)
    budget_envelope_id: Optional[str] = field(default=None)
    actor_id: Optional[str] = field(default=None)
    actor_type: Optional[str] = field(default=None)  # human | machine | system

    # ---- Execution State (CONTROLLED MUTATION) ----
    step_index: int = field(default=0)
    execution_phase: ExecutionPhase = field(default=ExecutionPhase.CREATED)

    # =========================
    # Construction
    # =========================

    @staticmethod
    def create(
        *,
        run_id: str,
        trace_id: str,
        source: EvidenceSource,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        policy_snapshot_id: Optional[str] = None,
        budget_envelope_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
    ) -> "ExecutionContext":
        """
        Create a new ExecutionContext at intent acceptance / run creation.

        Args:
            run_id: Globally unique execution identifier
            trace_id: Root trace identifier (generated, not derived from run_id)
            source: Origin of this execution
            is_synthetic: True for SDSR/test executions
            synthetic_scenario_id: Required if is_synthetic=True
            tenant_id: Tenant identifier (INV-W0-001)
            policy_snapshot_id: Policy snapshot for this execution (INV-W0-001)
            budget_envelope_id: Budget envelope for this execution (INV-W0-001)
            actor_id: Actor who initiated this execution (INV-W0-001)
            actor_type: Type of actor: human | machine | system (INV-W0-001)

        Returns:
            New ExecutionContext instance

        Raises:
            ValueError: If required fields are missing or inconsistent
        """
        if not run_id:
            raise ValueError("ExecutionContext requires run_id")

        if not trace_id:
            raise ValueError("ExecutionContext requires trace_id")

        if is_synthetic and not synthetic_scenario_id:
            raise ValueError(
                "synthetic_scenario_id is required when is_synthetic=True"
            )

        if not is_synthetic and synthetic_scenario_id is not None:
            raise ValueError(
                "synthetic_scenario_id must be None when is_synthetic=False"
            )

        return ExecutionContext(
            run_id=run_id,
            trace_id=trace_id,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
            source=source,
            created_at=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            policy_snapshot_id=policy_snapshot_id,
            budget_envelope_id=budget_envelope_id,
            actor_id=actor_id,
            actor_type=actor_type,
            step_index=0,
            execution_phase=ExecutionPhase.CREATED,
        )

    # =========================
    # Controlled Transitions
    # =========================

    def _advance_step(self) -> "ExecutionContext":
        """
        INTERNAL: Advance to the next execution step.

        This method is intentionally private (underscore prefix).
        Direct calls from outside ExecutionCursor are architectural violations.

        Use ExecutionCursor.advance() instead.
        """
        return replace(self, step_index=self.step_index + 1)

    def next_step(self, *, _caller: str = "executor") -> "ExecutionContext":
        """
        DEPRECATED: Use ExecutionCursor.advance() instead.

        This method exists for backward compatibility during migration.
        New code MUST use ExecutionCursor pattern.

        Authority is now structural via ExecutionCursor, not string-based.
        """
        import logging
        import warnings

        logger = logging.getLogger("nova.core.execution_context")

        # Emit deprecation warning
        warnings.warn(
            "ExecutionContext.next_step() is deprecated. "
            "Use ExecutionCursor.advance() for structural authority.",
            DeprecationWarning,
            stacklevel=2,
        )

        if _caller != "executor":
            logger.warning(
                "AUTHORITY_VIOLATION: next_step() called from non-executor",
                extra={
                    "caller": _caller,
                    "run_id": self.run_id,
                    "step_index": self.step_index,
                },
            )

        return self._advance_step()

    def with_phase(self, phase: ExecutionPhase) -> "ExecutionContext":
        """
        Transition execution phase.

        Args:
            phase: Target execution phase

        Returns:
            New ExecutionContext with updated phase (or same if unchanged)
        """
        if phase == self.execution_phase:
            return self

        return replace(self, execution_phase=phase)

    # =========================
    # Validation Guards
    # =========================

    def assert_valid_for_evidence(self) -> None:
        """
        Guardrail for evidence capture.
        Must be called by evidence writers before writing.

        Raises:
            RuntimeError: If context is invalid for evidence capture
        """
        if not self.run_id:
            raise RuntimeError("Evidence capture attempted without run_id")

        if not self.trace_id:
            raise RuntimeError("Evidence capture attempted without trace_id")

        if self.is_synthetic and not self.synthetic_scenario_id:
            raise RuntimeError(
                "Synthetic execution missing synthetic_scenario_id"
            )

    def assert_terminal(self) -> None:
        """
        Guardrail for integrity computation.
        Must be called before computing integrity evidence.

        Raises:
            RuntimeError: If not in terminal state
        """
        if self.execution_phase != ExecutionPhase.TERMINAL:
            raise RuntimeError(
                f"Integrity computation attempted before terminal state "
                f"(current phase: {self.execution_phase})"
            )

    # =========================
    # Utility
    # =========================

    def to_dict(self) -> dict:
        """
        Export context as dictionary for logging/debugging.
        """
        return {
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "step_index": self.step_index,
            "execution_phase": self.execution_phase.value,
            "is_synthetic": self.is_synthetic,
            "synthetic_scenario_id": self.synthetic_scenario_id,
            "source": self.source.value,
            "created_at": self.created_at.isoformat(),
            "tenant_id": self.tenant_id,
            "policy_snapshot_id": self.policy_snapshot_id,
            "budget_envelope_id": self.budget_envelope_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
        }

    def to_audit_dict(self) -> dict:
        """
        Extract audit-relevant fields for compliance logging (INV-W0-001).

        Returns minimal set needed for audit trail provenance.
        """
        return {
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "step_index": self.step_index,
            "trace_id": self.trace_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "policy_snapshot_id": self.policy_snapshot_id,
        }

    def with_governance(
        self,
        *,
        tenant_id: Optional[str] = None,
        policy_snapshot_id: Optional[str] = None,
        budget_envelope_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
    ) -> "ExecutionContext":
        """
        Create copy with governance context (INV-W0-001).

        Use this to add governance metadata to an existing context.
        """
        return replace(
            self,
            tenant_id=tenant_id if tenant_id is not None else self.tenant_id,
            policy_snapshot_id=policy_snapshot_id if policy_snapshot_id is not None else self.policy_snapshot_id,
            budget_envelope_id=budget_envelope_id if budget_envelope_id is not None else self.budget_envelope_id,
            actor_id=actor_id if actor_id is not None else self.actor_id,
            actor_type=actor_type if actor_type is not None else self.actor_type,
        )


# =============================================================================
# ExecutionCursor - Structural Step Authority (v1.1)
# =============================================================================


class ExecutionCursor:
    """
    Structural authority for step advancement.

    The ExecutionCursor owns step progression and provides read-only
    context snapshots to evidence writers.

    Authority Model:
    - Only the executor creates and holds an ExecutionCursor
    - cursor.advance() is the ONLY way to progress steps
    - cursor.context returns read-only snapshot for evidence
    - Evidence writers cannot advance steps (no access to cursor)

    Usage:
        # Executor creates cursor
        cursor = ExecutionCursor.create(run_id, trace_id, source, ...)

        # Executor advances step BEFORE skill execution
        cursor.advance()

        # Pass read-only context to evidence capture
        capture_activity_evidence(cursor.context, ...)

        # Evidence writers CANNOT advance (they only have context)

    This design makes authority violations structurally impossible,
    not just conventionally discouraged.
    """

    __slots__ = ("_context",)

    def __init__(self, context: ExecutionContext):
        """
        INTERNAL: Use ExecutionCursor.create() instead.
        """
        self._context = context

    @staticmethod
    def create(
        *,
        run_id: str,
        trace_id: str,
        source: EvidenceSource,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        policy_snapshot_id: Optional[str] = None,
        budget_envelope_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
    ) -> "ExecutionCursor":
        """
        Create a new ExecutionCursor for an execution.

        This is the ONLY way to create step-advancement authority.
        Should be called once per run, by the executor only.

        Args:
            run_id: Globally unique execution identifier
            trace_id: Root trace identifier
            source: Origin of this execution
            is_synthetic: True for SDSR/test executions
            synthetic_scenario_id: Required if is_synthetic=True
            tenant_id: Tenant identifier (INV-W0-001)
            policy_snapshot_id: Policy snapshot for governance (INV-W0-001)
            budget_envelope_id: Budget envelope for this execution (INV-W0-001)
            actor_id: Actor who initiated this execution (INV-W0-001)
            actor_type: Type of actor: human | machine | system (INV-W0-001)

        Returns:
            New ExecutionCursor with authority over step advancement
        """
        ctx = ExecutionContext.create(
            run_id=run_id,
            trace_id=trace_id,
            source=source,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
            tenant_id=tenant_id,
            policy_snapshot_id=policy_snapshot_id,
            budget_envelope_id=budget_envelope_id,
            actor_id=actor_id,
            actor_type=actor_type,
        )
        return ExecutionCursor(ctx)

    @staticmethod
    def from_context(context: ExecutionContext) -> "ExecutionCursor":
        """
        Create cursor from existing context.

        Use this when you need to wrap an existing context
        (e.g., during migration from old pattern).

        Args:
            context: Existing ExecutionContext

        Returns:
            ExecutionCursor wrapping the context
        """
        return ExecutionCursor(context)

    @property
    def context(self) -> ExecutionContext:
        """
        Get read-only execution context snapshot.

        This is what you pass to evidence capture functions.
        The returned context cannot advance steps (no cursor access).

        Returns:
            Current ExecutionContext (read-only snapshot)
        """
        return self._context

    @property
    def run_id(self) -> str:
        """Shortcut to context.run_id"""
        return self._context.run_id

    @property
    def step_index(self) -> int:
        """Shortcut to context.step_index"""
        return self._context.step_index

    def advance(self) -> ExecutionContext:
        """
        Advance to the next execution step.

        This is the ONLY sanctioned way to increment step_index.
        Only the executor should call this (they own the cursor).

        Returns:
            New ExecutionContext with incremented step_index
        """
        self._context = self._context._advance_step()
        return self._context

    def with_phase(self, phase: ExecutionPhase) -> ExecutionContext:
        """
        Transition execution phase.

        Args:
            phase: Target execution phase

        Returns:
            New ExecutionContext with updated phase
        """
        self._context = self._context.with_phase(phase)
        return self._context

    def to_dict(self) -> dict:
        """Export cursor state as dictionary."""
        return self._context.to_dict()
