# concurrent_runs.py

**Path:** `backend/app/hoc/cus/hoc_spine/authority/concurrent_runs.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            concurrent_runs.py
Lives in:        authority/
Role:            Authority
Inbound:         API routes
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Concurrent run limit enforcement (Redis-backed)
Violations:      none
```

## Purpose

Concurrent run limit enforcement (Redis-backed)

## Import Analysis

**External:**
- `redis`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_concurrent_limiter() -> ConcurrentRunsLimiter`

Get the singleton concurrent runs limiter.

### `acquire_slot(key: str, max_slots: int)`

Convenience context manager for acquiring a slot.

Args:
    key: Unique key (e.g., "agent:{agent_id}")
    max_slots: Maximum concurrent runs

Yields:
    Token string

Raises:
    RuntimeError: If limit reached

## Classes

### `ConcurrentRunsLimiter`

Limits concurrent runs using Redis-based semaphore.

Uses Redis sets to track active runs per key.
Automatically expires slots after timeout.

#### Methods

- `__init__(redis_url: Optional[str], slot_timeout: int, fail_open: bool)` — Initialize concurrent runs limiter.
- `_get_client()` — Lazy-load Redis client.
- `acquire(key: str, max_slots: int) -> Optional[str]` — Try to acquire a slot for concurrent run.
- `release(key: str, token: str) -> bool` — Release a slot.
- `get_count(key: str) -> int` — Get current count of active slots.
- `slot(key: str, max_slots: int)` — Context manager for acquiring/releasing a slot.

## Domain Usage

**Callers:** API routes

## Export Contract

```yaml
exports:
  functions:
    - name: get_concurrent_limiter
      signature: "get_concurrent_limiter() -> ConcurrentRunsLimiter"
      consumers: ["orchestrator"]
    - name: acquire_slot
      signature: "acquire_slot(key: str, max_slots: int)"
      consumers: ["orchestrator"]
  classes:
    - name: ConcurrentRunsLimiter
      methods:
        - acquire
        - release
        - get_count
        - slot
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
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

