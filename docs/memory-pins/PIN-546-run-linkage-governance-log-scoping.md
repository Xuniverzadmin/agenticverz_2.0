# PIN-546: Run Linkage & Governance Log Scoping

**Status:** ✅ COMPLETE  
**Created:** 2026-02-09  
**Category:** Architecture / Governance

---

## Summary

Run linkage across incidents, policies, logs, and activity is now mechanically connected for run-scoped evidence/proof. New L6 read drivers bridge run → incident/policy evidence, governance logs support run_id scoping, and activity run impact signals are persisted. Canonical literature + software bibles were updated to reflect these linkages.

---

## Context

Domain linkage audit flagged broken run-level linkage across:
- Incidents (reads + audit trail)
- Policies (evaluation ledger)
- Logs (governance events + traces)
- Activity (run impact signals)

Goal: Ensure a single L4 run-evidence/proof path can resolve incidents, policy evaluations, governance events, and trace evidence for a run.

---

## Changes (By Domain)

### Incidents
- **New L6 driver:** `IncidentRunReadDriver` for async run-scoped reads by `source_run_id`.
- **Run evidence wiring:** RunEvidenceCoordinator now reads incidents via the incidents bridge capability.
- **Audit ledger:** Incident audit events now embed `run_id` in `after_state` (governance log scoping).

### Policies
- **New L6 driver:** `PreventionRecordsReadDriver` for run-scoped policy evaluation reads from `prevention_records`.
- **Run evidence wiring:** RunEvidenceCoordinator reads evaluations from prevention_records (canonical ledger).
- **Writers:** Policy enforcement + policy violation paths mirror evaluations into `prevention_records` with `run_id`.

### Logs
- **Run-scoped governance logs:** `LogsDomainStore.get_governance_events` now filters `before_state`/`after_state` for `run_id`/`source_run_id`.
- **Trace store selection:** Postgres trace store is canonical for prod; SQLite remains dev-only.

### Activity
- **Run impact signals:** `RunMetricsDriver` writes `runs.policy_violation` and `runs.policy_draft_count`.
- **Signal severity mapping:** `RunSignalDriver` persists string risk levels (`NORMAL/NEAR_THRESHOLD/AT_RISK/VIOLATED`).

---

## Migration

**Alembic:** `124_prevention_records_run_id.py`  
Adds `run_id` to `prevention_records` to support run-scoped policy evaluations.

---

## Key Files

| Area | Files |
|------|-------|
| Incidents | `backend/app/hoc/cus/incidents/L6_drivers/incident_run_read_driver.py`, `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py`, `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/incidents_bridge.py` |
| Policies | `backend/app/hoc/cus/policies/L6_drivers/prevention_records_read_driver.py`, `backend/app/hoc/cus/policies/L6_drivers/policy_enforcement_write_driver.py`, `backend/app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py`, `backend/alembic/versions/124_prevention_records_run_id.py` |
| Logs | `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`, `backend/app/hoc/cus/logs/L5_engines/logs_facade.py`, `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/logs_bridge.py` |
| Activity | `backend/app/hoc/cus/activity/L6_drivers/run_metrics_driver.py`, `backend/app/hoc/cus/activity/L6_drivers/run_signal_driver.py`, `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/run_governance_handler.py`, `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` |
| Docs | `literature/hoc_domain/activity/ACTIVITY_CANONICAL_SOFTWARE_LITERATURE.md`, `literature/hoc_domain/incidents/INCIDENT_CANONICAL_SOFTWARE_LITERATURE.md`, `literature/hoc_domain/logs/LOGS_CANONICAL_SOFTWARE_LITERATURE.md`, `literature/hoc_domain/policies/POLICIES_CANONICAL_SOFTWARE_LITERATURE.md`, `literature/hoc_domain/*/SOFTWARE_BIBLE.md` |

---

## Status & Notes

- **Docs updated:** Canonical literature + software bibles for activity, incidents, logs, and policies.
- **Tests:** Not run in this change window.
- **DB:** Migration `124_prevention_records_run_id.py` required for full run-scoped evaluation reads.

---

## Related

- **PIN-519:** System Run Introspection (L4 run evidence/proof entry point)
- **PIN-412:** Incidents/Policies domain design (run linkage intent)
- **PIN-545:** Guardrail violations (DATA-001/LIMITS-001 analysis)
- **PIN-544:** Alembic stamp fix + two-path CI guard

