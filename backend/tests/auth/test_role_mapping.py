"""
Unit Tests for Role Mapping - M7-M28 RBAC Integration (PIN-169)

Tests the one-way role mapping from M28 Console roles to M7 RBAC roles.

INVARIANTS TESTED:
1. Mapping is ONE-WAY only (M28 → M7)
2. No bidirectional leakage possible
3. Founder roles are isolated
4. Unknown roles default safely

Created: 2025-12-25
"""

import pytest

from app.auth.role_mapping import (
    CUSTOMER_TO_RBAC,
    FOUNDER_TO_RBAC,
    AuthContext,
    CustomerRole,
    FounderIsolationError,
    FounderRole,
    Principal,
    PrincipalType,
    RBACRole,
    build_auth_context,
    get_role_hierarchy,
    guard_founder_isolation,
    map_console_role_string,
    map_customer_role_to_rbac,
    map_founder_role_to_rbac,
    role_subsumes,
)

# ============================================================================
# Test: One-Way Mapping (M28 → M7)
# ============================================================================


class TestOneWayMapping:
    """Tests for one-way role mapping invariant."""

    def test_customer_owner_maps_to_admin(self):
        """OWNER should map to admin role."""
        result = map_customer_role_to_rbac(CustomerRole.OWNER)
        assert result == RBACRole.ADMIN

    def test_customer_admin_maps_to_infra(self):
        """ADMIN should map to infra role."""
        result = map_customer_role_to_rbac(CustomerRole.ADMIN)
        assert result == RBACRole.INFRA

    def test_customer_dev_maps_to_dev(self):
        """DEV should map to dev role."""
        result = map_customer_role_to_rbac(CustomerRole.DEV)
        assert result == RBACRole.DEV

    def test_customer_viewer_maps_to_readonly(self):
        """VIEWER should map to readonly role."""
        result = map_customer_role_to_rbac(CustomerRole.VIEWER)
        assert result == RBACRole.READONLY

    def test_founder_maps_to_founder(self):
        """FOUNDER should map to founder role."""
        result = map_founder_role_to_rbac(FounderRole.FOUNDER)
        assert result == RBACRole.FOUNDER

    def test_operator_maps_to_operator(self):
        """OPERATOR should map to operator role."""
        result = map_founder_role_to_rbac(FounderRole.OPERATOR)
        assert result == RBACRole.OPERATOR

    def test_all_customer_roles_are_mapped(self):
        """All customer roles must have a mapping."""
        for role in CustomerRole:
            result = map_customer_role_to_rbac(role)
            assert result is not None
            assert isinstance(result, RBACRole)

    def test_all_founder_roles_are_mapped(self):
        """All founder roles must have a mapping."""
        for role in FounderRole:
            result = map_founder_role_to_rbac(role)
            assert result is not None
            assert isinstance(result, RBACRole)


class TestNoBidirectionalLeakage:
    """Tests to ensure no reverse mapping is possible."""

    def test_no_rbac_to_customer_mapping_exists(self):
        """There should be no RBAC → Customer mapping."""
        # Verify no such mapping exists in the module
        import app.auth.role_mapping as rm

        assert not hasattr(rm, "RBAC_TO_CUSTOMER")

    def test_no_rbac_to_founder_mapping_exists(self):
        """There should be no RBAC → Founder mapping."""
        import app.auth.role_mapping as rm

        assert not hasattr(rm, "RBAC_TO_FOUNDER")

    def test_mapping_returns_single_role_not_list(self):
        """Mapping should return a single role, not a list."""
        result = map_customer_role_to_rbac(CustomerRole.OWNER)
        assert isinstance(result, RBACRole)
        assert not isinstance(result, list)


# ============================================================================
# Test: Founder Isolation
# ============================================================================


