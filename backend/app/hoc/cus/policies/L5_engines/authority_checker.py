# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: overrides (via driver)
#   Writes: none
# Role: Check override authority before policy enforcement
# Callers: policy/prevention_engine.py, services/enforcement/
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: PIN-470, GAP-034 (Override Authority Integration)
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure check logic

"""
Module: authority_checker
Purpose: Check override authority status for prevention engine.

The prevention engine must check override authority before enforcing
any policy actions. If an override is active, enforcement is skipped.

Integration Flow:
    1. Prevention engine receives policy ID
    2. Calls OverrideAuthorityChecker.check()
    3. If override is active, skip enforcement
    4. If no override, proceed with enforcement

Exports:
    - OverrideStatus: Enum of override states
    - OverrideCheckResult: Result of an override check
    - OverrideAuthorityChecker: Main integration class
    - should_skip_enforcement: Quick helper function
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class OverrideStatus(str, Enum):
    """Status of an override check."""

    NO_OVERRIDE = "no_override"  # No override configured or active
    OVERRIDE_ACTIVE = "override_active"  # Override is currently active
    OVERRIDE_EXPIRED = "override_expired"  # Override was active but has expired
    OVERRIDE_NOT_ALLOWED = "override_not_allowed"  # Overrides disabled for this policy


@dataclass
class OverrideCheckResult:
    """
    Result of an override authority check.

    Contains the status and metadata about any active override.
    """

    status: OverrideStatus
    skip_enforcement: bool  # True if prevention should skip enforcement
    policy_id: str
    override_by: Optional[str] = None  # User who initiated override
    override_reason: Optional[str] = None  # Reason for override
    override_started_at: Optional[datetime] = None
    override_expires_at: Optional[datetime] = None
    remaining_seconds: Optional[int] = None  # Seconds until override expires

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "status": self.status.value,
            "skip_enforcement": self.skip_enforcement,
            "policy_id": self.policy_id,
            "override_by": self.override_by,
            "override_reason": self.override_reason,
            "override_started_at": (
                self.override_started_at.isoformat() if self.override_started_at else None
            ),
            "override_expires_at": (
                self.override_expires_at.isoformat() if self.override_expires_at else None
            ),
            "remaining_seconds": self.remaining_seconds,
        }


class OverrideAuthorityChecker:
    """
    Checks override authority status for the prevention engine.

    The prevention engine must call this before enforcing any
    policy actions to respect active overrides.

    GAP-034: Wire OverrideAuthority to prevention.

    Usage:
        checker = OverrideAuthorityChecker()
        result = checker.check(override_authority)
        if result.skip_enforcement:
            # Skip policy enforcement
            log.info(f"Skipping enforcement: override by {result.override_by}")
        else:
            # Proceed with enforcement
            enforce_policy()
    """

    def check(self, override_authority: Any) -> OverrideCheckResult:
        """
        Check override authority status.

        Args:
            override_authority: OverrideAuthority model instance

        Returns:
            OverrideCheckResult with status and metadata
        """
        if override_authority is None:
            return OverrideCheckResult(
                status=OverrideStatus.NO_OVERRIDE,
                skip_enforcement=False,
                policy_id="unknown",
            )

        policy_id = getattr(override_authority, "policy_id", "unknown")

        # Check if overrides are allowed for this policy
        override_allowed = getattr(override_authority, "override_allowed", True)
        if not override_allowed:
            return OverrideCheckResult(
                status=OverrideStatus.OVERRIDE_NOT_ALLOWED,
                skip_enforcement=False,
                policy_id=policy_id,
            )

        # Check if an override is currently active
        is_active = self._is_override_active(override_authority)

        if not is_active:
            # Check if there was an override that has expired
            currently_overridden = getattr(override_authority, "currently_overridden", False)
            if currently_overridden:
                return OverrideCheckResult(
                    status=OverrideStatus.OVERRIDE_EXPIRED,
                    skip_enforcement=False,
                    policy_id=policy_id,
                )
            return OverrideCheckResult(
                status=OverrideStatus.NO_OVERRIDE,
                skip_enforcement=False,
                policy_id=policy_id,
            )

        # Override is active - gather metadata
        override_by = getattr(override_authority, "override_by", None)
        override_reason = getattr(override_authority, "override_reason", None)
        override_started_at = getattr(override_authority, "override_started_at", None)
        override_expires_at = getattr(override_authority, "override_expires_at", None)

        # Calculate remaining seconds
        remaining_seconds = None
        if override_expires_at:
            now = datetime.now(timezone.utc)
            delta = override_expires_at - now
            remaining_seconds = max(0, int(delta.total_seconds()))

        return OverrideCheckResult(
            status=OverrideStatus.OVERRIDE_ACTIVE,
            skip_enforcement=True,  # Key: skip enforcement when override active
            policy_id=policy_id,
            override_by=override_by,
            override_reason=override_reason,
            override_started_at=override_started_at,
            override_expires_at=override_expires_at,
            remaining_seconds=remaining_seconds,
        )

    def _is_override_active(self, override_authority: Any) -> bool:
        """Check if override is currently active."""
        # Use the model's is_override_active() method if available
        if hasattr(override_authority, "is_override_active"):
            return override_authority.is_override_active()

        # Fallback to manual check
        currently_overridden = getattr(override_authority, "currently_overridden", False)
        if not currently_overridden:
            return False

        override_expires_at = getattr(override_authority, "override_expires_at", None)
        if override_expires_at is None:
            return False

        now = datetime.now(timezone.utc)
        return now < override_expires_at

    def check_from_dict(
        self,
        policy_id: str,
        currently_overridden: bool = False,
        override_allowed: bool = True,
        override_by: Optional[str] = None,
        override_reason: Optional[str] = None,
        override_started_at: Optional[datetime] = None,
        override_expires_at: Optional[datetime] = None,
    ) -> OverrideCheckResult:
        """
        Check override status from individual fields.

        Useful when override data comes from a snapshot or dict
        rather than a model instance.

        Args:
            policy_id: Policy ID
            currently_overridden: Whether override flag is set
            override_allowed: Whether overrides are allowed
            override_by: User who initiated override
            override_reason: Reason for override
            override_started_at: When override started
            override_expires_at: When override expires

        Returns:
            OverrideCheckResult with status and metadata
        """
        if not override_allowed:
            return OverrideCheckResult(
                status=OverrideStatus.OVERRIDE_NOT_ALLOWED,
                skip_enforcement=False,
                policy_id=policy_id,
            )

        if not currently_overridden:
            return OverrideCheckResult(
                status=OverrideStatus.NO_OVERRIDE,
                skip_enforcement=False,
                policy_id=policy_id,
            )

        # Check if override has expired
        if override_expires_at is None:
            return OverrideCheckResult(
                status=OverrideStatus.OVERRIDE_EXPIRED,
                skip_enforcement=False,
                policy_id=policy_id,
            )

        now = datetime.now(timezone.utc)
        if now >= override_expires_at:
            return OverrideCheckResult(
                status=OverrideStatus.OVERRIDE_EXPIRED,
                skip_enforcement=False,
                policy_id=policy_id,
            )

        # Override is active
        delta = override_expires_at - now
        remaining_seconds = max(0, int(delta.total_seconds()))

        return OverrideCheckResult(
            status=OverrideStatus.OVERRIDE_ACTIVE,
            skip_enforcement=True,
            policy_id=policy_id,
            override_by=override_by,
            override_reason=override_reason,
            override_started_at=override_started_at,
            override_expires_at=override_expires_at,
            remaining_seconds=remaining_seconds,
        )


def should_skip_enforcement(override_authority: Any) -> bool:
    """
    Quick helper to check if enforcement should be skipped.

    Args:
        override_authority: OverrideAuthority model instance or None

    Returns:
        True if enforcement should be skipped, False otherwise
    """
    checker = OverrideAuthorityChecker()
    result = checker.check(override_authority)
    return result.skip_enforcement
