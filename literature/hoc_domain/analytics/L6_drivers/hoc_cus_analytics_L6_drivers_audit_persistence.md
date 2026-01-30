# hoc_cus_analytics_L6_drivers_audit_persistence

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/audit_persistence.py` |
| Layer | L6 — Domain Driver |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Optimization audit trail persistence

## Intent

**Role:** Optimization audit trail persistence
**Reference:** PIN-470, M10 Optimization
**Callers:** coordinator.py (L5 engine)

## Purpose

_No module docstring._

---

## Functions

### `_now_utc() -> datetime`
- **Async:** No
- **Docstring:** Get current UTC timestamp.
- **Calls:** now

### `persist_audit_record(db: Session, audit_id: str, envelope_id: str, envelope_class: str, decision: str, reason: str, decision_timestamp: datetime, conflicting_envelope_id: Optional[str], preempting_envelope_id: Optional[str], active_envelopes_count: int, tenant_id: Optional[str], emit_traces: bool) -> bool`
- **Async:** No
- **Docstring:** Persist a coordination audit record to the database.  This function is the ONLY legal path to write audit records.
- **Calls:** CoordinationAuditRecordDB, UUID, add, debug, error, isinstance, rollback, str

## Classes

### `CoordinationAuditRecordDB(SQLModel)`
- **Docstring:** SQLModel for coordination_audit_records table.
- **Class Variables:** audit_id: UUID, envelope_id: str, envelope_class: str, decision: str, reason: str, decision_timestamp: datetime, created_at: datetime, conflicting_envelope_id: Optional[str], preempting_envelope_id: Optional[str], active_envelopes_count: int, tenant_id: Optional[str]

## Attributes

- `FEATURE_INTENT` (line 27)
- `RETRY_POLICY` (line 28)
- `logger` (line 49)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.infra`, `sqlmodel` |

## Callers

coordinator.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: persist_audit_record
      signature: "persist_audit_record(db: Session, audit_id: str, envelope_id: str, envelope_class: str, decision: str, reason: str, decision_timestamp: datetime, conflicting_envelope_id: Optional[str], preempting_envelope_id: Optional[str], active_envelopes_count: int, tenant_id: Optional[str], emit_traces: bool) -> bool"
  classes:
    - name: CoordinationAuditRecordDB
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
