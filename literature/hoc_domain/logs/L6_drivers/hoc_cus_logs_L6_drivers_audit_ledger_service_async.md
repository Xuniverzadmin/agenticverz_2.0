# hoc_cus_logs_L6_drivers_audit_ledger_service_async

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/audit_ledger_service_async.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Async audit ledger writer for governance events

## Intent

**Role:** Async audit ledger writer for governance events
**Reference:** PIN-470, PIN-413 (Logs Domain)
**Callers:** policy_limits_engine, policy_rules_engine, policy_proposal_engine (L5)

## Purpose

Audit Ledger Service (Async)

---

## Functions

### `get_audit_ledger_service_async(session: AsyncSession) -> AuditLedgerServiceAsync`
- **Async:** No
- **Docstring:** Get an AuditLedgerServiceAsync instance.  Args:
- **Calls:** AuditLedgerServiceAsync

## Classes

### `AuditLedgerServiceAsync`
- **Docstring:** Async service for writing to the audit ledger.
- **Methods:** __init__, _emit, limit_created, limit_updated, limit_breached, policy_rule_created, policy_rule_modified, policy_rule_retired, policy_proposal_approved, policy_proposal_rejected

## Attributes

- `logger` (line 45)
- `__all__` (line 326)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.audit_ledger` |
| External | `sqlalchemy.ext.asyncio` |

## Callers

policy_limits_engine, policy_rules_engine, policy_proposal_engine (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_audit_ledger_service_async
      signature: "get_audit_ledger_service_async(session: AsyncSession) -> AuditLedgerServiceAsync"
  classes:
    - name: AuditLedgerServiceAsync
      methods: [limit_created, limit_updated, limit_breached, policy_rule_created, policy_rule_modified, policy_rule_retired, policy_proposal_approved, policy_proposal_rejected]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
