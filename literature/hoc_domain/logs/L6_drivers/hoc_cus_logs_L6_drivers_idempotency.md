# hoc_cus_logs_L6_drivers_idempotency

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/idempotency.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace idempotency enforcement (Redis + Lua scripts)

## Intent

**Role:** Trace idempotency enforcement (Redis + Lua scripts)
**Reference:** PIN-470, EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 2: Idempotent Trace Emission)
**Callers:** trace store, workers

## Purpose

Redis Idempotency Store for AOS Traces

---

## Functions

### `_load_lua_script() -> str`
- **Async:** No
- **Docstring:** Load Lua script from file.
- **Calls:** exists, read_text

### `canonical_json(obj: Any) -> str`
- **Async:** No
- **Docstring:** Produce canonical JSON (sorted keys, compact format).
- **Calls:** dumps

### `hash_request(data: Dict[str, Any]) -> str`
- **Async:** No
- **Docstring:** Hash request data for idempotency comparison.
- **Calls:** canonical_json, encode, hexdigest, sha256

### `async get_idempotency_store() -> Any`
- **Async:** Yes
- **Docstring:** Get or create idempotency store based on environment.
- **Calls:** InMemoryIdempotencyStore, RedisIdempotencyStore, from_url, getenv, info, ping, warning

## Classes

### `IdempotencyResult(Enum)`
- **Docstring:** Result of idempotency check.

### `IdempotencyResponse`
- **Docstring:** Response from idempotency check.
- **Methods:** is_new, is_duplicate, is_conflict
- **Class Variables:** result: IdempotencyResult, stored_hash: str, stored_trace_id: str

### `RedisIdempotencyStore`
- **Docstring:** Redis-backed idempotency store with Lua script for atomicity.
- **Methods:** __init__, _make_key, _ensure_script_loaded, check, mark_completed, mark_failed, delete, get_status

### `InMemoryIdempotencyStore`
- **Docstring:** In-memory idempotency store for testing and development.
- **Methods:** __init__, _make_key, check, mark_completed, mark_failed, delete, get_status

## Attributes

- `logger` (line 42)
- `_LUA_SCRIPT_PATH` (line 75)
- `_LUA_SCRIPT: Optional[str]` (line 76)
- `_idempotency_store: Optional[Any]` (line 371)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `redis.asyncio` |

## Callers

trace store, workers

## Export Contract

```yaml
exports:
  functions:
    - name: canonical_json
      signature: "canonical_json(obj: Any) -> str"
    - name: hash_request
      signature: "hash_request(data: Dict[str, Any]) -> str"
    - name: get_idempotency_store
      signature: "async get_idempotency_store() -> Any"
  classes:
    - name: IdempotencyResult
      methods: []
    - name: IdempotencyResponse
      methods: [is_new, is_duplicate, is_conflict]
    - name: RedisIdempotencyStore
      methods: [check, mark_completed, mark_failed, delete, get_status]
    - name: InMemoryIdempotencyStore
      methods: [check, mark_completed, mark_failed, delete, get_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
