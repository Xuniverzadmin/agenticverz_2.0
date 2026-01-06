# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Contract tests for L2→L3 adapter interfaces (GATE-8)
# Callers: pytest, CI/CD
# Allowed Imports: L8 (test fixtures), L3 (adapters under test)
# Forbidden Imports: L6 directly (must go through L3→L4)
# Reference: PIN-280 (L2 Promotion Governance), PIN-281 (L3 Adapter Closure)
#
# GOVERNANCE NOTE:
# These tests verify the contract between L2 and L3 layers.
# They ensure that L3 adapters provide the expected interface to L2.
# Tests use mock L4 services to isolate the L3 layer.

"""
L2→L3 Contract Tests (GATE-8)

These contract tests verify that:
1. L3 adapters have the expected interface for L2
2. L3 adapters correctly translate requests to L4 services
3. L3 adapters correctly transform responses for L2

Contract tests do NOT test:
- Database persistence (that's L6 integration tests)
- Business logic (that's L4 unit tests)
- End-to-end flows (that's E2E tests)
"""

import inspect
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# INCIDENTS ADAPTER CONTRACT TESTS
# =============================================================================


class TestCustomerIncidentsAdapterContract:
    """Contract tests for CustomerIncidentsAdapter (L3)."""

    def test_list_incidents_returns_customer_safe_schema(self):
        """L3 must return customer-safe incident summaries."""
        from app.adapters.customer_incidents_adapter import (
            CustomerIncidentListResponse,
            CustomerIncidentsAdapter,
            CustomerIncidentSummary,
        )

        mock_session = MagicMock()
        mock_read_service = MagicMock()

        # Mock L4 service response
        mock_incident = MagicMock()
        mock_incident.id = "incident-123"
        mock_incident.title = "Test Incident"
        mock_incident.severity.value = "high"
        mock_incident.status.value = "open"
        mock_incident.trigger_type.value = "manual"
        mock_incident.action_taken = None
        mock_incident.cost_avoided_cents = 1000
        mock_incident.calls_affected = 5
        mock_incident.created_at = datetime.now(timezone.utc)
        mock_incident.resolved_at = None

        mock_read_service.list_incidents.return_value = ([mock_incident], 1)

        with patch("app.adapters.customer_incidents_adapter.get_incident_read_service", return_value=mock_read_service):
            with patch("app.adapters.customer_incidents_adapter.get_incident_write_service"):
                adapter = CustomerIncidentsAdapter(mock_session)
                result = adapter.list_incidents(tenant_id="tenant-123", limit=10, offset=0)

        # Contract assertions
        assert isinstance(result, CustomerIncidentListResponse)
        assert len(result.items) == 1
        assert isinstance(result.items[0], CustomerIncidentSummary)
        assert result.items[0].id == "incident-123"
        # Contract: Severity is translated to calm vocabulary
        assert result.items[0].severity == "action"  # "high" -> "action"

    def test_severity_translation_calm_vocabulary(self):
        """L3 must translate severity to calm customer vocabulary."""
        from app.adapters.customer_incidents_adapter import _translate_severity

        # Contract: Severity mapping
        assert _translate_severity("critical") == "urgent"
        assert _translate_severity("high") == "action"
        assert _translate_severity("medium") == "attention"
        assert _translate_severity("low") == "info"
        assert _translate_severity("info") == "info"

    def test_acknowledge_incident_requires_tenant_id(self):
        """L3 must enforce tenant isolation for mutations."""
        from app.adapters.customer_incidents_adapter import CustomerIncidentsAdapter

        mock_session = MagicMock()
        mock_read_service = MagicMock()
        mock_write_service = MagicMock()

        # Mock L4 read service - unauthorized
        mock_read_service.get_incident.return_value = None

        with patch("app.adapters.customer_incidents_adapter.get_incident_read_service", return_value=mock_read_service):
            with patch(
                "app.adapters.customer_incidents_adapter.get_incident_write_service", return_value=mock_write_service
            ):
                adapter = CustomerIncidentsAdapter(mock_session)
                result = adapter.acknowledge_incident(
                    incident_id="incident-123",
                    tenant_id="wrong-tenant",
                )

        # Contract: Returns None for unauthorized access
        assert result is None
        # Contract: Write service was NOT called (tenant isolation)
        mock_write_service.acknowledge_incident.assert_not_called()


# =============================================================================
# KEYS ADAPTER CONTRACT TESTS
# =============================================================================


