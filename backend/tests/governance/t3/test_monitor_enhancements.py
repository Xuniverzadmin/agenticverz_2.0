# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test T3 monitor enhancement governance requirements (GAP-005 to GAP-008)
# Reference: DOMAINS_E2E_SCAFFOLD_V3.md, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T3-002: Monitor Enhancement Tests (GAP-005 to GAP-008)

Tests the monitor configuration and binding features:
- GAP-005: Explicit MonitorConfig object
- GAP-006: RAG access monitoring with allowed sources
- GAP-007: Burn rate monitoring with configurable window
- GAP-008: Monitor → Limit binding enforcement

Key Principle:
> If something is not monitored, it cannot trigger a limit or action.
"""

from datetime import datetime, timezone

import pytest

from app.models.monitor_config import (
    MonitorConfig,
    MonitorConfigCreate,
    MonitorConfigResponse,
    MonitorConfigUpdate,
    MonitorMetric,
)


# ===========================================================================
# Test: Import Verification
# ===========================================================================


class TestMonitorImports:
    """Verify all monitor-related imports are accessible."""

    def test_monitor_metric_import(self) -> None:
        """Test MonitorMetric enum is importable."""
        assert MonitorMetric is not None

    def test_monitor_config_import(self) -> None:
        """Test MonitorConfig model is importable."""
        assert MonitorConfig is not None

    def test_monitor_config_create_import(self) -> None:
        """Test MonitorConfigCreate model is importable."""
        assert MonitorConfigCreate is not None

    def test_monitor_config_update_import(self) -> None:
        """Test MonitorConfigUpdate model is importable."""
        assert MonitorConfigUpdate is not None

    def test_monitor_config_response_import(self) -> None:
        """Test MonitorConfigResponse model is importable."""
        assert MonitorConfigResponse is not None


# ===========================================================================
# GAP-005: Explicit Monitor Config
# ===========================================================================


class TestGAP005ExplicitMonitorConfig:
    """
    GAP-005: Explicit MonitorConfig Object

    CURRENT: Implicit via limit types
    REQUIRED: Explicit `MonitorConfig` object
    """

    def test_monitor_config_is_explicit_model(self) -> None:
        """MonitorConfig is an explicit SQLModel table class."""
        assert hasattr(MonitorConfig, "__tablename__")
        assert MonitorConfig.__tablename__ == "policy_monitor_configs"

    def test_monitor_config_has_config_id(self) -> None:
        """MonitorConfig has unique config_id field."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.config_id == "MON-001"

    def test_monitor_config_linked_to_policy(self) -> None:
        """MonitorConfig is linked to a policy via policy_id."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.policy_id == "POL-001"

    def test_monitor_config_tenant_isolated(self) -> None:
        """MonitorConfig has tenant_id for isolation."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.tenant_id == "tenant-001"

    def test_monitor_config_has_timestamps(self) -> None:
        """MonitorConfig has created_at and updated_at timestamps."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "created_at")
        assert hasattr(config, "updated_at")

    def test_enabled_metrics_property(self) -> None:
        """MonitorConfig has enabled_metrics property listing active monitors."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_token_usage=True,
            monitor_cost=True,
            monitor_burn_rate=False,
        )
        metrics = config.enabled_metrics
        assert MonitorMetric.TOKEN_USAGE in metrics
        assert MonitorMetric.COST in metrics
        assert MonitorMetric.BURN_RATE not in metrics


# ===========================================================================
# GAP-006: RAG Access Monitoring
# ===========================================================================


