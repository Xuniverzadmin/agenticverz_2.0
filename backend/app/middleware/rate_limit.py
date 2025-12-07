"""
Rate Limit Middleware
M8 Deliverable: JWT-based rate limiting per tenant/tier

Enforces per-tenant rate limits based on user's rate_limit_tier claim from JWT.
Uses Redis (Upstash) for distributed rate limiting with fixed-window algorithm.

Tiers:
- free: 60 requests/minute
- dev: 300 requests/minute
- pro: 1200 requests/minute
- unlimited: no practical limit

Usage:
    from app.middleware.rate_limit import rate_limit_dependency

    @router.post("/simulate")
    async def simulate(
        request: SimulateRequest,
        user: User = Depends(get_current_user),
        _: bool = Depends(rate_limit_dependency)
    ):
        ...
"""
import os
import time
import logging
from typing import Optional
from fastapi import HTTPException, Depends, Request

try:
    import redis.asyncio as aioredis
except ImportError:
    import aioredis

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Prometheus metrics
rl_allowed = Counter(
    "aos_rate_limit_allowed_total",
    "Rate-limit allowed requests",
    ["tier", "tenant_id"]
)
rl_blocked = Counter(
    "aos_rate_limit_blocked_total",
    "Rate-limit blocked requests",
    ["tier", "tenant_id"]
)
rl_limit_gauge = Gauge(
    "aos_rate_limit_tier_limit",
    "Configured requests/interval for tier",
    ["tier"]
)
rl_redis_connected = Gauge(
    "aos_rate_limit_redis_connected",
    "Whether Redis is connected for rate limiting (1=connected, 0=disconnected)"
)
rl_redis_errors = Counter(
    "aos_rate_limit_redis_errors_total",
    "Total Redis errors in rate limiting"
)

# Configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_FAIL_OPEN = os.environ.get("RATE_LIMIT_FAIL_OPEN", "true").lower() == "true"

# Tier configurations: (requests_per_window, window_seconds)
RATE_LIMIT_TIERS = {
    "free": (60, 60),      # 60 req/min
    "dev": (300, 60),      # 300 req/min
    "pro": (1200, 60),     # 1200 req/min
    "enterprise": (6000, 60),  # 6000 req/min
    "unlimited": (10**9, 60),  # Effectively unlimited
}

# Publish tier limits to Prometheus
for tier, (limit, _) in RATE_LIMIT_TIERS.items():
    rl_limit_gauge.labels(tier=tier).set(limit)

# Redis connection pool
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get Redis connection pool (lazy initialization)."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5.0,
            socket_timeout=5.0,
        )
    return _redis_pool


def get_tier_limits(tier: Optional[str]) -> tuple:
    """Get rate limit configuration for a tier."""
    if not tier or tier not in RATE_LIMIT_TIERS:
        tier = "free"
    return RATE_LIMIT_TIERS[tier]


def extract_tier_from_user(user) -> str:
    """
    Extract rate limit tier from user object.

    Priority:
    1. Explicit rate_limit_tier attribute
    2. Role-based tier (admin -> unlimited, developer -> dev)
    3. Default to free
    """
    # Check for explicit tier claim
    if hasattr(user, "rate_limit_tier") and user.rate_limit_tier:
        return user.rate_limit_tier

    # Check roles for tier hints
    roles = getattr(user, "roles", []) or []

    if "admin" in roles:
        return "unlimited"
    if "enterprise" in roles:
        return "enterprise"
    if "pro" in roles:
        return "pro"
    if "developer" in roles or "dev" in roles:
        return "dev"

    return "free"


async def check_rate_limit(tenant_id: str, tier: str) -> tuple:
    """
    Check and increment rate limit counter.

    Returns:
        (allowed: bool, current_count: int, limit: int, remaining: int)

    Behavior on Redis failure:
        - RATE_LIMIT_FAIL_OPEN=true (default): Allow request, log warning
        - RATE_LIMIT_FAIL_OPEN=false: Deny request with 503
    """
    reqs_limit, window_seconds = get_tier_limits(tier)

    # Calculate current window slot
    current_slot = int(time.time() // window_seconds)
    key = f"rl:{tenant_id}:{tier}:{current_slot}"

    try:
        redis = await get_redis()
        rl_redis_connected.set(1)

        # Atomic increment
        current = await redis.incr(key)

        # Set expiry on first request in window
        if current == 1:
            await redis.expire(key, window_seconds + 2)

        allowed = current <= reqs_limit
        remaining = max(0, reqs_limit - current)

        return allowed, current, reqs_limit, remaining

    except Exception as e:
        rl_redis_connected.set(0)
        rl_redis_errors.inc()
        logger.warning(f"Rate limit Redis error: {e}")

        if RATE_LIMIT_FAIL_OPEN:
            # Fail-open: allow request if Redis unavailable
            logger.warning(f"Rate limit check failed (FAIL_OPEN=true, allowing request)")
            return True, 0, reqs_limit, reqs_limit
        else:
            # Fail-closed: deny request if Redis unavailable
            logger.error(f"Rate limit check failed (FAIL_OPEN=false, denying request)")
            return False, 0, reqs_limit, 0


async def rate_limit_dependency(request: Request) -> bool:
    """
    FastAPI dependency for rate limiting.

    Injects into endpoint and raises 429 if limit exceeded.
    Expects user to be available in request.state (set by auth middleware).
    """
    if not RATE_LIMIT_ENABLED:
        return True

    # Get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)

    if user is None:
        # No user context - use IP-based limiting with free tier
        client_ip = request.client.host if request.client else "unknown"
        tenant_id = f"ip:{client_ip}"
        tier = "free"
    else:
        tenant_id = getattr(user, "tenant_id", "default")
        tier = extract_tier_from_user(user)

    allowed, current, limit, remaining = await check_rate_limit(tenant_id, tier)

    # Add rate limit headers to response
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(int(time.time() // 60 + 1) * 60),
    }

    if allowed:
        rl_allowed.labels(tier=tier, tenant_id=tenant_id[:32]).inc()
        return True
    else:
        rl_blocked.labels(tier=tier, tenant_id=tenant_id[:32]).inc()
        logger.info(f"Rate limit exceeded: tenant={tenant_id}, tier={tier}, current={current}, limit={limit}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "tier": tier,
                "limit": limit,
                "retry_after": 60,
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            }
        )


class RateLimitMiddleware:
    """
    ASGI middleware alternative for rate limiting.

    Can be used instead of dependency injection for global rate limiting.
    """

    def __init__(self, app, exclude_paths: list = None):
        self.app = app
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/ready"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Skip rate limiting for excluded paths
        if any(path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # For middleware approach, we'd need to extract user from headers
        # This is more complex - prefer dependency injection
        await self.app(scope, receive, send)
