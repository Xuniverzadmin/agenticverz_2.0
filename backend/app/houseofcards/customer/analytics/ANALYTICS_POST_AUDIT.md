# Analytics Domain Post-Extraction Audit
# Reference: Phase-2.5A Analytics Extraction
# Date: 2026-01-24

## Audit Scope

- `engines/cost_anomaly_detector.py`
- `engines/alert_worker.py`
- `engines/prediction.py`
- `drivers/cost_anomaly_driver.py`
- `drivers/alert_driver.py`
- `drivers/prediction_driver.py`
- `adapters/alert_delivery.py`

---

## 1. Layer Purity

### Engines

| File | Status | Notes |
|------|--------|-------|
| `cost_anomaly_detector.py` | TRANSITIONAL | Lines 508, 865, 885, 906, 909 marked `TRANSITIONAL_READ_OK` |
| `alert_worker.py` | PASS | Only `async_session_context()` usage (for driver) |
| `prediction.py` | PASS | No forbidden patterns |

**Transitional Items (cost_anomaly_detector.py):**
- Line 508-513: Budget ORM query (`TRANSITIONAL_READ_OK`)
- Line 865-874: Deduplication ORM query (`TRANSITIONAL_READ_OK`)
- Lines 885, 906, 909: `session.add()` / `session.commit()` for `persist_anomalies` method

These were explicitly acknowledged during Phase-2.5A-1 and are scheduled for future driver migration.

### Drivers

| File | Status | Notes |
|------|--------|-------|
| `cost_anomaly_driver.py` | PASS | No decision logic (thresholds, confidence) |
| `alert_driver.py` | PASS | Uses `max_attempts` column reference only (not constant) |
| `prediction_driver.py` | PASS | No domain constants |

**Result: PASS (with documented transitional items)**

---

## 2. Inventory Consistency

| Driver | Actual Methods | Inventory Claimed | Status |
|--------|----------------|-------------------|--------|
| `cost_anomaly_driver.py` | 20 | 19 | MINOR DRIFT (+1) |
| `alert_driver.py` | 10 | 9 | MINOR DRIFT (+1) |
| `prediction_driver.py` | 7 | 7 | MATCH |
| `alert_delivery_adapter.py` | 2 | 2 | MATCH |

**Note:** +1 drift is from `commit()` helper method not counted in inventory.

**Duplicate Authorities:** None detected.
**Overlapping Write Ownership:** None detected.

**Result: PASS (inventory counts are approximate, method coverage verified)**

---

## 3. Import Graph Hygiene

### Cross-Domain Imports

| File | Import | Line | Status |
|------|--------|------|--------|
| `cost_anomaly_detector.py` | `app.houseofcards.customer.incidents.bridges` | 962 | EXPECTED |
| `cost_anomaly_detector.py` | `app.houseofcards.customer.incidents.bridges.anomaly_bridge` | 968, 1034 | EXPECTED |

**Assessment:** These imports are for the `AnomalyIncidentBridge` which is documented as "bridge excluded; must be incidents-owned". The analytics engine calls INTO incidents domain, not the reverse. This is the correct direction for cross-domain communication.

### Other Imports

| File | Import | Status |
|------|--------|--------|
| `prediction.py` | `app.houseofcards.customer.general.utils.time` | ALLOWED (shared utility) |

**Result: PASS (bridge imports are incidents-owned, direction is correct)**

---

## 4. Adapter Boundaries

| Check | Result |
|-------|--------|
| HTTP imports in engines | 0 (PASS) |
| HTTP imports in adapter | `httpx` at line 43 (EXPECTED) |
| Adapter interface explicit | Lines 142, 181 use `_adapter.close()`, `_adapter.send_alert()` |

**Result: PASS**

---

## 5. Runtime Gates

### Engines - Forbidden Imports

| File | `from sqlalchemy import (and_\|select\|...)` | Status |
|------|-----------------------------------------------|--------|
| `cost_anomaly_detector.py` | 0 | PASS |
| `alert_worker.py` | 0 | PASS |
| `prediction.py` | 0 | PASS |

### Drivers - Domain Constants

| File | THRESHOLD/CONFIDENCE constants | Status |
|------|--------------------------------|--------|
| `cost_anomaly_driver.py` | 0 | PASS |
| `alert_driver.py` | 0 | PASS |
| `prediction_driver.py` | 0 | PASS |

**Result: PASS**

---

## 6. Dormant Confirmation

| Check | Result |
|-------|--------|
| File exists | YES |
| MD5 hash | `cdabc665476c27945fcfa3e779b939cf` |
| Last modified | 2026-01-23 09:50:33 (before Phase-2.5A) |
| Phase-2.5A markers | 0 |

**Result: PASS (pattern_detection.py untouched)**

---

## Summary

| Checklist Item | Result |
|----------------|--------|
| 1. Layer Purity | PASS (with transitional items documented) |
| 2. Inventory Consistency | PASS |
| 3. Import Graph Hygiene | PASS |
| 4. Adapter Boundaries | PASS |
| 5. Runtime Gates | PASS |
| 6. Dormant Confirmation | PASS |

---

## Transitional Items (For Future Work)

The following items in `cost_anomaly_detector.py` remain as transitional ORM operations:

1. **Budget Query** (lines 508-513): Simple ORM select for active budgets
2. **Deduplication Query** (lines 865-874): ORM query to find existing anomalies
3. **Persist Anomalies** (lines 885, 906, 909): `session.add()` and `session.commit()` for anomaly records

These are marked `TRANSITIONAL_READ_OK` and scheduled for driver migration in a future phase.

---

## Recommendation

**CLOSE**

All gates pass. The analytics domain is structurally clean for the completed Phase-2.5A scope. Transitional items are documented and do not block domain closure.