class TestFounderIsolation:
    """Tests for founder isolation guard."""

    def test_founder_with_no_tenant_passes(self):
        """Founder context without tenant_id should pass."""
        ctx = AuthContext(
            principal_id="founder_123",
            principal_type=PrincipalType.FOPS,
            tenant_id=None,
            effective_roles=[RBACRole.FOUNDER],
        )
        # Should not raise
        guard_founder_isolation(ctx)

    def test_founder_with_tenant_fails(self):
        """Founder context WITH tenant_id should fail."""
        ctx = AuthContext(
            principal_id="founder_123",
            principal_type=PrincipalType.FOPS,
            tenant_id="tenant_456",  # VIOLATION
            effective_roles=[RBACRole.FOUNDER],
        )
        with pytest.raises(FounderIsolationError) as exc_info:
            guard_founder_isolation(ctx)

        assert "SECURITY" in str(exc_info.value)
        assert "founder_123" in str(exc_info.value)
        assert "tenant_456" in str(exc_info.value)

    def test_console_user_with_tenant_passes(self):
        """Console user WITH tenant_id should pass (expected behavior)."""
        ctx = AuthContext(
            principal_id="user_123",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_456",
            effective_roles=[RBACRole.ADMIN],
        )
        # Should not raise - console users are supposed to have tenant_id
        guard_founder_isolation(ctx)

    def test_machine_with_tenant_passes(self):
        """Machine principal WITH tenant_id should pass."""
        ctx = AuthContext(
            principal_id="machine_key_abc",
            principal_type=PrincipalType.MACHINE,
            tenant_id="tenant_456",
            effective_roles=[RBACRole.MACHINE],
        )
        # Should not raise
        guard_founder_isolation(ctx)


# ============================================================================
# Test: String Mapping (from raw role strings)
# ============================================================================


class TestStringMapping:
    """Tests for string-based role mapping."""

    def test_customer_role_string_mapping(self):
        """Customer role strings should map correctly."""
        assert map_console_role_string("OWNER", is_founder=False) == RBACRole.ADMIN
        assert map_console_role_string("ADMIN", is_founder=False) == RBACRole.INFRA
        assert map_console_role_string("DEV", is_founder=False) == RBACRole.DEV
        assert map_console_role_string("VIEWER", is_founder=False) == RBACRole.READONLY

    def test_founder_role_string_mapping(self):
        """Founder role strings should map correctly."""
        assert map_console_role_string("FOUNDER", is_founder=True) == RBACRole.FOUNDER
        assert map_console_role_string("OPERATOR", is_founder=True) == RBACRole.OPERATOR

    def test_invalid_customer_role_defaults_to_readonly(self):
        """Invalid customer role should default to readonly."""
        result = map_console_role_string("INVALID_ROLE", is_founder=False)
        assert result == RBACRole.READONLY

    def test_invalid_founder_role_defaults_to_operator(self):
        """Invalid founder role should default to operator."""
        result = map_console_role_string("INVALID_ROLE", is_founder=True)
        assert result == RBACRole.OPERATOR


# ============================================================================
# Test: Principal Model
# ============================================================================


class TestPrincipalModel:
    """Tests for Principal dataclass."""

    def test_principal_creation(self):
        """Principal should be created with all fields."""
        principal = Principal(
            principal_id="user_123",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_456",
            source_token_type="jwt",
        )
        assert principal.principal_id == "user_123"
        assert principal.principal_type == PrincipalType.CONSOLE
        assert principal.tenant_id == "tenant_456"
        assert principal.source_token_type == "jwt"

    def test_principal_without_tenant(self):
        """Principal can be created without tenant_id."""
        principal = Principal(
            principal_id="founder_123",
            principal_type=PrincipalType.FOPS,
            source_token_type="jwt",
        )
        assert principal.tenant_id is None


# ============================================================================
# Test: AuthContext Model
# ============================================================================


