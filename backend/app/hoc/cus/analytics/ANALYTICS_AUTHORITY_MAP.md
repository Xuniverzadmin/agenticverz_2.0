# ANALYTICS AUTHORITY MAP

**Status:** PHASE-2.5A-1 COMPLETE — cost_anomaly_detector.py EXTRACTED
**Date:** 2026-01-24
**Reference:** PIN-469 (Policies complete), R1 Resolution complete

---

## 1. Engine Inventory

| Engine | DB Signals | Layer Header | Status |
|--------|------------|--------------|--------|
| cost_anomaly_detector.py | 53 | L4 | ACTIVE - needs extraction |
| alert_worker.py | 18 | (none) | ACTIVE - needs extraction |
| prediction.py | 8 | L4 (Advisory) | ADVISORY - low priority |
| pattern_detection.py | 6 | L4 | DORMANT BY DESIGN |
| coordinator.py | 1 | L5 | Delegates to audit_persistence |
| cost_write_service.py | 0 | L4 | ALREADY EXTRACTED |
| ai_console_panel_engine.py | 0 | - | No DB access |
| canary.py | 0 | - | No DB access |
| cb_sync_wrapper.py | 0 | - | No DB access |
| config.py | 0 | - | No DB access |
| costsim_models.py | 0 | - | No DB access |
| datasets.py | 0 | - | No DB access |
| divergence.py | 0 | - | No DB access |
| envelope.py | 0 | - | No DB access |
| metrics.py | 0 | - | No DB access |
| provenance.py | 0 | - | No DB access |
| s1_retry_backoff.py | 0 | - | No DB access |
| s2_cost_smoothing.py | 0 | - | No DB access |
| sandbox.py | 0 | - | No DB access |

**Summary:** 4 engines with DB access, 2 need extraction (cost_anomaly_detector, alert_worker)

---

## 2. Authority Classification

### 2.1 cost_anomaly_detector.py — MIXED (READ + WRITE)

**Writes:**
| Table | Operation |
|-------|-----------|
| cost_breach_history | INSERT, UPDATE (DO UPDATE) |
| cost_drift_tracking | INSERT, UPDATE |
| cost_anomalies | INSERT (via ORM) |

**Reads:**
| Table | Operation |
|-------|-----------|
| cost_records | SELECT (aggregations, counts) |
| cost_budgets | SELECT (via ORM) |
| cost_breach_history | SELECT (consecutive check) |
| cost_drift_tracking | SELECT (rolling avg) |
| cost_anomalies | SELECT (deduplication) |

**Classification:** WRITE-AUTHORITATIVE

---

### 2.2 alert_worker.py — MIXED (READ + WRITE)

**Writes:**
| Table (Model) | Operation |
|---------------|-----------|
| CostSimAlertQueueModel | INSERT, UPDATE, DELETE |
| CostSimCBIncidentModel | UPDATE (alert_sent flag) |

**Reads:**
| Table (Model) | Operation |
|---------------|-----------|
| CostSimAlertQueueModel | SELECT (pending, failed) |

**Classification:** WRITE-AUTHORITATIVE

---

### 2.3 prediction.py — MIXED (READ + WRITE)

**Writes:**
| Table (Model) | Operation |
|---------------|-----------|
| PredictionEvent | INSERT (commit) |

**Reads:**
| Table (Model) | Operation |
|---------------|-----------|
| PatternFeedback | SELECT |
| WorkerRun | SELECT (tenant runs) |

**Classification:** WRITE (advisory predictions) — LOW PRIORITY

---

### 2.4 pattern_detection.py — MIXED (READ + WRITE)

**Writes:**
| Table (Model) | Operation |
|---------------|-----------|
| PatternFeedback | INSERT (commit) |

**Reads:**
| Table (Model) | Operation |
|---------------|-----------|
| WorkerRun | SELECT |

**Classification:** WRITE (feedback) — DORMANT BY DESIGN (do not activate)

---

### 2.5 cost_write_service.py — EXTRACTED

