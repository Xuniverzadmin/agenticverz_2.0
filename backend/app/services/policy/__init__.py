# Layer: L4 — Domain Engine
# Product: system-wide
# Role: Policy domain services package
# Reference: POLICY Domain Qualification, API-001 Guardrail

"""
Policy Domain Services (L4)

This package provides domain-level services for policy operations.
L3 adapters should import from this package, NOT from L6 models directly.

Available services:
- PolicyFacade: Primary facade for policy operations (API-001 compliant)
- CustomerPolicyReadService: Read operations for customer policy constraints
- PolicySnapshotRegistry: Immutable policy snapshot management (GAP-029)
"""

from app.services.policy.customer_policy_read_service import (
    BudgetConstraint,
    CustomerPolicyReadService,
    GuardrailSummary,
    PolicyConstraints,
    RateLimit,
    get_customer_policy_read_service,
)
from app.services.policy.facade import PolicyFacade, get_policy_facade, reset_policy_facade
from app.services.policy.snapshot_service import (
    ImmutabilityViolation,
    PolicySnapshotData,
    PolicySnapshotError,
    PolicySnapshotRegistry,
    SnapshotRegistryStats,
    SnapshotStatus,
    _reset_snapshot_registry,
    create_policy_snapshot,
    get_active_snapshot,
    get_policy_snapshot,
    get_snapshot_history,
    get_snapshot_registry,
    verify_snapshot,
)

__all__ = [
    # Facade (API-001 compliant - use this for policy operations)
    "PolicyFacade",
    "get_policy_facade",
    "reset_policy_facade",
    # Customer Policy Service
    "CustomerPolicyReadService",
    "get_customer_policy_read_service",
    # DTOs
    "BudgetConstraint",
    "RateLimit",
    "GuardrailSummary",
    "PolicyConstraints",
    # Policy Snapshot Immutability (GAP-029)
    "ImmutabilityViolation",
    "PolicySnapshotData",
    "PolicySnapshotError",
    "PolicySnapshotRegistry",
    "SnapshotRegistryStats",
    "SnapshotStatus",
    "_reset_snapshot_registry",
    "create_policy_snapshot",
    "get_active_snapshot",
    "get_policy_snapshot",
    "get_snapshot_history",
    "get_snapshot_registry",
    "verify_snapshot",
]
