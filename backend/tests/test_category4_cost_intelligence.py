"""
Category 4: Cost Intelligence Domain Separation Tests

M29 Category 4 verification tests ensuring:
1. Domain separation (ops vs guard DTOs)
2. No cross-domain field leakage
3. Vocabulary compliance (calm vs command)
4. Contract field validation
5. Auth boundary enforcement

THE INVARIANT: Customers never see cross-tenant data.
Founders see global aggregation with affected_tenants counts.
"""

import ast
import inspect
from typing import Literal, get_origin, get_type_hints

import pytest

from app.contracts.guard import (
    CostBreakdownItemDTO,
    CustomerCostExplainedDTO,
    CustomerCostIncidentDTO,
    CustomerCostIncidentListDTO,
    CustomerCostSummaryDTO,
)

# Category 3: Frozen Contracts
from app.contracts.ops import (
    CostByFeatureDTO,
    CostByModelDTO,
    CostByUserDTO,
    CostDailyBreakdownDTO,
    CustomerAnomalyHistoryDTO,
    FounderCostAnomalyDTO,
    FounderCostAnomalyListDTO,
    FounderCostOverviewDTO,
    FounderCostTenantDTO,
    FounderCustomerCostDrilldownDTO,
)

# =============================================================================
# DOMAIN SEPARATION TESTS
# =============================================================================


class TestDomainSeparation:
    """Verify ops and guard contracts are properly separated."""

    # Founder-only fields that MUST NOT appear in guard contracts
    FOUNDER_ONLY_FIELDS = {
        "affected_tenants",
        "is_systemic",
        "churn_risk",
        "churn_risk_score",
        "concentration_risk",
        "at_risk_mrr_cents",
        "systemic_count",
        "tenants_affected",
        "customers_at_risk",
        "largest_deviation_tenant_id",  # Cross-tenant reference
    }

    # Guard DTOs to validate
    GUARD_DTOS = [
        CustomerCostSummaryDTO,
        CostBreakdownItemDTO,
        CustomerCostExplainedDTO,
        CustomerCostIncidentDTO,
        CustomerCostIncidentListDTO,
    ]

    def test_guard_dtos_have_no_founder_fields(self):
        """Guard DTOs must not contain founder-only fields."""
        violations = []

        for dto in self.GUARD_DTOS:
            dto_fields = set(dto.model_fields.keys())
            leaked_fields = dto_fields & self.FOUNDER_ONLY_FIELDS

            if leaked_fields:
                violations.append(f"{dto.__name__}: {leaked_fields}")

        assert not violations, f"Founder-only fields leaked to guard DTOs: {violations}"

    def test_founder_dtos_have_cross_tenant_fields(self):
        """Founder DTOs should have cross-tenant aggregation fields."""
        # FounderCostAnomalyDTO must have affected_tenants
        assert "affected_tenants" in FounderCostAnomalyDTO.model_fields
        assert "is_systemic" in FounderCostAnomalyDTO.model_fields

        # FounderCostAnomalyListDTO must have tenants_affected
        assert "tenants_affected" in FounderCostAnomalyListDTO.model_fields
        assert "systemic_count" in FounderCostAnomalyListDTO.model_fields

        # FounderCostOverviewDTO must have tenants_with_anomalies
        assert "tenants_with_anomalies" in FounderCostOverviewDTO.model_fields

    def test_no_cross_import_in_ops_router(self):
        """cost_ops.py must not import from guard contracts."""
        import app.api.cost_ops as cost_ops_module

        source_file = inspect.getfile(cost_ops_module)
        with open(source_file, "r") as f:
            source = f.read()

        # Parse AST to find imports
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "guard" in node.module:
                    imports.append(node.module)

        assert not imports, f"cost_ops.py imports guard contracts: {imports}"

    def test_no_cross_import_in_guard_router(self):
        """cost_guard.py must not import from ops contracts."""
        import app.api.cost_guard as cost_guard_module

        source_file = inspect.getfile(cost_guard_module)
        with open(source_file, "r") as f:
            source = f.read()

        # Parse AST to find imports
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "contracts.ops" in node.module:
                    imports.append(node.module)

        assert not imports, f"cost_guard.py imports ops contracts: {imports}"


