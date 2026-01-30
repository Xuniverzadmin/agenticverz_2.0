# hoc_models_audit_ledger

| Field | Value |
|-------|-------|
| Path | `backend/app/models/audit_ledger.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Audit Ledger model for Logs domain (PIN-413)

## Intent

**Role:** Audit Ledger model for Logs domain (PIN-413)
**Reference:** PIN-413 Domain Design — Overview & Logs (CORRECTED)
**Callers:** runtime_projections/logs/*

## Purpose

Audit Ledger Model (PIN-413 CORRECTED)

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return current UTC time (PIN-413).
- **Calls:** now

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** Generate a UUID string (PIN-413).
- **Calls:** str, uuid4

## Classes

### `ActorType(str, Enum)`
- **Docstring:** Types of actors performing actions.

### `AuditEntityType(str, Enum)`
- **Docstring:** Entity types tracked in audit ledger.

### `AuditEventType(str, Enum)`
- **Docstring:** Canonical audit events - only these create audit rows.

### `AuditLedger(SQLModel)`
- **Docstring:** Immutable governance action log (Logs domain).
- **Class Variables:** id: str, tenant_id: str, event_type: str, entity_type: str, entity_id: str, actor_type: str, actor_id: Optional[str], action_reason: Optional[str], before_state: Optional[dict], after_state: Optional[dict], created_at: datetime

## Attributes

- `__all__` (line 140)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlmodel` |

## Callers

runtime_projections/logs/*

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: ActorType
      methods: []
    - name: AuditEntityType
      methods: []
    - name: AuditEventType
      methods: []
    - name: AuditLedger
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
