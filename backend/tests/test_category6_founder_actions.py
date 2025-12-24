"""
M29 Category 6: Founder Action Paths Backend Tests

Verifies that:
1. Action DTOs have correct fields and types
2. All 4 actions are defined (FREEZE_TENANT, THROTTLE_TENANT, FREEZE_API_KEY, OVERRIDE_INCIDENT)
3. All 3 reversals are defined (UNFREEZE_TENANT, UNTHROTTLE_TENANT, UNFREEZE_API_KEY)
4. Safety rails are implemented (rate limit, mutual exclusion, MFA)
5. Audit trail is mandatory
6. OVERRIDE_INCIDENT is not reversible
7. Customer tokens cannot trigger actions

Test Date: 2025-12-24
"""

import inspect
from typing import Literal, get_origin, get_type_hints

import pytest

# Action DTOs
from app.contracts.ops import (
    FounderActionReasonDTO,
    FounderActionRequestDTO,
    FounderActionResponseDTO,
    FounderActionTargetDTO,
    FounderAuditRecordDTO,
    FounderReversalRequestDTO,
)

# FounderAction model
from app.models.tenant import FounderAction

# =============================================================================
# CATEGORY 6 CORE INVARIANT: Every action is audited, reversible (except override)
# =============================================================================


class TestActionDTOStructure:
    """Verify Action DTO structure matches spec."""

    def test_action_request_has_required_fields(self):
        """FounderActionRequestDTO must have all required fields."""
        required_fields = {"action", "target", "reason", "source_incident_id"}
        fields = set(FounderActionRequestDTO.model_fields.keys())
        missing = required_fields - fields
        assert not missing, f"FounderActionRequestDTO missing fields: {missing}"

    def test_action_has_exactly_4_types(self):
        """Action field must have exactly 4 allowed values."""
        hints = get_type_hints(FounderActionRequestDTO)
        action_type = hints.get("action")

        if get_origin(action_type) is Literal:
            values = set(action_type.__args__)
            expected = {
                "FREEZE_TENANT",
                "THROTTLE_TENANT",
                "FREEZE_API_KEY",
                "OVERRIDE_INCIDENT",
            }
            assert values == expected, f"Action types should be {expected}, got {values}"

    def test_target_has_required_fields(self):
        """FounderActionTargetDTO must have type and id."""
        required_fields = {"type", "id"}
        fields = set(FounderActionTargetDTO.model_fields.keys())
        missing = required_fields - fields
        assert not missing, f"FounderActionTargetDTO missing fields: {missing}"

    def test_target_type_has_3_values(self):
        """Target type must have TENANT, API_KEY, INCIDENT."""
        hints = get_type_hints(FounderActionTargetDTO)
        target_type = hints.get("type")

        if get_origin(target_type) is Literal:
            values = set(target_type.__args__)
            expected = {"TENANT", "API_KEY", "INCIDENT"}
            assert values == expected, f"Target types should be {expected}, got {values}"

    def test_reason_has_required_fields(self):
        """FounderActionReasonDTO must have code and note."""
        required_fields = {"code", "note"}
        fields = set(FounderActionReasonDTO.model_fields.keys())
        missing = required_fields - fields
        assert not missing, f"FounderActionReasonDTO missing fields: {missing}"

    def test_reason_code_has_6_values(self):
        """Reason code must have 6 allowed values."""
        hints = get_type_hints(FounderActionReasonDTO)
        code_type = hints.get("code")

        if get_origin(code_type) is Literal:
            values = set(code_type.__args__)
            expected = {
                "COST_ANOMALY",
                "POLICY_VIOLATION",
                "RETRY_LOOP",
                "ABUSE_SUSPECTED",
                "FALSE_POSITIVE",
                "OTHER",
            }
            assert values == expected, f"Reason codes should be {expected}, got {values}"


