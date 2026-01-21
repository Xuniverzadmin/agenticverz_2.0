# Layer: L8 — Catalyst/Meta
# Product: system-wide
# Reference: GAP-049 (AlertFatigueController)
"""
Tests for AlertFatigueController (GAP-049).

Verifies alert fatigue management including rate limiting,
suppression, aggregation, and cool-down periods.
"""

import pytest
from datetime import datetime, timedelta, timezone


class TestAlertFatigueImports:
    """Test that all components are properly exported."""

    def test_fatigue_mode_import(self):
        """AlertFatigueMode should be importable from package."""
        from app.services.alerts import AlertFatigueMode
        assert AlertFatigueMode.MONITOR == "monitor"

    def test_fatigue_action_import(self):
        """AlertFatigueAction should be importable from package."""
        from app.services.alerts import AlertFatigueAction
        assert AlertFatigueAction.ALLOW == "allow"

    def test_fatigue_config_import(self):
        """AlertFatigueConfig should be importable from package."""
        from app.services.alerts import AlertFatigueConfig
        config = AlertFatigueConfig()
        assert config.rate_limit_count == 10

    def test_fatigue_state_import(self):
        """AlertFatigueState should be importable from package."""
        from app.services.alerts import AlertFatigueState
        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )
        assert state.total_count == 0

    def test_fatigue_controller_import(self):
        """AlertFatigueController should be importable from package."""
        from app.services.alerts import AlertFatigueController
        controller = AlertFatigueController()
        assert controller is not None

    def test_fatigue_error_import(self):
        """AlertFatigueError should be importable from package."""
        from app.services.alerts import AlertFatigueError
        error = AlertFatigueError("test error")
        assert str(error) == "test error"

    def test_helper_functions_import(self):
        """Helper functions should be importable from package."""
        from app.services.alerts import (
            check_alert_fatigue,
            get_fatigue_stats,
            suppress_alert,
        )
        assert callable(check_alert_fatigue)
        assert callable(get_fatigue_stats)
        assert callable(suppress_alert)


class TestAlertFatigueModeEnum:
    """Test AlertFatigueMode enum."""

    def test_all_modes_defined(self):
        """All fatigue modes should be defined."""
        from app.services.alerts import AlertFatigueMode

        assert hasattr(AlertFatigueMode, "MONITOR")
        assert hasattr(AlertFatigueMode, "WARN")
        assert hasattr(AlertFatigueMode, "ENFORCE")
        assert hasattr(AlertFatigueMode, "AGGREGATE")

    def test_mode_string_values(self):
        """Mode values should be lowercase strings."""
        from app.services.alerts import AlertFatigueMode

        assert AlertFatigueMode.MONITOR.value == "monitor"
        assert AlertFatigueMode.WARN.value == "warn"
        assert AlertFatigueMode.ENFORCE.value == "enforce"
        assert AlertFatigueMode.AGGREGATE.value == "aggregate"


class TestAlertFatigueActionEnum:
    """Test AlertFatigueAction enum."""

    def test_all_actions_defined(self):
        """All fatigue actions should be defined."""
        from app.services.alerts import AlertFatigueAction

        assert hasattr(AlertFatigueAction, "ALLOW")
        assert hasattr(AlertFatigueAction, "RATE_LIMITED")
        assert hasattr(AlertFatigueAction, "SUPPRESSED")
        assert hasattr(AlertFatigueAction, "AGGREGATED")
        assert hasattr(AlertFatigueAction, "WARNED")
        assert hasattr(AlertFatigueAction, "COOLING_DOWN")

    def test_action_string_values(self):
        """Action values should be lowercase strings."""
        from app.services.alerts import AlertFatigueAction

        assert AlertFatigueAction.ALLOW.value == "allow"
        assert AlertFatigueAction.RATE_LIMITED.value == "rate_limited"
        assert AlertFatigueAction.SUPPRESSED.value == "suppressed"


