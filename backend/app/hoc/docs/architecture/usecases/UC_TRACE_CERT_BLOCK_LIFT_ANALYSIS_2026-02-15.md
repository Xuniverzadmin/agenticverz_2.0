# UC Trace-Cert Block Lift Analysis (2026-02-15)

## Scope
Audit target: `UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15_executed.md` and related summaries/evidence.

## Why Blocks Happened

1. Structural checks were treated as certifiable runtime cases.
- Stage 1.1 rows were mostly script/governance verifiers (static/structural) that do not emit `execution_trace` / `db_writes` artifacts.
- Under mandatory trace-cert policy, these rows are correctly downgraded from PASS to BLOCKED.

2. Route resolution quality was too weak in generator output.
- Composite operation names (`opA|opB|...`) were not expanded against route map keys.
- Manifest symbolic route keys (e.g. `logs.traces_api`) were not resolved to concrete HTTP routes.
- Commands were not normalized to `hoc/api/cus` prefixed paths.

3. Stage 1.2 synthetic input file used placeholder stubs.
- Payloads were template text instead of concrete deterministic JSON objects.
- This made Stage 1.2 execution easy to block for "input unresolved" claims.

4. One real failing test existed.
- `tests/test_activity_facade_introspection.py` was written pre PIN-520 pattern (patching factory getters), while current facade expects coordinator injection.
- Result: `3 failed, 3 passed` in prior run.

5. Runtime trace suites exist only for 6 UCs today.
- Trace-capable Stage 1.2 suites currently cover: `UC-002`, `UC-004`, `UC-006`, `UC-008`, `UC-017`, `UC-032`.
- Remaining UCs have governance/script coverage but no emitted runtime trace/db artifacts yet.

## Fixes Implemented Now

1. Fixed the failing activity facade introspection tests.
- File: `backend/tests/test_activity_facade_introspection.py`
- Change: switched to explicit coordinator injection fixtures for PIN-520 compatibility.
- Verification: `PYTHONPATH=. pytest -q tests/test_activity_facade_introspection.py` -> `6 passed`.

2. Hardened testcase generator for executable/certifiable output.
- File: `/root/.codex/skills/uc-testcase-generator/scripts/uc_testcase_pack.py`
- Changes:
  - Route normalization to `hoc/api/cus` prefix.
  - Composite operation token expansion (`|`) for route lookup.
  - Symbolic `route_path` resolution via route-map op keys.
  - Correct test command typing:
    - `tests/*.py` -> `pytest`
    - `scripts/*.py` -> `python3`
  - Stage 1.2 trace-capable command mapping for UCs with runtime suites.
  - Concrete deterministic synthetic input payloads (no placeholder-only `input`).

3. Regenerated improved all-UC pack.
- Files:
  - `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15.md`
  - `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_executed.md`
  - `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_synthetic_inputs.json`
- Coverage deltas vs V2 pack:
  - Stage 1.1 with route evidence: `7 -> 11`
  - Stage 1.1 `NO_ROUTE_EVIDENCE`: `44 -> 40`
  - Stage 1.2 trace-capable commands: `0 -> 14`
  - Stage 1.2 unresolved-route commands: `44 -> 31`

4. Re-verified runtime trace/db artifact path still works.
- `STAGETEST_EMIT=1 PYTHONPATH=. pytest -q tests/uat/` -> `23 passed`
- `python3 scripts/verification/stagetest_artifact_check.py --strict --run-id <latest>` -> `PASS: 33 checks passed`
- Latest run confirms non-empty DB writes for synthetic write path cases:
  - `TestUC002OnboardingFlow__test_synthetic_write_path_insert_emits_db_write` -> trace `11`, db_writes `1`
  - `TestUC002OnboardingFlow__test_synthetic_write_path_update_emits_db_write` -> trace `12`, db_writes `2`

## What Blocks Can Be Lifted Now

1. Immediate lift candidates (after rerun using V3 pack):
- `UC-002`, `UC-004`, `UC-006`, `UC-008`, `UC-017`, `UC-032`
- Reason: trace-capable Stage 1.2 suites now explicitly generated, and artifact emission path is green.

2. Still valid HOLD blocks:
- UCs without runtime Stage 1.2 suites and without concrete route-op execution path remain HOLD under trace-cert policy.
- Stage 2 remains blocked without real env/auth credentials (`BASE_URL`, `AUTH_TOKEN`, `TENANT_ID`, optional LLM/API creds).

## Correct Block-Lift Rule (Operational)

1. A case can be moved from BLOCKED to PASS only if both artifact paths are present:
- `Trace Artifact`
- `DB Writes Artifact` (can represent empty write list, but path must exist)

2. Governance/static script pass is necessary but not sufficient for frontend publish certification.

3. Frontend publish readiness is lifted per UC only after trace-certifiable Stage 1.1/1.2 evidence is present and blocker rows are cleared for that UC.
