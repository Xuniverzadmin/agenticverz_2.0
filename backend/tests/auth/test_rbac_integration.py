# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Unit tests for RBAC integration layer (L6)
# Reference: PIN-271 (RBAC Authority Separation)

"""
Unit tests for RBAC integration layer.

Tests cover:
- Actor extraction from requests
- Fallback actor building from RBACv1 roles
- Authorization with RBACv2 AuthorizationEngine
- Decision comparison between RBACv1 and RBACv2 systems
- Role mapping between RBACv1 and RBACv2 systems

Terminology (LOCKED - PIN-273):
- RBACv1: Enforcement Authority (existing path)
- RBACv2: Reference Authority (ActorContext + AuthEngine)
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request

from app.auth.actor import ActorContext, ActorType, IdentitySource
from app.auth.authorization import AuthorizationResult
from app.auth.authorization import Decision as V2Decision
from app.auth.rbac_integration import (
    DecisionComparison,
    authorize_with_new_engine,
    build_fallback_actor_from_old_roles,
    compare_decisions,
    log_decision_comparison,
    map_old_roles_to_new_roles,
    map_policy_to_permission,
)
from app.auth.rbac_middleware import Decision as V1Decision
from app.auth.rbac_middleware import PolicyObject


class TestMapPolicyToPermission:
    """Tests for policy to permission mapping."""

    def test_simple_mapping(self):
        """Test simple policy to permission conversion."""
        policy = PolicyObject(resource="runs", action="read")
        assert map_policy_to_permission(policy) == "read:runs"

    def test_complex_resource(self):
        """Test policy with complex resource name."""
        policy = PolicyObject(resource="memory_pin", action="admin")
        assert map_policy_to_permission(policy) == "admin:memory_pin"


class TestMapOldRolesToNewRoles:
    """Tests for role mapping between old and new systems."""

    def test_infra_maps_to_admin(self):
        """Test infra role maps to admin."""
        old_roles = ["infra"]
        new_roles = map_old_roles_to_new_roles(old_roles)
        assert "admin" in new_roles

    def test_readonly_maps_to_viewer(self):
        """Test readonly role maps to viewer."""
        old_roles = ["readonly"]
        new_roles = map_old_roles_to_new_roles(old_roles)
        assert "viewer" in new_roles

    def test_dev_maps_to_developer(self):
        """Test dev role maps to developer."""
        old_roles = ["dev"]
        new_roles = map_old_roles_to_new_roles(old_roles)
        assert "developer" in new_roles

    def test_founder_stays_founder(self):
        """Test founder role stays as founder."""
        old_roles = ["founder"]
        new_roles = map_old_roles_to_new_roles(old_roles)
        assert "founder" in new_roles

    def test_multiple_roles(self):
        """Test multiple roles are all mapped."""
        old_roles = ["infra", "readonly"]
        new_roles = map_old_roles_to_new_roles(old_roles)
        assert "admin" in new_roles
        assert "viewer" in new_roles


class TestBuildFallbackActor:
    """Tests for building fallback actor from old roles."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.headers = {}
        return request

    def test_returns_none_for_empty_roles(self, mock_request):
        """Test returns None when roles is empty."""
        result = build_fallback_actor_from_old_roles([], mock_request)
        assert result is None

    def test_founder_becomes_operator(self, mock_request):
        """Test founder role creates operator actor type."""
        mock_request.headers = {"X-Machine-Token": "test"}
        actor = build_fallback_actor_from_old_roles(["founder"], mock_request)
        assert actor is not None
        assert actor.actor_type == ActorType.OPERATOR

    def test_machine_becomes_system(self, mock_request):
        """Test machine role creates system actor type."""
        mock_request.headers = {"X-Machine-Token": "test"}
        actor = build_fallback_actor_from_old_roles(["machine"], mock_request)
        assert actor is not None
        assert actor.actor_type == ActorType.SYSTEM

    def test_admin_becomes_external_paid(self, mock_request):
        """Test admin role creates external paid actor type."""
        mock_request.headers = {"Authorization": "Bearer token"}
        actor = build_fallback_actor_from_old_roles(["admin"], mock_request)
        assert actor is not None
        assert actor.actor_type == ActorType.EXTERNAL_PAID

    def test_detects_system_source_from_machine_token(self, mock_request):
        """Test source is SYSTEM when X-Machine-Token is present."""
        mock_request.headers = {"X-Machine-Token": "secret"}
        actor = build_fallback_actor_from_old_roles(["admin"], mock_request)
        assert actor.source == IdentitySource.SYSTEM

    def test_detects_clerk_source_from_bearer(self, mock_request):
        """Test source is CLERK when Bearer token is present."""
        mock_request.headers = {"Authorization": "Bearer token123"}
        actor = build_fallback_actor_from_old_roles(["admin"], mock_request)
        assert actor.source == IdentitySource.CLERK

    def test_detects_dev_source_from_roles_header(self, mock_request):
        """Test source is DEV when X-Roles header is present."""
        mock_request.headers = {"X-Roles": "admin,dev"}
        actor = build_fallback_actor_from_old_roles(["admin"], mock_request)
        assert actor.source == IdentitySource.DEV

    def test_extracts_tenant_from_header(self, mock_request):
        """Test tenant_id is extracted from X-Tenant-ID header."""
        mock_request.headers = {"X-Tenant-ID": "tenant-123"}
        actor = build_fallback_actor_from_old_roles(["admin"], mock_request)
        assert actor.tenant_id == "tenant-123"