Uses `CostWriteDriver` for:
- FeatureTag (CRUD)
- CostRecord (CRUD)
- CostBudget (CRUD)

**Classification:** ALREADY EXTRACTED — NO WORK NEEDED

---

### 2.6 coordinator.py — DELEGATED

- Layer: L5 (not L4)
- Delegates to `audit_persistence.py` driver
- Only passes Session, no direct DB access

**Classification:** NO EXTRACTION NEEDED (already uses L6)

---

## 3. Driver Inventory Check

### 3.1 Existing Drivers

| Driver | Tables/Operations | Usable By |
|--------|-------------------|-----------|
| cost_write_driver.py | FeatureTag, CostRecord, CostBudget | cost_write_service.py |
| audit_persistence.py | coordination_audit_records | coordinator.py |
| circuit_breaker.py | circuit breaker state | - |
| circuit_breaker_async.py | circuit breaker state (async) | - |
| leader.py | PostgreSQL advisory locks | alert_worker.py |
| manager.py | envelope lifecycle | - |
| provenance_async.py | provenance logging | - |
| killswitch.py | killswitch operations | - |

### 3.2 Driver Gaps (Methods Needed)

**For cost_anomaly_detector.py:**
- `fetch_cost_records_aggregates()` — daily spend, baseline calculations
- `fetch_cost_budget()` — active budget for tenant
- `insert_breach_history()` — consecutive breach tracking
- `update_breach_history()` — mark resolved
- `fetch_consecutive_breaches()` — breach count check
- `insert_drift_tracking()` — drift state
- `update_drift_tracking()` — drift state update
- `fetch_drift_tracking()` — current drift state
- `insert_anomaly()` — persist CostAnomaly
- `fetch_existing_anomaly()` — deduplication check

**For alert_worker.py:**
- `fetch_pending_alerts()` — queue processing
- `update_alert_status()` — mark sent/failed
- `insert_alert()` — enqueue new alert
- `delete_old_alerts()` — cleanup
- `update_incident_alert_sent()` — mark incident notified
- `fetch_alert_stats()` — queue metrics

**For prediction.py (LOW PRIORITY):**
- `fetch_pattern_feedback()` — read feedback
- `fetch_worker_runs()` — run statistics
- `insert_prediction_event()` — persist prediction

---

## 4. Cross-Domain Dependencies

### 4.1 Reads From

| Engine | Reads From | Tables |
|--------|------------|--------|
| prediction.py | tenant.WorkerRun | worker_runs (runs domain) |
| pattern_detection.py | tenant.WorkerRun | worker_runs (runs domain) |

### 4.2 Writes Outside Analytics

| Engine | Writes To | Via | RISK |
|--------|-----------|-----|------|
| cost_anomaly_detector.py | ~~incidents~~ | ~~`cross_domain.create_incident_from_cost_anomaly_sync`~~ | ~~**CROSS-DOMAIN WRITE**~~ **RESOLVED** |
| alert_worker.py | Alertmanager | HTTP POST | **EXTERNAL SIDE EFFECT** |

**R1 RESOLUTION:** `cost_anomaly_detector.py` no longer writes to incidents directly.
- Analytics emits `CostAnomalyFact` (pure data)
- Incidents domain owns incident creation via `AnomalyIncidentBridge`
- Bridge location: `app/houseofcards/customer/incidents/bridges/anomaly_bridge.py`

---

## 5. Risk Flags

### R1. Hidden Cross-Domain Write — **RESOLVED**

**Status:** ✅ RESOLVED (2026-01-24)

**Previous Issue:**
```python
# REMOVED
from app.services.governance.cross_domain import create_incident_from_cost_anomaly_sync
```

**Resolution Applied:** Option 1 + 3 (Combined)

| Component | Location | Authority |
|-----------|----------|-----------|
| `CostAnomalyFact` | `incidents/bridges/anomaly_bridge.py` | Pure data (no DB) |
| `AnomalyIncidentBridge` | `incidents/bridges/anomaly_bridge.py` | Incidents-owned |
| `run_anomaly_detection_with_facts` | `cost_anomaly_detector.py` | Emits facts only |