class TestGAP006RAGAccessMonitoring:
    """
    GAP-006: RAG Access Monitoring

    CURRENT: Not supported
    REQUIRED: `monitor_rag_access: { enabled, allowed_sources[] }`
    """

    def test_rag_access_monitor_flag_exists(self) -> None:
        """MonitorConfig has monitor_rag_access boolean flag."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "monitor_rag_access")
        assert isinstance(config.monitor_rag_access, bool)

    def test_rag_access_default_disabled(self) -> None:
        """RAG access monitoring is disabled by default."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.monitor_rag_access is False

    def test_rag_access_can_be_enabled(self) -> None:
        """RAG access monitoring can be explicitly enabled."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_rag_access=True,
        )
        assert config.monitor_rag_access is True

    def test_allowed_rag_sources_field_exists(self) -> None:
        """MonitorConfig has allowed_rag_sources_json field for source list."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "allowed_rag_sources_json")

    def test_allowed_rag_sources_property_getter(self) -> None:
        """allowed_rag_sources property returns list from JSON."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            allowed_rag_sources_json='["source-1", "source-2"]',
        )
        assert config.allowed_rag_sources == ["source-1", "source-2"]

    def test_allowed_rag_sources_property_setter(self) -> None:
        """allowed_rag_sources property sets JSON from list."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        config.allowed_rag_sources = ["src-a", "src-b", "src-c"]
        assert '"src-a"' in config.allowed_rag_sources_json
        assert '"src-b"' in config.allowed_rag_sources_json

    def test_allowed_rag_sources_empty_returns_empty_list(self) -> None:
        """allowed_rag_sources returns empty list when JSON is None."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.allowed_rag_sources == []

    def test_rag_metric_in_enabled_when_monitored(self) -> None:
        """RAG_ACCESS metric appears in enabled_metrics when monitored."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_rag_access=True,
        )
        assert MonitorMetric.RAG_ACCESS in config.enabled_metrics

    def test_rag_metric_not_in_enabled_when_disabled(self) -> None:
        """RAG_ACCESS metric not in enabled_metrics when disabled."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_rag_access=False,
        )
        assert MonitorMetric.RAG_ACCESS not in config.enabled_metrics


# ===========================================================================
# GAP-007: Burn Rate Monitoring
# ===========================================================================


class TestGAP007BurnRateMonitoring:
    """
    GAP-007: Burn Rate Monitoring

    CURRENT: Not supported
    REQUIRED: `monitor_burn_rate: true` with configurable window
    """

    def test_burn_rate_monitor_flag_exists(self) -> None:
        """MonitorConfig has monitor_burn_rate boolean flag."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "monitor_burn_rate")
        assert isinstance(config.monitor_burn_rate, bool)

    def test_burn_rate_default_disabled(self) -> None:
        """Burn rate monitoring is disabled by default."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.monitor_burn_rate is False

    def test_burn_rate_can_be_enabled(self) -> None:
        """Burn rate monitoring can be explicitly enabled."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_burn_rate=True,
        )
        assert config.monitor_burn_rate is True

    def test_burn_rate_window_field_exists(self) -> None:
        """MonitorConfig has burn_rate_window_seconds field."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "burn_rate_window_seconds")
        assert isinstance(config.burn_rate_window_seconds, int)

    def test_burn_rate_window_default_60_seconds(self) -> None:
        """Burn rate window defaults to 60 seconds."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.burn_rate_window_seconds == 60

    def test_burn_rate_window_configurable(self) -> None:
        """Burn rate window can be configured to different values."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_burn_rate=True,
            burn_rate_window_seconds=120,
        )
        assert config.burn_rate_window_seconds == 120

    def test_burn_rate_metric_in_enabled_when_monitored(self) -> None:
        """BURN_RATE metric appears in enabled_metrics when monitored."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_burn_rate=True,
        )
        assert MonitorMetric.BURN_RATE in config.enabled_metrics

    def test_burn_rate_metric_not_in_enabled_when_disabled(self) -> None:
        """BURN_RATE metric not in enabled_metrics when disabled."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_burn_rate=False,
        )
        assert MonitorMetric.BURN_RATE not in config.enabled_metrics


# ===========================================================================
# GAP-008: Monitor → Limit Binding
# ===========================================================================


class TestGAP008MonitorLimitBinding:
    """
    GAP-008: Monitor → Limit Binding

    CURRENT: Implicit
    REQUIRED: Explicit - "If not monitored, cannot trigger limit"
    """

    def test_is_metric_monitored_method_exists(self) -> None:
        """MonitorConfig has is_metric_monitored method."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "is_metric_monitored")
        assert callable(config.is_metric_monitored)

    def test_is_metric_monitored_returns_true_for_enabled(self) -> None:
        """is_metric_monitored returns True for enabled metrics."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_token_usage=True,
        )
        assert config.is_metric_monitored(MonitorMetric.TOKEN_USAGE) is True

    def test_is_metric_monitored_returns_false_for_disabled(self) -> None:
        """is_metric_monitored returns False for disabled metrics."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_burn_rate=False,
        )
        assert config.is_metric_monitored(MonitorMetric.BURN_RATE) is False

    def test_binding_principle_token_usage(self) -> None:
        """Token limit cannot be evaluated if token_usage not monitored."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_token_usage=False,  # Not monitored
        )
        # If not monitored, cannot check limit
        assert not config.is_metric_monitored(MonitorMetric.TOKEN_USAGE)

    def test_binding_principle_cost(self) -> None:
        """Cost limit cannot be evaluated if cost not monitored."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_cost=False,  # Not monitored
        )
        # If not monitored, cannot check limit
        assert not config.is_metric_monitored(MonitorMetric.COST)

    def test_binding_principle_burn_rate(self) -> None:
        """Burn rate limit cannot be evaluated if burn_rate not monitored."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_burn_rate=False,  # Not monitored
        )
        # If not monitored, cannot check limit
        assert not config.is_metric_monitored(MonitorMetric.BURN_RATE)

    def test_binding_principle_rag_access(self) -> None:
        """RAG access limit cannot be evaluated if rag_access not monitored."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_rag_access=False,  # Not monitored
        )
        # If not monitored, cannot check limit
        assert not config.is_metric_monitored(MonitorMetric.RAG_ACCESS)

    def test_multiple_metrics_binding(self) -> None:
        """Multiple metrics can be independently monitored."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_token_usage=True,
            monitor_cost=True,
            monitor_burn_rate=False,
            monitor_rag_access=False,
        )
        # Token and cost monitored
        assert config.is_metric_monitored(MonitorMetric.TOKEN_USAGE)
        assert config.is_metric_monitored(MonitorMetric.COST)
        # Burn rate and RAG not monitored
        assert not config.is_metric_monitored(MonitorMetric.BURN_RATE)
        assert not config.is_metric_monitored(MonitorMetric.RAG_ACCESS)


# ===========================================================================
# Test: Monitor Metric Enum
# ===========================================================================


class TestMonitorMetricEnum:
    """Test MonitorMetric enum values and behavior."""

    def test_token_usage_metric(self) -> None:
        """TOKEN_USAGE metric exists."""
        assert MonitorMetric.TOKEN_USAGE.value == "token_usage"

    def test_token_per_step_metric(self) -> None:
        """TOKEN_PER_STEP metric exists."""
        assert MonitorMetric.TOKEN_PER_STEP.value == "token_per_step"

    def test_cost_metric(self) -> None:
        """COST metric exists."""
        assert MonitorMetric.COST.value == "cost"

    def test_burn_rate_metric(self) -> None:
        """BURN_RATE metric exists."""
        assert MonitorMetric.BURN_RATE.value == "burn_rate"

    def test_rag_access_metric(self) -> None:
        """RAG_ACCESS metric exists."""
        assert MonitorMetric.RAG_ACCESS.value == "rag_access"

    def test_latency_metric(self) -> None:
        """LATENCY metric exists."""
        assert MonitorMetric.LATENCY.value == "latency"

    def test_step_count_metric(self) -> None:
        """STEP_COUNT metric exists."""
        assert MonitorMetric.STEP_COUNT.value == "step_count"


# ===========================================================================
# Test: Inspection Constraints (Negative Capabilities)
# ===========================================================================


class TestInspectionConstraints:
    """Test inspection constraint fields on MonitorConfig."""

    def test_allow_prompt_logging_field(self) -> None:
        """MonitorConfig has allow_prompt_logging field."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "allow_prompt_logging")
        assert config.allow_prompt_logging is False  # Default

    def test_allow_response_logging_field(self) -> None:
        """MonitorConfig has allow_response_logging field."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "allow_response_logging")
        assert config.allow_response_logging is False  # Default

    def test_allow_pii_capture_field(self) -> None:
        """MonitorConfig has allow_pii_capture field."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "allow_pii_capture")
        assert config.allow_pii_capture is False  # Default

    def test_allow_secret_access_field(self) -> None:
        """MonitorConfig has allow_secret_access field."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "allow_secret_access")
        assert config.allow_secret_access is False  # Default

    def test_inspection_constraints_configurable(self) -> None:
        """Inspection constraints can be individually configured."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            allow_prompt_logging=True,
            allow_response_logging=False,
            allow_pii_capture=False,
            allow_secret_access=True,
        )
        assert config.allow_prompt_logging is True
        assert config.allow_response_logging is False
        assert config.allow_pii_capture is False
        assert config.allow_secret_access is True


