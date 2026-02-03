# hoc_cus_policies_L6_drivers_policy_graph_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/policy_graph_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Policy graph data access operations

## Intent

**Role:** Policy graph data access operations
**Reference:** PIN-470, Phase-3B SQLAlchemy Extraction
**Callers:** policy_graph_engine.py (L5 engine)

## Purpose

Policy Graph Driver (L6 Data Access)

---

## Functions

### `get_policy_graph_driver(session: AsyncSession) -> PolicyGraphDriver`
- **Async:** No
- **Docstring:** Get a PolicyGraphDriver instance.
- **Calls:** PolicyGraphDriver

## Classes

### `PolicyGraphDriver`
- **Docstring:** L6 Driver for policy graph data operations.
- **Methods:** __init__, fetch_active_policies, fetch_all_policies, fetch_active_limits, fetch_all_limits, fetch_resolved_conflicts

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

| Caller | Pattern |
|--------|---------|
| `policies_facade.py` (L5) | Creates driver, passes to engine |
| `policy_graph_engine.py` (L5) | Receives driver as parameter |

## Wiring Pattern

```python
# In facade (L5):
from app.hoc.cus.policies.L6_drivers.policy_graph_driver import get_policy_graph_driver

driver = get_policy_graph_driver(session)
result = await engine.detect_conflicts(driver=driver, ...)
```

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_graph_driver
      signature: "get_policy_graph_driver(session: AsyncSession) -> PolicyGraphDriver"
  classes:
    - name: PolicyGraphDriver
      methods: [fetch_active_policies, fetch_all_policies, fetch_active_limits, fetch_all_limits, fetch_resolved_conflicts]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
