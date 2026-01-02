# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Unit tests for AuthorizationEngine (L4)
# Reference: PIN-271 (RBAC Authority Separation)

"""
Unit tests for AuthorizationEngine.

Tests cover:
- Permission computation from roles
- Authorization decisions
- ActorType restrictions
- Tenant isolation
- Operator bypass
- Wildcard matching
"""

import pytest

from app.auth.actor import ActorContext, ActorType, IdentitySource
from app.auth.authorization import (
    AuthorizationEngine,
    AuthorizationResult,
    Decision,
    authorize,
    get_authorization_engine,
)


@pytest.fixture
def engine() -> AuthorizationEngine:
    """Create fresh authorization engine."""
    return AuthorizationEngine()


@pytest.fixture
def external_paid_actor() -> ActorContext:
    """Create an external paid customer actor."""
    return ActorContext(
        actor_id="user-123",
        actor_type=ActorType.EXTERNAL_PAID,
        source=IdentitySource.CLERK,
        tenant_id="tenant-abc",
        account_id="acct-xyz",
        team_id="team-1",
        roles=frozenset({"developer"}),
        permissions=frozenset(),  # Will be computed
    )


@pytest.fixture
def operator_actor() -> ActorContext:
    """Create an operator actor."""
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


@pytest.fixture
def system_actor() -> ActorContext:
    """Create a system actor."""
    return ActorContext(
        actor_id="system:ci",
        actor_type=ActorType.SYSTEM,
        source=IdentitySource.SYSTEM,
        tenant_id=None,
        account_id=None,
        team_id=None,
        roles=frozenset({"ci"}),
        permissions=frozenset({"read:*", "write:metrics"}),
    )


@pytest.fixture
def trial_actor() -> ActorContext:
    """Create a trial user actor."""
    return ActorContext(
        actor_id="trial-user",
        actor_type=ActorType.EXTERNAL_TRIAL,
        source=IdentitySource.CLERK,
        tenant_id="trial-tenant",
        account_id=None,
        team_id=None,
        roles=frozenset({"viewer"}),
        permissions=frozenset(),
    )


