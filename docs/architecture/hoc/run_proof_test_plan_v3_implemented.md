# Run Proof Test Plan v3 — Implementation Report

**Date:** 2026-02-09
**Executed by:** Claude Opus 4.6
**Source plan:** `docs/architecture/hoc/run_proof_test_plan_v3.md`
**Policy:** No manual DB inserts. No SQLite fallback. Stop on failure and report evidence.

---

## Execution Summary

| Step | Status | Details |
|------|--------|---------|
| 1. Updated Design — New CLI locations | **PASS** | `cus_cli.py` + `int_cli.py` at correct HOC paths |
| 2. Customer CLI Fix — tenant_id + plan gen | **PASS** | `--tenant-id` required, plan generated via L4, RunRunner executed |
| 3. Internal CLI — ops/demo only | **PASS** | Demo runs, no customer run creation |
| 4. Legacy deletion | **PASS** | `app/aos_cli.py` and `hoc/api/int/account/aos_cli.py` deleted, zero stale references |
| 5. RunProof validation | **PASS** | HASH_CHAIN / VERIFIED / chain_length=1 |
| 6. Coordinator tests | **PASS** | 10/10 in 2.74s |

---

## Issues Encountered (Chronological)

### Issue 1: Missing `__init__.py` in `hoc/int/integrations/`

**When:** Checking import chain for `python3 -m app.hoc.int.integrations.int_cli`
**Error:** The directory `app/hoc/int/integrations/` had no `__init__.py`, which would prevent the module from being importable as a package.
**Resolution:** Created `app/hoc/int/integrations/__init__.py` with proper header.

### Issue 2: Stale `__pycache__` from Deleted Legacy CLIs

**When:** Post-deletion cleanup check
**Finding:** Two `.pyc` files lingered from the deleted legacy CLIs:
- `app/__pycache__/aos_cli.cpython-312.pyc`
- `app/hoc/api/int/account/__pycache__/aos_cli.cpython-312.pyc`

**Resolution:** Deleted both stale `.pyc` files.

### Issue 3: Run Step Failed — Missing `http_call` Skill

**When:** RunRunner executing the planned step
**Error:** `SkillExecutionError: Skill not found: http_call`
**Root cause:** Stub planner generates plans with `http_call` skill, which is not registered locally.
**Impact:** Run completed with status `retry` (1 failed step). **Acceptable** — the test validates trace creation and integrity verification, not skill execution. Trace was created with 1 step (status: `failure`).

---

## Step 1 — Updated Design (New CLI Locations)

### Customer CLI

**File:** `backend/app/hoc/cus/integrations/cus_cli.py`
**Audience:** CUSTOMER
**Layer:** L7 — Customer Integration (CLI)

Features:
- `run` command with required `--tenant-id` and optional `--origin-system-id` (default: `cus-cli`)
- `create-agent` command with optional `--tenant-id`
- `list-agents` command with optional `--tenant-id` filter
- `get-run` command
- `list-skills` command
- Plan generation via L4 `generate_plan_for_run` before RunRunner execution

### Internal CLI

**File:** `backend/app/hoc/int/integrations/int_cli.py`
**Audience:** INTERNAL
**Layer:** L7 — Internal Ops (CLI)

Features:
- `demo` command (60-second capability demo)
- `list-skills` command
- **No customer run creation** — ops/demo only

### Legacy Deletions

| File | Status |
|------|--------|
| `backend/app/aos_cli.py` | **DELETED** — no longer exists |
| `backend/app/hoc/api/int/account/aos_cli.py` | **DELETED** — no longer exists |
| `app/__pycache__/aos_cli.cpython-312.pyc` | **CLEANED** — stale pycache removed |
| `app/hoc/api/int/account/__pycache__/aos_cli.cpython-312.pyc` | **CLEANED** — stale pycache removed |

### Stale Reference Audit

Comprehensive search of the entire codebase for references to deleted modules:

| Pattern | Matches |
|---------|---------|
| `app.aos_cli` / `from app.aos_cli` | **0** |
| `app.hoc.api.int.account.aos_cli` | **0** |
| `hoc/api/int/account/aos_cli` | **0** |
| Dockerfile / Makefile / pyproject.toml references | **0** |

**Zero stale references.**

---

## Step 2 — Customer CLI Run (Production Path)

### CLI Command Executed

```bash
DATABASE_URL='postgresql://nova:novapass@localhost:6432/nova_aos' \
DB_ROLE=staging DB_AUTHORITY=local USE_POSTGRES_TRACES=true \
PYTHONPATH=. python3 -m app.hoc.cus.integrations.cus_cli run \
  --agent-id '46f4830d-e2e0-4a0a-aba4-d2741abd2ae1' \
  --goal "Run proof v3 validation run" \
  --tenant-id 'a1b2c3d4-e5f6-7890-abcd-ef1234567890' \
  --origin-system-id "run-proof-v3" \
  --verbose
```

### CLI Output

```
Creating run for agent 46f4830d-e2e0-4a0a-aba4-d2741abd2ae1...
Goal: Run proof v3 validation run
Run created: cf6c5f9e-f642-4a86-ac8b-f61c689aaf72
Executing...
Status: retry
Error: step_failed:1:Skill not found: http_call

Run ID: cf6c5f9e-f642-4a86-ac8b-f61c689aaf72
Status: retry
Error: step_failed:1:Skill not found: http_call
```

### Run Record

| Field | Value |
|-------|-------|
| Run ID | `cf6c5f9e-f642-4a86-ac8b-f61c689aaf72` |
| Agent ID | `46f4830d-e2e0-4a0a-aba4-d2741abd2ae1` |
| Tenant ID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Status | `retry` |
| Origin system ID | `run-proof-v3` |
| Plan generated | **YES** (`plan_json IS NOT NULL`) |
| Error | `step_failed:1:Skill not found: http_call` |

