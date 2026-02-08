# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Phase-9 Lifecycle Provider Unit Tests
# Callers: pytest, CI pipeline
# Allowed Imports: L4 (lifecycle), stdlib, pytest
# Forbidden Imports: L1, L2, L3
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)

"""
Phase-9 Tenant Lifecycle Provider Unit Tests

Tests for MockTenantLifecycleProvider and invariant enforcement.

Test Categories:
1. State enum semantics
2. Transition validity
3. Invariant enforcement (OFFBOARD-001 to OFFBOARD-010)
4. Actor restrictions
5. Observability integration
6. History/audit tracking
"""

import pytest
from datetime import datetime, timezone

from app.hoc.cus.account.L5_schemas.tenant_lifecycle_state import (
    TenantLifecycleState,
    LifecycleAction,
    VALID_TRANSITIONS,
    is_valid_transition,
    get_valid_transitions,
    get_action_for_transition,
)
from app.hoc.cus.hoc_spine.authority.lifecycle_provider import (
    ActorType,
    ActorContext,
    TransitionResult,
    MockTenantLifecycleProvider,
    get_lifecycle_provider,
    set_lifecycle_provider,
)


# ============================================================================
# STATE ENUM TESTS
# ============================================================================


class TestTenantLifecycleState:
    """Tests for TenantLifecycleState enum."""

    def test_state_values_are_monotonic(self):
        """State values should be monotonically increasing."""
        assert TenantLifecycleState.ACTIVE.value < TenantLifecycleState.SUSPENDED.value
        assert TenantLifecycleState.SUSPENDED.value < TenantLifecycleState.TERMINATED.value
        assert TenantLifecycleState.TERMINATED.value < TenantLifecycleState.ARCHIVED.value

    def test_active_allows_sdk_execution(self):
        """ACTIVE state allows SDK execution."""
        assert TenantLifecycleState.ACTIVE.allows_sdk_execution() is True

    def test_suspended_blocks_sdk_execution(self):
        """SUSPENDED state blocks SDK execution."""
        assert TenantLifecycleState.SUSPENDED.allows_sdk_execution() is False

    def test_terminated_blocks_sdk_execution(self):
        """TERMINATED state blocks SDK execution."""
        assert TenantLifecycleState.TERMINATED.allows_sdk_execution() is False

    def test_archived_blocks_sdk_execution(self):
        """ARCHIVED state blocks SDK execution."""
        assert TenantLifecycleState.ARCHIVED.allows_sdk_execution() is False

    def test_active_allows_writes(self):
        """ACTIVE state allows data writes."""
        assert TenantLifecycleState.ACTIVE.allows_writes() is True

    def test_suspended_blocks_writes(self):
        """SUSPENDED state blocks data writes."""
        assert TenantLifecycleState.SUSPENDED.allows_writes() is False

    def test_active_allows_reads(self):
        """ACTIVE state allows data reads."""
        assert TenantLifecycleState.ACTIVE.allows_reads() is True

    def test_suspended_allows_reads(self):
        """SUSPENDED state allows limited reads."""
        assert TenantLifecycleState.SUSPENDED.allows_reads() is True

    def test_terminated_blocks_reads(self):
        """TERMINATED state blocks data reads."""
        assert TenantLifecycleState.TERMINATED.allows_reads() is False

    def test_active_allows_new_api_keys(self):
        """ACTIVE state allows new API keys."""
        assert TenantLifecycleState.ACTIVE.allows_new_api_keys() is True

    def test_suspended_blocks_new_api_keys(self):
        """SUSPENDED state blocks new API keys."""
        assert TenantLifecycleState.SUSPENDED.allows_new_api_keys() is False

    def test_active_allows_token_refresh(self):
        """ACTIVE state allows token refresh."""
        assert TenantLifecycleState.ACTIVE.allows_token_refresh() is True

    def test_suspended_allows_token_refresh(self):
        """SUSPENDED state allows token refresh."""
        assert TenantLifecycleState.SUSPENDED.allows_token_refresh() is True

    def test_terminated_blocks_token_refresh(self):
        """TERMINATED state blocks token refresh (OFFBOARD-007)."""
        assert TenantLifecycleState.TERMINATED.allows_token_refresh() is False

    def test_terminated_is_terminal(self):
        """TERMINATED is a terminal state."""
        assert TenantLifecycleState.TERMINATED.is_terminal() is True

    def test_archived_is_terminal(self):
        """ARCHIVED is a terminal state."""
        assert TenantLifecycleState.ARCHIVED.is_terminal() is True

    def test_active_is_not_terminal(self):
        """ACTIVE is not a terminal state."""
        assert TenantLifecycleState.ACTIVE.is_terminal() is False

    def test_suspended_is_reversible(self):
        """SUSPENDED is the only reversible non-ACTIVE state."""
        assert TenantLifecycleState.SUSPENDED.is_reversible() is True
        assert TenantLifecycleState.ACTIVE.is_reversible() is False
        assert TenantLifecycleState.TERMINATED.is_reversible() is False
        assert TenantLifecycleState.ARCHIVED.is_reversible() is False


