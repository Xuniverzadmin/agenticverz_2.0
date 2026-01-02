# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: Infrastructure namespace for Phase-S systems
# Callers: Any layer requiring infra utilities
# Allowed Imports: L6 only
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264

"""
Infrastructure Namespace (infra.*)

This namespace contains Phase-S systems for:
- Error capture and forensics
- Correlation tracking
- Replay infrastructure
- Synthetic traffic generation

Semantic Separation:
- infra.* = Infrastructure systems (this namespace)
- product.* = Customer-facing product code

Everything here is L6 (Platform Substrate) or L7 (Ops Tools).
Nothing here should import L4 (Domain Engines) or L5 (Workers).
"""

from app.infra.correlation import (
    CorrelationContext,
    generate_correlation_id,
)
from app.infra.danger_fences import (
    DANGER_FENCES,
    # Phase-2.4: Danger Fences (PIN-268 GU-004)
    RecoveryEnqueueError,
    enqueue_recovery_candidate_safely,
    get_danger_fence_documentation,
)
from app.infra.error_envelope import (
    ErrorClass,
    ErrorEnvelope,
    ErrorSeverity,
)
from app.infra.error_store import (
    cleanup_old_errors,
    get_error_counts_by_class,
    get_error_counts_by_component,
    get_error_timeline,
    get_errors_by_class,
    get_errors_by_component,
    get_errors_by_correlation,
    persist_error,
    persist_errors_batch,
)
from app.infra.feature_intent import (
    INTENT_CONSISTENCY_MATRIX,
    # Phase-2.3: Feature Intent System
    FeatureIntent,
    IntentConsistencyError,
    RetryPolicy,
    RetryPolicyError,
    feature,
    get_feature_registry,
    validate_intent_consistency,
    validate_module_intent,
    validate_retry_policy,
)
from app.infra.transaction import (
    IntentViolationError,
    # Phase-2.1: Self-Defending Primitives
    SingleConnectionTxn,
    # Phase-2.2: Intent Declaration System
    TransactionIntent,
    get_intent_registry,
    get_or_create_locked,
    single_connection_transaction,
    single_connection_transaction_with_engine,
    transactional,
)

__all__ = [
    # Error Envelope
    "ErrorEnvelope",
    "ErrorSeverity",
    "ErrorClass",
    # Correlation
    "generate_correlation_id",
    "CorrelationContext",
    # Error Persistence (Track 1.3)
    "persist_error",
    "persist_errors_batch",
    "get_errors_by_correlation",
    "get_errors_by_component",
    "get_errors_by_class",
    "get_error_counts_by_class",
    "get_error_counts_by_component",
    "get_error_timeline",
    "cleanup_old_errors",
    # Feature Intent System (Phase-2.3)
    "FeatureIntent",
    "RetryPolicy",
    "feature",
    "validate_module_intent",
    "get_feature_registry",
    "validate_intent_consistency",
    "validate_retry_policy",
    "IntentConsistencyError",
    "RetryPolicyError",
    "INTENT_CONSISTENCY_MATRIX",
    # Transaction Intent System (Phase-2.2)
    "TransactionIntent",
    "transactional",
    "IntentViolationError",
    "get_intent_registry",
    # Transaction Primitives (Phase-2.1 Self-Defense)
    "SingleConnectionTxn",
    "single_connection_transaction",
    "single_connection_transaction_with_engine",
    "get_or_create_locked",
    # Danger Fences (Phase-2.4 PIN-268 GU-004)
    "RecoveryEnqueueError",
    "enqueue_recovery_candidate_safely",
    "get_danger_fence_documentation",
    "DANGER_FENCES",
]
