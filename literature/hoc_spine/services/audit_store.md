# audit_store.py

**Path:** `backend/app/hoc/hoc_spine/services/audit_store.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            audit_store.py
Lives in:        services/
Role:            Services
Inbound:         ROK (L5), Facades (L4), AuditReconciler
Outbound:        app.hoc.hoc_spine.schemas.rac_models
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Audit Store
Violations:      none
```

## Purpose

Audit Store

Provides storage for audit expectations and acknowledgments.

Storage Strategy:
- MEMORY: In-memory dictionary (dev/test only - NOT crash-safe)
- REDIS: Redis-backed store (staging/prod - crash-safe, cross-process)

Durability Modes:
- AOS_MODE=local → MEMORY allowed
- AOS_MODE=test/prod → REDIS required (startup fails without it)

The store is designed to be:
1. Fast for writes (acks happen in hot path)
2. Durable in production (Redis backing mandatory)
3. TTL-managed (old data expires automatically)

Redis keys:
- rac:expectations:{run_id} -> JSON list of expectations
- rac:acks:{run_id} -> JSON list of acks
- TTL: 1 hour (runs should complete within this time)

## Import Analysis

**Spine-internal:**
- `app.hoc.hoc_spine.schemas.rac_models`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `_determine_durability_mode(redis_client) -> StoreDurabilityMode`

Determine the durability mode based on environment and Redis availability.

Rules:
- AOS_MODE=local → MEMORY allowed (dev)
- AOS_MODE=test/prod + RAC_ENABLED + no Redis → ERROR
- AOS_MODE=test/prod + RAC_ENABLED + Redis → REDIS

### `get_audit_store(redis_client) -> AuditStore`

Get the audit store singleton.

Args:
    redis_client: Optional Redis client (only used on first call)

Returns:
    AuditStore instance

## Classes

### `StoreDurabilityMode(str, Enum)`

Durability mode for the audit store.

### `RACDurabilityError(Exception)`

Raised when RAC requires durable storage but none is available.

### `AuditStore`

Storage for audit expectations and acknowledgments.

Thread-safe store with configurable durability:
- MEMORY mode: In-memory only (dev/test, NOT crash-safe)
- REDIS mode: Redis-backed (staging/prod, crash-safe)

Usage:
    store = get_audit_store()

    # Add expectations at run start
    store.add_expectations(run_id, expectations)

    # Add acks as domains complete
    store.add_ack(run_id, ack)

    # Get for reconciliation
    expectations = store.get_expectations(run_id)
    acks = store.get_acks(run_id)

Durability:
    In production (AOS_MODE=test/prod), Redis is REQUIRED when RAC_ENABLED=true.
    This ensures expectations/acks survive worker crashes.

#### Methods

- `__init__(redis_client)` — Initialize the audit store.
- `durability_mode() -> StoreDurabilityMode` — Get the current durability mode.
- `is_durable() -> bool` — Check if the store is using durable (Redis) storage.
- `add_expectations(run_id: UUID, expectations: List[AuditExpectation]) -> None` — Add expectations for a run.
- `get_expectations(run_id: UUID) -> List[AuditExpectation]` — Get all expectations for a run.
- `update_expectation_status(run_id: UUID, domain: str, action: str, status: AuditStatus) -> bool` — Update the status of an expectation.
- `add_ack(run_id: UUID, ack: DomainAck) -> None` — Add an acknowledgment for a run.
- `get_acks(run_id: UUID) -> List[DomainAck]` — Get all acknowledgments for a run.
- `clear_run(run_id: UUID) -> None` — Clear all data for a run.
- `get_pending_run_ids() -> List[str]` — Get all run IDs with pending expectations.
- `_sync_expectations_to_redis(run_key: str) -> None` — Sync expectations to Redis.
- `_sync_acks_to_redis(run_key: str) -> None` — Sync acks to Redis.
- `load_from_redis(run_id: UUID) -> bool` — Load expectations and acks from Redis.

## Domain Usage

**Callers:** ROK (L5), Facades (L4), AuditReconciler

## Export Contract

```yaml
exports:
  functions:
    - name: _determine_durability_mode
      signature: "_determine_durability_mode(redis_client) -> StoreDurabilityMode"
      consumers: ["orchestrator"]
    - name: get_audit_store
      signature: "get_audit_store(redis_client) -> AuditStore"
      consumers: ["orchestrator"]
  classes:
    - name: StoreDurabilityMode
      methods: []
      consumers: ["orchestrator"]
    - name: RACDurabilityError
      methods: []
      consumers: ["orchestrator"]
    - name: AuditStore
      methods:
        - durability_mode
        - is_durable
        - add_expectations
        - get_expectations
        - update_expectation_status
        - add_ack
        - get_acks
        - clear_run
        - get_pending_run_ids
        - load_from_redis
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
    spine_internal: ['app.hoc.hoc_spine.schemas.rac_models']
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

