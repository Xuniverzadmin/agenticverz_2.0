# hoc_cus_integrations_L5_engines_customer_logs_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/customer_logs_adapter.py` |
| Layer | L3 — Boundary Adapter |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer logs boundary adapter (L2 → L3 → L4)

## Intent

**Role:** Customer logs boundary adapter (L2 → L3 → L4)
**Reference:** PIN-280, PIN-281 (L2 Promotion Governance - PHASE 1 L3 Closure)
**Callers:** guard_logs.py (L2)

## Purpose

Customer Logs Boundary Adapter (L3)

---

## Functions

### `get_customer_logs_adapter() -> CustomerLogsAdapter`
- **Async:** No
- **Docstring:** Get the singleton CustomerLogsAdapter instance.  This is the ONLY way L2 should obtain a logs adapter.
- **Calls:** CustomerLogsAdapter

## Classes

### `CustomerLogSummary(BaseModel)`
- **Docstring:** Customer-safe log summary for list view.
- **Class Variables:** log_id: str, run_id: str, agent_id: Optional[str], status: str, total_steps: int, success_count: int, failure_count: int, started_at: str, completed_at: Optional[str], total_duration_ms: float

### `CustomerLogStep(BaseModel)`
- **Docstring:** Customer-safe log step for detail view.
- **Class Variables:** step_index: int, skill_name: str, status: str, outcome_category: str, outcome_code: Optional[str], duration_ms: float, timestamp: str

### `CustomerLogDetail(BaseModel)`
- **Docstring:** Customer-safe log detail.
- **Class Variables:** log_id: str, run_id: str, correlation_id: str, agent_id: Optional[str], status: str, started_at: str, completed_at: Optional[str], steps: List[CustomerLogStep], total_steps: int, success_count: int, failure_count: int, total_duration_ms: float

### `CustomerLogListResponse(BaseModel)`
- **Docstring:** Paginated customer log list.
- **Class Variables:** items: List[CustomerLogSummary], total: int, page: int, page_size: int

### `CustomerLogsAdapter`
- **Docstring:** Boundary adapter for customer logs operations.
- **Methods:** __init__, _get_service, list_logs, get_log, export_logs

## Attributes

- `_customer_logs_adapter_instance: Optional[CustomerLogsAdapter]` (line 377)
- `__all__` (line 402)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.logs.L5_engines.logs_read_engine` |
| Cross-Domain | `app.hoc.cus.logs.L5_engines.logs_read_engine` |
| External | `pydantic` |

## Callers

guard_logs.py (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: get_customer_logs_adapter
      signature: "get_customer_logs_adapter() -> CustomerLogsAdapter"
  classes:
    - name: CustomerLogSummary
      methods: []
    - name: CustomerLogStep
      methods: []
    - name: CustomerLogDetail
      methods: []
    - name: CustomerLogListResponse
      methods: []
    - name: CustomerLogsAdapter
      methods: [list_logs, get_log, export_logs]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
