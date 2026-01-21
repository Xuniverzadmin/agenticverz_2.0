# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-025 (SOC2 Control Mapping)
"""
Unit tests for GAP-025: SOC2 Control Mapping.

Tests the complete SOC2 Trust Service Criteria control mapping
for incident response and evidence export.

CRITICAL TEST COVERAGE:
- Control registry has all required controls
- Incident categories map to appropriate controls
- Control mappings include evidence
- Compliance status is determined correctly
- API-ready output format
"""

import pytest
from datetime import datetime, timezone


class TestSOC2ControlRegistryImport:
    """Test SOC2 control registry imports."""

    def test_registry_import(self):
        """SOC2ControlRegistry should be importable."""
        from app.services.soc2 import SOC2ControlRegistry

        assert SOC2ControlRegistry is not None

    def test_control_import(self):
        """SOC2Control should be importable."""
        from app.services.soc2 import SOC2Control

        assert SOC2Control is not None

    def test_mapping_import(self):
        """SOC2ControlMapping should be importable."""
        from app.services.soc2 import SOC2ControlMapping

        assert SOC2ControlMapping is not None

    def test_category_import(self):
        """SOC2Category should be importable."""
        from app.services.soc2 import SOC2Category

        assert SOC2Category.COMMON_CRITERIA is not None

    def test_compliance_status_import(self):
        """SOC2ComplianceStatus should be importable."""
        from app.services.soc2 import SOC2ComplianceStatus

        assert SOC2ComplianceStatus.DEMONSTRATED is not None


class TestSOC2ControlRegistry:
    """Test SOC2 control registry."""

    def test_get_control_registry(self):
        """get_control_registry should return singleton."""
        from app.services.soc2 import get_control_registry

        registry1 = get_control_registry()
        registry2 = get_control_registry()

        assert registry1 is registry2

    def test_registry_has_incident_response_controls(self):
        """Registry should have CC7.x incident response controls."""
        from app.services.soc2 import get_control_registry

        registry = get_control_registry()
        controls = registry.get_incident_response_controls()

        assert len(controls) >= 5
        control_ids = [c.control_id for c in controls]
        assert "CC7.1" in control_ids
        assert "CC7.2" in control_ids
        assert "CC7.3" in control_ids
        assert "CC7.4" in control_ids
        assert "CC7.5" in control_ids

    def test_registry_has_processing_integrity_controls(self):
        """Registry should have PI1.x processing integrity controls."""
        from app.services.soc2 import get_control_registry

        registry = get_control_registry()
        controls = registry.get_controls_by_prefix("PI1")

        assert len(controls) >= 4
        control_ids = [c.control_id for c in controls]
        assert "PI1.1" in control_ids
        assert "PI1.4" in control_ids  # Output validation

    def test_registry_has_access_controls(self):
        """Registry should have CC6.x access controls."""
        from app.services.soc2 import get_control_registry

        registry = get_control_registry()
        controls = registry.get_controls_by_prefix("CC6")

        assert len(controls) >= 1
        control_ids = [c.control_id for c in controls]
        assert "CC6.1" in control_ids

    def test_registry_has_availability_controls(self):
        """Registry should have A1.x availability controls."""
        from app.services.soc2 import get_control_registry

        registry = get_control_registry()
        controls = registry.get_controls_by_prefix("A1")

        assert len(controls) >= 2

    def test_get_control_by_id(self):
        """Should get control by ID."""
        from app.services.soc2 import get_control_registry

        registry = get_control_registry()
        control = registry.get_control("CC7.2")

        assert control is not None
        assert control.control_id == "CC7.2"
        assert control.control_name == "Incident Response"

    def test_get_nonexistent_control(self):
        """Should return None for nonexistent control."""
        from app.services.soc2 import get_control_registry

        registry = get_control_registry()
        control = registry.get_control("XX9.9")

        assert control is None

    def test_get_all_controls(self):
        """Should get all registered controls."""
        from app.services.soc2 import get_control_registry

        registry = get_control_registry()
        controls = registry.get_all_controls()

        # Should have at least 15 controls across categories
        assert len(controls) >= 15


class TestSOC2Control:
    """Test SOC2Control dataclass."""

    def test_control_creation(self):
        """Should create control with all fields."""
        from app.services.soc2 import SOC2Control, SOC2Category

        control = SOC2Control(
            control_id="CC7.2",
            control_name="Incident Response",
            control_description="Test description",
            category=SOC2Category.COMMON_CRITERIA,
            subcategory="System Operations",
        )

        assert control.control_id == "CC7.2"
        assert control.control_name == "Incident Response"
        assert control.category == SOC2Category.COMMON_CRITERIA

    def test_control_default_evidence_types(self):
        """Control should have default evidence types based on ID."""
        from app.services.soc2 import SOC2Control, SOC2Category

        control = SOC2Control(
            control_id="CC7.2",
            control_name="Test",
            control_description="Test",
            category=SOC2Category.COMMON_CRITERIA,
        )

        # CC7.x controls should have incident-related evidence types
        assert len(control.evidence_types) > 0
        assert "incident_record" in control.evidence_types or "trace_evidence" in control.evidence_types


