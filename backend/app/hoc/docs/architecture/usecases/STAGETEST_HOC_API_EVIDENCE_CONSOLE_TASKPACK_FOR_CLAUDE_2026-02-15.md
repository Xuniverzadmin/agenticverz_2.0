# Stagetest HOC API Evidence Console Taskpack For Claude (2026-02-15)

## Objective

Build an audit-ready, read-only evidence console where visual test claims are backed by machine artifacts and served through canonical HOC routes.

This taskpack supersedes any prior `stagetest` route ideas that used `/api/v1/*`.

Canonical stagetest read API prefix is now:
1. `/hoc/api/stagetest/*`

## Source Plan

Primary source:
1. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_PLAN_2026-02-15.md`

## Required Context Load (Do First)

1. `codex_agents_agenticverz2.md`
2. `project_aware_agenticverz2.md`
3. `vision_mission_self_audit.md`
4. `architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md`
5. `docs/architecture/architecture_core/LAYER_MODEL.md`
6. `docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md`
7. `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
8. `backend/app/hoc/docs/architecture/usecases/UC_OPERATION_MANIFEST_2026-02-15.json`
9. `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_ROUTE_OPERATION_MAP.md`
10. `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`

## Non-Negotiable Constraints

1. Do not use `/api/v1/stagetest/*` anywhere.
2. All new stagetest APIs must be read-only and founder-auth protected.
3. Test execution remains in backend/CI/Claude. UI is evidence display only.
4. Every UI claim must map to artifact path + determinism hash.
5. Preserve architecture boundaries: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7`.
6. No DB/ORM logic in L2/L4 handlers for artifact reads if filesystem artifact model is used.
7. Do not break existing UAT and governance gates.

## Target API Contract (Canonical)

1. `GET /hoc/api/stagetest/runs`
2. `GET /hoc/api/stagetest/runs/{run_id}`
3. `GET /hoc/api/stagetest/runs/{run_id}/cases`
4. `GET /hoc/api/stagetest/runs/{run_id}/cases/{case_id}`
5. `GET /hoc/api/stagetest/apis`

## Evidence Artifact Contract (Required)

Root directory:
1. `backend/artifacts/stagetest/<run_id>/`

Required files:
1. `run_summary.json`
2. `apis_snapshot.json`
3. `cases/<case_id>.json` for each case

Minimum `run_summary.json` fields:
1. `run_id`
2. `created_at`
3. `stages_executed` (example: `["1.1","1.2"]`)
4. `total_cases`
5. `pass_count`
6. `fail_count`
7. `determinism_digest`
8. `artifact_version`

Minimum `cases/<case_id>.json` fields:
1. `run_id`
2. `case_id`
3. `uc_id`
4. `stage` (`1.1|1.2|2`)
5. `operation_name`
6. `route_path`
7. `api_method`
8. `request_fields`
9. `response_fields`
10. `synthetic_input`
11. `observed_output`
12. `assertions` (array with id/status/message)
13. `status` (`PASS|FAIL|SKIPPED`)
14. `determinism_hash` (sha256 of canonical payload)
15. `signature` (HMAC signature; if key unavailable in local, record `UNSIGNED_LOCAL` and fail release gate)
16. `evidence_files` (log references)

## Workstream 0: Baseline and Route Migration Guard

### Tasks

1. Audit current repo for stagetest route references and classify:
   - canonical (`/hoc/api/stagetest/*`)
   - forbidden (`/api/v1/stagetest/*`)
2. Add a regression check script:
   - `backend/scripts/verification/stagetest_route_prefix_guard.py`
3. Add a test:
   - `backend/tests/governance/t4/test_stagetest_route_prefix_guard.py`

### Acceptance

1. Forbidden prefix count is `0`.
2. New guard fails if `/api/v1/stagetest/*` appears in code/docs/tests.

## Workstream 1: Artifact Schema + Emitter

### Tasks

1. Create artifact JSON schema:
   - `backend/app/hoc/docs/architecture/usecases/stagetest_artifact_schema.json`
2. Implement reusable emitter helpers:
   - `backend/tests/uat/stagetest_artifacts.py`
3. Add canonical JSON hashing utility reuse from existing deterministic helpers where possible.
4. Add emission hooks into Stage 1.1/1.2 tests so case files include full request/response/synthetic/output payloads.
5. Emit `apis_snapshot.json` from route-operation manifest and stagetest endpoint map.

### Acceptance

1. Stage 1.1 + 1.2 execution produces complete artifact directory for a run.
2. Every case file validates against `stagetest_artifact_schema.json`.

## Workstream 2: Artifact Integrity and Determinism Gates

### Tasks

1. Add artifact validator:
   - `backend/scripts/verification/stagetest_artifact_check.py`
2. Checks must enforce:
   - required files present
   - schema-valid JSON
   - non-empty request/response fields
   - non-empty synthetic input and observed output for stage `1.2`
   - determinism hash correctness
   - signature presence policy
3. Integrate into:
   - `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`
4. Add determinism re-run check script that compares hashes across two synthetic reruns.

### Acceptance

1. Gate exits non-zero when artifacts are incomplete or hash/signature checks fail.
2. Gate summary clearly reports artifact pass/fail stage.

## Workstream 3: HOC Read-Only API Implementation

### Tasks

1. Add HOC founder ops router:
   - `backend/app/hoc/api/fdr/ops/stagetest.py`
2. Register router in facade:
   - `backend/app/hoc/api/facades/fdr/ops.py`
3. Add read engine:
   - `backend/app/hoc/fdr/ops/engines/stagetest_read_engine.py`
4. Add response/request schemas:
   - `backend/app/hoc/fdr/ops/schemas/stagetest.py`
5. Enforce founder auth dependency in router (`verify_fops_token`).
6. Ensure routes are strictly GET-only and return normalized DTOs.
7. Add API tests:
   - `backend/tests/api/test_stagetest_read_api.py`

### Acceptance

1. All 5 canonical endpoints return expected payload shapes.
2. Non-founder or missing auth gets expected rejection response.
3. No write endpoints exist for stagetest.

## Workstream 4: App-Shell Visual Evidence Console

### Tasks

1. Add stagetest feature module:
   - `website/app-shell/src/features/stagetest/StagetestPage.tsx`
   - `website/app-shell/src/features/stagetest/StagetestRunList.tsx`
   - `website/app-shell/src/features/stagetest/StagetestCaseTable.tsx`
   - `website/app-shell/src/features/stagetest/StagetestCaseDetail.tsx`
   - `website/app-shell/src/features/stagetest/stagetestClient.ts`
2. Route wiring:
   - add founder route for stagetest page in `website/app-shell/src/routes/index.tsx`
3. UI requirements:
   - API field form view (`request_fields`, `response_fields`)
   - synthetic input JSON view
   - produced output table view
   - assertion status columns
   - determinism hash and drift indicator
4. Add frontend tests:
   - `website/app-shell/tests/uat/stagetest.spec.ts`
   - fixtures under `website/app-shell/tests/uat/fixtures/stagetest-*.json`

### Acceptance

1. Browser view renders runs and cases from `/hoc/api/stagetest/*`.
2. Every displayed row includes artifact trace path + hash.
3. Playwright spec validates core render/filter/drilldown flow.

## Workstream 5: Publish Readiness for `stagetest.agenticverz.com`

### Tasks

1. Add deployment notes and infra checklist artifact:
   - `backend/app/hoc/docs/architecture/usecases/STAGETEST_SUBDOMAIN_DEPLOY_PLAN_2026-02-15.md`
2. Include:
   - host routing
   - auth enforcement
   - caching policy for artifact-backed API responses
   - TLS and access logging requirements
3. Add release checklist linking gate + UI + API verification.

### Acceptance

1. Subdomain deployment plan is executable by ops with clear prerequisites.
2. Release checklist references only canonical `/hoc/api/stagetest/*`.

## Workstream 6: Documentation and Tracker Sync

### Tasks

1. Update usecase index:
   - `backend/app/hoc/docs/architecture/usecases/INDEX.md`
2. Add stagetest evidence console references in linkage docs where relevant:
   - `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
3. Add a short reality-audit addendum section in implemented report for:
   - route prefix migration proof
   - artifact completeness proof
   - deterministic rerun proof

### Acceptance

1. Docs, routes, and gates are aligned on `/hoc/api/stagetest/*`.
2. No stale `/api/v1/stagetest/*` mention remains.

## Deterministic Command Pack (Run and Capture Logs)

From `/root/agenticverz2.0/backend`:

```bash
export PYTHONPATH=.
python3 scripts/verification/stagetest_route_prefix_guard.py
python3 scripts/verification/stagetest_artifact_check.py --strict --latest-run
python3 scripts/verification/uc_operation_manifest_check.py --strict
python3 scripts/ci/check_layer_boundaries.py
python3 scripts/ci/check_init_hygiene.py --ci
pytest -q tests/governance/t4/test_stagetest_route_prefix_guard.py
pytest -q tests/api/test_stagetest_read_api.py
pytest -q tests/uat/
./scripts/ops/hoc_uc_validation_uat_gate.sh
```

From `/root/agenticverz2.0/website/app-shell`:

```bash
npm run hygiene:ci
npm run boundary:ci
npm run typecheck:uat
npm run build
npm run test:uat:list
npx playwright test --config tests/uat/playwright.config.ts
```

## Required Deliverables

1. `backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_implemented.md`
2. `backend/app/hoc/docs/architecture/usecases/stagetest_artifact_schema.json`
3. `backend/app/hoc/docs/architecture/usecases/STAGETEST_SUBDOMAIN_DEPLOY_PLAN_2026-02-15.md`
4. Evidence logs directory:
   - `backend/app/hoc/docs/architecture/usecases/evidence_stagetest_hoc_api_2026_02_15/`

## Mandatory Format for `*_implemented.md` (Audit Contract)

The implementation report must include all sections below:

1. `Scope Executed` with explicit in/out list.
2. `File Change Ledger` table:
   - path
   - action (`CREATE|UPDATE|DELETE`)
   - purpose
3. `Route Prefix Migration Proof`:
   - grep command
   - before/after counts for `/api/v1/stagetest` and `/hoc/api/stagetest`
4. `Artifact Contract Proof`:
   - sample run directory tree
   - one sample case JSON excerpt
   - schema validation result
5. `API Contract Proof`:
   - endpoint list
   - sample responses
   - auth rejection checks
6. `UI Proof`:
   - screenshot references or Playwright assertions
   - field form visibility
   - synthetic input + output table rendering
7. `Gate Results` with exact command, exit code, and log file for each stage.
8. `Determinism Result`:
   - rerun hash comparison
   - drift flag status
9. `Residual Risks / Follow-ups`:
   - blockers
   - deferred items
10. `Definition of Done Checklist` with `PASS|FAIL` per criterion.

## Definition of Done

1. Canonical stagetest APIs are live under `/hoc/api/stagetest/*`.
2. UI renders API fields + synthetic input + produced output + assertions + determinism hash.
3. Artifact validator and route prefix guard are integrated and passing.
4. No `/api/v1/stagetest/*` usage remains.
5. `*_implemented.md` is complete and audit-ready with reproducible evidence.

## Claude Execute Command

```bash
claude -p "In /root/agenticverz2.0 execute backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15.md end-to-end. Implement all workstreams with canonical stagetest routes under /hoc/api/stagetest/* (never /api/v1/stagetest/*), run the full deterministic command pack, and publish backend/app/hoc/docs/architecture/usecases/STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_implemented.md with exact command outputs, exit codes, evidence log paths, route-migration proof, artifact proof, API proof, UI proof, and residual risks."
```