# ============================================================================
# TRANSITION VALIDITY TESTS
# ============================================================================


class TestTransitionValidity:
    """Tests for transition validity rules."""

    def test_offboard_001_active_to_suspended_valid(self):
        """OFFBOARD-001: ACTIVE -> SUSPENDED is valid."""
        assert is_valid_transition(
            TenantLifecycleState.ACTIVE,
            TenantLifecycleState.SUSPENDED,
        )

    def test_offboard_001_active_to_terminated_valid(self):
        """OFFBOARD-001: ACTIVE -> TERMINATED is valid."""
        assert is_valid_transition(
            TenantLifecycleState.ACTIVE,
            TenantLifecycleState.TERMINATED,
        )

    def test_offboard_001_suspended_to_active_valid(self):
        """OFFBOARD-001: SUSPENDED -> ACTIVE (resume) is valid."""
        assert is_valid_transition(
            TenantLifecycleState.SUSPENDED,
            TenantLifecycleState.ACTIVE,
        )

    def test_offboard_001_suspended_to_terminated_valid(self):
        """OFFBOARD-001: SUSPENDED -> TERMINATED is valid."""
        assert is_valid_transition(
            TenantLifecycleState.SUSPENDED,
            TenantLifecycleState.TERMINATED,
        )

    def test_offboard_001_terminated_to_archived_valid(self):
        """OFFBOARD-001: TERMINATED -> ARCHIVED is valid."""
        assert is_valid_transition(
            TenantLifecycleState.TERMINATED,
            TenantLifecycleState.ARCHIVED,
        )

    def test_offboard_002_terminated_to_active_invalid(self):
        """OFFBOARD-002: TERMINATED -> ACTIVE is INVALID (irreversible)."""
        assert not is_valid_transition(
            TenantLifecycleState.TERMINATED,
            TenantLifecycleState.ACTIVE,
        )

    def test_offboard_002_terminated_to_suspended_invalid(self):
        """OFFBOARD-002: TERMINATED -> SUSPENDED is INVALID."""
        assert not is_valid_transition(
            TenantLifecycleState.TERMINATED,
            TenantLifecycleState.SUSPENDED,
        )

    def test_offboard_003_active_to_archived_invalid(self):
        """OFFBOARD-003: ACTIVE -> ARCHIVED is INVALID (unreachable)."""
        assert not is_valid_transition(
            TenantLifecycleState.ACTIVE,
            TenantLifecycleState.ARCHIVED,
        )

    def test_offboard_003_suspended_to_archived_invalid(self):
        """OFFBOARD-003: SUSPENDED -> ARCHIVED is INVALID."""
        assert not is_valid_transition(
            TenantLifecycleState.SUSPENDED,
            TenantLifecycleState.ARCHIVED,
        )

    def test_archived_terminal_terminal(self):
        """ARCHIVED is terminal-terminal (no exits)."""
        valid = get_valid_transitions(TenantLifecycleState.ARCHIVED)
        assert len(valid) == 0

    def test_get_action_for_transition(self):
        """Action names match transitions."""
        assert get_action_for_transition(
            TenantLifecycleState.ACTIVE,
            TenantLifecycleState.SUSPENDED,
        ) == LifecycleAction.SUSPEND

        assert get_action_for_transition(
            TenantLifecycleState.SUSPENDED,
            TenantLifecycleState.ACTIVE,
        ) == LifecycleAction.RESUME

        assert get_action_for_transition(
            TenantLifecycleState.ACTIVE,
            TenantLifecycleState.TERMINATED,
        ) == LifecycleAction.TERMINATE

        assert get_action_for_transition(
            TenantLifecycleState.TERMINATED,
            TenantLifecycleState.ARCHIVED,
        ) == LifecycleAction.ARCHIVE


# ============================================================================
# MOCK PROVIDER TESTS
# ============================================================================


