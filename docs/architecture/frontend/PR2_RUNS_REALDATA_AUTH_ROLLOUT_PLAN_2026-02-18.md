# PR2 Runs Real-Data Auth Rollout Plan (2026-02-18)

- Capability ID: `CAP-CUS-ACT-RUNS-REALDATA-PR2`
- Scope: Replace PR1 fixture-backed scaffold behavior with authenticated real-data facade behavior for runs live/completed.
- Surfaces:
  - `/hoc/api/cus/activity/runs` (backend facade)
  - `/page/activity/runs-live` (scaffold probe)
  - `/page/activity/runs-completed` (scaffold probe)

## Goals
- Keep PR1 route/UI wiring intact.
- Serve real tenant data behind normal auth.
- Retire temporary preflight bypasses introduced for scaffold proof.

## Non-Goals
- New production table/card UX beyond scaffold payload preview.
- Broader domain expansion beyond activity runs live/completed.

## Implementation Steps
### Iteration 1 (completed 2026-02-18)
- Removed temporary RBAC public scaffold rule for `/cus/activity/runs`.
- Removed fixture toggle env from compose (`HOC_PR1_RUNS_SCAFFOLD_FIXTURE_ENABLED`).
- Removed PR1 scaffold probe fixture headers from `/page/activity/runs-live` and `/page/activity/runs-completed`.

### Iteration 2 (next)
- Captured pre-deploy stagetest evidence on 2026-02-18:
  - no fixture header -> `401` for both live and completed
  - manual fixture headers still return `200` fixture payloads (legacy runtime still deployed)
- Recorded in `docs/memory-pins/PIN-576-pr2-runs-realdata-auth-rollout-iteration-2-predeploy-evidence.md`.

### Iteration 3 (next)
1. Backend dispatch to real data
- Keep `GET /cus/activity/runs` contract shape unchanged.
- Validate `topic=live|completed` + existing query validation behavior.
- Ensure dispatch uses authenticated tenant context and real registry methods.

2. Fixture mode policy
- Keep fixture behavior disabled on stagetest/production paths.
- If fixture code is reintroduced for local testing, keep it local/test-only and non-routable in production.

3. RBAC cleanup
- Remove temporary rule `CUS_ACTIVITY_RUNS_SCAFFOLD_PREFLIGHT` from `design/auth/RBAC_RULES.yaml`.
- Confirm normal auth path is required for `/cus/activity/runs`.

4. Frontend probe behavior
- Keep same `/page/<domain>/<subpage>` URLs.
- Remove fixture headers from PR1 runs entries once real data path is verified.
- Ensure probe still shows clear `401` when unauthenticated and contract JSON when authenticated.

5. Tests and verification
- Backend:
  - facade tests for live/completed with authenticated context
  - negative tests for invalid query params
- Environment:
  - stagetest probe: unauthenticated `401`, authenticated `200` with real payload
- Frontend:
  - build + route rendering checks

6. Documentation updates
- Update PR1 live/completed slice docpacks to mark fixture-based evidence as superseded.
- Add PR2 acceptance evidence for authenticated real-data behavior.

## Acceptance Criteria
- `/hoc/api/cus/activity/runs?topic=live` returns:
  - unauthenticated: `401`
  - authenticated: `200` contract-shaped real payload
- `/hoc/api/cus/activity/runs?topic=completed` returns:
  - unauthenticated: `401`
  - authenticated: `200` contract-shaped real payload
- Temporary preflight RBAC scaffold rule removed.
- No fixture header required for normal stagetest validation.

## Rollback
1. Re-enable fixture mode only in controlled test environments if regression blocks validation.
2. Reintroduce temporary rule only as time-boxed emergency path with explicit expiry.
3. Keep PR1 scaffold pages published; they remain diagnostics surfaces.
