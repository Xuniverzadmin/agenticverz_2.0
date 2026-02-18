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

### Iteration 2 (completed 2026-02-18, pre-deploy evidence)
- Captured pre-deploy stagetest evidence:
  - no fixture header -> `401` for both live and completed
  - manual fixture headers still return `200` fixture payloads (legacy runtime still deployed)
- Recorded in `docs/memory-pins/PIN-576-pr2-runs-realdata-auth-rollout-iteration-2-predeploy-evidence.md`.

### Iteration 3 (completed 2026-02-18, post-deploy enforcement evidence)
- Deployed backend from merged `main` (`a7121076`) and reran rollout verifier on stagetest.
- Captured post-deploy evidence:
  - no fixture header -> `401` for live and completed
  - legacy fixture headers -> `401` for live and completed (no bypass)
- Recorded in `docs/memory-pins/PIN-578-pr2-runs-postdeploy-auth-enforcement-evidence.md`.

### Iteration 4 (next)
1. Authenticated positive-path evidence
- Run verifier with `AUTH_COOKIE` to capture `200` contract-shaped real payload for:
  - `topic=live`
  - `topic=completed`

2. Acceptance closure updates
- Update PR2 acceptance artifacts with authenticated success evidence.
- Mark PR2 rollout complete when both topics pass authenticated checks.

3. PR3 kickoff
- Start next scope after PR2 closure evidence is complete.

## Acceptance Criteria
- `/hoc/api/cus/activity/runs?topic=live` returns:
  - unauthenticated: `401`
  - authenticated: `200` contract-shaped real payload
- `/hoc/api/cus/activity/runs?topic=completed` returns:
  - unauthenticated: `401`
  - authenticated: `200` contract-shaped real payload
- Temporary preflight RBAC scaffold rule removed.
- Legacy fixture header path no longer yields fixture payloads.

## Rollback
1. Re-enable fixture mode only in controlled test environments if regression blocks validation.
2. Reintroduce temporary rule only as time-boxed emergency path with explicit expiry.
3. Keep PR1 scaffold pages published; they remain diagnostics surfaces.
