# PR-4: Controls List Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing controls list facade endpoint and locks deterministic, validated read behavior for the fourth frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/controls/list` facade endpoint (gateway path: `/hoc/api/cus/controls/list`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `controls.query`.
- Add L5/L4 support method for exact paging metadata.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `topic=all` -> `registry.execute("controls.query", method="list_controls_page", state=None, ...)`
- `topic=enabled` -> `registry.execute("controls.query", method="list_controls_page", state="enabled", ...)`
- `topic=disabled` -> `registry.execute("controls.query", method="list_controls_page", state="disabled", ...)`
- `topic=auto` -> `registry.execute("controls.query", method="list_controls_page", state="auto", ...)`

## Files Changed
- `backend/app/hoc/api/cus/controls/controls_public.py`
- `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`
- `backend/tests/api/test_controls_public_facade_pr4.py`
- `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR4-CTRL-001` scaffold-to-contract gap:
  - Detected: no concrete controls public list facade boundary existed.
  - Fix: implemented strict read-only `/cus/controls/list` endpoint with topic-scoped dispatch and deterministic pagination semantics.
- `PR4-CTRL-002` pagination total gap:
  - Detected: existing list method did not provide exact total for one-call facade paging contract.
  - Fix: added `list_controls_page` in L5 + routed via L4 dispatch.
- `PR4-CTRL-003` ordering tie-break gap:
  - Detected: list ordering lacked explicit unique final key.
  - Fix: added deterministic sort tie-break by `id`.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] `topic` required and enum validated
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] Pagination bounds enforced (`limit`, `offset`)
- [ ] `control_type` enum validation enforced
- [ ] Deterministic ordering and tie-break fixed in L5
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_controls_public_facade_pr4.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
