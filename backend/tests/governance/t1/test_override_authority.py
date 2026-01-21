# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-034 (Override Authority Integration)
"""
Unit tests for GAP-034: Override Authority Integration.

Tests the override authority checker that integrates OverrideAuthority
model with the prevention engine.

CRITICAL TEST COVERAGE:
- OverrideAuthorityChecker imports and initializes
- Override status correctly determined
- skip_enforcement flag set correctly
- Integration with OverrideAuthority model
- Expired overrides detected correctly
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestOverrideAuthorityImports:
    """Test override authority module imports."""

    def test_checker_import(self):
        """OverrideAuthorityChecker should be importable."""
        from app.services.override import OverrideAuthorityChecker

        assert OverrideAuthorityChecker is not None

    def test_status_import(self):
        """OverrideStatus should be importable."""
        from app.services.override import OverrideStatus

        assert OverrideStatus.NO_OVERRIDE is not None

    def test_result_import(self):
        """OverrideCheckResult should be importable."""
        from app.services.override import OverrideCheckResult

        assert OverrideCheckResult is not None

    def test_helper_import(self):
        """should_skip_enforcement helper should be importable."""
        from app.services.override import should_skip_enforcement

        assert should_skip_enforcement is not None


class TestOverrideStatus:
    """Test OverrideStatus enum."""

    def test_all_statuses_defined(self):
        """All required statuses should be defined."""
        from app.services.override import OverrideStatus

        assert OverrideStatus.NO_OVERRIDE is not None
        assert OverrideStatus.OVERRIDE_ACTIVE is not None
        assert OverrideStatus.OVERRIDE_EXPIRED is not None
        assert OverrideStatus.OVERRIDE_NOT_ALLOWED is not None

    def test_status_values(self):
        """Status values should be strings."""
        from app.services.override import OverrideStatus

        assert OverrideStatus.NO_OVERRIDE.value == "no_override"
        assert OverrideStatus.OVERRIDE_ACTIVE.value == "override_active"
        assert OverrideStatus.OVERRIDE_EXPIRED.value == "override_expired"
        assert OverrideStatus.OVERRIDE_NOT_ALLOWED.value == "override_not_allowed"


class TestOverrideCheckResult:
    """Test OverrideCheckResult dataclass."""

    def test_result_creation(self):
        """Should create result with all fields."""
        from app.services.override import OverrideCheckResult, OverrideStatus

        result = OverrideCheckResult(
            status=OverrideStatus.OVERRIDE_ACTIVE,
            skip_enforcement=True,
            policy_id="pol-001",
            override_by="user-001",
            override_reason="Emergency fix",
        )

        assert result.status == OverrideStatus.OVERRIDE_ACTIVE
        assert result.skip_enforcement is True
        assert result.policy_id == "pol-001"
        assert result.override_by == "user-001"
        assert result.override_reason == "Emergency fix"

    def test_result_to_dict(self):
        """to_dict should return API-ready format."""
        from app.services.override import OverrideCheckResult, OverrideStatus

        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=15)

        result = OverrideCheckResult(
            status=OverrideStatus.OVERRIDE_ACTIVE,
            skip_enforcement=True,
            policy_id="pol-001",
            override_by="user-001",
            override_reason="Test",
            override_started_at=now,
            override_expires_at=expires,
            remaining_seconds=900,
        )

        d = result.to_dict()

        assert d["status"] == "override_active"
        assert d["skip_enforcement"] is True
        assert d["policy_id"] == "pol-001"
        assert d["override_by"] == "user-001"
        assert d["override_started_at"] is not None
        assert d["override_expires_at"] is not None
        assert d["remaining_seconds"] == 900

    def test_result_to_dict_handles_none(self):
        """to_dict should handle None datetime fields."""
        from app.services.override import OverrideCheckResult, OverrideStatus

        result = OverrideCheckResult(
            status=OverrideStatus.NO_OVERRIDE,
            skip_enforcement=False,
            policy_id="pol-001",
        )

        d = result.to_dict()

        assert d["override_started_at"] is None
        assert d["override_expires_at"] is None


class TestOverrideAuthorityChecker:
    """Test OverrideAuthorityChecker class."""

    def test_check_none_returns_no_override(self):
        """check(None) should return NO_OVERRIDE status."""
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(None)

        assert result.status == OverrideStatus.NO_OVERRIDE
        assert result.skip_enforcement is False

    def test_check_not_overridden_returns_no_override(self):
        """Check authority with no active override should return NO_OVERRIDE."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=False,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        assert result.status == OverrideStatus.NO_OVERRIDE
        assert result.skip_enforcement is False
        assert result.policy_id == "pol-001"

    def test_check_active_override_returns_active(self):
        """Check authority with active override should return OVERRIDE_ACTIVE."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        now = datetime.now(timezone.utc)
        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=True,
            override_started_at=now,
            override_expires_at=now + timedelta(minutes=15),
            override_by="user-001",
            override_reason="Emergency fix",
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        assert result.status == OverrideStatus.OVERRIDE_ACTIVE
        assert result.skip_enforcement is True
        assert result.policy_id == "pol-001"
        assert result.override_by == "user-001"
        assert result.override_reason == "Emergency fix"
        assert result.remaining_seconds is not None
        assert result.remaining_seconds > 0

    def test_check_expired_override_returns_expired(self):
        """Check authority with expired override should return OVERRIDE_EXPIRED."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        past = datetime.now(timezone.utc) - timedelta(hours=1)
        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=True,
            override_started_at=past - timedelta(minutes=15),
            override_expires_at=past,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        assert result.status == OverrideStatus.OVERRIDE_EXPIRED
        assert result.skip_enforcement is False

    def test_check_override_not_allowed(self):
        """Check authority with overrides disabled should return OVERRIDE_NOT_ALLOWED."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            override_allowed=False,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        assert result.status == OverrideStatus.OVERRIDE_NOT_ALLOWED
        assert result.skip_enforcement is False


class TestOverrideAuthorityCheckerFromDict:
    """Test check_from_dict method."""

    def test_check_from_dict_no_override(self):
        """check_from_dict with no override should return NO_OVERRIDE."""
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check_from_dict(
            policy_id="pol-001",
            currently_overridden=False,
        )

        assert result.status == OverrideStatus.NO_OVERRIDE
        assert result.skip_enforcement is False

    def test_check_from_dict_active_override(self):
        """check_from_dict with active override should return OVERRIDE_ACTIVE."""
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        now = datetime.now(timezone.utc)

        checker = OverrideAuthorityChecker()
        result = checker.check_from_dict(
            policy_id="pol-001",
            currently_overridden=True,
            override_by="user-001",
            override_reason="Test",
            override_started_at=now,
            override_expires_at=now + timedelta(minutes=15),
        )

        assert result.status == OverrideStatus.OVERRIDE_ACTIVE
        assert result.skip_enforcement is True
        assert result.override_by == "user-001"

    def test_check_from_dict_expired(self):
        """check_from_dict with expired override should return OVERRIDE_EXPIRED."""
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        past = datetime.now(timezone.utc) - timedelta(hours=1)

        checker = OverrideAuthorityChecker()
        result = checker.check_from_dict(
            policy_id="pol-001",
            currently_overridden=True,
            override_expires_at=past,
        )

        assert result.status == OverrideStatus.OVERRIDE_EXPIRED
        assert result.skip_enforcement is False

    def test_check_from_dict_no_expiry(self):
        """check_from_dict with no expiry should return OVERRIDE_EXPIRED."""
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check_from_dict(
            policy_id="pol-001",
            currently_overridden=True,
            override_expires_at=None,  # Missing expiry
        )

        assert result.status == OverrideStatus.OVERRIDE_EXPIRED
        assert result.skip_enforcement is False

    def test_check_from_dict_not_allowed(self):
        """check_from_dict with override not allowed should return OVERRIDE_NOT_ALLOWED."""
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check_from_dict(
            policy_id="pol-001",
            override_allowed=False,
        )

        assert result.status == OverrideStatus.OVERRIDE_NOT_ALLOWED
        assert result.skip_enforcement is False


class TestShouldSkipEnforcement:
    """Test should_skip_enforcement helper function."""

    def test_skip_with_none(self):
        """should_skip_enforcement(None) should return False."""
        from app.services.override import should_skip_enforcement

        result = should_skip_enforcement(None)

        assert result is False

    def test_skip_with_no_override(self):
        """should_skip_enforcement should return False with no override."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import should_skip_enforcement

        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=False,
        )

        result = should_skip_enforcement(authority)

        assert result is False

    def test_skip_with_active_override(self):
        """should_skip_enforcement should return True with active override."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import should_skip_enforcement

        now = datetime.now(timezone.utc)
        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=True,
            override_expires_at=now + timedelta(minutes=15),
        )

        result = should_skip_enforcement(authority)

        assert result is True

    def test_skip_with_expired_override(self):
        """should_skip_enforcement should return False with expired override."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import should_skip_enforcement

        past = datetime.now(timezone.utc) - timedelta(hours=1)
        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=True,
            override_expires_at=past,
        )

        result = should_skip_enforcement(authority)

        assert result is False


