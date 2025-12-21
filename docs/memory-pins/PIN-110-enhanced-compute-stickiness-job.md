# PIN-110: Enhanced Compute Stickiness Job

**Status:** ✅ COMPLETE
**Created:** 2025-12-20
**Category:** Ops Console / Customer Intelligence
**Milestone:** M24 Phase-2.1

---

## Summary

Enhanced the `/ops/jobs/compute-stickiness` background job to compute comprehensive customer intelligence metrics, including stickiness_7d, stickiness_30d, stickiness_delta, friction_score, and last_friction_event.

---

## Problem

The original compute-stickiness job only computed a single `current_stickiness` value. The Ops Console requires:
- **Recency-weighted stickiness** (7d vs 30d)
- **Trend detection** (stickiness_delta ratio)
- **Friction tracking** (weighted friction events)
- **Timestamp tracking** (last friction event)

The `/ops/customers` endpoint was returning empty data because the cache table (`ops_customer_segments`) wasn't being populated with these fields.

---

## Solution

### 1. Added Missing Columns to Cache Table

```sql
ALTER TABLE ops_customer_segments
ADD COLUMN IF NOT EXISTS stickiness_7d NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS stickiness_30d NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS stickiness_delta NUMERIC(5,2) DEFAULT 1,
ADD COLUMN IF NOT EXISTS friction_score NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_friction_event TIMESTAMP WITH TIME ZONE;
```

### 2. Enhanced Compute Stickiness Job

The job now computes:

| Metric | Formula | Purpose |
|--------|---------|---------|
| `stickiness_7d` | `(views * 0.2 + replays * 0.3 + exports * 0.5)` for last 7 days | Recent engagement |
| `stickiness_30d` | Same formula for 30 days, normalized to weekly | Historical baseline |
| `stickiness_delta` | `stickiness_7d / stickiness_30d` | Trend indicator (>1 = accelerating) |
| `friction_score` | `LEAST(aborts*2 + export_aborts*1.5 + policy_blocks*3 + idle_timeouts*1, 50)` | Weighted friction (capped) |
| `last_friction_event` | `MAX(timestamp)` for friction event types | Most recent friction |
| `stickiness_trend` | Based on delta: rising (>1.1), falling (<0.9), stable | Categorical trend |

### 3. Updated /ops/customers Query

Added new columns to the SELECT and mapped them to the CustomerSegment model.

---

## Implementation

**File:** `backend/app/api/ops.py`

**Endpoint:** `POST /ops/jobs/compute-stickiness`

**SQL Query (simplified):**
```sql
WITH actions AS (
    SELECT
        tenant_id,
        -- 7-day metrics
        COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED' AND timestamp > now() - '7 days') as views_7d,
        COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED' AND timestamp > now() - '7 days') as replays_7d,
        COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED' AND timestamp > now() - '7 days') as exports_7d,
        -- 30-day metrics
        ...
        -- Friction events (14 days)
        COUNT(*) FILTER (WHERE event_type = 'REPLAY_ABORTED') as aborts,
        COUNT(*) FILTER (WHERE event_type = 'POLICY_BLOCK_REPEAT') as policy_blocks,
        ...
    FROM ops_events
    GROUP BY tenant_id
)
INSERT INTO ops_customer_segments (...)
ON CONFLICT (tenant_id) DO UPDATE SET ...
```

---

## Test Results

```
Customer Console – Ops API Test
================================
✓ pulse           2597ms  PASSED
✓ customers       1273ms  PASSED (12 items)
✓ customers/at-risk 1080ms PASSED (3 items)
✓ playbooks        217ms  PASSED (5 items)
✓ infra           4587ms  PASSED

Result: PASS
```

**Sample Customer Data After Job:**
```json
{
  "tenant_id": "82aeef02-...",
  "current_stickiness": 8.4,
  "stickiness_7d": 8.4,
  "stickiness_30d": 3.69,
  "stickiness_delta": 2.28,
  "friction_score": 0.0,
  "stickiness_trend": "rising"
}
```

---

## Commits

- `fe27a3c` - feat(ops): Enhance compute-stickiness job for comprehensive customer intelligence

---

## Related PINs

- [PIN-105](PIN-105-ops-console-founder-intelligence.md) - Ops Console Founder Intelligence
- [PIN-107](PIN-107-m24-phase2-friction-intel.md) - M24 Phase-2 Friction Intelligence
- [PIN-111](PIN-111-founder-ops-console-ui.md) - Founder Ops Console UI
- [PIN-112](PIN-112-compute-stickiness-scheduler.md) - Compute Stickiness Scheduler
