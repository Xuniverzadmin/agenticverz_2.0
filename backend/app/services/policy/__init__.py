# Layer: L4 — Domain Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: Policy domain services package
# Reference: POLICY Domain Qualification, API-001 Guardrail, FACADE_CONSOLIDATION_PLAN.md

"""
Policy Domain Services (L4)

This package provides domain-level services for policy operations.
L3 adapters should import from this package, NOT from L6 models directly.

Available services:
- PolicyDriver: INTERNAL driver for policy evaluation (workers, governance)
- CustomerPolicyReadService: Read operations for customer policy constraints
- PolicySnapshotRegistry: Immutable policy snapshot management (GAP-029)

For CUSTOMER API CRUD operations, use policies_facade.py (at services root) instead.
"""

from app.services.policy.customer_policy_read_service import (
    BudgetConstraint,
    CustomerPolicyReadService,
    GuardrailSummary,
    PolicyConstraints,
    RateLimit,
    get_customer_policy_read_service,
)

# NEW: Driver for internal use (policy_layer, governance)
from app.services.policy.policy_driver import (
    PolicyDriver,
    get_policy_driver,
    reset_policy_driver,
)

# DEPRECATED: Backward compatibility aliases (will be removed)
# Use PolicyDriver / get_policy_driver() instead
from app.services.policy.policy_driver import (
    PolicyFacade,  # Alias for PolicyDriver
    get_policy_facade,  # Alias for get_policy_driver
    reset_policy_facade,  # Alias for reset_policy_driver
)
# NOTE: LessonsLearnedEngine was moved to HOC (app.hoc.cus.policies.L5_engines.lessons_engine).
# Legacy shim is disconnected (PIN-468, PIN-495). Re-export removed per PIN-507 Law 0.

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
    # Driver (INTERNAL - for policy_layer, governance)
    "PolicyDriver",
    "get_policy_driver",
    "reset_policy_driver",
    # DEPRECATED: Backward compatibility aliases
    "PolicyFacade",  # Use PolicyDriver instead
    "get_policy_facade",  # Use get_policy_driver instead
    "reset_policy_facade",  # Use reset_policy_driver instead
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