class TestAlertFatigueConfig:
    """Test AlertFatigueConfig dataclass."""

    def test_default_values(self):
        """Default configuration should have sensible values."""
        from app.services.alerts import AlertFatigueConfig, AlertFatigueMode

        config = AlertFatigueConfig()

        assert config.rate_limit_count == 10
        assert config.rate_limit_window_seconds == 60
        assert config.suppression_threshold == 5
        assert config.suppression_duration_seconds == 300
        assert config.aggregation_window_seconds == 60
        assert config.aggregation_threshold == 3
        assert config.cooldown_threshold == 20
        assert config.cooldown_duration_seconds == 600
        assert config.mode == AlertFatigueMode.ENFORCE

    def test_custom_values(self):
        """Configuration should accept custom values."""
        from app.services.alerts import AlertFatigueConfig, AlertFatigueMode

        config = AlertFatigueConfig(
            rate_limit_count=5,
            rate_limit_window_seconds=30,
            mode=AlertFatigueMode.WARN,
        )

        assert config.rate_limit_count == 5
        assert config.rate_limit_window_seconds == 30
        assert config.mode == AlertFatigueMode.WARN

    def test_to_dict(self):
        """Configuration should serialize to dict."""
        from app.services.alerts import AlertFatigueConfig

        config = AlertFatigueConfig(rate_limit_count=5)
        result = config.to_dict()

        assert result["rate_limit_count"] == 5
        assert result["mode"] == "enforce"


