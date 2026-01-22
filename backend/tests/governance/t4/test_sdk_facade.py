# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: test
#   Execution: sync
# Role: T4 SDK Façade Tests (GAP-083 to GAP-085)
# Callers: pytest
# Reference: GAP_IMPLEMENTATION_PLAN_V1.md Section 7.18

"""
T4 SDK Façade Tests (GAP-083 to GAP-085)

Tests for the Knowledge SDK façade:
- GAP-083: Onboarding SDK methods
- GAP-084: Offboarding SDK methods
- GAP-085: Wait semantics and state queries

DESIGN PRINCIPLE:
    SDK calls REQUEST transitions.
    LifecycleManager DECIDES.
    Policy + state machine ARBITRATE.

TEST CATEGORIES:
1. SDKResult tests - structured result handling
2. PlaneInfo tests - plane information retrieval
3. Onboarding method tests (GAP-083)
4. Offboarding method tests (GAP-084)
5. Wait semantics tests (GAP-085)
6. Policy management tests
7. Error handling tests
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import pytest

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
    GateResult,
    reset_manager,
)
from app.services.knowledge_sdk import (
    KnowledgeSDK,
    KnowledgePlaneConfig,
    WaitOptions,
    SDKResult,
    PlaneInfo,
    create_knowledge_sdk,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def manager() -> KnowledgeLifecycleManager:
    """Create a fresh manager for each test."""
    reset_manager()
    return KnowledgeLifecycleManager()


@pytest.fixture
def sdk(manager: KnowledgeLifecycleManager) -> KnowledgeSDK:
    """Create SDK instance with test manager."""
    return KnowledgeSDK(
        tenant_id="test-tenant",
        actor_id="test-actor",
        manager=manager,
    )


@pytest.fixture
def registered_plane(sdk: KnowledgeSDK) -> str:
    """Create and return a registered plane ID."""
    result = sdk.register(KnowledgePlaneConfig(name="Test Plane"))
    assert result.success
    return result.plane_id


@pytest.fixture
def active_plane(sdk: KnowledgeSDK, manager: KnowledgeLifecycleManager) -> str:
    """Create a plane in ACTIVE state."""
    # Register
    result = sdk.register(KnowledgePlaneConfig(name="Active Plane"))
    plane_id = result.plane_id

    # Progress through onboarding
    sdk.verify(plane_id)
    manager.complete_job(manager.get_plane(plane_id).active_job_id, plane_id, True)

    sdk.ingest(plane_id)
    manager.complete_job(manager.get_plane(plane_id).active_job_id, plane_id, True)

    sdk.classify(plane_id)
    sdk.request_activation(plane_id)

    # Bind policy and activate
    sdk.bind_policy(plane_id, "test-policy")
    sdk.activate(plane_id)

    return plane_id


# =============================================================================
# Section 1: SDKResult Tests
# =============================================================================


class TestSDKResult:
    """Tests for SDKResult structured results."""

    def test_sdk_result_success(self):
        """Test successful SDKResult creation."""
        result = SDKResult(
            success=True,
            plane_id="plane-1",
            state=KnowledgePlaneLifecycleState.DRAFT,
            message="Success",
        )
        assert result.success
        assert result.plane_id == "plane-1"
        assert result.state == KnowledgePlaneLifecycleState.DRAFT

    def test_sdk_result_failure(self):
        """Test failure SDKResult creation."""
        result = SDKResult(
            success=False,
            message="Failed",
            error_code="TEST_ERROR",
        )
        assert not result.success
        assert result.error_code == "TEST_ERROR"

    def test_sdk_result_error_factory(self):
        """Test SDKResult.error() factory method."""
        result = SDKResult.error("Test error", "ERR_001")
        assert not result.success
        assert result.message == "Test error"
        assert result.error_code == "ERR_001"

    def test_sdk_result_from_transition_response(self):
        """Test SDKResult.from_transition_response()."""
        response = TransitionResponse(
            success=True,
            plane_id="plane-1",
            from_state=KnowledgePlaneLifecycleState.DRAFT,
            to_state=KnowledgePlaneLifecycleState.PENDING_VERIFY,
            action="verify",
            job_id="job-1",
            audit_event_id="evt-1",
        )
        result = SDKResult.from_transition_response(response)
        assert result.success
        assert result.plane_id == "plane-1"
        assert result.state == KnowledgePlaneLifecycleState.PENDING_VERIFY
        assert result.previous_state == KnowledgePlaneLifecycleState.DRAFT
        assert result.job_id == "job-1"
        assert result.audit_event_id == "evt-1"

    def test_sdk_result_from_blocked_response(self):
        """Test SDKResult.from_transition_response() with gate blocked."""
        response = TransitionResponse(
            success=False,
            plane_id="plane-1",
            from_state=KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            to_state=KnowledgePlaneLifecycleState.ACTIVE,
            action="activate",
            reason="No policy bound",
            gate_result=GateResult.blocked("No policy bound", "bind_policy"),
        )
        result = SDKResult.from_transition_response(response)
        assert not result.success
        assert result.gate_blocked
        assert result.gate_reason == "No policy bound"

    def test_sdk_result_to_dict(self):
        """Test SDKResult.to_dict() serialization."""
        result = SDKResult(
            success=True,
            plane_id="plane-1",
            state=KnowledgePlaneLifecycleState.ACTIVE,
            previous_state=KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            metadata={"key": "value"},
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["plane_id"] == "plane-1"
        assert d["state"] == "ACTIVE"
        assert d["previous_state"] == "PENDING_ACTIVATE"
        assert d["metadata"] == {"key": "value"}


# =============================================================================
# Section 2: PlaneInfo Tests
# =============================================================================


class TestPlaneInfo:
    """Tests for PlaneInfo plane information."""

    def test_plane_info_from_plane(self, manager: KnowledgeLifecycleManager):
        """Test PlaneInfo.from_plane() conversion."""
        # Create a plane via manager
        manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="test",
            action=LifecycleAction.REGISTER,
            actor_id="user-1",
            metadata={"name": "Test Plane", "description": "Test description"},
        ))

        plane = list(manager._planes.values())[0]
        info = PlaneInfo.from_plane(plane)

        assert info.tenant_id == "test"
        assert info.name == "Test Plane"
        assert info.state == KnowledgePlaneLifecycleState.DRAFT
        assert info.created_by == "user-1"

    def test_plane_info_capabilities_draft(self, manager: KnowledgeLifecycleManager):
        """Test PlaneInfo capabilities for DRAFT state."""
        manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="test",
            action=LifecycleAction.REGISTER,
        ))

        plane = list(manager._planes.values())[0]
        info = PlaneInfo.from_plane(plane)

        assert not info.allows_queries
        assert not info.allows_policy_binding
        assert not info.allows_new_runs
        assert info.allows_modifications
        assert info.is_onboarding
        assert not info.is_operational

    def test_plane_info_to_dict(self, sdk: KnowledgeSDK):
        """Test PlaneInfo.to_dict() serialization."""
        result = sdk.register(KnowledgePlaneConfig(name="Test"))
        info = sdk.get_plane(result.plane_id)

        d = info.to_dict()
        assert "id" in d
        assert "tenant_id" in d
        assert "state" in d
        assert "capabilities" in d
        assert "lifecycle" in d
        assert d["capabilities"]["allows_queries"] is False
        assert d["lifecycle"]["is_onboarding"] is True


# =============================================================================
# Section 3: Onboarding Method Tests (GAP-083)
# =============================================================================


class TestOnboardingMethods:
    """Tests for GAP-083 Onboarding SDK methods."""

    def test_register_creates_plane(self, sdk: KnowledgeSDK):
        """Test register() creates a new plane in DRAFT state."""
        result = sdk.register(KnowledgePlaneConfig(
            name="My Knowledge Base",
            description="Test description",
        ))

        assert result.success
        assert result.plane_id is not None
        assert result.state == KnowledgePlaneLifecycleState.DRAFT

    def test_register_with_config(self, sdk: KnowledgeSDK):
        """Test register() with full configuration."""
        result = sdk.register(KnowledgePlaneConfig(
            name="Configured Plane",
            description="With connection",
            connection_string="postgresql://localhost/db",
            credentials={"user": "test"},
            config={"timeout": 30},
        ))

        assert result.success
        info = sdk.get_plane(result.plane_id)
        assert info.name == "Configured Plane"

    def test_register_with_specific_id(self, sdk: KnowledgeSDK):
        """Test register() with specific plane ID."""
        result = sdk.register(
            KnowledgePlaneConfig(name="Test"),
            plane_id="my-custom-id",
        )

        assert result.success
        assert result.plane_id == "my-custom-id"

    def test_register_duplicate_id_fails(self, sdk: KnowledgeSDK):
        """Test register() with duplicate ID fails."""
        sdk.register(KnowledgePlaneConfig(name="First"), plane_id="dup-id")
        result = sdk.register(KnowledgePlaneConfig(name="Second"), plane_id="dup-id")

        assert not result.success
        assert "already exists" in result.message

    def test_verify_starts_verification(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test verify() starts verification process."""
        result = sdk.verify(registered_plane)

        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.PENDING_VERIFY
        assert result.previous_state == KnowledgePlaneLifecycleState.DRAFT

    def test_verify_returns_job_id(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test verify() returns job_id for async operation."""
        result = sdk.verify(registered_plane)

        assert result.success
        assert result.job_id is not None

    def test_verify_with_connection_override(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test verify() with connection string override."""
        result = sdk.verify(
            registered_plane,
            connection_string="postgresql://new/db",
            credentials={"user": "override"},
        )

        assert result.success

    def test_ingest_requires_verified(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test ingest() requires VERIFIED state."""
        # Try to ingest from DRAFT - should fail
        result = sdk.ingest(registered_plane)
        assert not result.success

    def test_ingest_from_verified(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        registered_plane: str,
    ):
        """Test ingest() from VERIFIED state."""
        # Progress to VERIFIED
        sdk.verify(registered_plane)
        plane = manager.get_plane(registered_plane)
        manager.complete_job(plane.active_job_id, registered_plane, True)

        result = sdk.ingest(registered_plane)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.INGESTING

    def test_index_from_ingesting(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        registered_plane: str,
    ):
        """Test index() from INGESTING state."""
        # Progress to VERIFIED
        sdk.verify(registered_plane)
        plane = manager.get_plane(registered_plane)
        manager.complete_job(plane.active_job_id, registered_plane, True)

        # Start ingestion - this moves to INGESTING
        sdk.ingest(registered_plane)
        # Note: Don't call complete_job here - we want to test sdk.index() as the transition

        # Call index() to manually advance from INGESTING → INDEXED
        result = sdk.index(registered_plane)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.INDEXED

    def test_classify_from_indexed(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        registered_plane: str,
    ):
        """Test classify() from INDEXED state."""
        # Progress to INDEXED
        sdk.verify(registered_plane)
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        sdk.ingest(registered_plane)
        # Job completion advances from INGESTING to INDEXED
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        # Note: No need to call sdk.index() - job completion already advanced to INDEXED

        result = sdk.classify(registered_plane)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.CLASSIFIED

    def test_request_activation_from_classified(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        registered_plane: str,
    ):
        """Test request_activation() from CLASSIFIED state."""
        # Progress to CLASSIFIED
        sdk.verify(registered_plane)
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        sdk.ingest(registered_plane)
        # Job completion advances from INGESTING to INDEXED
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        sdk.classify(registered_plane)

        result = sdk.request_activation(registered_plane)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.PENDING_ACTIVATE

    def test_activate_blocked_without_policy(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        registered_plane: str,
    ):
        """Test activate() blocked without policy binding (GAP-087)."""
        # Progress to PENDING_ACTIVATE
        sdk.verify(registered_plane)
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        sdk.ingest(registered_plane)
        # Job completion advances from INGESTING to INDEXED
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        sdk.classify(registered_plane)
        sdk.request_activation(registered_plane)

        result = sdk.activate(registered_plane)
        assert not result.success
        assert result.gate_blocked
        assert "policy" in result.gate_reason.lower()

    def test_activate_succeeds_with_policy(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        registered_plane: str,
    ):
        """Test activate() succeeds with policy binding."""
        # Progress to PENDING_ACTIVATE
        sdk.verify(registered_plane)
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        sdk.ingest(registered_plane)
        # Job completion advances from INGESTING to INDEXED
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)
        sdk.classify(registered_plane)
        sdk.request_activation(registered_plane)

        # Bind policy
        sdk.bind_policy(registered_plane, "my-policy")

        result = sdk.activate(registered_plane)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.ACTIVE

    def test_full_onboarding_flow(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
    ):
        """Test complete onboarding flow end-to-end."""
        # Register
        result = sdk.register(KnowledgePlaneConfig(name="Full Flow Test"))
        plane_id = result.plane_id
        assert result.success

        # Verify
        result = sdk.verify(plane_id)
        assert result.success
        manager.complete_job(manager.get_plane(plane_id).active_job_id, plane_id, True)

        # Ingest
        result = sdk.ingest(plane_id)
        assert result.success
        # Job completion advances from INGESTING to INDEXED
        manager.complete_job(manager.get_plane(plane_id).active_job_id, plane_id, True)

        # Classify (state is now INDEXED after job completion)
        result = sdk.classify(plane_id)
        assert result.success

        # Request activation
        result = sdk.request_activation(plane_id)
        assert result.success

        # Bind policy
        result = sdk.bind_policy(plane_id, "policy-1")
        assert result.success

        # Activate
        result = sdk.activate(plane_id)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.ACTIVE


# =============================================================================
# Section 4: Offboarding Method Tests (GAP-084)
# =============================================================================


class TestOffboardingMethods:
    """Tests for GAP-084 Offboarding SDK methods."""

    def test_deregister_starts_offboarding(self, sdk: KnowledgeSDK, active_plane: str):
        """Test deregister() starts offboarding process."""
        result = sdk.deregister(active_plane, reason="No longer needed")

        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.PENDING_DEACTIVATE

    def test_deregister_requires_active(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test deregister() requires ACTIVE state."""
        result = sdk.deregister(registered_plane)
        assert not result.success

    def test_cancel_deregister_restores_active(self, sdk: KnowledgeSDK, active_plane: str):
        """Test cancel_deregister() restores ACTIVE state."""
        sdk.deregister(active_plane)
        result = sdk.cancel_deregister(active_plane)

        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.ACTIVE

    def test_deactivate_soft_deletes(self, sdk: KnowledgeSDK, active_plane: str):
        """Test deactivate() soft-deletes the plane."""
        sdk.deregister(active_plane)
        result = sdk.deactivate(active_plane)

        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.DEACTIVATED

    def test_archive_exports_to_cold(self, sdk: KnowledgeSDK, active_plane: str):
        """Test archive() exports to cold storage."""
        sdk.deregister(active_plane)
        sdk.deactivate(active_plane)
        result = sdk.archive(active_plane)

        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.ARCHIVED

    def test_purge_requires_approval(self, sdk: KnowledgeSDK, active_plane: str):
        """Test purge() requires explicit approval (GAP-087)."""
        sdk.deregister(active_plane)
        sdk.deactivate(active_plane)
        sdk.archive(active_plane)

        result = sdk.purge(active_plane, reason="GDPR request")

        # Should be blocked without approval
        assert not result.success

    def test_purge_succeeds_with_approval(self, sdk: KnowledgeSDK, active_plane: str):
        """Test purge() succeeds with approval."""
        sdk.deregister(active_plane)
        sdk.deactivate(active_plane)
        sdk.archive(active_plane)

        # Approve purge first
        sdk.approve_purge(active_plane, reason="GDPR request")

        result = sdk.purge(active_plane, reason="GDPR request")
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.PURGED

    def test_full_offboarding_flow(self, sdk: KnowledgeSDK, active_plane: str):
        """Test complete offboarding flow end-to-end."""
        # Deregister
        result = sdk.deregister(active_plane, reason="Decommissioning")
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.PENDING_DEACTIVATE

        # Deactivate
        result = sdk.deactivate(active_plane)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.DEACTIVATED

        # Archive
        result = sdk.archive(active_plane)
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.ARCHIVED

        # Approve purge
        result = sdk.approve_purge(active_plane, reason="Data retention expired")
        assert result.success

        # Purge
        result = sdk.purge(active_plane, reason="Data retention expired")
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.PURGED


# =============================================================================
# Section 5: Wait Semantics Tests (GAP-085)
# =============================================================================


class TestWaitSemantics:
    """Tests for GAP-085 Wait semantics."""

    def test_get_state(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test get_state() returns current state."""
        state = sdk.get_state(registered_plane)
        assert state == KnowledgePlaneLifecycleState.DRAFT

    def test_get_state_not_found(self, sdk: KnowledgeSDK):
        """Test get_state() returns None for nonexistent plane."""
        state = sdk.get_state("nonexistent")
        assert state is None

    def test_get_plane(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test get_plane() returns PlaneInfo."""
        info = sdk.get_plane(registered_plane)
        assert info is not None
        assert info.id == registered_plane
        assert info.state == KnowledgePlaneLifecycleState.DRAFT

    def test_get_plane_not_found(self, sdk: KnowledgeSDK):
        """Test get_plane() returns None for nonexistent plane."""
        info = sdk.get_plane("nonexistent")
        assert info is None

    def test_get_history(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        registered_plane: str,
    ):
        """Test get_history() returns state transitions."""
        sdk.verify(registered_plane)
        manager.complete_job(manager.get_plane(registered_plane).active_job_id, registered_plane, True)

        history = sdk.get_history(registered_plane)
        assert len(history) >= 1

    def test_get_audit_log(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test get_audit_log() returns audit events."""
        sdk.verify(registered_plane)

        log = sdk.get_audit_log(plane_id=registered_plane)
        assert len(log) >= 1

    def test_get_next_action(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test get_next_action() returns suggested action."""
        action = sdk.get_next_action(registered_plane)
        assert action == LifecycleAction.VERIFY

    def test_can_transition_to_valid(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test can_transition_to() for valid transition."""
        can = sdk.can_transition_to(
            registered_plane,
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
        )
        assert can is True

    def test_can_transition_to_invalid(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test can_transition_to() for invalid transition."""
        can = sdk.can_transition_to(
            registered_plane,
            KnowledgePlaneLifecycleState.ACTIVE,  # Cannot skip states
        )
        assert can is False

    @pytest.mark.asyncio
    async def test_wait_until_immediate(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test wait_until() when already at target state."""
        result = await sdk.wait_until(
            registered_plane,
            KnowledgePlaneLifecycleState.DRAFT,
        )
        assert result.success
        assert result.state == KnowledgePlaneLifecycleState.DRAFT

    @pytest.mark.asyncio
    async def test_wait_until_plane_not_found(self, sdk: KnowledgeSDK):
        """Test wait_until() for nonexistent plane."""
        result = await sdk.wait_until(
            "nonexistent",
            KnowledgePlaneLifecycleState.ACTIVE,
        )
        assert not result.success
        assert result.error_code == "PLANE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_wait_until_timeout(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test wait_until() timeout."""
        result = await sdk.wait_until(
            registered_plane,
            KnowledgePlaneLifecycleState.VERIFIED,
            options=WaitOptions(timeout=0.1, poll_interval=0.05),
        )
        assert not result.success
        assert result.error_code == "TIMEOUT"

    def test_wait_until_sync(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test wait_until_sync() synchronous wait."""
        result = sdk.wait_until_sync(
            registered_plane,
            KnowledgePlaneLifecycleState.DRAFT,
        )
        assert result.success

    def test_wait_until_sync_timeout(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test wait_until_sync() timeout."""
        result = sdk.wait_until_sync(
            registered_plane,
            KnowledgePlaneLifecycleState.VERIFIED,
            options=WaitOptions(timeout=0.1, poll_interval=0.05),
        )
        assert not result.success
        assert result.error_code == "TIMEOUT"


# =============================================================================
# Section 6: Policy Management Tests
# =============================================================================


class TestPolicyManagement:
    """Tests for policy management methods."""

    def test_bind_policy(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test bind_policy() adds policy to plane."""
        result = sdk.bind_policy(registered_plane, "policy-1")

        assert result.success
        info = sdk.get_plane(registered_plane)
        assert "policy-1" in info.bound_policies

    def test_bind_multiple_policies(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test bind_policy() can add multiple policies."""
        sdk.bind_policy(registered_plane, "policy-1")
        sdk.bind_policy(registered_plane, "policy-2")

        info = sdk.get_plane(registered_plane)
        assert "policy-1" in info.bound_policies
        assert "policy-2" in info.bound_policies

    def test_bind_policy_idempotent(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test bind_policy() is idempotent."""
        sdk.bind_policy(registered_plane, "policy-1")
        sdk.bind_policy(registered_plane, "policy-1")

        info = sdk.get_plane(registered_plane)
        assert info.bound_policies.count("policy-1") == 1

    def test_unbind_policy(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test unbind_policy() removes policy from plane."""
        sdk.bind_policy(registered_plane, "policy-1")
        result = sdk.unbind_policy(registered_plane, "policy-1")

        assert result.success
        info = sdk.get_plane(registered_plane)
        assert "policy-1" not in info.bound_policies

    def test_unbind_policy_not_found(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test unbind_policy() succeeds even if policy not bound."""
        result = sdk.unbind_policy(registered_plane, "nonexistent")
        assert result.success

    def test_approve_purge(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
        active_plane: str,
    ):
        """Test approve_purge() sets approval flag."""
        sdk.deregister(active_plane)
        sdk.deactivate(active_plane)
        sdk.archive(active_plane)

        result = sdk.approve_purge(active_plane, reason="GDPR request")

        assert result.success
        plane = manager.get_plane(active_plane)
        assert plane.metadata.get("purge_approved") is True

    def test_approve_purge_requires_actor(self, manager: KnowledgeLifecycleManager):
        """Test approve_purge() requires actor ID."""
        # SDK without actor_id
        sdk = KnowledgeSDK(tenant_id="test", actor_id=None, manager=manager)

        result = sdk.register(KnowledgePlaneConfig(name="Test"))
        result = sdk.approve_purge(result.plane_id, reason="Test")

        assert not result.success
        assert result.error_code == "ACTOR_REQUIRED"


# =============================================================================
# Section 7: Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_tenant_mismatch(self, manager: KnowledgeLifecycleManager):
        """Test operations fail with tenant mismatch."""
        sdk1 = KnowledgeSDK(tenant_id="tenant-1", manager=manager)
        sdk2 = KnowledgeSDK(tenant_id="tenant-2", manager=manager)

        result = sdk1.register(KnowledgePlaneConfig(name="Test"))
        plane_id = result.plane_id

        # Try to verify from different tenant
        result = sdk2.verify(plane_id)
        assert not result.success
        assert "mismatch" in result.message.lower() or "denied" in result.message.lower()

    def test_invalid_action_from_state(self, sdk: KnowledgeSDK, registered_plane: str):
        """Test invalid action from current state."""
        # Try to activate from DRAFT - should fail
        result = sdk.activate(registered_plane)
        assert not result.success

    def test_plane_not_found(self, sdk: KnowledgeSDK):
        """Test operations on nonexistent plane."""
        result = sdk.verify("nonexistent")
        assert not result.success
        assert "not found" in result.message.lower()

    def test_bind_policy_plane_not_found(self, sdk: KnowledgeSDK):
        """Test bind_policy() for nonexistent plane."""
        result = sdk.bind_policy("nonexistent", "policy-1")
        assert not result.success
        assert result.error_code == "BIND_FAILED"


# =============================================================================
# Section 8: Factory Tests
# =============================================================================


class TestFactory:
    """Tests for SDK factory function."""

    def test_create_knowledge_sdk(self):
        """Test create_knowledge_sdk() factory function."""
        reset_manager()
        sdk = create_knowledge_sdk("test-tenant", "test-actor")

        assert sdk is not None
        assert sdk._tenant_id == "test-tenant"
        assert sdk._actor_id == "test-actor"

    def test_create_knowledge_sdk_without_actor(self):
        """Test create_knowledge_sdk() without actor."""
        reset_manager()
        sdk = create_knowledge_sdk("test-tenant")

        assert sdk is not None
        assert sdk._actor_id is None


# =============================================================================
# Section 9: Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_register_and_query(self, sdk: KnowledgeSDK):
        """Test register and immediate query."""
        result = sdk.register(KnowledgePlaneConfig(
            name="Query Test",
            description="Testing query after register",
        ))

        assert result.success
        info = sdk.get_plane(result.plane_id)
        assert info.name == "Query Test"
        assert info.description == "Testing query after register"

    def test_multiple_planes_isolation(self, sdk: KnowledgeSDK):
        """Test multiple planes are isolated."""
        result1 = sdk.register(KnowledgePlaneConfig(name="Plane 1"))
        result2 = sdk.register(KnowledgePlaneConfig(name="Plane 2"))

        info1 = sdk.get_plane(result1.plane_id)
        info2 = sdk.get_plane(result2.plane_id)

        assert info1.id != info2.id
        assert info1.name == "Plane 1"
        assert info2.name == "Plane 2"

    def test_audit_trail_completeness(
        self,
        sdk: KnowledgeSDK,
        manager: KnowledgeLifecycleManager,
    ):
        """Test audit trail captures all transitions."""
        result = sdk.register(KnowledgePlaneConfig(name="Audit Test"))
        plane_id = result.plane_id

        sdk.verify(plane_id)
        manager.complete_job(manager.get_plane(plane_id).active_job_id, plane_id, True)

        log = sdk.get_audit_log(plane_id=plane_id)

        # Should have events for: register, verify, job_complete
        assert len(log) >= 2  # At least register and verify
        event_types = [e["event_type"] for e in log]
        assert "LIFECYCLE_TRANSITION" in event_types

    def test_concurrent_operations(self, manager: KnowledgeLifecycleManager):
        """Test concurrent SDK operations from multiple instances."""
        sdk1 = KnowledgeSDK(tenant_id="tenant-1", manager=manager)
        sdk2 = KnowledgeSDK(tenant_id="tenant-2", manager=manager)

        result1 = sdk1.register(KnowledgePlaneConfig(name="T1 Plane"))
        result2 = sdk2.register(KnowledgePlaneConfig(name="T2 Plane"))

        assert result1.success
        assert result2.success
        assert result1.plane_id != result2.plane_id

        # Verify isolation
        assert sdk1.get_state(result2.plane_id) is not None  # Can see other tenant's plane
        # But cannot operate on it
        verify_result = sdk1.verify(result2.plane_id)
        assert not verify_result.success  # Tenant mismatch
