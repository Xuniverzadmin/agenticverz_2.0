# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-024 (Inflection Point Metadata)
"""
Unit tests for GAP-024: Inflection Point Metadata.

Tests the inflection point metadata fields on incident models that
capture the exact moment when an incident was triggered.

CRITICAL TEST COVERAGE:
- Inflection point fields exist on both Incident models
- set_inflection_point helper method works correctly
- get/set inflection context methods work
- to_dict includes inflection point data
- Default values are handled correctly
"""

import pytest
from datetime import datetime, timezone
import json


class TestIncidentInflectionPointFields:
    """Test Incident model has inflection point fields."""

    def test_incident_has_inflection_step_index(self):
        """Incident model should have inflection_step_index field."""
        from app.models.killswitch import Incident

        assert hasattr(Incident, "inflection_step_index")

    def test_incident_has_inflection_timestamp(self):
        """Incident model should have inflection_timestamp field."""
        from app.models.killswitch import Incident

        assert hasattr(Incident, "inflection_timestamp")

    def test_incident_has_inflection_context_json(self):
        """Incident model should have inflection_context_json field."""
        from app.models.killswitch import Incident

        assert hasattr(Incident, "inflection_context_json")

    def test_incident_default_inflection_values(self):
        """Incident inflection fields should default to None."""
        from app.models.killswitch import Incident

        incident = Incident(
            tenant_id="tenant-001",
            title="Test Incident",
            severity="HIGH",
            trigger_type="run_failure",
            started_at=datetime.now(timezone.utc),
        )

        assert incident.inflection_step_index is None
        assert incident.inflection_timestamp is None
        assert incident.inflection_context_json is None


class TestSDSRIncidentInflectionPointFields:
    """Test SDSRIncident model has inflection point fields."""

    def test_sdsr_incident_has_inflection_step_index(self):
        """SDSRIncident model should have inflection_step_index field."""
        from app.db import SDSRIncident

        assert hasattr(SDSRIncident, "inflection_step_index")

    def test_sdsr_incident_has_inflection_timestamp(self):
        """SDSRIncident model should have inflection_timestamp field."""
        from app.db import SDSRIncident

        assert hasattr(SDSRIncident, "inflection_timestamp")

    def test_sdsr_incident_has_inflection_context_json(self):
        """SDSRIncident model should have inflection_context_json field."""
        from app.db import SDSRIncident

        assert hasattr(SDSRIncident, "inflection_context_json")

    def test_sdsr_incident_default_inflection_values(self):
        """SDSRIncident inflection fields should default to None."""
        from app.db import SDSRIncident

        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Test SDSR Incident",
            category="EXECUTION_FAILURE",
        )

        assert incident.inflection_step_index is None
        assert incident.inflection_timestamp is None
        assert incident.inflection_context_json is None


class TestIncidentInflectionPointMethods:
    """Test Incident inflection point helper methods."""

    def test_get_inflection_context_empty(self):
        """get_inflection_context should return empty dict when None."""
        from app.models.killswitch import Incident

        incident = Incident(
            tenant_id="tenant-001",
            title="Test",
            severity="HIGH",
            trigger_type="run_failure",
            started_at=datetime.now(timezone.utc),
        )

        assert incident.get_inflection_context() == {}

    def test_get_inflection_context_with_data(self):
        """get_inflection_context should parse JSON correctly."""
        from app.models.killswitch import Incident

        incident = Incident(
            tenant_id="tenant-001",
            title="Test",
            severity="HIGH",
            trigger_type="run_failure",
            started_at=datetime.now(timezone.utc),
            inflection_context_json='{"step_name": "fetch_data", "error": "timeout"}',
        )

        context = incident.get_inflection_context()
        assert context["step_name"] == "fetch_data"
        assert context["error"] == "timeout"

    def test_set_inflection_context(self):
        """set_inflection_context should serialize to JSON."""
        from app.models.killswitch import Incident

        incident = Incident(
            tenant_id="tenant-001",
            title="Test",
            severity="HIGH",
            trigger_type="run_failure",
            started_at=datetime.now(timezone.utc),
        )

        incident.set_inflection_context({
            "step_name": "process_result",
            "input_tokens": 1500,
        })

        assert incident.inflection_context_json is not None
        parsed = json.loads(incident.inflection_context_json)
        assert parsed["step_name"] == "process_result"
        assert parsed["input_tokens"] == 1500

    def test_set_inflection_point_all_values(self):
        """set_inflection_point should set all inflection point data."""
        from app.models.killswitch import Incident

        incident = Incident(
            tenant_id="tenant-001",
            title="Test",
            severity="HIGH",
            trigger_type="run_failure",
            started_at=datetime.now(timezone.utc),
        )

        timestamp = datetime.now(timezone.utc)
        incident.set_inflection_point(
            step_index=3,
            timestamp=timestamp,
            context={"reason": "budget_exceeded"},
        )

        assert incident.inflection_step_index == 3
        assert incident.inflection_timestamp == timestamp
        assert incident.get_inflection_context()["reason"] == "budget_exceeded"

    def test_set_inflection_point_partial_values(self):
        """set_inflection_point should work with partial values."""
        from app.models.killswitch import Incident

        incident = Incident(
            tenant_id="tenant-001",
            title="Test",
            severity="HIGH",
            trigger_type="run_failure",
            started_at=datetime.now(timezone.utc),
        )

        incident.set_inflection_point(step_index=5)

        assert incident.inflection_step_index == 5
        assert incident.inflection_timestamp is not None  # Defaults to now
        assert incident.inflection_context_json is None

    def test_set_inflection_point_defaults_timestamp(self):
        """set_inflection_point should default timestamp to now if not provided."""
        from app.models.killswitch import Incident

        before = datetime.now(timezone.utc)

        incident = Incident(
            tenant_id="tenant-001",
            title="Test",
            severity="HIGH",
            trigger_type="run_failure",
            started_at=datetime.now(timezone.utc),
        )
        incident.set_inflection_point(step_index=1)

        after = datetime.now(timezone.utc)

        assert incident.inflection_timestamp is not None
        assert before <= incident.inflection_timestamp <= after