class TestMockTenantLifecycleProvider:
    """Tests for MockTenantLifecycleProvider."""

    @pytest.fixture
    def provider(self):
        """Fresh provider for each test."""
        return MockTenantLifecycleProvider()

    @pytest.fixture
    def founder_actor(self):
        """Founder actor context."""
        return ActorContext(
            actor_type=ActorType.FOUNDER,
            actor_id="founder_123",
            reason="test",
        )

    @pytest.fixture
    def system_actor(self):
        """System actor context."""
        return ActorContext(
            actor_type=ActorType.SYSTEM,
            actor_id="system",
            reason="automated",
        )

    @pytest.fixture
    def customer_actor(self):
        """Customer actor context."""
        return ActorContext(
            actor_type=ActorType.CUSTOMER,
            actor_id="user_456",
            reason="requested",
        )

    def test_default_state_is_active(self, provider):
        """Unknown tenants default to ACTIVE."""
        state = provider.get_state("unknown_tenant")
        assert state == TenantLifecycleState.ACTIVE

    def test_suspend_from_active(self, provider, founder_actor):
        """Suspend transitions ACTIVE -> SUSPENDED."""
        result = provider.suspend("t_123", founder_actor)

        assert result.success is True
        assert result.from_state == TenantLifecycleState.ACTIVE
        assert result.to_state == TenantLifecycleState.SUSPENDED
        assert result.action == LifecycleAction.SUSPEND
        assert provider.get_state("t_123") == TenantLifecycleState.SUSPENDED

    def test_resume_from_suspended(self, provider, founder_actor):
        """Resume transitions SUSPENDED -> ACTIVE."""
        provider.set_state("t_123", TenantLifecycleState.SUSPENDED)

        result = provider.resume("t_123", founder_actor)

        assert result.success is True
        assert result.from_state == TenantLifecycleState.SUSPENDED
        assert result.to_state == TenantLifecycleState.ACTIVE
        assert result.action == LifecycleAction.RESUME
        assert provider.get_state("t_123") == TenantLifecycleState.ACTIVE

    def test_terminate_from_active(self, provider, founder_actor):
        """Terminate transitions ACTIVE -> TERMINATED."""
        result = provider.terminate("t_123", founder_actor)

        assert result.success is True
        assert result.from_state == TenantLifecycleState.ACTIVE
        assert result.to_state == TenantLifecycleState.TERMINATED
        assert result.action == LifecycleAction.TERMINATE
        assert provider.get_state("t_123") == TenantLifecycleState.TERMINATED

    def test_terminate_from_suspended(self, provider, founder_actor):
        """Terminate transitions SUSPENDED -> TERMINATED."""
        provider.set_state("t_123", TenantLifecycleState.SUSPENDED)

        result = provider.terminate("t_123", founder_actor)

        assert result.success is True
        assert result.from_state == TenantLifecycleState.SUSPENDED
        assert result.to_state == TenantLifecycleState.TERMINATED

    def test_archive_from_terminated(self, provider, system_actor):
        """Archive transitions TERMINATED -> ARCHIVED."""
        provider.set_state("t_123", TenantLifecycleState.TERMINATED)

        result = provider.archive("t_123", system_actor)

        assert result.success is True
        assert result.from_state == TenantLifecycleState.TERMINATED
        assert result.to_state == TenantLifecycleState.ARCHIVED
        assert result.action == LifecycleAction.ARCHIVE
        assert provider.get_state("t_123") == TenantLifecycleState.ARCHIVED


# ============================================================================
# INVARIANT ENFORCEMENT TESTS
# ============================================================================


class TestInvariantEnforcement:
    """Tests for OFFBOARD invariant enforcement."""

    @pytest.fixture
    def provider(self):
        return MockTenantLifecycleProvider()

    @pytest.fixture
    def founder_actor(self):
        return ActorContext(
            actor_type=ActorType.FOUNDER,
            actor_id="founder_123",
            reason="test",
        )

    @pytest.fixture
    def customer_actor(self):
        return ActorContext(
            actor_type=ActorType.CUSTOMER,
            actor_id="user_456",
            reason="requested",
        )

    def test_offboard_002_terminated_is_irreversible(self, provider, founder_actor):
        """OFFBOARD-002: Cannot resume or suspend a TERMINATED tenant."""
        provider.set_state("t_123", TenantLifecycleState.TERMINATED)

        result = provider.resume("t_123", founder_actor)
        assert result.success is False
        assert "OFFBOARD-002" in result.error
        assert provider.get_state("t_123") == TenantLifecycleState.TERMINATED

        result = provider.suspend("t_123", founder_actor)
        assert result.success is False
        assert provider.get_state("t_123") == TenantLifecycleState.TERMINATED

    def test_offboard_003_archived_unreachable_from_active(self, provider, founder_actor):
        """OFFBOARD-003: Cannot archive directly from ACTIVE."""
        result = provider.archive("t_123", founder_actor)

        assert result.success is False
        assert "OFFBOARD-003" in result.error or "Invalid transition" in result.error
        assert provider.get_state("t_123") == TenantLifecycleState.ACTIVE

    def test_offboard_004_customer_cannot_mutate(self, provider, customer_actor):
        """OFFBOARD-004: Customers cannot initiate lifecycle mutations."""
        result = provider.suspend("t_123", customer_actor)

        assert result.success is False
        assert "OFFBOARD-004" in result.error
        assert provider.get_state("t_123") == TenantLifecycleState.ACTIVE

    def test_offboard_004_customer_cannot_terminate(self, provider, customer_actor):
        """OFFBOARD-004: Customers cannot terminate tenants."""
        result = provider.terminate("t_123", customer_actor)

        assert result.success is False
        assert "OFFBOARD-004" in result.error

    def test_archived_cannot_be_exited(self, provider, founder_actor):
        """ARCHIVED is terminal-terminal."""
        provider.set_state("t_123", TenantLifecycleState.ARCHIVED)

        result = provider.resume("t_123", founder_actor)
        assert result.success is False

        result = provider.terminate("t_123", founder_actor)
        assert result.success is False

        assert provider.get_state("t_123") == TenantLifecycleState.ARCHIVED


