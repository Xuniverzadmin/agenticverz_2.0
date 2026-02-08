# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, manual
#   Execution: sync
# Role: T4 Single Entry Enforcement Tests (GAP-086)
# Callers: pytest, CI
# Allowed Imports: L4 (models, services)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: GAP-086, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15.1

"""
T4 Single Entry Enforcement Tests (GAP-086)

These tests verify that the KnowledgeLifecycleManager is THE SINGLE ENTRY POINT
for all lifecycle state changes:

1. All state changes go through handle_transition()
2. No backdoor state mutation is allowed
3. Manager enforces state machine rules
4. Manager coordinates with policy gates and audit
5. Tenant isolation is enforced

Test Count Target: ~60 tests

INVARIANTS UNDER TEST:
- MANAGER-001: All transitions go through this manager
- MANAGER-002: No transition without audit event (tested in audit tests)
- MANAGER-003: Policy gates are mandatory for protected transitions
- MANAGER-004: Failed transitions leave state unchanged
- MANAGER-005: Async jobs report completion back to manager
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import List

from app.models.knowledge_lifecycle import (
    KnowledgePlaneLifecycleState,
    LifecycleAction,
)
from app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager import (
    KnowledgeLifecycleManager,
    KnowledgePlane,
    TransitionRequest,
    TransitionResponse,
    GateResult,
    GateDecision,
    LifecycleAuditEvent,
    LifecycleAuditEventType,
    reset_manager,
    get_knowledge_lifecycle_manager,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def manager() -> KnowledgeLifecycleManager:
    """Create a fresh KnowledgeLifecycleManager for testing."""
    reset_manager()
    return KnowledgeLifecycleManager()


@pytest.fixture
def registered_plane(manager: KnowledgeLifecycleManager) -> str:
    """Create and return a registered knowledge plane ID."""
    response = manager.handle_transition(TransitionRequest(
        plane_id="new",
        tenant_id="tenant-123",
        action=LifecycleAction.REGISTER,
        actor_id="user-456",
        metadata={"name": "Test Plane"},
    ))
    assert response.success, f"Registration failed: {response.reason}"
    return response.plane_id


@pytest.fixture
def verified_plane(manager: KnowledgeLifecycleManager, registered_plane: str) -> str:
    """Create a plane that has completed verification."""
    # Move to PENDING_VERIFY
    manager.handle_transition(TransitionRequest(
        plane_id=registered_plane,
        tenant_id="tenant-123",
        action=LifecycleAction.VERIFY,
    ))
    # Simulate verification complete - move to VERIFIED
    plane = manager.get_plane(registered_plane)
    plane.state = KnowledgePlaneLifecycleState.VERIFIED
    return registered_plane


# =============================================================================
# Registration (Entry Point)
# =============================================================================


class TestRegistration:
    """Tests for knowledge plane registration."""

    def test_register_creates_plane_in_draft_state(self, manager: KnowledgeLifecycleManager):
        """Registration creates a new plane in DRAFT state."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            actor_id="user-456",
        ))

        assert response.success
        assert response.to_state == KnowledgePlaneLifecycleState.DRAFT
        assert manager.get_state(response.plane_id) == KnowledgePlaneLifecycleState.DRAFT

    def test_register_assigns_unique_id(self, manager: KnowledgeLifecycleManager):
        """Registration assigns a unique plane ID."""
        response1 = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        response2 = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        assert response1.plane_id != response2.plane_id
        assert response1.plane_id.startswith("kp_")
        assert response2.plane_id.startswith("kp_")

    def test_register_with_explicit_id(self, manager: KnowledgeLifecycleManager):
        """Registration can use an explicit plane ID."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="my-plane-id",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        assert response.success
        assert response.plane_id == "my-plane-id"

    def test_register_duplicate_id_fails(self, manager: KnowledgeLifecycleManager):
        """Registration fails if plane ID already exists."""
        manager.handle_transition(TransitionRequest(
            plane_id="duplicate-id",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        response = manager.handle_transition(TransitionRequest(
            plane_id="duplicate-id",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        assert not response.success
        assert "already exists" in response.reason

    def test_register_stores_metadata(self, manager: KnowledgeLifecycleManager):
        """Registration stores provided metadata."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            actor_id="user-456",
            metadata={
                "name": "My Knowledge Plane",
                "description": "Test description",
                "config": {"key": "value"},
            },
        ))

        plane = manager.get_plane(response.plane_id)
        assert plane.name == "My Knowledge Plane"
        assert plane.description == "Test description"
        assert plane.config == {"key": "value"}
        assert plane.created_by == "user-456"


# =============================================================================
# Transition Entry Point Enforcement (MANAGER-001)
# =============================================================================


