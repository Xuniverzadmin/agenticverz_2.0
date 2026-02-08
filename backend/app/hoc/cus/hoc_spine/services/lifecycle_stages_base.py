# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync/async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (base types)
#   Writes: none
# Role: Stage Handler Protocol and Base Types (pure business logic)
# Callers: KnowledgeLifecycleManager, stage handlers
# Allowed Imports: stdlib, L6
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy (runtime)
# Reference: PIN-470, GAP-071-082, GAP_IMPLEMENTATION_PLAN_V1.md
# NOTE: Reclassified L4→L5 (2026-01-24) - Per HOC topology, engines are L5 (business logic)

"""
Stage Handler Protocol and Base Types

This module defines the contract for lifecycle stage handlers.

CRITICAL DESIGN INVARIANT:
    Stage handlers are DUMB PLUGINS.
    They do NOT manage state.
    They do NOT emit events.
    They do NOT check policies.
    The orchestrator does ALL of that.

Why Dumb:
- If stages manage state, you get split-brain
- If stages emit events, you get duplicate audit
- If stages check policy, you get enforcement fragmentation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState


class StageStatus(Enum):
    """Result status from stage execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"  # For async operations
    SKIPPED = "skipped"  # Stage not needed (e.g., already done)


@dataclass
class StageContext:
    """
    Context passed to stage handlers.

    Contains all information a stage needs to execute,
    without giving it direct access to state management.
    """
    plane_id: str
    tenant_id: str
    current_state: KnowledgePlaneLifecycleState
    target_state: KnowledgePlaneLifecycleState
    actor_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Connection/credential info (for verify/ingest stages)
    connection_string: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None

    # Job tracking (for async stages)
    job_id: Optional[str] = None

    # Timestamp for audit
    timestamp: Optional[datetime] = None


@dataclass
class StageResult:
    """
    Result returned by stage handlers.

    Stage handlers return this to indicate success/failure.
    The orchestrator uses this to decide what to do next.
    """
    status: StageStatus
    message: Optional[str] = None

    # Optional data from stage execution
    data: Dict[str, Any] = field(default_factory=dict)

    # For async stages: job ID to track
    job_id: Optional[str] = None

    # For failures: error details
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # Timing
    duration_ms: Optional[int] = None

    @property
    def success(self) -> bool:
        """Check if stage succeeded."""
        return self.status == StageStatus.SUCCESS

    @property
    def is_async(self) -> bool:
        """Check if stage is async (pending completion)."""
        return self.status == StageStatus.PENDING

    @classmethod
    def ok(cls, message: Optional[str] = None, **data: Any) -> "StageResult":
        """Create a successful result."""
        return cls(
            status=StageStatus.SUCCESS,
            message=message,
            data=data,
        )

    @classmethod
    def fail(
        cls,
        message: str,
        error_code: Optional[str] = None,
        **details: Any,
    ) -> "StageResult":
        """Create a failure result."""
        return cls(
            status=StageStatus.FAILURE,
            message=message,
            error_code=error_code,
            error_details=details if details else None,
        )

    @classmethod
    def pending(cls, job_id: str, message: Optional[str] = None) -> "StageResult":
        """Create a pending (async) result."""
        return cls(
            status=StageStatus.PENDING,
            message=message,
            job_id=job_id,
        )

    @classmethod
    def skipped(cls, reason: str) -> "StageResult":
        """Create a skipped result."""
        return cls(
            status=StageStatus.SKIPPED,
            message=reason,
        )


@runtime_checkable
class StageHandler(Protocol):
    """
    Protocol for stage handlers.

    Stage handlers are dumb. The orchestrator is smart.

    Implementation Requirements:
    - Must be stateless (no instance state that affects execution)
    - Must not call KnowledgeLifecycleManager methods
    - Must not emit audit events
    - Must not check policies
    - Must only perform their specific operation
    """

    @property
    def stage_name(self) -> str:
        """Human-readable name for this stage."""
        ...

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        """States this handler can execute from."""
        ...

    async def execute(
        self,
        context: StageContext,
    ) -> StageResult:
        """
        Execute stage-specific operation.

        Args:
            context: All information needed for execution.

        Returns:
            StageResult with success/failure and optional data.

        Important:
            - Does NOT modify plane state directly
            - Does NOT emit audit events
            - Does NOT check policies
            - Returns result; orchestrator decides what happens next
        """
        ...

    async def validate(self, context: StageContext) -> Optional[str]:
        """
        Validate that stage can execute with given context.

        Returns:
            None if valid, error message if invalid.
        """
        ...


class BaseStageHandler(ABC):
    """
    Base class for stage handlers.

    Provides common implementation while enforcing the "dumb plugin" contract.
    """

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Human-readable name for this stage."""
        ...

    @property
    @abstractmethod
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        """States this handler can execute from."""
        ...

    async def validate(self, context: StageContext) -> Optional[str]:
        """
        Default validation: check that current state is in handles_states.

        Override to add stage-specific validation.
        """
        if context.current_state not in self.handles_states:
            return (
                f"Stage '{self.stage_name}' cannot execute from state "
                f"{context.current_state.name}. Expected one of: "
                f"{[s.name for s in self.handles_states]}"
            )
        return None

    @abstractmethod
    async def execute(self, context: StageContext) -> StageResult:
        """Execute stage-specific operation."""
        ...


class StageRegistry:
    """
    Registry of stage handlers.

    Maps states to their handlers for the orchestrator to use.
    """

    def __init__(self) -> None:
        self._handlers: Dict[KnowledgePlaneLifecycleState, StageHandler] = {}

    def register(self, handler: StageHandler) -> None:
        """Register a handler for its states."""
        for state in handler.handles_states:
            self._handlers[state] = handler

    def get_handler(
        self,
        state: KnowledgePlaneLifecycleState,
    ) -> Optional[StageHandler]:
        """Get handler for a state, if any."""
        return self._handlers.get(state)

    def has_handler(self, state: KnowledgePlaneLifecycleState) -> bool:
        """Check if a handler is registered for a state."""
        return state in self._handlers

    @classmethod
    def create_default(cls) -> "StageRegistry":
        """Create registry with all default handlers."""
        from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.onboarding import (
            RegisterHandler,
            VerifyHandler,
            IngestHandler,
            IndexHandler,
            ClassifyHandler,
            ActivateHandler,
            GovernHandler,
        )
        from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.offboarding import (
            DeregisterHandler,
            VerifyDeactivateHandler,
            DeactivateHandler,
            ArchiveHandler,
            PurgeHandler,
        )

        registry = cls()

        # Register onboarding handlers
        registry.register(RegisterHandler())
        registry.register(VerifyHandler())
        registry.register(IngestHandler())
        registry.register(IndexHandler())
        registry.register(ClassifyHandler())
        registry.register(ActivateHandler())
        registry.register(GovernHandler())

        # Register offboarding handlers
        registry.register(DeregisterHandler())
        registry.register(VerifyDeactivateHandler())
        registry.register(DeactivateHandler())
        registry.register(ArchiveHandler())
        registry.register(PurgeHandler())

        return registry
