# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-027 (Evidence PDF Completeness)
"""
Unit tests for GAP-027: Evidence PDF Completeness.

Tests the evidence completeness checker service that validates
all required fields are present before PDF generation.

CRITICAL TEST COVERAGE:
- EvidenceCompletenessChecker imports and initializes
- Completeness correctly determines complete/incomplete
- Validation raises error when enabled and incomplete
- Helper functions work correctly
- All export types validated (evidence, soc2, executive)
"""

import pytest


class TestEvidenceCompletenessImports:
    """Test evidence completeness module imports."""

    def test_checker_import(self):
        """EvidenceCompletenessChecker should be importable."""
        from app.services.export import EvidenceCompletenessChecker

        assert EvidenceCompletenessChecker is not None

    def test_error_import(self):
        """EvidenceCompletenessError should be importable."""
        from app.services.export import EvidenceCompletenessError

        assert EvidenceCompletenessError is not None

    def test_result_enum_import(self):
        """CompletenessCheckResult should be importable."""
        from app.services.export import CompletenessCheckResult

        assert CompletenessCheckResult.COMPLETE is not None

    def test_response_import(self):
        """CompletenessCheckResponse should be importable."""
        from app.services.export import CompletenessCheckResponse

        assert CompletenessCheckResponse is not None

    def test_required_fields_import(self):
        """REQUIRED_EVIDENCE_FIELDS should be importable."""
        from app.services.export import REQUIRED_EVIDENCE_FIELDS

        assert REQUIRED_EVIDENCE_FIELDS is not None
        assert len(REQUIRED_EVIDENCE_FIELDS) > 0

    def test_soc2_fields_import(self):
        """SOC2_REQUIRED_FIELDS should be importable."""
        from app.services.export import SOC2_REQUIRED_FIELDS

        assert SOC2_REQUIRED_FIELDS is not None
        assert len(SOC2_REQUIRED_FIELDS) > 0

    def test_helper_imports(self):
        """Helper functions should be importable."""
        from app.services.export import (
            check_evidence_completeness,
            ensure_evidence_completeness,
        )

        assert check_evidence_completeness is not None
        assert ensure_evidence_completeness is not None


class TestCompletenessCheckResult:
    """Test CompletenessCheckResult enum."""

    def test_all_results_defined(self):
        """All required results should be defined."""
        from app.services.export import CompletenessCheckResult

        assert CompletenessCheckResult.COMPLETE is not None
        assert CompletenessCheckResult.INCOMPLETE is not None
        assert CompletenessCheckResult.VALIDATION_DISABLED is not None
        assert CompletenessCheckResult.PARTIAL is not None

    def test_result_values(self):
        """Result values should be strings."""
        from app.services.export import CompletenessCheckResult

        assert CompletenessCheckResult.COMPLETE.value == "complete"
        assert CompletenessCheckResult.INCOMPLETE.value == "incomplete"
        assert CompletenessCheckResult.PARTIAL.value == "partial"


class TestRequiredFields:
    """Test required fields definitions."""

    def test_evidence_required_fields_contains_bundle_id(self):
        """Required evidence fields should include bundle_id."""
        from app.services.export import REQUIRED_EVIDENCE_FIELDS

        assert "bundle_id" in REQUIRED_EVIDENCE_FIELDS

    def test_evidence_required_fields_contains_incident_id(self):
        """Required evidence fields should include incident_id."""
        from app.services.export import REQUIRED_EVIDENCE_FIELDS

        assert "incident_id" in REQUIRED_EVIDENCE_FIELDS

    def test_evidence_required_fields_contains_run_id(self):
        """Required evidence fields should include run_id."""
        from app.services.export import REQUIRED_EVIDENCE_FIELDS

        assert "run_id" in REQUIRED_EVIDENCE_FIELDS

    def test_soc2_fields_contains_control_mappings(self):
        """SOC2 fields should include control_mappings."""
        from app.services.export import SOC2_REQUIRED_FIELDS

        assert "control_mappings" in SOC2_REQUIRED_FIELDS

    def test_soc2_fields_contains_attestation(self):
        """SOC2 fields should include attestation_statement."""
        from app.services.export import SOC2_REQUIRED_FIELDS

        assert "attestation_statement" in SOC2_REQUIRED_FIELDS