class TestCustomerKeysAdapterContract:
    """Contract tests for CustomerKeysAdapter (L3)."""

    def test_list_keys_returns_customer_safe_schema(self):
        """L3 must return customer-safe key info (prefix only, no full key)."""
        from app.adapters.customer_keys_adapter import (
            CustomerKeyInfo,
            CustomerKeyListResponse,
            CustomerKeysAdapter,
        )

        mock_session = MagicMock()
        mock_read_service = MagicMock()
        mock_write_service = MagicMock()

        # Mock L4 service response
        mock_key = MagicMock()
        mock_key.id = "key-123"
        mock_key.name = "Test Key"
        mock_key.key_hash = "abcd1234efgh5678"  # Full hash
        mock_key.is_frozen = False
        mock_key.created_at = datetime.now(timezone.utc)
        mock_key.last_used_at = None

        mock_read_service.list_keys.return_value = ([mock_key], 1)
        mock_read_service.get_key_usage_today.return_value = (10, 500)

        with patch("app.adapters.customer_keys_adapter.get_keys_read_service", return_value=mock_read_service):
            with patch("app.adapters.customer_keys_adapter.get_keys_write_service", return_value=mock_write_service):
                adapter = CustomerKeysAdapter(mock_session)
                result = adapter.list_keys(tenant_id="tenant-123", limit=10, offset=0)

        # Contract assertions
        assert isinstance(result, CustomerKeyListResponse)
        assert len(result.items) == 1
        assert isinstance(result.items[0], CustomerKeyInfo)
        # Contract: Only prefix is exposed, not full key
        assert result.items[0].prefix == "abcd1234"  # First 8 chars only
        assert len(result.items[0].prefix) == 8

    def test_freeze_key_requires_tenant_id(self):
        """L3 must enforce tenant isolation for key mutations."""
        from app.adapters.customer_keys_adapter import CustomerKeysAdapter

        mock_session = MagicMock()
        mock_read_service = MagicMock()
        mock_write_service = MagicMock()

        # Mock L4 read service - unauthorized
        mock_read_service.get_key.return_value = None

        with patch("app.adapters.customer_keys_adapter.get_keys_read_service", return_value=mock_read_service):
            with patch("app.adapters.customer_keys_adapter.get_keys_write_service", return_value=mock_write_service):
                adapter = CustomerKeysAdapter(mock_session)
                result = adapter.freeze_key(key_id="key-123", tenant_id="wrong-tenant")

        # Contract: Returns None for unauthorized access
        assert result is None
        # Contract: Write service was NOT called (tenant isolation)
        mock_write_service.freeze_key.assert_not_called()

    def test_key_info_never_exposes_full_key(self):
        """L3 contract: CustomerKeyInfo NEVER contains full key value."""
        from app.adapters.customer_keys_adapter import CustomerKeyInfo

        # Contract: CustomerKeyInfo schema does NOT have a 'key' or 'key_value' field
        info = CustomerKeyInfo(
            id="key-123",
            name="Test",
            prefix="abcd1234",
            status="active",
            created_at="2026-01-03T00:00:00Z",
            requests_today=0,
            spend_today_cents=0,
        )

        # Contract assertions - these fields should NOT exist
        assert not hasattr(info, "key")
        assert not hasattr(info, "key_value")
        assert not hasattr(info, "full_key")
        assert not hasattr(info, "secret")


# =============================================================================
# LOGS ADAPTER CONTRACT TESTS (Async)
# =============================================================================


class TestCustomerLogsAdapterContract:
    """Contract tests for CustomerLogsAdapter (L3)."""

    def test_logs_adapter_exports_customer_safe_types(self):
        """L3 must export customer-safe DTO types."""
        from app.adapters.customer_logs_adapter import (
            CustomerLogDetail,
            CustomerLogListResponse,
            CustomerLogsAdapter,
            CustomerLogSummary,
        )

        # Contract: These types exist and are importable
        assert CustomerLogsAdapter is not None
        assert CustomerLogSummary is not None
        assert CustomerLogDetail is not None
        assert CustomerLogListResponse is not None

    def test_logs_adapter_list_logs_method_signature(self):
        """L3 adapter must have list_logs with tenant_id parameter."""
        from app.adapters.customer_logs_adapter import CustomerLogsAdapter

        # Contract: list_logs method exists and requires tenant_id
        method = getattr(CustomerLogsAdapter, "list_logs")
        sig = inspect.signature(method)
        assert "tenant_id" in sig.parameters
        # Contract: Method is async
        assert inspect.iscoroutinefunction(method)

    def test_logs_adapter_get_log_method_signature(self):
        """L3 adapter must have get_log with tenant_id parameter."""
        from app.adapters.customer_logs_adapter import CustomerLogsAdapter

        # Contract: get_log method exists and requires tenant_id
        method = getattr(CustomerLogsAdapter, "get_log")
        sig = inspect.signature(method)
        assert "tenant_id" in sig.parameters
        # Contract: Method is async
        assert inspect.iscoroutinefunction(method)

    def test_customer_log_summary_no_cost_field(self):
        """L3 contract: CustomerLogSummary should NOT expose cost_cents."""
        from app.adapters.customer_logs_adapter import CustomerLogSummary

        # Contract: Cost is internal metric, not exposed to customers
        summary = CustomerLogSummary(
            log_id="log-123",
            run_id="run-456",
            status="completed",
            total_steps=5,
            success_count=4,
            failure_count=1,
            started_at="2026-01-03T00:00:00Z",
        )

        # Contract: Cost field should NOT exist
        assert not hasattr(summary, "cost_cents")
        assert not hasattr(summary, "total_cost")


