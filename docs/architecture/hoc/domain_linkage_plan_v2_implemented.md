# Domain Linkage Plan v2 — Implementation Report

**Date:** 2026-02-09
**Executed by:** Claude Opus 4.6
**Source plan:** `docs/architecture/hoc/domain_linkage_plan_v2.md`
**Commit:** `214513c8` (linkage fixes + governance log scoping)

---

## Test Run Parameters

| Parameter | Value |
|-----------|-------|
| **Run ID** | `run-linkage-test-001` |
| **Tenant ID** | `tenant-test-001` |
| **DB** | Local staging (PostgreSQL via PgBouncer, port 6432) |
| **Alembic revision** | `124_prevention_records_run_id` |

---

## Phase A — Schema Verification (PASS 4/4)

| Check | Column(s) | Result |
|-------|-----------|--------|
| `prevention_records.run_id` | `run_id` | PASS |
| `runs.(policy_violation, policy_draft_count, risk_level)` | all 3 | PASS |
| `incidents.source_run_id` | `source_run_id` | PASS |
| `limit_breaches.run_id` | `run_id` | PASS |

**Note:** Staging DB was stamped at revision 123 without intermediate `CREATE TABLE` migrations. The following tables were missing and created during execution:

| Table | Original Migration | Columns |
|-------|-------------------|---------|
| `incidents` | 037 + 075 + 087 + 096 | 40 |
| `limit_breaches` | 088 | 11 |
| `aos_traces` | 012 + 078 + 080 | 24 |
| `aos_trace_steps` | 012 + 078 + 080 | 22 |
| `audit_ledger` | 091 + 109 | 12 |
| `policy_rules` | 088 | 20 |
| `limits` | 088 | 18 |

Migration 124 was previously applied (creates `prevention_records` table with fallback if missing + adds `run_id` column).

---

## Phase B — Data Linkage Validation (PASS 4/4)

Seeded synthetic test data for `run-linkage-test-001`:

| Query | Count | Result |
|-------|-------|--------|
| `incidents WHERE source_run_id` | 2 | PASS |
| `prevention_records WHERE run_id` | 3 | PASS |
| `limit_breaches WHERE run_id` | 1 | PASS |
| `aos_traces WHERE run_id` | 1 | PASS |

All 4 linkage paths correctly resolve from `run_id` to domain data.

---

## Phase C — L4 Coordinator Execution

### RunEvidenceCoordinator (PASS)

```
run_id: run-linkage-test-001
incidents_caused: 2
  - inc-test-001: Test incident 1 (HIGH)
  - inc-test-002: Test incident 2 (MEDIUM)
policies_evaluated: 3
  - policy-003: Test Policy Rule 3 -> PREVENTED
  - policy-002: Test Policy Rule 2 -> BLOCKED
  - policy-001: Test Policy Rule 1 -> WARNED
limits_hit: 1
  - limit-budget-001: Budget Limit (breach=105.5, threshold=100.0)
decisions_made: 3
  - POLICY_EVALUATION -> PREVENTED
  - POLICY_EVALUATION -> BLOCKED
  - POLICY_EVALUATION -> WARNED
```

**Verdict:** FULL PASS — all 4 evidence categories populated from cross-domain sources.

### RunProofCoordinator (UNSUPPORTED — documented gap)

```
run_id: run-linkage-test-001
integrity.verification_status: UNSUPPORTED
integrity.failure_reason: No trace found for run
```

**Root Cause:** Two issues prevent trace-based proof:

1. **`PostgresTraceStore` broken import (pre-existing):** `pg_store.py` line 51 imports `from .models import TraceRecord, TraceStatus, TraceStep, TraceSummary` but no `models.py` exists in `logs/L6_drivers/`. The models exist at `app/traces/models.py` and `logs/L5_schemas/traces_models.py` but the import path is wrong.

2. **`SQLiteTraceStore` has no data:** In dev mode (default), traces are stored in a SQLite file, not in the Postgres `aos_traces` table. No traces exist in the SQLite store for the test run.

