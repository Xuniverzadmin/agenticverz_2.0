# capability_id: CAP-008
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: Feature-level intent declarations for self-defending architecture
# Callers: Any module requiring feature-level intent clarity
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 (Phase-2.3 Feature Intent System)

"""
Feature Intent System (L6)

PHILOSOPHY (Phase-2.3)
----------------------
TransactionIntent answers: "How does this function interact with the database?"

FeatureIntent answers: "What does this feature DO to system state?"

A fully self-defending system requires BOTH:
- Function-level: TransactionIntent (READ_ONLY, ATOMIC_WRITE, LOCKED_MUTATION)
- Feature-level: FeatureIntent (PURE_QUERY, STATE_MUTATION, EXTERNAL_SIDE_EFFECT, RECOVERABLE_OPERATION)

INTENT HIERARCHY
----------------
The system enforces consistency across three layers:

    FeatureIntent (module-level)
         ↓ constrains
    TransactionIntent (function-level)
         ↓ constrains
    Primitive (implementation-level)

If any layer disagrees, CI fails.

VALID INTENT COMBINATIONS
-------------------------

| FeatureIntent           | Allowed TransactionIntent          |
|-------------------------|------------------------------------|
| PURE_QUERY              | READ_ONLY only                     |
| STATE_MUTATION          | ATOMIC_WRITE, LOCKED_MUTATION      |
| EXTERNAL_SIDE_EFFECT    | ATOMIC_WRITE only                  |
| RECOVERABLE_OPERATION   | LOCKED_MUTATION only               |

WHY THIS EXISTS
---------------
Without feature-level intent:
- Functions can be "locally correct, globally wrong"
- Engineers can write non-idempotent workers
- Retry safety is not explicit
- Side-effects leak across boundaries

With feature-level intent:
- Design thinking is forced at module creation
- Intent consistency is machine-checkable
- Dangerous combinations are structurally forbidden

USAGE
-----
Every state-touching module must declare:

    from app.infra.feature_intent import FeatureIntent, RetryPolicy

    # Module-level declarations (CI enforced)
    FEATURE_INTENT = FeatureIntent.STATE_MUTATION
    RETRY_POLICY = RetryPolicy.SAFE

    # Function-level (must be consistent with feature intent)
    @transactional(intent=TransactionIntent.LOCKED_MUTATION)
    def do_mutation(txn: SingleConnectionTxn, ...):
        ...

CI ENFORCEMENT
--------------
scripts/ci/check_feature_intent.py will FAIL if:
- Module touches persistence but has no FEATURE_INTENT
- TransactionIntent disagrees with FeatureIntent
- DANGEROUS RetryPolicy with retries enabled
- LOCKED_MUTATION in non-RECOVERABLE_OPERATION feature
"""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("nova.infra.feature_intent")


# =============================================================================
# FEATURE INTENT DECLARATION
# =============================================================================


class FeatureIntent(Enum):
    """
    Declared intent for a feature module.

    Every module that touches persistence MUST declare one of these
    at module level as FEATURE_INTENT.

    | Intent                | Meaning                                    |
    |-----------------------|--------------------------------------------|
    | PURE_QUERY            | Read-only, no state changes                |
    | STATE_MUTATION        | Changes system state (DB writes)           |
    | EXTERNAL_SIDE_EFFECT  | Calls external services (APIs, webhooks)   |
    | RECOVERABLE_OPERATION | Must be idempotent and resumable           |

    Usage:
        # At module level
        FEATURE_INTENT = FeatureIntent.STATE_MUTATION
    """

    PURE_QUERY = "pure_query"
    STATE_MUTATION = "state_mutation"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"
    RECOVERABLE_OPERATION = "recoverable_operation"


class RetryPolicy(Enum):
    """
    Declared retry safety for a feature module.

    Every module with background processing MUST declare one of these
    at module level as RETRY_POLICY.

    | Policy    | Meaning                                           |
    |-----------|---------------------------------------------------|
    | NEVER     | Retries are forbidden (side-effects, non-idempotent) |
    | SAFE      | Retries are safe (idempotent operations)          |
    | DANGEROUS | Retries possible but require manual review        |

    CI Rules:
    - DANGEROUS + enabled retries = BLOCKING
    - LOCKED_MUTATION + retries = BLOCKING unless SAFE
    - EXTERNAL_SIDE_EFFECT + NEVER = required
    """

    NEVER = "never"
    SAFE = "safe"
    DANGEROUS = "dangerous"


