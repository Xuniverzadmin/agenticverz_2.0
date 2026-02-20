# CI Baseline Remediation: SQL Misuse + Priority-5 Intent + Skill Tests + Migration Role Gate

**Date:** 2026-02-20  
**Scope:** Lane A CI baseline stabilization  
**Workflow(s):** `ci.yml`

## Problems

Fresh CI failures on PR run `22223767346` were traced to four concrete issues:

1. `sql-misuse-guard`
- Detected `session.exec(text(...))` usage in `backend/app/hoc/cus/integrations/cus_cli.py`.

2. `priority5-intent-guard`
- Guard script used stale pre-refactor file paths and reported `FILE_MISSING` regressions.

3. `unit-tests` (`tests/skills`)
- Skill test modules had broken import scaffolding (undefined `_skills_path`, stale import paths, and malformed path-insert blocks).

4. `run-migrations`
- Alembic DB role gate blocked CI because `DB_ROLE` was not set in workflow environment.

## Remediation

### A. SQL misuse guard compliance

- Updated raw-SQL calls in `backend/app/hoc/cus/integrations/cus_cli.py`:
  - `session.exec(text(...))` -> `session.execute(text(...))`

### B. Priority-5 intent guard path realignment

- Updated `backend/scripts/ci/check_priority5_intent.py` Priority-5 file map to current paths:
  - `worker/*` -> `hoc/int/worker/*`
  - `services/recovery_write_service.py` -> `hoc/cus/policies/L6_drivers/recovery_write_driver.py`
- Kept expected `FEATURE_INTENT` and `RETRY_POLICY` values unchanged.

### C. Skill tests and skill-runtime module import hygiene repair

- Updated tests to canonical package imports:
  - `backend/tests/skills/test_registry_v2.py`
  - `backend/tests/skills/test_registry_load.py`
  - `backend/tests/skills/test_stubs.py`
  - `backend/tests/skills/test_stub_replay.py`
- Repaired path/import scaffolding in skill modules used by those tests:
  - `backend/app/hoc/int/agent/drivers/registry_v2.py`
  - `backend/app/skills/registry_v2.py`
  - `backend/app/hoc/int/agent/drivers/json_transform_stub.py`
  - `backend/app/hoc/int/agent/engines/http_call_stub.py`
  - `backend/app/hoc/int/agent/engines/llm_invoke_stub.py`
- Replaced fragile `sys.path` hacks with canonical imports from `app.hoc.int.worker.runtime.core`.

### D. Migration role gate compliance in CI

- Added workflow env declaration in `.github/workflows/ci.yml`:
  - `DB_ROLE: staging`
- This satisfies Alembic role-gate requirements in CI migration steps.

## Validation

Executed locally:

1. `python3 scripts/ci/check_priority5_intent.py --verbose`
- Result: `PASSED: All 12 Priority-5 files have correct declarations`

2. SQL misuse guard probe (same pattern as CI step)
- Result: `sql_misuse_guard_violations=0`

3. `PYTHONPATH=. pytest tests/skills -v --maxfail=3`
- Result: `283 passed`

4. `python3 -m py_compile` across changed Python modules/tests
- Result: pass

5. `.github/workflows/ci.yml` parse check via PyYAML
- Result: pass

## Result

The CI failures for `sql-misuse-guard`, `priority5-intent-guard`, `unit-tests` (skill tests), and `run-migrations` are remediated in code and validated locally with deterministic commands.
