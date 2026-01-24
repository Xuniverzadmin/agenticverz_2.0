# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: runtime
#   Execution: sync
# Role: Phase-7 AbuseProtectionProvider protocol and MockAbuseProtectionProvider
# Callers: protection middleware, SDK endpoints, runtime paths
# Allowed Imports: L4 (protection.decisions, billing)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-7 (Abuse & Protection Layer)

"""
Phase-7 Abuse Protection Provider — Interface and Mock Implementation

PIN-399 Phase-7: Mock provider must be behavior-compatible with real provider.

DESIGN INVARIANTS (LOCKED):
- ABUSE-004: Protection providers are swappable behind a fixed interface
- ABUSE-005: Mock provider must be behavior-compatible with real provider

IMPLEMENTATION CONSTRAINTS:
- Deterministic thresholds
- Static configs
- No external calls
- No ML

ORDERING RULE (Critical):
    Checks execute in this order:
    1. Rate limit
    2. Burst control
    3. Cost guard
    4. Anomaly detection

    First REJECT stops evaluation.
    This order is LOCKED to preserve predictability.
"""

from typing import Protocol, Optional
import logging
import time

from app.protection.decisions import (
    Decision,
    ProtectionResult,
    AnomalySignal,
    allow,
    reject_rate_limit,
    reject_cost_limit,
    throttle,
)
from app.billing import get_billing_provider, Limits

logger = logging.getLogger(__name__)


class AbuseProtectionProvider(Protocol):
    """
    Phase-7 Abuse Protection Provider Protocol.

    All protection providers (mock and real) must implement this interface.

    This protocol is LOCKED per ABUSE-004.
    """

    def check_rate_limit(self, tenant_id: str, endpoint: str) -> ProtectionResult:
        """
        Check rate limit for a tenant/endpoint combination.

        Args:
            tenant_id: The tenant identifier
            endpoint: The endpoint being accessed

        Returns:
            ProtectionResult with decision
        """
        ...

    def check_burst(self, tenant_id: str, endpoint: str) -> ProtectionResult:
        """
        Check burst control for a tenant/endpoint combination.

        Args:
            tenant_id: The tenant identifier
            endpoint: The endpoint being accessed

        Returns:
            ProtectionResult with decision
        """
        ...

    def check_cost(self, tenant_id: str, operation: str) -> ProtectionResult:
        """
        Check cost guard for a tenant/operation combination.

        Args:
            tenant_id: The tenant identifier
            operation: The operation being performed

        Returns:
            ProtectionResult with decision
        """
        ...

    def detect_anomaly(self, tenant_id: str) -> Optional[AnomalySignal]:
        """
        Detect usage anomaly for a tenant.

        INVARIANT: Anomaly detection never blocks user traffic (ABUSE-003).

        Args:
            tenant_id: The tenant identifier

        Returns:
            AnomalySignal if anomaly detected, None otherwise
        """
        ...

    def check_all(self, tenant_id: str, endpoint: str, operation: str) -> ProtectionResult:
        """
        Run all protection checks in order.

        ORDER (LOCKED):
        1. Rate limit
        2. Burst control
        3. Cost guard
        4. Anomaly detection (non-blocking)

        First REJECT stops evaluation.

        Args:
            tenant_id: The tenant identifier
            endpoint: The endpoint being accessed
            operation: The operation being performed

        Returns:
            ProtectionResult with decision (first REJECT wins)
        """
        ...


