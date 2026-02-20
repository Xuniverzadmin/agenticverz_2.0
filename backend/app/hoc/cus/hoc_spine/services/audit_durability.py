# capability_id: CAP-012
# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: durability state (via driver)
#   Writes: none
# Role: RAC durability enforcement before acknowledgment
# Callers: ROK (L5), Facades (L4), AuditReconciler (L4)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-050 (RAC Durability Enforcement)

"""
Module: durability
Purpose: Enforce RAC durability before acknowledgment.

The rac_durability_enforce flag in GovernanceConfig controls whether
durability is strictly enforced before acknowledging audit operations.

When enabled:
    - Acks must be persisted to durable storage before being accepted
    - Expectations must be durably stored before run starts
    - In-memory-only mode raises RACDurabilityEnforcementError

This ensures audit contracts survive crashes and can be reconciled
even if workers fail.

Exports:
    - RACDurabilityEnforcementError: Raised when durability not satisfied
    - RACDurabilityChecker: Checks durability constraints
    - check_rac_durability: Quick helper function
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class DurabilityCheckResult(str, Enum):
    """Result of a durability check."""

    DURABLE = "durable"  # Data is durably stored
    NOT_DURABLE = "not_durable"  # Data is in-memory only
    ENFORCEMENT_DISABLED = "enforcement_disabled"  # Enforcement is disabled
    UNKNOWN = "unknown"  # Durability state unknown


class RACDurabilityEnforcementError(Exception):
    """
    Raised when RAC durability enforcement fails.

    This error indicates that an operation requiring durable storage
    was attempted without durable backing store available.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        durability_mode: str,
        enforcement_enabled: bool,
    ):
        super().__init__(message)
        self.operation = operation
        self.durability_mode = durability_mode
        self.enforcement_enabled = enforcement_enabled

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error": "RACDurabilityEnforcementError",
            "message": str(self),
            "operation": self.operation,
            "durability_mode": self.durability_mode,
            "enforcement_enabled": self.enforcement_enabled,
        }


@dataclass
class DurabilityCheckResponse:
    """Response from a durability check."""

    result: DurabilityCheckResult
    is_durable: bool
    enforcement_enabled: bool
    durability_mode: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "result": self.result.value,
            "is_durable": self.is_durable,
            "enforcement_enabled": self.enforcement_enabled,
            "durability_mode": self.durability_mode,
            "message": self.message,
        }


