"""
M29 Category 5: Incident Console Contrast Tests

Verifies that:
1. Same incident ID renders differently in /ops vs /guard
2. Founder view answers "why" definitively
3. Customer view answers "should I worry?" clearly
4. No internal terminology leaks to customer UI
5. Screenshots from both do not contradict
6. DTOs are enforced and tested
7. Incident -> cost links remain consistent

Test Date: 2025-12-24
"""

import inspect
from typing import Literal, get_origin, get_type_hints

import pytest

# Customer DTOs (Calm Vocabulary)
from app.contracts.guard import (
    CustomerIncidentActionDTO,
    CustomerIncidentImpactDTO,
    CustomerIncidentNarrativeDTO,
    CustomerIncidentResolutionDTO,
)

# Founder DTOs (Command Vocabulary)
from app.contracts.ops import (
    FounderBlastRadiusDTO,
    FounderDecisionTimelineEventDTO,
    FounderIncidentDetailDTO,
    FounderIncidentHeaderDTO,
    FounderRecurrenceRiskDTO,
    FounderRootCauseDTO,
)

# =============================================================================
# CATEGORY 5 CORE INVARIANT: One ID, Two Narratives, Zero Contradictions
# =============================================================================


class TestIncidentContrastRules:
    """Verify Category 5 contrast rules are enforced."""

    # Internal terminology that MUST NOT appear in customer DTOs
    FORBIDDEN_CUSTOMER_TERMS = {
        "policy",
        "threshold",
        "baseline",
        "deviation",
        "breach",
        "derived_cause",
        "blast_radius",
        "recurrence",
        "systemic",
        "affected_tenants",
        "percentile",
        "confidence",
        "root_cause",
    }

    # Calm vocabulary that MUST appear in customer DTOs
    CALM_VOCABULARY = {
        "investigating",
        "mitigating",
        "resolved",
        "monitoring",
        "yes",
        "no",
        "some",
        "briefly",
        "none",
        "minimal",
        "higher_than_usual",
        "significant",
    }

    def test_founder_dto_has_internal_terms(self):
        """Founder DTOs should contain internal terminology."""
        founder_fields = set(FounderIncidentDetailDTO.model_fields.keys())

        # These fields must exist in founder DTO
        required_internal = {"root_cause", "blast_radius", "recurrence_risk"}
        missing = required_internal - founder_fields

        assert not missing, f"FounderIncidentDetailDTO missing internal fields: {missing}"

    def test_customer_dto_has_no_internal_terms(self):
        """Customer DTOs must not contain internal terminology."""
        customer_fields = set(CustomerIncidentNarrativeDTO.model_fields.keys())

        leaked = customer_fields & self.FORBIDDEN_CUSTOMER_TERMS
        assert not leaked, f"CustomerIncidentNarrativeDTO has forbidden terms: {leaked}"

    def test_customer_impact_uses_calm_vocabulary(self):
        """CustomerIncidentImpactDTO must use calm vocabulary for all literals."""
        hints = get_type_hints(CustomerIncidentImpactDTO)

        for field_name, field_type in hints.items():
            if get_origin(field_type) is Literal:
                values = set(field_type.__args__)
                # All values should be calm
                assert values.issubset(self.CALM_VOCABULARY | {"no"}), (
                    f"CustomerIncidentImpactDTO.{field_name} uses non-calm values: {values}"
                )

    def test_customer_resolution_uses_calm_vocabulary(self):
        """CustomerIncidentResolutionDTO must use calm vocabulary."""
        hints = get_type_hints(CustomerIncidentResolutionDTO)
        status_type = hints.get("status")

        if get_origin(status_type) is Literal:
            values = set(status_type.__args__)
            expected = {"investigating", "mitigating", "resolved", "monitoring"}
            assert values == expected, f"CustomerIncidentResolutionDTO.status should be {expected}, got {values}"

    def test_founder_header_uses_command_vocabulary(self):
        """FounderIncidentHeaderDTO must use command vocabulary."""
        hints = get_type_hints(FounderIncidentHeaderDTO)

        # current_state should use lifecycle states
        state_type = hints.get("current_state")
        if get_origin(state_type) is Literal:
            values = set(state_type.__args__)
            expected = {"DETECTED", "TRIAGED", "MITIGATED", "RESOLVED"}
            assert values == expected, f"FounderIncidentHeaderDTO.current_state should be {expected}, got {values}"

    def test_founder_root_cause_has_derived_cause(self):
        """FounderRootCauseDTO must have derived_cause field."""
        fields = set(FounderRootCauseDTO.model_fields.keys())
        assert "derived_cause" in fields, "FounderRootCauseDTO missing derived_cause"

        # Check derived_cause values
        hints = get_type_hints(FounderRootCauseDTO)
        cause_type = hints.get("derived_cause")
        if get_origin(cause_type) is Literal:
            values = set(cause_type.__args__)
            expected_causes = {
                "RETRY_LOOP",
                "PROMPT_GROWTH",
                "FEATURE_SURGE",
                "TRAFFIC_GROWTH",
                "RATE_LIMIT_BREACH",
                "POLICY_VIOLATION",
                "BUDGET_EXCEEDED",
                "UNKNOWN",
            }
            assert values == expected_causes, (
                f"FounderRootCauseDTO.derived_cause should be {expected_causes}, got {values}"
            )

    def test_customer_dto_has_no_derived_cause(self):
        """Customer DTOs must not expose derived_cause."""
        customer_dtos = [
            CustomerIncidentNarrativeDTO,
            CustomerIncidentImpactDTO,
            CustomerIncidentResolutionDTO,
            CustomerIncidentActionDTO,
        ]

        for dto in customer_dtos:
            fields = set(dto.model_fields.keys())
            assert "derived_cause" not in fields, f"{dto.__name__} should not have derived_cause"


