# PR-5: Logs Replay Feed Facade Hardening (Read-Only)

## Summary
This PR adds a thin customer-facing logs replay-feed facade endpoint and locks deterministic, validated read behavior for the fifth frontend vertical slice.

Authoritative contract:
- `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
Issue ledger:
- `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_ISSUE_LEDGER_2026-02-16.md`

## Scope
- Add `GET /cus/logs/list` facade endpoint (gateway path: `/hoc/api/cus/logs/list`).
- Keep scope read-only and minimal-diff.
- Strict boundary validation in facade.
- One registry dispatch per request to `logs.query`.
- Add deterministic L6 tie-break for logs feed ordering.

Out of scope:
- Mutations
- Frontend implementation

## Dispatch Map
- `topic=llm_runs` -> `registry.execute("logs.query", method="list_llm_run_records", limit, offset)`
- `topic=system_records` -> `registry.execute("logs.query", method="list_system_records", limit, offset)`

## Files Changed
- `backend/app/hoc/api/cus/logs/logs_public.py`
- `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`
- `backend/tests/api/test_logs_public_facade_pr5.py`
- `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_ISSUE_LEDGER_2026-02-16.md`
- `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issues Surfaced and Fixed
- `PR5-LOG-001` scaffold-to-contract gap:
  - Detected: no concrete logs public replay-feed boundary existed.
  - Fix: implemented strict read-only `/cus/logs/list` endpoint with topic-scoped dispatch and deterministic pagination semantics.
- `PR5-LOG-002` ordering tie-break gap:
  - Detected: list ordering lacked unique stable final key.
  - Fix: added `id desc` tie-break in both L6 list queries.

## Acceptance Checklist
- [ ] Route uniqueness: one backend route path only
- [ ] `topic` required and enum validated
- [ ] Unknown query params rejected with `400 INVALID_QUERY`
- [ ] `as_of` rejected with `400 UNSUPPORTED_PARAM`
- [ ] Pagination bounds enforced (`limit`, `offset`)
- [ ] Deterministic ordering retained with L6 tie-break keys
- [ ] `X-Request-ID` equals `meta.request_id`
- [ ] Correlation header echoed to `meta.correlation_id`

## Verification Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_logs_public_facade_pr5.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
