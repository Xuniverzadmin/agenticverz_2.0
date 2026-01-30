# hoc_cus_analytics_L5_schemas_cost_snapshot_schemas

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_schemas/cost_snapshot_schemas.py` |
| Layer | L5 — Domain Schemas |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cost snapshot dataclasses and enums

## Intent

**Role:** Cost snapshot dataclasses and enums
**Reference:** HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** cost_snapshot_engine, cost_snapshot_driver

## Purpose

M27 Cost Snapshot Schemas

---

## Classes

### `SnapshotType(str, Enum)`
- **Docstring:** _None_

### `SnapshotStatus(str, Enum)`
- **Docstring:** _None_

### `EntityType(str, Enum)`
- **Docstring:** _None_

### `CostSnapshot`
- **Docstring:** Point-in-time cost snapshot definition.
- **Methods:** create, to_dict
- **Class Variables:** id: str, tenant_id: str, snapshot_type: SnapshotType, period_start: datetime, period_end: datetime, status: SnapshotStatus, version: int, records_processed: int | None, computation_ms: int | None, error_message: str | None, created_at: datetime, completed_at: datetime | None

### `SnapshotAggregate`
- **Docstring:** Aggregated cost data for an entity within a snapshot.
- **Methods:** create
- **Class Variables:** id: str, snapshot_id: str, tenant_id: str, entity_type: EntityType, entity_id: str | None, total_cost_cents: float, request_count: int, total_input_tokens: int, total_output_tokens: int, avg_cost_per_request_cents: float | None, avg_tokens_per_request: float | None, baseline_7d_avg_cents: float | None, baseline_30d_avg_cents: float | None, deviation_from_7d_pct: float | None, deviation_from_30d_pct: float | None

### `SnapshotBaseline`
- **Docstring:** Rolling baseline for an entity (used for anomaly threshold).
- **Methods:** create
- **Class Variables:** id: str, tenant_id: str, entity_type: EntityType, entity_id: str | None, avg_daily_cost_cents: float, stddev_daily_cost_cents: float | None, avg_daily_requests: float, max_daily_cost_cents: float | None, min_daily_cost_cents: float | None, window_days: int, samples_count: int, computed_at: datetime, valid_until: datetime, is_current: bool, last_snapshot_id: str | None

### `AnomalyEvaluation`
- **Docstring:** Audit record for an anomaly evaluation.
- **Class Variables:** id: str, tenant_id: str, snapshot_id: str | None, entity_type: EntityType, entity_id: str | None, current_value_cents: float, baseline_value_cents: float, threshold_pct: float, deviation_pct: float, triggered: bool, severity_computed: str | None, anomaly_id: str | None, evaluation_reason: str | None, evaluated_at: datetime

## Attributes

- `SEVERITY_THRESHOLDS` (line 52)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

cost_snapshot_engine, cost_snapshot_driver

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SnapshotType
      methods: []
    - name: SnapshotStatus
      methods: []
    - name: EntityType
      methods: []
    - name: CostSnapshot
      methods: [create, to_dict]
    - name: SnapshotAggregate
      methods: [create]
    - name: SnapshotBaseline
      methods: [create]
    - name: AnomalyEvaluation
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
