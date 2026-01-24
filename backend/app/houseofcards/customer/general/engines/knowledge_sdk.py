# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api, sdk
#   Execution: sync (with async wait support)
# Role: GAP-083-085 Knowledge SDK Façade (thin wrapper over KnowledgeLifecycleManager)
# Callers: External SDK consumers, API endpoints
# Allowed Imports: L5, L6, L7 (via manager)
# Forbidden Imports: L1, L2, L3, L4
# Reference: GAP-083-085, GAP_IMPLEMENTATION_PLAN_V1.md Section 7.18
#
# NOTE: This is a thin domain-level SDK facade.
# It contains dataclass schemas and delegates all decisions to KnowledgeLifecycleManager.
# Reclassified from L2 to L5 based on HOC_LAYER_TOPOLOGY_V1 evidence analysis (2026-01-24).
# Full migration blocked until KnowledgeLifecycleManager moves from app.services to HOC.

"""
GAP-083-085: Knowledge SDK Façade

A thin, state-driven, async-aware SDK interface over KnowledgeLifecycleManager.

ARCHITECTURAL PRINCIPLE:
    SDK calls REQUEST transitions.
    LifecycleManager DECIDES.
    Policy + state machine ARBITRATE.

DESIGN INVARIANTS:
- SDK-001: SDK does NOT force transitions — it requests them
- SDK-002: SDK does NOT manage state — orchestrator does
- SDK-003: SDK does NOT bypass policy gates — gates are mandatory
- SDK-004: SDK provides async-aware wait semantics
- SDK-005: SDK returns rich results, not exceptions

WHY THIN:
- If SDK owns state logic, you get split-brain with orchestrator
- If SDK bypasses gates, you lose governance
- If SDK throws exceptions, you lose structured outcomes

COVERAGE:
- GAP-083: Onboarding SDK methods (register, verify, ingest, index, classify, activate)
- GAP-084: Offboarding SDK methods (deregister, deactivate, archive, purge)
- GAP-085: Wait semantics and state queries
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.knowledge_lifecycle import (
    KnowledgePlaneLifecycleState,
    LifecycleAction,
)
from app.services.knowledge_lifecycle_manager import (
    KnowledgeLifecycleManager,
    KnowledgePlane,
    TransitionRequest,
    TransitionResponse,
    GateDecision,
    get_knowledge_lifecycle_manager,
)


# =============================================================================
# SDK Configuration
# =============================================================================


@dataclass
class KnowledgePlaneConfig:
    """Configuration for creating a knowledge plane."""
    name: str
    description: Optional[str] = None
    connection_string: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WaitOptions:
    """Options for wait operations."""
    timeout: float = 300.0  # 5 minutes default
    poll_interval: float = 1.0  # Check every second
    fail_on_error_state: bool = True  # Fail if plane reaches FAILED state


# =============================================================================
# SDK Result Types
# =============================================================================


@dataclass
class SDKResult:
    """
    Structured result from SDK operations.

    SDK-005: SDK returns rich results, not exceptions.
    Every SDK method returns this type with success/failure and context.
    """
    success: bool
    plane_id: Optional[str] = None
    state: Optional[KnowledgePlaneLifecycleState] = None
    previous_state: Optional[KnowledgePlaneLifecycleState] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    job_id: Optional[str] = None
    audit_event_id: Optional[str] = None
    gate_blocked: bool = False
    gate_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_transition_response(cls, response: TransitionResponse) -> "SDKResult":
        """Convert TransitionResponse to SDKResult."""
        gate_blocked = False
        gate_reason = None
        # Note: GateResult.__bool__ returns False when blocked, so we must check 'is not None'
        if response.gate_result is not None and response.gate_result.decision == GateDecision.BLOCKED:
            gate_blocked = True
            gate_reason = response.gate_result.reason

        return cls(
            success=response.success,
            plane_id=response.plane_id,
            state=response.to_state,
            previous_state=response.from_state,
            message=response.reason,
            job_id=response.job_id,
            audit_event_id=response.audit_event_id,
            gate_blocked=gate_blocked,
            gate_reason=gate_reason,
            metadata=response.metadata,
        )

    @classmethod
    def error(cls, message: str, error_code: Optional[str] = None) -> "SDKResult":
        """Create an error result."""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "success": self.success,
            "plane_id": self.plane_id,
            "state": self.state.name if self.state else None,
            "previous_state": self.previous_state.name if self.previous_state else None,
            "message": self.message,
            "error_code": self.error_code,
            "job_id": self.job_id,
            "audit_event_id": self.audit_event_id,
            "gate_blocked": self.gate_blocked,
            "gate_reason": self.gate_reason,
            "metadata": self.metadata,
        }


@dataclass
class PlaneInfo:
    """Information about a knowledge plane for SDK consumers."""
    id: str
    tenant_id: str
    name: str
    state: KnowledgePlaneLifecycleState
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    description: Optional[str]
    bound_policies: List[str]
    active_job_id: Optional[str]

    # Capability flags (derived from state)
    allows_queries: bool
    allows_policy_binding: bool
    allows_new_runs: bool
    allows_modifications: bool
    is_onboarding: bool
    is_operational: bool
    is_offboarding: bool
    is_terminal: bool

    @classmethod
    def from_plane(cls, plane: KnowledgePlane) -> "PlaneInfo":
        """Create from internal KnowledgePlane."""
        return cls(
            id=plane.id,
            tenant_id=plane.tenant_id,
            name=plane.name,
            state=plane.state,
            created_at=plane.created_at,
            updated_at=plane.updated_at,
            created_by=plane.created_by,
            description=plane.description,
            bound_policies=plane.bound_policies.copy(),
            active_job_id=plane.active_job_id,
            allows_queries=plane.state.allows_queries(),
            allows_policy_binding=plane.state.allows_policy_binding(),
            allows_new_runs=plane.state.allows_new_runs(),
            allows_modifications=plane.state.allows_modifications(),
            is_onboarding=plane.state.is_onboarding(),
            is_operational=plane.state.is_operational(),
            is_offboarding=plane.state.is_offboarding(),
            is_terminal=plane.state.is_terminal(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "state": self.state.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "description": self.description,
            "bound_policies": self.bound_policies,
            "active_job_id": self.active_job_id,
            "capabilities": {
                "allows_queries": self.allows_queries,
                "allows_policy_binding": self.allows_policy_binding,
                "allows_new_runs": self.allows_new_runs,
                "allows_modifications": self.allows_modifications,
            },
            "lifecycle": {
                "is_onboarding": self.is_onboarding,
                "is_operational": self.is_operational,
                "is_offboarding": self.is_offboarding,
                "is_terminal": self.is_terminal,
            },
        }


# =============================================================================
# Knowledge SDK (THE FAÇADE)
# =============================================================================


class KnowledgeSDK:
    """
    GAP-083-085: Knowledge SDK Façade.

    A thin, state-driven, async-aware SDK interface.

    Usage:
        sdk = KnowledgeSDK(tenant_id="tenant-123")

        # Register a new knowledge plane
        result = sdk.register(KnowledgePlaneConfig(
            name="My Knowledge Base",
            connection_string="postgresql://...",
        ))

        if result.success:
            plane_id = result.plane_id

            # Progress through lifecycle
            await sdk.verify(plane_id)
            await sdk.wait_until(plane_id, KnowledgePlaneLifecycleState.VERIFIED)

            await sdk.ingest(plane_id)
            await sdk.wait_until(plane_id, KnowledgePlaneLifecycleState.INDEXED)

            # ... continue through activation

    IMPORTANT:
        SDK calls REQUEST transitions. This SDK does NOT guarantee success.
        The KnowledgeLifecycleManager decides whether transitions are allowed
        based on state machine rules and policy gates.
    """

    def __init__(
        self,
        tenant_id: str,
        actor_id: Optional[str] = None,
        manager: Optional[KnowledgeLifecycleManager] = None,
    ):
        """
        Initialize the SDK.

        Args:
            tenant_id: Tenant ID for all operations (required)
            actor_id: Optional actor ID for audit trails
            manager: Optional custom lifecycle manager (for testing)
        """
        self._tenant_id = tenant_id
        self._actor_id = actor_id
        self._manager = manager or get_knowledge_lifecycle_manager()

    # =========================================================================
    # GAP-083: Onboarding Methods
    # =========================================================================

    def register(
        self,
        config: KnowledgePlaneConfig,
        plane_id: Optional[str] = None,
    ) -> SDKResult:
        """
        Register a new knowledge plane.

        Creates a new knowledge plane in DRAFT state.

        Args:
            config: Configuration for the knowledge plane
            plane_id: Optional specific plane ID (for testing), otherwise generated

        Returns:
            SDKResult with plane_id if successful
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id or "new",
            tenant_id=self._tenant_id,
            action=LifecycleAction.REGISTER,
            actor_id=self._actor_id,
            metadata={
                "name": config.name,
                "description": config.description,
                "config": {
                    "connection_string": config.connection_string,
                    "credentials": config.credentials,
                    **config.config,
                },
            },
        ))
        return SDKResult.from_transition_response(response)

    def verify(
        self,
        plane_id: str,
        connection_string: Optional[str] = None,
        credentials: Optional[Dict[str, str]] = None,
    ) -> SDKResult:
        """
        Request verification of a knowledge plane.

        Starts the verification process (DRAFT → PENDING_VERIFY).
        This may trigger an async job to test connectivity.

        Args:
            plane_id: Knowledge plane ID
            connection_string: Optional connection string override
            credentials: Optional credentials override

        Returns:
            SDKResult with job_id if async verification started
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.VERIFY,
            actor_id=self._actor_id,
            metadata={
                "connection_string": connection_string,
                "credentials": credentials,
            },
        ))
        return SDKResult.from_transition_response(response)

    def ingest(
        self,
        plane_id: str,
        ingest_config: Optional[Dict[str, Any]] = None,
    ) -> SDKResult:
        """
        Start data ingestion for a knowledge plane.

        Starts the ingestion process (VERIFIED → INGESTING).
        This triggers an async job to read and store data.

        Args:
            plane_id: Knowledge plane ID
            ingest_config: Optional ingestion configuration

        Returns:
            SDKResult with job_id if async ingestion started
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.INGEST,
            actor_id=self._actor_id,
            metadata={"ingest_config": ingest_config or {}},
        ))
        return SDKResult.from_transition_response(response)

    def index(self, plane_id: str) -> SDKResult:
        """
        Complete indexing for a knowledge plane.

        Advances from INGESTING → INDEXED after ingestion completes.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            SDKResult indicating success or failure
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.INDEX,
            actor_id=self._actor_id,
        ))
        return SDKResult.from_transition_response(response)

    def classify(self, plane_id: str) -> SDKResult:
        """
        Complete classification for a knowledge plane.

        Advances from INDEXED → CLASSIFIED after data classification.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            SDKResult indicating success or failure
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.CLASSIFY,
            actor_id=self._actor_id,
        ))
        return SDKResult.from_transition_response(response)

    def request_activation(self, plane_id: str) -> SDKResult:
        """
        Request activation for a knowledge plane.

        Moves from CLASSIFIED → PENDING_ACTIVATE.
        The plane must have at least one policy bound before actual activation.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            SDKResult indicating success or failure
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action="request_activation",
            actor_id=self._actor_id,
        ))
        return SDKResult.from_transition_response(response)

    def activate(self, plane_id: str) -> SDKResult:
        """
        Activate a knowledge plane.

        Moves from PENDING_ACTIVATE → ACTIVE.
        IMPORTANT: This requires at least one policy to be bound (GAP-087 gate).

        Args:
            plane_id: Knowledge plane ID

        Returns:
            SDKResult indicating success or gate_blocked if policy missing
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.ACTIVATE,
            actor_id=self._actor_id,
        ))
        return SDKResult.from_transition_response(response)

    # =========================================================================
    # GAP-084: Offboarding Methods
    # =========================================================================

    def deregister(
        self,
        plane_id: str,
        reason: Optional[str] = None,
    ) -> SDKResult:
        """
        Request deregistration of a knowledge plane.

        Starts the offboarding process (ACTIVE → PENDING_DEACTIVATE).
        A grace period applies during which deregistration can be cancelled.

        Args:
            plane_id: Knowledge plane ID
            reason: Optional reason for deregistration

        Returns:
            SDKResult indicating success or failure
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.DEREGISTER,
            actor_id=self._actor_id,
            reason=reason,
        ))
        return SDKResult.from_transition_response(response)

    def cancel_deregister(self, plane_id: str) -> SDKResult:
        """
        Cancel a pending deregistration.

        Moves from PENDING_DEACTIVATE → ACTIVE (cancels offboarding).
        Only valid during the grace period.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            SDKResult indicating success or failure
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.CANCEL_DEREGISTER,
            actor_id=self._actor_id,
        ))
        return SDKResult.from_transition_response(response)

    def deactivate(
        self,
        plane_id: str,
        force: bool = False,
    ) -> SDKResult:
        """
        Deactivate a knowledge plane.

        Moves from PENDING_DEACTIVATE → DEACTIVATED.
        This soft-deletes the plane, preserving data but preventing new runs.

        Args:
            plane_id: Knowledge plane ID
            force: If True, bypass grace period check

        Returns:
            SDKResult indicating success or failure
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.DEACTIVATE,
            actor_id=self._actor_id,
            metadata={"force": force},
        ))
        return SDKResult.from_transition_response(response)

    def archive(self, plane_id: str) -> SDKResult:
        """
        Archive a deactivated knowledge plane.

        Moves from DEACTIVATED → ARCHIVED.
        Exports data to cold storage.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            SDKResult with job_id if async archive started
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.ARCHIVE,
            actor_id=self._actor_id,
        ))
        return SDKResult.from_transition_response(response)

    def purge(
        self,
        plane_id: str,
        reason: str,
    ) -> SDKResult:
        """
        Permanently purge a knowledge plane.

        Moves from ARCHIVED → PURGED.
        IMPORTANT: This requires explicit approval (GAP-087 gate).

        The plane must have purge_approved=True in metadata before this call
        will succeed. Use approve_purge() first.

        Args:
            plane_id: Knowledge plane ID
            reason: Mandatory reason for purge (audit requirement)

        Returns:
            SDKResult indicating success or gate_blocked if not approved
        """
        response = self._manager.handle_transition(TransitionRequest(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
            action=LifecycleAction.PURGE,
            actor_id=self._actor_id,
            reason=reason,
        ))
        return SDKResult.from_transition_response(response)

    # =========================================================================
    # GAP-085: Wait Semantics and State Queries
    # =========================================================================

    def get_state(self, plane_id: str) -> Optional[KnowledgePlaneLifecycleState]:
        """
        Get current lifecycle state of a knowledge plane.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            Current state, or None if plane not found
        """
        return self._manager.get_state(plane_id)

    def get_plane(self, plane_id: str) -> Optional[PlaneInfo]:
        """
        Get detailed information about a knowledge plane.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            PlaneInfo with full details, or None if not found
        """
        plane = self._manager.get_plane(plane_id)
        if not plane:
            return None
        return PlaneInfo.from_plane(plane)

    def get_history(self, plane_id: str) -> List[Dict[str, Any]]:
        """
        Get state transition history for a knowledge plane.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            List of state transition records
        """
        return self._manager.get_history(plane_id)

    def get_audit_log(
        self,
        plane_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get audit events for knowledge planes.

        Args:
            plane_id: Optional plane ID filter

        Returns:
            List of audit events as dictionaries
        """
        events = self._manager.get_audit_log(
            plane_id=plane_id,
            tenant_id=self._tenant_id,
        )
        return [e.to_dict() for e in events]

    def get_next_action(self, plane_id: str) -> Optional[str]:
        """
        Get the next logical action for a knowledge plane.

        Useful for guiding users through the lifecycle.

        Args:
            plane_id: Knowledge plane ID

        Returns:
            Next action name, or None if no automatic progression
        """
        return self._manager.get_next_action(plane_id)

    def can_transition_to(
        self,
        plane_id: str,
        target_state: KnowledgePlaneLifecycleState,
    ) -> bool:
        """
        Check if a transition to target state is possible.

        Note: This checks state machine validity only, not policy gates.

        Args:
            plane_id: Knowledge plane ID
            target_state: Desired target state

        Returns:
            True if transition is valid per state machine
        """
        result = self._manager.can_transition_to(plane_id, target_state)
        return result.allowed

    async def wait_until(
        self,
        plane_id: str,
        target_state: KnowledgePlaneLifecycleState,
        options: Optional[WaitOptions] = None,
    ) -> SDKResult:
        """
        Wait for a knowledge plane to reach a target state.

        This is the primary async-aware method for waiting on background jobs.
        Polls the state until target is reached or timeout occurs.

        Args:
            plane_id: Knowledge plane ID
            target_state: State to wait for
            options: Wait options (timeout, poll interval)

        Returns:
            SDKResult indicating whether target state was reached
        """
        opts = options or WaitOptions()
        start_time = time.time()
        deadline = start_time + opts.timeout

        while time.time() < deadline:
            state = self._manager.get_state(plane_id)

            if state is None:
                return SDKResult.error(
                    f"Knowledge plane not found: {plane_id}",
                    error_code="PLANE_NOT_FOUND",
                )

            if state == target_state:
                return SDKResult(
                    success=True,
                    plane_id=plane_id,
                    state=state,
                    message=f"Reached target state: {target_state.name}",
                )

            # Check for error state
            if opts.fail_on_error_state and state.is_failed():
                return SDKResult(
                    success=False,
                    plane_id=plane_id,
                    state=state,
                    message=f"Knowledge plane reached FAILED state",
                    error_code="PLANE_FAILED",
                )

            # Check for terminal state (other than target)
            if state.is_terminal() and state != target_state:
                return SDKResult(
                    success=False,
                    plane_id=plane_id,
                    state=state,
                    message=f"Knowledge plane reached terminal state {state.name}, "
                            f"cannot reach {target_state.name}",
                    error_code="TERMINAL_STATE",
                )

            # Wait before next poll
            await asyncio.sleep(opts.poll_interval)

        # Timeout
        current_state = self._manager.get_state(plane_id)
        return SDKResult(
            success=False,
            plane_id=plane_id,
            state=current_state,
            message=f"Timeout waiting for state {target_state.name} "
                    f"(current: {current_state.name if current_state else 'unknown'})",
            error_code="TIMEOUT",
        )

    def wait_until_sync(
        self,
        plane_id: str,
        target_state: KnowledgePlaneLifecycleState,
        options: Optional[WaitOptions] = None,
    ) -> SDKResult:
        """
        Synchronous version of wait_until.

        For use in non-async contexts.

        Args:
            plane_id: Knowledge plane ID
            target_state: State to wait for
            options: Wait options (timeout, poll interval)

        Returns:
            SDKResult indicating whether target state was reached
        """
        opts = options or WaitOptions()
        start_time = time.time()
        deadline = start_time + opts.timeout

        while time.time() < deadline:
            state = self._manager.get_state(plane_id)

            if state is None:
                return SDKResult.error(
                    f"Knowledge plane not found: {plane_id}",
                    error_code="PLANE_NOT_FOUND",
                )

            if state == target_state:
                return SDKResult(
                    success=True,
                    plane_id=plane_id,
                    state=state,
                    message=f"Reached target state: {target_state.name}",
                )

            # Check for error state
            if opts.fail_on_error_state and state.is_failed():
                return SDKResult(
                    success=False,
                    plane_id=plane_id,
                    state=state,
                    message=f"Knowledge plane reached FAILED state",
                    error_code="PLANE_FAILED",
                )

            # Check for terminal state (other than target)
            if state.is_terminal() and state != target_state:
                return SDKResult(
                    success=False,
                    plane_id=plane_id,
                    state=state,
                    message=f"Knowledge plane reached terminal state {state.name}, "
                            f"cannot reach {target_state.name}",
                    error_code="TERMINAL_STATE",
                )

            # Wait before next poll
            time.sleep(opts.poll_interval)

        # Timeout
        current_state = self._manager.get_state(plane_id)
        return SDKResult(
            success=False,
            plane_id=plane_id,
            state=current_state,
            message=f"Timeout waiting for state {target_state.name} "
                    f"(current: {current_state.name if current_state else 'unknown'})",
            error_code="TIMEOUT",
        )

    # =========================================================================
    # Policy Management (GAP-087 integration)
    # =========================================================================

    def bind_policy(self, plane_id: str, policy_id: str) -> SDKResult:
        """
        Bind a policy to a knowledge plane.

        Required before activation (GAP-087 policy gate).

        Args:
            plane_id: Knowledge plane ID
            policy_id: Policy ID to bind

        Returns:
            SDKResult indicating success or failure
        """
        if self._manager.bind_policy(plane_id, policy_id):
            plane = self._manager.get_plane(plane_id)
            return SDKResult(
                success=True,
                plane_id=plane_id,
                state=plane.state if plane else None,
                message=f"Policy {policy_id} bound to plane {plane_id}",
                metadata={"policy_id": policy_id},
            )
        return SDKResult.error(
            f"Failed to bind policy {policy_id} to plane {plane_id}",
            error_code="BIND_FAILED",
        )

    def unbind_policy(self, plane_id: str, policy_id: str) -> SDKResult:
        """
        Unbind a policy from a knowledge plane.

        Args:
            plane_id: Knowledge plane ID
            policy_id: Policy ID to unbind

        Returns:
            SDKResult indicating success or failure
        """
        if self._manager.unbind_policy(plane_id, policy_id):
            plane = self._manager.get_plane(plane_id)
            return SDKResult(
                success=True,
                plane_id=plane_id,
                state=plane.state if plane else None,
                message=f"Policy {policy_id} unbound from plane {plane_id}",
                metadata={"policy_id": policy_id},
            )
        return SDKResult.error(
            f"Failed to unbind policy {policy_id} from plane {plane_id}",
            error_code="UNBIND_FAILED",
        )

    def approve_purge(
        self,
        plane_id: str,
        reason: str,
    ) -> SDKResult:
        """
        Approve purge for a knowledge plane.

        Required before purge (GAP-087 policy gate).

        Args:
            plane_id: Knowledge plane ID
            reason: Reason for purge approval

        Returns:
            SDKResult indicating success or failure
        """
        if not self._actor_id:
            return SDKResult.error(
                "Actor ID required for purge approval",
                error_code="ACTOR_REQUIRED",
            )

        if self._manager.approve_purge(plane_id, self._actor_id):
            plane = self._manager.get_plane(plane_id)
            return SDKResult(
                success=True,
                plane_id=plane_id,
                state=plane.state if plane else None,
                message=f"Purge approved for plane {plane_id}",
                metadata={
                    "approver": self._actor_id,
                    "reason": reason,
                },
            )
        return SDKResult.error(
            f"Failed to approve purge for plane {plane_id}",
            error_code="APPROVAL_FAILED",
        )


# =============================================================================
# Singleton Factory
# =============================================================================


def create_knowledge_sdk(
    tenant_id: str,
    actor_id: Optional[str] = None,
) -> KnowledgeSDK:
    """
    Create a KnowledgeSDK instance for a tenant.

    Args:
        tenant_id: Tenant ID (required)
        actor_id: Optional actor ID for audit trails

    Returns:
        KnowledgeSDK instance bound to the tenant
    """
    return KnowledgeSDK(tenant_id=tenant_id, actor_id=actor_id)


__all__ = [
    "KnowledgeSDK",
    "KnowledgePlaneConfig",
    "WaitOptions",
    "SDKResult",
    "PlaneInfo",
    "create_knowledge_sdk",
]
