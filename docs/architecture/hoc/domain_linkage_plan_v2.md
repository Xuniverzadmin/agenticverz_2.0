# Domain Linkage Plan v2 (HOC)

**Date:** 2026-02-09  
**Scope:** LLM run monitoring linkages across Activity, Incidents, Policies, Controls, Logs  
**Audience:** Claude execution plan  
**Goal:** Verify and fix run-scoped linkage paths so `run_id` connects activity, incidents, policy evaluations, limit breaches, governance logs, and traces.

---

## 1. Definitions (Canonical)

**Run ID:** `runs.id` (string, not UUID).  
**Canonical incident linkage:** `incidents.source_run_id`  
**Canonical policy evaluation ledger:** `prevention_records`  
**Canonical limit breach linkage:** `limit_breaches.run_id`  
**Canonical trace store (prod):** Postgres `aos_traces` / `aos_trace_steps`  
**Governance logs:** `audit_ledger` with `before_state` / `after_state` dicts

---

## 2. Evidence Sources (Must Read Before Changes)

- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_evidence_coordinator.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_proof_coordinator.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/incidents_bridge.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/policies_bridge.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/controls_bridge.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py`
- `backend/app/hoc/cus/incidents/L6_drivers/incident_run_read_driver.py`
- `backend/app/hoc/cus/policies/L6_drivers/prevention_records_read_driver.py`
- `backend/app/hoc/cus/controls/L6_drivers/limits_read_driver.py`
- `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`
- `backend/app/hoc/cus/logs/L5_engines/logs_facade.py`
- `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py`
- `backend/app/hoc/cus/activity/L6_drivers/run_signal_driver.py`
- `backend/app/hoc/cus/activity/L6_drivers/run_metrics_driver.py`
- `backend/alembic/versions/124_prevention_records_run_id.py`

---

## 3. Audit Workflow (Phased)

### Phase A — Schema Verification (Blocking)

Run these queries in the target DB:

```sql
SELECT column_name
FROM information_schema.columns
WHERE table_name='prevention_records' AND column_name='run_id';

SELECT column_name
FROM information_schema.columns
WHERE table_name='runs'
  AND column_name IN ('policy_violation','policy_draft_count','risk_level');

SELECT column_name
FROM information_schema.columns
WHERE table_name='incidents' AND column_name='source_run_id';

SELECT column_name
FROM information_schema.columns
WHERE table_name='limit_breaches' AND column_name='run_id';
```

**Stop** if any required column is missing and apply the migration before continuing.

---

### Phase B — Data Linkage Validation (Run ID Focus)

Pick a real `run_id` and check linkage counts:

```sql
SELECT COUNT(*) FROM incidents WHERE source_run_id = '<run_id>';
SELECT COUNT(*) FROM prevention_records WHERE run_id = '<run_id>';
SELECT COUNT(*) FROM limit_breaches WHERE run_id = '<run_id>';
SELECT COUNT(*) FROM aos_traces WHERE run_id = '<run_id>';
```

**Expected:** At least one signal in any relevant domain for a non-trivial run.

---

### Phase C — L4 Orchestration Checks (Runtime Path)

Execute the L4 coordinators and confirm they return data:

- `RunEvidenceCoordinator.get_run_evidence(session, tenant_id, run_id)`
- `RunProofCoordinator.get_run_proof(session, tenant_id, run_id)`

**Expected:**  
Run evidence includes incidents, policy evaluations, and limits when present.  
Run proof returns HASH_CHAIN integrity for traced runs.

---

### Phase D — Governance Logs (Run‑Scoped Filtering)

Validate governance log scoping by run:

```sql
SELECT event_type, entity_type, after_state
FROM audit_ledger
WHERE entity_type IN ('POLICY_RULE','LIMIT','POLICY_PROPOSAL','INCIDENT')
ORDER BY created_at DESC
LIMIT 50;
```

**Expected:** Incident entries include `after_state.run_id`.  
If policy/limit events lack `run_id`, note as a gap for optional fix.

---

## 4. Task TODO List (Execute in Order)

### Task 1 — Migration Safety

1. Confirm `prevention_records.run_id` exists.  
2. If missing, apply `124_prevention_records_run_id.py` and re‑verify.

### Task 2 — Run‑Scoped Evidence Validation

1. Validate incident linkage via `incidents.source_run_id`.  
2. Validate policy evaluation linkage via `prevention_records.run_id`.  
3. Validate limit breach linkage via `limit_breaches.run_id`.  
4. Validate trace linkage via `aos_traces.run_id`.

### Task 3 — L4 Coordinator Execution

1. Execute `RunEvidenceCoordinator.get_run_evidence()` with a run that has at least one incident or policy evaluation.  
2. Execute `RunProofCoordinator.get_run_proof()` with a run that has traces.  
3. Record outputs for the audit log.

### Task 4 — Governance Log Scoping

1. Run `LogsFacade.get_llm_run_governance()` for the same `run_id`.  
2. Compare returned events to `audit_ledger` entries.  
3. If policy/limit events lack `run_id`, create a follow‑up fix list.

### Task 5 — Report + Evidence Package

1. Provide a short report with run_id, counts, and coordinator outputs.  
2. Capture any gaps with file references and exact paths.

---

## 5. Fix Candidates (Only If Gaps Are Confirmed)

**Fix A — Policy/Limit audit events missing run_id**  
Add `run_id` to `after_state` when emitting policy/limit audit events (if run_id is available in the calling context).

Likely touchpoints:
- `backend/app/hoc/cus/logs/L6_drivers/audit_ledger_driver.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py`

**Fix B — Trace store mismatch**  
Ensure `USE_POSTGRES_TRACES=true` for environments where run proof is expected.

---

## 6. Acceptance Criteria

- `RunEvidenceCoordinator` returns at least one of: incident, policy evaluation, limit breach for a real run with evidence.
- `RunProofCoordinator` returns HASH_CHAIN for traced runs.
- `LogsFacade.get_llm_run_governance()` returns incident‑scoped governance events for the same run.
- Any missing linkage is documented with precise file references and DB evidence.

---

## 7. Out of Scope (Explicitly Deferred)

- `incidents.source_run_id` → FK hardening beyond existing guardrails.
- Policy vs. cost‑budget table unification.
- New schema fields or cross‑domain refactors not strictly required for run‑scoped linkage.

---

## 8. Output Template (For Claude to Fill)

**Run ID tested:** `<run_id>`  
**Tenant ID:** `<tenant_id>`  
**Incident count:** `<n>`  
**Policy evaluation count:** `<n>`  
**Limit breach count:** `<n>`  
**Trace count:** `<n>`  
**RunEvidenceCoordinator result:** `<summary>`  
**RunProofCoordinator result:** `<summary>`  
**Governance events for run:** `<summary>`  
**Gaps:** `<list>`  
**Recommended fixes:** `<list>`
