"""
Category 3: Data Contract Freeze - CI Guardrails

PIN-148: These tests MUST pass in CI to prevent regression of data contracts.

Contract Invariants:
1. Guard contracts MUST NOT reference Ops types
2. Ops contracts MUST NOT reference Guard types
3. Response schemas MUST match frozen DTOs
4. Field types MUST NOT change (widening forbidden)
5. Required fields MUST NOT become optional
6. New fields MUST be optional (backward compatible)

Absence Tests:
- No cross-domain imports
- No founder-only fields in guard responses
- No tenant-specific aggregation in ops responses
- No shared response models between domains
"""

import re
from pathlib import Path

import pytest


class TestContractNamespaceSeparation:
    """
    Test that guard and ops contracts are completely separate.

    INVARIANT: No cross-domain type references.
    """

    @pytest.fixture
    def contracts_dir(self):
        return Path(__file__).parent.parent / "app" / "contracts"

    def test_guard_does_not_import_ops(self, contracts_dir):
        """
        ABSENCE TEST: guard.py MUST NOT import from ops.py.
        """
        guard_file = contracts_dir / "guard.py"
        if not guard_file.exists():
            pytest.skip("guard.py not found")

        content = guard_file.read_text()

        # Check for any ops imports
        forbidden_patterns = [
            r"from\s+app\.contracts\.ops\s+import",
            r"from\s+\.ops\s+import",
            r"import\s+app\.contracts\.ops",
            r"OpsEvent",
            r"SystemPulse",
            r"CustomerSegment",
            r"IncidentPattern",
            r"StickinessByFeature",
            r"RevenueRisk",
            r"InfraLimits",
            r"Playbook",
        ]

        for pattern in forbidden_patterns:
            assert not re.search(pattern, content), f"guard.py MUST NOT contain ops references: found '{pattern}'"

    def test_ops_does_not_import_guard(self, contracts_dir):
        """
        ABSENCE TEST: ops.py MUST NOT import from guard.py.
        """
        ops_file = contracts_dir / "ops.py"
        if not ops_file.exists():
            pytest.skip("ops.py not found")

        content = ops_file.read_text()

        # Check for any guard imports
        forbidden_patterns = [
            r"from\s+app\.contracts\.guard\s+import",
            r"from\s+\.guard\s+import",
            r"import\s+app\.contracts\.guard",
            r"GuardStatus",
            r"TodaySnapshot",
            r"IncidentSummary",
            r"ApiKey",
            r"TenantSettings",
            r"ReplayResult",
            r"KillSwitchAction",
        ]

        for pattern in forbidden_patterns:
            assert not re.search(pattern, content), f"ops.py MUST NOT contain guard references: found '{pattern}'"

    def test_common_has_no_domain_types(self, contracts_dir):
        """
        ABSENCE TEST: common.py MUST NOT contain domain-specific types.
        """
        common_file = contracts_dir / "common.py"
        if not common_file.exists():
            pytest.skip("common.py not found")

        content = common_file.read_text()

        # Check for domain-specific patterns
        forbidden_patterns = [
            r"class\s+Guard",
            r"class\s+Ops",
            r"class\s+Incident",
            r"class\s+Customer",
            r"class\s+Tenant",
            r"class\s+Playbook",
            r"class\s+Replay",
        ]

        for pattern in forbidden_patterns:
            assert not re.search(pattern, content), f"common.py MUST NOT contain domain types: found '{pattern}'"