# ============================================================================
# CALLBACK INTEGRATION TESTS
# ============================================================================


class TestCallbackIntegration:
    """Tests for callback integration (revocation, blocking, observability)."""

    def test_offboard_005_api_key_revocation_on_terminate(self):
        """OFFBOARD-005: API keys revoked on TERMINATED."""
        revoked_count = 0

        def revoke_callback(tenant_id: str) -> int:
            nonlocal revoked_count
            revoked_count = 5  # Simulate 5 keys revoked
            return 5

        provider = MockTenantLifecycleProvider(
            api_key_revocation_callback=revoke_callback
        )
        founder = ActorContext(ActorType.FOUNDER, "f_1", "test")

        result = provider.terminate("t_123", founder)

        assert result.success is True
        assert result.revoked_api_keys == 5
        assert revoked_count == 5

    def test_offboard_006_worker_blocking_on_terminate(self):
        """OFFBOARD-006: Workers blocked on TERMINATED."""
        blocked_count = 0

        def block_callback(tenant_id: str) -> int:
            nonlocal blocked_count
            blocked_count = 3
            return 3

        provider = MockTenantLifecycleProvider(
            worker_blocking_callback=block_callback
        )
        founder = ActorContext(ActorType.FOUNDER, "f_1", "test")

        result = provider.terminate("t_123", founder)

        assert result.success is True
        assert result.blocked_workers == 3

    def test_offboard_008_observability_event_emitted(self):
        """OFFBOARD-008: Lifecycle transitions emit observability events."""
        events = []

        def event_callback(event: dict):
            events.append(event)

        provider = MockTenantLifecycleProvider(
            observability_callback=event_callback
        )
        founder = ActorContext(ActorType.FOUNDER, "f_1", "contract_ended")

        provider.terminate("t_123", founder)

        assert len(events) == 1
        event = events[0]
        assert event["event_type"] == "tenant_lifecycle_transition"
        assert event["tenant_id"] == "t_123"
        assert event["from_state"] == "ACTIVE"
        assert event["to_state"] == "TERMINATED"
        assert event["actor_type"] == "FOUNDER"
        assert event["reason"] == "contract_ended"
        assert event["success"] is True

    def test_offboard_009_observability_failure_non_blocking(self):
        """OFFBOARD-009: Observability failure doesn't block transition."""

        def failing_callback(event: dict):
            raise RuntimeError("Observability system down")

        provider = MockTenantLifecycleProvider(
            observability_callback=failing_callback
        )
        founder = ActorContext(ActorType.FOUNDER, "f_1", "test")

        # Should succeed despite observability failure
        result = provider.terminate("t_123", founder)

        assert result.success is True
        assert provider.get_state("t_123") == TenantLifecycleState.TERMINATED


# ============================================================================
# AUDIT / HISTORY TESTS
# ============================================================================