**Gap file:** `backend/app/hoc/cus/logs/L6_drivers/pg_store.py:51`

---

## Phase D — Governance Log Scoping (PASS)

### Direct SQL Validation

```
audit_ledger entries for entity_type IN (POLICY_RULE, LIMIT, INCIDENT):
  Total: 3
  With run_id in after_state: 3
  Without run_id: 0
```

All 3 governance events (incident_created, policy_rule_created, limit_breach_detected) include `run_id` in `after_state` JSONB.

### LogsFacade.get_llm_run_governance() Execution

```
run_id: run-linkage-test-001
total_events: 3
events: 3 GovernanceEventResult objects
metadata:
  tenant_id: tenant-test-001
  run_id: run-linkage-test-001
  source_domain: LOGS
  source_component: AuditLedger
  immutable: true
```

**Verdict:** PASS — `LogsFacade.get_llm_run_governance()` correctly returns run-scoped governance events filtered by `run_id` in `after_state`/`before_state` JSONB.

---

## Acceptance Criteria Evaluation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `RunEvidenceCoordinator` returns at least one of: incident, policy evaluation, limit breach | **PASS** | 2 incidents + 3 policy evals + 1 limit breach |
| `RunProofCoordinator` returns HASH_CHAIN for traced runs | **GAP** | `PostgresTraceStore` broken import; `SQLiteTraceStore` has no data |
| `LogsFacade.get_llm_run_governance()` returns incident-scoped governance events | **PASS** | 3 events returned, all with `run_id` in `after_state` |
| Missing linkage documented with file references and DB evidence | **PASS** | See Gaps section |

**Overall: 3/4 PASS, 1 documented gap (RunProof — pre-existing broken import)**

---

## Gaps & Recommended Fixes

### Gap 1: `PostgresTraceStore` broken import (BLOCKING for run proof in production)

**File:** `backend/app/hoc/cus/logs/L6_drivers/pg_store.py:51`
**Issue:** `from .models import TraceRecord, TraceStatus, TraceStep, TraceSummary` — no `models.py` in `L6_drivers/`
**Models exist at:** `app/traces/models.py` and `logs/L5_schemas/traces_models.py`

**Recommended fix:** Create `backend/app/hoc/cus/logs/L6_drivers/models.py` that re-exports from `app.traces.models`, OR fix the import path in `pg_store.py` to point to `app.traces.models` directly.

**Priority:** HIGH — blocks `RunProofCoordinator` in production when `USE_POSTGRES_TRACES=true`.

### Gap 2: Policy/limit audit events — `run_id` embedding depends on caller context

**Files:**
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py`
- `backend/app/hoc/cus/logs/L6_drivers/audit_ledger_driver.py`

**Issue:** Policy rule creation and limit events only include `run_id` in `after_state` when the calling context provides it. Standalone policy/limit mutations (not triggered by a run) will not have `run_id` — this is correct behavior (not a bug), but means governance log scoping only works for run-triggered events.

**Status:** BY DESIGN — no fix needed.

### Gap 3: Pre-existing `resolution_method` kwarg (non-blocking)

**File:** `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py:222`
**Issue:** Passes `resolution_method=resolution_method` to `audit_ledger_engine.incident_resolved()` which doesn't accept it. Pre-existing, not introduced by linkage changes.

**Priority:** LOW — may cause `TypeError` at runtime if `**kwargs` not used.

---

## Summary

| Phase | Status | Details |
|-------|--------|---------|
| A — Schema Verification | **PASS 4/4** | All required columns exist (after table creation for stamped DB) |
| B — Data Linkage | **PASS 4/4** | All 4 linkage paths resolve correctly |
| C — L4 Coordinators | **PASS 1/2** | RunEvidence: FULL PASS; RunProof: UNSUPPORTED (broken import) |
| D — Governance Logs | **PASS** | 3/3 events scoped by `run_id`, `LogsFacade` returns correctly |

**Domain linkage is operational across 5 domains (Activity, Incidents, Policies, Controls, Logs) with 1 documented gap (trace proof — broken `PostgresTraceStore` import).**