# =============================================================================
# CROSS-ADAPTER CONTRACT TESTS
# =============================================================================


class TestL3AdapterContracts:
    """Cross-cutting contract tests for all L3 adapters."""

    def test_incidents_and_keys_adapters_require_session(self):
        """Incidents and Keys adapters require a Session for initialization."""
        from app.adapters.customer_incidents_adapter import CustomerIncidentsAdapter
        from app.adapters.customer_keys_adapter import CustomerKeysAdapter

        mock_session = MagicMock()

        # Contract: Adapters accept Session
        with patch("app.adapters.customer_incidents_adapter.get_incident_read_service"):
            with patch("app.adapters.customer_incidents_adapter.get_incident_write_service"):
                incidents_adapter = CustomerIncidentsAdapter(mock_session)
                assert incidents_adapter._session == mock_session

        with patch("app.adapters.customer_keys_adapter.get_keys_read_service"):
            with patch("app.adapters.customer_keys_adapter.get_keys_write_service"):
                keys_adapter = CustomerKeysAdapter(mock_session)
                assert keys_adapter._session == mock_session

    def test_incidents_adapter_methods_require_tenant_id(self):
        """Incidents adapter methods must require tenant_id for tenant isolation."""
        from app.adapters.customer_incidents_adapter import CustomerIncidentsAdapter

        # Contract: These methods must have tenant_id parameter
        incidents_methods = ["list_incidents", "get_incident", "acknowledge_incident", "resolve_incident"]

        for method_name in incidents_methods:
            method = getattr(CustomerIncidentsAdapter, method_name)
            sig = inspect.signature(method)
            assert "tenant_id" in sig.parameters, f"CustomerIncidentsAdapter.{method_name} missing tenant_id"

    def test_keys_adapter_methods_require_tenant_id(self):
        """Keys adapter methods must require tenant_id for tenant isolation."""
        from app.adapters.customer_keys_adapter import CustomerKeysAdapter

        # Contract: These methods must have tenant_id parameter
        keys_methods = ["list_keys", "get_key", "freeze_key", "unfreeze_key"]

        for method_name in keys_methods:
            method = getattr(CustomerKeysAdapter, method_name)
            sig = inspect.signature(method)
            assert "tenant_id" in sig.parameters, f"CustomerKeysAdapter.{method_name} missing tenant_id"

    def test_all_adapters_export_via_all(self):
        """All adapters should have __all__ defined for explicit exports."""
        from app.adapters import customer_incidents_adapter, customer_keys_adapter, customer_logs_adapter

        # Contract: __all__ is defined
        assert hasattr(customer_incidents_adapter, "__all__")
        assert hasattr(customer_keys_adapter, "__all__")
        assert hasattr(customer_logs_adapter, "__all__")

        # Contract: Main adapter class is exported
        assert "CustomerIncidentsAdapter" in customer_incidents_adapter.__all__
        assert "CustomerKeysAdapter" in customer_keys_adapter.__all__
        assert "CustomerLogsAdapter" in customer_logs_adapter.__all__


# =============================================================================
# ACTIVITY ADAPTER CONTRACT TESTS
# =============================================================================