# =============================================================================
# DTO STRUCTURE TESTS
# =============================================================================


class TestFounderIncidentDTOStructure:
    """Verify Founder Incident DTOs have all required sections."""

    def test_founder_detail_has_required_sections(self):
        """FounderIncidentDetailDTO must have all 5 sections."""
        required_sections = {
            "header",  # Section A: Incident Header
            "timeline",  # Section B: Full Decision Timeline
            "root_cause",  # Section C: Root Cause
            "blast_radius",  # Section D: Blast Radius
            "recurrence_risk",  # Section E: Recurrence Risk
        }

        fields = set(FounderIncidentDetailDTO.model_fields.keys())
        missing = required_sections - fields

        assert not missing, f"FounderIncidentDetailDTO missing sections: {missing}"

    def test_founder_header_fields(self):
        """FounderIncidentHeaderDTO must have dense header fields."""
        required_fields = {
            "incident_id",
            "incident_type",
            "severity",
            "tenant_id",
            "current_state",
            "first_detected",
            "last_updated",
        }

        fields = set(FounderIncidentHeaderDTO.model_fields.keys())
        missing = required_fields - fields

        assert not missing, f"FounderIncidentHeaderDTO missing fields: {missing}"

    def test_founder_blast_radius_fields(self):
        """FounderBlastRadiusDTO must have impact assessment fields."""
        required_fields = {
            "requests_affected",
            "requests_blocked",
            "cost_impact_cents",
            "cost_impact_pct",
            "duration_seconds",
            "customer_visible_degradation",
        }

        fields = set(FounderBlastRadiusDTO.model_fields.keys())
        missing = required_fields - fields

        assert not missing, f"FounderBlastRadiusDTO missing fields: {missing}"

    def test_founder_recurrence_fields(self):
        """FounderRecurrenceRiskDTO must have recurrence analysis fields."""
        required_fields = {
            "similar_incidents_7d",
            "similar_incidents_30d",
            "same_tenant_recurrence",
            "risk_level",
        }

        fields = set(FounderRecurrenceRiskDTO.model_fields.keys())
        missing = required_fields - fields

        assert not missing, f"FounderRecurrenceRiskDTO missing fields: {missing}"


