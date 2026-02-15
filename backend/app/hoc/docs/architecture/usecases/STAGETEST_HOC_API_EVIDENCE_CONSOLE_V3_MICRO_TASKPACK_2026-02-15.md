# Stagetest Evidence Console V3 Micro-Taskpack (2026-02-15)

## Objective

Close the remaining reality gaps and guarantee that `stagetest.agenticverz.com` visibly shows:
1. **Inputs** used for each test case
2. **Outputs** produced for each test case
3. **APIs used** (method + route + operation) per case/run

This is a micro-taskpack focused on correctness and live visual proof.

## Mandatory User-Visible Outcome (Live)

On `https://stagetest.agenticverz.com/fops/stagetest`, case detail must display:
1. `API Request Fields` table
2. `Synthetic Input` table
3. `API Response Fields` table
4. `Produced Output` table
5. `APIs Used` table (method, path, operation, status, duration)

No “PASS” claim is valid without live screenshot evidence of all five sections.

## Canonical API Contract (No Legacy Prefix)

Only these endpoints are allowed:
1. `GET /hoc/api/stagetest/runs`
2. `GET /hoc/api/stagetest/runs/{run_id}`
3. `GET /hoc/api/stagetest/runs/{run_id}/cases`
4. `GET /hoc/api/stagetest/runs/{run_id}/cases/{case_id}`
5. `GET /hoc/api/stagetest/apis`

Forbidden:
1. `/api/v1/stagetest/*`

## Workstream V3-1: Full Stage 1.2 Metadata Coverage

### Tasks

1. Remove partial route metadata behavior for stage `1.2` artifact emission.
2. Ensure every emitted stage `1.2` case includes non-empty:
   - `route_path`
   - `api_method`
   - `request_fields`
   - `response_fields`
   - `synthetic_input`
   - `observed_output`
3. Add `api_calls_used` array to each stage `1.2` case artifact with minimum fields:
   - `method`
   - `path`
   - `operation`
   - `status_code`
   - `duration_ms`

### Acceptance

1. `STAGETEST_EMIT=1 pytest -q tests/uat/` passes.
2. `stagetest_artifact_check.py --strict --latest-run` passes on the generated run.
3. No stage `1.2` case has `N/A` or empty route/fields.

## Workstream V3-2: Gate Determinism (Pinned Run)

### Tasks

1. Update `backend/scripts/ops/hoc_uc_validation_uat_gate.sh` to:
   - generate a fresh stagetest emission run within gate
   - capture emitted `run_id`
   - validate that exact run id (`--run-id <id>`) instead of `--latest-run`
2. Fail gate if emission step fails or run id not found.
3. Keep existing route prefix guard and governance checks.

### Acceptance

1. Gate result is deterministic and self-contained.
2. No pass/fail drift caused by older artifact directories.

## Workstream V3-3: Backend Contract for APIs Used

### Tasks

1. Extend case schema/model/API response so case detail includes `api_calls_used`.
2. Ensure read engine returns `api_calls_used` from artifact file.
3. Add runtime API tests for `api_calls_used` presence and shape.

### Acceptance

1. Runtime tests validate that case detail returns non-empty `api_calls_used` for stage `1.2`.

## Workstream V3-4: Frontend Case Detail (Input/Output/APIs)

### Tasks

1. In `StagetestCaseDetail` render explicit sections with tables:
   - `API Request Fields` (input contract)
   - `Synthetic Input` (input payload)
   - `API Response Fields` (output contract)
   - `Produced Output` (actual output payload)
   - `APIs Used` (method/path/operation/status/duration)
2. Add stable test ids:
   - `api-request-fields-table`
   - `synthetic-input-table`
   - `api-response-fields-table`
   - `produced-output-table`
   - `apis-used-table`
3. Keep deterministic hash and signature visible.

### Acceptance

1. Playwright and/or DOM assertions confirm all five tables exist.
2. At least one data row present in each table for fixture-backed case.

## Workstream V3-5: Live Publish Proof (Authenticated)

### Tasks

1. Verify live deployment at `stagetest.agenticverz.com`.
2. Perform authenticated browser run and capture screenshots showing all five table sections.
3. Capture authenticated API responses for:
   - `/hoc/api/stagetest/runs`
   - `/hoc/api/stagetest/runs/{run_id}/cases/{case_id}`
4. If auth credentials are unavailable, mark as `BLOCKED` with exact missing secret/token and stop claiming closure.

### Acceptance

1. Live evidence contains:
   - URL + timestamp
   - screenshot files
   - authenticated API JSON samples
2. All five table sections are visible in the live UI evidence.

## Required Evidence Directory

1. `backend/app/hoc/docs/architecture/usecases/evidence_stagetest_hoc_api_v3_2026_02_15/`

Include at minimum:
1. `v3_gate.log`
2. `v3_emit.log`
3. `v3_artifact_check.log`
4. `v3_runtime_api_tests.log`
5. `v3_ui_tests.log`
6. `v3_live_auth_runs.json`
7. `v3_live_auth_case_detail.json`
8. `v3_live_ui_case_detail.png`
9. `v3_live_ui_apis_used.png`

## Required Output Artifact

1. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_V3_MICRO_TASKPACK_2026-02-15_implemented.md`

Must include:
1. Findings closure matrix (`CLOSED|OPEN|BLOCKED`)
2. File change ledger
3. Pinned-run gate proof (`run_id` shown)
4. Input/Output/APIs-used live UI proof section
5. Authenticated API response proof
6. Residual risks and blockers

## Execution Commands (Minimum)

From `/root/agenticverz2.0/backend`:

```bash
export PYTHONPATH=.
EVIDENCE=app/hoc/docs/architecture/usecases/evidence_stagetest_hoc_api_v3_2026_02_15
mkdir -p "$EVIDENCE"

STAGETEST_EMIT=1 pytest -q tests/uat/ | tee "$EVIDENCE/v3_emit.log"
python3 scripts/verification/stagetest_artifact_check.py --strict --latest-run | tee "$EVIDENCE/v3_artifact_check.log"
pytest -q tests/api/test_stagetest_runtime_api.py | tee "$EVIDENCE/v3_runtime_api_tests.log"
./scripts/ops/hoc_uc_validation_uat_gate.sh | tee "$EVIDENCE/v3_gate.log" || true
```

From `/root/agenticverz2.0/website/app-shell`:

```bash
npm run typecheck:uat
npm run build
npm run test:uat:list
```

## Claude Command

```bash
claude -p "In /root/agenticverz2.0 execute backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_V3_MICRO_TASKPACK_2026-02-15.md end-to-end. Focus on guaranteed live visibility of input tables, output tables, and APIs-used table on stagetest.agenticverz.com. Fix full stage-1.2 artifact metadata coverage, make the gate deterministic with pinned emitted run_id validation, extend runtime API contract/tests for api_calls_used, and produce authenticated live proof (screenshots + API JSON) for the five required table sections. Publish backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_V3_MICRO_TASKPACK_2026-02-15_implemented.md with exact logs, exit codes, and CLOSED/OPEN/BLOCKED statuses."
```