class TestAlertFatigueState:
    """Test AlertFatigueState dataclass."""

    def test_state_creation(self):
        """State should be created with required fields."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )

        assert state.source_id == "src-1"
        assert state.tenant_id == "tenant-1"
        assert state.alert_type == "threshold"
        assert state.total_count == 0
        assert state.window_count == 0

    def test_record_alert(self):
        """Recording alert should update counters."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )

        state.record_alert()

        assert state.total_count == 1
        assert state.window_count == 1
        assert state.first_alert is not None
        assert state.last_alert is not None

    def test_reset_window(self):
        """Reset window should clear window count."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )
        state.record_alert()
        state.record_alert()
        state.reset_window()

        assert state.window_count == 0
        assert state.total_count == 2
        assert state.window_start is not None

    def test_suppression_lifecycle(self):
        """Suppression should start and end correctly."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )

        assert not state.is_suppressed

        state.start_suppression()
        assert state.is_suppressed
        assert state.suppression_started is not None
        assert state.suppression_count == 1

        state.end_suppression()
        assert not state.is_suppressed
        assert state.suppression_started is None

    def test_cooldown_lifecycle(self):
        """Cooldown should start and end correctly."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )

        assert not state.is_cooling_down

        state.start_cooldown()
        assert state.is_cooling_down
        assert state.cooldown_started is not None

        state.end_cooldown()
        assert not state.is_cooling_down
        assert state.cooldown_started is None

    def test_aggregation(self):
        """Aggregation should collect and flush alerts."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )

        state.add_to_aggregation({"value": 1})
        state.add_to_aggregation({"value": 2})

        assert len(state.aggregation_bucket) == 2

        bucket = state.flush_aggregation()
        assert len(bucket) == 2
        assert len(state.aggregation_bucket) == 0

    def test_window_expired(self):
        """Window expiration should be detected correctly."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )

        # No window set
        assert state.is_window_expired(60)

        # Window just started
        now = datetime.now(timezone.utc)
        state.reset_window(now)
        assert not state.is_window_expired(60, now)

        # Window expired
        future = now + timedelta(seconds=61)
        assert state.is_window_expired(60, future)

    def test_to_dict(self):
        """State should serialize to dict."""
        from app.services.alerts import AlertFatigueState

        state = AlertFatigueState(
            source_id="src-1",
            tenant_id="tenant-1",
            alert_type="threshold",
        )
        state.record_alert()

        result = state.to_dict()

        assert result["source_id"] == "src-1"
        assert result["tenant_id"] == "tenant-1"
        assert result["total_count"] == 1


class TestAlertFatigueStats:
    """Test AlertFatigueStats dataclass."""

    def test_stats_creation(self):
        """Stats should be created with zero values."""
        from app.services.alerts.fatigue_controller import AlertFatigueStats

        stats = AlertFatigueStats()

        assert stats.total_alerts == 0
        assert stats.allowed_alerts == 0
        assert stats.suppression_rate == 0.0

    def test_update_rates(self):
        """Rates should be calculated correctly."""
        from app.services.alerts.fatigue_controller import AlertFatigueStats

        stats = AlertFatigueStats(
            total_alerts=100,
            allowed_alerts=70,
            rate_limited_alerts=10,
            suppressed_alerts=15,
            cooldown_alerts=5,
        )
        stats.update_rates()

        assert stats.suppression_rate == 0.30

    def test_to_dict(self):
        """Stats should serialize to dict."""
        from app.services.alerts.fatigue_controller import AlertFatigueStats

        stats = AlertFatigueStats(total_alerts=10, allowed_alerts=8)
        result = stats.to_dict()

        assert result["total_alerts"] == 10
        assert result["allowed_alerts"] == 8


class TestAlertFatigueError:
    """Test AlertFatigueError exception."""

    def test_error_creation(self):
        """Error should be created with message."""
        from app.services.alerts import AlertFatigueError, AlertFatigueAction

        error = AlertFatigueError(
            message="Rate limit exceeded",
            source_id="src-1",
            action=AlertFatigueAction.RATE_LIMITED,
        )

        assert str(error) == "Rate limit exceeded"
        assert error.source_id == "src-1"
        assert error.action == AlertFatigueAction.RATE_LIMITED

    def test_error_to_dict(self):
        """Error should serialize to dict."""
        from app.services.alerts import AlertFatigueError, AlertFatigueAction

        error = AlertFatigueError(
            message="Suppressed",
            source_id="src-1",
            action=AlertFatigueAction.SUPPRESSED,
        )
        result = error.to_dict()

        assert result["error"] == "Suppressed"
        assert result["source_id"] == "src-1"
        assert result["action"] == "suppressed"


class TestAlertFatigueController:
    """Test AlertFatigueController core functionality."""

    @pytest.fixture(autouse=True)
    def reset_controller(self):
        """Reset controller before each test."""
        from app.services.alerts.fatigue_controller import _reset_controller
        _reset_controller()
        yield
        _reset_controller()

    def test_controller_creation(self):
        """Controller should be created with default config."""
        from app.services.alerts import AlertFatigueController

        controller = AlertFatigueController()
        assert controller is not None

    def test_controller_with_custom_config(self):
        """Controller should accept custom default config."""
        from app.services.alerts import AlertFatigueController, AlertFatigueConfig

        config = AlertFatigueConfig(rate_limit_count=5)
        controller = AlertFatigueController(default_config=config)

        tenant_config = controller.get_config("tenant-1")
        assert tenant_config.rate_limit_count == 5

    def test_configure_tenant(self):
        """Tenant-specific config should override default."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
        )

        controller = AlertFatigueController()
        controller.configure_tenant(
            "tenant-1",
            AlertFatigueConfig(
                rate_limit_count=3,
                mode=AlertFatigueMode.WARN,
            ),
        )

        config = controller.get_config("tenant-1")
        assert config.rate_limit_count == 3
        assert config.mode == AlertFatigueMode.WARN

        # Other tenant gets default
        default_config = controller.get_config("tenant-2")
        assert default_config.rate_limit_count == 10


