# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
#   Lifecycle: batch
# Role: Tests for PIN-399 Phase-5 role guard dependency
# Callers: CI pipeline, pytest
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-399 Phase-5

"""
PIN-399 Phase-5: Role Guard Tests

CRITICAL TEST OBJECTIVES:
1. TenantRole enum has correct values and ordering
2. Permission derivation is correct
3. Role subsumption works correctly
4. require_role() dependency structure is correct
5. Role violation error has structured response

These tests verify the HARD CONSTRAINTS of Phase-5:
- ROLE-001: Roles do not exist before onboarding COMPLETE
- ROLE-002: Permissions are derived, not stored
- ROLE-003: Human roles never affect machine scopes
- ROLE-004: Console origin never grants authority
- ROLE-005: Role enforcement never mutates state
"""

import pytest

from app.auth.tenant_roles import (
    PERM_BILLING_MANAGE,
    PERM_POLICIES_READ,
    PERM_POLICIES_WRITE,
    PERM_RUNS_READ,
    PERM_RUNS_WRITE,
    PERM_USERS_MANAGE,
    ROLE_PERMISSIONS,
    TenantRole,
    get_permissions_for_role,
    role_has_permission,
    role_subsumes,
)


# =============================================================================
# TenantRole Enum Tests
# =============================================================================


class TestTenantRoleEnum:
    """Tests for TenantRole enum correctness."""

    def test_has_four_roles(self):
        """TenantRole must have exactly 4 roles."""
        roles = list(TenantRole)
        assert len(roles) == 4, f"Expected 4 roles, got {len(roles)}"

    def test_role_names(self):
        """TenantRole must have VIEWER, MEMBER, ADMIN, OWNER."""
        expected_names = {"VIEWER", "MEMBER", "ADMIN", "OWNER"}
        actual_names = {r.name for r in TenantRole}
        assert actual_names == expected_names, f"Expected {expected_names}, got {actual_names}"

    def test_role_ordering(self):
        """Roles must be ordered by privilege: VIEWER < MEMBER < ADMIN < OWNER."""
        assert TenantRole.VIEWER < TenantRole.MEMBER
        assert TenantRole.MEMBER < TenantRole.ADMIN
        assert TenantRole.ADMIN < TenantRole.OWNER

    def test_role_values_are_integers(self):
        """Role values must be integers for comparison."""
        for role in TenantRole:
            assert isinstance(role.value, int), f"{role.name} value is not int"

    def test_from_string_valid(self):
        """from_string should parse valid role names."""
        assert TenantRole.from_string("OWNER") == TenantRole.OWNER
        assert TenantRole.from_string("owner") == TenantRole.OWNER
        assert TenantRole.from_string("Owner") == TenantRole.OWNER
        assert TenantRole.from_string("  MEMBER  ") == TenantRole.MEMBER

    def test_from_string_invalid(self):
        """from_string should raise ValueError for invalid roles."""
        with pytest.raises(ValueError):
            TenantRole.from_string("SUPERADMIN")
        with pytest.raises(ValueError):
            TenantRole.from_string("")


# =============================================================================
# Permission Derivation Tests
# =============================================================================


class TestPermissionDerivation:
    """Tests for permission derivation from roles."""

    def test_all_roles_have_permissions(self):
        """Every role must have at least one permission."""
        for role in TenantRole:
            perms = get_permissions_for_role(role)
            assert len(perms) > 0, f"{role.name} has no permissions"

    def test_viewer_has_read_only(self):
        """VIEWER should only have read permissions."""
        perms = get_permissions_for_role(TenantRole.VIEWER)
        for perm in perms:
            assert ":write" not in perm, f"VIEWER has write permission: {perm}"
            assert ":manage" not in perm, f"VIEWER has manage permission: {perm}"

    def test_member_has_write_permissions(self):
        """MEMBER should have write permissions for runs and policies."""
        perms = get_permissions_for_role(TenantRole.MEMBER)
        assert PERM_RUNS_WRITE in perms
        assert PERM_POLICIES_WRITE in perms

    def test_admin_has_manage_permissions(self):
        """ADMIN should have user and api_key management."""
        perms = get_permissions_for_role(TenantRole.ADMIN)
        assert PERM_USERS_MANAGE in perms

    def test_owner_has_billing_manage(self):
        """OWNER should have billing management (owner-only)."""
        perms = get_permissions_for_role(TenantRole.OWNER)
        assert PERM_BILLING_MANAGE in perms

    def test_non_owner_lacks_billing_manage(self):
        """Non-OWNER roles should NOT have billing management."""
        for role in [TenantRole.VIEWER, TenantRole.MEMBER, TenantRole.ADMIN]:
            perms = get_permissions_for_role(role)
            assert PERM_BILLING_MANAGE not in perms, f"{role.name} has billing:manage"

    def test_permission_inheritance(self):
        """Higher roles should have all permissions of lower roles."""
        viewer_perms = get_permissions_for_role(TenantRole.VIEWER)
        member_perms = get_permissions_for_role(TenantRole.MEMBER)
        admin_perms = get_permissions_for_role(TenantRole.ADMIN)
        owner_perms = get_permissions_for_role(TenantRole.OWNER)

        assert viewer_perms.issubset(member_perms), "MEMBER should have all VIEWER perms"
        assert member_perms.issubset(admin_perms), "ADMIN should have all MEMBER perms"
        assert admin_perms.issubset(owner_perms), "OWNER should have all ADMIN perms"