class TestAuthContextModel:
    """Tests for AuthContext dataclass."""

    def test_auth_context_creation(self):
        """AuthContext should be created with all fields."""
        ctx = AuthContext(
            principal_id="user_123",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_456",
            effective_roles=[RBACRole.ADMIN],
            source_token_type="jwt",
            original_console_role="OWNER",
            mapping_source="console_auth",
        )
        assert ctx.principal_id == "user_123"
        assert ctx.effective_roles == [RBACRole.ADMIN]
        assert ctx.original_console_role == "OWNER"

    def test_is_founder(self):
        """is_founder() should return True for FOPS principal."""
        ctx = AuthContext(
            principal_id="founder_123",
            principal_type=PrincipalType.FOPS,
            tenant_id=None,
            effective_roles=[RBACRole.FOUNDER],
        )
        assert ctx.is_founder() is True

        ctx2 = AuthContext(
            principal_id="user_123",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_456",
            effective_roles=[RBACRole.ADMIN],
        )
        assert ctx2.is_founder() is False

    def test_is_tenant_scoped(self):
        """is_tenant_scoped() should return True when tenant_id is set."""
        ctx = AuthContext(
            principal_id="user_123",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_456",
            effective_roles=[RBACRole.ADMIN],
        )
        assert ctx.is_tenant_scoped() is True

        ctx2 = AuthContext(
            principal_id="founder_123",
            principal_type=PrincipalType.FOPS,
            tenant_id=None,
            effective_roles=[RBACRole.FOUNDER],
        )
        assert ctx2.is_tenant_scoped() is False

    def test_has_role(self):
        """has_role() should check if role is in effective_roles."""
        ctx = AuthContext(
            principal_id="user_123",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_456",
            effective_roles=[RBACRole.ADMIN, RBACRole.DEV],
        )
        assert ctx.has_role(RBACRole.ADMIN) is True
        assert ctx.has_role(RBACRole.DEV) is True
        assert ctx.has_role(RBACRole.FOUNDER) is False


# ============================================================================
# Test: Role Hierarchy
# ============================================================================


class TestRoleHierarchy:
    """Tests for role hierarchy and subsumption."""

    def test_founder_is_highest(self):
        """Founder should be the highest role."""
        hierarchy = get_role_hierarchy()
        assert hierarchy[RBACRole.FOUNDER] == max(hierarchy.values())

    def test_readonly_is_lowest(self):
        """Readonly should be the lowest role."""
        hierarchy = get_role_hierarchy()
        assert hierarchy[RBACRole.READONLY] == min(hierarchy.values())

    def test_founder_subsumes_all(self):
        """Founder should subsume all other roles."""
        for role in RBACRole:
            assert role_subsumes(RBACRole.FOUNDER, role) is True

    def test_readonly_subsumes_only_itself(self):
        """Readonly should only subsume itself."""
        assert role_subsumes(RBACRole.READONLY, RBACRole.READONLY) is True
        assert role_subsumes(RBACRole.READONLY, RBACRole.DEV) is False
        assert role_subsumes(RBACRole.READONLY, RBACRole.ADMIN) is False

    def test_admin_subsumes_dev_and_readonly(self):
        """Admin should subsume dev and readonly."""
        assert role_subsumes(RBACRole.ADMIN, RBACRole.DEV) is True
        assert role_subsumes(RBACRole.ADMIN, RBACRole.READONLY) is True
        assert role_subsumes(RBACRole.ADMIN, RBACRole.FOUNDER) is False


# ============================================================================
# Test: Mapping Completeness
# ============================================================================


class TestMappingCompleteness:
    """Tests for mapping completeness."""

    def test_customer_mapping_covers_all_roles(self):
        """CUSTOMER_TO_RBAC should cover all CustomerRole values."""
        for role in CustomerRole:
            assert role in CUSTOMER_TO_RBAC

    def test_founder_mapping_covers_all_roles(self):
        """FOUNDER_TO_RBAC should cover all FounderRole values."""
        for role in FounderRole:
            assert role in FOUNDER_TO_RBAC

    def test_all_mapped_roles_are_valid_rbac_roles(self):
        """All mapped roles should be valid RBACRole values."""
        for rbac_role in CUSTOMER_TO_RBAC.values():
            assert isinstance(rbac_role, RBACRole)

        for rbac_role in FOUNDER_TO_RBAC.values():
            assert isinstance(rbac_role, RBACRole)


# ============================================================================
# Test: Security Edge Cases
# ============================================================================


