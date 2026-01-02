# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Unit tests for ActorContext (L6)
# Reference: PIN-271 (RBAC Authority Separation)

"""
Unit tests for ActorContext and related functions.

Tests cover:
- ActorContext creation and immutability
- ActorType classification
- Permission matching with wildcards
- System actor presets
- Factory functions
"""

import pytest

from app.auth.actor import (
    SYSTEM_ACTORS,
    ActorContext,
    ActorType,
    IdentitySource,
    create_external_actor,
    create_operator_actor,
    get_system_actor,
)


class TestActorContext:
    """Tests for ActorContext dataclass."""

    def test_create_basic_actor(self):
        """Test basic actor creation."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id="acct-xyz",
            team_id="team-1",
            roles=frozenset({"admin", "developer"}),
            permissions=frozenset({"read:*", "write:runs"}),
        )

        assert actor.actor_id == "user-123"
        assert actor.actor_type == ActorType.EXTERNAL_PAID
        assert actor.source == IdentitySource.CLERK
        assert actor.tenant_id == "tenant-abc"
        assert actor.account_id == "acct-xyz"
        assert actor.team_id == "team-1"
        assert "admin" in actor.roles
        assert "developer" in actor.roles

    def test_actor_is_frozen(self):
        """Test that ActorContext is immutable."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset({"admin"}),
            permissions=frozenset(),
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            actor.actor_id = "user-456"

    def test_has_role(self):
        """Test role checking."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset({"admin", "developer"}),
            permissions=frozenset(),
        )

        assert actor.has_role("admin") is True
        assert actor.has_role("developer") is True
        assert actor.has_role("founder") is False

    def test_has_permission_exact_match(self):
        """Test exact permission matching."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset({"read:runs", "write:agents"}),
        )

        assert actor.has_permission("read:runs") is True
        assert actor.has_permission("write:agents") is True
        assert actor.has_permission("delete:runs") is False

    def test_has_permission_global_wildcard(self):
        """Test global wildcard permission."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.OPERATOR,
            source=IdentitySource.CLERK,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset({"founder"}),
            permissions=frozenset({"*"}),
        )

        assert actor.has_permission("read:runs") is True
        assert actor.has_permission("write:anything") is True
        assert actor.has_permission("delete:everything") is True

    def test_has_permission_action_wildcard(self):
        """Test action wildcard (read:*)."""
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

        assert actor.has_permission("read:runs") is True
        assert actor.has_permission("read:agents") is True
        assert actor.has_permission("read:anything") is True
        assert actor.has_permission("write:runs") is False

    def test_is_operator(self):
        """Test operator check."""
        operator = ActorContext(
            actor_id="founder-1",
            actor_type=ActorType.OPERATOR,
            source=IdentitySource.CLERK,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset({"founder"}),
            permissions=frozenset({"*"}),
        )

        user = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset({"admin"}),
            permissions=frozenset(),
        )

        assert operator.is_operator() is True
        assert user.is_operator() is False

    def test_is_system(self):
        """Test system actor check."""
        system = ActorContext(
            actor_id="system:ci",
            actor_type=ActorType.SYSTEM,
            source=IdentitySource.SYSTEM,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset({"ci"}),
            permissions=frozenset(),
        )

        user = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset(),
        )

        assert system.is_system() is True
        assert user.is_system() is False

    def test_tenant_scoped(self):
        """Test tenant scope checks."""
        scoped = ActorContext(
            actor_id="user-123",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset(),
        )

        unscoped = ActorContext(
            actor_id="system:ci",
            actor_type=ActorType.SYSTEM,
            source=IdentitySource.SYSTEM,
            tenant_id=None,
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset(),
        )

        assert scoped.is_tenant_scoped() is True
        assert unscoped.is_tenant_scoped() is False

    def test_same_tenant(self):
        """Test same tenant comparison."""
        actor1 = ActorContext(
            actor_id="user-1",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset(),
        )

        actor2 = ActorContext(
            actor_id="user-2",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-abc",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset(),
        )

        actor3 = ActorContext(
            actor_id="user-3",
            actor_type=ActorType.EXTERNAL_PAID,
            source=IdentitySource.CLERK,
            tenant_id="tenant-xyz",
            account_id=None,
            team_id=None,
            roles=frozenset(),
            permissions=frozenset(),
        )

        assert actor1.same_tenant(actor2) is True
        assert actor1.same_tenant(actor3) is False


class TestSystemActors:
    """Tests for predefined system actors."""

    def test_ci_actor_exists(self):
        """Test CI actor is defined."""
        ci = SYSTEM_ACTORS.get("ci")
        assert ci is not None
        assert ci.actor_id == "system:ci"
        assert ci.actor_type == ActorType.SYSTEM
        assert ci.source == IdentitySource.SYSTEM
        assert "ci" in ci.roles

    def test_worker_actor_exists(self):
        """Test worker actor is defined."""
        worker = SYSTEM_ACTORS.get("worker")
        assert worker is not None
        assert worker.actor_id == "system:worker"
        assert worker.actor_type == ActorType.SYSTEM
        assert "worker" in worker.roles

    def test_replay_actor_exists(self):
        """Test replay actor is defined."""
        replay = SYSTEM_ACTORS.get("replay")
        assert replay is not None
        assert replay.actor_id == "system:replay"
        assert "replay" in replay.roles

    def test_get_system_actor(self):
        """Test get_system_actor helper."""
        ci = get_system_actor("ci")
        assert ci is not None
        assert ci.actor_id == "system:ci"

        unknown = get_system_actor("unknown")
        assert unknown is None

    def test_system_actors_have_no_tenant(self):
        """Test system actors are not tenant-scoped."""
        for name, actor in SYSTEM_ACTORS.items():
            assert actor.tenant_id is None, f"{name} should not have tenant"
            assert actor.account_id is None, f"{name} should not have account"


class TestFactoryFunctions:
    """Tests for actor factory functions."""

    def test_create_operator_actor(self):
        """Test operator actor creation."""
        actor = create_operator_actor(
            actor_id="founder-1",
            email="founder@example.com",
            display_name="Founder One",
        )

        assert actor.actor_type == ActorType.OPERATOR
        assert actor.source == IdentitySource.CLERK
        assert actor.tenant_id is None
        assert "founder" in actor.roles
        assert "*" in actor.permissions
        assert actor.email == "founder@example.com"

    def test_create_external_actor_paid(self):
        """Test paid external actor creation."""
        actor = create_external_actor(
            actor_id="user-123",
            tenant_id="tenant-abc",
            account_id="acct-xyz",
            team_id="team-1",
            roles=frozenset({"admin"}),
            is_paid=True,
        )

        assert actor.actor_type == ActorType.EXTERNAL_PAID
        assert actor.tenant_id == "tenant-abc"
        assert actor.account_id == "acct-xyz"
        assert actor.team_id == "team-1"
        assert "admin" in actor.roles
        # Permissions should be empty (computed by engine)
        assert len(actor.permissions) == 0

    def test_create_external_actor_trial(self):
        """Test trial external actor creation."""
        actor = create_external_actor(
            actor_id="user-456",
            tenant_id="tenant-trial",
            account_id=None,
            team_id=None,
            roles=frozenset({"viewer"}),
            is_paid=False,
        )

        assert actor.actor_type == ActorType.EXTERNAL_TRIAL
        assert actor.tenant_id == "tenant-trial"
        assert "viewer" in actor.roles


class TestActorType:
    """Tests for ActorType enum."""

    def test_all_types_exist(self):
        """Test all expected actor types exist."""
        assert ActorType.EXTERNAL_PAID.value == "external_paid"
        assert ActorType.EXTERNAL_TRIAL.value == "external_trial"
        assert ActorType.INTERNAL_PRODUCT.value == "internal_product"
        assert ActorType.OPERATOR.value == "operator"
        assert ActorType.SYSTEM.value == "system"

    def test_actor_type_is_string(self):
        """Test ActorType values are strings (for serialization)."""
        for actor_type in ActorType:
            assert isinstance(actor_type.value, str)


class TestIdentitySource:
    """Tests for IdentitySource enum."""

    def test_all_sources_exist(self):
        """Test all expected identity sources exist."""
        assert IdentitySource.CLERK.value == "clerk"
        assert IdentitySource.OIDC.value == "oidc"
        assert IdentitySource.INTERNAL.value == "internal"
        assert IdentitySource.SYSTEM.value == "system"
        assert IdentitySource.DEV.value == "dev"