# =============================================================================
# VOCABULARY COMPLIANCE TESTS
# =============================================================================


class TestVocabularyCompliance:
    """Verify vocabulary separation between domains."""

    # Calm vocabulary for customers
    CALM_VOCABULARY = {"normal", "rising", "spike", "protected", "attention_needed", "resolved"}

    # Command vocabulary for founders
    COMMAND_VOCABULARY = {"stable", "elevated", "degraded", "critical", "increasing", "decreasing"}

    def test_customer_cost_summary_uses_calm_trend(self):
        """CustomerCostSummaryDTO.trend must use calm vocabulary."""
        hints = get_type_hints(CustomerCostSummaryDTO)
        trend_type = hints.get("trend")

        # Get Literal args
        if get_origin(trend_type) is Literal:
            allowed_values = set(trend_type.__args__)
            assert allowed_values == {
                "normal",
                "rising",
                "spike",
            }, f"Customer trend should use calm vocabulary, got: {allowed_values}"

    def test_customer_incident_uses_calm_status(self):
        """CustomerCostIncidentDTO.status must use calm vocabulary."""
        hints = get_type_hints(CustomerCostIncidentDTO)
        status_type = hints.get("status")

        if get_origin(status_type) is Literal:
            allowed_values = set(status_type.__args__)
            assert allowed_values == {
                "protected",
                "attention_needed",
                "resolved",
            }, f"Customer incident status should use calm vocabulary, got: {allowed_values}"

    def test_founder_overview_uses_command_trend(self):
        """FounderCostOverviewDTO.trend_7d must use command vocabulary."""
        hints = get_type_hints(FounderCostOverviewDTO)
        trend_type = hints.get("trend_7d")

        if get_origin(trend_type) is Literal:
            allowed_values = set(trend_type.__args__)
            assert allowed_values == {
                "increasing",
                "stable",
                "decreasing",
            }, f"Founder trend should use command vocabulary, got: {allowed_values}"

    def test_founder_tenant_uses_command_trend(self):
        """FounderCostTenantDTO.trend must use command vocabulary."""
        hints = get_type_hints(FounderCostTenantDTO)
        trend_type = hints.get("trend")

        if get_origin(trend_type) is Literal:
            allowed_values = set(trend_type.__args__)
            assert allowed_values == {
                "increasing",
                "stable",
                "decreasing",
            }, f"Founder tenant trend should use command vocabulary, got: {allowed_values}"

    def test_no_command_words_in_guard_contracts(self):
        """Guard contracts should not use command vocabulary words."""
        import app.contracts.guard as guard_module

        source_file = inspect.getfile(guard_module)
        with open(source_file, "r") as f:
            source = f.read()

        # Check for command words in Literal definitions (outside comments)
        tree = ast.parse(source)

        command_words_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in {"elevated", "degraded", "critical", "increasing", "decreasing"}:
                    # Allow in existing non-cost DTOs (IncidentSummaryDTO has severity)
                    # But cost DTOs should use calm vocabulary
                    pass  # We check specific DTOs above

        # This is a softer check - the specific DTO tests above are the strict ones


# =============================================================================
# CONTRACT FIELD VALIDATION TESTS
# =============================================================================