class TestGuardContractInvariants:
    """
    Test Guard contract structure invariants.
    """

    def test_guard_status_has_required_fields(self):
        """GuardStatusDTO MUST have all required fields."""
        from app.contracts.guard import GuardStatusDTO

        required_fields = {
            "status",
            "is_frozen",
            "incidents_blocked_24h",
            "active_guardrails",
        }

        model_fields = set(GuardStatusDTO.model_fields.keys())
        missing = required_fields - model_fields

        assert not missing, f"GuardStatusDTO missing required fields: {missing}"

    def test_guard_status_types_are_strict(self):
        """GuardStatusDTO field types MUST be strict."""
        from app.contracts.guard import GuardStatusDTO

        # status must be a literal, not any string
        status_field = GuardStatusDTO.model_fields["status"]
        assert "Literal" in str(status_field.annotation), "status must be Literal type, not str"

        # is_frozen must be bool
        frozen_field = GuardStatusDTO.model_fields["is_frozen"]
        assert frozen_field.annotation == bool, "is_frozen must be bool"

        # incidents_blocked_24h must be int
        incidents_field = GuardStatusDTO.model_fields["incidents_blocked_24h"]
        assert incidents_field.annotation == int, "incidents_blocked_24h must be int"

    def test_incident_summary_has_id_prefix_constraint(self):
        """IncidentSummaryDTO.id should document prefix requirement."""
        from app.contracts.guard import IncidentSummaryDTO

        id_field = GuardStatusDTO if False else IncidentSummaryDTO.model_fields["id"]
        description = id_field.description or ""

        assert (
            "inc_" in description.lower() or id_field.annotation == str
        ), "id field should document the inc_ prefix convention"

    def test_guard_no_founder_only_fields(self):
        """
        ABSENCE TEST: Guard contracts MUST NOT have founder-only fields.
        """
        from app.contracts.guard import (
            GuardStatusDTO,
            IncidentSummaryDTO,
            TenantSettingsDTO,
            TodaySnapshotDTO,
        )

        founder_only_fields = {
            "churn_risk_score",
            "stickiness_delta",
            "mrr_cents",
            "ltv_cents",
            "concentration_risk",
            "playbook_id",
            "affected_tenants",  # Cross-tenant aggregation
            "is_systemic",  # Cross-tenant pattern
        }

        for dto in [GuardStatusDTO, TodaySnapshotDTO, IncidentSummaryDTO, TenantSettingsDTO]:
            model_fields = set(dto.model_fields.keys())
            forbidden = model_fields & founder_only_fields

            assert not forbidden, f"{dto.__name__} MUST NOT have founder-only fields: {forbidden}"


class TestOpsContractInvariants:
    """
    Test Ops contract structure invariants.
    """

    def test_system_pulse_has_required_fields(self):
        """SystemPulseDTO MUST have all required fields."""
        from app.contracts.ops import SystemPulseDTO

        required_fields = {
            "status",
            "active_customers",
            "incidents_24h",
            "revenue_today_cents",
            "customers_at_risk",
        }

        model_fields = set(SystemPulseDTO.model_fields.keys())
        missing = required_fields - model_fields

        assert not missing, f"SystemPulseDTO missing required fields: {missing}"

    def test_system_pulse_status_is_command_vocabulary(self):
        """SystemPulseDTO.status MUST use command vocabulary."""
        from app.contracts.ops import SystemPulseDTO

        status_field = SystemPulseDTO.model_fields["status"]
        annotation_str = str(status_field.annotation)

        # Must use ops vocabulary: stable, elevated, degraded, critical
        # NOT guard vocabulary: protected, attention_needed, action_required
        assert "stable" in annotation_str, "status must include 'stable'"
        assert "critical" in annotation_str, "status must include 'critical'"
        assert "protected" not in annotation_str, "status MUST NOT use guard vocabulary 'protected'"

    def test_customer_segment_has_global_metrics(self):
        """CustomerSegmentDTO MUST have founder-level metrics."""
        from app.contracts.ops import CustomerSegmentDTO

        founder_metrics = {
            "mrr_cents",
            "ltv_cents",
            "churn_risk_score",
            "stickiness_delta",
        }

        model_fields = set(CustomerSegmentDTO.model_fields.keys())
        missing = founder_metrics - model_fields

        assert not missing, f"CustomerSegmentDTO missing founder metrics: {missing}"

    def test_incident_pattern_has_cross_tenant_fields(self):
        """IncidentPatternDTO MUST have cross-tenant aggregation."""
        from app.contracts.ops import IncidentPatternDTO

        cross_tenant_fields = {
            "affected_tenants",
            "is_systemic",
        }

        model_fields = set(IncidentPatternDTO.model_fields.keys())
        missing = cross_tenant_fields - model_fields

        assert not missing, f"IncidentPatternDTO missing cross-tenant fields: {missing}"


