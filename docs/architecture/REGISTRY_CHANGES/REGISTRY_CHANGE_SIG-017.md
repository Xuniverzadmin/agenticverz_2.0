# Registry Change: SIG-017 CostSnapshot

**Change ID:** RC-002
**Date:** 2025-12-31
**Status:** APPLIED
**Severity:** P2 (Gap Closure)
**Reference:** GAP-002 in L7_L6_FLOWS.md

---

## Change Summary

New signal registration to close GAP-002.

| Field | Value |
|-------|-------|
| Signal UID | SIG-017 |
| Signal Name | CostSnapshot |
| Class | raw |
| Trigger | scheduled_job |
| Producer | cost_snapshot_job.py |
| Producer Layer | L7 |
| Consumer | cost_anomaly_detector.py (SIG-011) |
| Consumer Layer | L4 |
| L2 API | /cost/snapshots |
| Persistence | PostgreSQL |

---

## Rationale

The Cost Snapshot Job produces `cost_snapshots` table records that are consumed by the CostAnomalyDetector (SIG-011). This intermediate signal was previously unregistered, creating a gap in the L7→L6 flow documentation.

### Evidence

**Producer:**
- File: `scripts/ops/cost_snapshot_job.py`
- File: `backend/app/integrations/cost_snapshots.py`
- Trigger: Hourly (:05) and daily (00:30 UTC) via systemd timer
- Output: `cost_snapshots` table records with status PENDING→COMPUTING→COMPLETE

**Consumer:**
- File: `backend/app/services/cost_anomaly_detector.py`
- Reads: COMPLETE snapshots only
- Produces: SIG-011 CostAnomaly

---

## Registry Updates

### SIGNAL_REGISTRY_PYTHON_BASELINE.md

Added to Cost Domain (after SIG-016):

```
| SIG-017 | CostSnapshot | raw | scheduled_job | cost_snapshot_job.py | L7 | cost_anomaly_detector.py | L4 | /cost/snapshots | PostgreSQL |
```

### SIGNAL_REGISTRY_COMPLETE.md

- Updated Cost domain count: 7 → 8
- Added SIG-017 to signal table

---

## Impact

- Closes GAP-002 in L7_L6_FLOWS.md
- Completes L7→L6 flow documentation for cost subsystem
- No code changes required (signal already exists, just unregistered)

---

**Applied by:** Claude Opus 4.5
**Verification:** Static code path verification
