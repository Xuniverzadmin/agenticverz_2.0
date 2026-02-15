# Stagetest Evidence Console Plan (HOC API Paths)

## Strategy

1. Use `stagetest.agenticverz.com` as a read-only evidence console, not a test runner.
2. Make UI truth come from machine-generated JSON artifacts, not markdown claims.
3. Split execution vs visualization:
   - Tests run in backend/CI/Claude.
   - Visualization reads signed artifacts via read-only HOC APIs.
   - Publish is deterministic deploy.

## Updated Read APIs (replace `/api/v1/*`)

1. `GET /hoc/api/stagetest/runs`
2. `GET /hoc/api/stagetest/runs/{run_id}`
3. `GET /hoc/api/stagetest/runs/{run_id}/cases`
4. `GET /hoc/api/stagetest/runs/{run_id}/cases/{case_id}`
5. `GET /hoc/api/stagetest/apis`

## Reality Gap to Close First

1. Current Stage 1.1/1.2 evidence is mostly pass/fail logs, not full request/response payload artifacts.
2. Add structured per-case artifact emission before UI rollout.

## Target Architecture

1. Evidence emitter during tests:
   - `run_summary.json`
   - `case_result.json` per case with `uc_id`, `case_id`, `operation`, `stage`, `status`
   - API contract snapshot: method/path/operation + request/response field schema
   - Synthetic input snapshot
   - Observed output snapshot
   - Assertions + determinism hash/signature
2. Read-only HOC API layer under `backend/app/hoc/api/...`
3. Browser UI in app-shell with:
   - API field form panel
   - Synthetic input panel
   - Produced output table + assertion columns
   - Filters: UC, stage, status, drift
4. Subdomain publish: `stagetest.agenticverz.com`, founder/auth-only.

## Execution Phases

1. Phase 1: Artifact contract
   - Create `backend/app/hoc/docs/architecture/usecases/stagetest_artifact_schema.json`
   - Update Stage 1.1 + 1.2 runners/tests to emit artifacts under `backend/artifacts/stagetest/<run_id>/`
   - Add schema validation test.
2. Phase 2: Determinism + integrity gates
   - Extend `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`
   - Gate on artifact completeness, hash presence, and required payload fields
   - Fail on missing request/response/input/output/assertion evidence.
3. Phase 3: HOC read APIs (`/hoc/api/stagetest/*`)
   - Add router: `backend/app/hoc/api/fdr/ops/stagetest.py`
   - Register in facade: `backend/app/hoc/api/facades/fdr/ops.py`
   - Add read engine/repo in HOC domain layer for artifact indexing and retrieval
   - Add auth guard (founder-only).
4. Phase 4: UI evidence console
   - Extend `website/app-shell/src/features/uat/*` (or add `src/features/stagetest/*`)
   - Add views for API fields, synthetic input JSON, output JSON, assertions/status/hash
   - Add run/case drilldown and filters.
5. Phase 5: Domain and routing migration checks
   - Ensure docs, route maps, and tests use `/hoc/api/*` not `/api/v1/*` for stagetest
   - Add regression test to prevent accidental `/api/v1/stagetest/*` reintroduction.
6. Phase 6: Subdomain publish
   - Add vhost/ingress for `stagetest.agenticverz.com`
   - Point to app-shell route entry
   - Enforce founder auth + cache rules for evidence payloads.

## Acceptance Criteria

1. Every displayed case includes API fields, synthetic input, produced output, assertions, status, and determinism hash.
2. Every UI row is traceable to one artifact file path + hash.
3. Re-running same synthetic inputs yields same determinism hash or explicit drift flag.
4. All stagetest routes are served from `/hoc/api/stagetest/*`, with no `/api/v1/stagetest/*` usage.