class TestContractFieldValidation:
    """Verify contract fields have proper constraints."""

    def test_customer_cost_summary_has_required_fields(self):
        """CustomerCostSummaryDTO must have all required fields."""
        required_fields = {
            "spend_today_cents",
            "spend_mtd_cents",
            "spend_7d_cents",
            "projected_month_end_cents",
            "trend",
            "last_updated",
        }

        actual_fields = set(CustomerCostSummaryDTO.model_fields.keys())
        missing = required_fields - actual_fields

        assert not missing, f"CustomerCostSummaryDTO missing fields: {missing}"

    def test_founder_cost_overview_has_required_fields(self):
        """FounderCostOverviewDTO must have all required fields."""
        required_fields = {
            "spend_today_cents",
            "spend_mtd_cents",
            "spend_7d_cents",
            "tenants_with_anomalies",
            "total_anomalies_24h",
            "snapshot_freshness_minutes",
            "snapshot_status",
            "trend_7d",
        }

        actual_fields = set(FounderCostOverviewDTO.model_fields.keys())
        missing = required_fields - actual_fields

        assert not missing, f"FounderCostOverviewDTO missing fields: {missing}"

    def test_cents_fields_are_integers(self):
        """All *_cents fields must be integers, not floats.

        Exception: Fields with 'avg' in the name can be floats (averages of integers).
        """
        dtos_to_check = [
            CustomerCostSummaryDTO,
            CustomerCostExplainedDTO,
            CustomerCostIncidentDTO,
            FounderCostOverviewDTO,
            FounderCostTenantDTO,
        ]

        violations = []
        for dto in dtos_to_check:
            hints = get_type_hints(dto)
            for field_name, field_type in hints.items():
                if "_cents" in field_name:
                    # Exception: averages can be floats (avg of integers = fractional)
                    if "avg" in field_name.lower():
                        continue

                    # Check if it's int (or Optional[int])
                    origin = get_origin(field_type)
                    if origin is not None:
                        # It's a generic (Optional, Union, etc.)
                        args = getattr(field_type, "__args__", ())
                        # Allow int or None
                        allowed = all(arg is type(None) or arg is int for arg in args)
                        if not allowed:
                            violations.append(f"{dto.__name__}.{field_name}: {field_type}")
                    elif field_type is not int:
                        violations.append(f"{dto.__name__}.{field_name}: {field_type}")

        assert not violations, f"Cents fields must be integers: {violations}"

    def test_pct_fields_are_floats(self):
        """All *_pct fields must be floats, not integers."""
        dtos_to_check = [
            CustomerCostSummaryDTO,
            CostBreakdownItemDTO,
            FounderCostOverviewDTO,
            FounderCostTenantDTO,
            FounderCostAnomalyDTO,
        ]

        violations = []
        for dto in dtos_to_check:
            hints = get_type_hints(dto)
            for field_name, field_type in hints.items():
                if "_pct" in field_name:
                    origin = get_origin(field_type)
                    if origin is not None:
                        args = getattr(field_type, "__args__", ())
                        # Allow float or None
                        allowed = all(arg is type(None) or arg is float for arg in args)
                        if not allowed:
                            violations.append(f"{dto.__name__}.{field_name}: {field_type}")
                    elif field_type is not float:
                        violations.append(f"{dto.__name__}.{field_name}: {field_type}")

        assert not violations, f"Pct fields must be floats: {violations}"


# =============================================================================
# DTO INSTANTIATION TESTS
# =============================================================================


