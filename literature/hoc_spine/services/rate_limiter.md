# rate_limiter.py

**Path:** `backend/app/hoc/hoc_spine/services/rate_limiter.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            rate_limiter.py
Lives in:        services/
Role:            Services
Inbound:         middleware, API routes
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Rate limiting utilities (Redis-backed)
Violations:      none
```

## Purpose

Rate limiting utilities (Redis-backed)

## Import Analysis

**External:**
- `redis`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_rate_limiter() -> RateLimiter`

Get the singleton rate limiter instance.

### `allow_request(key: str, rate_per_min: int) -> bool`

Convenience function to check rate limit.

Args:
    key: Rate limit key
    rate_per_min: Max requests per minute

Returns:
    True if allowed

## Classes

### `RateLimiter`

Token bucket rate limiter using Redis.

Provides per-key rate limiting with configurable RPM.
Falls back to allowing requests if Redis is unavailable.

#### Methods

- `__init__(redis_url: Optional[str], fail_open: bool)` — Initialize rate limiter.
- `_get_client()` — Lazy-load Redis client.
- `allow(key: str, rate_per_min: int) -> bool` — Check if request should be allowed.
- `get_remaining(key: str, rate_per_min: int) -> int` — Get remaining tokens for a key.

## Domain Usage

**Callers:** middleware, API routes

## Export Contract

```yaml
exports:
  functions:
    - name: get_rate_limiter
      signature: "get_rate_limiter() -> RateLimiter"
      consumers: ["orchestrator"]
    - name: allow_request
      signature: "allow_request(key: str, rate_per_min: int) -> bool"
      consumers: ["orchestrator"]
  classes:
    - name: RateLimiter
      methods:
        - allow
        - get_remaining
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['redis']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

