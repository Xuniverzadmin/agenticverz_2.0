# hoc_cus_integrations_L5_engines_customer_activity_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/customer_activity_adapter.py` |
| Layer | L3 — Boundary Adapter |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer activity boundary adapter (L2 → L3 → L5)

## Intent

**Role:** Customer activity boundary adapter (L2 → L3 → L5)
**Reference:** ACTIVITY Domain Qualification Task, SWEEP-03
**Callers:** L2 activity routes

## Purpose

Customer Activity Boundary Adapter (L3)

---

## Functions

### `get_customer_activity_adapter() -> CustomerActivityAdapter`
- **Async:** No
- **Docstring:** Get the singleton CustomerActivityAdapter instance.  This is the ONLY way L2 should obtain an activity adapter.
- **Calls:** CustomerActivityAdapter

## Classes

### `CustomerActivitySummary(BaseModel)`
- **Docstring:** Customer-safe activity summary for list view.
- **Class Variables:** run_id: str, worker_name: str, task_preview: str, status: str, success: Optional[bool], total_steps: Optional[int], duration_ms: Optional[int], created_at: str, completed_at: Optional[str]

### `CustomerActivityDetail(BaseModel)`
- **Docstring:** Customer-safe activity detail.
- **Class Variables:** run_id: str, worker_name: str, task: str, status: str, success: Optional[bool], error_summary: Optional[str], total_steps: Optional[int], recoveries: int, policy_violations: int, duration_ms: Optional[int], created_at: str, started_at: Optional[str], completed_at: Optional[str]

### `CustomerActivityListResponse(BaseModel)`
- **Docstring:** Paginated list of customer activities.
- **Class Variables:** items: List[CustomerActivitySummary], total: int, limit: int, offset: int, has_more: bool

### `CustomerActivityAdapter`
- **Docstring:** L3 boundary adapter for customer activity operations.
- **Methods:** __init__, _get_facade, list_activities, get_activity, _to_customer_summary, _to_customer_detail

## Attributes

- `_customer_activity_adapter_instance: Optional[CustomerActivityAdapter]` (line 304)
- `__all__` (line 326)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.activity.L5_engines.activity_facade` |
| Cross-Domain | `app.hoc.cus.activity.L5_engines.activity_facade` |
| External | `pydantic`, `sqlalchemy.ext.asyncio` |

## Callers

L2 activity routes

## Export Contract

```yaml
exports:
  functions:
    - name: get_customer_activity_adapter
      signature: "get_customer_activity_adapter() -> CustomerActivityAdapter"
  classes:
    - name: CustomerActivitySummary
      methods: []
    - name: CustomerActivityDetail
      methods: []
    - name: CustomerActivityListResponse
      methods: []
    - name: CustomerActivityAdapter
      methods: [list_activities, get_activity]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
