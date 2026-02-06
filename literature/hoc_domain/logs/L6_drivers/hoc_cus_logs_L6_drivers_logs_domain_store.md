# hoc_cus_logs_L6_drivers_logs_domain_store

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Database operations for Logs domain (LLM runs, system records, audit ledger)

## Intent

**Role:** Database operations for Logs domain (LLM runs, system records, audit ledger)
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** L5 LogsFacade

## Purpose

Logs Domain Store (L6)

---

## Functions

### `get_logs_domain_store() -> LogsDomainStore`
- **Async:** No
- **Docstring:** Get the singleton LogsDomainStore instance.
- **Calls:** LogsDomainStore

## Classes

### `LLMRunSnapshot`
- **Docstring:** Immutable snapshot of LLM run record.
- **Class Variables:** id: str, run_id: str, trace_id: Optional[str], tenant_id: str, provider: str, model: str, input_tokens: int, output_tokens: int, cost_cents: int, execution_status: str, started_at: datetime, completed_at: Optional[datetime], source: str, is_synthetic: bool, created_at: datetime

### `SystemRecordSnapshot`
- **Docstring:** Immutable snapshot of system record.
- **Class Variables:** id: str, tenant_id: Optional[str], component: str, event_type: str, severity: str, summary: str, details: Optional[dict], caused_by: Optional[str], correlation_id: Optional[str], created_at: datetime

### `AuditLedgerSnapshot`
- **Docstring:** Immutable snapshot of audit ledger entry.
- **Class Variables:** id: str, tenant_id: str, event_type: str, entity_type: str, entity_id: str, actor_type: str, actor_id: Optional[str], action_reason: Optional[str], before_state: Optional[dict], after_state: Optional[dict], correlation_id: Optional[str], created_at: datetime

### `LogExportSnapshot`
- **Docstring:** Immutable snapshot of log export record.
- **Class Variables:** id: str, tenant_id: str, scope: str, format: str, requested_by: str, status: str, checksum: Optional[str], created_at: datetime, delivered_at: Optional[datetime]

### `TraceStepSnapshot`
- **Docstring:** Immutable snapshot of trace step.
- **Class Variables:** step_index: int, timestamp: datetime, skill_name: str, status: str, outcome_category: str, cost_cents: int, duration_ms: int

### `QueryResult`
- **Docstring:** Generic query result with pagination info.
- **Class Variables:** items: list, total: int, has_more: bool

### `LogsDomainStore`
- **Docstring:** L6 Database Driver for Logs domain.
- **Methods:** list_llm_runs, get_llm_run, _to_llm_run_snapshot, get_trace_id_for_run, get_trace_steps, get_replay_window_events, list_system_records, get_system_record_by_correlation, get_system_records_in_window, _to_system_record_snapshot, list_audit_entries, get_audit_entry, get_governance_events, _to_audit_snapshot, list_log_exports, _to_export_snapshot

## Attributes

- `_store_instance: LogsDomainStore | None` (line 652)
- `__all__` (line 663)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.audit_ledger`, `app.models.log_exports`, `app.models.logs_records` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 LogsFacade

## Export Contract

```yaml
exports:
  functions:
    - name: get_logs_domain_store
      signature: "get_logs_domain_store() -> LogsDomainStore"
  classes:
    - name: LLMRunSnapshot
      methods: []
    - name: SystemRecordSnapshot
      methods: []
    - name: AuditLedgerSnapshot
      methods: []
    - name: LogExportSnapshot
      methods: []
    - name: TraceStepSnapshot
      methods: []
    - name: QueryResult
      methods: []
    - name: LogsDomainStore
      methods: [list_llm_runs, get_llm_run, get_trace_id_for_run, get_trace_steps, get_replay_window_events, list_system_records, get_system_record_by_correlation, get_system_records_in_window, list_audit_entries, get_audit_entry, get_governance_events, list_log_exports]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
