# hoc_cus_analytics_L5_engines_cost_snapshots

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/cost_snapshots.py` |
| Layer | L5/L6 — HYBRID (pending refactor) |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cost snapshot computation with embedded DB operations

## Intent

**Role:** Cost snapshot computation with embedded DB operations
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** workers, cost services

## Purpose

M27 Cost Snapshots - Deterministic Enforcement Barrier

---

## Functions

### `async run_hourly_snapshot_job(session: AsyncSession, tenant_ids: list[str]) -> dict`
- **Async:** Yes
- **Docstring:** Run hourly snapshot job for multiple tenants.  Schedule this via cron/systemd timer every hour at :05.
- **Calls:** SnapshotComputer, append, compute_hourly_snapshot, str

### `async run_daily_snapshot_and_baseline_job(session: AsyncSession, tenant_ids: list[str]) -> dict`
- **Async:** Yes
- **Docstring:** Run daily snapshot and baseline computation for multiple tenants.  Schedule this via cron/systemd timer daily at 00:30.
- **Calls:** BaselineComputer, SnapshotAnomalyDetector, SnapshotComputer, append, compute_baselines, compute_daily_snapshot, evaluate_snapshot, len

## Classes

### `SnapshotComputer`
- **Docstring:** Computes cost snapshots from raw cost_records.
- **Methods:** __init__, compute_hourly_snapshot, compute_daily_snapshot, _compute_snapshot, _aggregate_cost_records, _get_current_baseline, _insert_snapshot, _update_snapshot, _insert_aggregate

### `BaselineComputer`
- **Docstring:** Computes rolling baselines from historical snapshots.
- **Methods:** __init__, compute_baselines, _insert_baseline

### `SnapshotAnomalyDetector`
- **Docstring:** Detects anomalies from complete snapshots only.
- **Methods:** __init__, evaluate_snapshot, _get_snapshot, _insert_evaluation, _create_anomaly_from_evaluation

## Attributes

- `logger` (line 68)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `schemas.cost_snapshot_schemas`, `sqlalchemy.ext.asyncio` |

## Callers

workers, cost services

## Export Contract

```yaml
exports:
  functions:
    - name: run_hourly_snapshot_job
      signature: "async run_hourly_snapshot_job(session: AsyncSession, tenant_ids: list[str]) -> dict"
    - name: run_daily_snapshot_and_baseline_job
      signature: "async run_daily_snapshot_and_baseline_job(session: AsyncSession, tenant_ids: list[str]) -> dict"
  classes:
    - name: SnapshotComputer
      methods: [compute_hourly_snapshot, compute_daily_snapshot]
    - name: BaselineComputer
      methods: [compute_baselines]
    - name: SnapshotAnomalyDetector
      methods: [evaluate_snapshot]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