class TestCustomerActivityAdapterContract:
    """Contract tests for CustomerActivityAdapter (L3).

    ACTIVITY Domain Qualification:
    - GATE-8: L2→L3 contract adherence
    - Customer-safe schema (no cost_cents)
    - Tenant isolation via tenant_id requirement
    """

    def test_list_activities_returns_customer_safe_schema(self):
        """L3 must return customer-safe activity summaries (no cost_cents)."""
        from app.adapters.customer_activity_adapter import (
            CustomerActivityAdapter,
            CustomerActivityListResponse,
            CustomerActivitySummary,
        )
        from app.services.activity.customer_activity_read_service import (
            ActivityListResult,
            ActivitySummary,
        )

        mock_read_service = MagicMock()

        # Mock L4 service response
        mock_summary = ActivitySummary(
            run_id="run-123",
            worker_name="worker-abc",
            task_preview="Test task for customer...",
            status="completed",
            success=True,
            total_steps=5,
            duration_ms=1500,
            created_at="2026-01-04T00:00:00Z",
            completed_at="2026-01-04T00:00:01.5Z",
        )

        mock_read_service.list_activities.return_value = ActivityListResult(
            items=[mock_summary],
            total=1,
            limit=20,
            offset=0,
            has_more=False,
        )

        with patch(
            "app.adapters.customer_activity_adapter.get_customer_activity_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerActivityAdapter()
            result = adapter.list_activities(tenant_id="tenant-123", limit=20, offset=0)

        # Contract assertions
        assert isinstance(result, CustomerActivityListResponse)
        assert len(result.items) == 1
        assert isinstance(result.items[0], CustomerActivitySummary)
        assert result.items[0].run_id == "run-123"
        assert result.items[0].status == "completed"
        assert result.items[0].success is True

    def test_get_activity_returns_customer_safe_detail(self):
        """L3 must return customer-safe activity detail (no cost_cents, no replay_token)."""
        from app.adapters.customer_activity_adapter import (
            CustomerActivityAdapter,
            CustomerActivityDetail,
        )
        from app.services.activity.customer_activity_read_service import ActivityDetail

        mock_read_service = MagicMock()

        # Mock L4 service response
        mock_detail = ActivityDetail(
            run_id="run-123",
            worker_name="worker-abc",
            task="Full task description for the customer to see...",
            status="completed",
            success=True,
            error_summary=None,
            total_steps=5,
            recoveries=1,
            policy_violations=0,
            duration_ms=1500,
            created_at="2026-01-04T00:00:00Z",
            started_at="2026-01-04T00:00:00.1Z",
            completed_at="2026-01-04T00:00:01.5Z",
        )

        mock_read_service.get_activity.return_value = mock_detail

        with patch(
            "app.adapters.customer_activity_adapter.get_customer_activity_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerActivityAdapter()
            result = adapter.get_activity(tenant_id="tenant-123", run_id="run-123")

        # Contract assertions
        assert isinstance(result, CustomerActivityDetail)
        assert result.run_id == "run-123"
        assert result.status == "completed"
        assert result.recoveries == 1
        assert result.policy_violations == 0

    def test_customer_activity_summary_no_cost_field(self):
        """L3 contract: CustomerActivitySummary should NOT expose cost_cents."""
        from app.adapters.customer_activity_adapter import CustomerActivitySummary

        # Create a summary
        summary = CustomerActivitySummary(
            run_id="run-123",
            worker_name="worker-abc",
            task_preview="Test task...",
            status="completed",
            success=True,
            total_steps=5,
            duration_ms=1500,
            created_at="2026-01-04T00:00:00Z",
            completed_at="2026-01-04T00:00:01.5Z",
        )

        # Contract: Cost fields should NOT exist
        assert not hasattr(summary, "cost_cents")
        assert not hasattr(summary, "total_cost")
        assert not hasattr(summary, "estimated_cost")

    def test_customer_activity_detail_no_internal_fields(self):
        """L3 contract: CustomerActivityDetail should NOT expose internal fields."""
        from app.adapters.customer_activity_adapter import CustomerActivityDetail

        # Create a detail
        detail = CustomerActivityDetail(
            run_id="run-123",
            worker_name="worker-abc",
            task="Full task description...",
            status="completed",
            success=True,
            error_summary=None,
            total_steps=5,
            recoveries=0,
            policy_violations=0,
            duration_ms=1500,
            created_at="2026-01-04T00:00:00Z",
            started_at="2026-01-04T00:00:00.1Z",
            completed_at="2026-01-04T00:00:01.5Z",
        )

        # Contract: Internal fields should NOT exist
        assert not hasattr(detail, "cost_cents")
        assert not hasattr(detail, "replay_token")
        assert not hasattr(detail, "input_json")
        assert not hasattr(detail, "output_json")

    def test_list_activities_requires_tenant_id(self):
        """L3 must enforce tenant isolation - missing tenant_id raises ValueError."""
        from app.adapters.customer_activity_adapter import CustomerActivityAdapter

        mock_read_service = MagicMock()

        with patch(
            "app.adapters.customer_activity_adapter.get_customer_activity_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerActivityAdapter()

            # Contract: Empty tenant_id raises ValueError
            with pytest.raises(ValueError, match="tenant_id is required"):
                adapter.list_activities(tenant_id="", limit=20, offset=0)

    def test_get_activity_requires_tenant_id(self):
        """L3 must enforce tenant isolation - missing tenant_id raises ValueError."""
        from app.adapters.customer_activity_adapter import CustomerActivityAdapter

        mock_read_service = MagicMock()

        with patch(
            "app.adapters.customer_activity_adapter.get_customer_activity_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerActivityAdapter()

            # Contract: Empty tenant_id raises ValueError
            with pytest.raises(ValueError, match="tenant_id is required"):
                adapter.get_activity(tenant_id="", run_id="run-123")

    def test_get_activity_requires_run_id(self):
        """L3 must require run_id for get_activity."""
        from app.adapters.customer_activity_adapter import CustomerActivityAdapter

        mock_read_service = MagicMock()

        with patch(
            "app.adapters.customer_activity_adapter.get_customer_activity_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerActivityAdapter()

            # Contract: Empty run_id raises ValueError
            with pytest.raises(ValueError, match="run_id is required"):
                adapter.get_activity(tenant_id="tenant-123", run_id="")

    def test_activity_adapter_methods_require_tenant_id(self):
        """Activity adapter methods must require tenant_id for tenant isolation."""
        from app.adapters.customer_activity_adapter import CustomerActivityAdapter

        # Contract: These methods must have tenant_id parameter
        activity_methods = ["list_activities", "get_activity"]

        for method_name in activity_methods:
            method = getattr(CustomerActivityAdapter, method_name)
            sig = inspect.signature(method)
            assert "tenant_id" in sig.parameters, f"CustomerActivityAdapter.{method_name} missing tenant_id"

    def test_activity_adapter_exports_via_all(self):
        """Activity adapter should have __all__ defined for explicit exports."""
        from app.adapters import customer_activity_adapter

        # Contract: __all__ is defined
        assert hasattr(customer_activity_adapter, "__all__")

        # Contract: Main adapter class and DTOs are exported
        assert "CustomerActivityAdapter" in customer_activity_adapter.__all__
        assert "CustomerActivitySummary" in customer_activity_adapter.__all__
        assert "CustomerActivityDetail" in customer_activity_adapter.__all__
        assert "CustomerActivityListResponse" in customer_activity_adapter.__all__
        assert "get_customer_activity_adapter" in customer_activity_adapter.__all__

    def test_activity_adapter_uses_singleton_pattern(self):
        """Activity adapter uses singleton pattern for L4 service access."""
        from app.adapters.customer_activity_adapter import CustomerActivityAdapter

        with patch("app.adapters.customer_activity_adapter.get_customer_activity_read_service") as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            adapter = CustomerActivityAdapter()
            # First call - service should be lazily loaded
            service1 = adapter._get_service()
            mock_get_service.assert_called_once()

            # Second call - should reuse cached service
            service2 = adapter._get_service()
            # Still only one call (cached)
            mock_get_service.assert_called_once()
            assert service1 is service2


# =============================================================================
# POLICY ADAPTER CONTRACT TESTS
# =============================================================================


class TestCustomerPoliciesAdapterContract:
    """Contract tests for CustomerPoliciesAdapter (L3).

    POLICY Domain Qualification:
    - GATE-8: L2→L3 contract adherence
    - Customer-safe schema (no threshold values, no rule configs)
    - Tenant isolation via tenant_id requirement
    """

    def test_get_policy_constraints_returns_customer_safe_schema(self):
        """L3 must return customer-safe policy constraints (no thresholds)."""
        from app.adapters.customer_policies_adapter import (
            CustomerBudgetConstraint,
            CustomerGuardrail,
            CustomerPoliciesAdapter,
            CustomerPolicyConstraints,
            CustomerRateLimit,
        )
        from app.services.policy.customer_policy_read_service import (
            BudgetConstraint,
            GuardrailSummary,
            PolicyConstraints,
            RateLimit,
        )

        mock_read_service = MagicMock()

        # Mock L4 service response
        mock_budget = BudgetConstraint(
            limit_cents=10000,
            period="daily",
            current_usage_cents=5000,
            remaining_cents=5000,
            percentage_used=50.0,
            reset_at="2026-01-05T00:00:00Z",
        )

        mock_rate_limit = RateLimit(
            requests_per_period=1000,
            period="hour",
            current_usage=100,
            remaining=900,
        )

        mock_guardrail = GuardrailSummary(
            id="guardrail-123",
            name="Budget Guard",
            description="Limits daily spend",
            enabled=True,
            category="cost",
            action_on_trigger="block",
        )

        mock_read_service.get_policy_constraints.return_value = PolicyConstraints(
            tenant_id="tenant-123",
            budget=mock_budget,
            rate_limits=[mock_rate_limit],
            guardrails=[mock_guardrail],
            last_updated="2026-01-04T00:00:00Z",
        )

        with patch(
            "app.adapters.customer_policies_adapter.get_customer_policy_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerPoliciesAdapter()
            result = adapter.get_policy_constraints(tenant_id="tenant-123")

        # Contract assertions
        assert isinstance(result, CustomerPolicyConstraints)
        assert result.tenant_id == "tenant-123"
        assert isinstance(result.budget, CustomerBudgetConstraint)
        assert result.budget.limit_cents == 10000
        assert result.budget.percentage_used == 50.0
        assert len(result.rate_limits) == 1
        assert isinstance(result.rate_limits[0], CustomerRateLimit)
        assert len(result.guardrails) == 1
        assert isinstance(result.guardrails[0], CustomerGuardrail)
        assert result.guardrails[0].action_on_trigger == "block"

    def test_get_guardrail_detail_returns_customer_safe_detail(self):
        """L3 must return customer-safe guardrail detail (no thresholds)."""
        from app.adapters.customer_policies_adapter import (
            CustomerGuardrail,
            CustomerPoliciesAdapter,
        )
        from app.services.policy.customer_policy_read_service import GuardrailSummary

        mock_read_service = MagicMock()

        # Mock L4 service response
        mock_guardrail = GuardrailSummary(
            id="guardrail-123",
            name="Rate Limiter",
            description="Prevents API abuse",
            enabled=True,
            category="rate",
            action_on_trigger="throttle",
        )

        mock_read_service.get_guardrail_detail.return_value = mock_guardrail

        with patch(
            "app.adapters.customer_policies_adapter.get_customer_policy_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerPoliciesAdapter()
            result = adapter.get_guardrail_detail(
                tenant_id="tenant-123",
                guardrail_id="guardrail-123",
            )

        # Contract assertions
        assert isinstance(result, CustomerGuardrail)
        assert result.id == "guardrail-123"
        assert result.name == "Rate Limiter"
        assert result.enabled is True
        assert result.action_on_trigger == "throttle"

    def test_customer_guardrail_no_threshold_fields(self):
        """L3 contract: CustomerGuardrail should NOT expose threshold values."""
        from app.adapters.customer_policies_adapter import CustomerGuardrail

        # Create a guardrail
        guardrail = CustomerGuardrail(
            id="guardrail-123",
            name="Cost Guard",
            description="Blocks expensive operations",
            enabled=True,
            category="cost",
            action_on_trigger="block",
        )

        # Contract: Threshold/config fields should NOT exist
        assert not hasattr(guardrail, "threshold")
        assert not hasattr(guardrail, "threshold_value")
        assert not hasattr(guardrail, "rule_config")
        assert not hasattr(guardrail, "rule_config_json")
        assert not hasattr(guardrail, "priority")
        assert not hasattr(guardrail, "rule_type")

    def test_customer_policy_constraints_no_internal_fields(self):
        """L3 contract: CustomerPolicyConstraints should NOT expose internal fields."""
        from app.adapters.customer_policies_adapter import CustomerPolicyConstraints

        # Create policy constraints
        constraints = CustomerPolicyConstraints(
            tenant_id="tenant-123",
            budget=None,
            rate_limits=[],
            guardrails=[],
            last_updated="2026-01-04T00:00:00Z",
        )

        # Contract: Internal fields should NOT exist
        assert not hasattr(constraints, "internal_config")
        assert not hasattr(constraints, "enforcement_level")
        assert not hasattr(constraints, "policy_version")

    def test_get_policy_constraints_requires_tenant_id(self):
        """L3 must enforce tenant isolation - missing tenant_id raises ValueError."""
        from app.adapters.customer_policies_adapter import CustomerPoliciesAdapter

        mock_read_service = MagicMock()

        with patch(
            "app.adapters.customer_policies_adapter.get_customer_policy_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerPoliciesAdapter()

            # Contract: Empty tenant_id raises ValueError
            with pytest.raises(ValueError, match="tenant_id is required"):
                adapter.get_policy_constraints(tenant_id="")

    def test_get_guardrail_detail_requires_tenant_id(self):
        """L3 must enforce tenant isolation - missing tenant_id raises ValueError."""
        from app.adapters.customer_policies_adapter import CustomerPoliciesAdapter

        mock_read_service = MagicMock()

        with patch(
            "app.adapters.customer_policies_adapter.get_customer_policy_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerPoliciesAdapter()

            # Contract: Empty tenant_id raises ValueError
            with pytest.raises(ValueError, match="tenant_id is required"):
                adapter.get_guardrail_detail(tenant_id="", guardrail_id="g-123")

    def test_get_guardrail_detail_requires_guardrail_id(self):
        """L3 must require guardrail_id for get_guardrail_detail."""
        from app.adapters.customer_policies_adapter import CustomerPoliciesAdapter

        mock_read_service = MagicMock()

        with patch(
            "app.adapters.customer_policies_adapter.get_customer_policy_read_service",
            return_value=mock_read_service,
        ):
            adapter = CustomerPoliciesAdapter()

            # Contract: Empty guardrail_id raises ValueError
            with pytest.raises(ValueError, match="guardrail_id is required"):
                adapter.get_guardrail_detail(tenant_id="tenant-123", guardrail_id="")

    def test_policies_adapter_methods_require_tenant_id(self):
        """Policies adapter methods must require tenant_id for tenant isolation."""
        from app.adapters.customer_policies_adapter import CustomerPoliciesAdapter

        # Contract: These methods must have tenant_id parameter
        policies_methods = ["get_policy_constraints", "get_guardrail_detail"]

        for method_name in policies_methods:
            method = getattr(CustomerPoliciesAdapter, method_name)
            sig = inspect.signature(method)
            assert "tenant_id" in sig.parameters, f"CustomerPoliciesAdapter.{method_name} missing tenant_id"

    def test_policies_adapter_exports_via_all(self):
        """Policies adapter should have __all__ defined for explicit exports."""
        from app.adapters import customer_policies_adapter

        # Contract: __all__ is defined
        assert hasattr(customer_policies_adapter, "__all__")

        # Contract: Main adapter class and DTOs are exported
        assert "CustomerPoliciesAdapter" in customer_policies_adapter.__all__
        assert "CustomerPolicyConstraints" in customer_policies_adapter.__all__
        assert "CustomerGuardrail" in customer_policies_adapter.__all__
        assert "CustomerBudgetConstraint" in customer_policies_adapter.__all__
        assert "CustomerRateLimit" in customer_policies_adapter.__all__
        assert "get_customer_policies_adapter" in customer_policies_adapter.__all__

    def test_policies_adapter_uses_singleton_pattern(self):
        """Policies adapter uses singleton pattern for L4 service access."""
        from app.adapters.customer_policies_adapter import CustomerPoliciesAdapter

        with patch("app.adapters.customer_policies_adapter.get_customer_policy_read_service") as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            adapter = CustomerPoliciesAdapter()
            # First call - service should be lazily loaded
            service1 = adapter._get_service()
            mock_get_service.assert_called_once()

            # Second call - should reuse cached service
            service2 = adapter._get_service()
            # Still only one call (cached)
            mock_get_service.assert_called_once()
            assert service1 is service2


# =============================================================================
# KILLSWITCH ADAPTER CONTRACT TESTS
# =============================================================================


class TestCustomerKillswitchAdapterContract:
    """Contract tests for CustomerKillswitchAdapter (L3).

    KILLSWITCH Domain Qualification:
    - GATE-8: L2→L3 contract adherence
    - Customer-safe schema (no internal state details)
    - Tenant isolation via tenant_id requirement
    """

    def test_get_status_returns_customer_safe_schema(self):
        """L3 must return customer-safe killswitch status."""
        from app.adapters.customer_killswitch_adapter import (
            CustomerKillswitchAdapter,
            CustomerKillswitchStatus,
        )
        from app.services.killswitch.customer_killswitch_read_service import (
            IncidentStats,
            KillswitchState,
            KillswitchStatusInfo,
        )

        mock_session = MagicMock()
        mock_read_service = MagicMock()
        mock_write_service = MagicMock()

        # Mock L4 service response
        mock_read_service.get_killswitch_status.return_value = KillswitchStatusInfo(
            state=KillswitchState(
                is_frozen=True,
                frozen_at=datetime(2026, 1, 4, 12, 0, 0, tzinfo=timezone.utc),
                frozen_by="customer",
            ),
            active_guardrails=["Budget Guard", "Rate Limiter"],
            incident_stats=IncidentStats(
                incidents_blocked_24h=5,
                last_incident_time=datetime(2026, 1, 4, 11, 30, 0, tzinfo=timezone.utc),
            ),
        )

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)
                result = adapter.get_status(tenant_id="tenant-123")

        # Contract assertions
        assert isinstance(result, CustomerKillswitchStatus)
        assert result.is_frozen is True
        assert result.frozen_by == "customer"
        assert result.incidents_blocked_24h == 5
        assert len(result.active_guardrails) == 2
        assert "Budget Guard" in result.active_guardrails
        # Contract: Datetime is ISO format string
        assert "2026-01-04" in result.frozen_at
        assert "2026-01-04" in result.last_incident_time

    def test_activate_returns_customer_safe_action(self):
        """L3 must return customer-safe action result on activate."""
        from app.adapters.customer_killswitch_adapter import (
            CustomerKillswitchAction,
            CustomerKillswitchAdapter,
        )

        mock_session = MagicMock()
        mock_write_service = MagicMock()
        mock_read_service = MagicMock()

        # Mock state - not frozen
        mock_state = MagicMock()
        mock_state.is_frozen = False
        mock_write_service.get_or_create_killswitch_state.return_value = (mock_state, False)

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)
                result = adapter.activate(tenant_id="tenant-123")

        # Contract assertions
        assert isinstance(result, CustomerKillswitchAction)
        assert result.status == "frozen"
        assert "stopped" in result.message.lower() or "protected" in result.message.lower()
        assert result.frozen_at is not None
        # Contract: Write service was called
        mock_write_service.freeze_killswitch.assert_called_once()

    def test_deactivate_returns_customer_safe_action(self):
        """L3 must return customer-safe action result on deactivate."""
        from app.adapters.customer_killswitch_adapter import (
            CustomerKillswitchAction,
            CustomerKillswitchAdapter,
        )

        mock_session = MagicMock()
        mock_write_service = MagicMock()
        mock_read_service = MagicMock()

        # Mock state - frozen
        mock_state = MagicMock()
        mock_state.is_frozen = True
        mock_write_service.get_or_create_killswitch_state.return_value = (mock_state, False)

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)
                result = adapter.deactivate(tenant_id="tenant-123")

        # Contract assertions
        assert isinstance(result, CustomerKillswitchAction)
        assert result.status == "active"
        assert "resumed" in result.message.lower()
        assert result.frozen_at is None
        # Contract: Write service was called
        mock_write_service.unfreeze_killswitch.assert_called_once()

    def test_customer_killswitch_status_no_internal_fields(self):
        """L3 contract: CustomerKillswitchStatus should NOT expose internal fields."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchStatus

        # Create a status
        status = CustomerKillswitchStatus(
            is_frozen=True,
            frozen_at="2026-01-04T00:00:00Z",
            frozen_by="customer",
            incidents_blocked_24h=5,
            active_guardrails=["Budget Guard"],
            last_incident_time="2026-01-04T00:00:00Z",
        )

        # Contract: Internal fields should NOT exist
        assert not hasattr(status, "entity_type")
        assert not hasattr(status, "entity_id")
        assert not hasattr(status, "freeze_reason")
        assert not hasattr(status, "freeze_trigger")
        assert not hasattr(status, "auto_frozen")

    def test_customer_killswitch_action_no_internal_fields(self):
        """L3 contract: CustomerKillswitchAction should NOT expose internal fields."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAction

        # Create an action result
        action = CustomerKillswitchAction(
            status="frozen",
            message="Traffic stopped.",
            frozen_at="2026-01-04T00:00:00Z",
        )

        # Contract: Internal fields should NOT exist
        assert not hasattr(action, "state_id")
        assert not hasattr(action, "trigger_type")
        assert not hasattr(action, "auto")
        assert not hasattr(action, "reason")

    def test_get_status_requires_tenant_id(self):
        """L3 must enforce tenant isolation - missing tenant_id raises ValueError."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAdapter

        mock_session = MagicMock()
        mock_read_service = MagicMock()
        mock_write_service = MagicMock()

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)

                # Contract: Empty tenant_id raises ValueError
                with pytest.raises(ValueError, match="tenant_id is required"):
                    adapter.get_status(tenant_id="")

    def test_activate_requires_tenant_id(self):
        """L3 must enforce tenant isolation - missing tenant_id raises ValueError."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAdapter

        mock_session = MagicMock()
        mock_read_service = MagicMock()
        mock_write_service = MagicMock()

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)

                # Contract: Empty tenant_id raises ValueError
                with pytest.raises(ValueError, match="tenant_id is required"):
                    adapter.activate(tenant_id="")

    def test_deactivate_requires_tenant_id(self):
        """L3 must enforce tenant isolation - missing tenant_id raises ValueError."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAdapter

        mock_session = MagicMock()
        mock_read_service = MagicMock()
        mock_write_service = MagicMock()

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)

                # Contract: Empty tenant_id raises ValueError
                with pytest.raises(ValueError, match="tenant_id is required"):
                    adapter.deactivate(tenant_id="")

    def test_killswitch_adapter_methods_require_tenant_id(self):
        """Killswitch adapter methods must require tenant_id for tenant isolation."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAdapter

        # Contract: These methods must have tenant_id parameter
        killswitch_methods = ["get_status", "activate", "deactivate"]

        for method_name in killswitch_methods:
            method = getattr(CustomerKillswitchAdapter, method_name)
            sig = inspect.signature(method)
            assert "tenant_id" in sig.parameters, f"CustomerKillswitchAdapter.{method_name} missing tenant_id"

    def test_killswitch_adapter_exports_via_all(self):
        """Killswitch adapter should have __all__ defined for explicit exports."""
        from app.adapters import customer_killswitch_adapter

        # Contract: __all__ is defined
        assert hasattr(customer_killswitch_adapter, "__all__")

        # Contract: Main adapter class and DTOs are exported
        assert "CustomerKillswitchAdapter" in customer_killswitch_adapter.__all__
        assert "CustomerKillswitchStatus" in customer_killswitch_adapter.__all__
        assert "CustomerKillswitchAction" in customer_killswitch_adapter.__all__
        assert "get_customer_killswitch_adapter" in customer_killswitch_adapter.__all__

    def test_killswitch_adapter_requires_session(self):
        """Killswitch adapter requires a Session for initialization (for write operations)."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAdapter

        mock_session = MagicMock()
        mock_write_service = MagicMock()

        with patch(
            "app.adapters.customer_killswitch_adapter.GuardWriteService",
            return_value=mock_write_service,
        ):
            adapter = CustomerKillswitchAdapter(mock_session)
            assert adapter._session == mock_session

    def test_activate_already_frozen_raises_error(self):
        """L3 must raise ValueError if killswitch already activated."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAdapter

        mock_session = MagicMock()
        mock_write_service = MagicMock()
        mock_read_service = MagicMock()

        # Mock state - already frozen
        mock_state = MagicMock()
        mock_state.is_frozen = True
        mock_write_service.get_or_create_killswitch_state.return_value = (mock_state, False)

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)

                # Contract: Already frozen raises ValueError
                with pytest.raises(ValueError, match="already stopped"):
                    adapter.activate(tenant_id="tenant-123")

    def test_deactivate_not_frozen_raises_error(self):
        """L3 must raise ValueError if killswitch not activated."""
        from app.adapters.customer_killswitch_adapter import CustomerKillswitchAdapter

        mock_session = MagicMock()
        mock_write_service = MagicMock()
        mock_read_service = MagicMock()

        # Mock state - not frozen
        mock_state = MagicMock()
        mock_state.is_frozen = False
        mock_write_service.get_or_create_killswitch_state.return_value = (mock_state, False)

        with patch(
            "app.adapters.customer_killswitch_adapter.get_customer_killswitch_read_service",
            return_value=mock_read_service,
        ):
            with patch(
                "app.adapters.customer_killswitch_adapter.GuardWriteService",
                return_value=mock_write_service,
            ):
                adapter = CustomerKillswitchAdapter(mock_session)

                # Contract: Not frozen raises ValueError
                with pytest.raises(ValueError, match="not stopped"):
                    adapter.deactivate(tenant_id="tenant-123")
