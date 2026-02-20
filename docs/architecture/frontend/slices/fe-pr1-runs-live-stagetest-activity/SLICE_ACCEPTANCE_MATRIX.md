# FE-PR1-RUNS-LIVE-STAGETEST Frontend Slice Acceptance Matrix

## Route
- Frontend route: `/page/activity/runs-live`
- Backend endpoint: `/hoc/api/cus/activity/runs`
- Backend recovery PR: `#12` (merged 2026-02-20)

| Area | Scenario | Expected | Evidence | Status |
|---|---|---|---|---|
| Routing | Route wired | Route resolves correctly | `curl https://stagetest.agenticverz.com/page/activity/runs-live` -> HTTP 200 on 2026-02-20 | PASS |
| Auth Boundary | No auth on CUS API | Explicit auth rejection | `curl .../hoc/api/cus/activity/runs?topic=live...` -> HTTP 401 on 2026-02-20 | PASS |
| Contract | Positive-path payload (auth required) | 200 contract-shaped JSON when authenticated | `backend/app/hoc/docs/architecture/usecases/PR2_AUTH_CLOSURE_EVIDENCE.md` test matrix #2 (`200`, 6 runs) | PASS |
| Query Validation | Unknown param | Actionable validation behavior | `PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py` -> 14 passed (includes invalid query coverage) | PASS |
| Determinism | Repeated same query | Stable ordering | `PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py` -> determinism assertions pass | PASS |
| Pagination | Next page behavior | Contract-aligned pagination | `PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py` -> pagination assertions pass | PASS |
| Quality | Build/tests | Pass | `npm run build` (frontend) + PR-1 backend tests green in merge PR #12 | PASS |

## Gate Summary
- G0: PASS (contract frozen and referenced)
- G1: PASS (UI map + request mapping documented)
- G2: PASS (API probe boundary implemented)
- G3: PASS (slice page exposed under scaffold path)
- G4: PASS (stagetest route + auth boundary verified)
- G5: PASS (build + backend PR-1 tests green)
- G6: BLOCKED (browser-authenticated tenant session evidence still pending for page-level positive path)
- Overall: NOT_ELIGIBLE
