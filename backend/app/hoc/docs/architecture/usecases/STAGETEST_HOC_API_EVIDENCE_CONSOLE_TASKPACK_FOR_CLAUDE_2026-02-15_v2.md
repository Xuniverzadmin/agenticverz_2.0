# Stagetest HOC API Evidence Console Taskpack For Claude v2 (2026-02-15)

## Objective

Execute a corrective pass that closes v1 audit gaps and proves live visual validation on `stagetest.agenticverz.com`.

Primary plan:
1. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_PLAN_2026-02-15_v2.md`

## Required Context Load

1. `codex_agents_agenticverz2.md`
2. `project_aware_agenticverz2.md`
3. `vision_mission_self_audit.md`
4. `architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md`
5. `docs/architecture/architecture_core/LAYER_MODEL.md`
6. `docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md`
7. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_implemented.md`

## Non-Negotiables

1. Never use `/api/v1/stagetest/*`.
2. Keep canonical stagetest API under `/hoc/api/stagetest/*`.
3. Do not claim success unless commands and logs prove it.
4. Mark blocked infrastructure items as `BLOCKED`, not `PASS`.

## Evidence Directory

Use:
1. `backend/app/hoc/docs/architecture/usecases/evidence_stagetest_hoc_api_v2_2026_02_15/`

## Workstream Execution

### W0: Baseline Repro (capture pre-fix failures)

From `/root/agenticverz2.0/backend`:

```bash
export PYTHONPATH=.
mkdir -p app/hoc/docs/architecture/usecases/evidence_stagetest_hoc_api_v2_2026_02_15
EVIDENCE=app/hoc/docs/architecture/usecases/evidence_stagetest_hoc_api_v2_2026_02_15

STAGETEST_EMIT=1 pytest -q tests/uat/test_uc002_onboarding_flow.py > "$EVIDENCE/w0_emit_failure.log" 2>&1 || true
python3 - <<'PY' > "$EVIDENCE/w0_path_mismatch.log" 2>&1
from app.hoc.fdr.ops.engines.stagetest_read_engine import ARTIFACTS_ROOT as read_root
from tests.uat.stagetest_artifacts import ARTIFACTS_ROOT as emit_root
print("read_root=", read_root)
print("emit_root=", emit_root)
print("same=", read_root == emit_root)
PY
rg -n "stagetest_route_prefix_guard|stagetest_artifact_check" scripts/ops/hoc_uc_validation_uat_gate.sh > "$EVIDENCE/w0_gate_missing_stages.log" || true
```

Acceptance:
1. Baseline logs show reproducible defects before fixes.

### W1: Artifact Plumbing Fixes

Tasks:
1. Fix emitter import path in `backend/tests/uat/conftest.py`.
2. Align artifact root used by:
   - `backend/tests/uat/stagetest_artifacts.py`
   - `backend/app/hoc/fdr/ops/engines/stagetest_read_engine.py`
3. Ensure session finalization does not duplicate or corrupt run summaries.

Verify:

```bash
STAGETEST_EMIT=1 pytest -q tests/uat/test_uc002_onboarding_flow.py | tee "$EVIDENCE/w1_emit_smoke.log"
python3 - <<'PY' | tee "$EVIDENCE/w1_engine_reads_emitted.log"
from app.hoc.fdr.ops.engines.stagetest_read_engine import list_runs
runs = list_runs()
print("runs_found=", len(runs))
print("top_run=", runs[0]["run_id"] if runs else "NONE")
PY
```

Acceptance:
1. Emit smoke test exits `0`.
2. Read engine reports at least one run.

### W2: Contract and Validator Hardening

Tasks:
1. Strengthen `backend/scripts/verification/stagetest_artifact_check.py` checks for stage `1.2`:
   - require non-empty `request_fields`, `response_fields`, `synthetic_input`, `observed_output`, `assertions`
   - reject `route_path == "N/A"` or `api_method == "N/A"`
2. Add signature mode policy flag (e.g. `--release-signature-required`).

Verify:

```bash
python3 scripts/verification/stagetest_artifact_check.py --strict --latest-run | tee "$EVIDENCE/w2_artifact_check_strict.log"
```

Acceptance:
1. Strict check passes on emitted run.
2. Validation errors are explicit when contract is violated.