**Authority Model (Final):**
- **Analytics:** Detect anomalies, compute severity/confidence, emit `CostAnomalyFact`
- **Incidents:** Decide if anomaly warrants incident creation (bridge)
- **Bridge:** Translation boundary (owned by incidents)

**Import Hygiene:**
- Analytics imports zero incident writers
- Only local import of `CostAnomalyFact` (in function scope, not module level)

---

### R2. External Side Effect (MEDIUM)

**File:** alert_worker.py

Sends HTTP POST to Alertmanager. Marked with:
```python
FEATURE_INTENT = FeatureIntent.EXTERNAL_SIDE_EFFECT
RETRY_POLICY = RetryPolicy.NEVER
```

Already properly classified. No extraction issue.

---

### R3. Mixed Authority in Single File (MEDIUM)

**File:** cost_anomaly_detector.py

Contains:
- Read operations (aggregations)
- Write operations (breach/drift tracking)
- Cross-domain side effect (incident creation)

This file has the **highest complexity** and should be extracted carefully.

---

### R4. Dormant Code (LOW)

**File:** pattern_detection.py

Marked "DORMANT BY DESIGN" — do not wire or activate.

---

## 6. Extraction Order Proposal

### P0 — Must Extract First

| Engine | Reason | Est. Driver Methods |
|--------|--------|---------------------|
| cost_anomaly_detector.py | 53 signals, cross-domain write, high complexity | 10 |

**Note:** Resolve cross-domain incident write before or during extraction.

---

### P1 — Extract Second

| Engine | Reason | Est. Driver Methods |
|--------|--------|---------------------|
| alert_worker.py | 18 signals, external side effect, queue management | 6 |

---

### P2 — Optional / Low Priority

| Engine | Reason | Est. Driver Methods |
|--------|--------|---------------------|
| prediction.py | Advisory only, low risk, 8 signals | 3 |

---

### DO LAST (or never)

| Engine | Reason |
|--------|--------|
| pattern_detection.py | DORMANT BY DESIGN — do not activate |
| coordinator.py | L5, already uses L6 driver |
| cost_write_service.py | Already extracted |

---

## 7. Estimated Driver Count

| Priority | Engines | New Driver Methods |
|----------|---------|-------------------|
| P0 | cost_anomaly_detector.py | ~10 methods |
| P1 | alert_worker.py | ~6 methods |
| P2 | prediction.py | ~3 methods |
| **Total** | 3 engines | **~19 methods** |

Existing drivers may absorb some methods (cost_write_driver.py for budget reads).

---

## 8. Open Questions (Before Extraction)

### Q1. Is analytics write-authoritative or read-derived?

**Answer:** WRITE-AUTHORITATIVE for:
- cost_breach_history
- cost_drift_tracking
- cost_anomalies
- CostSimAlertQueueModel

READ-DERIVED for:
- cost_records (reads only, writes elsewhere)
- worker_runs (reads only, runs domain owns)

---

### Q2. Are alerts written here or elsewhere?

**Answer:** Alert queue (CostSimAlertQueueModel) is written HERE.
Alertmanager delivery is an external side effect from here.

---

### Q3. Does analytics depend on policy/incident internals?

**Answer (Updated after R1 Resolution):**
- **Incidents:** ~~YES~~ → **NO** — R1 resolved, analytics emits facts only
- **Policies:** NO direct dependency found
- **Logs:** NO direct dependency found

**Action Required:** ~~Resolve incident write dependency before extraction.~~ **DONE**

---

## 9. Recommendation

1. ~~**Resolve R1 first** — cross-domain incident write must be addressed~~ ✅ **DONE**
2. **Extract P0 (cost_anomaly_detector.py)** — highest complexity, highest risk
3. **Extract P1 (alert_worker.py)** — queue management
4. **Skip P2 and dormant engines** — low value, advisory only

**Estimated effort:** 2 engines, ~16 driver methods