class RACDurabilityChecker:
    """
    Checks and enforces RAC durability constraints.

    GAP-050: Add durability checks to RAC.

    The checker verifies that audit data is durably stored before
    allowing acknowledgment operations when enforcement is enabled.

    Usage:
        checker = RACDurabilityChecker(
            enforcement_enabled=True,
            durability_mode="REDIS",
        )

        # Before adding an ack
        checker.ensure_durable("add_ack")

        # Or check without raising
        response = checker.check()
        if not response.is_durable and response.enforcement_enabled:
            handle_durability_issue()
    """

    def __init__(
        self,
        enforcement_enabled: bool = True,
        durability_mode: str = "MEMORY",
    ):
        """
        Initialize the durability checker.

        Args:
            enforcement_enabled: Whether rac_durability_enforce is True
            durability_mode: Current durability mode (MEMORY or REDIS)
        """
        self._enforcement_enabled = enforcement_enabled
        self._durability_mode = durability_mode

    @classmethod
    def from_governance_config(cls, config: Any) -> "RACDurabilityChecker":
        """
        Create checker from GovernanceConfig.

        Args:
            config: GovernanceConfig instance

        Returns:
            RACDurabilityChecker configured from config
        """
        enforcement_enabled = getattr(config, "rac_durability_enforce", True)
        return cls(
            enforcement_enabled=enforcement_enabled,
            durability_mode="MEMORY",  # Will be updated by audit store
        )

    @classmethod
    def from_audit_store(
        cls,
        store: Any,
        enforcement_enabled: bool = True,
    ) -> "RACDurabilityChecker":
        """
        Create checker from AuditStore instance.

        Args:
            store: AuditStore instance
            enforcement_enabled: Whether rac_durability_enforce is True

        Returns:
            RACDurabilityChecker configured from store
        """
        durability_mode = "MEMORY"
        if store is not None:
            mode = getattr(store, "durability_mode", None)
            if mode is not None:
                durability_mode = mode.value if hasattr(mode, "value") else str(mode)

        return cls(
            enforcement_enabled=enforcement_enabled,
            durability_mode=durability_mode,
        )

    @property
    def is_durable(self) -> bool:
        """Check if current mode is durable."""
        return self._durability_mode == "REDIS"

    @property
    def enforcement_enabled(self) -> bool:
        """Check if durability enforcement is enabled."""
        return self._enforcement_enabled

    def check(self) -> DurabilityCheckResponse:
        """
        Check durability status.

        Returns:
            DurabilityCheckResponse with status and metadata
        """
        if not self._enforcement_enabled:
            return DurabilityCheckResponse(
                result=DurabilityCheckResult.ENFORCEMENT_DISABLED,
                is_durable=self.is_durable,
                enforcement_enabled=False,
                durability_mode=self._durability_mode,
                message="RAC durability enforcement is disabled",
            )

        if self.is_durable:
            return DurabilityCheckResponse(
                result=DurabilityCheckResult.DURABLE,
                is_durable=True,
                enforcement_enabled=True,
                durability_mode=self._durability_mode,
                message="Storage is durable (Redis-backed)",
            )

        return DurabilityCheckResponse(
            result=DurabilityCheckResult.NOT_DURABLE,
            is_durable=False,
            enforcement_enabled=True,
            durability_mode=self._durability_mode,
            message="Storage is NOT durable (in-memory only)",
        )

    def ensure_durable(self, operation: str) -> None:
        """
        Ensure durability or raise error.

        This method should be called before any operation that requires
        durable storage when enforcement is enabled.

        Args:
            operation: Name of the operation being performed

        Raises:
            RACDurabilityEnforcementError: If enforcement enabled and not durable
        """
        response = self.check()

        if response.result == DurabilityCheckResult.NOT_DURABLE:
            raise RACDurabilityEnforcementError(
                message=(
                    f"RAC durability enforcement failed for '{operation}': "
                    f"storage is not durable ({self._durability_mode}). "
                    f"Enable Redis-backed storage or disable rac_durability_enforce."
                ),
                operation=operation,
                durability_mode=self._durability_mode,
                enforcement_enabled=True,
            )

    def should_allow_operation(self, operation: str) -> tuple[bool, str]:
        """
        Check if an operation should be allowed.

        Returns a tuple with (allowed, reason) instead of raising.

        Args:
            operation: Name of the operation

        Returns:
            Tuple of (allowed, reason_message)
        """
        response = self.check()

        if response.result == DurabilityCheckResult.DURABLE:
            return True, "Storage is durable"

        if response.result == DurabilityCheckResult.ENFORCEMENT_DISABLED:
            return True, "Durability enforcement is disabled"

        return False, (
            f"Operation '{operation}' blocked: storage is not durable "
            f"({self._durability_mode}) and enforcement is enabled"
        )


def check_rac_durability(
    enforcement_enabled: bool = True,
    durability_mode: str = "MEMORY",
) -> DurabilityCheckResponse:
    """
    Quick helper to check RAC durability.

    Args:
        enforcement_enabled: Whether rac_durability_enforce is True
        durability_mode: Current durability mode

    Returns:
        DurabilityCheckResponse with status and metadata
    """
    checker = RACDurabilityChecker(
        enforcement_enabled=enforcement_enabled,
        durability_mode=durability_mode,
    )
    return checker.check()


def ensure_rac_durability(
    operation: str,
    enforcement_enabled: bool = True,
    durability_mode: str = "MEMORY",
) -> None:
    """
    Quick helper to ensure RAC durability or raise error.

    Args:
        operation: Name of the operation being performed
        enforcement_enabled: Whether rac_durability_enforce is True
        durability_mode: Current durability mode

    Raises:
        RACDurabilityEnforcementError: If enforcement enabled and not durable
    """
    checker = RACDurabilityChecker(
        enforcement_enabled=enforcement_enabled,
        durability_mode=durability_mode,
    )
    checker.ensure_durable(operation)