class TestAlertFatigueControllerCheckAlert:
    """Test alert checking behavior."""

    @pytest.fixture(autouse=True)
    def reset_controller(self):
        """Reset controller before each test."""
        from app.services.alerts.fatigue_controller import _reset_controller
        _reset_controller()
        yield
        _reset_controller()

    def test_first_alert_allowed(self):
        """First alert should always be allowed."""
        from app.services.alerts import AlertFatigueController, AlertFatigueAction

        controller = AlertFatigueController()
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
        )

        assert result.allowed is True
        assert result.action == AlertFatigueAction.ALLOW

    def test_monitor_mode_always_allows(self):
        """Monitor mode should allow all alerts."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
            AlertFatigueAction,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.MONITOR,
            rate_limit_count=2,
        )
        controller = AlertFatigueController(default_config=config)

        # Fire many alerts
        for i in range(10):
            result = controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="src-1",
            )
            assert result.allowed is True
            assert result.action == AlertFatigueAction.ALLOW

    def test_rate_limiting_enforce_mode(self):
        """Rate limiting should block in enforce mode."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
            AlertFatigueAction,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.ENFORCE,
            rate_limit_count=3,
            suppression_threshold=10,  # High to avoid triggering
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # First 3 should be allowed
        for i in range(3):
            result = controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="src-1",
                now=now,
            )
            assert result.allowed is True

        # 4th should be rate limited
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
            now=now,
        )
        assert result.allowed is False
        assert result.action == AlertFatigueAction.RATE_LIMITED

    def test_rate_limiting_warn_mode(self):
        """Rate limiting should warn but allow in warn mode."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
            AlertFatigueAction,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.WARN,
            rate_limit_count=2,
            suppression_threshold=10,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # Fire 3 alerts
        for i in range(3):
            result = controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="src-1",
                now=now,
            )

        # Should warn but allow
        assert result.allowed is True
        assert result.action == AlertFatigueAction.WARNED

    def test_suppression_trigger(self):
        """Suppression should trigger at threshold."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
            AlertFatigueAction,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.ENFORCE,
            rate_limit_count=100,  # High to avoid
            suppression_threshold=3,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # Fire 3 alerts (threshold)
        for i in range(3):
            result = controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="src-1",
                now=now,
            )

        # 3rd should trigger suppression
        assert result.allowed is False
        assert result.action == AlertFatigueAction.SUPPRESSED

        # Next alert should be suppressed
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
            now=now,
        )
        assert result.allowed is False
        assert result.action == AlertFatigueAction.SUPPRESSED

    def test_suppression_expires(self):
        """Suppression should expire after duration."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
            AlertFatigueAction,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.ENFORCE,
            rate_limit_count=100,
            suppression_threshold=2,
            suppression_duration_seconds=60,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # Trigger suppression
        for i in range(2):
            controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="src-1",
                now=now,
            )

        # Should be suppressed
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
            now=now,
        )
        assert result.allowed is False
        assert result.action == AlertFatigueAction.SUPPRESSED

        # After expiration
        future = now + timedelta(seconds=61)
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
            now=future,
        )
        assert result.allowed is True
        assert result.action == AlertFatigueAction.ALLOW

    def test_cooldown_trigger(self):
        """Cooldown should trigger at high threshold."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
            AlertFatigueAction,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.ENFORCE,
            rate_limit_count=100,
            suppression_threshold=100,
            cooldown_threshold=5,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # Fire 5 alerts
        for i in range(5):
            result = controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="src-1",
                now=now,
            )

        # 5th should trigger cooldown
        assert result.allowed is False
        assert result.action == AlertFatigueAction.COOLING_DOWN


