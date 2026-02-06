# hoc_cus_logs_L6_drivers_replay

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/replay.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace replay execution

## Intent

**Role:** Trace replay execution
**Reference:** PIN-470, Trace System
**Callers:** API routes

## Purpose

Server-Side Replay Enforcement
M8 Deliverable: Enforce replay_behavior during trace execution

---

## Functions

### `hash_output(data: Any) -> str`
- **Async:** No
- **Docstring:** Compute hash of output data for comparison.
- **Calls:** dumps, encode, hexdigest, sha256

### `get_replay_enforcer(use_redis: bool) -> ReplayEnforcer`
- **Async:** No
- **Docstring:** Get singleton replay enforcer.
- **Calls:** InMemoryIdempotencyStore, RedisIdempotencyStore, ReplayEnforcer

## Classes

### `ReplayBehavior(str, Enum)`
- **Docstring:** Replay behavior options.

### `ReplayMismatchError(Exception)`
- **Docstring:** Raised when replay output doesn't match original.
- **Methods:** __init__

### `IdempotencyViolationError(Exception)`
- **Docstring:** Raised when idempotency key is violated.
- **Methods:** __init__

### `ReplayResult`
- **Docstring:** Result of a replay operation.
- **Class Variables:** executed: bool, skipped: bool, checked: bool, output_data: Any, output_hash: str, from_cache: bool

### `ReplayEnforcer`
- **Docstring:** Server-side replay behavior enforcer.
- **Methods:** __init__, enforce_step, enforce_trace

### `IdempotencyStore`
- **Docstring:** Abstract base for idempotency storage.
- **Methods:** get, set, delete

### `InMemoryIdempotencyStore(IdempotencyStore)`
- **Docstring:** In-memory idempotency store for testing.
- **Methods:** __init__, _make_key, get, set, delete, clear

### `RedisIdempotencyStore(IdempotencyStore)`
- **Docstring:** Redis-based idempotency store for production.
- **Methods:** __init__, _get_client, _make_key, get, set, delete

## Attributes

- `_enforcer: Optional[ReplayEnforcer]` (line 317)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `redis.asyncio` |

## Callers

API routes

## Export Contract

```yaml
exports:
  functions:
    - name: hash_output
      signature: "hash_output(data: Any) -> str"
    - name: get_replay_enforcer
      signature: "get_replay_enforcer(use_redis: bool) -> ReplayEnforcer"
  classes:
    - name: ReplayBehavior
      methods: []
    - name: ReplayMismatchError
      methods: []
    - name: IdempotencyViolationError
      methods: []
    - name: ReplayResult
      methods: []
    - name: ReplayEnforcer
      methods: [enforce_step, enforce_trace]
    - name: IdempotencyStore
      methods: [get, set, delete]
    - name: InMemoryIdempotencyStore
      methods: [get, set, delete, clear]
    - name: RedisIdempotencyStore
      methods: [get, set, delete]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
