# PR-1: Runs Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing runs facade endpoint and locks deterministic, validated read behavior for the first frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/activity/runs` facade endpoint (gateway path: `/hoc/api/cus/activity/runs`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `activity.query`.

Out of scope:
- Signals topic
- Mutations
- Frontend implementation

## Dispatch Map
- `topic=live` -> `registry.execute("activity.query", method="get_live_runs", ...)`
- `topic=completed` -> `registry.execute("activity.query", method="get_completed_runs", ...)`

## Files Changed
- `backend/app/hoc/api/cus/activity/runs_facade.py`
- `backend/app/hoc/api/facades/cus/activity/activity_fac.py`
- `backend/app/hoc/cus/activity/L6_drivers/activity_read_driver.py`
- `backend/tests/api/test_runs_facade_pr1.py`
- `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR1-RUNS-001` pagination contract drift:
  - Detected mismatch: facade trusted upstream `has_more`.
  - Contract fix applied: derive `has_more` as `(offset + len(runs) < total)`.
  - Regression test added to enforce boundary recomputation.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] `topic` required and enum validated
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] Pagination bounds enforced (`limit`, `offset`)
- [ ] Deterministic ordering with tie-break enforced
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
