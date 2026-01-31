# runtime.py

**Path:** `backend/app/hoc/hoc_spine/authority/runtime.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            runtime.py
Lives in:        authority/
Role:            Authority
Inbound:         runtime, workers
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Runtime Utilities - Centralized Shared Helpers
Violations:      none
```

## Purpose

Runtime Utilities - Centralized Shared Helpers

CANONICAL LOCATION: All code needing generate_uuid() or utc_now() must import from here.
DO NOT define these functions elsewhere.
DO NOT import them transitively through other modules.

This prevents import hygiene violations where services fail at runtime
because they relied on transitive imports that aren't guaranteed.

See LESSONS_ENFORCED.md Invariant #5: Import Locality

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `generate_uuid() -> str`

Generate a UUID string.

CANONICAL LOCATION: Import from app.utils.runtime, not from other modules.

### `utc_now() -> datetime`

Return timezone-aware UTC datetime.

CANONICAL LOCATION: Import from app.utils.runtime, not from other modules.

For asyncpg compatibility in raw SQL, use utc_now_naive() instead.

### `utc_now_naive() -> datetime`

Return timezone-naive UTC datetime (for asyncpg raw SQL compatibility).

Use this ONLY when:
- Writing raw SQL with asyncpg
- You explicitly need a naive datetime

For all other cases, prefer utc_now().

## Domain Usage

**Callers:** runtime, workers

## Export Contract

```yaml
exports:
  functions:
    - name: generate_uuid
      signature: "generate_uuid() -> str"
      consumers: ["orchestrator"]
    - name: utc_now
      signature: "utc_now() -> datetime"
      consumers: ["orchestrator"]
    - name: utc_now_naive
      signature: "utc_now_naive() -> datetime"
      consumers: ["orchestrator"]
  classes: []
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