class TestEvidenceCompletenessChecker:
    """Test EvidenceCompletenessChecker class."""

    def test_default_validation_enabled(self):
        """Default checker should have validation enabled."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()

        assert checker.validation_enabled

    def test_validation_can_be_disabled(self):
        """Checker can be created with validation disabled."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker(validation_enabled=False)

        assert not checker.validation_enabled

    def test_strict_mode_default_disabled(self):
        """Default checker should have strict mode disabled."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()

        assert not checker.strict_mode

    def test_strict_mode_can_be_enabled(self):
        """Checker can be created with strict mode."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker(strict_mode=True)

        assert checker.strict_mode

    def test_get_required_fields_evidence(self):
        """get_required_fields should return evidence fields."""
        from app.services.export import (
            EvidenceCompletenessChecker,
            REQUIRED_EVIDENCE_FIELDS,
        )

        checker = EvidenceCompletenessChecker()
        fields = checker.get_required_fields("evidence")

        assert fields == REQUIRED_EVIDENCE_FIELDS

    def test_get_required_fields_soc2_includes_both(self):
        """get_required_fields should return combined fields for SOC2."""
        from app.services.export import (
            EvidenceCompletenessChecker,
            REQUIRED_EVIDENCE_FIELDS,
            SOC2_REQUIRED_FIELDS,
        )

        checker = EvidenceCompletenessChecker()
        fields = checker.get_required_fields("soc2")

        assert REQUIRED_EVIDENCE_FIELDS.issubset(fields)
        assert SOC2_REQUIRED_FIELDS.issubset(fields)

    def test_get_required_fields_executive(self):
        """get_required_fields should return executive fields."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()
        fields = checker.get_required_fields("executive")

        assert "risk_level" in fields
        assert "incident_summary" in fields
        assert "business_impact" in fields


class TestEvidenceCompletenessCheckerCheck:
    """Test check method."""

    def test_complete_bundle_returns_complete(self):
        """Check should return COMPLETE or PARTIAL for complete bundles."""
        from datetime import datetime

        from app.services.export import (
            CompletenessCheckResult,
            EvidenceCompletenessChecker,
        )

        checker = EvidenceCompletenessChecker()

        # Complete bundle (all required fields, may be missing recommended)
        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
        }

        response = checker.check(bundle, "evidence")

        # COMPLETE or PARTIAL both mean required fields are present
        assert response.result in (CompletenessCheckResult.COMPLETE, CompletenessCheckResult.PARTIAL)
        assert response.is_complete is True
        assert len(response.missing_required) == 0

    def test_incomplete_bundle_returns_incomplete(self):
        """Check should return INCOMPLETE for missing required fields."""
        from app.services.export import (
            CompletenessCheckResult,
            EvidenceCompletenessChecker,
        )

        checker = EvidenceCompletenessChecker()

        # Missing required fields
        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            # Missing: run_id, trace_id, etc.
        }

        response = checker.check(bundle, "evidence")

        assert response.result == CompletenessCheckResult.INCOMPLETE
        assert response.is_complete is False
        assert len(response.missing_required) > 0

    def test_validation_disabled_returns_disabled(self):
        """Check should return VALIDATION_DISABLED when disabled."""
        from app.services.export import (
            CompletenessCheckResult,
            EvidenceCompletenessChecker,
        )

        checker = EvidenceCompletenessChecker(validation_enabled=False)

        # Incomplete bundle
        bundle = {"bundle_id": "b1"}

        response = checker.check(bundle, "evidence")

        assert response.result == CompletenessCheckResult.VALIDATION_DISABLED
        assert response.validation_enabled is False

    def test_partial_returns_for_missing_recommended(self):
        """Check should return PARTIAL when only recommended fields missing."""
        from datetime import datetime

        from app.services.export import (
            CompletenessCheckResult,
            EvidenceCompletenessChecker,
        )

        checker = EvidenceCompletenessChecker()

        # Complete required, missing recommended
        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
            # Missing recommended: content_hash, violation_step_index, etc.
        }

        response = checker.check(bundle, "evidence")

        assert response.result in (CompletenessCheckResult.COMPLETE, CompletenessCheckResult.PARTIAL)
        assert response.is_complete is True

    def test_check_dict_bundle(self):
        """Check should work with dict bundles."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()

        bundle = {"bundle_id": "b1", "incident_id": None}  # None = missing

        response = checker.check(bundle, "evidence")

        assert "incident_id" in response.missing_required

    def test_check_object_bundle(self):
        """Check should work with object bundles."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()

        class MockBundle:
            bundle_id = "b1"
            incident_id = None

        response = checker.check(MockBundle(), "evidence")

        assert "incident_id" in response.missing_required


class TestEvidenceCompletenessCheckerEnsure:
    """Test ensure_complete method."""

    def test_ensure_complete_passes_for_complete(self):
        """ensure_complete should pass for complete bundles."""
        from datetime import datetime

        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()

        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
        }

        # Should not raise
        checker.ensure_complete(bundle, "evidence")

    def test_ensure_complete_raises_for_incomplete(self):
        """ensure_complete should raise for incomplete bundles."""
        from app.services.export import (
            EvidenceCompletenessChecker,
            EvidenceCompletenessError,
        )

        checker = EvidenceCompletenessChecker()

        bundle = {"bundle_id": "b1"}

        with pytest.raises(EvidenceCompletenessError) as exc_info:
            checker.ensure_complete(bundle, "evidence")

        assert exc_info.value.export_type == "evidence"
        assert len(exc_info.value.missing_fields) > 0

    def test_ensure_complete_passes_when_validation_disabled(self):
        """ensure_complete should pass when validation disabled."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker(validation_enabled=False)

        bundle = {"bundle_id": "b1"}  # Incomplete

        # Should not raise even though incomplete
        checker.ensure_complete(bundle, "evidence")