class TestResponseDTOStructure:
    """Verify Response DTO structure matches spec."""

    def test_response_has_required_fields(self):
        """FounderActionResponseDTO must have all required fields."""
        required_fields = {
            "status",
            "action_id",
            "applied_at",
            "reversible",
            "undo_hint",
            "message",
        }
        fields = set(FounderActionResponseDTO.model_fields.keys())
        missing = required_fields - fields
        assert not missing, f"FounderActionResponseDTO missing fields: {missing}"

    def test_response_status_has_4_values(self):
        """Status must have APPLIED, REJECTED, RATE_LIMITED, CONFLICT."""
        hints = get_type_hints(FounderActionResponseDTO)
        status_type = hints.get("status")

        if get_origin(status_type) is Literal:
            values = set(status_type.__args__)
            expected = {"APPLIED", "REJECTED", "RATE_LIMITED", "CONFLICT"}
            assert values == expected, f"Status values should be {expected}, got {values}"


class TestAuditDTOStructure:
    """Verify Audit DTO structure matches spec."""

    def test_audit_has_required_fields(self):
        """FounderAuditRecordDTO must have all required fields."""
        required_fields = {
            "audit_id",
            "action_id",
            "action_type",
            "target_type",
            "target_id",
            "reason_code",
            "reason_note",
            "source_incident_id",
            "founder_id",
            "founder_email",
            "mfa_verified",
            "applied_at",
            "reversed_at",
            "reversed_by_action_id",
        }
        fields = set(FounderAuditRecordDTO.model_fields.keys())
        missing = required_fields - fields
        assert not missing, f"FounderAuditRecordDTO missing fields: {missing}"

    def test_audit_action_type_includes_reversals(self):
        """Audit action_type must include all actions and reversals."""
        hints = get_type_hints(FounderAuditRecordDTO)
        action_type = hints.get("action_type")

        if get_origin(action_type) is Literal:
            values = set(action_type.__args__)
            expected = {
                "FREEZE_TENANT",
                "THROTTLE_TENANT",
                "FREEZE_API_KEY",
                "OVERRIDE_INCIDENT",
                "UNFREEZE_TENANT",
                "UNTHROTTLE_TENANT",
                "UNFREEZE_API_KEY",
            }
            assert values == expected, f"Audit action types should be {expected}, got {values}"


class TestReversalDTOStructure:
    """Verify Reversal DTO structure matches spec."""

    def test_reversal_has_required_fields(self):
        """FounderReversalRequestDTO must have action_id and reason."""
        required_fields = {"action_id", "reason"}
        fields = set(FounderReversalRequestDTO.model_fields.keys())
        missing = required_fields - fields
        assert not missing, f"FounderReversalRequestDTO missing fields: {missing}"


# =============================================================================
# FOUNDER ACTION MODEL TESTS
# =============================================================================


class TestFounderActionModel:
    """Verify FounderAction model has all required fields."""

    def test_model_has_required_fields(self):
        """FounderAction model must have all required fields."""
        required_fields = {
            "id",
            "action_type",
            "target_type",
            "target_id",
            "target_name",
            "reason_code",
            "reason_note",
            "source_incident_id",
            "founder_id",
            "founder_email",
            "mfa_verified",
            "applied_at",
            "reversed_at",
            "reversed_by_action_id",
            "is_active",
            "is_reversible",
        }
        fields = set(FounderAction.model_fields.keys())
        missing = required_fields - fields
        assert not missing, f"FounderAction model missing fields: {missing}"

    def test_model_has_is_reversal_property(self):
        """FounderAction model must have is_reversal property."""
        assert hasattr(FounderAction, "is_reversal"), "FounderAction missing is_reversal property"


# =============================================================================
# ENDPOINT REGISTRATION TESTS
# =============================================================================


