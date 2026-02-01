# retry.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/retry.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            retry.py
Lives in:        schemas/
Role:            Schemas
Inbound:         API routes
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Retry API schemas
Violations:      none
```

## Purpose

Retry API schemas

## Import Analysis

**External:**
- `pydantic`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `BackoffStrategy(str, Enum)`

Backoff strategy for retries.

### `RetryPolicy(BaseModel)`

Retry policy configuration for skills and steps.

Defines how failures should be retried, including
max attempts, delays, and backoff strategies.

#### Methods

- `get_delay(attempt: int) -> float` — Calculate delay for given attempt number (1-indexed).
- `_fibonacci(n: int) -> int` — Calculate nth fibonacci number.

## Domain Usage

**Callers:** API routes

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: BackoffStrategy
      methods: []
      consumers: ["orchestrator"]
    - name: RetryPolicy
      methods:
        - get_delay
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