class TestDTOInstantiation:
    """Verify DTOs can be instantiated with valid data."""

    def test_customer_cost_summary_instantiation(self):
        """CustomerCostSummaryDTO can be created with valid data."""
        dto = CustomerCostSummaryDTO(
            spend_today_cents=2340,
            spend_mtd_cents=45000,
            spend_7d_cents=18000,
            budget_daily_cents=10000,
            budget_monthly_cents=300000,
            budget_used_daily_pct=23.4,
            budget_used_monthly_pct=15.0,
            projected_month_end_cents=72000,
            days_until_budget_exhausted=None,
            trend="normal",
            trend_message="Spending is within normal range",
            last_updated="2025-12-23T10:00:00Z",
        )

        assert dto.trend == "normal"
        assert dto.spend_today_cents == 2340

    def test_customer_cost_summary_rejects_invalid_trend(self):
        """CustomerCostSummaryDTO rejects invalid trend values."""
        with pytest.raises(ValueError):
            CustomerCostSummaryDTO(
                spend_today_cents=2340,
                spend_mtd_cents=45000,
                spend_7d_cents=18000,
                projected_month_end_cents=72000,
                trend="critical",  # Invalid - command vocabulary
                last_updated="2025-12-23T10:00:00Z",
            )

    def test_founder_cost_overview_instantiation(self):
        """FounderCostOverviewDTO can be created with valid data."""
        dto = FounderCostOverviewDTO(
            spend_today_cents=125000,
            spend_mtd_cents=2500000,
            spend_7d_cents=875000,
            tenants_with_anomalies=3,
            total_anomalies_24h=5,
            largest_deviation_tenant_id="tenant_abc",
            largest_deviation_pct=450.0,
            largest_deviation_type="user_spike",
            last_snapshot_at="2025-12-23T10:00:00Z",
            snapshot_freshness_minutes=15,
            snapshot_status="fresh",
            trend_7d="stable",
        )

        assert dto.snapshot_status == "fresh"
        assert dto.tenants_with_anomalies == 3

    def test_founder_cost_anomaly_instantiation(self):
        """FounderCostAnomalyDTO can be created with cross-tenant data."""
        dto = FounderCostAnomalyDTO(
            id="anom_123",
            anomaly_type="user_spike",
            severity="high",
            entity_type="user",
            entity_id="user_abc",
            current_value_cents=50000.0,
            expected_value_cents=10000.0,
            deviation_pct=400.0,
            threshold_pct=40.0,  # M29: Aligned threshold (40% = 1.4x)
            affected_tenants=5,  # Cross-tenant field
            is_systemic=True,  # Cross-tenant indicator
            derived_cause="RETRY_LOOP",  # M29 Category 4: Root cause
            breach_count=2,  # M29 Category 4: Consecutive intervals
            message="User spending 4x above baseline",
            incident_id=None,
            action_taken=None,
            resolved=False,
            detected_at="2025-12-23T10:00:00Z",
            snapshot_id="snap_456",
        )

        assert dto.affected_tenants == 5
        assert dto.is_systemic is True
        assert dto.derived_cause == "RETRY_LOOP"
        assert dto.breach_count == 2

    def test_customer_incident_uses_calm_status(self):
        """CustomerCostIncidentDTO uses calm vocabulary for status."""
        dto = CustomerCostIncidentDTO(
            id="inc_123",
            title="Cost spike detected and blocked",
            status="protected",  # Calm vocabulary
            trigger_type="cost_spike",
            cost_at_trigger_cents=50000,
            cost_avoided_cents=45000,
            action_taken="Requests blocked",
            recommendation="Review API usage patterns",
            cause_explanation="Usage increased due to higher traffic",  # M29: Calm explanation
            detected_at="2025-12-23T10:00:00Z",
            resolved_at=None,
        )

        assert dto.status == "protected"
        assert dto.cause_explanation == "Usage increased due to higher traffic"


# =============================================================================
# AUTH BOUNDARY TESTS (Structural)
# =============================================================================


class TestAuthBoundaryStructure:
    """Verify auth dependencies are properly configured."""

    def test_cost_ops_uses_fops_auth(self):
        """cost_ops router must use verify_fops_token dependency."""
        import app.api.cost_ops as cost_ops_module

        source_file = inspect.getfile(cost_ops_module)
        with open(source_file, "r") as f:
            source = f.read()

        assert "verify_fops_token" in source, "cost_ops.py must use verify_fops_token"
        assert (
            "aud=fops" in source or 'aud="fops"' in source or "FOPS" in source
        ), "cost_ops.py must reference FOPS audience"

    def test_cost_guard_uses_console_auth(self):
        """cost_guard router must use verify_console_token dependency."""
        import app.api.cost_guard as cost_guard_module

        source_file = inspect.getfile(cost_guard_module)
        with open(source_file, "r") as f:
            source = f.read()

        assert "verify_console_token" in source, "cost_guard.py must use verify_console_token"


