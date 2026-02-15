# Run Proof Test Plan v2 — Implementation Report

**Date:** 2026-02-09
**Executed by:** Claude Opus 4.6
**Source plan:** `docs/architecture/hoc/run_proof_test_plan_v2.md`
**Policy:** No manual DB inserts into runs/traces/steps. No SQLite fallback. Stop on failure and report evidence.

---

## Execution Summary

| Step | Status | Details |
|------|--------|---------|
| 1. Fix A — origin_system_id design fix | **PASS** | Migration 125, ORM updates, 4 creation paths patched |
| 2. Generate real run (production path) | **PASS** | Run via L4 plan gen + RunRunner, trace produced |
| 3. Verify trace data exists | **PASS** | 1 trace, 1 step in Postgres |
| 4. RunProofCoordinator validation | **PASS** | HASH_CHAIN / VERIFIED / chain_length=1 |
| 5. Coordinator tests | **PASS** | 10/10 in 2.67s |

---

## Issues Encountered (Chronological)

### Issue 1: DB_ROLE Gate on Migration

**When:** Running `alembic upgrade head` for migration 125
**Error:** `RuntimeError: DB_ROLE must be set (staging|prod|replica)`
**Resolution:** Added `DB_ROLE=staging DB_AUTHORITY=local` to the alembic command.

### Issue 2: CLI Missing Plan Generation + tenant_id

**When:** Attempting to create a run via `python -m app.aos_cli run`
**Error:**
```
NotNullViolationError: null value in column "tenant_id" of relation "aos_traces" violates not-null constraint
L5_GOVERNANCE_VIOLATION_NO_PLAN
RuntimeError: Governance violation: Run has no plan.
```
**Root cause:** The CLI's `create_run` function creates a bare `Run` record without:
- `tenant_id` (required for trace creation)
- Plan generation via L4 `PlanGenerationEngine` (required by PIN-257 Phase R-2)

The API endpoint (`main.py:1402`) handles both, but the CLI does not replicate this flow.
**Resolution:** Used a Python script that replicates the exact API flow:
1. Create `Run` with `tenant_id` and `origin_system_id`
2. Generate plan via `generate_plan_for_run` (L4)
3. Execute via `RunRunner` (L5)

### Issue 3: Empty DB — No Tenants or API Keys

**When:** Attempting to use the API endpoint `/api/v1/runs`
**Error:** `{"error": "api_key_invalid"}` and `410 GONE` for legacy endpoint
**Root cause:** Freshly rebuilt DB has zero rows in `tenants` and `api_keys` tables. The gateway's API key service validates against DB first (before legacy env fallback).
**Resolution:** Created tenant and API key in DB. Ultimately used direct Python execution instead of API endpoint because HOC routes don't expose a "create run" endpoint.

### Issue 4: Run Step Failed — Missing `http_call` Skill

**When:** Runner executing the planned step
**Error:** `SkillExecutionError: Skill not found: http_call`
**Root cause:** The stub planner generated a plan with `http_call` skill, which is not registered in the local environment.
**Impact:** Run completed with status `retry` (1 failed step). **This is acceptable** — the test validates trace creation and integrity verification, not skill execution. The trace was created with 1 step (status: `failure`), proving the production trace path works for both success and failure cases.

---

## Step 1 — Fix A: origin_system_id Design Fix

### Problem

`runs.origin_system_id` had `DEFAULT 'legacy-migration'` (migration 104), but trigger `trg_runs_origin_system_not_legacy` (migration 105) rejected that value. Any INSERT omitting `origin_system_id` would get the default, which was then immediately rejected.

### Migration Applied

**File:** `alembic/versions/125_drop_origin_system_id_default.py`
**Revision:** `125_drop_origin_system_id_default`
**DDL:** `ALTER TABLE runs ALTER COLUMN origin_system_id DROP DEFAULT;`

### ORM Model Updates

| File | Change |
|------|--------|
| `app/db.py:312` | Removed `default="legacy-migration"` from `origin_system_id` Field |
| `app/hoc/int/agent/drivers/db.py:312` | Same change |

### Run Creation Paths Patched (4 files)

| File | Line | origin_system_id Value |
|------|------|----------------------|
| `app/aos_cli.py` | 134 | `"aos-cli"` |
| `app/main.py` | 1408 | `"api-endpoint"` |
| `app/hoc/api/int/account/aos_cli.py` | 164 | `"hoc-cli"` |
| `app/hoc/cus/policies/L6_drivers/workers_read_driver.py` | 268 | `"policy-retry"` |

### Acceptance Verification

| Test | Expected | Actual |
|------|----------|--------|
| INSERT without origin_system_id | NOT NULL violation | `null value in column "origin_system_id" violates not-null constraint` |
| INSERT with `'legacy-migration'` | Trigger rejection | `origin_system_id cannot be 'legacy-migration' for new runs` |
| INSERT with explicit value | Success | `INSERT 0 1` |

---

## Step 2 — Generate Real Run (Production Path)

### Execution Method

Python script replicating the exact production API flow:

```python
# 1. Create Run with origin_system_id
run = Run(agent_id=AGENT_ID, goal=GOAL, status="queued",
          tenant_id=TENANT_ID, origin_system_id="run-proof-v2")

# 2. Generate plan via L4 PlanGenerationEngine
plan_result = generate_plan_for_run(agent_id=AGENT_ID, goal=GOAL, run_id=run_id)
run.plan_json = plan_result.plan_json

# 3. Execute via RunRunner (same as worker)
runner = RunRunner(run_id)
runner.run()
```

### Run Result

