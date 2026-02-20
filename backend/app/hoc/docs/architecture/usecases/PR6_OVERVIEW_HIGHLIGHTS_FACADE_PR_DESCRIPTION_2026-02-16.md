# PR-6: Overview Highlights Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing overview highlights facade endpoint and locks validated read behavior for the sixth frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/overview/highlights` facade endpoint (gateway path: `/hoc/api/cus/overview/highlights`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `overview.query`.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `GET /cus/overview/highlights` -> `registry.execute("overview.query", method="get_highlights")`

## Files Changed
- `backend/app/hoc/api/cus/overview/overview_public.py`
- `backend/tests/api/test_overview_public_facade_pr6.py`
- `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR6-OV-001` scaffold-to-contract gap:
  - Detected: no concrete overview public highlights boundary existed.
  - Fix: implemented strict read-only `/cus/overview/highlights` endpoint with one-dispatch contract and trace/meta propagation.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] One dispatch call to `overview.query` with `method=get_highlights`
- [ ] Stable `domain_counts` ordering retained
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_overview_public_facade_pr6.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