class TestAlertFatigueAggregation:
    """Test alert aggregation behavior."""

    @pytest.fixture(autouse=True)
    def reset_controller(self):
        """Reset controller before each test."""
        from app.services.alerts.fatigue_controller import _reset_controller
        _reset_controller()
        yield
        _reset_controller()

    def test_aggregation_mode(self):
        """Alerts should be aggregated in aggregate mode."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
            AlertFatigueAction,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.AGGREGATE,
            aggregation_threshold=3,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # First 2 should be held
        for i in range(2):
            result = controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="src-1",
                alert_data={"value": i},
                now=now,
            )
            assert result.allowed is False
            assert result.action == AlertFatigueAction.AGGREGATED

        # 3rd should release aggregation
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
            alert_data={"value": 2},
            now=now,
        )
        assert result.allowed is True
        assert result.action == AlertFatigueAction.AGGREGATED
        assert result.aggregated_count == 3


class TestAlertFatigueControllerManualOps:
    """Test manual suppression operations."""

    @pytest.fixture(autouse=True)
    def reset_controller(self):
        """Reset controller before each test."""
        from app.services.alerts.fatigue_controller import _reset_controller
        _reset_controller()
        yield
        _reset_controller()

    def test_manual_suppress(self):
        """Manual suppression should block alerts."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueAction,
        )

        controller = AlertFatigueController()

        # Manually suppress
        state = controller.suppress_source(
            tenant_id="tenant-1",
            source_id="src-1",
            alert_type="threshold",
        )
        assert state.is_suppressed is True

        # Alert should be blocked
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
        )
        assert result.allowed is False
        assert result.action == AlertFatigueAction.SUPPRESSED

    def test_manual_unsuppress(self):
        """Manual unsuppression should allow alerts."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueAction,
        )

        controller = AlertFatigueController()

        # Suppress then unsuppress
        controller.suppress_source(
            tenant_id="tenant-1",
            source_id="src-1",
            alert_type="threshold",
        )
        controller.unsuppress_source(
            tenant_id="tenant-1",
            source_id="src-1",
            alert_type="threshold",
        )

        # Alert should be allowed
        result = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
        )
        assert result.allowed is True
        assert result.action == AlertFatigueAction.ALLOW


class TestAlertFatigueControllerStatistics:
    """Test statistics gathering."""

    @pytest.fixture(autouse=True)
    def reset_controller(self):
        """Reset controller before each test."""
        from app.services.alerts.fatigue_controller import _reset_controller
        _reset_controller()
        yield
        _reset_controller()

    def test_get_statistics(self):
        """Statistics should be collected correctly."""
        from app.services.alerts import AlertFatigueController

        controller = AlertFatigueController()

        # Fire some alerts
        for i in range(5):
            controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id=f"src-{i}",
            )

        stats = controller.get_statistics()
        assert stats.active_sources == 5
        assert stats.total_alerts == 5

    def test_get_statistics_by_tenant(self):
        """Statistics should filter by tenant."""
        from app.services.alerts import AlertFatigueController

        controller = AlertFatigueController()

        # Fire alerts for multiple tenants
        for i in range(3):
            controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id=f"src-{i}",
            )
        for i in range(2):
            controller.check_alert(
                tenant_id="tenant-2",
                alert_type="threshold",
                source_id=f"src-{i}",
            )

        stats = controller.get_statistics(tenant_id="tenant-1")
        assert stats.active_sources == 3

    def test_get_active_sources(self):
        """Active sources should be retrieved."""
        from app.services.alerts import AlertFatigueController

        controller = AlertFatigueController()

        controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
        )
        controller.check_alert(
            tenant_id="tenant-1",
            alert_type="policy",
            source_id="src-2",
        )

        sources = controller.get_active_sources(tenant_id="tenant-1")
        assert len(sources) == 2

    def test_clear_tenant(self):
        """Clearing tenant should remove all state."""
        from app.services.alerts import AlertFatigueController

        controller = AlertFatigueController()

        # Fire alerts
        for i in range(5):
            controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id=f"src-{i}",
            )

        cleared = controller.clear_tenant("tenant-1")
        assert cleared == 5

        sources = controller.get_active_sources(tenant_id="tenant-1")
        assert len(sources) == 0


class TestHelperFunctions:
    """Test module-level helper functions."""

    @pytest.fixture(autouse=True)
    def reset_controller(self):
        """Reset controller before each test."""
        from app.services.alerts.fatigue_controller import _reset_controller
        _reset_controller()
        yield
        _reset_controller()

    def test_check_alert_fatigue_helper(self):
        """check_alert_fatigue should use singleton."""
        from app.services.alerts import check_alert_fatigue

        result = check_alert_fatigue(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
        )
        assert result.allowed is True

    def test_suppress_alert_helper(self):
        """suppress_alert should suppress via singleton."""
        from app.services.alerts import suppress_alert, check_alert_fatigue

        suppress_alert(
            tenant_id="tenant-1",
            source_id="src-1",
            alert_type="threshold",
        )

        result = check_alert_fatigue(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_id="src-1",
        )
        assert result.allowed is False

    def test_get_fatigue_stats_helper(self):
        """get_fatigue_stats should return stats from singleton."""
        from app.services.alerts import get_fatigue_stats, check_alert_fatigue

        # Fire some alerts
        for i in range(3):
            check_alert_fatigue(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id=f"src-{i}",
            )

        stats = get_fatigue_stats()
        assert stats.active_sources == 3


class TestAlertFatigueUseCases:
    """Test real-world use cases."""

    @pytest.fixture(autouse=True)
    def reset_controller(self):
        """Reset controller before each test."""
        from app.services.alerts.fatigue_controller import _reset_controller
        _reset_controller()
        yield
        _reset_controller()

    def test_threshold_alert_storm(self):
        """Simulate a threshold alert storm scenario."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.ENFORCE,
            rate_limit_count=5,
            suppression_threshold=10,
            cooldown_threshold=50,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # Simulate storm of 100 alerts
        allowed = 0
        blocked = 0
        for i in range(100):
            result = controller.check_alert(
                tenant_id="tenant-1",
                alert_type="threshold",
                source_id="cpu-monitor",
                now=now,
            )
            if result.allowed:
                allowed += 1
            else:
                blocked += 1

        # Should have blocked most alerts
        assert blocked > allowed
        assert blocked >= 90  # At least 90% blocked

    def test_multi_source_isolation(self):
        """Different sources should be tracked independently."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.ENFORCE,
            rate_limit_count=2,
            suppression_threshold=100,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # Fire alerts from multiple sources
        for source in ["cpu", "memory", "disk"]:
            for i in range(3):
                result = controller.check_alert(
                    tenant_id="tenant-1",
                    alert_type="threshold",
                    source_id=source,
                    now=now,
                )

        # Each source should have its own limit
        stats = controller.get_statistics()
        assert stats.active_sources == 3
        # 3 sources * (2 allowed + 1 blocked) = 3 sources * 3 alerts
        assert stats.total_alerts == 9

    def test_tenant_isolation(self):
        """Different tenants should be tracked independently."""
        from app.services.alerts import (
            AlertFatigueController,
            AlertFatigueConfig,
            AlertFatigueMode,
        )

        config = AlertFatigueConfig(
            mode=AlertFatigueMode.ENFORCE,
            rate_limit_count=2,
            suppression_threshold=100,
        )
        controller = AlertFatigueController(default_config=config)
        now = datetime.now(timezone.utc)

        # Fire alerts from different tenants
        for tenant in ["tenant-1", "tenant-2"]:
            for i in range(3):
                result = controller.check_alert(
                    tenant_id=tenant,
                    alert_type="threshold",
                    source_id="cpu",
                    now=now,
                )

        # Each tenant should have independent limits
        stats_1 = controller.get_statistics(tenant_id="tenant-1")
        stats_2 = controller.get_statistics(tenant_id="tenant-2")

        assert stats_1.active_sources == 1
        assert stats_2.active_sources == 1

    def test_source_id_from_data(self):
        """Source ID should be generated from data if not provided."""
        from app.services.alerts import AlertFatigueController

        controller = AlertFatigueController()

        result1 = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_data={"metric": "cpu", "host": "server-1"},
        )

        result2 = controller.check_alert(
            tenant_id="tenant-1",
            alert_type="threshold",
            source_data={"metric": "cpu", "host": "server-1"},
        )

        # Same source data should produce same source ID
        assert result1.source_id == result2.source_id
