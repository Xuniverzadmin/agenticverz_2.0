# hoc_cus_account_L6_drivers_tenant_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L6_drivers/tenant_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Tenant domain driver - pure data access for tenant operations — L6 DOES NOT COMMIT

## Intent

**Role:** Tenant domain driver - pure data access for tenant operations — L6 DOES NOT COMMIT
**Reference:** PIN-470, ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** tenant_engine.py (L5), must provide session, must own transaction boundary

## Purpose

Tenant Driver (L6)

---

## Functions

### `get_tenant_driver(session: Session) -> TenantDriver`
- **Async:** No
- **Docstring:** Get a TenantDriver instance.
- **Calls:** TenantDriver

## Classes

### `TenantCoreSnapshot`
- **Docstring:** Core tenant data for engine operations.
- **Class Variables:** id: str, name: str, slug: str, status: str, plan: str, max_workers: int, max_runs_per_day: int, max_concurrent_runs: int, max_tokens_per_month: int, max_api_keys: int, runs_today: int, runs_this_month: int, tokens_this_month: int, last_run_reset_at: Optional[datetime], created_at: datetime, updated_at: Optional[datetime]

### `RunCountSnapshot`
- **Docstring:** Running count for quota checks.
- **Class Variables:** count: int

### `APIKeySnapshot`
- **Docstring:** API key data snapshot.
- **Class Variables:** id: str, tenant_id: str, user_id: Optional[str], name: str, key_prefix: str, status: str, permissions: List[str], allowed_workers: Optional[List[str]], rate_limit_rpm: Optional[int], max_concurrent_runs: Optional[int], expires_at: Optional[datetime], created_at: datetime

### `UsageRecordSnapshot`
- **Docstring:** Usage record data.
- **Class Variables:** id: str, tenant_id: str, meter_name: str, amount: int, unit: str, period_start: datetime, period_end: datetime

### `RunSnapshot`
- **Docstring:** Worker run snapshot.
- **Class Variables:** id: str, tenant_id: str, worker_id: str, task: str, status: str, success: Optional[bool], total_tokens: int, total_latency_ms: int, cost_cents: int, created_at: datetime, completed_at: Optional[datetime]

### `TenantDriver`
- **Docstring:** L6 Driver for tenant data access.
- **Methods:** __init__, fetch_tenant_by_id, fetch_tenant_by_slug, fetch_tenant_snapshot, insert_tenant, update_tenant_plan, update_tenant_status, update_tenant_usage, increment_tenant_usage, insert_membership, count_active_api_keys, insert_api_key, fetch_api_keys, fetch_api_key_by_id, update_api_key_revoked, count_running_runs, insert_run, fetch_run_by_id, update_run_completed, fetch_runs, insert_usage_record, fetch_usage_records, insert_audit_log

## Attributes

- `__all__` (line 565)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.tenant` |
| External | `__future__`, `app.hoc.cus.hoc_spine.services.time`, `sqlmodel` |

## Callers

tenant_engine.py (L5), must provide session, must own transaction boundary

## Export Contract

```yaml
exports:
  functions:
    - name: get_tenant_driver
      signature: "get_tenant_driver(session: Session) -> TenantDriver"
  classes:
    - name: TenantCoreSnapshot
      methods: []
    - name: RunCountSnapshot
      methods: []
    - name: APIKeySnapshot
      methods: []
    - name: UsageRecordSnapshot
      methods: []
    - name: RunSnapshot
      methods: []
    - name: TenantDriver
      methods: [fetch_tenant_by_id, fetch_tenant_by_slug, fetch_tenant_snapshot, insert_tenant, update_tenant_plan, update_tenant_status, update_tenant_usage, increment_tenant_usage, insert_membership, count_active_api_keys, insert_api_key, fetch_api_keys, fetch_api_key_by_id, update_api_key_revoked, count_running_runs, insert_run, fetch_run_by_id, update_run_completed, fetch_runs, insert_usage_record, fetch_usage_records, insert_audit_log]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
