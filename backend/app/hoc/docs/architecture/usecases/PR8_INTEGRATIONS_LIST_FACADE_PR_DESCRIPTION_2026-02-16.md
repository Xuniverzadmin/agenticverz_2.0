# PR-8: Integrations List Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing integrations list facade endpoint and locks validated read behavior for the eighth frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/integrations/list` facade endpoint (gateway path: `/hoc/api/cus/integrations/list`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `integrations.query`.
- Add deterministic L6 tie-break for integrations list ordering.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `GET /cus/integrations/list` -> `registry.execute("integrations.query", method="list_integrations", offset, limit, status, provider_type)`

## Files Changed
- `backend/app/hoc/api/cus/integrations/integrations_public.py`
- `backend/app/hoc/cus/integrations/L6_drivers/cus_integration_driver.py`
- `backend/tests/api/test_integrations_public_facade_pr8.py`
- `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR8-INT-001` scaffold-to-contract gap:
  - Detected: no concrete integrations list public boundary existed.
  - Fix: implemented strict read-only `/cus/integrations/list` endpoint with one-dispatch contract and trace/meta propagation.
- `PR8-INT-002` ordering tie-break gap:
  - Detected: list ordering lacked unique stable final key.
  - Fix: added `id desc` tie-break in L6 list query.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] Invalid `status`/`provider_type` rejected with `400 INVALID_QUERY`
- [ ] Pagination bounds enforced (`limit`, `offset`)
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] One dispatch call to `integrations.query` with `method=list_integrations`
- [ ] Deterministic ordering retained with L6 tie-break keys
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_integrations_public_facade_pr8.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
