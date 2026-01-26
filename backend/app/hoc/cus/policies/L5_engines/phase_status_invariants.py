# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: governance_config (via driver)
#   Writes: none
# Role: Phase-status invariant enforcement from GovernanceConfig
# Callers: ROK (L5), worker runtime
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-051 (Phase-Status Invariants)

"""
Module: phase_status_invariants
Purpose: Enforce phase-status invariants using GovernanceConfig.

The phase_status_invariant_enforce flag in GovernanceConfig controls
whether invalid phase-status combinations are blocked.

Phase-Status Invariants:
    - CREATED, AUTHORIZED: status must be "queued"
    - EXECUTING, GOVERNANCE_CHECK, FINALIZING: status must be "running"
    - COMPLETED: status must be "succeeded"
    - FAILED: status must be "failed", "failed_policy", "cancelled", or "retry"

When enforcement is enabled, attempting an invalid combination raises
PhaseStatusInvariantEnforcementError.

Exports:
    - PhaseStatusInvariantEnforcementError: Raised on violation
    - PhaseStatusInvariantChecker: Main checker class
    - check_phase_status_invariant: Quick helper function
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, FrozenSet, Optional


class InvariantCheckResult(str, Enum):
    """Result of an invariant check."""

    VALID = "valid"  # Phase-status combination is valid
    INVALID = "invalid"  # Combination is invalid
    ENFORCEMENT_DISABLED = "enforcement_disabled"  # Enforcement is disabled
    UNKNOWN_PHASE = "unknown_phase"  # Phase not recognized


# Phase-status invariants map
PHASE_STATUS_INVARIANTS: dict[str, FrozenSet[str]] = {
    "CREATED": frozenset({"queued"}),
    "AUTHORIZED": frozenset({"queued"}),
    "EXECUTING": frozenset({"running"}),
    "GOVERNANCE_CHECK": frozenset({"running"}),
    "FINALIZING": frozenset({"running"}),
    "COMPLETED": frozenset({"succeeded"}),
    "FAILED": frozenset({"failed", "failed_policy", "cancelled", "retry"}),
}


class PhaseStatusInvariantEnforcementError(Exception):
    """
    Raised when phase-status invariant enforcement fails.

    This error indicates that an invalid phase-status combination
    was attempted when enforcement is enabled.
    """

    def __init__(
        self,
        message: str,
        phase: str,
        status: str,
        allowed_statuses: FrozenSet[str],
        enforcement_enabled: bool,
    ):
        super().__init__(message)
        self.phase = phase
        self.status = status
        self.allowed_statuses = allowed_statuses
        self.enforcement_enabled = enforcement_enabled

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error": "PhaseStatusInvariantEnforcementError",
            "message": str(self),
            "phase": self.phase,
            "status": self.status,
            "allowed_statuses": list(self.allowed_statuses),
            "enforcement_enabled": self.enforcement_enabled,
        }


@dataclass
class InvariantCheckResponse:
    """Response from an invariant check."""

    result: InvariantCheckResult
    is_valid: bool
    enforcement_enabled: bool
    phase: str
    status: str
    allowed_statuses: FrozenSet[str]
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "result": self.result.value,
            "is_valid": self.is_valid,
            "enforcement_enabled": self.enforcement_enabled,
            "phase": self.phase,
            "status": self.status,
            "allowed_statuses": list(self.allowed_statuses),
            "message": self.message,
        }


class PhaseStatusInvariantChecker:
    """
    Checks and enforces phase-status invariants.

    GAP-051: Add invariant checks to ROK.

    The checker validates that phase-status combinations are valid
    and can raise errors when enforcement is enabled.

    Usage:
        checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

        # Before a phase transition
        checker.ensure_valid("EXECUTING", "running")

        # Or check without raising
        response = checker.check("EXECUTING", "running")
        if not response.is_valid and response.enforcement_enabled:
            handle_invariant_violation()
    """

    def __init__(self, enforcement_enabled: bool = True):
        """
        Initialize the invariant checker.

        Args:
            enforcement_enabled: Whether phase_status_invariant_enforce is True
        """
        self._enforcement_enabled = enforcement_enabled

    @classmethod
    def from_governance_config(cls, config: Any) -> "PhaseStatusInvariantChecker":
        """
        Create checker from GovernanceConfig.

        Args:
            config: GovernanceConfig instance

        Returns:
            PhaseStatusInvariantChecker configured from config
        """
        enforcement_enabled = getattr(config, "phase_status_invariant_enforce", True)
        return cls(enforcement_enabled=enforcement_enabled)

    @property
    def enforcement_enabled(self) -> bool:
        """Check if enforcement is enabled."""
        return self._enforcement_enabled

    def get_allowed_statuses(self, phase: str) -> FrozenSet[str]:
        """
        Get allowed statuses for a phase.

        Args:
            phase: Phase name (e.g., "EXECUTING")

        Returns:
            Frozenset of allowed status strings, or empty set if unknown phase
        """
        return PHASE_STATUS_INVARIANTS.get(phase.upper(), frozenset())

    def is_valid_combination(self, phase: str, status: str) -> bool:
        """
        Check if a phase-status combination is valid.

        Args:
            phase: Phase name
            status: Status value

        Returns:
            True if valid, False if invalid or unknown phase
        """
        allowed = self.get_allowed_statuses(phase)
        if not allowed:
            return True  # Unknown phase, can't validate
        return status in allowed

    def check(self, phase: str, status: str) -> InvariantCheckResponse:
        """
        Check if a phase-status combination is valid.

        Args:
            phase: Phase name (e.g., "EXECUTING")
            status: Status value (e.g., "running")

        Returns:
            InvariantCheckResponse with validation result
        """
        phase_upper = phase.upper()
        allowed_statuses = self.get_allowed_statuses(phase_upper)

        if not allowed_statuses:
            return InvariantCheckResponse(
                result=InvariantCheckResult.UNKNOWN_PHASE,
                is_valid=True,  # Can't validate unknown phase
                enforcement_enabled=self._enforcement_enabled,
                phase=phase_upper,
                status=status,
                allowed_statuses=frozenset(),
                message=f"Unknown phase '{phase_upper}' - cannot validate",
            )

        if status in allowed_statuses:
            return InvariantCheckResponse(
                result=InvariantCheckResult.VALID,
                is_valid=True,
                enforcement_enabled=self._enforcement_enabled,
                phase=phase_upper,
                status=status,
                allowed_statuses=allowed_statuses,
                message=f"Status '{status}' is valid for phase '{phase_upper}'",
            )

        if not self._enforcement_enabled:
            return InvariantCheckResponse(
                result=InvariantCheckResult.ENFORCEMENT_DISABLED,
                is_valid=False,
                enforcement_enabled=False,
                phase=phase_upper,
                status=status,
                allowed_statuses=allowed_statuses,
                message=(
                    f"Invalid combination: phase '{phase_upper}' does not allow "
                    f"status '{status}' (enforcement disabled)"
                ),
            )

        return InvariantCheckResponse(
            result=InvariantCheckResult.INVALID,
            is_valid=False,
            enforcement_enabled=True,
            phase=phase_upper,
            status=status,
            allowed_statuses=allowed_statuses,
            message=(
                f"Invalid combination: phase '{phase_upper}' does not allow "
                f"status '{status}'. Allowed: {sorted(allowed_statuses)}"
            ),
        )

    def ensure_valid(self, phase: str, status: str) -> None:
        """
        Ensure a phase-status combination is valid or raise error.

        This method should be called before phase transitions
        when enforcement is enabled.

        Args:
            phase: Phase name
            status: Status value

        Raises:
            PhaseStatusInvariantEnforcementError: If invalid and enforcement enabled
        """
        response = self.check(phase, status)

        if response.result == InvariantCheckResult.INVALID:
            raise PhaseStatusInvariantEnforcementError(
                message=(
                    f"Phase-status invariant violated: phase '{response.phase}' "
                    f"does not allow status '{response.status}'. "
                    f"Allowed statuses: {sorted(response.allowed_statuses)}"
                ),
                phase=response.phase,
                status=response.status,
                allowed_statuses=response.allowed_statuses,
                enforcement_enabled=True,
            )

    def should_allow_transition(
        self,
        phase: str,
        status: str,
    ) -> tuple[bool, str]:
        """
        Check if a transition should be allowed.

        Returns a tuple with (allowed, reason) instead of raising.

        Args:
            phase: Phase name
            status: Status value

        Returns:
            Tuple of (allowed, reason_message)
        """
        response = self.check(phase, status)

        if response.is_valid:
            return True, response.message

        if not self._enforcement_enabled:
            return True, "Enforcement disabled - allowing invalid combination"

        return False, response.message


def check_phase_status_invariant(
    phase: str,
    status: str,
    enforcement_enabled: bool = True,
) -> InvariantCheckResponse:
    """
    Quick helper to check a phase-status invariant.

    Args:
        phase: Phase name
        status: Status value
        enforcement_enabled: Whether enforcement is enabled

    Returns:
        InvariantCheckResponse with validation result
    """
    checker = PhaseStatusInvariantChecker(enforcement_enabled=enforcement_enabled)
    return checker.check(phase, status)


def ensure_phase_status_invariant(
    phase: str,
    status: str,
    enforcement_enabled: bool = True,
) -> None:
    """
    Quick helper to ensure phase-status invariant or raise error.

    Args:
        phase: Phase name
        status: Status value
        enforcement_enabled: Whether enforcement is enabled

    Raises:
        PhaseStatusInvariantEnforcementError: If invalid and enforcement enabled
    """
    checker = PhaseStatusInvariantChecker(enforcement_enabled=enforcement_enabled)
    checker.ensure_valid(phase, status)