class TestOverrideAuthorityUseCases:
    """Test realistic use cases for override authority."""

    def test_prevention_engine_flow_no_override(self):
        """Simulate prevention engine with no override active."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        # Policy with no active override
        authority = OverrideAuthority(
            policy_id="pol-budget-001",
            tenant_id="tenant-001",
            currently_overridden=False,
            override_allowed=True,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        # Prevention engine should enforce policy
        assert result.status == OverrideStatus.NO_OVERRIDE
        assert result.skip_enforcement is False
        # Enforcement proceeds...

    def test_prevention_engine_flow_with_override(self):
        """Simulate prevention engine with active override."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        now = datetime.now(timezone.utc)

        # Policy with active emergency override
        authority = OverrideAuthority(
            policy_id="pol-budget-001",
            tenant_id="tenant-001",
            currently_overridden=True,
            override_started_at=now,
            override_expires_at=now + timedelta(minutes=15),
            override_by="security-admin-001",
            override_reason="Emergency: production incident, need to allow higher budget",
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        # Prevention engine should skip enforcement
        assert result.status == OverrideStatus.OVERRIDE_ACTIVE
        assert result.skip_enforcement is True
        assert result.override_reason == "Emergency: production incident, need to allow higher budget"
        # Enforcement skipped, log the override

    def test_critical_policy_no_override_allowed(self):
        """Critical policy that doesn't allow overrides."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        # Security-critical policy that cannot be overridden
        authority = OverrideAuthority(
            policy_id="pol-security-critical-001",
            tenant_id="tenant-001",
            override_allowed=False,
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        # Prevention engine must enforce regardless
        assert result.status == OverrideStatus.OVERRIDE_NOT_ALLOWED
        assert result.skip_enforcement is False

    def test_override_just_expired(self):
        """Override that has just expired."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import (
            OverrideAuthorityChecker,
            OverrideStatus,
        )

        # Override expired 1 second ago
        expired = datetime.now(timezone.utc) - timedelta(seconds=1)

        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=True,
            override_started_at=expired - timedelta(minutes=15),
            override_expires_at=expired,
            override_by="user-001",
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        # Should detect as expired, resume enforcement
        assert result.status == OverrideStatus.OVERRIDE_EXPIRED
        assert result.skip_enforcement is False

    def test_remaining_seconds_calculation(self):
        """Check remaining seconds is calculated correctly."""
        from app.models.override_authority import OverrideAuthority
        from app.services.override import OverrideAuthorityChecker

        now = datetime.now(timezone.utc)

        # 5 minutes remaining
        authority = OverrideAuthority(
            policy_id="pol-001",
            tenant_id="tenant-001",
            currently_overridden=True,
            override_expires_at=now + timedelta(minutes=5),
        )

        checker = OverrideAuthorityChecker()
        result = checker.check(authority)

        # Should have approximately 300 seconds remaining
        assert result.remaining_seconds is not None
        assert 290 <= result.remaining_seconds <= 310