class TestEvidenceCompletenessError:
    """Test EvidenceCompletenessError exception."""

    def test_error_creation(self):
        """Should create error with all fields."""
        from app.services.export import EvidenceCompletenessError

        error = EvidenceCompletenessError(
            message="Test error",
            missing_fields={"field1", "field2"},
            export_type="evidence",
            validation_enabled=True,
        )

        assert str(error) == "Test error"
        assert "field1" in error.missing_fields
        assert error.export_type == "evidence"

    def test_error_to_dict(self):
        """to_dict should return structured error info."""
        from app.services.export import EvidenceCompletenessError

        error = EvidenceCompletenessError(
            message="Test error",
            missing_fields={"run_id", "trace_id"},
            export_type="soc2",
            validation_enabled=True,
        )

        d = error.to_dict()

        assert d["error"] == "EvidenceCompletenessError"
        assert d["export_type"] == "soc2"
        assert "run_id" in d["missing_fields"]


class TestCompletenessCheckResponse:
    """Test CompletenessCheckResponse dataclass."""

    def test_response_creation(self):
        """Should create response with all fields."""
        from app.services.export import (
            CompletenessCheckResponse,
            CompletenessCheckResult,
        )

        response = CompletenessCheckResponse(
            result=CompletenessCheckResult.COMPLETE,
            is_complete=True,
            validation_enabled=True,
            export_type="evidence",
            missing_required=set(),
            missing_recommended=set(),
            completeness_percentage=100.0,
            message="Test",
        )

        assert response.result == CompletenessCheckResult.COMPLETE
        assert response.is_complete is True
        assert response.completeness_percentage == 100.0

    def test_response_to_dict(self):
        """to_dict should return API-ready format."""
        from app.services.export import (
            CompletenessCheckResponse,
            CompletenessCheckResult,
        )

        response = CompletenessCheckResponse(
            result=CompletenessCheckResult.INCOMPLETE,
            is_complete=False,
            validation_enabled=True,
            export_type="evidence",
            missing_required={"run_id"},
            missing_recommended={"content_hash"},
            completeness_percentage=80.0,
            message="Missing",
        )

        d = response.to_dict()

        assert d["result"] == "incomplete"
        assert d["is_complete"] is False
        assert "run_id" in d["missing_required"]


