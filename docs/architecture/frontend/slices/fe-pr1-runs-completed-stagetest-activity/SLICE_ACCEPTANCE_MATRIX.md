# FE-PR1-RUNS-COMPLETED-STAGETEST Frontend Slice Acceptance Matrix

## Route
- Frontend route: `/page/activity/runs-completed`
- Backend endpoint: `/hoc/api/cus/activity/runs`

| Area | Scenario | Expected | Evidence | Status |
|---|---|---|---|---|
| Routing | Route wired | Route resolves correctly | `curl https://stagetest.agenticverz.com/page/activity/runs-completed` -> HTTP 200 on 2026-02-18 | PASS |
| Query Validation | Unknown fixture key | Actionable validation error | `X-HOC-Scaffold-Fixture: bad-fixture-id` -> HTTP 400 (`INVALID_QUERY`) | PASS |
| Contract | Payload parse pass | UI renders completed payload | `topic=completed` + fixture header -> HTTP 200 JSON (`run_comp_003`) | PASS |
| Contract | Fixture/topic mismatch | Fail fast, no fallback payload | `pytest tests/api/test_runs_facade_pr1.py -q` mismatch tests passed | PASS |
| Observability | request-id present | Response traceability retained | `/tmp/pr1_completed_fixture_headers.txt` includes `x-request-id` header | PASS |
| Determinism | Repeated same query | Stable ordering and pagination semantics | `pytest tests/api/test_runs_facade_pr1.py -q` determinism tests passed | PASS |
| Pagination | Next page behavior | Contract-aligned metadata | fixture response includes `next_offset=2` for `limit=2` | PASS |
| Quality | lint/test/build | Pass | backend tests `20 passed`; `npm run build` passed | PASS |

## Gate Summary
- G0: PASS (contract frozen and referenced)
- G1: PASS (UI map and topic-specific probe mapping documented)
- G2: PASS (completed probe and header boundary implemented)
- G3: PASS (slice page published under scaffold path)
- G4: PASS (stagetest route/probe verified)
- G5: PASS (backend tests + frontend build green)
- G6: BLOCKED (fixture-backed scaffold evidence only; not production data)
- Overall: NOT_ELIGIBLE