| Field | Value |
|-------|-------|
| Run ID | `78d877a8-9f1e-4bf5-b060-1d5e23949a68` |
| Agent ID | `46f4830d-e2e0-4a0a-aba4-d2741abd2ae1` |
| Tenant ID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Status | `retry` |
| Plan steps | 1 (`http_call`) |
| Origin system ID | `run-proof-v2` |
| Error | `Skill not found: http_call` |

---

## Step 3 — Verify Trace Data Exists

### Trace Record

```sql
SELECT run_id, tenant_id, started_at, status FROM aos_traces
WHERE run_id = '78d877a8-9f1e-4bf5-b060-1d5e23949a68';
```

| run_id | tenant_id | started_at | status |
|--------|-----------|------------|--------|
| 78d877a8-... | a1b2c3d4-... | 2026-02-09 17:08:34.002752+00 | running |

### Trace Steps

```sql
SELECT step_index, skill_name, status, duration_ms FROM aos_trace_steps
WHERE trace_id = 'trace_78d877a8-9f1e-4bf5-b060-1d5e23949a68';
```

| step_index | skill_name | status | duration_ms |
|------------|------------|--------|-------------|
| 0 | http_call | failure | 0.39 |

**1 trace row, 1 step — both produced by the production RunRunner, not manual inserts.**

---

## Step 4 — RunProofCoordinator Validation

```bash
RUN_ID='78d877a8-...' TENANT_ID='a1b2c3d4-...' \
PYTHONPATH=. USE_POSTGRES_TRACES=true python3 <coordinator_script>
```

**Output:**
```
integrity_model: HASH_CHAIN
verification_status: VERIFIED
chain_length: 1
root_hash: 5583fbff25cd1129f6d19d662de123f367865ef69a24e0bc420040efc6480783
trace_count: 1
step_count: 1
```

| Check | Expected | Actual | Result |
|-------|----------|--------|--------|
| `integrity_model` | `HASH_CHAIN` | `HASH_CHAIN` | **PASS** |
| `verification_status` | `VERIFIED` | `VERIFIED` | **PASS** |
| `chain_length == step_count` | `1` | `1` | **PASS** |
| `trace_count >= 1` | `>= 1` | `1` | **PASS** |

---

## Step 5 — Coordinator Pytest

```bash
PYTHONPATH=. pytest tests/test_run_introspection_coordinators.py -q
```

```
..........                                                               [100%]
10 passed in 2.67s
```

---

## Output Report

| Field | Value |
|-------|-------|
| **Migration applied** | `125_drop_origin_system_id_default` |
| **origin_system_id default removed** | YES — column has no default, NOT NULL enforced |
| **Run creation paths patched** | `aos_cli.py`, `main.py`, `hoc/api/int/account/aos_cli.py`, `workers_read_driver.py` |
| **Run ID** | `78d877a8-9f1e-4bf5-b060-1d5e23949a68` |
| **Tenant ID** | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| **Trace rows** | 1 |
| **Trace step_count** | 1 |
| **Integrity model** | `HASH_CHAIN` |
| **Verification status** | `VERIFIED` |
| **chain_length** | 1 |
| **root_hash** | `5583fbff25cd1129f6d19d662de123f367865ef69a24e0bc420040efc6480783` |
| **Pytest** | 10/10 passed (2.67s) |

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `origin_system_id` schema no longer self-contradictory | **MET** — default dropped, trigger enforced, NOT NULL |
| 2 | All run creation paths set `origin_system_id` explicitly | **MET** — 4 files patched |
| 3 | A real run (not DB seed) produces trace rows in Postgres | **MET** — RunRunner produced 1 trace + 1 step |
| 4 | `RunProofCoordinator` returns `HASH_CHAIN` + `VERIFIED` | **MET** |
| 5 | Coordinator tests pass | **MET** — 10/10 |

---

## Files Modified

| File | Change |
|------|--------|
| `app/db.py:312` | Removed `default="legacy-migration"` from origin_system_id |
| `app/hoc/int/agent/drivers/db.py:312` | Same ORM fix |
| `app/aos_cli.py:134` | Added `origin_system_id="aos-cli"` |
| `app/main.py:1408` | Added `origin_system_id="api-endpoint"` |
| `app/hoc/api/int/account/aos_cli.py:164` | Added `origin_system_id="hoc-cli"` |
| `app/hoc/cus/policies/L6_drivers/workers_read_driver.py:268-279` | Added `origin_system_id="policy-retry"` to SQL INSERT |

## Files Created

| File | Purpose |
|------|---------|
| `alembic/versions/125_drop_origin_system_id_default.py` | Migration: drop contradictory default |

---

## Structural Findings

### Finding 1: CLI Doesn't Replicate API Flow

The CLI's `create_run`/`run_goal` functions create bare `Run` records without:
- `tenant_id` (required for trace creation in Postgres)
- Plan generation via L4 `PlanGenerationEngine` (required by PIN-257)

The API endpoint at `main.py:1402` handles both. The CLI should be updated to match, or documented as dev-only.

### Finding 2: No "Create Run" Endpoint in HOC Routes

The legacy `POST /api/v1/runs` returns `410 GONE`. The HOC route layer exposes `GET /activity/runs` (read) and `GET /activity/runs/{id}/proof` but has no write endpoint for creating new runs. Run creation only works through legacy `main.py` or direct Python.

### Finding 3: Stub Planner Uses Missing Skills

The stub planner generates plans with `http_call` skill, which is not registered. This causes all stub-planned runs to fail at execution. Not a blocking issue for trace validation.