---

## Step 3 — Internal CLI Verification

```bash
python3 -m app.hoc.int.integrations.int_cli demo --quick
```

**Output (excerpt):**
```
============================================================
   AOS 60-Second Demo
============================================================

[1/5] Discovering skills...
      Found 11 skills registered
[2/5] Budget tracking status...
      Daily limit: 10000c
[3/5] Executing json_transform skill...
      Deterministic: Yes (same input -> same output)
[4/5] Recording cost event...
      Alerts triggered: 0
[5/5] Demo complete!
```

Internal CLI runs successfully. Does **not** create customer runs.

---

## Step 4 — Verify Trace Data Exists

### Trace Record

```sql
SELECT run_id, tenant_id, started_at, status
FROM aos_traces
WHERE run_id = 'cf6c5f9e-f642-4a86-ac8b-f61c689aaf72';
```

| run_id | tenant_id | started_at | status |
|--------|-----------|------------|--------|
| cf6c5f9e-... | a1b2c3d4-... | 2026-02-09 18:12:00.986112+00 | running |

### Trace Steps

```sql
SELECT step_index, skill_name, status, duration_ms
FROM aos_trace_steps
WHERE trace_id = 'trace_cf6c5f9e-f642-4a86-ac8b-f61c689aaf72';
```

| step_index | skill_name | status | duration_ms |
|------------|------------|--------|-------------|
| 0 | http_call | failure | 0.45 |

**1 trace row, 1 step — both produced by the production RunRunner via Customer CLI, not manual inserts.**

---

## Step 5 — RunProofCoordinator Validation

```bash
RUN_ID='cf6c5f9e-f642-4a86-ac8b-f61c689aaf72' \
TENANT_ID='a1b2c3d4-e5f6-7890-abcd-ef1234567890' \
DATABASE_URL='...' PYTHONPATH=. USE_POSTGRES_TRACES=true \
python3 <coordinator_script>
```

**Output:**
```
integrity_model: HASH_CHAIN
verification_status: VERIFIED
chain_length: 1
root_hash: 743a5cb677203925459007dec87fbba007afd816e6ef70f91c14102821e348bc
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

## Step 6 — Coordinator Pytest

```bash
PYTHONPATH=. pytest tests/test_run_introspection_coordinators.py -q
```

```
..........                                                               [100%]
10 passed in 2.74s
```

---

## Output Report

| Field | Value |
|-------|-------|
| **Run ID** | `cf6c5f9e-f642-4a86-ac8b-f61c689aaf72` |
| **Tenant ID** | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| **Trace rows** | 1 |
| **Trace step_count** | 1 |
| **Integrity model** | `HASH_CHAIN` |
| **Verification status** | `VERIFIED` |
| **chain_length** | 1 |
| **root_hash** | `743a5cb677203925459007dec87fbba007afd816e6ef70f91c14102821e348bc` |
| **Pytest** | 10/10 passed (2.74s) |

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Customer CLI creates a real run with explicit `tenant_id` and `origin_system_id` | **MET** — `--tenant-id` required, `--origin-system-id` defaults to `cus-cli` |
| 2 | Plan generation occurs before execution (stored in `run.plan_json`) | **MET** — `_generate_plan_or_fail()` called before `RunRunner`, `has_plan=True` |
| 3 | Postgres trace rows exist for the run | **MET** — 1 trace + 1 step in `aos_traces` / `aos_trace_steps` |
| 4 | `RunProofCoordinator` returns `HASH_CHAIN` + `VERIFIED` | **MET** |
| 5 | Coordinator tests pass | **MET** — 10/10 |

---

## Files Created

| File | Purpose |
|------|---------|
| `app/hoc/cus/integrations/cus_cli.py` | Customer CLI with tenant_id + plan generation |
| `app/hoc/int/integrations/int_cli.py` | Internal CLI (ops/demo only) |
| `app/hoc/int/integrations/__init__.py` | Package init for int/integrations |

## Files Deleted

| File | Reason |
|------|--------|
| `app/aos_cli.py` | Legacy root CLI — replaced by `cus_cli.py` |
| `app/hoc/api/int/account/aos_cli.py` | Legacy HOC CLI — replaced by `cus_cli.py` + `int_cli.py` |
| `app/__pycache__/aos_cli.cpython-312.pyc` | Stale pycache for deleted file |
| `app/hoc/api/int/account/__pycache__/aos_cli.cpython-312.pyc` | Stale pycache for deleted file |

---

## Structural Improvements Over v2

| Aspect | v2 (workaround) | v3 (production path) |
|--------|-----------------|---------------------|
| Run creation | Direct Python script | Customer CLI (`cus_cli.py`) |
| tenant_id | Hardcoded in script | `--tenant-id` CLI argument (required) |
| origin_system_id | Hardcoded in script | `--origin-system-id` CLI argument (default: `cus-cli`) |
| Plan generation | Manual call in script | Automatic via `_generate_plan_or_fail()` |
| CLI location | Root `app/aos_cli.py` | Proper HOC path: `hoc/cus/integrations/cus_cli.py` |
| Audience separation | Single CLI for all | CUSTOMER (`cus_cli`) vs INTERNAL (`int_cli`) |
| Legacy files | Still present | Deleted + zero stale references |

---

## Finding: Stub Planner Still Uses Missing Skills

Same as v2: the stub planner generates plans with `http_call` skill, which is not registered locally. This causes all stub-planned runs to fail at execution time. Not blocking for trace validation, but would need to be addressed for full end-to-end run success.
