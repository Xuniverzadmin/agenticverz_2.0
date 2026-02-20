# FE-PR1-RUNS-LIVE-STAGETEST Frontend Slice Implementation Report

## Summary
Frontend slice for `activity` aligned to backend contract.

## Scope
- Route: `/page/activity/runs-live`
- Backend endpoint: `/hoc/api/cus/activity/runs`
- Contract: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Findings ledger: `docs/architecture/frontend/slices/fe-pr1-runs-live-stagetest-activity/SLICE_FINDINGS_LEDGER.md`

## Files Changed
- `website/app-shell/src/features/scaffold/scaffoldCatalog.ts`
- `website/app-shell/src/features/scaffold/ScaffoldSlicePage.tsx`
- `website/app-shell/src/features/scaffold/ScaffoldCatalogPage.tsx`
- `website/app-shell/src/routes/index.tsx`
- `website/app-shell/src/routing/RouteGuardAssertion.tsx`
- `docs/architecture/frontend/slices/fe-pr1-runs-live-stagetest-activity/SLICE_EXECUTION.md`
- `docs/architecture/frontend/slices/fe-pr1-runs-live-stagetest-activity/SLICE_FINDINGS_LEDGER.md`
- `docs/architecture/frontend/slices/fe-pr1-runs-live-stagetest-activity/SLICE_IMPLEMENTATION_REPORT.md`
- `docs/architecture/frontend/slices/fe-pr1-runs-live-stagetest-activity/SLICE_ACCEPTANCE_MATRIX.md`

## Implementation Notes
- API boundary behavior: route-level metadata maps PR1 live topic to `/hoc/api/cus/activity/runs?topic=live&limit=50&offset=0`.
- Page behavior: scaffold page renders contract metadata + live probe status + payload preview for rapid slice validation.
- Error/observability behavior: probe records HTTP status/content-type/body preview; HTML fallback is flagged; backend `x-request-id` visible in headers.
- Historical preflight note: this slice originally used `X-HOC-Scaffold-Fixture: pr1-runs-live-v1` for synthetic payload checks before PR2 auth closure.

## Test/Evidence Commands
```bash
# backend PR1 facade contract checks
cd /root/agenticverz2.0/backend && pytest tests/api/test_runs_facade_pr1.py -q
# result: 20 passed, 0 failed

# frontend build + guards
cd /root/agenticverz2.0/website/app-shell && npm run build
# result: build passed

# stagetest route availability
curl -ksS -D /tmp/pr1_page_headers.txt https://stagetest.agenticverz.com/page/activity/runs-live -o /tmp/pr1_page_body.html
# result: HTTP/2 200

# stagetest facade reachability
curl -ksS -D /tmp/pr1_api_headers.txt 'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0' -o /tmp/pr1_api_body.json
# result: HTTP/2 401 without fixture header

# stagetest scaffold fixture payload
curl -ksS -D /tmp/pr1_api_fixture_headers.txt 'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0' \
  -H 'X-HOC-Scaffold-Fixture: pr1-runs-live-v1' \
  -o /tmp/pr1_api_fixture_body.json
# result: HTTP/2 200 contract-shaped payload
```

## Performance Notes
- Pagination: fixed initial probe page (`limit=50`, `offset=0`) for deterministic first-load behavior.
- Virtualization: not applicable in scaffold phase (raw JSON preview only).
- Polling/backoff: none; single probe on mount.

## Post-Merge Sync (2026-02-20)
- Backend PR-1 recovery (`#12`) is merged.
- PR2 auth closure is merged and fixture/public bypass behavior is retired:
  - `backend/app/hoc/docs/architecture/usecases/PR2_AUTH_CLOSURE_EVIDENCE.md`
- Current stagetest no-auth probe is expected to return `401`; authenticated path remains required for `200` page-level evidence.

## Promotion Recommendation
- Current gate status: NOT_ELIGIBLE
- Blockers:
  - Browser-authenticated tenant runtime evidence is still missing.
  - Need PR1 display UX beyond raw JSON preview (domain table/cards) before public promotion.