class TestComputePermissions:
    """Tests for permission computation from roles."""

    def test_compute_developer_permissions(self, engine, external_paid_actor):
        """Test developer role gets correct permissions."""
        actor = engine.compute_permissions(external_paid_actor)

        assert actor.has_permission("read:runs")
        assert actor.has_permission("write:runs")
        assert actor.has_permission("write:agents")
        assert actor.has_permission("execute:anything")  # execute:*

    def test_compute_admin_permissions(self, engine):
        """Test admin role gets correct permissions."""
        actor = ActorContext(
            actor_id="admin-1",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset({"admin"}),
            permissions=frozenset(),
        )

        computed = engine.compute_permissions(actor)

        assert computed.has_permission("read:runs")
        assert computed.has_permission("write:runs")
        assert computed.has_permission("delete:runs")
        assert computed.has_permission("admin:account")

    def test_compute_founder_permissions(self, engine, operator_actor):
        """Test founder role gets full access."""
        # Operator already has * in permissions, but test the role mapping
        actor = ActorContext(
            actor_id="founder-1",
            actor_type=ActorType.OPERATOR,
            source=IdentitySource.CLERK,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset({"founder"}),
            permissions=frozenset(),
        )

        computed = engine.compute_permissions(actor)

        assert "*" in computed.permissions
        assert computed.has_permission("anything:everything")

    def test_compute_multiple_roles(self, engine):
        """Test multiple roles combine permissions."""
        actor = ActorContext(
            actor_id="user-multi",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset({"developer", "viewer"}),
            permissions=frozenset(),
        )

        computed = engine.compute_permissions(actor)

        # Should have both developer and viewer permissions
        assert computed.has_permission("write:runs")  # from developer
        assert computed.has_permission("audit:anything")  # from viewer (audit:*)

    def test_compute_preserves_metadata(self, engine):
        """Test compute_permissions preserves all metadata."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id="acct-xyz",
            team_id="team-1",
            roles=frozenset({"developer"}),
            permissions=frozenset(),
            email="user@example.com",
            display_name="Test User",
        )

        computed = engine.compute_permissions(actor)

        assert computed.actor_id == actor.actor_id
        assert computed.actor_type == actor.actor_type
        assert computed.source == actor.source
        assert computed.tenant_id == actor.tenant_id
        assert computed.account_id == actor.account_id
        assert computed.team_id == actor.team_id
        assert computed.email == actor.email
        assert computed.display_name == actor.display_name


class TestAuthorize:
    """Tests for authorization decisions."""

    def test_allow_with_permission(self, engine):
        """Test allow when actor has permission."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"read:runs", "write:runs"}),
        )

        result = engine.authorize(actor, "runs", "read")

        assert result.allowed is True
        assert result.decision == Decision.ALLOW
        assert "permission" in result.reason

    def test_deny_without_permission(self, engine):
        """Test deny when actor lacks permission."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"read:runs"}),
        )

        result = engine.authorize(actor, "runs", "delete")

        assert result.allowed is False
        assert result.decision == Decision.DENY
        assert "no_permission" in result.reason

    def test_operator_bypass(self, engine, operator_actor):
        """Test operators bypass all permission checks."""
        result = engine.authorize(operator_actor, "anything", "everything")

        assert result.allowed is True
        assert result.decision == Decision.ALLOW
        assert "operator_bypass" in result.reason

    def test_operator_bypass_tenant_isolation(self, engine, operator_actor):
        """Test operators bypass tenant isolation."""
        result = engine.authorize(operator_actor, "runs", "read", tenant_id="other-tenant")

        assert result.allowed is True
        assert "operator_bypass" in result.reason

    def test_tenant_isolation_same_tenant(self, engine):
        """Test access allowed for same tenant."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"read:runs"}),
        )

        result = engine.authorize(actor, "runs", "read", tenant_id="tenant-abc")

        assert result.allowed is True

    def test_tenant_isolation_different_tenant(self, engine):
        """Test access denied for different tenant."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"read:runs"}),
        )

        result = engine.authorize(actor, "runs", "read", tenant_id="tenant-xyz")

        assert result.allowed is False
        assert "tenant_isolation" in result.reason


class TestActorTypeRestrictions:
    """Tests for ActorType-based restrictions."""

    def test_external_paid_allowed_actions(self, engine):
        """Test external paid can access allowed resources."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"read:runs", "write:runs"}),
        )

        # Allowed actions
        assert engine.authorize(actor, "runs", "read").allowed is True
        assert engine.authorize(actor, "runs", "write").allowed is True

    def test_external_paid_forbidden_actions(self, engine):
        """Test external paid cannot access system resources."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"*"}),  # Even with wildcard permission
        )

        # Forbidden actions (system scope)
        result = engine.authorize(actor, "system", "admin")
        assert result.allowed is False
        assert "forbidden" in result.reason

    def test_trial_forbidden_policies(self, engine, trial_actor):
        """Test trial users cannot write policies."""
        # Compute permissions for trial
        actor = engine.compute_permissions(trial_actor)

        result = engine.authorize(actor, "policies", "write")
        assert result.allowed is False

    def test_system_cannot_delete(self, engine, system_actor):
        """Test system actors cannot delete resources."""
        result = engine.authorize(system_actor, "runs", "delete")
        assert result.allowed is False
        assert "forbidden" in result.reason

    def test_system_cannot_admin(self, engine, system_actor):
        """Test system actors cannot perform admin actions."""
        result = engine.authorize(system_actor, "account", "admin")
        assert result.allowed is False


class TestWildcardMatching:
    """Tests for wildcard permission matching."""

    def test_global_wildcard_matches_all(self, engine):
        """Test * matches any permission."""
        actor = ActorContext(
            actor_id="founder-1",
            actor_type=ActorType.OPERATOR,
            source=IdentitySource.CLERK,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"*"}),
        )

        assert engine.authorize(actor, "anything", "everything").allowed is True
        assert engine.authorize(actor, "runs", "read").allowed is True
        assert engine.authorize(actor, "system", "admin").allowed is True

    def test_action_wildcard_matches_action(self, engine):
        """Test read:* matches any read action."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"read:*"}),
        )

        assert engine.authorize(actor, "runs", "read").allowed is True
        assert engine.authorize(actor, "agents", "read").allowed is True
        assert engine.authorize(actor, "anything", "read").allowed is True
        assert engine.authorize(actor, "runs", "write").allowed is False


class TestAuthorizationResult:
    """Tests for AuthorizationResult."""

    def test_result_is_frozen(self, engine, external_paid_actor):
        """Test AuthorizationResult is immutable."""
        actor = engine.compute_permissions(external_paid_actor)
        result = engine.authorize(actor, "runs", "read")

        with pytest.raises(Exception):
            result.allowed = False

    def test_result_repr(self, engine, external_paid_actor):
        """Test AuthorizationResult string representation."""
        actor = engine.compute_permissions(external_paid_actor)
        result = engine.authorize(actor, "runs", "read")

        repr_str = repr(result)
        assert "AuthResult" in repr_str
        assert "read:runs" in repr_str

    def test_raise_if_denied_allowed(self, engine, operator_actor):
        """Test raise_if_denied does nothing when allowed."""
        result = engine.authorize(operator_actor, "runs", "read")
        # Should not raise
        result.raise_if_denied()

    def test_raise_if_denied_denied(self, engine):
        """Test raise_if_denied raises HTTPException when denied."""
        from fastapi import HTTPException

        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset(),
        )

        result = engine.authorize(actor, "runs", "delete")

        with pytest.raises(HTTPException) as exc_info:
            result.raise_if_denied()

        assert exc_info.value.status_code == 403


class TestSingletonAndConvenience:
    """Tests for singleton and convenience functions."""

    def test_get_authorization_engine_singleton(self):
        """Test get_authorization_engine returns same instance."""
        engine1 = get_authorization_engine()
        engine2 = get_authorization_engine()

        assert engine1 is engine2

    def test_authorize_convenience_function(self, operator_actor):
        """Test authorize() convenience function."""
        result = authorize(operator_actor, "runs", "read")

        assert result.allowed is True
        assert isinstance(result, AuthorizationResult)