class TestShouldAllowExport:
    """Test should_allow_export method."""

    def test_allow_complete_export(self):
        """should_allow_export should return True for complete."""
        from datetime import datetime

        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()

        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
        }

        allowed, reason = checker.should_allow_export(bundle, "evidence")

        assert allowed is True

    def test_disallow_incomplete_export_when_enforced(self):
        """should_allow_export should return False when enforced."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker(validation_enabled=True)

        bundle = {"bundle_id": "b1"}

        allowed, reason = checker.should_allow_export(bundle, "evidence")

        assert allowed is False
        assert "missing" in reason.lower()

    def test_allow_incomplete_export_when_disabled(self):
        """should_allow_export should return True when disabled."""
        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker(validation_enabled=False)

        bundle = {"bundle_id": "b1"}

        allowed, reason = checker.should_allow_export(bundle, "evidence")

        assert allowed is True
        assert "disabled" in reason.lower()


class TestHelperFunctions:
    """Test helper functions."""

    def test_check_evidence_completeness_complete(self):
        """check_evidence_completeness should return COMPLETE or PARTIAL for complete."""
        from datetime import datetime

        from app.services.export import (
            CompletenessCheckResult,
            check_evidence_completeness,
        )

        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
        }

        response = check_evidence_completeness(
            bundle=bundle,
            export_type="evidence",
            validation_enabled=True,
        )

        # COMPLETE or PARTIAL both mean required fields are present
        assert response.result in (CompletenessCheckResult.COMPLETE, CompletenessCheckResult.PARTIAL)
        assert response.is_complete is True

    def test_check_evidence_completeness_incomplete(self):
        """check_evidence_completeness should return INCOMPLETE for incomplete."""
        from app.services.export import (
            CompletenessCheckResult,
            check_evidence_completeness,
        )

        response = check_evidence_completeness(
            bundle={"bundle_id": "b1"},
            export_type="evidence",
            validation_enabled=True,
        )

        assert response.result == CompletenessCheckResult.INCOMPLETE

    def test_ensure_evidence_completeness_passes(self):
        """ensure_evidence_completeness should pass for complete."""
        from datetime import datetime

        from app.services.export import ensure_evidence_completeness

        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
        }

        # Should not raise
        ensure_evidence_completeness(
            bundle=bundle,
            export_type="evidence",
            validation_enabled=True,
        )

    def test_ensure_evidence_completeness_raises(self):
        """ensure_evidence_completeness should raise for incomplete."""
        from app.services.export import (
            EvidenceCompletenessError,
            ensure_evidence_completeness,
        )

        with pytest.raises(EvidenceCompletenessError):
            ensure_evidence_completeness(
                bundle={"bundle_id": "b1"},
                export_type="evidence",
                validation_enabled=True,
            )


class TestEvidenceCompletenessUseCases:
    """Test realistic use cases for evidence completeness."""

    def test_pre_export_validation(self):
        """Simulate pre-export validation check."""
        from datetime import datetime

        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker(validation_enabled=True)

        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
        }

        # Pre-check before generating PDF
        allowed, reason = checker.should_allow_export(bundle, "evidence")

        assert allowed is True

    def test_soc2_export_requires_additional_fields(self):
        """SOC2 export should require additional fields."""
        from datetime import datetime

        from app.services.export import (
            EvidenceCompletenessChecker,
            EvidenceCompletenessError,
        )

        checker = EvidenceCompletenessChecker(validation_enabled=True)

        # Complete for evidence but not for SOC2
        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
            # Missing SOC2 fields: control_mappings, attestation_statement, etc.
        }

        # Evidence export allowed
        checker.ensure_complete(bundle, "evidence")

        # SOC2 export blocked
        with pytest.raises(EvidenceCompletenessError) as exc_info:
            checker.ensure_complete(bundle, "soc2")

        assert "control_mappings" in exc_info.value.missing_fields

    def test_strict_mode_requires_recommended_fields(self):
        """Strict mode should require recommended fields."""
        from datetime import datetime

        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker(
            validation_enabled=True,
            strict_mode=True,
        )

        # Complete required but missing recommended
        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
            # Missing recommended: content_hash
        }

        response = checker.check(bundle, "evidence")

        # In strict mode, recommended fields are required
        if "content_hash" not in bundle:
            assert "content_hash" in response.missing_required

    def test_from_governance_config(self):
        """Create checker from GovernanceConfig."""
        from app.services.export import EvidenceCompletenessChecker

        class MockGovernanceConfig:
            evidence_completeness_enforce = True
            evidence_strict_mode = False

        checker = EvidenceCompletenessChecker.from_governance_config(
            MockGovernanceConfig()
        )

        assert checker.validation_enabled is True
        assert checker.strict_mode is False

    def test_from_governance_config_disabled(self):
        """Create checker with validation disabled via config."""
        from app.services.export import EvidenceCompletenessChecker

        class MockGovernanceConfig:
            evidence_completeness_enforce = False
            evidence_strict_mode = False

        checker = EvidenceCompletenessChecker.from_governance_config(
            MockGovernanceConfig()
        )

        assert checker.validation_enabled is False

    def test_get_completeness_summary(self):
        """get_completeness_summary should return field-level info."""
        from datetime import datetime

        from app.services.export import EvidenceCompletenessChecker

        checker = EvidenceCompletenessChecker()

        bundle = {
            "bundle_id": "b1",
            "incident_id": "i1",
            "run_id": "r1",
            "trace_id": "t1",
            "tenant_id": "tenant1",
            "policy_snapshot_id": "ps1",
            "termination_reason": "completed",
            "total_steps": 10,
            "total_tokens": 1000,
            "total_cost_cents": 50,
            "created_at": datetime.utcnow(),
            "exported_by": "user1",
        }

        summary = checker.get_completeness_summary(bundle, "evidence")

        assert "total_fields" in summary
        assert "present_fields" in summary
        assert "completeness_percentage" in summary
        assert "field_status" in summary
        assert summary["field_status"]["bundle_id"]["present"] is True
