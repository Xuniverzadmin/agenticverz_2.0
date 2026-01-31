# pool_manager.py

**Path:** `backend/app/hoc/hoc_spine/orchestrator/lifecycle/engines/pool_manager.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            pool_manager.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         Services, API routes
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Connection Pool Manager (GAP-172)
Violations:      none
```

## Purpose

Connection Pool Manager (GAP-172)

Manages connection pools for various services with:
- Health checking
- Per-tenant limits
- Metrics
- Graceful shutdown

## Import Analysis

**External:**
- `httpx`
- `asyncpg`
- `redis.asyncio`
- `redis.asyncio`
- `redis.asyncio`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `PoolType(str, Enum)`

Types of connection pools.

### `PoolStatus(str, Enum)`

Pool health status.

### `PoolConfig`

Configuration for a connection pool.

### `PoolStats`

Statistics for a connection pool.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `PoolHandle`

Handle to a managed connection pool.

### `ConnectionPoolManager`

Unified connection pool manager.

Features:
- Manages multiple pool types (database, redis, http)
- Health checking with automatic status updates
- Per-tenant connection limits
- Graceful shutdown
- Metrics collection

#### Methods

- `__init__()` — _No docstring._
- `async start() -> None` — Start the pool manager.
- `async stop() -> None` — Stop all pools and cleanup.
- `async create_database_pool(pool_id: str, connection_string: Optional[str], min_size: int, max_size: int, max_connections_per_tenant: Optional[int]) -> PoolHandle` — Create a PostgreSQL connection pool.
- `async create_redis_pool(pool_id: str, redis_url: Optional[str], max_connections: int) -> PoolHandle` — Create a Redis connection pool.
- `async create_http_pool(pool_id: str, base_url: Optional[str], max_connections: int, timeout_seconds: float) -> PoolHandle` — Create an HTTP client pool.
- `async get_pool(pool_id: str) -> Optional[PoolHandle]` — Get a pool by ID.
- `async acquire_connection(pool_id: str, tenant_id: Optional[str], timeout: Optional[float]) -> Any` — Acquire a connection from a pool.
- `async release_connection(pool_id: str, connection: Any, tenant_id: Optional[str]) -> None` — Release a connection back to the pool.
- `async close_pool(pool_id: str) -> bool` — Close a pool and release all resources.
- `async get_stats(pool_id: Optional[str]) -> Dict[str, PoolStats]` — Get pool statistics.
- `async health_check(pool_id: str) -> PoolStatus` — Perform health check on a pool.
- `async _health_check_loop(handle: PoolHandle) -> None` — Background health check loop for a pool.
- `list_pools() -> list[str]` — List all pool IDs.

## Domain Usage

**Callers:** Services, API routes

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PoolType
      methods: []
      consumers: ["orchestrator"]
    - name: PoolStatus
      methods: []
      consumers: ["orchestrator"]
    - name: PoolConfig
      methods: []
      consumers: ["orchestrator"]
    - name: PoolStats
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: PoolHandle
      methods: []
      consumers: ["orchestrator"]
    - name: ConnectionPoolManager
      methods:
        - start
        - stop
        - create_database_pool
        - create_redis_pool
        - create_http_pool
        - get_pool
        - acquire_connection
        - release_connection
        - close_pool
        - get_stats
        - health_check
        - list_pools
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['httpx', 'asyncpg', 'redis.asyncio', 'redis.asyncio', 'redis.asyncio']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