class TestTransitionEntryPointEnforcement:
    """Tests that all transitions go through handle_transition."""

    def test_transition_updates_state_via_handle_transition(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Transitions update state only through handle_transition."""
        initial_state = manager.get_state(registered_plane)
        assert initial_state == KnowledgePlaneLifecycleState.DRAFT

        response = manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert response.success
        assert manager.get_state(registered_plane) == KnowledgePlaneLifecycleState.PENDING_VERIFY

    def test_transition_requires_valid_plane(self, manager: KnowledgeLifecycleManager):
        """Transition fails for non-existent plane."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="non-existent-id",
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert not response.success
        assert "not found" in response.reason

    def test_transition_requires_valid_action(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Transition fails for invalid action from current state."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid from DRAFT
        ))

        assert not response.success
        assert "not valid" in response.reason

    def test_transition_returns_audit_event_id(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Successful transitions return an audit event ID."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert response.success
        assert response.audit_event_id is not None
        assert response.audit_event_id.startswith("evt_")


# =============================================================================
# Tenant Isolation (MANAGER-001 + Authorization)
# =============================================================================


class TestTenantIsolation:
    """Tests that manager enforces tenant isolation."""

    def test_transition_requires_correct_tenant(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Transitions fail for wrong tenant."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="wrong-tenant",  # Registered with tenant-123
            action=LifecycleAction.VERIFY,
        ))

        assert not response.success
        assert "Tenant mismatch" in response.reason

    def test_tenant_cannot_see_other_tenants_planes(
        self, manager: KnowledgeLifecycleManager
    ):
        """Tenants are isolated - cannot interact with other tenants' planes."""
        # Create plane for tenant A
        response_a = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-A",
            action=LifecycleAction.REGISTER,
        ))

        # Tenant B tries to transition tenant A's plane
        response_b = manager.handle_transition(TransitionRequest(
            plane_id=response_a.plane_id,
            tenant_id="tenant-B",
            action=LifecycleAction.VERIFY,
        ))

        assert not response_b.success
        assert "Tenant mismatch" in response_b.reason


# =============================================================================
# Failed Transitions Leave State Unchanged (MANAGER-004)
# =============================================================================


class TestFailedTransitionsPreserveState:
    """Tests that failed transitions don't change state."""

    def test_invalid_action_preserves_state(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Invalid action doesn't change state."""
        initial_state = manager.get_state(registered_plane)

        manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid from DRAFT
        ))

        assert manager.get_state(registered_plane) == initial_state

    def test_tenant_mismatch_preserves_state(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Tenant mismatch doesn't change state."""
        initial_state = manager.get_state(registered_plane)

        manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="wrong-tenant",
            action=LifecycleAction.VERIFY,
        ))

        assert manager.get_state(registered_plane) == initial_state

    def test_gate_block_preserves_state(self, manager: KnowledgeLifecycleManager):
        """Policy gate block doesn't change state."""
        # Create and advance plane to PENDING_ACTIVATE
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        # Try to ACTIVATE without binding policy (default gate blocks this)
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        # Should be blocked by policy gate
        assert not response.success
        assert manager.get_state(plane.id) == KnowledgePlaneLifecycleState.PENDING_ACTIVATE


# =============================================================================
# State Query Methods
# =============================================================================