# ===========================================================================
# Test: Monitor Config Snapshot
# ===========================================================================


class TestMonitorConfigSnapshot:
    """Test MonitorConfig to_snapshot method."""

    def test_to_snapshot_returns_dict(self) -> None:
        """to_snapshot returns a dictionary."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        snapshot = config.to_snapshot()
        assert isinstance(snapshot, dict)

    def test_snapshot_contains_config_id(self) -> None:
        """Snapshot contains config_id."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        snapshot = config.to_snapshot()
        assert snapshot["config_id"] == "MON-001"

    def test_snapshot_contains_enabled_metrics(self) -> None:
        """Snapshot contains list of enabled metrics."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            monitor_token_usage=True,
            monitor_cost=True,
        )
        snapshot = config.to_snapshot()
        assert "enabled_metrics" in snapshot
        assert "token_usage" in snapshot["enabled_metrics"]
        assert "cost" in snapshot["enabled_metrics"]

    def test_snapshot_contains_burn_rate_window(self) -> None:
        """Snapshot contains burn_rate_window_seconds."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            burn_rate_window_seconds=90,
        )
        snapshot = config.to_snapshot()
        assert snapshot["burn_rate_window_seconds"] == 90

    def test_snapshot_contains_allowed_rag_sources(self) -> None:
        """Snapshot contains allowed_rag_sources."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        config.allowed_rag_sources = ["source-1", "source-2"]
        snapshot = config.to_snapshot()
        assert snapshot["allowed_rag_sources"] == ["source-1", "source-2"]

    def test_snapshot_contains_inspection_constraints(self) -> None:
        """Snapshot contains inspection_constraints dict."""
        config = MonitorConfig(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            allow_prompt_logging=True,
        )
        snapshot = config.to_snapshot()
        assert "inspection_constraints" in snapshot
        assert snapshot["inspection_constraints"]["allow_prompt_logging"] is True


# ===========================================================================
# Test: Pydantic Models (Create/Update/Response)
# ===========================================================================


class TestMonitorConfigPydanticModels:
    """Test Pydantic models for API operations."""

    def test_create_model_validates_policy_id(self) -> None:
        """MonitorConfigCreate requires policy_id."""
        create = MonitorConfigCreate(policy_id="POL-001")
        assert create.policy_id == "POL-001"

    def test_create_model_has_defaults(self) -> None:
        """MonitorConfigCreate has sensible defaults."""
        create = MonitorConfigCreate(policy_id="POL-001")
        assert create.monitor_token_usage is True
        assert create.monitor_cost is True
        assert create.monitor_burn_rate is False
        assert create.monitor_rag_access is False

    def test_update_model_all_fields_optional(self) -> None:
        """MonitorConfigUpdate has all fields optional."""
        update = MonitorConfigUpdate()
        assert update.monitor_token_usage is None
        assert update.monitor_cost is None

    def test_update_model_partial_update(self) -> None:
        """MonitorConfigUpdate allows partial updates."""
        update = MonitorConfigUpdate(monitor_burn_rate=True)
        assert update.monitor_burn_rate is True
        assert update.monitor_cost is None  # Not specified

    def test_response_model_structure(self) -> None:
        """MonitorConfigResponse has expected structure."""
        response = MonitorConfigResponse(
            config_id="MON-001",
            policy_id="POL-001",
            tenant_id="tenant-001",
            enabled_metrics=["token_usage", "cost"],
            burn_rate_window_seconds=60,
            allowed_rag_sources=[],
            inspection_constraints={
                "allow_prompt_logging": False,
                "allow_response_logging": False,
                "allow_pii_capture": False,
                "allow_secret_access": False,
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert response.config_id == "MON-001"
        assert "token_usage" in response.enabled_metrics