class TestEndpointRegistration:
    """Verify endpoints are registered in founder_actions.py."""

    def test_action_endpoints_exist(self):
        """Verify all 4 action endpoints are defined."""
        import app.api.founder_actions as actions_module

        source_file = inspect.getfile(actions_module)
        with open(source_file, "r") as f:
            source = f.read()

        # Check all 4 action endpoints
        assert "/freeze-tenant" in source, "freeze-tenant endpoint not found"
        assert "/throttle-tenant" in source, "throttle-tenant endpoint not found"
        assert "/freeze-api-key" in source, "freeze-api-key endpoint not found"
        assert "/override-incident" in source, "override-incident endpoint not found"

    def test_reversal_endpoints_exist(self):
        """Verify all 3 reversal endpoints are defined."""
        import app.api.founder_actions as actions_module

        source_file = inspect.getfile(actions_module)
        with open(source_file, "r") as f:
            source = f.read()

        # Check all 3 reversal endpoints
        assert "/unfreeze-tenant" in source, "unfreeze-tenant endpoint not found"
        assert "/unthrottle-tenant" in source, "unthrottle-tenant endpoint not found"
        assert "/unfreeze-api-key" in source, "unfreeze-api-key endpoint not found"

    def test_audit_endpoints_exist(self):
        """Verify audit trail endpoints are defined."""
        import app.api.founder_actions as actions_module

        source_file = inspect.getfile(actions_module)
        with open(source_file, "r") as f:
            source = f.read()

        assert "/audit" in source, "audit list endpoint not found"
        assert "/audit/{action_id}" in source, "audit detail endpoint not found"

    def test_uses_fops_auth(self):
        """All endpoints must use verify_fops_token."""
        import app.api.founder_actions as actions_module

        source_file = inspect.getfile(actions_module)
        with open(source_file, "r") as f:
            source = f.read()

        assert "verify_fops_token" in source, "Endpoints should use FOPS auth"
        assert "verify_console_token" not in source, "Should NOT use console auth"


# =============================================================================
# SAFETY RAILS TESTS
# =============================================================================


class TestSafetyRails:
    """Verify safety rails are implemented."""

    def test_rate_limit_configured(self):
        """Rate limit must be configured."""
        import app.api.founder_actions as actions_module

        assert hasattr(actions_module, "MAX_ACTIONS_PER_HOUR"), "Rate limit not configured"
        assert actions_module.MAX_ACTIONS_PER_HOUR > 0, "Rate limit must be positive"

    def test_reversal_map_configured(self):
        """Reversal map must be configured."""
        import app.api.founder_actions as actions_module

        assert hasattr(actions_module, "REVERSAL_MAP"), "Reversal map not configured"
        reversal_map = actions_module.REVERSAL_MAP

        expected = {
            "FREEZE_TENANT": "UNFREEZE_TENANT",
            "THROTTLE_TENANT": "UNTHROTTLE_TENANT",
            "FREEZE_API_KEY": "UNFREEZE_API_KEY",
        }
        assert reversal_map == expected, f"Reversal map should be {expected}, got {reversal_map}"

    def test_reversible_actions_configured(self):
        """Reversible actions must be configured correctly."""
        import app.api.founder_actions as actions_module

        assert hasattr(actions_module, "REVERSIBLE_ACTIONS"), "Reversible actions not configured"
        reversible = actions_module.REVERSIBLE_ACTIONS

        expected = {"FREEZE_TENANT", "THROTTLE_TENANT", "FREEZE_API_KEY"}
        assert reversible == expected, f"Reversible actions should be {expected}, got {reversible}"

    def test_override_incident_not_reversible(self):
        """OVERRIDE_INCIDENT must NOT be in reversible actions."""
        import app.api.founder_actions as actions_module

        reversible = actions_module.REVERSIBLE_ACTIONS
        assert "OVERRIDE_INCIDENT" not in reversible, "OVERRIDE_INCIDENT should NOT be reversible"

    def test_mutual_exclusion_configured(self):
        """Mutual exclusion must be configured for freeze and throttle."""
        import app.api.founder_actions as actions_module

        assert hasattr(actions_module, "MUTUALLY_EXCLUSIVE"), "Mutual exclusion not configured"
        exclusive = actions_module.MUTUALLY_EXCLUSIVE

        # Check that FREEZE_TENANT and THROTTLE_TENANT are mutually exclusive
        found_pair = False
        for pair in exclusive:
            if "FREEZE_TENANT" in pair and "THROTTLE_TENANT" in pair:
                found_pair = True
                break

        assert found_pair, "FREEZE_TENANT and THROTTLE_TENANT should be mutually exclusive"


# =============================================================================
# DTO INSTANTIATION TESTS
# =============================================================================