---

## 10. R1 Resolution Summary (2026-01-24)

### Files Created

| File | Purpose |
|------|---------|
| `incidents/bridges/__init__.py` | Bridge module exports |
| `incidents/bridges/anomaly_bridge.py` | Anomaly-to-incident translation |

### Files Modified

| File | Change |
|------|--------|
| `analytics/engines/cost_anomaly_detector.py` | Removed cross_domain import, added fact emission |

### Authority After Fix

| Domain | Responsibility |
|--------|----------------|
| Analytics | Detect anomalies, compute severity/confidence |
| Incidents | Decide if anomaly → incident |
| Bridge | Translation boundary (owned by incidents) |

### Verification

- [x] Analytics has no incident/governance imports
- [x] Bridge file exists under incidents
- [x] Bridge uses only incident engines/drivers
- [x] Authority map updated
- [x] No CI violations introduced (verified: no cross-domain imports in analytics engines)

---

## 11. Phase-2.5A-1 Extraction Summary (2026-01-24)

### Engine: cost_anomaly_detector.py

**Status:** ✅ EXTRACTION COMPLETE

### Driver Created

| File | Location | Methods |
|------|----------|---------|
| `cost_anomaly_driver.py` | `analytics/drivers/` | 19 methods |

### Methods Extracted

| Method Group | Driver Methods | Status |
|--------------|----------------|--------|
| M1: Entity spike | `fetch_entity_baseline`, `fetch_entity_today_spend` | ✅ DONE |
| M2: Tenant spike | `fetch_tenant_baseline`, `fetch_tenant_today_spend` | ✅ DONE |
| M3: Sustained drift | `fetch_rolling_avg`, `fetch_baseline_avg` | ✅ DONE |
| M4: Budget detection | `fetch_daily_spend`, `fetch_monthly_spend` | ✅ DONE |
| M5: Breach tracking | `fetch_breach_exists_today`, `insert_breach_history`, `fetch_consecutive_breaches` | ✅ DONE |
| M6: Drift tracking | `fetch_drift_tracking`, `update_drift_tracking`, `insert_drift_tracking` | ✅ DONE |
| M7: Drift reset | `reset_drift_tracking` | ✅ DONE |
| M8: Cause derivation | `fetch_retry_comparison`, `fetch_prompt_comparison`, `fetch_feature_concentration`, `fetch_request_comparison` | ✅ DONE |
| M9: Anomaly persistence | ORM retained in engine | N/A |

### Engine Cleanup

| Change | Reason |
|--------|--------|
| Removed `text` import | No longer needed (driver handles SQL) |
| Retained ORM `select()` | Simple entity queries stay in engine |
| Added driver initialization | `self._driver = get_cost_anomaly_driver(session)` |

### Remaining in Engine (Intentional)

| Operation | Why Retained |
|-----------|--------------|
| `session.exec(select(CostBudget))` | Simple ORM entity query |
| `session.exec(select(CostAnomaly))` | Simple ORM deduplication query |
| `session.add()` / `session.commit()` | ORM persistence in persist_anomalies |

### Authority After Extraction

| Layer | Responsibility |
|-------|----------------|
| L4 Engine | Threshold comparisons, severity classification, anomaly type decisions |
| L6 Driver | All raw SQL aggregations, INSERT/UPDATE operations |

### Verification

- [x] All raw SQL (`text()`) removed from engine
- [x] Driver handles all DB aggregation queries
- [x] Engine retains business logic only
- [x] No session.execute calls remain (only session.exec for ORM)
- [x] Driver inventory updated in header

---

## 12. Next: Phase-2.5A-2 (alert_worker.py)

**Status:** PENDING

| Engine | Priority | Est. Driver Methods |
|--------|----------|---------------------|
| alert_worker.py | P1 | ~6 methods |

Methods needed:
- `fetch_pending_alerts`
- `update_alert_status`
- `insert_alert`
- `delete_old_alerts`
- `update_incident_alert_sent`
- `fetch_alert_stats`