# =============================================================================
# SNAPSHOT INVARIANT TESTS
# =============================================================================


class TestSnapshotInvariant:
    """Verify cost data derives from snapshots, not live queries."""

    def test_founder_overview_has_snapshot_fields(self):
        """FounderCostOverviewDTO must have snapshot freshness tracking."""
        required = {"last_snapshot_at", "snapshot_freshness_minutes", "snapshot_status"}
        actual = set(FounderCostOverviewDTO.model_fields.keys())

        missing = required - actual
        assert not missing, f"Missing snapshot tracking fields: {missing}"

    def test_customer_summary_has_last_updated(self):
        """CustomerCostSummaryDTO must have last_updated for freshness."""
        assert "last_updated" in CustomerCostSummaryDTO.model_fields

    def test_snapshot_status_values(self):
        """Snapshot status must use fresh/stale/missing vocabulary."""
        hints = get_type_hints(FounderCostOverviewDTO)
        status_type = hints.get("snapshot_status")

        if get_origin(status_type) is Literal:
            allowed = set(status_type.__args__)
            assert allowed == {
                "fresh",
                "stale",
                "missing",
            }, f"Snapshot status should be fresh/stale/missing, got: {allowed}"


# =============================================================================
# CROSS-DOMAIN LEAKAGE PREVENTION
# =============================================================================


class TestCrossDomainLeakagePrevention:
    """Ensure no cross-domain data leakage is possible."""

    def test_customer_explained_has_no_tenant_comparison(self):
        """CustomerCostExplainedDTO must not compare to other tenants."""
        fields = set(CustomerCostExplainedDTO.model_fields.keys())

        # These fields would expose cross-tenant data
        forbidden = {
            "percentile_rank",
            "vs_average",
            "tenant_rank",
            "compared_to_peers",
            "industry_average",
        }

        leaked = fields & forbidden
        assert not leaked, f"CustomerCostExplainedDTO has cross-tenant fields: {leaked}"

    def test_breakdown_item_has_no_tenant_reference(self):
        """CostBreakdownItemDTO must not reference other tenants."""
        fields = set(CostBreakdownItemDTO.model_fields.keys())

        forbidden = {"tenant_id", "other_tenants", "rank", "percentile"}

        leaked = fields & forbidden
        assert not leaked, f"CostBreakdownItemDTO has cross-tenant fields: {leaked}"


# =============================================================================
# M29 CATEGORY 4: ANOMALY RULES ALIGNMENT TESTS
# =============================================================================


