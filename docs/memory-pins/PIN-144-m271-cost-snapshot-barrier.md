# PIN-144: M27.1 Cost Snapshot Barrier

**Status:** ✅ COMPLETE
**Created:** 2025-12-23
**Category:** Infrastructure / Cost Enforcement
**Milestone:** M27

---

## Summary

Deterministic enforcement barrier between async cost ingestion and anomaly detection. Fixes async race condition.

---

## Details

## Problem

Async cost ingestion races with synchronous anomaly detection:

```
cost_records (async, delayed)
       ↓
anomaly detection (immediate)
       ↓
STALE DATA → WRONG SEVERITY → UNDER-ENFORCEMENT
```

## Solution: Snapshot Barrier

```
cost_records (streaming, async)
       ↓
cost_snapshots (explicit 'complete' marker)
       ↓
anomaly detection (reads ONLY from complete snapshots)
```

## Schema (Migration 047)

### 1. cost_snapshots
Point-in-time snapshot definitions with status machine.

| Column | Type | Purpose |
|--------|------|---------|
| id | string | Snapshot ID |
| tenant_id | string | Tenant |
| snapshot_type | enum | 'hourly' or 'daily' |
| period_start/end | datetime | Snapshot window |
| status | enum | pending → computing → complete/failed |
| records_processed | int | Audit count |
| completed_at | datetime | When marked complete |

### 2. cost_snapshot_aggregates
Per-entity aggregates within a snapshot.

| Column | Type | Purpose |
|--------|------|---------|
| snapshot_id | FK | Parent snapshot |
| entity_type | enum | tenant/user/feature/model |
| entity_id | string | Specific entity |
| total_cost_cents | float | Period cost |
| baseline_7d_avg_cents | float | Historical baseline |
| deviation_from_7d_pct | float | For anomaly threshold |

### 3. cost_snapshot_baselines
Rolling averages computed from historical snapshots.

| Column | Type | Purpose |
|--------|------|---------|
| window_days | int | 7 or 30 |
| avg_daily_cost_cents | float | Baseline for comparison |
| stddev_daily_cost_cents | float | For confidence bands |
| is_current | bool | Latest valid baseline |

### 4. cost_anomaly_evaluations
Audit trail for every anomaly check.

| Column | Type | Purpose |
|--------|------|---------|
| snapshot_id | FK | Source snapshot |
| deviation_pct | float | Computed deviation |
| triggered | bool | Did it create anomaly? |
| evaluation_reason | text | For debugging |

## Key Classes

| Class | Purpose |
|-------|---------|
| SnapshotComputer | Computes hourly/daily snapshots |
| BaselineComputer | Updates rolling baselines |
| SnapshotAnomalyDetector | Evaluates snapshots for anomalies |

## Scheduled Jobs

| Job | Schedule | Function |
|-----|----------|----------|
| Hourly Snapshot | :05 every hour | run_hourly_snapshot_job() |
| Daily Snapshot + Baselines | 00:30 daily | run_daily_snapshot_and_baseline_job() |

## THE INVARIANT

> Anomaly detection NEVER reads from cost_records directly.
> It ONLY reads from complete snapshots.

This decouples ingestion timing from enforcement timing.

## Files

| File | Purpose |
|------|---------|
| alembic/versions/047_m27_cost_snapshots.py | Schema migration |
| app/integrations/cost_snapshots.py | Service implementation |


---

## Test Results (2025-12-23)

### Migration Applied
```
✅ Migration 047_m27_snapshots applied to Neon production
Tables created:
- cost_snapshots
- cost_snapshot_aggregates
- cost_snapshot_baselines
- cost_anomaly_evaluations
+ snapshot_id, baseline_id columns on cost_anomalies
```

### Snapshot Computation Test
```
Snapshot ID: snap_f806269177a7cb6b
Status: complete
Records Processed: 120
Computation Time: 11207ms

📊 Aggregates Created:
   tenant: (tenant-level) → $0.0303 (10 requests)
   user: user_m27_demo → $0.0303 (10 requests)
   feature: business_builder → $0.0303 (10 requests)
   model: gpt-4o-mini → $0.0303 (10 requests)
```

### Anomaly Detection via Snapshot
```
Synthetic baseline: $0.006/day (1/5 of current)
Current spend: $0.0303
Deviation: 400%

🔍 Anomaly Evaluation:
   🚨 TRIGGERED - 400.0% deviation (threshold: 200%)
   Severity: high
   Anomaly ID: anom_d39f4e...
```

### Full C1-C5 Loop with Snapshot Anomaly
```
Status: complete
Stages: ['incident_created', 'pattern_matched', 'recovery_suggested',
         'policy_generated', 'routing_adjusted']

✅ All 5 bridges working with snapshot-triggered anomaly
```

### Database State Verified
```
📸 Snapshots: 1 (snap_f806269177a7cb6b: complete)
📊 Aggregates: 4 total (tenant, user, feature, model)
📈 Active Baselines: 1 (7-day window)
🔍 Evaluations: 1 total, 1 triggered
🚨 Anomalies (from snapshots): 1 (anom_d39f4e...: high)
```

---

## Related PINs

- [PIN-141](PIN-141-m26-cost-intelligence.md) - M26 Cost Intelligence
- [PIN-143](PIN-143-m27-real-cost-enforcement-proof.md) - M27 Real Cost Enforcement Proof
- [PIN-139](PIN-139-m27-cost-loop-integration.md) - M27 Cost Loop Integration
