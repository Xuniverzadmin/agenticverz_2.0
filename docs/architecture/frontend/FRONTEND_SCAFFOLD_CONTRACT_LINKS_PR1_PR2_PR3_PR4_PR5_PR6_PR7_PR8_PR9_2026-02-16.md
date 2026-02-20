# FRONTEND_SCAFFOLD_CONTRACT_LINKS_PR1_PR2_PR3_PR4_PR5_PR6_PR7_PR8_PR9_2026-02-16

## Purpose
Establish the frontend scaffold baseline using backend-frozen facade contracts for the first nine read vertical slices.

## Linked Backend Contracts (Authoritative)
1. Runs vertical slice (PR-1):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/activity/runs`

2. Incidents vertical slice (PR-2):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/incidents/list`

3. Policies vertical slice (PR-3):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/policies/list`

4. Controls vertical slice (PR-4):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/controls/list`

5. Logs replay-feed vertical slice (PR-5):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/logs/list`

6. Overview highlights vertical slice (PR-6):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/overview/highlights`

7. Analytics usage vertical slice (PR-7):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/analytics/statistics/usage`

8. Integrations list vertical slice (PR-8):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/integrations/list`

9. API keys list vertical slice (PR-9):
- Contract: `backend/app/hoc/docs/architecture/usecases/PR9_API_KEYS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Endpoint: `GET /hoc/api/cus/api_keys/list`

## Frontend Scaffold Rules (Immediate)
- Build one typed API client module and bind these read endpoints first.
- Enforce runtime parsing at API boundary (contract mismatch visible in UI).
- Use server-side pagination for list endpoints from contract fields.
- Show request-id/correlation-id aware error states.
- Do not implement mutations until read slices are stable.

## Slice-by-Slice Build Sequence
1. `/overview` highlights shell from `/overview/highlights`.
2. `/runs` page (read-only, server pagination).
3. `/incidents` page (read-only, topic list via `/list?topic=...`).
4. `/policies` page (read-only, topic list via `/list?topic=...`).
5. `/controls` page (read-only, topic list via `/list?topic=...`).
6. `/replay` page backed by `/logs/list?topic=...` + run-specific drilldown.
7. `/analytics` usage widgets backed by `/analytics/statistics/usage`.
8. `/integrations` list page backed by `/integrations/list`.
9. `/api-keys` list page backed by `/api_keys/list`.

## Notes
- Frontend strategy docs live under `docs/architecture/frontend/`.
- Backend contracts stay under `backend/app/hoc/docs/architecture/usecases/` and are consumed via links, not duplicated.
