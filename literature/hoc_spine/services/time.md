# time.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/time.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            time.py
Lives in:        services/
Role:            Services
Inbound:         All customer modules
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Common time utilities for customer domain modules (pure datetime computation)
Violations:      none
```

## Purpose

Common time utilities for customer domain modules (pure datetime computation)

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `utc_now() -> datetime`

Get current UTC time.

## Domain Usage

**Callers:** All customer modules

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
      consumers: ["orchestrator"]
  classes: []
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

