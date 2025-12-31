# L7 → L6 Runtime Integration

**Status:** VERIFIED (all gaps closed)
**Version:** 1.0.1
**Generated:** 2025-12-31
**Method:** L7 producer survey + L6 consumption verification

---

## Scope

This document records all L7-produced artifacts that are consumed by L6 or higher runtime layers.

**L7 → L6 boundary rule:**
- L7 produces operational facts
- L6 consumes for runtime behavior
- Flow must be explicit and registered

---

## L7 Producers Identified

| Producer | Output | L6 Consumer | Persistence | Status |
|----------|--------|-------------|-------------|--------|
| Failure Aggregation | candidate_failure_patterns.json | failure_catalog expansion | R2 + PostgreSQL | ✅ VERIFIED |
| Graduation Evaluator | GraduationStatus | capability_lockouts (L6) | PostgreSQL | ✅ VERIFIED (RC-001) |
| M10 Metrics Collector | Prometheus gauges | Grafana/Alerting | Prometheus | ✅ VERIFIED (L8) |
| M10 Orchestrator | Maintenance state | None (control-plane) | PostgreSQL + Redis | ✅ L7-INTERNAL |
| Cost Snapshot Job | cost_snapshots records | CostAnomalyDetector | PostgreSQL | ✅ VERIFIED (RC-002) |
| CostSim Canary | CanaryReport + CB state | costsim.py | PostgreSQL | ✅ VERIFIED |
| R2 Retry Worker | Retried uploads | failure_catalog | R2 | ✅ VERIFIED |

---

## Flow Details

### Verified Flows

#### 1. Failure Aggregation → L6

| Field | Value |
|-------|-------|
| Producer | `jobs/failure_aggregation.py` |
| Signal | SIG-206 (FailureCatalogMatch) |
| Output | candidate_failure_patterns.json |
| Persistence | Cloudflare R2 + failure_pattern_exports table |
| L6 Consumer | Failure catalog expansion |
| Verified | YES |

#### 2. Graduation Evaluator → L6

| Field | Value |
|-------|-------|
| Producer | `jobs/graduation_evaluator.py` |
| Signal | SIG-100 (GraduationStatus) |
| Output | graduation_history, m25_graduation_status, capability_lockouts |
| Persistence | PostgreSQL |
| L6 Consumer | capability_lockouts (runtime feature gating) |
| Verified | YES (corrected via RC-001) |

#### 3. CostSim Canary → L6

| Field | Value |
|-------|-------|
| Producer | `costsim/canary.py` |
| Signal | SIG-015, SIG-016 |
| Output | CanaryReport, circuit breaker state |
| Persistence | PostgreSQL |
| L6 Consumer | costsim.py (V2 validation) |
| Verified | YES |

#### 4. R2 Retry Worker → L6

| Field | Value |
|-------|-------|
| Producer | `jobs/storage.py` |
| Signal | Part of SIG-206 |
| Output | Retried R2 uploads |
| Persistence | Cloudflare R2 |
| L6 Consumer | failure_catalog |
| Verified | YES (subsystem of Failure Aggregation) |

---

## Open Gaps

### GAP-002: Cost Snapshot Job — ✅ RESOLVED

**Status:** RESOLVED via RC-002 (2025-12-31)

| Field | Value |
|-------|-------|
| Producer | `scripts/ops/cost_snapshot_job.py`, `integrations/cost_snapshots.py` |
| Trigger | Hourly (:05) and daily (00:30 UTC) via systemd timer |
| Output | cost_snapshots table records (PENDING→COMPUTING→COMPLETE) |
| Persistence | PostgreSQL |
| L6 Consumer | CostAnomalyDetector (reads COMPLETE snapshots only) |
| Signal | **SIG-017 CostSnapshot** |

**Resolution:** Registered as SIG-017 CostSnapshot.

**Registry Entry (applied):**
```
| SIG-017 | CostSnapshot | raw | scheduled_job | cost_snapshot_job.py | L7 | cost_anomaly_detector.py | L4 | /cost/snapshots | PostgreSQL |
```

**Change Record:** `REGISTRY_CHANGES/REGISTRY_CHANGE_SIG-017.md`

---

### GAP-003: M10 Orchestrator Classification — ✅ RESOLVED

**Status:** RESOLVED (2025-12-31)
**Decision:** Control-plane only (Option A)

| Field | Value |
|-------|-------|
| Producer | `scripts/ops/m10_orchestrator.py` |
| Trigger | Every 5 minutes via systemd timer |
| Output | Processed outbox events, dead-letter ACKs, matview refreshes |
| Persistence | PostgreSQL + Redis |
| L6 Consumer | None (coordinates existing L7→L6 flows) |
| Signal | **NOT A SIGNAL** — control-plane coordinator |

**Classification:** L7-internal maintenance. The orchestrator:
- Coordinates existing signals (does not produce new ones)
- Triggers refresh/cleanup of existing artifacts
- Has no independent L6 consumer

**Resolution:** Documented as L7-internal flow in L7_INTERNAL_FLOWS.md. No signal registration required.

**Reference:** L7_INTERNAL_FLOWS.md (systemd services section)

---

## Required Actions

| Priority | Action | Target |
|----------|--------|--------|
| P1 | ~~Resolve GAP-001~~ | ~~SIG-100 semantics~~ ✅ DONE (RC-001) |
| P2 | ~~Register GAP-002 as SIG-017~~ | ~~SIGNAL_REGISTRY_COMPLETE.md~~ ✅ DONE (RC-002) |
| P3 | ~~Classify GAP-003~~ | ~~This document + L7_INTERNAL_FLOWS.md~~ ✅ DONE (control-plane) |

---

## Registry Change History

| Change | Date | Description |
|--------|------|-------------|
| RC-002 | 2025-12-31 | SIG-017 registered: CostSnapshot (closes GAP-002) |
| RC-001 | 2025-12-31 | SIG-100 corrected: L4→L5 producer, In-memory→PostgreSQL |

---

## Verification Summary

| Category | Count | Status |
|----------|-------|--------|
| L7 Producers | 7 | Identified |
| Verified L7→L6 flows | 6 | ✅ All verified |
| L7-Internal (control-plane) | 1 | ✅ M10 Orchestrator |
| Open gaps | 0 | All resolved |
| L7→L8 flows | 1 | ✅ Metrics to Prometheus |

---

**Generated by:** Claude Opus 4.5
**Cross-reference:** L7_INTERNAL_FLOWS.md, SIGNAL_REGISTRY_COMPLETE.md
**Next:** L6_INTERNAL_FLOWS.md
