# PIN-040: Rate Limit Middleware

**Status:** COMPLETE
**Created:** 2025-12-06
**Category:** Security / API Protection
**Exclusivity:** This PIN describes an exclusive component - only one rate limit implementation should exist

---

## Overview

JWT-based per-tenant rate limiting middleware for AOS API endpoints. Uses Redis (Upstash) for distributed rate limiting with fixed-window algorithm.

---

## Implementation

**Primary File:** `backend/app/middleware/rate_limit.py`

### Rate Limit Tiers

| Tier | Requests/Minute | Use Case |
|------|-----------------|----------|
| free | 60 | Anonymous / unauthenticated |
| dev | 300 | Developer accounts |
| pro | 1200 | Pro tier customers |
| enterprise | 6000 | Enterprise customers |
| unlimited | 10^9 | Admin / internal |

### Tier Resolution Priority

1. Explicit `rate_limit_tier` claim in JWT
2. Role-based: admin → unlimited, enterprise → enterprise, pro → pro, developer → dev
3. Default: free

### Algorithm

Fixed-window rate limiting:
- Window size: 60 seconds
- Key format: `rl:{tenant_id}:{tier}:{window_slot}`
- Redis INCR for atomic counting
- TTL set on first request in window

### Fail-Open Behavior

If Redis is unavailable, requests are **allowed** (fail-open). This prioritizes availability over strict enforcement. A warning is logged.

---

## API Integration

### Protected Endpoints

| Endpoint | Dependency |
|----------|------------|
| `POST /api/v1/runtime/simulate` | `rate_limit_dependency` |
| `POST /api/v1/runtime/replay/{run_id}` | `rate_limit_dependency` |

### Response Headers

All responses include:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1733506800
```

### 429 Response

When limit exceeded:
```json
{
  "error": "rate_limit_exceeded",
  "tier": "free",
  "limit": 60,
  "retry_after": 60
}
```

Headers: `Retry-After: 60`

---

## Prometheus Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `aos_rate_limit_allowed_total` | Counter | tier, tenant_id |
| `aos_rate_limit_blocked_total` | Counter | tier, tenant_id |
| `aos_rate_limit_tier_limit` | Gauge | tier |

---

## Configuration

Environment variables:
```bash
REDIS_URL=rediss://...@upstash.io:6379
RATE_LIMIT_ENABLED=true  # Set false to disable
```

---

## Testing

```bash
# Unit test
PYTHONPATH=. python3 -c "
from app.middleware.rate_limit import get_tier_limits, RATE_LIMIT_TIERS
print('Tiers:', list(RATE_LIMIT_TIERS.keys()))
print('Free limits:', get_tier_limits('free'))
"

# Integration test
curl -X POST http://localhost:8000/api/v1/runtime/simulate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan": [{"skill": "http_call", "params": {}}]}'
# Check X-RateLimit-* headers
```

---

## Exclusivity Notes

This is the **authoritative** rate limiting implementation for AOS. Do not:
- Create alternative rate limiting middleware
- Add rate limiting at nginx/reverse proxy (handled here)
- Duplicate tier logic elsewhere

Any changes to rate limiting must update this PIN.

---

## Related

- PIN-038: Upstash Redis Integration (backend)
- PIN-039: M8 Implementation Progress (parent)
