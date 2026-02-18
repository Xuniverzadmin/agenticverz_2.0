# PIN-575: PR2 Runs Real-Data Auth Rollout — Iteration 1

**Created:** 2026-02-18
**Status:** IN_PROGRESS
**Category:** Frontend / Auth / RBAC
**Depends on:** PIN-570 (temporary auth bypass), PR #3 merge (`b36ff7dc`)

---

## Summary

Started PR-2 rollout to move Activity Runs scaffold from temporary fixture/bypass posture to normal auth + real-data posture.

Iteration 1 removes temporary scaffold allowances and keeps `/page/activity/runs-live` + `/page/activity/runs-completed` on the authenticated facade path.

## Changes Applied

1. Removed temporary public RBAC rule for runs scaffold path.
- File: `design/auth/RBAC_RULES.yaml`
- Removed rule: `CUS_ACTIVITY_RUNS_SCAFFOLD_PREFLIGHT`

2. Removed fixture-mode compose toggle.
- File: `docker-compose.yml`
- Removed env: `HOC_PR1_RUNS_SCAFFOLD_FIXTURE_ENABLED`

3. Removed fixture header injection from PR1 scaffold probes.
- File: `website/app-shell/src/features/scaffold/scaffoldCatalog.ts`
- Removed headers:
  - `X-HOC-Scaffold-Fixture: pr1-runs-live-v1`
  - `X-HOC-Scaffold-Fixture: pr1-runs-completed-v1`

4. Updated rollout plan with completed iteration log.
- File: `docs/architecture/frontend/PR2_RUNS_REALDATA_AUTH_ROLLOUT_PLAN_2026-02-18.md`

## Expected Runtime Behavior After Iteration 1

- `GET /hoc/api/cus/activity/runs?topic=live`:
  - unauthenticated -> `401`
  - authenticated -> `200` (contract-shaped real payload)
- `GET /hoc/api/cus/activity/runs?topic=completed`:
  - unauthenticated -> `401`
  - authenticated -> `200` (contract-shaped real payload)

## Next Iteration

- Capture authenticated stagetest evidence for both topics (live/completed).
- Update slice acceptance docs to mark fixture-backed evidence as superseded by auth real-data evidence.
- Open implementation PR updates on PR #4 branch.