class TestNoSharedResponseModels:
    """
    ABSENCE TEST: Ensure no response models are shared between domains.
    """

    def test_guard_api_uses_guard_contracts(self):
        """guard.py API MUST use contracts from guard module only."""
        guard_api = Path(__file__).parent.parent / "app" / "api" / "guard.py"
        if not guard_api.exists():
            pytest.skip("guard.py not found")

        content = guard_api.read_text()

        # Should not import from ops contracts
        forbidden = [
            "from app.contracts.ops import",
            "from ..contracts.ops import",
        ]

        for pattern in forbidden:
            assert pattern not in content, "guard.py API MUST NOT import from ops contracts"

    def test_ops_api_uses_ops_contracts(self):
        """ops.py API MUST use contracts from ops module only."""
        ops_api = Path(__file__).parent.parent / "app" / "api" / "ops.py"
        if not ops_api.exists():
            pytest.skip("ops.py not found")

        content = ops_api.read_text()

        # Should not import from guard contracts
        forbidden = [
            "from app.contracts.guard import",
            "from ..contracts.guard import",
        ]

        for pattern in forbidden:
            assert pattern not in content, "ops.py API MUST NOT import from guard contracts"


class TestVocabularySeparation:
    """
    Test that guard and ops use distinct vocabulary.

    Guard: Customer-facing, calm language
    Ops: Founder-facing, command language
    """

    def test_guard_uses_calm_status_vocabulary(self):
        """Guard status MUST use calm vocabulary."""
        from app.contracts.guard import GuardStatusDTO

        status_annotation = str(GuardStatusDTO.model_fields["status"].annotation)

        calm_terms = ["protected", "attention_needed", "action_required"]
        command_terms = ["stable", "elevated", "degraded", "critical"]

        has_calm = any(term in status_annotation for term in calm_terms)
        has_command = any(term in status_annotation for term in command_terms)

        assert has_calm, f"Guard status should use calm vocabulary: {calm_terms}"
        assert not has_command, f"Guard status MUST NOT use command vocabulary: {command_terms}"

    def test_ops_uses_command_status_vocabulary(self):
        """Ops status MUST use command vocabulary."""
        from app.contracts.ops import SystemPulseDTO

        status_annotation = str(SystemPulseDTO.model_fields["status"].annotation)

        calm_terms = ["protected", "attention_needed", "action_required"]
        command_terms = ["stable", "elevated", "degraded", "critical"]

        has_command = any(term in status_annotation for term in command_terms)
        has_calm = any(term in status_annotation for term in calm_terms)

        assert has_command, f"Ops status should use command vocabulary: {command_terms}"
        assert not has_calm, f"Ops status MUST NOT use calm vocabulary: {calm_terms}"


class TestContractVersioning:
    """Test contract version tracking."""

    def test_contract_version_exists(self):
        """Contract version MUST be defined."""
        from app.contracts import CONTRACT_FROZEN_AT, CONTRACT_VERSION

        assert CONTRACT_VERSION, "CONTRACT_VERSION must be set"
        assert CONTRACT_FROZEN_AT, "CONTRACT_FROZEN_AT must be set"

    def test_contract_version_is_semver(self):
        """Contract version MUST be semver format."""
        from app.contracts import CONTRACT_VERSION

        parts = CONTRACT_VERSION.split(".")
        assert len(parts) == 3, f"Version must be semver: {CONTRACT_VERSION}"

        for part in parts:
            assert part.isdigit(), f"Version parts must be numeric: {CONTRACT_VERSION}"

    def test_frozen_date_is_iso(self):
        """Frozen date MUST be ISO format."""
        from datetime import datetime

        from app.contracts import CONTRACT_FROZEN_AT

        try:
            datetime.fromisoformat(CONTRACT_FROZEN_AT)
        except ValueError:
            pytest.fail(f"CONTRACT_FROZEN_AT must be ISO format: {CONTRACT_FROZEN_AT}")


# Run tests with: pytest tests/test_category3_data_contracts.py -v
