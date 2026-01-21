# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Reference: GAP-019 (Alert → Log Linking)

"""
Tests for GAP-019: Alert → Log Linking

Tests the alert-to-log linking service for explicit
correlation between alerts and run execution logs.
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.services.logging import (
    AlertLogLink,
    AlertLogLinker,
    AlertLogLinkError,
    AlertLogLinkResponse,
    AlertLogLinkStatus,
    AlertLogLinkType,
    create_alert_log_link,
    get_alerts_for_run,
    get_logs_for_alert,
)
from app.services.logging.alert_log_linker import (
    _reset_alert_log_linker,
    get_alert_log_linker,
)


class TestAlertLogLinkImports:
    """Test that all exports are importable."""

    def test_alert_log_link_type_import(self):
        """Verify AlertLogLinkType enum is importable."""
        assert AlertLogLinkType is not None
        assert hasattr(AlertLogLinkType, "THRESHOLD_NEAR")
        assert hasattr(AlertLogLinkType, "THRESHOLD_BREACH")
        assert hasattr(AlertLogLinkType, "INCIDENT_CREATED")

    def test_alert_log_link_status_import(self):
        """Verify AlertLogLinkStatus enum is importable."""
        assert AlertLogLinkStatus is not None
        assert hasattr(AlertLogLinkStatus, "ACTIVE")
        assert hasattr(AlertLogLinkStatus, "EXPIRED")
        assert hasattr(AlertLogLinkStatus, "ARCHIVED")

    def test_alert_log_link_import(self):
        """Verify AlertLogLink is importable."""
        assert AlertLogLink is not None

    def test_alert_log_linker_import(self):
        """Verify AlertLogLinker is importable."""
        assert AlertLogLinker is not None

    def test_alert_log_link_error_import(self):
        """Verify AlertLogLinkError is importable."""
        assert AlertLogLinkError is not None

    def test_helper_functions_import(self):
        """Verify helper functions are importable."""
        assert create_alert_log_link is not None
        assert get_alerts_for_run is not None
        assert get_logs_for_alert is not None


class TestAlertLogLinkTypeEnum:
    """Test AlertLogLinkType enum values."""

    def test_all_link_types_defined(self):
        """Verify all expected link types are defined."""
        types = list(AlertLogLinkType)
        assert len(types) >= 5
        assert AlertLogLinkType.THRESHOLD_NEAR in types
        assert AlertLogLinkType.THRESHOLD_BREACH in types
        assert AlertLogLinkType.INCIDENT_CREATED in types

    def test_link_type_string_values(self):
        """Verify link type enum string values."""
        assert AlertLogLinkType.THRESHOLD_NEAR.value == "threshold_near"
        assert AlertLogLinkType.THRESHOLD_BREACH.value == "threshold_breach"
        assert AlertLogLinkType.INCIDENT_CREATED.value == "incident_created"


class TestAlertLogLinkStatusEnum:
    """Test AlertLogLinkStatus enum values."""

    def test_all_statuses_defined(self):
        """Verify all expected statuses are defined."""
        statuses = list(AlertLogLinkStatus)
        assert len(statuses) >= 3
        assert AlertLogLinkStatus.ACTIVE in statuses
        assert AlertLogLinkStatus.EXPIRED in statuses
        assert AlertLogLinkStatus.ARCHIVED in statuses

    def test_status_string_values(self):
        """Verify status enum string values."""
        assert AlertLogLinkStatus.ACTIVE.value == "active"
        assert AlertLogLinkStatus.EXPIRED.value == "expired"
        assert AlertLogLinkStatus.ARCHIVED.value == "archived"


class TestAlertLogLink:
    """Test AlertLogLink dataclass."""

    def test_link_creation(self):
        """Test creating an alert log link."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
            step_indices=[10, 11, 12],
        )
        assert link.link_id == "link-123"
        assert link.link_type == AlertLogLinkType.THRESHOLD_BREACH
        assert link.status == AlertLogLinkStatus.ACTIVE
        assert link.step_indices == [10, 11, 12]

    def test_link_default_values(self):
        """Test link default values."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
        )
        assert link.log_entry_ids == []
        assert link.step_indices == []
        assert link.access_count == 0
        assert link.created_by == "system"

    def test_is_valid_active(self):
        """Test is_valid returns True for active link."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        assert link.is_valid() is True

    def test_is_valid_expired_status(self):
        """Test is_valid returns False for expired status."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.EXPIRED,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
        )
        assert link.is_valid() is False

    def test_is_valid_past_expiration(self):
        """Test is_valid returns False for past expiration."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert link.is_valid() is False

    def test_record_access(self):
        """Test recording access updates counters."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
        )
        assert link.access_count == 0
        assert link.last_accessed_at is None

        link.record_access()

        assert link.access_count == 1
        assert link.last_accessed_at is not None

    def test_expire(self):
        """Test expiring a link."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
        )
        link.expire()
        assert link.status == AlertLogLinkStatus.EXPIRED

    def test_archive(self):
        """Test archiving a link."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
        )
        link.archive()
        assert link.status == AlertLogLinkStatus.ARCHIVED

    def test_to_dict(self):
        """Test link serialization."""
        link = AlertLogLink(
            link_id="link-123",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id="alert-456",
            alert_timestamp=datetime.now(timezone.utc),
            run_id="run-789",
            tenant_id="tenant-1",
            step_indices=[10, 11],
            metric_name="cost",
            metric_value=150.0,
            threshold_value=100.0,
        )
        data = link.to_dict()
        assert data["link_id"] == "link-123"
        assert data["link_type"] == "threshold_breach"
        assert data["status"] == "active"
        assert data["step_indices"] == [10, 11]
        assert data["metric_name"] == "cost"
        assert data["metric_value"] == 150.0


class TestAlertLogLinkError:
    """Test AlertLogLinkError exception."""

    def test_error_creation(self):
        """Test creating a link error."""
        error = AlertLogLinkError(
            message="Link creation failed",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            alert_id="alert-123",
            run_id="run-456",
        )
        assert str(error) == "Link creation failed"
        assert error.link_type == AlertLogLinkType.THRESHOLD_BREACH
        assert error.alert_id == "alert-123"
        assert error.run_id == "run-456"

    def test_error_to_dict(self):
        """Test error serialization."""
        error = AlertLogLinkError(
            message="Link creation failed",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        data = error.to_dict()
        assert data["error"] == "AlertLogLinkError"
        assert data["link_type"] == "threshold_breach"


class TestAlertLogLinker:
    """Test AlertLogLinker service class."""

    def setup_method(self):
        """Reset linker before each test."""
        _reset_alert_log_linker()

    def test_linker_creation(self):
        """Test creating linker."""
        linker = AlertLogLinker()
        assert linker is not None

    def test_create_link(self):
        """Test creating a link."""
        linker = AlertLogLinker()
        link = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            step_indices=[10, 11, 12],
        )
        assert link.alert_id == "alert-123"
        assert link.run_id == "run-456"
        assert link.link_type == AlertLogLinkType.THRESHOLD_BREACH
        assert link.step_indices == [10, 11, 12]
        assert link.status == AlertLogLinkStatus.ACTIVE

    def test_create_link_with_metadata(self):
        """Test creating a link with full metadata."""
        linker = AlertLogLinker()
        link = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            trace_id="trace-789",
            policy_id="policy-1",
            metric_name="cost",
            metric_value=150.0,
            threshold_value=100.0,
            action_taken="terminate",
        )
        assert link.trace_id == "trace-789"
        assert link.policy_id == "policy-1"
        assert link.metric_name == "cost"
        assert link.metric_value == 150.0
        assert link.action_taken == "terminate"

    def test_create_link_max_per_run(self):
        """Test max links per run limit."""
        linker = AlertLogLinker(max_links_per_run=5)

        # Create 5 links (should succeed)
        for i in range(5):
            linker.create_link(
                alert_id=f"alert-{i}",
                run_id="run-1",
                tenant_id="tenant-1",
                link_type=AlertLogLinkType.THRESHOLD_NEAR,
            )

        # 6th link should fail
        with pytest.raises(AlertLogLinkError) as exc_info:
            linker.create_link(
                alert_id="alert-6",
                run_id="run-1",
                tenant_id="tenant-1",
                link_type=AlertLogLinkType.THRESHOLD_NEAR,
            )
        assert "exceeded" in str(exc_info.value).lower()

    def test_get_link(self):
        """Test getting a link by ID."""
        linker = AlertLogLinker()
        created = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        retrieved = linker.get_link(created.link_id)
        assert retrieved is not None
        assert retrieved.link_id == created.link_id

    def test_get_link_not_found(self):
        """Test getting non-existent link."""
        linker = AlertLogLinker()
        result = linker.get_link("non-existent")
        assert result is None

    def test_get_links_for_alert(self):
        """Test getting links for an alert."""
        linker = AlertLogLinker()
        linker.create_link(
            alert_id="alert-123",
            run_id="run-1",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        linker.create_link(
            alert_id="alert-123",
            run_id="run-2",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.INCIDENT_CREATED,
        )
        links = linker.get_links_for_alert("alert-123")
        assert len(links) == 2

    def test_get_links_for_run(self):
        """Test getting links for a run."""
        linker = AlertLogLinker()
        linker.create_link(
            alert_id="alert-1",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
        )
        linker.create_link(
            alert_id="alert-2",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        links = linker.get_links_for_run("run-123")
        assert len(links) == 2

    def test_get_links_for_run_by_type(self):
        """Test getting links for a run filtered by type."""
        linker = AlertLogLinker()
        linker.create_link(
            alert_id="alert-1",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
        )
        linker.create_link(
            alert_id="alert-2",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        links = linker.get_links_for_run(
            "run-123", link_type=AlertLogLinkType.THRESHOLD_BREACH
        )
        assert len(links) == 1
        assert links[0].link_type == AlertLogLinkType.THRESHOLD_BREACH

    def test_get_links_for_tenant(self):
        """Test getting links for a tenant."""
        linker = AlertLogLinker()
        linker.create_link(
            alert_id="alert-1",
            run_id="run-1",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
        )
        linker.create_link(
            alert_id="alert-2",
            run_id="run-2",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        linker.create_link(
            alert_id="alert-3",
            run_id="run-3",
            tenant_id="tenant-2",
            link_type=AlertLogLinkType.INCIDENT_CREATED,
        )
        links = linker.get_links_for_tenant("tenant-1")
        assert len(links) == 2

    def test_get_links_by_step(self):
        """Test getting links that reference a specific step."""
        linker = AlertLogLinker()
        linker.create_link(
            alert_id="alert-1",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
            step_indices=[5, 6, 7],
        )
        linker.create_link(
            alert_id="alert-2",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            step_indices=[10, 11],
        )
        links = linker.get_links_by_step("run-123", 6)
        assert len(links) == 1
        assert 6 in links[0].step_indices


class TestAlertLogLinkerUpdate:
    """Test link update functionality."""

    def setup_method(self):
        """Reset linker before each test."""
        _reset_alert_log_linker()

    def test_update_link(self):
        """Test updating a link."""
        linker = AlertLogLinker()
        link = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            step_indices=[10],
        )
        updated = linker.update_link(
            link.link_id,
            step_indices=[11, 12],
            action_taken="terminate",
        )
        assert updated is not None
        assert updated.step_indices == [10, 11, 12]
        assert updated.action_taken == "terminate"

    def test_update_link_not_found(self):
        """Test updating non-existent link."""
        linker = AlertLogLinker()
        result = linker.update_link("non-existent", step_indices=[1])
        assert result is None


class TestAlertLogLinkerLifecycle:
    """Test link lifecycle operations."""

    def setup_method(self):
        """Reset linker before each test."""
        _reset_alert_log_linker()

    def test_expire_link(self):
        """Test expiring a link."""
        linker = AlertLogLinker()
        link = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        result = linker.expire_link(link.link_id)
        assert result is True

        retrieved = linker.get_link(link.link_id)
        assert retrieved.status == AlertLogLinkStatus.EXPIRED

    def test_archive_link(self):
        """Test archiving a link."""
        linker = AlertLogLinker()
        link = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        result = linker.archive_link(link.link_id)
        assert result is True

        retrieved = linker.get_link(link.link_id)
        assert retrieved.status == AlertLogLinkStatus.ARCHIVED

    def test_delete_link(self):
        """Test deleting a link."""
        linker = AlertLogLinker()
        link = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        result = linker.delete_link(link.link_id)
        assert result is True

        retrieved = linker.get_link(link.link_id)
        assert retrieved.status == AlertLogLinkStatus.DELETED

    def test_cleanup_expired(self):
        """Test cleaning up expired links."""
        linker = AlertLogLinker(default_retention_days=0)  # Immediate expiration

        # Create some links that will be immediately expired
        for i in range(5):
            linker.create_link(
                alert_id=f"alert-{i}",
                run_id=f"run-{i}",
                tenant_id="tenant-1",
                link_type=AlertLogLinkType.THRESHOLD_NEAR,
                retention_days=0,
            )

        # Cleanup with a future time
        cleaned = linker.cleanup_expired(
            before=datetime.now(timezone.utc) + timedelta(seconds=1)
        )
        assert cleaned == 5


class TestAlertLogLinkerStatistics:
    """Test statistics functionality."""

    def setup_method(self):
        """Reset linker before each test."""
        _reset_alert_log_linker()

    def test_get_statistics(self):
        """Test getting statistics."""
        linker = AlertLogLinker()
        linker.create_link(
            alert_id="alert-1",
            run_id="run-1",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
        )
        linker.create_link(
            alert_id="alert-2",
            run_id="run-2",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        stats = linker.get_statistics()
        assert stats["total_links"] == 2
        assert stats["active"] == 2
        assert "threshold_near" in stats["by_type"]
        assert "threshold_breach" in stats["by_type"]

    def test_get_statistics_by_tenant(self):
        """Test getting statistics for a tenant."""
        linker = AlertLogLinker()
        linker.create_link(
            alert_id="alert-1",
            run_id="run-1",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
        )
        linker.create_link(
            alert_id="alert-2",
            run_id="run-2",
            tenant_id="tenant-2",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        stats = linker.get_statistics(tenant_id="tenant-1")
        assert stats["total_links"] == 1


class TestHelperFunctions:
    """Test module-level helper functions."""

    def setup_method(self):
        """Reset linker before each test."""
        _reset_alert_log_linker()

    def test_get_alert_log_linker_singleton(self):
        """Test linker singleton."""
        linker1 = get_alert_log_linker()
        linker2 = get_alert_log_linker()
        assert linker1 is linker2

    def test_create_alert_log_link_helper(self):
        """Test create_alert_log_link helper."""
        link = create_alert_log_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            step_indices=[10, 11],
        )
        assert link.alert_id == "alert-123"
        assert link.step_indices == [10, 11]

    def test_get_alerts_for_run_helper(self):
        """Test get_alerts_for_run helper."""
        create_alert_log_link(
            alert_id="alert-1",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
        )
        create_alert_log_link(
            alert_id="alert-2",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        links = get_alerts_for_run("run-123")
        assert len(links) == 2

    def test_get_logs_for_alert_helper(self):
        """Test get_logs_for_alert helper."""
        create_alert_log_link(
            alert_id="alert-123",
            run_id="run-1",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        create_alert_log_link(
            alert_id="alert-123",
            run_id="run-2",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.INCIDENT_CREATED,
        )
        links = get_logs_for_alert("alert-123")
        assert len(links) == 2


class TestAlertLogLinkUseCases:
    """Test real-world use cases."""

    def setup_method(self):
        """Reset linker before each test."""
        _reset_alert_log_linker()

    def test_threshold_alert_flow(self):
        """Test complete threshold alert linking flow."""
        linker = AlertLogLinker()

        # Step 1: Near-threshold warning at step 10
        near_link = linker.create_link(
            alert_id="alert-near-1",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_NEAR,
            step_indices=[10],
            metric_name="cost",
            metric_value=85.0,
            threshold_value=100.0,
        )
        assert near_link.status == AlertLogLinkStatus.ACTIVE

        # Step 2: Breach at step 15
        breach_link = linker.create_link(
            alert_id="alert-breach-1",
            run_id="run-123",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            step_indices=[15],
            metric_name="cost",
            metric_value=105.0,
            threshold_value=100.0,
            action_taken="terminate",
        )
        assert breach_link.metric_value == 105.0

        # Step 3: Query all alerts for run
        run_links = linker.get_links_for_run("run-123")
        assert len(run_links) == 2

        # Step 4: Query by type
        breach_links = linker.get_links_for_run(
            "run-123", link_type=AlertLogLinkType.THRESHOLD_BREACH
        )
        assert len(breach_links) == 1
        assert breach_links[0].action_taken == "terminate"

    def test_incident_linking_flow(self):
        """Test incident creation and resolution linking."""
        linker = AlertLogLinker()

        # Create incident
        created_link = linker.create_link(
            alert_id="incident-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.INCIDENT_CREATED,
            step_indices=[20, 21, 22],
            policy_id="policy-budget-1",
        )

        # Resolve incident later
        resolved_link = linker.create_link(
            alert_id="incident-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.INCIDENT_RESOLVED,
            step_indices=[25],
            action_taken="auto_resolved",
        )

        # Query all links for the incident alert
        incident_links = linker.get_links_for_alert("incident-123")
        assert len(incident_links) == 2

        # Verify we can trace the incident lifecycle
        types = [l.link_type for l in incident_links]
        assert AlertLogLinkType.INCIDENT_CREATED in types
        assert AlertLogLinkType.INCIDENT_RESOLVED in types

    def test_multi_tenant_isolation(self):
        """Test that tenants are isolated."""
        linker = AlertLogLinker()

        # Create links for different tenants
        linker.create_link(
            alert_id="alert-1",
            run_id="run-1",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )
        linker.create_link(
            alert_id="alert-2",
            run_id="run-2",
            tenant_id="tenant-2",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
        )

        # Each tenant should only see their own links
        tenant1_links = linker.get_links_for_tenant("tenant-1")
        tenant2_links = linker.get_links_for_tenant("tenant-2")

        assert len(tenant1_links) == 1
        assert len(tenant2_links) == 1
        assert tenant1_links[0].tenant_id == "tenant-1"
        assert tenant2_links[0].tenant_id == "tenant-2"
