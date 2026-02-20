# FE-PR1-RUNS-COMPLETED-STAGETEST Frontend Slice Implementation Report

## Summary
Completed-runs scaffold slice is wired to the PR1 contract surface; post-PR2 auth closure runtime now requires authenticated context for positive-path payload evidence.

## Scope
- Route: `/page/activity/runs-completed`
- Backend endpoint: `/hoc/api/cus/activity/runs`
- Contract: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Findings ledger: `docs/architecture/frontend/slices/fe-pr1-runs-completed-stagetest-activity/SLICE_FINDINGS_LEDGER.md`

## Files Changed
- `backend/app/hoc/api/cus/activity/runs_facade.py`
- `backend/tests/api/test_runs_facade_pr1.py`
- `website/app-shell/src/features/scaffold/scaffoldCatalog.ts`
- `website/app-shell/src/features/scaffold/ScaffoldSlicePage.tsx`
- `website/app-shell/src/features/scaffold/ScaffoldCatalogPage.tsx`
- `website/app-shell/src/routes/index.tsx`
- `website/app-shell/src/routing/RouteGuardAssertion.tsx`
- `design/auth/RBAC_RULES.yaml`
- `docker-compose.yml`
- `docs/architecture/frontend/slices/fe-pr1-runs-completed-stagetest-activity/SLICE_EXECUTION.md`
- `docs/architecture/frontend/slices/fe-pr1-runs-completed-stagetest-activity/SLICE_FINDINGS_LEDGER.md`
- `docs/architecture/frontend/slices/fe-pr1-runs-completed-stagetest-activity/SLICE_IMPLEMENTATION_REPORT.md`
- `docs/architecture/frontend/slices/fe-pr1-runs-completed-stagetest-activity/SLICE_ACCEPTANCE_MATRIX.md`

## Implementation Notes
- API boundary behavior: completed topic probe maps to `/hoc/api/cus/activity/runs?topic=completed&limit=50&offset=0`.
- Page behavior: scaffold page renders contract details and live probe payload preview for completed topic.
- Guardrail behavior: unknown fixture ids and topic/fixture mismatches return `400 INVALID_QUERY`.
- Historical preflight note: fixture-specific checks were used during initial scaffold phase; current runtime is auth-enforced.

## Test/Evidence Commands
```bash
# backend PR1 facade tests
cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py
# result: 20 passed

# frontend build
cd /root/agenticverz2.0/website/app-shell && npm run build
# result: build passed

# completed route availability
curl -ksS -o /tmp/pr1_completed_page.html -w '%{http_code} %{content_type}\n' \
  https://stagetest.agenticverz.com/page/activity/runs-completed
# result: 200 text/html

# completed facade auth path
curl -ksS -o /tmp/pr1_completed_nohdr.json -w '%{http_code} %{content_type}\n' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# result: 401 application/json

# completed fixture payload
curl -ksS -o /tmp/pr1_completed_fixture.json -w '%{http_code} %{content_type}\n' \
  -H 'X-HOC-Scaffold-Fixture: pr1-runs-completed-v1' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# result: 200 application/json
```

## Performance Notes
- Pagination: deterministic first probe page with `limit=50`, `offset=0`.
- Virtualization: not in scope for scaffold phase.
- Polling/backoff: none in scaffold probe.

## Post-Merge Sync (2026-02-20)
- Backend PR-1 recovery (`#12`) is merged.
- PR2 auth closure is merged and fixture/public bypass behavior is retired:
  - `backend/app/hoc/docs/architecture/usecases/PR2_AUTH_CLOSURE_EVIDENCE.md`
- Current stagetest no-auth probe is expected to return `401`; authenticated path remains required for `200` page-level evidence.

## Promotion Recommendation
- Current gate status: NOT_ELIGIBLE
- Blockers:
- Browser-authenticated tenant runtime evidence is still missing.
- Production display UX for completed runs remains pending (current scaffold renders raw payload preview).

## Rollback Plan
- Keep frontend pages published; they should continue returning auth-gated probe responses until authenticated session evidence is available.
