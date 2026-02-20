# PR-2: Incidents List Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing incidents list facade endpoint and locks deterministic, validated read behavior for the second frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/incidents/list` facade endpoint (gateway path: `/hoc/api/cus/incidents/list`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `incidents.query`.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `topic=active` -> `registry.execute("incidents.query", method="list_active_incidents", ...)`
- `topic=resolved` -> `registry.execute("incidents.query", method="list_resolved_incidents", ...)`
- `topic=historical` -> `registry.execute("incidents.query", method="list_historical_incidents", ...)`

## Files Changed
- `backend/app/hoc/api/cus/incidents/incidents_public.py`
- `backend/tests/api/test_incidents_public_facade_pr2.py`
- `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR2-INC-001` scaffold-to-contract gap:
  - Detected: no concrete incidents public list facade boundary existed.
  - Fix: implemented strict read-only `/cus/incidents/list` endpoint with topic-scoped dispatch and deterministic pagination semantics.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] `topic` required and enum validated
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] Pagination bounds enforced (`limit`, `offset`, `retention_days`)
- [ ] Deterministic ordering params fixed per topic
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_incidents_public_facade_pr2.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