class TestSOC2ControlMapping:
    """Test SOC2ControlMapping dataclass."""

    def test_mapping_creation(self):
        """Should create mapping with control and evidence."""
        from app.services.soc2 import (
            SOC2Control,
            SOC2ControlMapping,
            SOC2Category,
            SOC2ComplianceStatus,
        )

        control = SOC2Control(
            control_id="CC7.2",
            control_name="Incident Response",
            control_description="Test",
            category=SOC2Category.COMMON_CRITERIA,
        )

        mapping = SOC2ControlMapping(
            control=control,
            evidence_provided="Incident response initiated",
            compliance_status=SOC2ComplianceStatus.DEMONSTRATED,
        )

        assert mapping.control.control_id == "CC7.2"
        assert mapping.compliance_status == SOC2ComplianceStatus.DEMONSTRATED

    def test_mapping_to_dict(self):
        """to_dict should return API-ready format."""
        from app.services.soc2 import (
            SOC2Control,
            SOC2ControlMapping,
            SOC2Category,
            SOC2ComplianceStatus,
        )

        control = SOC2Control(
            control_id="CC7.2",
            control_name="Incident Response",
            control_description="Test description",
            category=SOC2Category.COMMON_CRITERIA,
            subcategory="System Operations",
        )

        mapping = SOC2ControlMapping(
            control=control,
            evidence_provided="Test evidence",
            compliance_status=SOC2ComplianceStatus.DEMONSTRATED,
            evidence_sources=["incident:inc_123", "trace:tr_456"],
        )

        result = mapping.to_dict()

        assert result["control_id"] == "CC7.2"
        assert result["control_name"] == "Incident Response"
        assert result["category"] == "CC"
        assert result["compliance_status"] == "DEMONSTRATED"
        assert result["evidence_provided"] == "Test evidence"
        assert len(result["evidence_sources"]) == 2


class TestSOC2ControlMapper:
    """Test SOC2ControlMapper."""

    def test_mapper_import(self):
        """SOC2ControlMapper should be importable."""
        from app.services.soc2 import SOC2ControlMapper

        assert SOC2ControlMapper is not None

    def test_map_execution_failure(self):
        """Should map EXECUTION_FAILURE to CC7.x and PI1.x controls."""
        from app.services.soc2 import SOC2ControlMapper

        mapper = SOC2ControlMapper()
        mappings = mapper.map_incident_to_controls(
            incident_category="EXECUTION_FAILURE",
            incident_data={
                "incident_id": "inc_test123",
                "trace_id": "tr_test456",
                "run_id": "run_test789",
                "severity": "HIGH",
                "error_code": "EXECUTION_TIMEOUT",
                "step_index": 5,
            },
        )

        # Should have multiple mappings
        assert len(mappings) >= 4

        control_ids = [m.control.control_id for m in mappings]
        # Should include incident response controls
        assert "CC7.1" in control_ids
        assert "CC7.2" in control_ids
        # Should include processing integrity
        assert "PI1.1" in control_ids

    def test_map_budget_exceeded(self):
        """Should map BUDGET_EXCEEDED to CC7.x and CC9.x controls."""
        from app.services.soc2 import SOC2ControlMapper

        mapper = SOC2ControlMapper()
        mappings = mapper.map_incident_to_controls(
            incident_category="BUDGET_EXCEEDED",
            incident_data={
                "incident_id": "inc_budget123",
                "severity": "MEDIUM",
            },
        )

        control_ids = [m.control.control_id for m in mappings]
        # Should include risk controls
        assert "CC9.1" in control_ids or "CC9.2" in control_ids

    def test_map_rate_limit(self):
        """Should map RATE_LIMIT to availability controls."""
        from app.services.soc2 import SOC2ControlMapper

        mapper = SOC2ControlMapper()
        mappings = mapper.map_incident_to_controls(
            incident_category="RATE_LIMIT",
            incident_data={
                "incident_id": "inc_rate123",
            },
        )

        control_ids = [m.control.control_id for m in mappings]
        # Should include availability control
        assert "A1.1" in control_ids

    def test_map_hallucination(self):
        """Should map HALLUCINATION to processing integrity controls."""
        from app.services.soc2 import SOC2ControlMapper

        mapper = SOC2ControlMapper()
        mappings = mapper.map_incident_to_controls(
            incident_category="HALLUCINATION",
            incident_data={
                "incident_id": "inc_hallu123",
            },
        )

        control_ids = [m.control.control_id for m in mappings]
        # Should include output validation (PI1.4)
        assert "PI1.4" in control_ids

    def test_map_unknown_category_uses_default(self):
        """Should use default controls for unknown category."""
        from app.services.soc2 import SOC2ControlMapper

        mapper = SOC2ControlMapper()
        mappings = mapper.map_incident_to_controls(
            incident_category="UNKNOWN_CATEGORY",
            incident_data={
                "incident_id": "inc_unknown123",
            },
        )

        # Should still have mappings (from default)
        assert len(mappings) >= 3
        control_ids = [m.control.control_id for m in mappings]
        assert "CC7.1" in control_ids

    def test_compliance_status_demonstrated_with_full_evidence(self):
        """Should be DEMONSTRATED with incident and trace."""
        from app.services.soc2 import SOC2ControlMapper, SOC2ComplianceStatus

        mapper = SOC2ControlMapper()
        mappings = mapper.map_incident_to_controls(
            incident_category="EXECUTION_FAILURE",
            incident_data={
                "incident_id": "inc_full123",
                "trace_id": "tr_full456",
                "run_id": "run_full789",
            },
        )

        # CC7.x controls should be DEMONSTRATED
        cc7_mappings = [m for m in mappings if m.control.control_id.startswith("CC7")]
        for mapping in cc7_mappings:
            assert mapping.compliance_status == SOC2ComplianceStatus.DEMONSTRATED

    def test_evidence_sources_populated(self):
        """Mapping should include evidence sources."""
        from app.services.soc2 import SOC2ControlMapper

        mapper = SOC2ControlMapper()
        mappings = mapper.map_incident_to_controls(
            incident_category="EXECUTION_FAILURE",
            incident_data={
                "incident_id": "inc_src123",
                "trace_id": "tr_src456",
                "run_id": "run_src789",
            },
        )

        for mapping in mappings:
            # Should have at least incident source
            assert any("incident:" in s for s in mapping.evidence_sources)