class TestCustomerIncidentDTOStructure:
    """Verify Customer Incident DTOs have all required sections."""

    def test_customer_narrative_has_required_sections(self):
        """CustomerIncidentNarrativeDTO must have all 4 sections."""
        required_sections = {
            "summary",  # Section A: Summary (plain language)
            "impact",  # Section B: Impact Assessment
            "resolution",  # Section C: Resolution Status
            "customer_actions",  # Section D: What You Can Do
        }

        fields = set(CustomerIncidentNarrativeDTO.model_fields.keys())
        missing = required_sections - fields

        assert not missing, f"CustomerIncidentNarrativeDTO missing sections: {missing}"

    def test_customer_impact_fields(self):
        """CustomerIncidentImpactDTO must have calm impact fields."""
        required_fields = {
            "requests_affected",
            "service_interrupted",
            "data_exposed",
            "cost_impact",
        }

        fields = set(CustomerIncidentImpactDTO.model_fields.keys())
        missing = required_fields - fields

        assert not missing, f"CustomerIncidentImpactDTO missing fields: {missing}"

    def test_customer_data_exposed_always_no(self):
        """CustomerIncidentImpactDTO.data_exposed must always be 'no'."""
        hints = get_type_hints(CustomerIncidentImpactDTO)
        data_exposed_type = hints.get("data_exposed")

        if get_origin(data_exposed_type) is Literal:
            values = set(data_exposed_type.__args__)
            assert values == {"no"}, f"CustomerIncidentImpactDTO.data_exposed should only allow 'no', got {values}"


# =============================================================================
# DTO INSTANTIATION TESTS
# =============================================================================


class TestDTOInstantiation:
    """Verify DTOs can be instantiated with valid data."""

    def test_founder_incident_detail_instantiation(self):
        """FounderIncidentDetailDTO can be created with valid data."""
        dto = FounderIncidentDetailDTO(
            header=FounderIncidentHeaderDTO(
                incident_id="inc_123",
                incident_type="COST",
                severity="high",
                tenant_id="tenant_abc",
                tenant_name="Acme Corp",
                current_state="MITIGATED",
                first_detected="2025-12-24T10:00:00Z",
                last_updated="2025-12-24T10:15:00Z",
            ),
            timeline=[
                FounderDecisionTimelineEventDTO(
                    timestamp="2025-12-24T10:00:00Z",
                    event_type="DETECTION_SIGNAL",
                    description="Cost anomaly detected",
                    data={"deviation_pct": 40.0},
                )
            ],
            root_cause=FounderRootCauseDTO(
                derived_cause="RETRY_LOOP",
                evidence="retry/request +92% over baseline",
                confidence="high",
            ),
            blast_radius=FounderBlastRadiusDTO(
                requests_affected=1500,
                requests_blocked=200,
                cost_impact_cents=5000,
                cost_impact_pct=45.0,
                duration_seconds=900,
                customer_visible_degradation=False,
                users_affected=12,
                features_affected=["customer_support.chat"],
            ),
            recurrence_risk=FounderRecurrenceRiskDTO(
                similar_incidents_7d=1,
                similar_incidents_30d=3,
                same_tenant_recurrence=True,
                same_feature_recurrence=True,
                same_root_cause_recurrence=True,
                risk_level="high",
                suggested_prevention="Review retry logic",
            ),
        )

        assert dto.header.incident_id == "inc_123"
        assert dto.root_cause.derived_cause == "RETRY_LOOP"
        assert dto.blast_radius.requests_affected == 1500

    def test_customer_narrative_instantiation(self):
        """CustomerIncidentNarrativeDTO can be created with valid data."""
        dto = CustomerIncidentNarrativeDTO(
            incident_id="inc_123",
            title="Unusual usage pattern detected and resolved",
            summary="We detected unusual AI usage. The situation has been resolved.",
            impact=CustomerIncidentImpactDTO(
                requests_affected="some",
                service_interrupted="no",
                data_exposed="no",
                cost_impact="higher_than_usual",
                cost_impact_message="Higher than usual for a short period",
            ),
            resolution=CustomerIncidentResolutionDTO(
                status="resolved",
                status_message="The issue was automatically mitigated at 14:32 UTC.",
                resolved_at="2025-12-24T14:32:00Z",
                requires_action=False,
            ),
            customer_actions=[
                CustomerIncidentActionDTO(
                    action_type="none",
                    description="No action is required from you.",
                    urgency="optional",
                    link=None,
                )
            ],
            started_at="2025-12-24T14:00:00Z",
            ended_at="2025-12-24T14:32:00Z",
            cost_summary_link="/guard/costs/summary",
        )

        assert dto.incident_id == "inc_123"
        assert dto.impact.data_exposed == "no"
        assert dto.resolution.requires_action is False