class TestSecurityEdgeCases:
    """Tests for security edge cases."""

    def test_case_sensitivity_in_string_mapping(self):
        """Role string mapping should be case-sensitive."""
        # Valid uppercase
        assert map_console_role_string("OWNER", is_founder=False) == RBACRole.ADMIN

        # Lowercase should fail (defaults to readonly)
        assert map_console_role_string("owner", is_founder=False) == RBACRole.READONLY

    def test_empty_string_role(self):
        """Empty string should default safely."""
        assert map_console_role_string("", is_founder=False) == RBACRole.READONLY
        assert map_console_role_string("", is_founder=True) == RBACRole.OPERATOR

    def test_none_like_strings(self):
        """None-like strings should default safely."""
        assert map_console_role_string("null", is_founder=False) == RBACRole.READONLY
        assert map_console_role_string("None", is_founder=False) == RBACRole.READONLY
        assert map_console_role_string("undefined", is_founder=False) == RBACRole.READONLY

    def test_sql_injection_strings(self):
        """SQL injection-like strings should default safely."""
        assert map_console_role_string("'; DROP TABLE users;--", is_founder=False) == RBACRole.READONLY
        assert map_console_role_string("OWNER' OR '1'='1", is_founder=False) == RBACRole.READONLY


# ============================================================================
# Test: build_auth_context Function
# ============================================================================


class TestBuildAuthContext:
    """Tests for the build_auth_context function."""

    def test_build_console_context_owner(self):
        """Building context for console OWNER should work."""
        ctx = build_auth_context(
            principal_id="user_123",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_456",
            console_role="OWNER",
            source_token_type="jwt",
            mapping_source="console_auth",
        )
        assert ctx.principal_id == "user_123"
        assert ctx.principal_type == PrincipalType.CONSOLE
        assert ctx.tenant_id == "tenant_456"
        assert ctx.effective_roles == [RBACRole.ADMIN]
        assert ctx.original_console_role == "OWNER"

    def test_build_console_context_dev(self):
        """Building context for console DEV should work."""
        ctx = build_auth_context(
            principal_id="user_dev",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_789",
            console_role="DEV",
        )
        assert ctx.effective_roles == [RBACRole.DEV]

    def test_build_founder_context(self):
        """Building context for founder should work."""
        ctx = build_auth_context(
            principal_id="founder_001",
            principal_type=PrincipalType.FOPS,
            tenant_id=None,  # Founders have no tenant
            console_role="FOUNDER",
        )
        assert ctx.principal_type == PrincipalType.FOPS
        assert ctx.tenant_id is None
        assert ctx.effective_roles == [RBACRole.FOUNDER]

    def test_build_founder_context_fails_with_tenant(self):
        """Building founder context WITH tenant_id should fail."""
        with pytest.raises(FounderIsolationError):
            build_auth_context(
                principal_id="founder_001",
                principal_type=PrincipalType.FOPS,
                tenant_id="tenant_456",  # VIOLATION
                console_role="FOUNDER",
            )

    def test_build_machine_context(self):
        """Building context for machine token should work."""
        ctx = build_auth_context(
            principal_id="key_fingerprint_abc",
            principal_type=PrincipalType.MACHINE,
            tenant_id="tenant_123",
            source_token_type="api_key",
        )
        assert ctx.principal_type == PrincipalType.MACHINE
        assert ctx.effective_roles == [RBACRole.MACHINE]

    def test_build_anonymous_context(self):
        """Building context for anonymous should default to readonly."""
        ctx = build_auth_context(
            principal_id="anonymous",
            principal_type=PrincipalType.ANONYMOUS,
        )
        assert ctx.effective_roles == [RBACRole.READONLY]

    def test_build_context_without_role_defaults_safely(self):
        """Building context without role should default safely."""
        ctx = build_auth_context(
            principal_id="user_norol",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_123",
            # No console_role provided
        )
        assert ctx.effective_roles == [RBACRole.READONLY]

    def test_build_context_invalid_role_defaults_safely(self):
        """Building context with invalid role should default safely."""
        ctx = build_auth_context(
            principal_id="user_bad",
            principal_type=PrincipalType.CONSOLE,
            tenant_id="tenant_123",
            console_role="SUPER_ADMIN",  # Invalid role
        )
        assert ctx.effective_roles == [RBACRole.READONLY]