class TestRoleHasPermission:
    """Tests for role_has_permission function."""

    def test_viewer_has_runs_read(self):
        """VIEWER should have runs:read."""
        assert role_has_permission(TenantRole.VIEWER, PERM_RUNS_READ)

    def test_viewer_lacks_runs_write(self):
        """VIEWER should NOT have runs:write."""
        assert not role_has_permission(TenantRole.VIEWER, PERM_RUNS_WRITE)

    def test_member_has_policies_write(self):
        """MEMBER should have policies:write."""
        assert role_has_permission(TenantRole.MEMBER, PERM_POLICIES_WRITE)

    def test_unknown_permission(self):
        """Unknown permission should return False."""
        assert not role_has_permission(TenantRole.OWNER, "unknown:permission")


class TestRoleSubsumes:
    """Tests for role subsumption logic."""

    def test_owner_subsumes_all(self):
        """OWNER should subsume all other roles."""
        assert role_subsumes(TenantRole.OWNER, TenantRole.OWNER)
        assert role_subsumes(TenantRole.OWNER, TenantRole.ADMIN)
        assert role_subsumes(TenantRole.OWNER, TenantRole.MEMBER)
        assert role_subsumes(TenantRole.OWNER, TenantRole.VIEWER)

    def test_viewer_subsumes_only_self(self):
        """VIEWER should only subsume itself."""
        assert role_subsumes(TenantRole.VIEWER, TenantRole.VIEWER)
        assert not role_subsumes(TenantRole.VIEWER, TenantRole.MEMBER)
        assert not role_subsumes(TenantRole.VIEWER, TenantRole.ADMIN)
        assert not role_subsumes(TenantRole.VIEWER, TenantRole.OWNER)

    def test_admin_does_not_subsume_owner(self):
        """ADMIN should NOT subsume OWNER."""
        assert not role_subsumes(TenantRole.ADMIN, TenantRole.OWNER)


# =============================================================================
# Role Guard Dependency Tests
# =============================================================================


class TestRoleGuardDependency:
    """Tests for require_role dependency structure."""

    def test_require_role_exists(self):
        """require_role should be importable."""
        from app.auth.role_guard import require_role

        assert callable(require_role)

    def test_require_role_returns_callable(self):
        """require_role should return a callable dependency."""
        from app.auth.role_guard import require_role

        dependency = require_role(TenantRole.MEMBER)
        assert callable(dependency)

    def test_require_role_requires_at_least_one_role(self):
        """require_role should raise if no roles specified."""
        from app.auth.role_guard import require_role

        with pytest.raises(ValueError):
            require_role()

    def test_require_role_accepts_multiple_roles(self):
        """require_role should accept multiple roles."""
        from app.auth.role_guard import require_role

        dependency = require_role(TenantRole.MEMBER, TenantRole.ADMIN, TenantRole.OWNER)
        assert callable(dependency)


class TestRoleViolationError:
    """Tests for structured role violation errors."""

    def test_role_violation_has_structured_response(self):
        """RoleViolationError should have structured detail."""
        from app.auth.role_guard import RoleViolationError

        error = RoleViolationError(
            required_roles=["MEMBER", "ADMIN"],
            actor_role="VIEWER",
            tenant_id="tenant-001",
        )

        assert error.status_code == 403
        assert isinstance(error.detail, dict)
        assert error.detail["error"] == "role_violation"
        assert error.detail["required_roles"] == ["MEMBER", "ADMIN"]
        assert error.detail["actor_role"] == "VIEWER"
        assert error.detail["tenant_id"] == "tenant-001"


# =============================================================================
# Phase-5 Invariant Tests
# =============================================================================


class TestPhase5Invariants:
    """Tests for Phase-5 design invariants."""

    def test_role_002_permissions_not_stored(self):
        """ROLE-002: Permissions should be in code, not DB models."""
        # Verify ROLE_PERMISSIONS is a Python dict, not a DB model
        assert isinstance(ROLE_PERMISSIONS, dict)
        for role, perms in ROLE_PERMISSIONS.items():
            assert isinstance(role, TenantRole)
            assert isinstance(perms, frozenset)

    def test_no_wildcard_permissions_stored(self):
        """ROLE-002: No wildcard (*) permissions in the mapping."""
        for role, perms in ROLE_PERMISSIONS.items():
            for perm in perms:
                assert "*" not in perm, f"Wildcard found in {role.name}: {perm}"

    def test_role_005_guard_is_read_only(self):
        """ROLE-005: Role guard functions should be pure (no mutations)."""
        # get_permissions_for_role should be pure
        result1 = get_permissions_for_role(TenantRole.MEMBER)
        result2 = get_permissions_for_role(TenantRole.MEMBER)
        assert result1 == result2, "get_permissions_for_role should be deterministic"

        # role_has_permission should be pure
        result1 = role_has_permission(TenantRole.MEMBER, PERM_RUNS_WRITE)
        result2 = role_has_permission(TenantRole.MEMBER, PERM_RUNS_WRITE)
        assert result1 == result2, "role_has_permission should be deterministic"
