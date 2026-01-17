"""Customer LLM Enforcement Client

PURPOSE:
    Client-side enforcement adapter that consumes backend decisions
    and applies local behavior (allow, warn, throttle, block).

RESPONSIBILITIES:
    - Fetch enforcement decisions from AOS backend
    - Cache decisions for performance
    - Apply enforcement behavior locally
    - Emit enforcement signals/events

DESIGN PRINCIPLES:
    1. AUTHORITY SERVER-SIDE: All decisions come from backend
    2. EXECUTION CLIENT-SIDE: SDK applies the behavior
    3. DETERMINISTIC: Same decision → same behavior
    4. EXPLICIT: All blocked/throttled calls raise explicit exceptions

USAGE:
    enforcer = CusEnforcer(base_url="https://api.agenticverz.com")

    # Pre-flight check
    decision = enforcer.check(
        tenant_id="...",
        integration_id="...",
        estimated_cost_cents=100,
        estimated_tokens=1000,
    )

    if decision.is_blocked:
        raise decision.to_exception()

    # Or use with context manager
    with enforcer.enforce(tenant_id, integration_id) as ctx:
        # Make LLM call here
        response = client.chat.completions.create(...)
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EnforcementResult(str, Enum):
    """Enforcement decision result (mirrors backend)."""

    HARD_BLOCKED = "hard_blocked"
    BLOCKED = "blocked"
    THROTTLED = "throttled"
    WARNED = "warned"
    ALLOWED = "allowed"


@dataclass
class EnforcementReason:
    """Explanation for an enforcement decision."""

    code: str
    message: str
    limit_type: Optional[str] = None
    limit_value: Optional[int] = None
    current_value: Optional[int] = None
    threshold_percent: Optional[float] = None
    retry_after_seconds: Optional[int] = None


@dataclass
class EnforcementDecision:
    """Client-side enforcement decision."""

    result: EnforcementResult
    integration_id: str
    tenant_id: str
    reasons: List[EnforcementReason] = field(default_factory=list)
    degraded: bool = False
    evaluated_at: Optional[datetime] = None
    cached: bool = False

    @property
    def is_allowed(self) -> bool:
        """Check if the call is allowed."""
        return self.result in (EnforcementResult.ALLOWED, EnforcementResult.WARNED)

    @property
    def is_blocked(self) -> bool:
        """Check if the call is blocked (hard or soft)."""
        return self.result in (
            EnforcementResult.HARD_BLOCKED,
            EnforcementResult.BLOCKED,
        )

    @property
    def is_throttled(self) -> bool:
        """Check if the call should be throttled."""
        return self.result == EnforcementResult.THROTTLED

    @property
    def is_warned(self) -> bool:
        """Check if a warning should be emitted."""
        return self.result == EnforcementResult.WARNED

    @property
    def retry_after_seconds(self) -> Optional[int]:
        """Get retry-after value if throttled."""
        for reason in self.reasons:
            if reason.retry_after_seconds:
                return reason.retry_after_seconds
        return None

    @property
    def primary_reason(self) -> Optional[EnforcementReason]:
        """Get the primary (first) reason."""
        return self.reasons[0] if self.reasons else None

    def to_exception(self) -> "EnforcementError":
        """Convert to an exception for raising."""
        return EnforcementError(decision=self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnforcementDecision":
        """Create from API response dict."""
        reasons = [
            EnforcementReason(
                code=r["code"],
                message=r["message"],
                limit_type=r.get("limit_type"),
                limit_value=r.get("limit_value"),
                current_value=r.get("current_value"),
                threshold_percent=r.get("threshold_percent"),
                retry_after_seconds=r.get("retry_after_seconds"),
            )
            for r in data.get("reasons", [])
        ]

        evaluated_at = None
        if data.get("evaluated_at"):
            try:
                evaluated_at = datetime.fromisoformat(
                    data["evaluated_at"].replace("Z", "+00:00")
                )
            except Exception:
                pass

        return cls(
            result=EnforcementResult(data["result"]),
            integration_id=data["integration_id"],
            tenant_id=data["tenant_id"],
            reasons=reasons,
            degraded=data.get("degraded", False),
            evaluated_at=evaluated_at,
        )


class EnforcementError(Exception):
    """Exception raised when enforcement blocks a call."""

    def __init__(self, decision: EnforcementDecision):
        self.decision = decision
        self.result = decision.result
        self.reasons = decision.reasons

        # Build message
        reason = decision.primary_reason
        if reason:
            message = f"[{decision.result.value}] {reason.message}"
        else:
            message = f"[{decision.result.value}] Enforcement blocked this call"

        super().__init__(message)

    @property
    def is_hard_blocked(self) -> bool:
        """Check if this is a hard block (no retry)."""
        return self.result == EnforcementResult.HARD_BLOCKED

    @property
    def is_soft_blocked(self) -> bool:
        """Check if this is a soft block (can retry later)."""
        return self.result == EnforcementResult.BLOCKED

    @property
    def retry_after_seconds(self) -> Optional[int]:
        """Get retry-after value if available."""
        return self.decision.retry_after_seconds


class ThrottleError(EnforcementError):
    """Exception raised when enforcement throttles a call."""

    pass


@dataclass
class CachedDecision:
    """Cached enforcement decision with TTL."""

    decision: EnforcementDecision
    cached_at: datetime
    ttl_seconds: int = 5

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        age = datetime.now(timezone.utc) - self.cached_at
        return age.total_seconds() > self.ttl_seconds


class CusEnforcer:
    """Client-side enforcement adapter.

    Consumes backend decisions and applies local behavior.
    """

    DEFAULT_TIMEOUT = 5.0  # seconds
    DEFAULT_CACHE_TTL = 5  # seconds

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        on_warn: Optional[Callable[[EnforcementDecision], None]] = None,
        on_block: Optional[Callable[[EnforcementDecision], None]] = None,
        on_throttle: Optional[Callable[[EnforcementDecision], None]] = None,
    ):
        """Initialize enforcer.

        Args:
            base_url: AOS API base URL
            api_key: API key for authentication
            timeout: Request timeout in seconds
            cache_ttl: Cache TTL in seconds for decisions
            on_warn: Callback for warning decisions
            on_block: Callback for block decisions
            on_throttle: Callback for throttle decisions
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._cache_ttl = cache_ttl
        self._cache: Dict[str, CachedDecision] = {}

        # Callbacks
        self._on_warn = on_warn
        self._on_block = on_block
        self._on_throttle = on_throttle

    def _cache_key(self, tenant_id: str, integration_id: str) -> str:
        """Generate cache key."""
        return f"{tenant_id}:{integration_id}"

    def _get_cached(
        self, tenant_id: str, integration_id: str
    ) -> Optional[EnforcementDecision]:
        """Get cached decision if valid."""
        key = self._cache_key(tenant_id, integration_id)
        cached = self._cache.get(key)

        if cached and not cached.is_expired:
            decision = cached.decision
            decision.cached = True
            return decision

        # Clean up expired entry
        if cached:
            del self._cache[key]

        return None

    def _set_cached(self, decision: EnforcementDecision) -> None:
        """Cache a decision."""
        key = self._cache_key(decision.tenant_id, decision.integration_id)
        self._cache[key] = CachedDecision(
            decision=decision,
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=self._cache_ttl,
        )

    def check(
        self,
        tenant_id: str,
        integration_id: str,
        estimated_cost_cents: int = 0,
        estimated_tokens: int = 0,
        use_cache: bool = True,
    ) -> EnforcementDecision:
        """Check enforcement policy (synchronous).

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID
            estimated_cost_cents: Estimated cost of the call
            estimated_tokens: Estimated tokens for the call
            use_cache: Whether to use cached decisions

        Returns:
            EnforcementDecision

        Raises:
            httpx.HTTPError: On network errors
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached(tenant_id, integration_id)
            if cached:
                return cached

        # Make API call
        url = f"{self._base_url}/api/v1/enforcement/check"
        headers = {}
        if self._api_key:
            headers["X-AOS-Key"] = self._api_key
        headers["X-Tenant-ID"] = tenant_id

        payload = {
            "integration_id": integration_id,
            "estimated_cost_cents": estimated_cost_cents,
            "estimated_tokens": estimated_tokens,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                decision = EnforcementDecision.from_dict(data.get("data", data))

                # Cache the decision
                if use_cache:
                    self._set_cached(decision)

                return decision

        except httpx.HTTPError as e:
            logger.warning(f"Enforcement check failed: {e}")
            # On failure, allow with degraded flag
            return EnforcementDecision(
                result=EnforcementResult.ALLOWED,
                integration_id=integration_id,
                tenant_id=tenant_id,
                reasons=[
                    EnforcementReason(
                        code="check_failed",
                        message=f"Enforcement check failed: {e}",
                    )
                ],
                degraded=True,
            )

    def enforce(
        self,
        tenant_id: str,
        integration_id: str,
        estimated_cost_cents: int = 0,
        estimated_tokens: int = 0,
        raise_on_block: bool = True,
        throttle_wait: bool = True,
    ) -> EnforcementDecision:
        """Check and enforce policy.

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID
            estimated_cost_cents: Estimated cost
            estimated_tokens: Estimated tokens
            raise_on_block: Raise exception if blocked
            throttle_wait: Wait if throttled (vs raise)

        Returns:
            EnforcementDecision

        Raises:
            EnforcementError: If blocked and raise_on_block=True
            ThrottleError: If throttled and throttle_wait=False
        """
        decision = self.check(
            tenant_id=tenant_id,
            integration_id=integration_id,
            estimated_cost_cents=estimated_cost_cents,
            estimated_tokens=estimated_tokens,
        )

        # Handle decision
        if decision.is_warned and self._on_warn:
            self._on_warn(decision)

        if decision.is_blocked:
            if self._on_block:
                self._on_block(decision)
            if raise_on_block:
                raise decision.to_exception()

        if decision.is_throttled:
            if self._on_throttle:
                self._on_throttle(decision)

            retry_after = decision.retry_after_seconds or 60

            if throttle_wait:
                logger.info(f"Throttled - waiting {retry_after}s before retry")
                time.sleep(retry_after)
                # Retry after waiting
                return self.enforce(
                    tenant_id=tenant_id,
                    integration_id=integration_id,
                    estimated_cost_cents=estimated_cost_cents,
                    estimated_tokens=estimated_tokens,
                    raise_on_block=raise_on_block,
                    throttle_wait=False,  # Don't wait again
                )
            else:
                raise ThrottleError(decision)

        return decision

    def get_status(
        self,
        tenant_id: str,
        integration_id: str,
    ) -> Dict[str, Any]:
        """Get current enforcement status (limits and usage).

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID

        Returns:
            Status dict with limits and usage
        """
        url = f"{self._base_url}/api/v1/enforcement/status"
        headers = {}
        if self._api_key:
            headers["X-AOS-Key"] = self._api_key
        headers["X-Tenant-ID"] = tenant_id

        params = {"integration_id": integration_id}

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("data", data)

        except httpx.HTTPError as e:
            logger.warning(f"Status check failed: {e}")
            return {"error": str(e)}

    def clear_cache(self, tenant_id: Optional[str] = None) -> int:
        """Clear cached decisions.

        Args:
            tenant_id: If provided, only clear for this tenant

        Returns:
            Number of entries cleared
        """
        if tenant_id:
            keys_to_remove = [
                k for k in self._cache.keys() if k.startswith(f"{tenant_id}:")
            ]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)
        else:
            count = len(self._cache)
            self._cache.clear()
            return count


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_default_enforcer: Optional[CusEnforcer] = None


def configure_enforcer(
    base_url: str,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> CusEnforcer:
    """Configure the default enforcer.

    Args:
        base_url: AOS API base URL
        api_key: API key for authentication
        **kwargs: Additional arguments for CusEnforcer

    Returns:
        Configured enforcer
    """
    global _default_enforcer
    _default_enforcer = CusEnforcer(base_url=base_url, api_key=api_key, **kwargs)
    return _default_enforcer


def get_enforcer() -> Optional[CusEnforcer]:
    """Get the default enforcer."""
    return _default_enforcer


def check_enforcement(
    tenant_id: str,
    integration_id: str,
    estimated_cost_cents: int = 0,
    estimated_tokens: int = 0,
) -> EnforcementDecision:
    """Check enforcement using default enforcer.

    Args:
        tenant_id: Tenant ID
        integration_id: Integration ID
        estimated_cost_cents: Estimated cost
        estimated_tokens: Estimated tokens

    Returns:
        EnforcementDecision

    Raises:
        RuntimeError: If enforcer not configured
    """
    if not _default_enforcer:
        raise RuntimeError("Enforcer not configured. Call configure_enforcer() first.")

    return _default_enforcer.check(
        tenant_id=tenant_id,
        integration_id=integration_id,
        estimated_cost_cents=estimated_cost_cents,
        estimated_tokens=estimated_tokens,
    )


def enforce(
    tenant_id: str,
    integration_id: str,
    estimated_cost_cents: int = 0,
    estimated_tokens: int = 0,
    raise_on_block: bool = True,
) -> EnforcementDecision:
    """Enforce policy using default enforcer.

    Args:
        tenant_id: Tenant ID
        integration_id: Integration ID
        estimated_cost_cents: Estimated cost
        estimated_tokens: Estimated tokens
        raise_on_block: Raise if blocked

    Returns:
        EnforcementDecision

    Raises:
        RuntimeError: If enforcer not configured
        EnforcementError: If blocked
    """
    if not _default_enforcer:
        raise RuntimeError("Enforcer not configured. Call configure_enforcer() first.")

    return _default_enforcer.enforce(
        tenant_id=tenant_id,
        integration_id=integration_id,
        estimated_cost_cents=estimated_cost_cents,
        estimated_tokens=estimated_tokens,
        raise_on_block=raise_on_block,
    )