class TestAuthorizeWithNewEngine:
    """Tests for authorization with new engine."""

    @pytest.fixture
    def policy(self):
        """Create test policy."""
        return PolicyObject(resource="runs", action="read")

    def test_returns_deny_for_none_actor(self, policy):
        """Test returns deny when actor is None."""
        result = authorize_with_new_engine(None, policy)

        assert result.allowed is False
        assert result.decision == V2Decision.DENY
        assert "no_actor" in result.reason

    def test_authorizes_with_actor(self, policy):
        """Test authorization with valid actor."""
        actor = ActorContext(
            actor_id="user-1",
            actor_type=ActorType.OPERATOR,
            source=IdentitySource.CLERK,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset({"founder"}),
            permissions=frozenset({"*"}),
        )

        result = authorize_with_new_engine(actor, policy)

        assert result.allowed is True
        assert result.decision == V2Decision.ALLOW

    def test_computes_permissions_if_empty(self, policy):
        """Test permissions are computed if not present."""
        actor = ActorContext(
            actor_id="user-1",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-1",
            account_id=None,
            team_id=None,
            roles=frozenset({"developer"}),
            permissions=frozenset(),  # Empty - should be computed
        )

        result = authorize_with_new_engine(actor, policy)

        # Developer role should have read:* permission
        assert result.allowed is True


