# guard_cache.py

**Path:** `backend/app/hoc/cus/hoc_spine/drivers/guard_cache.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            guard_cache.py
Lives in:        drivers/
Role:            Drivers
Inbound:         guard API
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Redis-based cache for Guard Console endpoints.
Violations:      none
```

## Purpose

Redis-based cache for Guard Console endpoints.

Reduces database query latency by caching frequently-accessed data.
Critical for cross-region deployments (EU server, Singapore DB).

Cache Keys:
- guard:status:{tenant_id} - 5s TTL (real-time status)
- guard:snapshot:{tenant_id} - 10s TTL (today's metrics)
- guard:incidents:{tenant_id}:{limit}:{offset} - 5s TTL

Performance Target:
- Reduce /guard/status from 4-7s to <100ms (cache hit)
- Reduce /guard/snapshot/today from 2-6s to <100ms (cache hit)

## Import Analysis

**External:**
- `metrics_helpers`
- `redis.asyncio`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_guard_cache() -> GuardCache`

Get guard cache singleton.

## Classes

### `GuardCache`

Redis-based cache for Guard Console API.

Usage:
    cache = GuardCache()

    # Check cache first
    data = await cache.get_status(tenant_id)
    if data is None:
        data = fetch_from_db(...)
        await cache.set_status(tenant_id, data)

#### Methods

- `__init__(redis_client)` — _No docstring._
- `get_instance() -> 'GuardCache'` — Get singleton instance.
- `async _get_redis()` — Get Redis client, initializing if needed.
- `_make_key(endpoint: str, tenant_id: str, extra: str) -> str` — Generate cache key.
- `async get(endpoint: str, tenant_id: str, extra: str) -> Optional[Dict]` — Get cached data.
- `async set(endpoint: str, tenant_id: str, data: Dict, ttl: int, extra: str) -> bool` — Set cached data.
- `async invalidate(endpoint: str, tenant_id: str, extra: str) -> bool` — Invalidate cached data.
- `async get_status(tenant_id: str) -> Optional[Dict]` — Get cached guard status.
- `async set_status(tenant_id: str, data: Dict) -> bool` — Cache guard status.
- `async get_snapshot(tenant_id: str) -> Optional[Dict]` — Get cached today snapshot.
- `async set_snapshot(tenant_id: str, data: Dict) -> bool` — Cache today snapshot.
- `async get_incidents(tenant_id: str, limit: int, offset: int) -> Optional[Dict]` — Get cached incidents list.
- `async set_incidents(tenant_id: str, data: Dict, limit: int, offset: int) -> bool` — Cache incidents list.
- `async invalidate_tenant(tenant_id: str) -> int` — Invalidate all cache for a tenant (on mutations).

## Domain Usage

**Callers:** guard API

## Export Contract

```yaml
exports:
  functions:
    - name: get_guard_cache
      signature: "get_guard_cache() -> GuardCache"
      consumers: ["orchestrator"]
  classes:
    - name: GuardCache
      methods:
        - get_instance
        - get
        - set
        - invalidate
        - get_status
        - set_status
        - get_snapshot
        - set_snapshot
        - get_incidents
        - set_incidents
        - invalidate_tenant
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['metrics_helpers', 'redis.asyncio']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

