# PR-7: Analytics Usage Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing analytics usage facade endpoint and locks validated read behavior for the seventh frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/analytics/statistics/usage` facade endpoint (gateway path: `/hoc/api/cus/analytics/statistics/usage`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `analytics.query`.

Out of scope:
- Mutations
- Export endpoints
- Frontend implementation

## Dispatch Map
- `GET /cus/analytics/statistics/usage` -> `registry.execute("analytics.query", method="get_usage_statistics", from_ts, to_ts, resolution, scope)`

## Files Changed
- `backend/app/hoc/api/cus/analytics/analytics_public.py`
- `backend/tests/api/test_analytics_public_facade_pr7.py`
- `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR7-AN-001` scaffold-to-contract gap:
  - Detected: no concrete analytics usage public boundary existed.
  - Fix: implemented strict read-only `/cus/analytics/statistics/usage` endpoint with one-dispatch contract and trace/meta propagation.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] Missing/invalid `from` and `to` rejected with `400 INVALID_QUERY`
- [ ] Invalid `resolution`/`scope` rejected with `400 INVALID_QUERY`
- [ ] Invalid time window rejected with `400 INVALID_QUERY`
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] One dispatch call to `analytics.query` with `method=get_usage_statistics`
- [ ] Stable `series` ordering retained
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_analytics_public_facade_pr7.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
