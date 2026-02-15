# Stagetest HOC API Evidence Console Plan v2 (2026-02-15)

## Objective

Close the reality-audit gaps from v1 and deliver a production-visible stagetest evidence console at `stagetest.agenticverz.com` with:
1. canonical HOC API routes under `/hoc/api/stagetest/*`
2. working artifact emission + API read linkage
3. UI field/table rendering for API fields, synthetic inputs, and produced outputs
4. deterministic proof artifacts and executable audit evidence

## Gap Closure Targets (from audit)

1. Fix emitter/import runtime failure in `tests/uat/conftest.py`.
2. Align artifact path between emitter and read engine.
3. Integrate stagetest guard + artifact validator into unified gate.
4. Replace structural-only API tests with runtime endpoint tests.
5. Strengthen artifact contract enforcement (not pass with empty required payloads).
6. Correct implementation-report claims to match actual gate/browser outcomes.
7. Publish and verify field/table rendering on `stagetest.agenticverz.com`.

## Canonical API Contract (unchanged)

1. `GET /hoc/api/stagetest/runs`
2. `GET /hoc/api/stagetest/runs/{run_id}`
3. `GET /hoc/api/stagetest/runs/{run_id}/cases`
4. `GET /hoc/api/stagetest/runs/{run_id}/cases/{case_id}`
5. `GET /hoc/api/stagetest/apis`

## Workstreams

### W0: Repro Baseline (must fail before fix)

1. Reproduce `STAGETEST_EMIT=1` pytest failure and capture log.
2. Reproduce path mismatch between emitter and read engine roots.
3. Capture gate script stages showing missing stagetest checks.

Acceptance:
1. Three baseline logs prove each defect before patching.

### W1: Artifact Plumbing Fixes

1. Fix import path in `tests/uat/conftest.py` to package-safe import.
2. Align emitter/read engine artifact root to the same canonical directory:
   - `backend/artifacts/stagetest/`
3. Add guardrails so emitter finalization is idempotent (avoid double finalize side effects).

Acceptance:
1. `STAGETEST_EMIT=1 PYTHONPATH=. pytest -q tests/uat/test_uc002_onboarding_flow.py` exits `0`.
2. Emitted run is visible through read engine functions.

### W2: Contract + Validator Hardening

1. Update validator to enforce non-empty payload requirements for Stage 1.2:
   - `request_fields`, `response_fields`, `synthetic_input`, `observed_output`, `assertions`
2. Disallow placeholder route metadata for emitted Stage 1.2 cases:
   - `route_path != "N/A"`
   - `api_method != "N/A"`
3. Enforce signature policy by mode:
   - local/dev: allow `UNSIGNED_LOCAL` with warning
   - release/strict-release: fail unless signed

Acceptance:
1. Invalid sample artifacts fail validator with explicit errors.
2. Valid emitted artifacts pass strict mode in configured local policy.

### W3: Gate Integration

1. Add blocking stages in `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`:
   - `stagetest_route_prefix_guard.py`
   - `stagetest_artifact_check.py --strict --latest-run`
2. Keep existing UAT and frontend stages; preserve non-blocking global TS debt stage.
3. Emit explicit summary line for stagetest stages.

Acceptance:
1. Gate fails if forbidden route appears.
2. Gate fails if latest stagetest artifacts are missing/invalid (post-emission mode).

### W4: Runtime API Tests (replace structural-only confidence)

1. Add runtime endpoint tests with FastAPI TestClient and fixture artifact runs:
   - success: list runs, run detail, case list, case detail, apis snapshot
   - failures: unknown run/case returns 404
   - auth policy behavior validated in test environment contract
2. Keep structural tests only as supplemental.

Acceptance:
1. Runtime API test suite passes and proves real payload flow.

### W5: UI Field/Table Rendering (what is missing now)

1. Ensure case detail renders visible field tables (not only raw JSON blocks):
   - API request fields table
   - API response fields table
   - synthetic input table
   - produced output table
2. Keep raw JSON toggles for audit traceability.
3. Add stable test ids for each table block and rows.
4. Extend Playwright checks for table headers/cell visibility.

Acceptance:
1. Browser tests assert table visibility and non-empty rows for fixture-backed case.
2. UAT page shows API fields + synthetic input + produced output in table form.

### W6: Publish to `stagetest.agenticverz.com`

1. Configure host routing so subdomain lands directly on stagetest UI entry.
2. Ensure app uses correct backend origin for `/hoc/api/stagetest/*`.
3. Apply founder-auth-only access controls on subdomain and API.
4. Deploy and run smoke checks:
   - URL reachable
   - login/auth enforced
   - runs list visible
   - case detail table sections visible
5. Capture screenshots and curl outputs as evidence.

Acceptance:
1. Live URL renders stagetest field/table sections.
2. Claims are backed by published evidence files/logs.

### W7: Corrected v2 Report and Signoff

1. Publish corrected implementation artifact with no inflated claims:
   - `STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_v2_implemented.md`
2. Include explicit PASS/FAIL/BLOCKED matrix with command exit codes.
3. Include subdomain publication proof section.

Acceptance:
1. Report content is fully reproducible from logs and runtime checks.

## Deliverables

1. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_v2.md`
2. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_v2_implemented.md`
3. `backend/app/hoc/docs/architecture/usecases/evidence_stagetest_hoc_api_v2_2026_02_15/` (logs + screenshots + curl outputs)

## Definition of Done

1. Artifact emission works with `STAGETEST_EMIT=1` and creates consumable runs.
2. API reads emitted artifacts successfully through `/hoc/api/stagetest/*`.
3. Unified gate includes and enforces stagetest route/artifact checks.
4. UI displays required field/input/output tables in browser.
5. `stagetest.agenticverz.com` is live and verified with evidence.
