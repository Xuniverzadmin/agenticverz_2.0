# PR-3: Policies List Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing policies list facade endpoint and locks deterministic, validated read behavior for the third frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/policies/list` facade endpoint (gateway path: `/hoc/api/cus/policies/list`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `policies.query`.
- Add deterministic L6 tie-break for rules ordering.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `topic=active` -> `registry.execute("policies.query", method="list_policy_rules", status="ACTIVE", ...)`
- `topic=retired` -> `registry.execute("policies.query", method="list_policy_rules", status="RETIRED", ...)`

## Files Changed
- `backend/app/hoc/api/cus/policies/policies_public.py`
- `backend/app/hoc/cus/policies/L6_drivers/policies_facade_driver.py`
- `backend/tests/api/test_policies_public_facade_pr3.py`
- `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR3-POL-001` scaffold-to-contract gap:
  - Detected: no concrete policies public list facade boundary existed.
  - Fix: implemented strict read-only `/cus/policies/list` endpoint with topic-scoped dispatch and deterministic pagination semantics.
- `PR3-POL-002` ordering tie-break gap:
  - Detected: query ordering lacked unique stable final key.
  - Fix: added `PolicyRule.id.desc()` to L6 ordering chain.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] `topic` required and enum validated
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] Pagination bounds enforced (`limit`, `offset`)
- [ ] Date-window validation enforced (`created_after <= created_before`)
- [ ] Deterministic ordering preserved and tie-break fixed in L6
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_policies_public_facade_pr3.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