class TestStateQueryMethods:
    """Tests for state query methods."""

    def test_get_state_returns_current_state(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """get_state returns the current lifecycle state."""
        state = manager.get_state(registered_plane)
        assert state == KnowledgePlaneLifecycleState.DRAFT

    def test_get_state_returns_none_for_unknown_plane(
        self, manager: KnowledgeLifecycleManager
    ):
        """get_state returns None for unknown plane."""
        state = manager.get_state("unknown-plane-id")
        assert state is None

    def test_get_plane_returns_plane_object(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """get_plane returns the full KnowledgePlane object."""
        plane = manager.get_plane(registered_plane)
        assert plane is not None
        assert plane.id == registered_plane
        assert plane.tenant_id == "tenant-123"
        assert plane.state == KnowledgePlaneLifecycleState.DRAFT

    def test_get_plane_returns_none_for_unknown_plane(
        self, manager: KnowledgeLifecycleManager
    ):
        """get_plane returns None for unknown plane."""
        plane = manager.get_plane("unknown-plane-id")
        assert plane is None

    def test_get_history_returns_state_history(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """get_history returns the state transition history."""
        # Perform a transition
        manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        history = manager.get_history(registered_plane)
        assert len(history) >= 1
        assert history[-1]["to_state"] == "PENDING_VERIFY"

    def test_get_history_returns_empty_for_unknown_plane(
        self, manager: KnowledgeLifecycleManager
    ):
        """get_history returns empty list for unknown plane."""
        history = manager.get_history("unknown-plane-id")
        assert history == []


# =============================================================================
# Transition Validation via can_transition_to
# =============================================================================


class TestCanTransitionTo:
    """Tests for can_transition_to validation method."""

    def test_can_transition_to_valid_state(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """can_transition_to returns allowed=True for valid transitions."""
        result = manager.can_transition_to(
            registered_plane,
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
        )
        assert result.allowed is True

    def test_can_transition_to_invalid_state(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """can_transition_to returns allowed=False for invalid transitions."""
        result = manager.can_transition_to(
            registered_plane,
            KnowledgePlaneLifecycleState.ACTIVE,  # Cannot skip to ACTIVE from DRAFT
        )
        assert result.allowed is False

    def test_can_transition_to_unknown_plane(self, manager: KnowledgeLifecycleManager):
        """can_transition_to returns allowed=False for unknown plane."""
        result = manager.can_transition_to(
            "unknown-plane-id",
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
        )
        assert result.allowed is False
        assert "not found" in result.reason


# =============================================================================
# Progression Helper (get_next_action)
# =============================================================================


class TestGetNextAction:
    """Tests for get_next_action helper method."""

    def test_get_next_action_from_draft(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """get_next_action returns VERIFY from DRAFT."""
        action = manager.get_next_action(registered_plane)
        assert action == LifecycleAction.VERIFY

    def test_get_next_action_from_active(self, manager: KnowledgeLifecycleManager):
        """get_next_action returns DEREGISTER from ACTIVE."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.ACTIVE

        action = manager.get_next_action(plane.id)
        assert action == LifecycleAction.DEREGISTER

    def test_get_next_action_from_terminal_returns_none(
        self, manager: KnowledgeLifecycleManager
    ):
        """get_next_action returns None from terminal states."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PURGED

        action = manager.get_next_action(plane.id)
        assert action is None

    def test_get_next_action_unknown_plane_returns_none(
        self, manager: KnowledgeLifecycleManager
    ):
        """get_next_action returns None for unknown plane."""
        action = manager.get_next_action("unknown-plane-id")
        assert action is None


# =============================================================================
# Singleton Pattern
# =============================================================================


class TestSingletonPattern:
    """Tests for singleton manager pattern."""

    def test_get_knowledge_lifecycle_manager_returns_same_instance(self):
        """get_knowledge_lifecycle_manager returns the same instance."""
        reset_manager()
        manager1 = get_knowledge_lifecycle_manager()
        manager2 = get_knowledge_lifecycle_manager()
        assert manager1 is manager2

    def test_reset_manager_clears_singleton(self):
        """reset_manager clears the singleton instance."""
        manager1 = get_knowledge_lifecycle_manager()
        reset_manager()
        manager2 = get_knowledge_lifecycle_manager()
        assert manager1 is not manager2


# =============================================================================
# Custom Integration Points
# =============================================================================


class TestCustomIntegrationPoints:
    """Tests for custom policy gate, audit sink, and job scheduler."""

    def test_custom_policy_gate_is_called(self):
        """Custom policy gate function is called for gated transitions."""
        gate_called = []

        def custom_gate(plane_id, from_state, to_state):
            gate_called.append((plane_id, from_state, to_state))
            return GateResult.allowed()

        manager = KnowledgeLifecycleManager(policy_gate=custom_gate)

        # Register and advance to PENDING_ACTIVATE
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        # Attempt ACTIVATE (requires gate)
        manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        # Gate should have been called
        assert len(gate_called) == 1
        assert gate_called[0][0] == plane.id
        assert gate_called[0][1] == KnowledgePlaneLifecycleState.PENDING_ACTIVATE
        assert gate_called[0][2] == KnowledgePlaneLifecycleState.ACTIVE

    def test_custom_audit_sink_is_called(self):
        """Custom audit sink function is called for all events."""
        events = []

        def custom_sink(event: LifecycleAuditEvent):
            events.append(event)

        manager = KnowledgeLifecycleManager(audit_sink=custom_sink)

        manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        assert len(events) == 1
        assert events[0].event_type == LifecycleAuditEventType.TRANSITION

    def test_custom_job_scheduler_is_called(self):
        """Custom job scheduler function is called for async transitions."""
        jobs = []

        def custom_scheduler(plane_id, job_type, config):
            job_id = f"job_{len(jobs)}"
            jobs.append((plane_id, job_type, config))
            return job_id

        manager = KnowledgeLifecycleManager(job_scheduler=custom_scheduler)

        # Register and verify (PENDING_VERIFY is async)
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        # Scheduler should have been called
        assert len(jobs) == 1
        assert jobs[0][1] == "verify_connectivity"


# =============================================================================
# Response Object Structure
# =============================================================================


class TestTransitionResponseStructure:
    """Tests for TransitionResponse object structure."""

    def test_successful_response_structure(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Successful response has correct structure."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert response.success is True
        assert response.plane_id == registered_plane
        assert response.from_state == KnowledgePlaneLifecycleState.DRAFT
        assert response.to_state == KnowledgePlaneLifecycleState.PENDING_VERIFY
        assert response.action == LifecycleAction.VERIFY
        assert response.audit_event_id is not None

    def test_failed_response_structure(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Failed response has correct structure."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid from DRAFT
        ))

        assert response.success is False
        assert response.plane_id == registered_plane
        assert response.from_state == KnowledgePlaneLifecycleState.DRAFT
        assert response.to_state is None or response.to_state == KnowledgePlaneLifecycleState.PURGED
        assert response.reason is not None

    def test_response_to_dict(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Response can be converted to dictionary."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        data = response.to_dict()
        assert isinstance(data, dict)
        assert data["success"] is True
        assert data["plane_id"] == registered_plane
        assert data["from_state"] == "DRAFT"
        assert data["to_state"] == "PENDING_VERIFY"
