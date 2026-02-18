# FE-PR1-RUNS-LIVE-STAGETEST Frontend Slice Acceptance Matrix

## Route
- Frontend route: `/page/activity/runs-live`
- Backend endpoint: `/hoc/api/cus/activity/runs`

| Area | Scenario | Expected | Evidence | Status |
|---|---|---|---|---|
| Routing | Route wired | Route resolves correctly | `curl https://stagetest.agenticverz.com/page/activity/runs-live` -> HTTP 200 on 2026-02-18 | PASS |
| Query Validation | Unknown param | Actionable error state | `pytest tests/api/test_runs_facade_pr1.py -q` includes invalid param test (`?foo=bar`) and passed | PASS |
| Contract | Payload parse pass | UI renders | `curl .../hoc/api/cus/activity/runs?...` with `X-HOC-Scaffold-Fixture: pr1-runs-live-v1` -> HTTP 200 contract-shaped JSON | PASS |
| Contract | Payload mismatch | Contract mismatch UI | `ScaffoldSlicePage` HTML fallback warning path implemented and manually verified by code path | PASS |
| Observability | request-id shown | Error includes request-id | `curl .../hoc/api/cus/activity/runs?...` returned `x-request-id: 4f858df3-ac43-4be4-bc68-1f6cfd939e6b` | PASS |
| Determinism | Repeated same query | Stable order | `pytest tests/api/test_runs_facade_pr1.py -q` determinism test passed | PASS |
| Pagination | Next page behavior | Contract-aligned | `pytest tests/api/test_runs_facade_pr1.py -q` pagination tests passed | PASS |
| Quality | lint/test/build | Pass | `npm run build` passed on 2026-02-18; backend PR1 tests passed | PASS |

## Gate Summary
- G0: PASS (contract frozen and referenced)
- G1: PASS (UI map + request mapping documented)
- G2: PASS (API probe boundary implemented)
- G3: PASS (slice page exposed under scaffold path)
- G4: PASS (stagetest route and facade reachability verified)
- G5: PASS (build + PR1 backend tests green)
- G6: BLOCKED (temporary scaffold bypass + synthetic fixture evidence only; production promotion remains blocked)
- Overall: NOT_ELIGIBLE
