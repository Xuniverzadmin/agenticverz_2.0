# PR-10: Account Users List Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing account users list facade endpoint and locks validated read behavior for the tenth frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/account/users/list` facade endpoint (gateway path: `/hoc/api/cus/account/users/list`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `account.query`.
- Add deterministic L6 tie-break for account users list ordering.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `GET /cus/account/users/list` -> `registry.execute("account.query", method="list_users", role, status, limit, offset)`

## Files Changed
- `backend/app/hoc/api/cus/account/account_public.py`
- `backend/app/hoc/cus/account/L6_drivers/accounts_facade_driver.py`
- `backend/tests/api/test_account_public_facade_pr10.py`
- `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR10-AC-001` scaffold-to-contract gap:
  - Detected: no concrete account users list public boundary existed.
  - Fix: implemented strict read-only `/cus/account/users/list` endpoint with one-dispatch contract and trace/meta propagation.
- `PR10-AC-002` ordering tie-break gap:
  - Detected: list ordering lacked unique stable final key.
  - Fix: added `id asc` tie-break in L6 list query after `email asc`.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] Invalid `role` rejected with `400 INVALID_QUERY`
- [ ] Invalid `status` rejected with `400 INVALID_QUERY`
- [ ] Pagination bounds enforced (`limit`, `offset`)
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] One dispatch call to `account.query` with `method=list_users`
- [ ] Deterministic ordering retained with L6 tie-break keys
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_account_public_facade_pr10.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