# =============================================================================
# INTENT CONSISTENCY MATRIX
# =============================================================================


# Valid combinations: FeatureIntent -> allowed TransactionIntents
INTENT_CONSISTENCY_MATRIX: Dict[FeatureIntent, Set[str]] = {
    FeatureIntent.PURE_QUERY: {"READ_ONLY"},
    FeatureIntent.STATE_MUTATION: {"ATOMIC_WRITE", "LOCKED_MUTATION"},
    FeatureIntent.EXTERNAL_SIDE_EFFECT: {"ATOMIC_WRITE"},
    FeatureIntent.RECOVERABLE_OPERATION: {"LOCKED_MUTATION"},
}

# Forbidden combinations: (FeatureIntent, RetryPolicy) pairs that are invalid
FORBIDDEN_RETRY_COMBINATIONS: List[Tuple[FeatureIntent, RetryPolicy]] = [
    (FeatureIntent.EXTERNAL_SIDE_EFFECT, RetryPolicy.SAFE),  # Side effects can't be "safe" to retry
]

# Required retry policies by feature intent
REQUIRED_RETRY_POLICY: Dict[FeatureIntent, RetryPolicy] = {
    FeatureIntent.EXTERNAL_SIDE_EFFECT: RetryPolicy.NEVER,
    FeatureIntent.RECOVERABLE_OPERATION: RetryPolicy.SAFE,
}


# =============================================================================
# INTENT VALIDATION
# =============================================================================


class IntentConsistencyError(Exception):
    """
    Raised when feature intent doesn't match function intent.

    This is a DESIGN error. Fix the design, don't catch this.
    """

    pass


class RetryPolicyError(Exception):
    """
    Raised when retry policy is inconsistent with feature intent.

    This is a DESIGN error. Fix the design, don't catch this.
    """

    pass


def validate_intent_consistency(
    feature_intent: FeatureIntent,
    transaction_intent_name: str,
) -> None:
    """
    Validate that transaction intent is allowed for the feature intent.

    Args:
        feature_intent: The module's declared FeatureIntent
        transaction_intent_name: The function's TransactionIntent name

    Raises:
        IntentConsistencyError: If intents are inconsistent
    """
    allowed = INTENT_CONSISTENCY_MATRIX.get(feature_intent, set())

    if transaction_intent_name not in allowed:
        raise IntentConsistencyError(
            f"TransactionIntent.{transaction_intent_name} is not allowed "
            f"for FeatureIntent.{feature_intent.name}. "
            f"Allowed: {sorted(allowed)}"
        )


def validate_retry_policy(
    feature_intent: FeatureIntent,
    retry_policy: RetryPolicy,
) -> None:
    """
    Validate that retry policy is consistent with feature intent.

    Args:
        feature_intent: The module's declared FeatureIntent
        retry_policy: The module's declared RetryPolicy

    Raises:
        RetryPolicyError: If policy is inconsistent
    """
    # Check forbidden combinations
    if (feature_intent, retry_policy) in FORBIDDEN_RETRY_COMBINATIONS:
        raise RetryPolicyError(f"RetryPolicy.{retry_policy.name} is forbidden for FeatureIntent.{feature_intent.name}")

    # Check required policies
    required = REQUIRED_RETRY_POLICY.get(feature_intent)
    if required and retry_policy != required:
        raise RetryPolicyError(
            f"FeatureIntent.{feature_intent.name} requires RetryPolicy.{required.name}, got {retry_policy.name}"
        )


# =============================================================================
# FEATURE REGISTRY (for CI validation)
# =============================================================================


@dataclass
class FeatureDeclaration:
    """Registration of a feature module's intent declarations."""

    module_path: str
    feature_intent: FeatureIntent
    retry_policy: Optional[RetryPolicy] = None
    functions: List[str] = field(default_factory=list)


# Global registry of feature declarations
_FEATURE_REGISTRY: Dict[str, FeatureDeclaration] = {}


def get_feature_registry() -> Dict[str, FeatureDeclaration]:
    """Return the feature registry for CI validation."""
    return _FEATURE_REGISTRY.copy()


