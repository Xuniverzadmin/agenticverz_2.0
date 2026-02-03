# hoc_cus_policies_L5_engines_policies_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policies_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policies facade - unified entry point for policy management

## Intent

**Role:** Policies facade - unified entry point for policy management
**Reference:** SWEEP-03 Batch 3, PIN-470
**Callers:** policies.py (L2 API)

## Purpose

PoliciesFacade (SWEEP-03 Batch 3)

---

## Attributes

- `__all__` (line 75)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.services.policies_facade` |

## Callers

policies.py (L2 API)

## Export Contract

```yaml
exports:
  functions: []
  classes: []
```

## Wiring

### L6 Driver Dependencies

The facade delegates to L5 engines which require L6 drivers:

| Method | Engine | Driver |
|--------|--------|--------|
| `list_policy_conflicts` | `PolicyConflictEngine` | `PolicyGraphDriver` |
| `get_policy_dependencies` | `PolicyDependencyEngine` | `PolicyGraphDriver` |

**Pattern:** Facade creates driver via `get_policy_graph_driver(session)` and passes to engine methods.

### PIN-520 Wiring Fix (2026-02-03)

Fixed wiring bug where `session` was passed directly to engine instead of creating driver:

```python
# Before (WRONG)
result = await engine.detect_conflicts(session=session, ...)

# After (CORRECT)
driver = get_policy_graph_driver(session)
result = await engine.detect_conflicts(driver=driver, ...)
```

## Evaluation Notes

- **Disposition:** KEEP
- **Rationale:** Core facade for policies domain, properly wired to L6 drivers
