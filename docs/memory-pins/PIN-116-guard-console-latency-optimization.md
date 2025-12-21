# PIN-116: Guard Console Latency Optimization

**Status:** COMPLETE
**Created:** 2025-12-21
**Category:** Performance / Backend
**Milestone:** M23.2 Performance
**Related PINs:** PIN-115, PIN-100

---

## Summary

Implemented Redis caching layer for Guard Console API endpoints to reduce latency from 4-7 seconds to ~300ms (94% improvement). Root cause was cross-region database queries (EU server -> Singapore Neon DB).

---

## Problem

Guard Console was extremely slow:
- `/guard/status`: 4-7 seconds
- `/guard/snapshot/today`: 2-6 seconds

### Root Cause Analysis

```
Server Location: Europe (2a02:c207:...)
Database Location: Singapore (ap-southeast-1)
Network Latency: ~200-400ms per query round-trip
```

Each endpoint executed 4-5 sequential database queries:
- `get_guard_status`: 4 queries (tenant state, guardrails, incident count, last incident)
- `get_today_snapshot`: 5 queries (request count, spend sum, blocked count, blocked sum, last incident)

**Total latency**: 5 queries × 400ms = 2-7 seconds

---

## Solution

### 1. Redis Cache Layer

Created `backend/app/utils/guard_cache.py`:

```python
class GuardCache:
    """Redis-based cache for Guard Console API."""

    async def get_status(self, tenant_id: str) -> Optional[Dict]
    async def set_status(self, tenant_id: str, data: Dict) -> bool
    async def get_snapshot(self, tenant_id: str) -> Optional[Dict]
    async def set_snapshot(self, tenant_id: str, data: Dict) -> bool
    async def invalidate_tenant(self, tenant_id: str) -> int
```

### 2. Cache Configuration

| Endpoint | Cache Key | TTL |
|----------|-----------|-----|
| `/guard/status` | `guard:status:{tenant_id}` | 5 seconds |
| `/guard/snapshot/today` | `guard:snapshot:{tenant_id}` | 10 seconds |
| `/guard/incidents` | `guard:incidents:{tenant_id}:{limit}:{offset}` | 5 seconds |

### 3. Query Optimization

Reduced snapshot queries from 5 to 3 by combining aggregations:

```python
# Before: 5 separate queries
# After: 3 combined queries
stmt = select(
    func.count(ProxyCall.id),
    func.coalesce(func.sum(ProxyCall.cost_cents), 0)
).where(...)
```

### 4. Cache Invalidation

Automatic invalidation on mutations:
- `POST /guard/killswitch/activate`
- `POST /guard/killswitch/deactivate`

```python
# In mutation endpoints
cache = get_guard_cache()
await cache.invalidate_tenant(tenant_id)
```

### 5. Frontend Optimization

Added `staleTime` to prevent unnecessary refetches:

```typescript
const { data: status } = useQuery({
  queryKey: ['guard', 'status'],
  queryFn: guardApi.getStatus,
  refetchInterval: 5000,
  staleTime: 4000,  // Fresh for 4s (< 5s cache TTL)
});
```

---

## Performance Results

### Before (No Cache)

| Endpoint | Latency |
|----------|---------|
| `/guard/status` | 4-7 seconds |
| `/guard/snapshot/today` | 2-6 seconds |

### After (With Cache)

| Request Type | Latency | Improvement |
|--------------|---------|-------------|
| Cold cache (first request) | 1.8-2.2s | 50% |
| Warm cache (subsequent) | 0.28-0.33s | **94%** |

---

## Files Changed

### New Files
```
backend/app/utils/guard_cache.py    # Redis cache utility
```

### Modified Files
```
backend/app/api/guard.py           # Added cache checks + invalidation
website/.../GuardDashboard.tsx     # Added staleTime
website/.../GuardLayout.tsx        # Added staleTime
```

---

## Prometheus Metrics

New metrics for cache observability:

```
aos_guard_cache_hits_total{endpoint="status"}
aos_guard_cache_misses_total{endpoint="status"}
aos_guard_cache_latency_seconds
```

---

## Environment Variables

```bash
GUARD_CACHE_ENABLED=true      # Enable/disable caching
GUARD_STATUS_TTL=5            # Status cache TTL (seconds)
GUARD_SNAPSHOT_TTL=10         # Snapshot cache TTL (seconds)
GUARD_INCIDENTS_TTL=5         # Incidents cache TTL (seconds)
```

---

## Testing

```bash
# Cold cache (first request)
curl -w "%{time_total}s" "https://agenticverz.com/guard/status?tenant_id=tenant_demo" \
  -H "X-API-Key: $API_KEY"
# Result: ~2s

# Warm cache (subsequent requests)
curl -w "%{time_total}s" "https://agenticverz.com/guard/status?tenant_id=tenant_demo" \
  -H "X-API-Key: $API_KEY"
# Result: ~0.3s
```

---

## Architecture

```
Browser
   │
   ▼
Apache (proxy)
   │
   ▼
FastAPI (EU)
   │
   ├──► Redis (Upstash) ──► Cache Hit → Return immediately (~50ms)
   │
   └──► Cache Miss
          │
          ▼
       Neon DB (Singapore) → ~400ms per query
          │
          ▼
       Cache result in Redis
          │
          ▼
       Return response
```

---

## Lessons Learned

1. **Cross-region DB queries are expensive** - Always consider geographic latency
2. **Cache at the API layer** - Not just the database layer
3. **Short TTL is fine for real-time data** - 5-10s caching still provides huge benefits
4. **Invalidate on mutations** - Ensures data consistency
5. **Combine queries** - Reduce round-trips when possible

---

## Next Steps

1. Consider moving to a regional database replica
2. Add cache warming on application startup
3. Implement cache-aside pattern for incidents list
4. Add Grafana dashboard for cache metrics
