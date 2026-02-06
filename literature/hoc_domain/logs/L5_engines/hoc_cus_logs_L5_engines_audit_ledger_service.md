# hoc_cus_logs_L5_engines_audit_ledger_service

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/audit_ledger_service.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Sync audit ledger writer for governance events (incidents)

## Intent

**Role:** Sync audit ledger writer for governance events (incidents)
**Reference:** SWEEP-03 Batch 3, PIN-470, PIN-413 (Logs Domain)
**Callers:** incident_write_engine (L5)

## Purpose

Audit Ledger Service (Sync)

---

## Functions

### `get_audit_ledger_service(session: 'Session') -> AuditLedgerService`
- **Async:** No
- **Docstring:** Get an AuditLedgerService instance.  Args:
- **Calls:** AuditLedgerService

## Classes

### `AuditLedgerService`
- **Docstring:** Sync service for writing to the audit ledger.
- **Methods:** __init__, _emit, incident_acknowledged, incident_resolved, incident_manually_closed

## Attributes

- `logger` (line 51)
- `__all__` (line 217)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.audit_ledger` |
| External | `sqlmodel` |

## Callers

incident_write_engine (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_audit_ledger_service
      signature: "get_audit_ledger_service(session: 'Session') -> AuditLedgerService"
  classes:
    - name: AuditLedgerService
      methods: [incident_acknowledged, incident_resolved, incident_manually_closed]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