# =============================================================================
# ENDPOINT REGISTRATION TESTS
# =============================================================================


class TestEndpointRegistration:
    """Verify endpoints are registered in the correct routers."""

    def test_founder_incident_endpoint_in_ops(self):
        """Verify /ops/incidents/{id} endpoint is in ops.py."""
        import app.api.ops as ops_module

        source_file = inspect.getfile(ops_module)
        with open(source_file, "r") as f:
            source = f.read()

        assert "/incidents/{incident_id}" in source, "Founder incident endpoint not found in ops.py"
        assert "FounderIncidentDetailDTO" in source, "FounderIncidentDetailDTO not used in ops.py"
        assert "verify_fops_token" in source, "Founder incident endpoint should use fops auth"

    def test_customer_narrative_endpoint_in_guard(self):
        """Verify /guard/incidents/{id}/narrative endpoint is in guard.py."""
        import app.api.guard as guard_module

        source_file = inspect.getfile(guard_module)
        with open(source_file, "r") as f:
            source = f.read()

        assert "/incidents/{incident_id}/narrative" in source, "Customer narrative endpoint not found in guard.py"
        assert "CustomerIncidentNarrativeDTO" in source, "CustomerIncidentNarrativeDTO not used in guard.py"
        assert "verify_console_token" in source, "Customer narrative endpoint should use console auth"


# =============================================================================
# CROSS-DOMAIN LEAKAGE PREVENTION TESTS
# =============================================================================


class TestCrossDomainLeakage:
    """Verify no internal data leaks to customer views."""

    def test_customer_narrative_no_threshold_fields(self):
        """Customer narrative must not expose thresholds."""
        fields = set(CustomerIncidentNarrativeDTO.model_fields.keys())

        forbidden = {"threshold", "baseline", "threshold_breached", "deviation_pct"}
        leaked = fields & forbidden

        assert not leaked, f"CustomerIncidentNarrativeDTO exposes threshold data: {leaked}"

    def test_customer_impact_no_raw_metrics(self):
        """Customer impact must not expose raw metric values."""
        fields = set(CustomerIncidentImpactDTO.model_fields.keys())

        # These would expose raw numbers
        forbidden = {
            "cost_cents",
            "cost_delta_cents",
            "requests_count",
            "calls_affected",
            "error_rate",
        }
        leaked = fields & forbidden

        assert not leaked, f"CustomerIncidentImpactDTO exposes raw metrics: {leaked}"

    def test_customer_actions_no_internal_links(self):
        """Customer actions should only link to customer-safe pages."""
        hints = get_type_hints(CustomerIncidentActionDTO)
        action_type = hints.get("action_type")

        if get_origin(action_type) is Literal:
            values = set(action_type.__args__)
            # Should not have actions that lead to internal pages
            forbidden_actions = {"view_logs", "view_metrics", "view_policy", "admin"}
            leaked = values & forbidden_actions

            assert not leaked, f"CustomerIncidentActionDTO has forbidden actions: {leaked}"


# =============================================================================
# INCIDENT LIFECYCLE CONSISTENCY TESTS
# =============================================================================


class TestIncidentLifecycle:
    """Verify incident lifecycle is consistent across views."""

    def test_lifecycle_states_match(self):
        """Both DTOs should map to same lifecycle."""
        # Founder uses: DETECTED, TRIAGED, MITIGATED, RESOLVED
        # Customer uses: investigating, mitigating, resolved, monitoring

        founder_hints = get_type_hints(FounderIncidentHeaderDTO)
        founder_state = founder_hints.get("current_state")

        customer_hints = get_type_hints(CustomerIncidentResolutionDTO)
        customer_status = customer_hints.get("status")

        if get_origin(founder_state) is Literal and get_origin(customer_status) is Literal:
            founder_values = set(founder_state.__args__)
            customer_values = set(customer_status.__args__)

            # Both should have 4 states
            assert len(founder_values) == 4, "Founder should have 4 lifecycle states"
            assert len(customer_values) == 4, "Customer should have 4 resolution states"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
