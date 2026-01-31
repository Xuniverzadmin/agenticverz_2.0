# idempotency.py

**Path:** `backend/app/hoc/hoc_spine/drivers/idempotency.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            idempotency.py
Lives in:        drivers/
Role:            Drivers
Inbound:         API routes, workers
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Idempotency key utilities
Violations:      none
```

## Purpose

Idempotency key utilities

## Import Analysis

**External:**
- `sqlmodel`
- `db`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_existing_run(idempotency_key: str, tenant_id: Optional[str], agent_id: Optional[str]) -> Optional[Run]`

Check if a run with this idempotency key already exists.

Args:
    idempotency_key: The idempotency key to check
    tenant_id: Optional tenant filter
    agent_id: Optional agent filter

Returns:
    Existing Run if found, None otherwise

### `check_idempotency(idempotency_key: str, tenant_id: Optional[str], agent_id: Optional[str]) -> IdempotencyResult`

Check idempotency and return result with status.

Args:
    idempotency_key: The idempotency key to check
    tenant_id: Optional tenant filter
    agent_id: Optional agent filter

Returns:
    IdempotencyResult indicating if key exists and its status

### `should_return_cached(result: IdempotencyResult) -> bool`

Determine if we should return cached result.

Returns True if:
- Key exists and is not expired
- Status is succeeded, failed, or in progress (queued/running)

Returns False if:
- Key doesn't exist
- Key is expired

## Classes

### `IdempotencyResult`

Result of idempotency check.

## Domain Usage

**Callers:** API routes, workers

## Export Contract

```yaml
exports:
  functions:
    - name: get_existing_run
      signature: "get_existing_run(idempotency_key: str, tenant_id: Optional[str], agent_id: Optional[str]) -> Optional[Run]"
      consumers: ["orchestrator"]
    - name: check_idempotency
      signature: "check_idempotency(idempotency_key: str, tenant_id: Optional[str], agent_id: Optional[str]) -> IdempotencyResult"
      consumers: ["orchestrator"]
    - name: should_return_cached
      signature: "should_return_cached(result: IdempotencyResult) -> bool"
      consumers: ["orchestrator"]
  classes:
    - name: IdempotencyResult
      methods: []
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
    external: ['sqlmodel', 'db']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