class TestSDSRIncidentInflectionPointMethods:
    """Test SDSRIncident inflection point helper methods."""

    def test_get_inflection_context_empty(self):
        """get_inflection_context should return empty dict when None."""
        from app.db import SDSRIncident

        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Test",
            category="EXECUTION_FAILURE",
        )

        assert incident.get_inflection_context() == {}

    def test_get_inflection_context_with_data(self):
        """get_inflection_context should parse JSON correctly."""
        from app.db import SDSRIncident

        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Test",
            category="EXECUTION_FAILURE",
            inflection_context_json='{"skill": "web_search", "attempts": 3}',
        )

        context = incident.get_inflection_context()
        assert context["skill"] == "web_search"
        assert context["attempts"] == 3

    def test_set_inflection_context(self):
        """set_inflection_context should serialize to JSON."""
        from app.db import SDSRIncident

        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Test",
            category="EXECUTION_FAILURE",
        )

        incident.set_inflection_context({
            "tool_call": "calculate",
            "duration_ms": 5000,
        })

        assert incident.inflection_context_json is not None
        parsed = json.loads(incident.inflection_context_json)
        assert parsed["tool_call"] == "calculate"
        assert parsed["duration_ms"] == 5000

    def test_set_inflection_point_all_values(self):
        """set_inflection_point should set all inflection point data."""
        from app.db import SDSRIncident

        timestamp = datetime.now(timezone.utc)
        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Test",
            category="EXECUTION_FAILURE",
        )

        incident.set_inflection_point(
            step_index=7,
            timestamp=timestamp,
            context={"failure_type": "rate_limit"},
        )

        assert incident.inflection_step_index == 7
        assert incident.inflection_timestamp == timestamp
        assert incident.get_inflection_context()["failure_type"] == "rate_limit"


class TestSDSRIncidentToDict:
    """Test SDSRIncident.to_dict includes inflection point data."""

    def test_to_dict_includes_inflection_fields(self):
        """to_dict should include inflection point fields."""
        from app.db import SDSRIncident

        timestamp = datetime.now(timezone.utc)
        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Test Incident",
            category="EXECUTION_FAILURE",
            inflection_step_index=4,
            inflection_timestamp=timestamp,
            inflection_context_json='{"error": "timeout"}',
        )

        result = incident.to_dict()

        assert "inflection_step_index" in result
        assert result["inflection_step_index"] == 4
        assert "inflection_timestamp" in result
        assert result["inflection_timestamp"] == timestamp.isoformat()
        assert "inflection_context" in result
        assert result["inflection_context"]["error"] == "timeout"

    def test_to_dict_handles_none_inflection_fields(self):
        """to_dict should handle None inflection fields gracefully."""
        from app.db import SDSRIncident

        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Test Incident",
            category="EXECUTION_FAILURE",
        )

        result = incident.to_dict()

        assert "inflection_step_index" in result
        assert result["inflection_step_index"] is None
        assert "inflection_timestamp" in result
        assert result["inflection_timestamp"] is None
        assert "inflection_context" in result
        assert result["inflection_context"] == {}


class TestInflectionPointUseCases:
    """Test realistic use cases for inflection point metadata."""

    def test_step_failure_inflection(self):
        """Capture inflection point when a step fails."""
        from app.db import SDSRIncident

        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Step Failure: web_search timed out",
            category="EXECUTION_FAILURE",
            error_code="STEP_FAILURE",
        )

        incident.set_inflection_point(
            step_index=2,
            context={
                "step_name": "web_search",
                "skill_id": "skill_web_search_v1",
                "input_tokens": 450,
                "timeout_ms": 30000,
                "actual_duration_ms": 35000,
            },
        )

        context = incident.get_inflection_context()
        assert context["step_name"] == "web_search"
        assert context["timeout_ms"] == 30000
        assert incident.inflection_step_index == 2

    def test_budget_exceeded_inflection(self):
        """Capture inflection point when budget is exceeded."""
        from app.db import SDSRIncident

        incident = SDSRIncident(
            tenant_id="tenant-001",
            title="Budget Exceeded",
            category="BUDGET_EXCEEDED",
            error_code="BUDGET_EXCEEDED",
        )

        incident.set_inflection_point(
            step_index=5,
            context={
                "budget_limit_cents": 1000,
                "cost_at_inflection_cents": 1050,
                "token_count_at_inflection": 25000,
                "last_model": "claude-3-opus",
            },
        )

        context = incident.get_inflection_context()
        assert context["budget_limit_cents"] == 1000
        assert context["cost_at_inflection_cents"] == 1050
        assert incident.inflection_step_index == 5

    def test_policy_violation_inflection(self):
        """Capture inflection point for policy violations."""
        from app.models.killswitch import Incident

        incident = Incident(
            tenant_id="tenant-001",
            title="Policy Violation Detected",
            severity="HIGH",
            trigger_type="policy_violation",
            started_at=datetime.now(timezone.utc),
        )

        incident.set_inflection_point(
            step_index=1,
            context={
                "policy_id": "pol-content-filter-001",
                "policy_name": "Content Safety Filter",
                "violation_type": "harmful_content",
                "confidence": 0.95,
            },
        )

        context = incident.get_inflection_context()
        assert context["policy_id"] == "pol-content-filter-001"
        assert context["violation_type"] == "harmful_content"
        assert context["confidence"] == 0.95