class TestCompareDecisions:
    """Tests for decision comparison."""

    @pytest.fixture
    def policy(self):
        """Create test policy."""
        return PolicyObject(resource="runs", action="read")

    @pytest.fixture
    def operator_actor(self):
        """Create operator actor for tests."""
        return ActorContext(
            actor_id="founder-1",
            actor_type=ActorType.OPERATOR,
            source=IdentitySource.CLERK,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset({"founder"}),
            permissions=frozenset({"*"}),
        )

    def test_matching_allow_decisions(self, policy, operator_actor):
        """Test comparison when both systems allow."""
        old_decision = V1Decision(allowed=True, reason="role:founder", roles=["founder"])
        new_result = AuthorizationResult(
            allowed=True,
            decision=V2Decision.ALLOW,
            reason="operator_bypass",
            actor=operator_actor,
            resource="runs",
            action="read",
        )

        comparison = compare_decisions(old_decision, new_result, policy)

        assert comparison.match is True
        assert comparison.discrepancy_type is None
        assert comparison.old_allowed is True
        assert comparison.new_allowed is True

    def test_matching_deny_decisions(self, policy, operator_actor):
        """Test comparison when both systems deny."""
        old_decision = V1Decision(allowed=False, reason="no-credentials", roles=[])
        new_result = AuthorizationResult(
            allowed=False,
            decision=V2Decision.DENY,
            reason="no_actor:identity_extraction_failed",
            actor=operator_actor,
            resource="runs",
            action="read",
        )

        comparison = compare_decisions(old_decision, new_result, policy)

        assert comparison.match is True
        assert comparison.discrepancy_type is None

    def test_new_more_restrictive(self, policy, operator_actor):
        """Test comparison when new system is more restrictive."""
        old_decision = V1Decision(allowed=True, reason="role:admin", roles=["admin"])
        new_result = AuthorizationResult(
            allowed=False,
            decision=V2Decision.DENY,
            reason="no_permission:read:runs",
            actor=operator_actor,
            resource="runs",
            action="read",
        )

        comparison = compare_decisions(old_decision, new_result, policy)

        assert comparison.match is False
        assert comparison.discrepancy_type == "v2_more_restrictive"

    def test_new_more_permissive(self, policy, operator_actor):
        """Test comparison when new system is more permissive."""
        old_decision = V1Decision(allowed=False, reason="no-credentials", roles=[])
        new_result = AuthorizationResult(
            allowed=True,
            decision=V2Decision.ALLOW,
            reason="operator_bypass",
            actor=operator_actor,
            resource="runs",
            action="read",
        )

        comparison = compare_decisions(old_decision, new_result, policy)

        assert comparison.match is False
        assert comparison.discrepancy_type == "v2_more_permissive"

    def test_comparison_includes_context(self, policy, operator_actor):
        """Test comparison includes full context."""
        old_decision = V1Decision(allowed=True, reason="role:founder", roles=["founder"])
        new_result = AuthorizationResult(
            allowed=True,
            decision=V2Decision.ALLOW,
            reason="operator_bypass",
            actor=operator_actor,
            resource="runs",
            action="read",
        )

        comparison = compare_decisions(old_decision, new_result, policy)

        assert comparison.resource == "runs"
        assert comparison.action == "read"
        assert comparison.actor_id == "founder-1"
        assert comparison.old_reason == "role:founder"
        assert comparison.new_reason == "operator_bypass"


class TestDecisionComparisonToDict:
    """Tests for DecisionComparison.to_dict()."""

    def test_to_dict_contains_all_fields(self):
        """Test to_dict returns all comparison fields."""
        comparison = DecisionComparison(
            v1_allowed=True,
            v2_allowed=False,
            match=False,
            discrepancy_type="v2_more_restrictive",
            v1_reason="role:admin",
            v2_reason="no_permission",
            actor_id="user-1",
            resource="runs",
            action="delete",
        )

        result = comparison.to_dict()

        assert result["v1_allowed"] is True
        assert result["v2_allowed"] is False
        assert result["match"] is False
        assert result["discrepancy_type"] == "v2_more_restrictive"
        assert result["v1_reason"] == "role:admin"
        assert result["v2_reason"] == "no_permission"
        assert result["actor_id"] == "user-1"
        assert result["resource"] == "runs"
        assert result["action"] == "delete"


class TestLogDecisionComparison:
    """Tests for logging decision comparisons."""

    def test_logs_match_at_debug_level(self):
        """Test matching decisions are logged at debug level."""
        comparison = DecisionComparison(
            v1_allowed=True,
            v2_allowed=True,
            match=True,
            discrepancy_type=None,
            v1_reason="role:admin",
            v2_reason="permission:read:runs",
            actor_id="user-1",
            resource="runs",
            action="read",
        )

        with patch("app.auth.rbac_integration.logger") as mock_logger:
            log_decision_comparison(comparison, "/api/v1/runs", "GET")

            # Should call debug for matching decisions
            mock_logger.debug.assert_called_once()
            mock_logger.warning.assert_not_called()

    def test_logs_mismatch_at_warning_level(self):
        """Test mismatched decisions are logged at warning level."""
        comparison = DecisionComparison(
            v1_allowed=True,
            v2_allowed=False,
            match=False,
            discrepancy_type="v2_more_restrictive",
            v1_reason="role:admin",
            v2_reason="no_permission",
            actor_id="user-1",
            resource="runs",
            action="read",
        )

        with patch("app.auth.rbac_integration.logger") as mock_logger:
            log_decision_comparison(comparison, "/api/v1/runs", "GET")

            # Should call warning for mismatched decisions
            mock_logger.warning.assert_called_once()
            mock_logger.debug.assert_not_called()
