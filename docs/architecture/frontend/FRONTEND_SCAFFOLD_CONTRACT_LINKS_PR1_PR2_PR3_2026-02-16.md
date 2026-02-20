# FRONTEND_SCAFFOLD_CONTRACT_LINKS_PR1_PR2_PR3_2026-02-16

## Purpose
Establish the frontend scaffold baseline using backend-frozen facade contracts for the first three read vertical slices.

## Linked Backend Contracts (Authoritative)
1. Runs vertical slice (PR-1):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Issue ledger: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_ISSUE_LEDGER_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/activity/runs`

2. Incidents vertical slice (PR-2):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Issue ledger: `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/incidents/list`

3. Policies vertical slice (PR-3):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Issue ledger: `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/policies/list`

## Frontend Scaffold Rules (Immediate)
- Build one typed API client module and bind these read endpoints first.
- Enforce runtime parsing at API boundary (contract mismatch visible in UI).
- Use server-side pagination from contract fields (`total`, `has_more`, `pagination.next_offset`).
- Show request-id/correlation-id aware error states.
- Do not implement mutations until read slices are stable.

## Slice-by-Slice Build Sequence
1. `/runs` page (read-only, server pagination).
2. `/incidents` page (read-only, topic list via `/list?topic=...`).
3. `/policies` page (read-only, topic list via `/list?topic=...`).
4. Shared error/loading/empty shell states.

## Notes
- Frontend strategy docs live under `docs/architecture/frontend/`.
- Backend contracts stay under `backend/app/hoc/docs/architecture/usecases/` and are consumed via links, not duplicated.
