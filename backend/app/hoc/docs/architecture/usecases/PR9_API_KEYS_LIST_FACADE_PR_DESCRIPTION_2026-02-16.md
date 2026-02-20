# PR-9: API Keys List Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing API keys list facade endpoint and locks validated read behavior for the ninth frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR9_API_KEYS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR9_API_KEYS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/api_keys/list` facade endpoint (gateway path: `/hoc/api/cus/api_keys/list`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `api_keys.query`.
- Add deterministic L6 tie-break for API key list ordering.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `GET /cus/api_keys/list` -> `registry.execute("api_keys.query", method="list_api_keys", status, limit, offset)`

## Files Changed
- `backend/app/hoc/api/cus/api_keys/api_keys_public.py`
- `backend/app/hoc/cus/api_keys/L6_drivers/api_keys_facade_driver.py`
- `backend/tests/api/test_api_keys_public_facade_pr9.py`
- `backend/app/hoc/docs/architecture/usecases/PR9_API_KEYS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR9_API_KEYS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR9_API_KEYS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR9-AK-001` scaffold-to-contract gap:
  - Detected: no concrete API keys list public boundary existed.
  - Fix: implemented strict read-only `/cus/api_keys/list` endpoint with one-dispatch contract and trace/meta propagation.
- `PR9-AK-002` ordering tie-break gap:
  - Detected: list ordering lacked unique stable final key.
  - Fix: added `id desc` tie-break in L6 list query.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] Invalid `status` rejected with `400 INVALID_QUERY`
- [ ] Pagination bounds enforced (`limit`, `offset`)
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] One dispatch call to `api_keys.query` with `method=list_api_keys`
- [ ] Deterministic ordering retained with L6 tie-break keys
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_api_keys_public_facade_pr9.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
