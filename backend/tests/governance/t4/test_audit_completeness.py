# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, manual
#   Execution: sync
# Role: T4 Audit Completeness Tests (GAP-088)
# Callers: pytest, CI
# Allowed Imports: L4 (models, services)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: GAP-088, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15.5

"""
T4 Audit Completeness Tests (GAP-088)

These tests verify that lifecycle audit events are complete and immutable:

1. Every transition emits exactly one audit event
2. Every block (failed transition) emits exactly one event
3. Audit events have correct structure and timestamps
4. Audit history is append-only (immutable)
5. Custom audit sinks receive all events

Test Count Target: ~100 tests

INVARIANTS UNDER TEST:
- LIFECYCLE-005: Every transition emits audit event
- MANAGER-002: No transition without audit event

AUDIT EVENT TYPES:
- TRANSITION: Successful state change
- BLOCKED: Failed state change (gate or state machine)
- ROLLBACK: Recovery from failure
- PURGE_APPROVED: Explicit purge approval
- JOB_STARTED: Async job started
- JOB_COMPLETED: Async job succeeded
- JOB_FAILED: Async job failed
"""

import pytest
from datetime import datetime, timezone
from typing import List

from app.models.knowledge_lifecycle import (
    KnowledgePlaneLifecycleState,
    LifecycleAction,
)
from app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager import (
    KnowledgeLifecycleManager,
    TransitionRequest,
    GateResult,
    LifecycleAuditEvent,
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
def registered_plane(manager: KnowledgeLifecycleManager) -> str:
    """Create and return a registered knowledge plane ID."""
    response = manager.handle_transition(TransitionRequest(
        plane_id="new",
        tenant_id="tenant-123",
        action=LifecycleAction.REGISTER,
        actor_id="user-456",
    ))
    return response.plane_id


@pytest.fixture
def event_collector() -> List[LifecycleAuditEvent]:
    """Create an event collector list."""
    return []


@pytest.fixture
def manager_with_collector(event_collector: List[LifecycleAuditEvent]) -> KnowledgeLifecycleManager:
    """Create manager with custom audit sink that collects events."""
    reset_manager()

    def collector_sink(event: LifecycleAuditEvent):
        event_collector.append(event)

    return KnowledgeLifecycleManager(audit_sink=collector_sink)


# =============================================================================
# Every Transition Emits Exactly One Event (LIFECYCLE-005)
# =============================================================================


class TestTransitionEmitsEvent:
    """Tests that every successful transition emits exactly one audit event."""

    def test_register_emits_transition_event(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """REGISTER emits exactly one TRANSITION event."""
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            actor_id="user-456",
        ))

        assert len(event_collector) == 1
        assert event_collector[0].event_type == LifecycleAuditEventType.TRANSITION

    def test_verify_emits_transition_event(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """VERIFY emits exactly one TRANSITION event."""
        response = manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        event_collector.clear()

        manager_with_collector.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert len(event_collector) == 1
        assert event_collector[0].event_type == LifecycleAuditEventType.TRANSITION

    def test_multiple_transitions_emit_multiple_events(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Multiple transitions emit one event each."""
        response = manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        # Should have exactly 2 events (REGISTER + VERIFY)
        assert len(event_collector) == 2
        assert all(e.event_type == LifecycleAuditEventType.TRANSITION for e in event_collector)


# =============================================================================
# Every Block Emits Exactly One Event
# =============================================================================


class TestBlockEmitsEvent:
    """Tests that every blocked transition emits exactly one audit event."""

    def test_invalid_action_emits_blocked_event(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Invalid action emits BLOCKED event."""
        response = manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        event_collector.clear()

        manager_with_collector.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid from DRAFT
        ))

        assert len(event_collector) == 1
        assert event_collector[0].event_type == LifecycleAuditEventType.BLOCKED

    def test_policy_gate_block_emits_blocked_event(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Policy gate block emits BLOCKED event."""
        response = manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager_with_collector.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.PENDING_ACTIVATE
        event_collector.clear()

        # Attempt ACTIVATE without policy (will be blocked)
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.ACTIVATE,
        ))

        assert len(event_collector) == 1
        assert event_collector[0].event_type == LifecycleAuditEventType.BLOCKED


# =============================================================================
# Audit Event Structure
# =============================================================================


class TestAuditEventStructure:
    """Tests for audit event structure and content."""

    def test_transition_event_has_required_fields(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Transition event has all required fields."""
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            actor_id="user-456",
        ))

        event = event_collector[0]
        assert event.event_id is not None
        assert event.event_id.startswith("evt_")
        assert event.event_type == LifecycleAuditEventType.TRANSITION
        assert event.plane_id is not None
        assert event.tenant_id == "tenant-123"
        assert event.timestamp is not None
        assert event.actor_id == "user-456"
        assert event.action == LifecycleAction.REGISTER

    def test_transition_event_has_state_info(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Transition event includes from_state and to_state."""
        response = manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        event_collector.clear()

        manager_with_collector.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        event = event_collector[0]
        assert event.from_state == KnowledgePlaneLifecycleState.DRAFT
        assert event.to_state == KnowledgePlaneLifecycleState.PENDING_VERIFY

    def test_blocked_event_has_reason(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Blocked event includes reason."""
        response = manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        event_collector.clear()

        manager_with_collector.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,
        ))

        event = event_collector[0]
        assert event.reason is not None
        assert len(event.reason) > 0

    def test_event_timestamp_is_utc(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Event timestamp is timezone-aware UTC."""
        before = datetime.now(timezone.utc)

        manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        after = datetime.now(timezone.utc)

        event = event_collector[0]
        assert event.timestamp.tzinfo is not None
        assert before <= event.timestamp <= after

    def test_event_to_dict(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Event can be converted to dictionary."""
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            actor_id="user-456",
        ))

        data = event_collector[0].to_dict()
        assert isinstance(data, dict)
        assert data["event_id"].startswith("evt_")
        assert data["event_type"] == "LIFECYCLE_TRANSITION"
        assert data["tenant_id"] == "tenant-123"
        assert data["actor_id"] == "user-456"