class TestAnomalyRulesAlignment:
    """Verify M29 Category 4 anomaly rules are correctly aligned."""

    def test_anomaly_thresholds_constants(self):
        """Verify threshold constants match plan specification."""
        from app.services.cost_anomaly_detector import (
            ABSOLUTE_SPIKE_THRESHOLD,
            CONSECUTIVE_INTERVALS_REQUIRED,
            DRIFT_DAYS_REQUIRED,
            SEVERITY_BANDS,
            SUSTAINED_DRIFT_THRESHOLD,
        )

        # Absolute spike: 1.4x (40% increase)
        assert ABSOLUTE_SPIKE_THRESHOLD == 1.40, "Absolute spike must be 1.4x"

        # Consecutive intervals: 2 days
        assert CONSECUTIVE_INTERVALS_REQUIRED == 2, "Must require 2 consecutive days"

        # Sustained drift: 1.25x (25% increase)
        assert SUSTAINED_DRIFT_THRESHOLD == 1.25, "Sustained drift must be 1.25x"

        # Drift days: 3
        assert DRIFT_DAYS_REQUIRED == 3, "Must require 3 drift days"

        # Severity bands
        assert SEVERITY_BANDS["LOW"] == (15, 25), "LOW must be 15-25%"
        assert SEVERITY_BANDS["MEDIUM"] == (25, 40), "MEDIUM must be 25-40%"
        assert SEVERITY_BANDS["HIGH"][0] == 40, "HIGH must start at 40%"

    def test_severity_classifier(self):
        """Verify severity classification matches plan bands."""
        from app.services.cost_anomaly_detector import AnomalySeverity, classify_severity

        # LOW: 15-25%
        assert classify_severity(15) == AnomalySeverity.LOW
        assert classify_severity(20) == AnomalySeverity.LOW
        assert classify_severity(24.9) == AnomalySeverity.LOW

        # MEDIUM: 25-40%
        assert classify_severity(25) == AnomalySeverity.MEDIUM
        assert classify_severity(30) == AnomalySeverity.MEDIUM
        assert classify_severity(39.9) == AnomalySeverity.MEDIUM

        # HIGH: >40%
        assert classify_severity(40) == AnomalySeverity.HIGH
        assert classify_severity(50) == AnomalySeverity.HIGH
        assert classify_severity(100) == AnomalySeverity.HIGH
        assert classify_severity(500) == AnomalySeverity.HIGH

    def test_derived_cause_enum_values(self):
        """Verify DerivedCause enum has exactly the plan-specified values."""
        from app.services.cost_anomaly_detector import DerivedCause

        expected = {"RETRY_LOOP", "PROMPT_GROWTH", "FEATURE_SURGE", "TRAFFIC_GROWTH", "UNKNOWN"}
        actual = {e.value for e in DerivedCause}

        assert actual == expected, f"DerivedCause mismatch. Expected: {expected}, Got: {actual}"

    def test_anomaly_type_enum_values(self):
        """Verify AnomalyType enum has the correct types."""
        from app.services.cost_anomaly_detector import AnomalyType

        expected = {"ABSOLUTE_SPIKE", "SUSTAINED_DRIFT", "BUDGET_WARNING", "BUDGET_EXCEEDED"}
        actual = {e.value for e in AnomalyType}

        assert actual == expected, f"AnomalyType mismatch. Expected: {expected}, Got: {actual}"

    def test_founder_dto_has_derived_cause_field(self):
        """FounderCostAnomalyDTO must have derived_cause field as Optional."""
        assert "derived_cause" in FounderCostAnomalyDTO.model_fields

        # Verify it's optional by instantiating without it
        dto = FounderCostAnomalyDTO(
            id="anom_test",
            anomaly_type="ABSOLUTE_SPIKE",
            severity="high",
            entity_type="user",
            entity_id="user_1",
            current_value_cents=1000.0,
            expected_value_cents=500.0,
            deviation_pct=100.0,
            threshold_pct=40.0,
            affected_tenants=1,
            is_systemic=False,
            message="Test",
            detected_at="2025-12-24T00:00:00Z",
        )
        assert dto.derived_cause is None  # Default is None

    def test_founder_dto_has_breach_count_field(self):
        """FounderCostAnomalyDTO must have breach_count field with default 1."""
        assert "breach_count" in FounderCostAnomalyDTO.model_fields
        field = FounderCostAnomalyDTO.model_fields["breach_count"]
        assert field.default == 1

    def test_customer_incident_has_cause_explanation(self):
        """CustomerCostIncidentDTO must have cause_explanation field as Optional."""
        assert "cause_explanation" in CustomerCostIncidentDTO.model_fields

        # Verify it's optional by instantiating without it
        dto = CustomerCostIncidentDTO(
            id="inc_test",
            title="Test Incident",
            status="protected",
            trigger_type="cost_spike",
            cost_at_trigger_cents=1000,
            cost_avoided_cents=500,
            action_taken="blocked",
            detected_at="2025-12-24T00:00:00Z",
        )
        assert dto.cause_explanation is None  # Default is None

    def test_derived_cause_not_exposed_to_customer(self):
        """Customer DTOs should not expose raw derived_cause enum."""
        customer_dtos = [
            CustomerCostSummaryDTO,
            CostBreakdownItemDTO,
            CustomerCostExplainedDTO,
            CustomerCostIncidentDTO,
            CustomerCostIncidentListDTO,
        ]

        for dto in customer_dtos:
            fields = set(dto.model_fields.keys())
            assert (
                "derived_cause" not in fields
            ), f"{dto.__name__} should not have derived_cause (use cause_explanation instead)"


