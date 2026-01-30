# hoc_models_logs_records

| Field | Value |
|-------|-------|
| Path | `backend/app/models/logs_records.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

LLM Run Records and System Records models for Logs domain (PIN-413)

## Intent

**Role:** LLM Run Records and System Records models for Logs domain (PIN-413)
**Reference:** PIN-413 Domain Design — Logs v1 Expansion
**Callers:** runtime_projections/logs/*, worker capture

## Purpose

Logs Records Models (PIN-413)

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return current UTC time.
- **Calls:** now

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** Generate a UUID string.
- **Calls:** str, uuid4

## Classes

### `ExecutionStatus(str, Enum)`
- **Docstring:** LLM run execution status values.

### `RecordSource(str, Enum)`
- **Docstring:** Source of the record.

### `SystemComponent(str, Enum)`
- **Docstring:** System component types.

### `SystemEventType(str, Enum)`
- **Docstring:** System event types.

### `SystemSeverity(str, Enum)`
- **Docstring:** System event severity levels.

### `SystemCausedBy(str, Enum)`
- **Docstring:** What caused the system event.

### `LLMRunRecord(SQLModel)`
- **Docstring:** Immutable execution record for every LLM run (Logs domain).
- **Class Variables:** id: str, tenant_id: str, run_id: str, trace_id: Optional[str], provider: str, model: str, prompt_hash: Optional[str], response_hash: Optional[str], input_tokens: int, output_tokens: int, cost_cents: int, execution_status: str, started_at: datetime, completed_at: Optional[datetime], source: str, is_synthetic: bool, synthetic_scenario_id: Optional[str], created_at: datetime

### `SystemRecord(SQLModel)`
- **Docstring:** Immutable records for system-level events that affect trust (Logs domain).
- **Class Variables:** id: str, tenant_id: Optional[str], component: str, event_type: str, severity: str, summary: str, details: Optional[dict], caused_by: Optional[str], correlation_id: Optional[str], created_at: datetime

## Attributes

- `__all__` (line 215)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlmodel` |

## Callers

runtime_projections/logs/*, worker capture

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: ExecutionStatus
      methods: []
    - name: RecordSource
      methods: []
    - name: SystemComponent
      methods: []
    - name: SystemEventType
      methods: []
    - name: SystemSeverity
      methods: []
    - name: SystemCausedBy
      methods: []
    - name: LLMRunRecord
      methods: []
    - name: SystemRecord
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
