# capability_id: CAP-006
# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: Prometheus metrics for auth gateway token verification
# Callers: gateway.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-XXX (Auth Gateway Metrics)

"""
Auth Gateway Metrics

Provides Prometheus metrics for token verification.

Metrics:
    auth_tokens_verified_total: Counter for successful token verifications
    auth_tokens_rejected_total: Counter for rejected tokens

Reference: AUTH_DESIGN.md
"""

from __future__ import annotations

import logging

logger = logging.getLogger("nova.auth.gateway_metrics")

# Try to import prometheus_client, gracefully degrade if not available
try:
    from prometheus_client import Counter

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not available, metrics will be logged only")


# =============================================================================
# Prometheus Metrics
# =============================================================================

if PROMETHEUS_AVAILABLE:
    # Counter: Track successful token verifications by source
    AUTH_TOKENS_VERIFIED = Counter(
        "auth_tokens_verified_total",
        "Count of successfully verified auth tokens",
        ["source"],  # clerk only (for humans)
    )

    # Counter: Track rejected tokens by source and reason
    AUTH_TOKENS_REJECTED = Counter(
        "auth_tokens_rejected_total",
        "Count of rejected auth tokens",
        ["source", "reason"],  # source: clerk, unknown; reason: expired, invalid_signature, etc.
    )


# =============================================================================
# Metric Recording Functions
# =============================================================================


def record_token_verified(source: str) -> None:
    """Record a successful token verification."""
    if PROMETHEUS_AVAILABLE:
        AUTH_TOKENS_VERIFIED.labels(source=source).inc()
    logger.debug(f"Token verified: source={source}")


def record_token_rejected(source: str, reason: str) -> None:
    """Record a rejected token."""
    if PROMETHEUS_AVAILABLE:
        AUTH_TOKENS_REJECTED.labels(source=source, reason=reason).inc()
    logger.debug(f"Token rejected: source={source}, reason={reason}")