class MockAbuseProtectionProvider:
    """
    Phase-7 Mock Abuse Protection Provider.

    Implements AbuseProtectionProvider protocol with deterministic behavior.

    IMPLEMENTATION CONSTRAINTS:
    - Deterministic thresholds
    - Static configs
    - No external calls
    - No ML
    - No adaptive behavior

    PROTECTION DIMENSIONS:
    - Rate limits: 1000 req/min default
    - Burst control: 100 req/sec default
    - Cost guards: Read from billing limits
    - Anomaly detection: 10x jump threshold
    """

    def __init__(self) -> None:
        """Initialize mock provider with in-memory state."""
        # Request tracking (in-memory, not persistent)
        self._request_counts: dict[str, dict[str, int]] = {}  # tenant -> endpoint -> count
        self._request_timestamps: dict[str, float] = {}  # tenant -> last request time
        self._burst_counts: dict[str, int] = {}  # tenant -> burst count in current second
        self._burst_second: dict[str, int] = {}  # tenant -> which second we're counting
        self._daily_costs: dict[str, float] = {}  # tenant -> daily cost accumulator

        # Static thresholds (deterministic)
        self._rate_limit_per_minute = 1000
        self._burst_limit_per_second = 100
        self._anomaly_multiplier = 10.0
        self._baseline_requests = 100.0  # baseline for anomaly detection

    def check_rate_limit(self, tenant_id: str, endpoint: str) -> ProtectionResult:
        """
        Check rate limit for a tenant/endpoint combination.

        Mock behavior: Track requests per minute, reject if over limit.
        """
        # Initialize tracking
        if tenant_id not in self._request_counts:
            self._request_counts[tenant_id] = {}

        # Count for this endpoint
        endpoint_counts = self._request_counts[tenant_id]
        current_count = endpoint_counts.get(endpoint, 0)

        # Check against limit
        if current_count >= self._rate_limit_per_minute:
            return reject_rate_limit(
                dimension="rate",
                retry_after_ms=60000,  # 1 minute
                message=f"Rate limit exceeded: {current_count}/{self._rate_limit_per_minute} req/min",
            )

        # Increment count
        endpoint_counts[endpoint] = current_count + 1

        return allow()

    def check_burst(self, tenant_id: str, endpoint: str) -> ProtectionResult:
        """
        Check burst control for a tenant/endpoint combination.

        Mock behavior: Track requests per second, throttle if over limit.
        """
        current_second = int(time.time())

        # Reset if new second
        if self._burst_second.get(tenant_id) != current_second:
            self._burst_second[tenant_id] = current_second
            self._burst_counts[tenant_id] = 0

        current_burst = self._burst_counts.get(tenant_id, 0)

        # Check against limit
        if current_burst >= self._burst_limit_per_second:
            return throttle(
                dimension="burst",
                retry_after_ms=1000,  # 1 second
                message=f"Burst limit exceeded: {current_burst}/{self._burst_limit_per_second} req/sec",
            )

        # Increment burst count
        self._burst_counts[tenant_id] = current_burst + 1

        return allow()

    def check_cost(self, tenant_id: str, operation: str) -> ProtectionResult:
        """
        Check cost guard for a tenant/operation combination.

        Mock behavior: Read limits from billing provider, check daily cost.
        """
        # Get billing limits
        billing = get_billing_provider()
        plan = billing.get_plan(tenant_id)
        limits = billing.get_limits(plan)

        # If no cost limit, allow
        if limits.max_monthly_cost_usd is None:
            return allow()

        # Get daily cost (approximation: monthly / 30)
        daily_limit = limits.max_monthly_cost_usd / 30.0
        current_cost = self._daily_costs.get(tenant_id, 0.0)

        if current_cost >= daily_limit:
            return reject_cost_limit(
                current_value=current_cost,
                allowed_value=daily_limit,
                message=f"Daily cost limit exceeded: ${current_cost:.2f}/${daily_limit:.2f}",
            )

        return allow()

    def detect_anomaly(self, tenant_id: str) -> Optional[AnomalySignal]:
        """
        Detect usage anomaly for a tenant.

        Mock behavior: Check if request count exceeds 10x baseline.
        Per ABUSE-003, this never blocks - just signals.
        """
        # Count total requests for tenant
        if tenant_id not in self._request_counts:
            return None

        total_requests = sum(self._request_counts[tenant_id].values())

        # Check for anomaly (10x baseline)
        if total_requests > self._baseline_requests * self._anomaly_multiplier:
            return AnomalySignal(
                baseline=self._baseline_requests,
                observed=float(total_requests),
                window="5m",
                severity="high" if total_requests > self._baseline_requests * 20 else "medium",
            )

        return None

    def check_all(self, tenant_id: str, endpoint: str, operation: str) -> ProtectionResult:
        """
        Run all protection checks in order.

        ORDER (LOCKED):
        1. Rate limit
        2. Burst control
        3. Cost guard
        4. Anomaly detection (non-blocking)
        """
        # 1. Rate limit
        result = self.check_rate_limit(tenant_id, endpoint)
        if result.decision == Decision.REJECT:
            logger.info(f"Protection REJECT for {tenant_id}: rate limit")
            return result

        # 2. Burst control
        result = self.check_burst(tenant_id, endpoint)
        if result.decision in (Decision.REJECT, Decision.THROTTLE):
            logger.info(f"Protection {result.decision.value} for {tenant_id}: burst")
            return result

        # 3. Cost guard
        result = self.check_cost(tenant_id, operation)
        if result.decision == Decision.REJECT:
            logger.info(f"Protection REJECT for {tenant_id}: cost")
            return result

        # 4. Anomaly detection (non-blocking per ABUSE-003)
        anomaly = self.detect_anomaly(tenant_id)
        if anomaly:
            logger.warning(
                f"Anomaly detected for {tenant_id}: {anomaly.observed}/{anomaly.baseline} "
                f"({anomaly.window})"
            )
            # Anomaly is non-blocking - return ALLOW but could emit signal

        return allow()

    # ==========================================================================
    # Mock-specific methods (for testing only, not part of protocol)
    # ==========================================================================

    def add_cost(self, tenant_id: str, amount: float) -> None:
        """Add cost to tenant's daily accumulator (mock/test only)."""
        current = self._daily_costs.get(tenant_id, 0.0)
        self._daily_costs[tenant_id] = current + amount

    def reset(self) -> None:
        """Reset all mock state (for testing)."""
        self._request_counts.clear()
        self._request_timestamps.clear()
        self._burst_counts.clear()
        self._burst_second.clear()
        self._daily_costs.clear()

    def reset_rate_limits(self, tenant_id: str) -> None:
        """Reset rate limits for a tenant (for testing)."""
        if tenant_id in self._request_counts:
            del self._request_counts[tenant_id]


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global protection provider instance
_protection_provider: Optional[AbuseProtectionProvider] = None


def get_protection_provider() -> AbuseProtectionProvider:
    """
    Get the abuse protection provider instance.

    Returns MockAbuseProtectionProvider by default.
    Can be replaced for testing or production.
    """
    global _protection_provider
    if _protection_provider is None:
        _protection_provider = MockAbuseProtectionProvider()
    return _protection_provider


def set_protection_provider(provider: AbuseProtectionProvider) -> None:
    """
    Set the abuse protection provider instance.

    Used for testing or to swap in a real provider.
    """
    global _protection_provider
    _protection_provider = provider


__all__ = [
    "AbuseProtectionProvider",
    "MockAbuseProtectionProvider",
    "get_protection_provider",
    "set_protection_provider",
]