class TestGetControlMappingsForIncident:
    """Test get_control_mappings_for_incident function."""

    def test_function_import(self):
        """get_control_mappings_for_incident should be importable."""
        from app.services.soc2 import get_control_mappings_for_incident

        assert get_control_mappings_for_incident is not None

    def test_returns_dict_list(self):
        """Should return list of dicts for API responses."""
        from app.services.soc2 import get_control_mappings_for_incident

        result = get_control_mappings_for_incident(
            incident_category="EXECUTION_FAILURE",
            incident_data={
                "incident_id": "inc_api123",
                "severity": "HIGH",
            },
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)
        assert "control_id" in result[0]
        assert "compliance_status" in result[0]

    def test_result_format_complete(self):
        """Result dict should have all required fields."""
        from app.services.soc2 import get_control_mappings_for_incident

        result = get_control_mappings_for_incident(
            incident_category="EXECUTION_FAILURE",
            incident_data={"incident_id": "inc_format123"},
        )

        first = result[0]
        required_fields = [
            "control_id",
            "control_name",
            "control_description",
            "category",
            "evidence_provided",
            "compliance_status",
            "evidence_sources",
        ]
        for field in required_fields:
            assert field in first, f"Missing field: {field}"


class TestSOC2ComplianceStatus:
    """Test SOC2ComplianceStatus enum."""

    def test_all_statuses_defined(self):
        """All required statuses should be defined."""
        from app.services.soc2 import SOC2ComplianceStatus

        assert SOC2ComplianceStatus.DEMONSTRATED is not None
        assert SOC2ComplianceStatus.PARTIAL is not None
        assert SOC2ComplianceStatus.NOT_APPLICABLE is not None
        assert SOC2ComplianceStatus.NOT_DEMONSTRATED is not None
        assert SOC2ComplianceStatus.PENDING_REVIEW is not None

    def test_status_values(self):
        """Status values should be strings."""
        from app.services.soc2 import SOC2ComplianceStatus

        assert SOC2ComplianceStatus.DEMONSTRATED.value == "DEMONSTRATED"
        assert SOC2ComplianceStatus.PARTIAL.value == "PARTIAL"


class TestSOC2Category:
    """Test SOC2Category enum."""

    def test_all_categories_defined(self):
        """All trust service categories should be defined."""
        from app.services.soc2 import SOC2Category

        assert SOC2Category.COMMON_CRITERIA is not None
        assert SOC2Category.AVAILABILITY is not None
        assert SOC2Category.PROCESSING_INTEGRITY is not None
        assert SOC2Category.CONFIDENTIALITY is not None
        assert SOC2Category.PRIVACY is not None

    def test_category_values(self):
        """Category values should be standard SOC2 abbreviations."""
        from app.services.soc2 import SOC2Category

        assert SOC2Category.COMMON_CRITERIA.value == "CC"
        assert SOC2Category.AVAILABILITY.value == "A"
        assert SOC2Category.PROCESSING_INTEGRITY.value == "PI"
