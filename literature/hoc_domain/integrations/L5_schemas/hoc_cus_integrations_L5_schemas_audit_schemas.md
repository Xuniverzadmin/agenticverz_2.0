# hoc_cus_integrations_L5_schemas_audit_schemas

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_schemas/audit_schemas.py` |
| Layer | L5 — Domain Schemas |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Audit trail dataclasses for integration bridges

## Intent

**Role:** Audit trail dataclasses for integration bridges
**Reference:** HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** bridges, engines

## Purpose

M25 Audit Schemas

---

## Classes

### `PolicyActivationAudit`
- **Docstring:** Audit record for policy activation.
- **Methods:** to_dict
- **Class Variables:** policy_id: str, source_pattern_id: str, source_recovery_id: str, confidence_at_activation: float, confidence_version: str, approval_path: str, loop_trace_id: str, activated_at: datetime, tenant_id: str

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

bridges, engines

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PolicyActivationAudit
      methods: [to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