# =============================================================================
# Audit Log Query
# =============================================================================


class TestAuditLogQuery:
    """Tests for audit log query methods."""

    def test_get_audit_log_returns_all_events(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """get_audit_log returns all events."""
        # Perform some transitions
        manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        events = manager.get_audit_log()
        assert len(events) >= 2  # REGISTER + VERIFY

    def test_filter_by_plane_id(
        self, manager: KnowledgeLifecycleManager
    ):
        """get_audit_log filters by plane_id."""
        # Create two planes
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

        # Query for plane1 only
        events = manager.get_audit_log(plane_id=response1.plane_id)
        assert len(events) == 1
        assert all(e.plane_id == response1.plane_id for e in events)

    def test_filter_by_tenant_id(
        self, manager: KnowledgeLifecycleManager
    ):
        """get_audit_log filters by tenant_id."""
        # Create planes for different tenants
        manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-A",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-B",
            action=LifecycleAction.REGISTER,
        ))

        # Query for tenant-A only
        events = manager.get_audit_log(tenant_id="tenant-A")
        assert len(events) == 1
        assert all(e.tenant_id == "tenant-A" for e in events)

    def test_filter_by_event_type(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """get_audit_log filters by event_type."""
        # Cause a blocked transition
        manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid
        ))

        # Query for BLOCKED events only
        events = manager.get_audit_log(event_type=LifecycleAuditEventType.BLOCKED)
        assert len(events) >= 1
        assert all(e.event_type == LifecycleAuditEventType.BLOCKED for e in events)

    def test_combined_filters(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """get_audit_log supports combined filters."""
        # Query with multiple filters
        events = manager.get_audit_log(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            event_type=LifecycleAuditEventType.TRANSITION,
        )

        assert all(e.plane_id == registered_plane for e in events)
        assert all(e.tenant_id == "tenant-123" for e in events)
        assert all(e.event_type == LifecycleAuditEventType.TRANSITION for e in events)


# =============================================================================
# Audit History Immutability
# =============================================================================


class TestAuditHistoryImmutability:
    """Tests that audit history is append-only (immutable)."""

    def test_audit_log_grows_monotonically(
        self, manager: KnowledgeLifecycleManager
    ):
        """Audit log only grows, never shrinks."""
        counts = []

        # Perform several operations
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        counts.append(len(manager.get_audit_log()))

        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))
        counts.append(len(manager.get_audit_log()))

        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid - blocked
        ))
        counts.append(len(manager.get_audit_log()))

        # Each count should be >= previous
        for i in range(1, len(counts)):
            assert counts[i] >= counts[i - 1], "Audit log should never shrink"

    def test_events_have_unique_ids(
        self, manager: KnowledgeLifecycleManager
    ):
        """Each event has a unique ID."""
        # Perform several operations
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
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid
        ))

        events = manager.get_audit_log()
        event_ids = [e.event_id for e in events]
        assert len(event_ids) == len(set(event_ids)), "Event IDs should be unique"

    def test_event_timestamps_are_ordered(
        self, manager: KnowledgeLifecycleManager
    ):
        """Events have non-decreasing timestamps."""
        # Perform several operations
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

        events = manager.get_audit_log()
        for i in range(1, len(events)):
            assert events[i].timestamp >= events[i - 1].timestamp, (
                "Event timestamps should be non-decreasing"
            )


