# hoc_cus_logs_L6_drivers_bridges_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/bridges_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Database operations for integration bridges

## Intent

**Role:** Database operations for integration bridges
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** bridges_engine

## Purpose

M25 Bridges Driver

---

## Functions

### `async record_policy_activation(db_factory, policy_id: str, source_pattern_id: str, source_recovery_id: str, confidence: float, approval_path: str, loop_trace_id: str, tenant_id: str) -> PolicyActivationAudit`
- **Async:** Yes
- **Docstring:** Record policy activation for audit trail.  Every ACTIVE policy must have an audit record.
- **Calls:** PolicyActivationAudit, db_factory, execute, info, now, text

## Attributes

- `logger` (line 39)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `schemas.audit_schemas`, `schemas.loop_events`, `sqlalchemy` |

## Callers

bridges_engine

## Export Contract

```yaml
exports:
  functions:
    - name: record_policy_activation
      signature: "async record_policy_activation(db_factory, policy_id: str, source_pattern_id: str, source_recovery_id: str, confidence: float, approval_path: str, loop_trace_id: str, tenant_id: str) -> PolicyActivationAudit"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