def register_feature(
    module_path: str,
    feature_intent: FeatureIntent,
    retry_policy: Optional[RetryPolicy] = None,
) -> None:
    """
    Register a feature module's intent declarations.

    This is called automatically by the @feature decorator or can be
    called explicitly at module load time.

    Args:
        module_path: Full module path (e.g., "app.costsim.circuit_breaker")
        feature_intent: The module's FeatureIntent
        retry_policy: The module's RetryPolicy (optional for PURE_QUERY)
    """
    # Validate retry policy if provided
    if retry_policy:
        validate_retry_policy(feature_intent, retry_policy)

    _FEATURE_REGISTRY[module_path] = FeatureDeclaration(
        module_path=module_path,
        feature_intent=feature_intent,
        retry_policy=retry_policy,
    )


# =============================================================================
# FEATURE DECORATOR
# =============================================================================


def feature(
    intent: FeatureIntent,
    retry: Optional[RetryPolicy] = None,
) -> Callable:
    """
    Decorator for feature functions that validates intent consistency.

    Use this on functions within a feature module to:
    1. Register the function with the feature
    2. Validate at decoration time that TransactionIntent is consistent
    3. Provide runtime validation

    Args:
        intent: The FeatureIntent this function belongs to
        retry: Optional RetryPolicy override for this function

    Usage:
        FEATURE_INTENT = FeatureIntent.STATE_MUTATION
        RETRY_POLICY = RetryPolicy.SAFE

        @feature(intent=FEATURE_INTENT, retry=RETRY_POLICY)
        @transactional(intent=TransactionIntent.LOCKED_MUTATION)
        def trip_circuit(txn: SingleConnectionTxn, ...):
            ...

    Note:
        The @feature decorator should be OUTERMOST (applied first,
        executes last) so it can inspect the @transactional metadata.
    """

    def decorator(func: Callable) -> Callable:
        module = func.__module__
        qualname = func.__qualname__
        full_name = f"{module}.{qualname}"

        # Register this function with the feature
        if module not in _FEATURE_REGISTRY:
            register_feature(module, intent, retry)

        feature_decl = _FEATURE_REGISTRY.get(module)
        if feature_decl:
            feature_decl.functions.append(full_name)

        # Check if function has @transactional decorator
        if hasattr(func, "_transaction_intent"):
            txn_intent_name = func._transaction_intent.name
            try:
                validate_intent_consistency(intent, txn_intent_name)
            except IntentConsistencyError as e:
                raise IntentConsistencyError(f"{full_name}: {e}") from e

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Attach metadata
        wrapper._feature_intent = intent
        wrapper._retry_policy = retry
        wrapper._feature_full_name = full_name

        return wrapper

    return decorator


# =============================================================================
# MODULE-LEVEL VALIDATION HELPER
# =============================================================================


def validate_module_intent(module_globals: Dict[str, Any]) -> None:
    """
    Validate that a module has required intent declarations.

    Call this at the end of a feature module to ensure declarations exist:

        from app.infra.feature_intent import (
            FeatureIntent, RetryPolicy, validate_module_intent
        )

        FEATURE_INTENT = FeatureIntent.STATE_MUTATION
        RETRY_POLICY = RetryPolicy.SAFE

        # ... module code ...

        # At end of module
        validate_module_intent(globals())

    Raises:
        ValueError: If required declarations are missing
    """
    module_name = module_globals.get("__name__", "<unknown>")

    # Check for FEATURE_INTENT
    if "FEATURE_INTENT" not in module_globals:
        raise ValueError(
            f"Module {module_name} touches persistence but has no FEATURE_INTENT. Add: FEATURE_INTENT = FeatureIntent.X"
        )

    feature_intent = module_globals["FEATURE_INTENT"]
    if not isinstance(feature_intent, FeatureIntent):
        raise ValueError(f"Module {module_name}: FEATURE_INTENT must be a FeatureIntent enum value")

    # Check for RETRY_POLICY (required for certain intents)
    retry_policy = module_globals.get("RETRY_POLICY")

    if feature_intent in REQUIRED_RETRY_POLICY:
        if retry_policy is None:
            required = REQUIRED_RETRY_POLICY[feature_intent]
            raise ValueError(
                f"Module {module_name}: FeatureIntent.{feature_intent.name} "
                f"requires RETRY_POLICY = RetryPolicy.{required.name}"
            )

    # Register the module
    register_feature(
        module_path=module_name,
        feature_intent=feature_intent,
        retry_policy=retry_policy,
    )

    logger.debug(
        f"Module {module_name} registered: "
        f"intent={feature_intent.name}, retry={retry_policy.name if retry_policy else 'None'}"
    )
