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
from app.infra.error_envelope import (
    ErrorClass,
    ErrorEnvelope,
    ErrorSeverity,
)
from app.infra.error_store import (
    persist_error,
    persist_errors_batch,
    get_errors_by_correlation,
    get_errors_by_component,
    get_errors_by_class,
    get_error_counts_by_class,
    get_error_counts_by_component,
    get_error_timeline,
    cleanup_old_errors,
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
]
