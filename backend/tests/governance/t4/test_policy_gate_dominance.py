# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, manual
#   Execution: sync
# Role: T4 Policy Gate Dominance Tests (GAP-087)
# Callers: pytest, CI
# Allowed Imports: L4 (models, services)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: GAP-087, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15.4

"""
T4 Policy Gate Dominance Tests (GAP-087)

These tests verify that policy gates dominate lifecycle transitions:

1. ACTIVATE is blocked without policy binding
2. DEACTIVATE blocked if knowledge plane is actively referenced
3. PURGE is blocked without explicit approval
4. Custom gates can override default behavior
5. Gate decisions are captured in responses

Test Count Target: ~80 tests

POLICY GATES UNDER TEST:
- PENDING_ACTIVATE → ACTIVE: Requires at least one policy binding
- PENDING_DEACTIVATE → DEACTIVATED: No active policy references (stub)
- ARCHIVED → PURGED: Requires explicit purge approval

INVARIANTS:
- LIFECYCLE-004: ACTIVE requires policy binding
- LIFECYCLE-006: Offboarding requires dependency checks
- MANAGER-003: Policy gates are mandatory for protected transitions
"""

import pytest
from typing import Callable, Optional

from app.models.knowledge_lifecycle import (
    KnowledgePlaneLifecycleState,
    LifecycleAction,
)
from app.services.knowledge_lifecycle_manager import (
    KnowledgeLifecycleManager,
    KnowledgePlane,
    TransitionRequest,
    GateResult,
    GateDecision,
    LifecycleAuditEventType,
    reset_manager,
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
def plane_at_pending_activate(manager: KnowledgeLifecycleManager) -> str:
    """Create a plane at PENDING_ACTIVATE state (ready for activation)."""
    response = manager.handle_transition(TransitionRequest(
        plane_id="new",
        tenant_id="tenant-123",
        action=LifecycleAction.REGISTER,
    ))
    plane = manager.get_plane(response.plane_id)
    plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE
    return response.plane_id


@pytest.fixture
def plane_at_pending_deactivate(manager: KnowledgeLifecycleManager) -> str:
    """Create a plane at PENDING_DEACTIVATE state (ready for deactivation)."""
    response = manager.handle_transition(TransitionRequest(
        plane_id="new",
        tenant_id="tenant-123",
        action=LifecycleAction.REGISTER,
    ))
    plane = manager.get_plane(response.plane_id)
    plane.state = KnowledgePlaneLifecycleState.PENDING_DEACTIVATE
    return response.plane_id


@pytest.fixture
def plane_at_archived(manager: KnowledgeLifecycleManager) -> str:
    """Create a plane at ARCHIVED state (ready for purge)."""
    response = manager.handle_transition(TransitionRequest(
        plane_id="new",
        tenant_id="tenant-123",
        action=LifecycleAction.REGISTER,
    ))
    plane = manager.get_plane(response.plane_id)
    plane.state = KnowledgePlaneLifecycleState.ARCHIVED
    return response.plane_id


# =============================================================================
# ACTIVATE Gate: Requires Policy Binding (LIFECYCLE-004)
# =============================================================================


class TestActivateGate:
    """Tests for ACTIVATE transition gate (policy binding required)."""

    def test_activate_blocked_without_policy(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """ACTIVATE is blocked if no policy is bound."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_pending_activate,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert not response.success
        assert "No policy bound" in response.reason
        assert response.gate_result is not None
        assert response.gate_result.decision == GateDecision.BLOCKED

    def test_activate_blocked_reason_specifies_required_action(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """ACTIVATE block provides required action hint."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_pending_activate,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert response.gate_result.required_action == "bind_policy"

    def test_activate_allowed_with_policy_bound(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """ACTIVATE succeeds when at least one policy is bound."""
        # Bind a policy first
        manager.bind_policy(plane_at_pending_activate, "policy-001")

        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_pending_activate,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert response.success
        assert manager.get_state(plane_at_pending_activate) == KnowledgePlaneLifecycleState.ACTIVE

    def test_activate_with_multiple_policies(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """ACTIVATE succeeds with multiple policies bound."""
        manager.bind_policy(plane_at_pending_activate, "policy-001")
        manager.bind_policy(plane_at_pending_activate, "policy-002")
        manager.bind_policy(plane_at_pending_activate, "policy-003")

        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_pending_activate,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert response.success

    def test_activate_preserves_state_on_block(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """ACTIVATE block preserves PENDING_ACTIVATE state."""
        manager.handle_transition(TransitionRequest(
            plane_id=plane_at_pending_activate,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert manager.get_state(plane_at_pending_activate) == KnowledgePlaneLifecycleState.PENDING_ACTIVATE


# =============================================================================
# DEACTIVATE Gate (Dependency Check - Stub)
# =============================================================================


class TestDeactivateGate:
    """Tests for DEACTIVATE transition gate (dependency check)."""

    def test_deactivate_allowed_by_default(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_deactivate: str
    ):
        """DEACTIVATE is allowed by default (no references in stub)."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_pending_deactivate,
            tenant_id="tenant-123",
            action=LifecycleAction.DEACTIVATE,
        ))

        # Default gate allows DEACTIVATE (no dependency tracking in stub)
        assert response.success
        assert manager.get_state(plane_at_pending_deactivate) == KnowledgePlaneLifecycleState.DEACTIVATED

    def test_deactivate_blocked_by_custom_gate(
        self, plane_at_pending_deactivate: str
    ):
        """DEACTIVATE can be blocked by custom gate (active references)."""
        def custom_gate(plane_id, from_state, to_state):
            if to_state == KnowledgePlaneLifecycleState.DEACTIVATED:
                return GateResult.blocked(
                    "Knowledge plane is actively referenced by 3 policies",
                    required_action="unbind_policies",
                )
            return GateResult.allowed()

        manager = KnowledgeLifecycleManager(policy_gate=custom_gate)

        # Re-create plane in this manager
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_DEACTIVATE

        # Try to deactivate
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.DEACTIVATE,
        ))

        assert not response.success
        assert "actively referenced" in response.reason


# =============================================================================
# PURGE Gate: Requires Explicit Approval
# =============================================================================


class TestPurgeGate:
    """Tests for PURGE transition gate (approval required)."""

    def test_purge_blocked_without_approval(
        self, manager: KnowledgeLifecycleManager, plane_at_archived: str
    ):
        """PURGE is blocked if not explicitly approved."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_archived,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,
        ))

        assert not response.success
        assert response.gate_result.decision == GateDecision.PENDING
        assert "approval" in response.reason.lower()

    def test_purge_blocked_reason_specifies_required_action(
        self, manager: KnowledgeLifecycleManager, plane_at_archived: str
    ):
        """PURGE block provides required action hint."""
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_archived,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,
        ))

        assert response.gate_result.required_action == "get_purge_approval"

    def test_purge_allowed_after_approval(
        self, manager: KnowledgeLifecycleManager, plane_at_archived: str
    ):
        """PURGE succeeds after explicit approval."""
        # Get approval first
        manager.approve_purge(plane_at_archived, "admin-user")

        response = manager.handle_transition(TransitionRequest(
            plane_id=plane_at_archived,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,
        ))

        assert response.success
        assert manager.get_state(plane_at_archived) == KnowledgePlaneLifecycleState.PURGED

    def test_approve_purge_records_metadata(
        self, manager: KnowledgeLifecycleManager, plane_at_archived: str
    ):
        """approve_purge records approver and timestamp."""
        manager.approve_purge(plane_at_archived, "admin-user")

        plane = manager.get_plane(plane_at_archived)
        assert plane.metadata.get("purge_approved") is True
        assert plane.metadata.get("purge_approver") == "admin-user"
        assert "purge_approved_at" in plane.metadata

    def test_approve_purge_emits_audit_event(
        self, manager: KnowledgeLifecycleManager, plane_at_archived: str
    ):
        """approve_purge emits an audit event."""
        manager.approve_purge(plane_at_archived, "admin-user")

        events = manager.get_audit_log(
            plane_id=plane_at_archived,
            event_type=LifecycleAuditEventType.PURGE_APPROVED,
        )
        assert len(events) == 1
        assert events[0].actor_id == "admin-user"

    def test_purge_preserves_state_on_block(
        self, manager: KnowledgeLifecycleManager, plane_at_archived: str
    ):
        """PURGE block preserves ARCHIVED state."""
        manager.handle_transition(TransitionRequest(
            plane_id=plane_at_archived,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,
        ))

        assert manager.get_state(plane_at_archived) == KnowledgePlaneLifecycleState.ARCHIVED


# =============================================================================
# Custom Gate Integration
# =============================================================================


class TestCustomGateIntegration:
    """Tests for custom policy gate integration."""

    def test_custom_gate_receives_correct_arguments(self):
        """Custom gate receives plane_id, from_state, to_state."""
        gate_calls = []

        def custom_gate(plane_id, from_state, to_state):
            gate_calls.append((plane_id, from_state, to_state))
            return GateResult.allowed()

        manager = KnowledgeLifecycleManager(policy_gate=custom_gate)

        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert len(gate_calls) == 1
        assert gate_calls[0] == (
            plane.id,
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.ACTIVE,
        )

    def test_custom_gate_can_allow_all(self):
        """Custom gate can allow all transitions (for testing)."""
        def allow_all_gate(plane_id, from_state, to_state):
            return GateResult.allowed()

        manager = KnowledgeLifecycleManager(policy_gate=allow_all_gate)

        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        # Should succeed without policy binding
        response = manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert response.success

    def test_custom_gate_can_block_with_custom_reason(self):
        """Custom gate can block with custom reason."""
        def custom_gate(plane_id, from_state, to_state):
            return GateResult.blocked(
                "Custom block reason for testing",
                required_action="custom_action",
            )

        manager = KnowledgeLifecycleManager(policy_gate=custom_gate)

        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        response = manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert not response.success
        assert "Custom block reason" in response.reason
        assert response.gate_result.required_action == "custom_action"

    def test_custom_gate_can_return_pending(self):
        """Custom gate can return PENDING status."""
        def custom_gate(plane_id, from_state, to_state):
            return GateResult.pending(
                "Waiting for external approval system",
                required_action="await_external_approval",
            )

        manager = KnowledgeLifecycleManager(policy_gate=custom_gate)

        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        response = manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert not response.success
        assert response.gate_result.decision == GateDecision.PENDING

    def test_set_policy_gate_replaces_gate(self):
        """set_policy_gate replaces the existing gate."""
        manager = KnowledgeLifecycleManager()

        gate_calls = []
        def custom_gate(plane_id, from_state, to_state):
            gate_calls.append("called")
            return GateResult.allowed()

        manager.set_policy_gate(custom_gate)

        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert "called" in gate_calls


# =============================================================================
# Policy Binding Management
# =============================================================================


class TestPolicyBindingManagement:
    """Tests for policy binding and unbinding."""

    def test_bind_policy_adds_to_plane(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """bind_policy adds policy to plane's bound_policies list."""
        result = manager.bind_policy(plane_at_pending_activate, "policy-001")

        assert result is True
        plane = manager.get_plane(plane_at_pending_activate)
        assert "policy-001" in plane.bound_policies

    def test_bind_policy_idempotent(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """bind_policy is idempotent (no duplicates)."""
        manager.bind_policy(plane_at_pending_activate, "policy-001")
        manager.bind_policy(plane_at_pending_activate, "policy-001")
        manager.bind_policy(plane_at_pending_activate, "policy-001")

        plane = manager.get_plane(plane_at_pending_activate)
        assert plane.bound_policies.count("policy-001") == 1

    def test_bind_policy_fails_for_unknown_plane(
        self, manager: KnowledgeLifecycleManager
    ):
        """bind_policy returns False for unknown plane."""
        result = manager.bind_policy("unknown-plane-id", "policy-001")
        assert result is False

    def test_unbind_policy_removes_from_plane(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """unbind_policy removes policy from plane's bound_policies list."""
        manager.bind_policy(plane_at_pending_activate, "policy-001")
        manager.bind_policy(plane_at_pending_activate, "policy-002")

        result = manager.unbind_policy(plane_at_pending_activate, "policy-001")

        assert result is True
        plane = manager.get_plane(plane_at_pending_activate)
        assert "policy-001" not in plane.bound_policies
        assert "policy-002" in plane.bound_policies

    def test_unbind_policy_idempotent(
        self, manager: KnowledgeLifecycleManager, plane_at_pending_activate: str
    ):
        """unbind_policy is idempotent (no error if not bound)."""
        # Unbind policy that was never bound
        result = manager.unbind_policy(plane_at_pending_activate, "policy-001")
        assert result is True  # No error, but nothing removed

    def test_unbind_policy_fails_for_unknown_plane(
        self, manager: KnowledgeLifecycleManager
    ):
        """unbind_policy returns False for unknown plane."""
        result = manager.unbind_policy("unknown-plane-id", "policy-001")
        assert result is False


# =============================================================================
# Gate Result Object
# =============================================================================


class TestGateResultObject:
    """Tests for GateResult object behavior."""

    def test_gate_result_allowed_is_truthy(self):
        """GateResult.allowed() is truthy."""
        result = GateResult.allowed()
        assert bool(result) is True
        assert result.decision == GateDecision.ALLOWED

    def test_gate_result_blocked_is_falsy(self):
        """GateResult.blocked() is falsy."""
        result = GateResult.blocked("reason")
        assert bool(result) is False
        assert result.decision == GateDecision.BLOCKED

    def test_gate_result_pending_is_falsy(self):
        """GateResult.pending() is falsy (not allowed to proceed)."""
        result = GateResult.pending("reason", "action")
        assert bool(result) is False
        assert result.decision == GateDecision.PENDING

    def test_gate_result_blocked_stores_reason(self):
        """GateResult.blocked() stores the reason."""
        result = GateResult.blocked("Custom reason", "custom_action")
        assert result.reason == "Custom reason"
        assert result.required_action == "custom_action"


# =============================================================================
# Gate Not Invoked for Non-Gated Transitions
# =============================================================================


class TestGateNotInvokedForNonGated:
    """Tests that gate is not invoked for non-gated transitions."""

    def test_gate_not_called_for_register(self):
        """Gate is not called for REGISTER action."""
        gate_calls = []

        def tracking_gate(plane_id, from_state, to_state):
            gate_calls.append((from_state, to_state))
            return GateResult.allowed()

        manager = KnowledgeLifecycleManager(policy_gate=tracking_gate)

        manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        assert len(gate_calls) == 0

    def test_gate_not_called_for_verify(self):
        """Gate is not called for VERIFY action."""
        gate_calls = []

        def tracking_gate(plane_id, from_state, to_state):
            gate_calls.append((from_state, to_state))
            return GateResult.allowed()

        manager = KnowledgeLifecycleManager(policy_gate=tracking_gate)

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

        # Gate should not have been called
        assert len(gate_calls) == 0

    def test_gate_called_only_for_gated_transitions(self):
        """Gate is only called for ACTIVATE, DEACTIVATE, PURGE."""
        gate_calls = []

        def tracking_gate(plane_id, from_state, to_state):
            gate_calls.append(to_state)
            return GateResult.allowed()

        manager = KnowledgeLifecycleManager(policy_gate=tracking_gate)

        # Register
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager.get_plane(response.plane_id)

        # Move through states (non-gated)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE

        # ACTIVATE (gated)
        manager.bind_policy(plane.id, "policy-001")
        manager.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        # Should have called gate for ACTIVATE
        assert KnowledgePlaneLifecycleState.ACTIVE in gate_calls
