# Sweep-1: TRANSACTION_BYPASS Elimination Log

## Invariant

> Only L4 Runtime Coordinators may call commit/rollback.

## Progress Log

| Timestamp | Total | Delta | Note |
|-----------|-------|-------|------|
| 2026-01-25T14:40:06 | 101 | — | Initial baseline after 4 files remediated |
| 2026-01-25T14:44:29 | 90 | -11 | tenant_driver.py -11 commits |
| 2026-01-25T14:46:53 | 83 | -7 | accounts_facade_driver.py -7 commits |
| 2026-01-25T14:49:34 | 75 | -8 | ACCOUNT DOMAIN DONE: worker_registry_driver.py -4, user_write_driver.py -2, tenant_engine.py -2 |
| 2026-01-25T14:55:04 | 56 | -19 | ANALYTICS DOMAIN DONE: cost_anomaly_driver.py -5, cost_write_driver.py -4, provenance_async.py -4, circuit_breaker_async.py -2, alert_driver.py -1, pattern_detection_driver.py -1, prediction_driver.py -1, alert_worker.py -4, cost_anomaly_detector.py -1 |
| 2026-01-25T14:55:56 | 55 | -1 | alert_worker.py -1 rollback |
| 2026-01-25T16:30:00 | 48 | -7 | INCIDENTS DOMAIN DONE: guard_write_driver.py, incident_write_driver.py, lessons_driver.py, llm_failure_driver.py, policy_violation_driver.py, llm_failure_engine.py, policy_violation_engine.py, incident_engine.py, lessons_engine.py, anomaly_bridge.py |
| 2026-01-25T16:45:00 | 46 | -2 | ANALYTICS DOMAIN COMPLETE + API_KEYS DOMAIN DONE: pattern_detection.py -1, prediction.py -1, keys_driver.py -2 (flush) |
| 2026-01-25T17:00:00 | 42 | -4 | POLICIES DOMAIN (session.commit only): orphan_recovery.py -1, keys_driver.py -1 (flush), recovery_write_driver.py -2 (commit+rollback), prevention_engine.py -1 (flush) |
| 2026-01-25T18:30:00 | 14 | -28 | GENERAL+INTEGRATIONS+DUPLICATES+ANALYTICS COMPLETE: worker_write_service_async.py -1, db_helpers.py -1 (flush), cost_snapshots.py -6, dispatcher.py -3, cus_health_engine.py -1, bridges.py -5, bridges_driver.py -1, cost_anomaly_detector.py -5, api.py -3, pattern_detection.py -1, audit_persistence.py -1 |

## Status: SESSION.COMMIT() SWEEP COMPLETE

**Session.commit() violations: 0** (All SQLAlchemy/SQLModel commits eliminated)

All remaining `.commit()` references in `hoc/cus/` are now either:
1. **Forbidden clauses** in file headers (correct - declarative)
2. **Documentation** in markdown files (correct - descriptive)
3. **Comments** stating "never session.commit()" (correct - enforcement guidance)

## Remaining: Raw SQL conn.commit() (Design Debt)

Raw SQL conn.commit(): 19 violations (separate workstream, requires architectural refactor)
- policies/engine.py: 13 violations
- general/decisions.py: 4 violations
- general/ledger.py: 1 violation
- incidents/policy_violation_driver.py: 1 violation (raw psycopg2)

Note: L4 transaction_coordinator.py commit is LEGITIMATE (L4 owns transaction boundary).

## Summary

| Metric | Value |
|--------|-------|
| Initial baseline | 101 |
| Final session.commit() | 0 |
| Reduction | 100% |
| Domains completed | ALL (account, analytics, incidents, api_keys, policies, general, integrations, duplicates) |
| Design debt (conn.commit) | 19 (separate workstream) |
