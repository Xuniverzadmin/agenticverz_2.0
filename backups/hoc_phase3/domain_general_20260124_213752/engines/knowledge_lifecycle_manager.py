# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api, worker
#   Execution: sync (with async job coordination)
# Role: GAP-086 Knowledge Lifecycle Manager (THE ORCHESTRATOR) - pure business logic
# Callers: SDK facade, API endpoints, async workers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: GAP-086, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15
# NOTE: Reclassified L4→L5 (2026-01-24) - Per HOC topology, engines are L5 (business logic)

"""
GAP-086: Knowledge Lifecycle Manager

THE ORCHESTRATOR — Single service owning entire knowledge plane lifecycle.

ARCHITECTURAL PRINCIPLE:
    Lifecycle operations are governance-controlled, not user-controlled.
    SDK calls REQUEST transitions. This manager DECIDES.
    Policy + state machine ARBITRATE.
    Users never force transitions directly.

RESPONSIBILITIES:
1. Enforce state machine transitions (GAP-089)
2. Coordinate with policy gates (GAP-087)
3. Emit audit events for all transitions (GAP-088)
4. Coordinate async background jobs
5. Block illegal transitions with clear reasons

DESIGN INVARIANTS:
- MANAGER-001: All transitions go through this manager
- MANAGER-002: No transition without audit event
- MANAGER-003: Policy gates are mandatory for protected transitions
- MANAGER-004: Failed transitions leave state unchanged
- MANAGER-005: Async jobs report completion back to manager
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.models.knowledge_lifecycle import (
    KnowledgePlaneLifecycleState,
    LifecycleAction,
    TransitionResult,
    is_valid_transition,
    validate_transition,
    get_action_for_transition,
    get_transition_for_action,
    get_next_onboarding_state,
    get_next_offboarding_state,
)

logger = logging.getLogger("nova.services.knowledge_lifecycle_manager")


# =============================================================================
# Utility Functions
# =============================================================================


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def generate_id(prefix: str = "kp") -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{uuid4().hex[:12]}"


# =============================================================================
# Gate Results (GAP-087 integration)
# =============================================================================


class GateDecision(Enum):
    """Policy gate decision."""
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"  # Requires async approval


@dataclass(frozen=True)
class GateResult:
    """Result of a policy gate check."""
    decision: GateDecision
    reason: Optional[str] = None
    required_action: Optional[str] = None  # e.g., "bind_policy", "get_approval"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.decision == GateDecision.ALLOWED

    @classmethod
    def allowed(cls) -> "GateResult":
        return cls(decision=GateDecision.ALLOWED)

    @classmethod
    def blocked(cls, reason: str, required_action: Optional[str] = None) -> "GateResult":
        return cls(
            decision=GateDecision.BLOCKED,
            reason=reason,
            required_action=required_action,
        )

    @classmethod
    def pending(cls, reason: str, required_action: str) -> "GateResult":
        return cls(
            decision=GateDecision.PENDING,
            reason=reason,
            required_action=required_action,
        )


# =============================================================================
# Audit Events (GAP-088 integration)
# =============================================================================


class LifecycleAuditEventType(Enum):
    """Types of lifecycle audit events."""
    TRANSITION = "LIFECYCLE_TRANSITION"
    BLOCKED = "LIFECYCLE_BLOCKED"
    ROLLBACK = "LIFECYCLE_ROLLBACK"
    PURGE_APPROVED = "LIFECYCLE_PURGE_APPROVED"
    JOB_STARTED = "LIFECYCLE_JOB_STARTED"
    JOB_COMPLETED = "LIFECYCLE_JOB_COMPLETED"
    JOB_FAILED = "LIFECYCLE_JOB_FAILED"


@dataclass
class LifecycleAuditEvent:
    """Audit event for lifecycle transitions (GAP-088)."""
    event_id: str
    event_type: LifecycleAuditEventType
    plane_id: str
    tenant_id: str
    timestamp: datetime
    actor_id: Optional[str]
    from_state: Optional[KnowledgePlaneLifecycleState]
    to_state: Optional[KnowledgePlaneLifecycleState]
    action: Optional[str]
    gate_result: Optional[GateResult]
    reason: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "plane_id": self.plane_id,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "from_state": self.from_state.name if self.from_state else None,
            "to_state": self.to_state.name if self.to_state else None,
            "action": self.action,
            "gate_result": {
                "decision": self.gate_result.decision.value,
                "reason": self.gate_result.reason,
            } if self.gate_result else None,
            "reason": self.reason,
            "metadata": self.metadata,
        }


# =============================================================================
# Knowledge Plane Lifecycle Entity (in-memory representation)
# =============================================================================


@dataclass
class KnowledgePlaneLifecycle:
    """
    In-memory representation of a knowledge plane lifecycle.

    Renamed from KnowledgePlane to KnowledgePlaneLifecycle (2026-01-23)
    to avoid name collision with lifecycle/engines/knowledge_plane.py::KnowledgePlane
    which represents the knowledge graph abstraction.

    This class represents the LIFECYCLE state machine for knowledge planes.
    Reference: GEN-DUP-002, HOC_general_deep_audit_report.md
    """
    id: str
    tenant_id: str
    name: str
    state: KnowledgePlaneLifecycleState
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Lifecycle tracking
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    bound_policies: List[str] = field(default_factory=list)
    active_job_id: Optional[str] = None

    def record_state_change(
        self,
        from_state: KnowledgePlaneLifecycleState,
        to_state: KnowledgePlaneLifecycleState,
        actor_id: Optional[str],
        reason: Optional[str] = None,
    ) -> None:
        """Record a state change in history."""
        self.state_history.append({
            "from_state": from_state.name,
            "to_state": to_state.name,
            "timestamp": utc_now().isoformat(),
            "actor_id": actor_id,
            "reason": reason,
        })
        self.state = to_state
        self.updated_at = utc_now()


# =============================================================================
# Transition Request & Response
# =============================================================================


@dataclass
class TransitionRequest:
    """Request to transition a knowledge plane to a new state."""
    plane_id: str
    tenant_id: str
    action: str
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # For async job completion
    job_id: Optional[str] = None
    job_result: Optional[Dict[str, Any]] = None


@dataclass
class TransitionResponse:
    """Response from a transition attempt."""
    success: bool
    plane_id: str
    from_state: KnowledgePlaneLifecycleState
    to_state: Optional[KnowledgePlaneLifecycleState]
    action: str
    reason: Optional[str] = None
    audit_event_id: Optional[str] = None
    job_id: Optional[str] = None  # If async job started
    gate_result: Optional[GateResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "success": self.success,
            "plane_id": self.plane_id,
            "from_state": self.from_state.name,
            "to_state": self.to_state.name if self.to_state else None,
            "action": self.action,
            "reason": self.reason,
            "audit_event_id": self.audit_event_id,
            "job_id": self.job_id,
            "gate_blocked": self.gate_result.decision == GateDecision.BLOCKED if self.gate_result else False,
            "metadata": self.metadata,
        }


# =============================================================================
# Knowledge Lifecycle Manager (THE ORCHESTRATOR)
# =============================================================================


class KnowledgeLifecycleManager:
    """
    GAP-086: Knowledge Lifecycle Manager — THE ORCHESTRATOR.

    Single service owning entire knowledge plane lifecycle.

    Usage:
        manager = KnowledgeLifecycleManager()

        # Register a new plane
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            actor_id="user-456",
        ))

        # Check current state
        state = manager.get_state("plane-id")

        # Wait for state
        reached = manager.wait_until("plane-id", KnowledgePlaneLifecycleState.ACTIVE)
    """

    def __init__(
        self,
        policy_gate: Optional[Callable[[str, KnowledgePlaneLifecycleState, KnowledgePlaneLifecycleState], GateResult]] = None,
        audit_sink: Optional[Callable[[LifecycleAuditEvent], None]] = None,
        job_scheduler: Optional[Callable[[str, str, Dict[str, Any]], str]] = None,
    ):
        """
        Initialize the lifecycle manager.

        Args:
            policy_gate: GAP-087 policy gate function (plane_id, from_state, to_state) -> GateResult
            audit_sink: GAP-088 audit event sink function
            job_scheduler: Function to schedule async jobs (plane_id, job_type, config) -> job_id
        """
        # In-memory storage (will be replaced with DB in production)
        self._planes: Dict[str, KnowledgePlaneLifecycle] = {}
        self._audit_log: List[LifecycleAuditEvent] = []

        # Integration points
        self._policy_gate = policy_gate or self._default_policy_gate
        self._audit_sink = audit_sink or self._default_audit_sink
        self._job_scheduler = job_scheduler or self._default_job_scheduler

        logger.info("KnowledgeLifecycleManager initialized")

    # =========================================================================
    # Core Transition Handler
    # =========================================================================

    def handle_transition(self, request: TransitionRequest) -> TransitionResponse:
        """
        Handle a lifecycle transition request.

        This is the SINGLE ENTRY POINT for all state changes.
        Every transition goes through:
        1. State machine validation (GAP-089)
        2. Policy gate check (GAP-087)
        3. Audit event emission (GAP-088)
        4. State update

        Args:
            request: Transition request with action and context

        Returns:
            TransitionResponse with success/failure and details
        """
        # Special case: REGISTER creates a new plane
        if request.action == LifecycleAction.REGISTER:
            return self._handle_register(request)

        # Get current plane
        plane = self._planes.get(request.plane_id)
        if not plane:
            return TransitionResponse(
                success=False,
                plane_id=request.plane_id,
                from_state=KnowledgePlaneLifecycleState.DRAFT,  # placeholder
                to_state=None,
                action=request.action,
                reason=f"Knowledge plane not found: {request.plane_id}",
            )

        # Validate tenant ownership
        if plane.tenant_id != request.tenant_id:
            return TransitionResponse(
                success=False,
                plane_id=request.plane_id,
                from_state=plane.state,
                to_state=None,
                action=request.action,
                reason="Tenant mismatch: access denied",
            )

        # Get target state for action
        target_state = get_transition_for_action(request.action, plane.state)
        if target_state is None:
            reason = f"Action '{request.action}' not valid from state {plane.state.name}"
            self._emit_blocked_event(plane, None, request, reason)
            return TransitionResponse(
                success=False,
                plane_id=request.plane_id,
                from_state=plane.state,
                to_state=None,
                action=request.action,
                reason=reason,
            )

        # Validate transition using state machine (GAP-089)
        validation = validate_transition(plane.state, target_state)
        if not validation.allowed:
            self._emit_blocked_event(plane, target_state, request, validation.reason)
            return TransitionResponse(
                success=False,
                plane_id=request.plane_id,
                from_state=plane.state,
                to_state=target_state,
                action=request.action,
                reason=validation.reason,
            )

        # Check policy gate if required (GAP-087)
        gate_result: Optional[GateResult] = None
        if validation.requires_gate:
            gate_result = self._policy_gate(plane.id, plane.state, target_state)
            if not gate_result:
                self._emit_blocked_event(plane, target_state, request, gate_result.reason)
                return TransitionResponse(
                    success=False,
                    plane_id=request.plane_id,
                    from_state=plane.state,
                    to_state=target_state,
                    action=request.action,
                    reason=gate_result.reason,
                    gate_result=gate_result,
                )

        # Handle async jobs if required
        job_id: Optional[str] = None
        if validation.requires_async:
            job_id = self._start_async_job(plane, target_state, request)
            if job_id:
                plane.active_job_id = job_id

        # Perform the transition
        from_state = plane.state
        plane.record_state_change(from_state, target_state, request.actor_id, request.reason)

        # Emit audit event (GAP-088)
        audit_event = self._emit_transition_event(
            plane, from_state, target_state, request, gate_result
        )

        logger.info(
            f"Lifecycle transition: {plane.id} {from_state.name} → {target_state.name} "
            f"(action={request.action}, actor={request.actor_id})"
        )

        return TransitionResponse(
            success=True,
            plane_id=plane.id,
            from_state=from_state,
            to_state=target_state,
            action=request.action,
            audit_event_id=audit_event.event_id,
            job_id=job_id,
            gate_result=gate_result,
            metadata=request.metadata,
        )

    # =========================================================================
    # Registration (Special Case)
    # =========================================================================

    def _handle_register(self, request: TransitionRequest) -> TransitionResponse:
        """Handle REGISTER action - creates a new knowledge plane."""
        plane_id = request.plane_id if request.plane_id != "new" else generate_id("kp")

        if plane_id in self._planes:
            return TransitionResponse(
                success=False,
                plane_id=plane_id,
                from_state=KnowledgePlaneLifecycleState.DRAFT,
                to_state=None,
                action=request.action,
                reason=f"Knowledge plane already exists: {plane_id}",
            )

        # Create new plane in DRAFT state
        now = utc_now()
        plane = KnowledgePlaneLifecycle(
            id=plane_id,
            tenant_id=request.tenant_id,
            name=request.metadata.get("name", f"Knowledge Plane {plane_id}"),
            state=KnowledgePlaneLifecycleState.DRAFT,
            created_at=now,
            updated_at=now,
            created_by=request.actor_id,
            description=request.metadata.get("description"),
            config=request.metadata.get("config", {}),
        )

        self._planes[plane_id] = plane

        # Emit audit event
        audit_event = self._emit_transition_event(
            plane,
            None,  # No from_state for registration
            KnowledgePlaneLifecycleState.DRAFT,
            request,
            None,
        )

        logger.info(
            f"Knowledge plane registered: {plane_id} (tenant={request.tenant_id}, "
            f"actor={request.actor_id})"
        )

        return TransitionResponse(
            success=True,
            plane_id=plane_id,
            from_state=KnowledgePlaneLifecycleState.DRAFT,
            to_state=KnowledgePlaneLifecycleState.DRAFT,
            action=request.action,
            audit_event_id=audit_event.event_id,
            metadata={"created": True},
        )

    # =========================================================================
    # State Query Methods
    # =========================================================================

    def get_state(self, plane_id: str) -> Optional[KnowledgePlaneLifecycleState]:
        """Get current lifecycle state of a knowledge plane."""
        plane = self._planes.get(plane_id)
        return plane.state if plane else None

    def get_plane(self, plane_id: str) -> Optional[KnowledgePlaneLifecycle]:
        """Get knowledge plane by ID."""
        return self._planes.get(plane_id)

    def get_history(self, plane_id: str) -> List[Dict[str, Any]]:
        """Get state transition history for a knowledge plane."""
        plane = self._planes.get(plane_id)
        return plane.state_history if plane else []

    def get_audit_log(
        self,
        plane_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        event_type: Optional[LifecycleAuditEventType] = None,
    ) -> List[LifecycleAuditEvent]:
        """Get audit events with optional filtering."""
        events = self._audit_log
        if plane_id:
            events = [e for e in events if e.plane_id == plane_id]
        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events

    # =========================================================================
    # Progression Helpers
    # =========================================================================

    def get_next_action(self, plane_id: str) -> Optional[str]:
        """Get the next logical action for a knowledge plane."""
        plane = self._planes.get(plane_id)
        if not plane:
            return None

        # Check onboarding progression
        next_state = get_next_onboarding_state(plane.state)
        if next_state:
            action = get_action_for_transition(plane.state, next_state)
            if action:
                return action

        # Check offboarding progression
        next_state = get_next_offboarding_state(plane.state)
        if next_state:
            action = get_action_for_transition(plane.state, next_state)
            if action:
                return action

        return None

    def can_transition_to(
        self,
        plane_id: str,
        target_state: KnowledgePlaneLifecycleState,
    ) -> TransitionResult:
        """Check if a transition to target state is possible."""
        plane = self._planes.get(plane_id)
        if not plane:
            return TransitionResult(
                allowed=False,
                from_state=KnowledgePlaneLifecycleState.DRAFT,
                to_state=target_state,
                reason="Knowledge plane not found",
            )
        return validate_transition(plane.state, target_state)

    # =========================================================================
    # Policy Gate Integration (GAP-087)
    # =========================================================================

    def _default_policy_gate(
        self,
        plane_id: str,
        from_state: KnowledgePlaneLifecycleState,
        to_state: KnowledgePlaneLifecycleState,
    ) -> GateResult:
        """
        Default policy gate implementation (GAP-087 stub).

        In production, this will be replaced with real policy checks:
        - ACTIVATE: Requires policy binding
        - DEACTIVATE: Requires no active policy references
        - PURGE: Requires approval + retention check
        """
        plane = self._planes.get(plane_id)
        if not plane:
            return GateResult.blocked("Knowledge plane not found")

        # PENDING_ACTIVATE → ACTIVE: Require at least one policy
        if (from_state == KnowledgePlaneLifecycleState.PENDING_ACTIVATE and
                to_state == KnowledgePlaneLifecycleState.ACTIVE):
            if not plane.bound_policies:
                return GateResult.blocked(
                    "No policy bound. Cannot activate knowledge plane.",
                    required_action="bind_policy",
                )

        # ARCHIVED → PURGED: Require explicit approval
        if (from_state == KnowledgePlaneLifecycleState.ARCHIVED and
                to_state == KnowledgePlaneLifecycleState.PURGED):
            # For now, require explicit purge_approved in metadata
            if not plane.metadata.get("purge_approved"):
                return GateResult.pending(
                    "Purge requires explicit approval",
                    required_action="get_purge_approval",
                )

        return GateResult.allowed()

    def set_policy_gate(
        self,
        gate: Callable[[str, KnowledgePlaneLifecycleState, KnowledgePlaneLifecycleState], GateResult],
    ) -> None:
        """Set custom policy gate (for GAP-087 integration)."""
        self._policy_gate = gate

    # =========================================================================
    # Audit Event Emission (GAP-088)
    # =========================================================================

    def _emit_transition_event(
        self,
        plane: KnowledgePlaneLifecycle,
        from_state: Optional[KnowledgePlaneLifecycleState],
        to_state: KnowledgePlaneLifecycleState,
        request: TransitionRequest,
        gate_result: Optional[GateResult],
    ) -> LifecycleAuditEvent:
        """Emit audit event for a successful transition."""
        event = LifecycleAuditEvent(
            event_id=generate_id("evt"),
            event_type=LifecycleAuditEventType.TRANSITION,
            plane_id=plane.id,
            tenant_id=plane.tenant_id,
            timestamp=utc_now(),
            actor_id=request.actor_id,
            from_state=from_state,
            to_state=to_state,
            action=request.action,
            gate_result=gate_result,
            reason=request.reason,
            metadata=request.metadata,
        )
        self._audit_log.append(event)
        self._audit_sink(event)
        return event

    def _emit_blocked_event(
        self,
        plane: KnowledgePlaneLifecycle,
        target_state: Optional[KnowledgePlaneLifecycleState],
        request: TransitionRequest,
        reason: Optional[str],
    ) -> LifecycleAuditEvent:
        """Emit audit event for a blocked transition."""
        event = LifecycleAuditEvent(
            event_id=generate_id("evt"),
            event_type=LifecycleAuditEventType.BLOCKED,
            plane_id=plane.id,
            tenant_id=plane.tenant_id,
            timestamp=utc_now(),
            actor_id=request.actor_id,
            from_state=plane.state,
            to_state=target_state,
            action=request.action,
            gate_result=None,
            reason=reason,
            metadata=request.metadata,
        )
        self._audit_log.append(event)
        self._audit_sink(event)
        return event

    def _default_audit_sink(self, event: LifecycleAuditEvent) -> None:
        """Default audit sink - logs the event."""
        logger.info(
            f"Audit: {event.event_type.value} plane={event.plane_id} "
            f"{event.from_state.name if event.from_state else 'N/A'} → "
            f"{event.to_state.name if event.to_state else 'N/A'}"
        )

    def set_audit_sink(self, sink: Callable[[LifecycleAuditEvent], None]) -> None:
        """Set custom audit sink (for GAP-088 integration)."""
        self._audit_sink = sink

    # =========================================================================
    # Async Job Coordination
    # =========================================================================

    def _start_async_job(
        self,
        plane: KnowledgePlaneLifecycle,
        target_state: KnowledgePlaneLifecycleState,
        request: TransitionRequest,
    ) -> Optional[str]:
        """Start an async job for long-running operations."""
        job_type = self._get_job_type_for_state(target_state)
        if not job_type:
            return None

        config = {
            "plane_id": plane.id,
            "tenant_id": plane.tenant_id,
            "target_state": target_state.name,
            "actor_id": request.actor_id,
            **request.metadata,
        }

        return self._job_scheduler(plane.id, job_type, config)

    def _get_job_type_for_state(
        self,
        state: KnowledgePlaneLifecycleState,
    ) -> Optional[str]:
        """Get the async job type for a state."""
        job_types = {
            KnowledgePlaneLifecycleState.PENDING_VERIFY: "verify_connectivity",
            KnowledgePlaneLifecycleState.INGESTING: "ingest_data",
            KnowledgePlaneLifecycleState.INDEXED: "index_data",
            KnowledgePlaneLifecycleState.CLASSIFIED: "classify_data",
            KnowledgePlaneLifecycleState.ARCHIVED: "archive_data",
            KnowledgePlaneLifecycleState.PURGED: "purge_data",
        }
        return job_types.get(state)

    def _default_job_scheduler(
        self,
        plane_id: str,
        job_type: str,
        config: Dict[str, Any],
    ) -> str:
        """Default job scheduler - generates job ID without actual scheduling."""
        job_id = generate_id("job")
        logger.info(f"Job scheduled: {job_id} type={job_type} plane={plane_id}")
        return job_id

    def complete_job(
        self,
        job_id: str,
        plane_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
    ) -> TransitionResponse:
        """
        Called when an async job completes.

        This advances the state machine based on job result.
        """
        plane = self._planes.get(plane_id)
        if not plane:
            return TransitionResponse(
                success=False,
                plane_id=plane_id,
                from_state=KnowledgePlaneLifecycleState.DRAFT,
                to_state=None,
                action="job_complete",
                reason="Knowledge plane not found",
            )

        if plane.active_job_id != job_id:
            return TransitionResponse(
                success=False,
                plane_id=plane_id,
                from_state=plane.state,
                to_state=None,
                action="job_complete",
                reason=f"Job ID mismatch: expected {plane.active_job_id}, got {job_id}",
            )

        plane.active_job_id = None

        if success:
            # Advance to next state
            next_state = get_next_onboarding_state(plane.state)
            if next_state and is_valid_transition(plane.state, next_state):
                action = get_action_for_transition(plane.state, next_state) or "job_complete"
                return self.handle_transition(TransitionRequest(
                    plane_id=plane_id,
                    tenant_id=plane.tenant_id,
                    action=action,
                    metadata={"job_id": job_id, "job_result": result},
                ))

        else:
            # Job failed - emit failure event
            event = LifecycleAuditEvent(
                event_id=generate_id("evt"),
                event_type=LifecycleAuditEventType.JOB_FAILED,
                plane_id=plane.id,
                tenant_id=plane.tenant_id,
                timestamp=utc_now(),
                actor_id=None,
                from_state=plane.state,
                to_state=None,
                action="job_failed",
                gate_result=None,
                reason=result.get("error") if result else "Job failed",
                metadata={"job_id": job_id, "job_result": result},
            )
            self._audit_log.append(event)
            self._audit_sink(event)

        return TransitionResponse(
            success=success,
            plane_id=plane_id,
            from_state=plane.state,
            to_state=plane.state,
            action="job_complete",
            metadata={"job_id": job_id, "job_success": success},
        )

    # =========================================================================
    # Policy Binding (for GAP-087 integration)
    # =========================================================================

    def bind_policy(self, plane_id: str, policy_id: str) -> bool:
        """Bind a policy to a knowledge plane."""
        plane = self._planes.get(plane_id)
        if not plane:
            return False
        if policy_id not in plane.bound_policies:
            plane.bound_policies.append(policy_id)
            logger.info(f"Policy bound: {policy_id} → {plane_id}")
        return True

    def unbind_policy(self, plane_id: str, policy_id: str) -> bool:
        """Unbind a policy from a knowledge plane."""
        plane = self._planes.get(plane_id)
        if not plane:
            return False
        if policy_id in plane.bound_policies:
            plane.bound_policies.remove(policy_id)
            logger.info(f"Policy unbound: {policy_id} from {plane_id}")
        return True

    def approve_purge(self, plane_id: str, approver_id: str) -> bool:
        """Approve purge for a knowledge plane."""
        plane = self._planes.get(plane_id)
        if not plane:
            return False
        plane.metadata["purge_approved"] = True
        plane.metadata["purge_approver"] = approver_id
        plane.metadata["purge_approved_at"] = utc_now().isoformat()

        # Emit approval event
        event = LifecycleAuditEvent(
            event_id=generate_id("evt"),
            event_type=LifecycleAuditEventType.PURGE_APPROVED,
            plane_id=plane.id,
            tenant_id=plane.tenant_id,
            timestamp=utc_now(),
            actor_id=approver_id,
            from_state=plane.state,
            to_state=None,
            action="approve_purge",
            gate_result=None,
            reason="Purge approved",
            metadata={},
        )
        self._audit_log.append(event)
        self._audit_sink(event)

        logger.info(f"Purge approved: {plane_id} by {approver_id}")
        return True


# =============================================================================
# Singleton Instance
# =============================================================================

_manager_instance: Optional[KnowledgeLifecycleManager] = None


def get_knowledge_lifecycle_manager() -> KnowledgeLifecycleManager:
    """Get the singleton KnowledgeLifecycleManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = KnowledgeLifecycleManager()
    return _manager_instance


def reset_manager() -> None:
    """Reset the singleton instance (for testing)."""
    global _manager_instance
    _manager_instance = None


__all__ = [
    "KnowledgeLifecycleManager",
    "KnowledgePlaneLifecycle",
    "TransitionRequest",
    "TransitionResponse",
    "GateDecision",
    "GateResult",
    "LifecycleAuditEventType",
    "LifecycleAuditEvent",
    "get_knowledge_lifecycle_manager",
    "reset_manager",
]