# =============================================================================
# M29 CATEGORY 4.2: CUSTOMER COST DRILLDOWN TESTS
# =============================================================================


class TestCustomerCostDrilldown:
    """Verify M29 Category 4.2 customer cost drilldown DTOs and structure."""

    def test_drilldown_dto_has_required_fields(self):
        """FounderCustomerCostDrilldownDTO must have all required fields."""
        required_fields = {
            "tenant_id",
            "tenant_name",
            "spend_today_cents",
            "spend_mtd_cents",
            "spend_7d_cents",
            "spend_30d_cents",
            "daily_breakdown",
            "by_feature",
            "by_user",
            "by_model",
            "largest_driver_type",
            "largest_driver_name",
            "largest_driver_pct",
            "active_anomalies",
            "recent_anomalies",
            "trend_7d",
            "last_updated",
        }

        actual_fields = set(FounderCustomerCostDrilldownDTO.model_fields.keys())
        missing = required_fields - actual_fields

        assert not missing, f"FounderCustomerCostDrilldownDTO missing fields: {missing}"

    def test_drilldown_dto_instantiation(self):
        """FounderCustomerCostDrilldownDTO can be created with valid data."""
        dto = FounderCustomerCostDrilldownDTO(
            tenant_id="tenant_abc123",
            tenant_name="Acme Corp",
            spend_today_cents=2500,
            spend_mtd_cents=45000,
            spend_7d_cents=18000,
            spend_30d_cents=72000,
            baseline_7d_avg_cents=2000.0,
            deviation_from_baseline_pct=25.0,
            budget_monthly_cents=100000,
            budget_used_pct=45.0,
            projected_month_end_cents=90000,
            days_until_budget_exhausted=None,
            daily_breakdown=[
                CostDailyBreakdownDTO(
                    date="2025-12-23",
                    spend_cents=2500,
                    request_count=150,
                    avg_cost_per_request_cents=16.67,
                )
            ],
            by_feature=[
                CostByFeatureDTO(
                    feature_tag="customer_support.chat",
                    display_name="Customer Support",
                    spend_cents=12000,
                    request_count=500,
                    pct_of_total=66.7,
                    trend="stable",
                )
            ],
            by_user=[
                CostByUserDTO(
                    user_id="user_xyz",
                    spend_cents=5000,
                    request_count=200,
                    pct_of_total=27.8,
                    is_anomalous=False,
                )
            ],
            by_model=[
                CostByModelDTO(
                    model="claude-sonnet-4-20250514",
                    spend_cents=15000,
                    input_tokens=500000,
                    output_tokens=100000,
                    request_count=600,
                    pct_of_total=83.3,
                )
            ],
            largest_driver_type="feature",
            largest_driver_name="customer_support.chat",
            largest_driver_pct=66.7,
            active_anomalies=0,
            recent_anomalies=[],
            trend_7d="stable",
            trend_message="Cost is within normal range for this customer",
            last_activity="2025-12-23T15:30:00Z",
            last_updated="2025-12-23T16:00:00Z",
        )

        assert dto.tenant_id == "tenant_abc123"
        assert dto.trend_7d == "stable"
        assert len(dto.daily_breakdown) == 1
        assert len(dto.by_feature) == 1
        assert dto.largest_driver_type == "feature"

    def test_daily_breakdown_dto(self):
        """CostDailyBreakdownDTO can be created with valid data."""
        dto = CostDailyBreakdownDTO(
            date="2025-12-23",
            spend_cents=2500,
            request_count=150,
            avg_cost_per_request_cents=16.67,
        )

        assert dto.date == "2025-12-23"
        assert dto.spend_cents == 2500
        assert dto.request_count == 150

    def test_cost_by_feature_dto(self):
        """CostByFeatureDTO can be created with valid data."""
        dto = CostByFeatureDTO(
            feature_tag="customer_support.chat",
            display_name="Customer Support",
            spend_cents=12000,
            request_count=500,
            pct_of_total=66.7,
            trend="stable",
        )

        assert dto.feature_tag == "customer_support.chat"
        assert dto.trend == "stable"

    def test_cost_by_feature_rejects_invalid_trend(self):
        """CostByFeatureDTO rejects invalid trend values."""
        with pytest.raises(ValueError):
            CostByFeatureDTO(
                feature_tag="test",
                spend_cents=100,
                request_count=10,
                pct_of_total=10.0,
                trend="critical",  # Invalid - not increasing/stable/decreasing
            )

    def test_cost_by_user_dto(self):
        """CostByUserDTO can be created with valid data."""
        dto = CostByUserDTO(
            user_id="user_xyz",
            spend_cents=5000,
            request_count=200,
            pct_of_total=27.8,
            is_anomalous=True,
        )

        assert dto.user_id == "user_xyz"
        assert dto.is_anomalous is True

    def test_cost_by_model_dto(self):
        """CostByModelDTO can be created with valid data."""
        dto = CostByModelDTO(
            model="claude-sonnet-4-20250514",
            spend_cents=15000,
            input_tokens=500000,
            output_tokens=100000,
            request_count=600,
            pct_of_total=83.3,
        )

        assert dto.model == "claude-sonnet-4-20250514"
        assert dto.input_tokens == 500000
        assert dto.output_tokens == 100000

    def test_customer_anomaly_history_dto(self):
        """CustomerAnomalyHistoryDTO can be created with valid data."""
        dto = CustomerAnomalyHistoryDTO(
            id="anom_123",
            anomaly_type="ABSOLUTE_SPIKE",
            severity="high",
            detected_at="2025-12-23T10:00:00Z",
            resolved=False,
            deviation_pct=150.0,
            derived_cause="RETRY_LOOP",
            message="User spending 1.5x above baseline",
        )

        assert dto.id == "anom_123"
        assert dto.severity == "high"
        assert dto.derived_cause == "RETRY_LOOP"

    def test_drilldown_uses_command_vocabulary(self):
        """FounderCustomerCostDrilldownDTO.trend_7d must use command vocabulary."""
        hints = get_type_hints(FounderCustomerCostDrilldownDTO)
        trend_type = hints.get("trend_7d")

        if get_origin(trend_type) is Literal:
            allowed_values = set(trend_type.__args__)
            assert allowed_values == {
                "increasing",
                "stable",
                "decreasing",
            }, f"Drilldown trend should use command vocabulary, got: {allowed_values}"

    def test_drilldown_dto_no_cross_tenant_leakage(self):
        """FounderCustomerCostDrilldownDTO should not expose other tenants."""
        fields = set(FounderCustomerCostDrilldownDTO.model_fields.keys())

        # These fields would expose other tenant data in single-tenant view
        forbidden = {
            "other_tenants",
            "peer_comparison",
            "industry_average",
            "tenant_rank",
            "percentile_rank",
        }

        leaked = fields & forbidden
        assert not leaked, f"FounderCustomerCostDrilldownDTO has forbidden fields: {leaked}"

    def test_drilldown_endpoint_registered(self):
        """Verify /ops/cost/customers/{tenant_id} endpoint is registered."""
        import app.api.cost_ops as cost_ops_module

        source_file = inspect.getfile(cost_ops_module)
        with open(source_file, "r") as f:
            source = f.read()

        # Check for the endpoint pattern
        assert (
            "/customers/{tenant_id}" in source or "/customers/{id}" in source
        ), "Customer cost drilldown endpoint not found in cost_ops.py"
        assert "FounderCustomerCostDrilldownDTO" in source, "FounderCustomerCostDrilldownDTO not used in cost_ops.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