### W3: Gate Integration

Tasks:
1. Update `backend/scripts/ops/hoc_uc_validation_uat_gate.sh` to include:
   - `python3 scripts/verification/stagetest_route_prefix_guard.py`
   - `python3 scripts/verification/stagetest_artifact_check.py --strict --latest-run`
2. Keep clear blocking semantics in summary.

Verify:

```bash
bash scripts/ops/hoc_uc_validation_uat_gate.sh | tee "$EVIDENCE/w3_gate_full.log" || true
```

Acceptance:
1. New stagetest stages appear in gate output.
2. Failures are accurately labeled by cause.

### W4: Runtime API Tests

Tasks:
1. Add runtime endpoint tests using FastAPI TestClient and seeded artifact fixture data.
2. Cover all 5 endpoints with success + 404 cases.

Verify:

```bash
pytest -q tests/api/test_stagetest_read_api.py | tee "$EVIDENCE/w4_api_tests.log"
```

Acceptance:
1. Runtime tests pass and prove endpoint behavior.

### W5: UI Field/Table Visibility

Tasks:
1. Update stagetest UI to render explicit tables (not only raw JSON):
   - request fields table
   - response fields table
   - synthetic input table
   - produced output table
2. Add/adjust `data-testid`:
   - `api-request-fields-table`
   - `api-response-fields-table`
   - `synthetic-input-table`
   - `observed-output-table`
3. Extend Playwright with assertions for these table headers/rows.

Verify:

```bash
cd /root/agenticverz2.0/website/app-shell
npm run typecheck:uat | tee "/root/agenticverz2.0/backend/$EVIDENCE/w5_typecheck.log"
npm run build | tee "/root/agenticverz2.0/backend/$EVIDENCE/w5_build.log"
npm run test:uat:list | tee "/root/agenticverz2.0/backend/$EVIDENCE/w5_uat_list.log"
npx playwright test --config tests/uat/playwright.config.ts tests/uat/stagetest.spec.ts | tee "/root/agenticverz2.0/backend/$EVIDENCE/w5_playwright.log" || true
```

Acceptance:
1. Table testids are asserted in Playwright specs.
2. If browser missing, mark as `BLOCKED` and include install instruction.

### W6: Publish to `stagetest.agenticverz.com` (requested)

Tasks:
1. Deploy app-shell build for stagetest subdomain entry.
2. Ensure runtime API target reaches backend `/hoc/api/stagetest/*`.
3. Enforce founder auth.
4. Capture live verification evidence:
   - curl endpoint checks
   - browser screenshots showing all four table sections
   - URL + timestamp proof

Verify (adapt commands to your deployment stack):

```bash
curl -I https://stagetest.agenticverz.com | tee "/root/agenticverz2.0/backend/$EVIDENCE/w6_live_head.log"
curl -sS https://stagetest.agenticverz.com/hoc/api/stagetest/runs | tee "/root/agenticverz2.0/backend/$EVIDENCE/w6_live_runs.json" || true
```

Acceptance:
1. `stagetest.agenticverz.com` is reachable.
2. UI visibly shows field/input/output tables.
3. Live checks are evidence-backed.

### W7: Corrected v2 Implementation Artifact

Publish:
1. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_v2_implemented.md`

Must include:
1. Findings closure matrix for all audit gaps (`OPEN|CLOSED|BLOCKED`).
2. File change ledger.
3. Runtime API proof (not only structural tests).
4. Gate output with exact exit codes.
5. Subdomain publication proof and table visibility proof.
6. Explicit residual risks.

## Required Deliverables

1. Updated code and tests for W1–W5.
2. Publication evidence for W6.
3. `*_v2_implemented.md` report.
4. Evidence directory logs and screenshots.

## Claude Execute Command

```bash
claude -p "In /root/agenticverz2.0 execute backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_v2.md end-to-end. First reproduce and log the known gaps, then fix them (artifact path mismatch, emitter import failure, missing gate integration, runtime API test coverage, and UI field/table rendering). Also execute publish work for stagetest.agenticverz.com and provide live evidence that API fields, synthetic input, and produced output tables are visible in browser. Publish backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_v2_implemented.md with exact command outputs, exit codes, and gap closure status per finding."
```