class TestDTOInstantiation:
    """Verify DTOs can be instantiated with valid data."""

    def test_action_request_instantiation(self):
        """FounderActionRequestDTO can be created with valid data."""
        dto = FounderActionRequestDTO(
            action="FREEZE_TENANT",
            target=FounderActionTargetDTO(
                type="TENANT",
                id="tenant_abc123",
            ),
            reason=FounderActionReasonDTO(
                code="COST_ANOMALY",
                note="Spending 40% above baseline",
            ),
            source_incident_id="inc_xyz789",
        )

        assert dto.action == "FREEZE_TENANT"
        assert dto.target.type == "TENANT"
        assert dto.reason.code == "COST_ANOMALY"

    def test_action_response_instantiation(self):
        """FounderActionResponseDTO can be created with valid data."""
        dto = FounderActionResponseDTO(
            status="APPLIED",
            action_id="action_abc123def456",
            applied_at="2025-12-24T10:30:00Z",
            reversible=True,
            undo_hint="Use POST /ops/actions/unfreeze-tenant",
            message=None,
        )

        assert dto.status == "APPLIED"
        assert dto.reversible is True
        assert dto.undo_hint is not None

    def test_audit_record_instantiation(self):
        """FounderAuditRecordDTO can be created with valid data."""
        dto = FounderAuditRecordDTO(
            audit_id="audit_xyz123",
            action_id="action_abc123def456",
            action_type="FREEZE_TENANT",
            target_type="TENANT",
            target_id="tenant_abc123",
            reason_code="COST_ANOMALY",
            reason_note="Spending above baseline",
            source_incident_id="inc_xyz789",
            founder_id="founder_001",
            founder_email="admin@company.com",
            mfa_verified=True,
            applied_at="2025-12-24T10:30:00Z",
            reversed_at=None,
            reversed_by_action_id=None,
        )

        assert dto.action_type == "FREEZE_TENANT"
        assert dto.mfa_verified is True
        assert dto.reversed_at is None

    def test_reversal_request_instantiation(self):
        """FounderReversalRequestDTO can be created with valid data."""
        dto = FounderReversalRequestDTO(
            action_id="action_abc123def456",
            reason="False positive confirmed",
        )

        assert dto.action_id == "action_abc123def456"
        assert dto.reason == "False positive confirmed"


# =============================================================================
# INVARIANT TESTS
# =============================================================================


class TestInvariants:
    """Verify Category 6 invariants are enforced."""

    def test_invariant_1_audit_mandatory(self):
        """Every action must have audit record (FounderAction model exists)."""
        # FounderAction model exists with all audit fields
        fields = set(FounderAction.model_fields.keys())
        assert "founder_id" in fields, "Must track who took action"
        assert "founder_email" in fields, "Must track founder email"
        assert "mfa_verified" in fields, "Must track MFA verification"
        assert "applied_at" in fields, "Must track when applied"

    def test_invariant_2_mutual_exclusion(self):
        """Freeze and throttle must be mutually exclusive."""
        import app.api.founder_actions as actions_module

        exclusive = actions_module.MUTUALLY_EXCLUSIVE
        pairs = [set(p) for p in exclusive]

        freeze_throttle = {"FREEZE_TENANT", "THROTTLE_TENANT"}
        assert freeze_throttle in pairs, "FREEZE_TENANT and THROTTLE_TENANT must be mutually exclusive"

    def test_invariant_3_override_not_reversible(self):
        """OVERRIDE_INCIDENT must NOT be reversible."""
        import app.api.founder_actions as actions_module

        reversible = actions_module.REVERSIBLE_ACTIONS
        reversal_map = actions_module.REVERSAL_MAP

        assert "OVERRIDE_INCIDENT" not in reversible, "OVERRIDE_INCIDENT should not be reversible"
        assert "OVERRIDE_INCIDENT" not in reversal_map, "OVERRIDE_INCIDENT should not have reversal"

    def test_invariant_4_fops_auth_only(self):
        """Actions must require FOPS auth, not console auth."""
        import app.api.founder_actions as actions_module

        source_file = inspect.getfile(actions_module)
        with open(source_file, "r") as f:
            source = f.read()

        assert "verify_fops_token" in source, "Must use FOPS auth"
        assert "FounderToken" in source, "Must use FounderToken"
        assert "verify_console_token" not in source, "Must NOT use console auth"
        assert "CustomerToken" not in source, "Must NOT use CustomerToken"

    def test_invariant_5_rate_limited(self):
        """Actions must be rate limited."""
        import app.api.founder_actions as actions_module

        assert hasattr(actions_module, "MAX_ACTIONS_PER_HOUR"), "Rate limit must be configured"
        assert hasattr(actions_module, "check_rate_limit"), "Rate limit check function must exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
