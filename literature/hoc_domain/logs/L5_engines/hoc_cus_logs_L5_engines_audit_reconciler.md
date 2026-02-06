# hoc_cus_logs_L5_engines_audit_reconciler

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/audit_reconciler.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Reconcile audit expectations against acknowledgments

## Intent

**Role:** Reconcile audit expectations against acknowledgments
**Reference:** PIN-470, PIN-454 (Cross-Domain Orchestration Audit)
**Callers:** ROK (L5), Scheduler (L5)

## Purpose

Audit Reconciler

---

## Functions

### `get_audit_reconciler(store: Optional[AuditStore]) -> AuditReconciler`
- **Async:** No
- **Docstring:** Get the audit reconciler singleton.  Args:
- **Calls:** AuditReconciler

## Classes

### `AuditReconciler`
- **Docstring:** Reconciles expectations with acknowledgments.
- **Methods:** __init__, reconcile, check_deadline_violations, get_run_audit_summary, _record_metrics

## Attributes

- `logger` (line 60)
- `RECONCILIATION_TOTAL` (line 66)
- `MISSING_ACTIONS_TOTAL` (line 72)
- `DRIFT_ACTIONS_TOTAL` (line 78)
- `STALE_RUNS_TOTAL` (line 84)
- `RECONCILIATION_DURATION` (line 89)
- `_reconciler_instance: Optional[AuditReconciler]` (line 306)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.schemas.rac_models`, `app.hoc.cus.hoc_spine.services.audit_store`, `prometheus_client` |

## Callers

ROK (L5), Scheduler (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_audit_reconciler
      signature: "get_audit_reconciler(store: Optional[AuditStore]) -> AuditReconciler"
  classes:
    - name: AuditReconciler
      methods: [reconcile, check_deadline_violations, get_run_audit_summary]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