# =============================================================================
# Special Audit Events
# =============================================================================


class TestSpecialAuditEvents:
    """Tests for special audit event types."""

    def test_purge_approval_emits_event(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """approve_purge emits PURGE_APPROVED event."""
        response = manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager_with_collector.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.ARCHIVED
        event_collector.clear()

        manager_with_collector.approve_purge(plane.id, "admin-user")

        assert len(event_collector) == 1
        assert event_collector[0].event_type == LifecycleAuditEventType.PURGE_APPROVED
        assert event_collector[0].actor_id == "admin-user"

    def test_registration_event_has_no_from_state(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Registration event has None for from_state."""
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        event = event_collector[0]
        assert event.from_state is None
        assert event.to_state == KnowledgePlaneLifecycleState.DRAFT


# =============================================================================
# Custom Audit Sink
# =============================================================================


class TestCustomAuditSink:
    """Tests for custom audit sink integration."""

    def test_set_audit_sink_replaces_sink(self):
        """set_audit_sink replaces the existing sink."""
        manager = KnowledgeLifecycleManager()

        collected = []
        def custom_sink(event):
            collected.append(event)

        manager.set_audit_sink(custom_sink)

        manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        assert len(collected) == 1

    def test_audit_sink_receives_all_event_types(self):
        """Custom sink receives all event types."""
        event_types = set()

        def collecting_sink(event):
            event_types.add(event.event_type)

        manager = KnowledgeLifecycleManager(audit_sink=collecting_sink)

        # TRANSITION event
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        # BLOCKED event
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.PURGE,  # Invalid
        ))

        # PURGE_APPROVED event
        plane = manager.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.ARCHIVED
        manager.approve_purge(plane.id, "admin")

        assert LifecycleAuditEventType.TRANSITION in event_types
        assert LifecycleAuditEventType.BLOCKED in event_types
        assert LifecycleAuditEventType.PURGE_APPROVED in event_types


# =============================================================================
# Audit Event Metadata
# =============================================================================


class TestAuditEventMetadata:
    """Tests for audit event metadata handling."""

    def test_event_preserves_request_metadata(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Event preserves metadata from request."""
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            metadata={"custom_key": "custom_value"},
        ))

        event = event_collector[0]
        assert event.metadata.get("custom_key") == "custom_value"

    def test_event_preserves_reason(
        self, manager_with_collector: KnowledgeLifecycleManager,
        event_collector: List[LifecycleAuditEvent],
    ):
        """Event preserves reason from request."""
        manager_with_collector.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            reason="Initial registration for testing",
        ))

        event = event_collector[0]
        assert event.reason == "Initial registration for testing"


# =============================================================================
# Plane State History
# =============================================================================


class TestPlaneStateHistory:
    """Tests for plane state history (separate from audit log)."""

    def test_plane_records_state_history(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Plane maintains state change history."""
        manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
            actor_id="user-456",
        ))

        history = manager.get_history(registered_plane)
        assert len(history) >= 1
        last_entry = history[-1]
        assert last_entry["from_state"] == "DRAFT"
        assert last_entry["to_state"] == "PENDING_VERIFY"
        assert last_entry["actor_id"] == "user-456"

    def test_plane_history_has_timestamps(
        self, manager: KnowledgeLifecycleManager, registered_plane: str
    ):
        """Plane history entries have timestamps."""
        manager.handle_transition(TransitionRequest(
            plane_id=registered_plane,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        history = manager.get_history(registered_plane)
        assert "timestamp" in history[-1]
