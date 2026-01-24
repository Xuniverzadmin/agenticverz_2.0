# Analytics Domain Lock Registry
# Reference: Phase-2.5A Analytics Extraction

## Locked Artifacts

| File | Status | Pattern Applied | Lock Date |
|------|--------|-----------------|-----------|
| `engines/cost_anomaly_detector.py` | LOCKED | Driver pattern | 2026-01-24 |
| `engines/alert_worker.py` | LOCKED | Driver/Adapter pattern | 2026-01-24 |
| `engines/prediction.py` | LOCKED | Driver pattern | 2026-01-24 |
| `drivers/cost_anomaly_driver.py` | LOCKED | L6 persistence | 2026-01-24 |
| `drivers/alert_driver.py` | LOCKED | L6 persistence | 2026-01-24 |
| `drivers/prediction_driver.py` | LOCKED | L6 persistence | 2026-01-24 |
| `adapters/alert_delivery.py` | LOCKED | L3 HTTP delivery | 2026-01-24 |

## Lock Conditions

A file is locked when:
1. All forbidden imports removed (sqlalchemy direct queries, httpx)
2. Persistence delegated to L6 driver
3. Side-effects delegated to L3 adapter (where applicable)
4. Verification grep passes: `0` matches for forbidden patterns

## Pending Extraction

| File | Status | Notes |
|------|--------|-------|
| `engines/pattern_detection.py` | DORMANT | Explicitly excluded |

## Phase-2.5A Extraction Summary

| Phase | File | Signal Before | Signal After | Status |
|-------|------|---------------|--------------|--------|
| 2.5A-1 | cost_anomaly_detector.py | 19 raw SQL | 0 | COMPLETE |
| 2.5A-2 | alert_worker.py | 8 raw SQL + httpx | 0 | COMPLETE |
| 2.5A-3 | prediction.py | 5 SELECT + 3 WRITE | 0 | COMPLETE |
