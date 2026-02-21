# capability_id: CAP-009
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Role: Override error type definitions (shared across L2 and L6)
# Callers: api/cus/policies/override.py (L2), controls/L6_drivers/override_driver.py (L6)
# Reference: PIN-504 (Cross-Domain Violation Resolution)
# artifact_class: CODE

"""
Override Types

Error classes for limit override operations.
Lives in L5_schemas so L2 can import without violating L2→L6 rules.
"""


class LimitOverrideServiceError(Exception):
    """Base exception for limit override service."""
    pass


class LimitNotFoundError(LimitOverrideServiceError):
    """Raised when the target limit does not exist."""
    pass


class OverrideNotFoundError(LimitOverrideServiceError):
    """Raised when the override does not exist."""
    pass


class OverrideValidationError(LimitOverrideServiceError):
    """Raised when override request validation fails."""
    pass


class StackingAbuseError(LimitOverrideServiceError):
    """Raised when attempting to stack overrides on same limit."""
    pass


__all__ = [
    "LimitOverrideServiceError",
    "LimitNotFoundError",
    "OverrideNotFoundError",
    "OverrideValidationError",
    "StackingAbuseError",
]