class TestAuditHistory:
    """Tests for transition history (OFFBOARD-010)."""

    @pytest.fixture
    def provider(self):
        return MockTenantLifecycleProvider()

    @pytest.fixture
    def founder_actor(self):
        return ActorContext(ActorType.FOUNDER, "f_1", "test")

    def test_offboard_010_transitions_recorded(self, provider, founder_actor):
        """OFFBOARD-010: All transitions are recorded in history."""
        provider.suspend("t_123", founder_actor)
        provider.resume("t_123", founder_actor)
        provider.terminate("t_123", founder_actor)

        history = provider.get_history("t_123")

        assert len(history) == 3
        assert history[0].action == LifecycleAction.SUSPEND
        assert history[1].action == LifecycleAction.RESUME
        assert history[2].action == LifecycleAction.TERMINATE

    def test_failed_transitions_recorded(self, provider, founder_actor):
        """Failed transitions are also recorded."""
        provider.set_state("t_123", TenantLifecycleState.TERMINATED)
        provider.resume("t_123", founder_actor)  # Should fail

        history = provider.get_history("t_123")

        assert len(history) == 1
        assert history[0].success is False
        assert history[0].error is not None

    def test_history_includes_actor_context(self, provider, founder_actor):
        """History includes full actor context."""
        provider.terminate("t_123", founder_actor)

        history = provider.get_history("t_123")

        assert history[0].actor.actor_type == ActorType.FOUNDER
        assert history[0].actor.actor_id == "f_1"
        assert history[0].actor.reason == "test"

    def test_history_per_tenant(self, provider, founder_actor):
        """History is tenant-scoped."""
        provider.suspend("t_123", founder_actor)
        provider.terminate("t_456", founder_actor)

        history_123 = provider.get_history("t_123")
        history_456 = provider.get_history("t_456")

        assert len(history_123) == 1
        assert history_123[0].tenant_id == "t_123"
        assert len(history_456) == 1
        assert history_456[0].tenant_id == "t_456"


# ============================================================================
# PERMISSION CHECK TESTS
# ============================================================================


class TestPermissionChecks:
    """Tests for permission check methods."""

    @pytest.fixture
    def provider(self):
        return MockTenantLifecycleProvider()

    def test_allows_sdk_execution_active(self, provider):
        """ACTIVE allows SDK execution."""
        assert provider.allows_sdk_execution("t_123") is True

    def test_allows_sdk_execution_suspended(self, provider):
        """SUSPENDED blocks SDK execution."""
        provider.set_state("t_123", TenantLifecycleState.SUSPENDED)
        assert provider.allows_sdk_execution("t_123") is False

    def test_allows_sdk_execution_terminated(self, provider):
        """TERMINATED blocks SDK execution."""
        provider.set_state("t_123", TenantLifecycleState.TERMINATED)
        assert provider.allows_sdk_execution("t_123") is False

    def test_allows_writes_active(self, provider):
        """ACTIVE allows writes."""
        assert provider.allows_writes("t_123") is True

    def test_allows_writes_suspended(self, provider):
        """SUSPENDED blocks writes."""
        provider.set_state("t_123", TenantLifecycleState.SUSPENDED)
        assert provider.allows_writes("t_123") is False

    def test_allows_new_api_keys_active(self, provider):
        """ACTIVE allows new API keys."""
        assert provider.allows_new_api_keys("t_123") is True

    def test_allows_new_api_keys_suspended(self, provider):
        """SUSPENDED blocks new API keys."""
        provider.set_state("t_123", TenantLifecycleState.SUSPENDED)
        assert provider.allows_new_api_keys("t_123") is False


# ============================================================================
# GLOBAL PROVIDER TESTS
# ============================================================================


class TestGlobalProvider:
    """Tests for global provider getter/setter."""

    def test_get_lifecycle_provider_returns_mock(self):
        """Default provider is MockTenantLifecycleProvider."""
        provider = get_lifecycle_provider()
        assert isinstance(provider, MockTenantLifecycleProvider)

    def test_set_lifecycle_provider(self):
        """Can swap provider."""
        custom = MockTenantLifecycleProvider()
        set_lifecycle_provider(custom)
        assert get_lifecycle_provider() is custom

        # Reset for other tests
        set_lifecycle_provider(MockTenantLifecycleProvider())


# ============================================================================
# TRANSITION RESULT TESTS
# ============================================================================


class TestTransitionResult:
    """Tests for TransitionResult dataclass."""

    def test_to_audit_record(self):
        """TransitionResult converts to audit record."""
        result = TransitionResult(
            success=True,
            from_state=TenantLifecycleState.ACTIVE,
            to_state=TenantLifecycleState.TERMINATED,
            action=LifecycleAction.TERMINATE,
            revoked_api_keys=5,
            blocked_workers=2,
        )

        record = result.to_audit_record()

        assert record["event_type"] == "tenant_lifecycle_transition"
        assert record["success"] is True
        assert record["from_state"] == "ACTIVE"
        assert record["to_state"] == "TERMINATED"
        assert record["action"] == "terminate_tenant"
        assert record["revoked_api_keys"] == 5
        assert record["blocked_workers"] == 2
        assert "timestamp" in record
