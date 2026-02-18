# FE-PR1-RUNS-COMPLETED-STAGETEST Frontend Slice Execution

## Metadata
- Slice ID: FE-PR1-RUNS-COMPLETED-STAGETEST
- Domain: activity
- Route: `/page/activity/runs-completed`
- Backend Endpoint: `/hoc/api/cus/activity/runs`
- Backend Contract: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Owner: Codex
- Date: 2026-02-18

## Objective
- Implement a contract-respecting frontend vertical slice for completed activity runs.
- Keep scope limited to scaffold proof with deterministic fixture payload.

## Scope
- In scope:
- `/page/activity/runs-completed` scaffold route and domain/subpage mapping.
- Facade probe wiring to `/hoc/api/cus/activity/runs?topic=completed&limit=50&offset=0`.
- Header-gated fixture enablement: `X-HOC-Scaffold-Fixture: pr1-runs-completed-v1`.
- Contract metadata display and raw JSON probe rendering.
- Out of scope:
- Production UX for completed runs table/cards.
- Auth/session acquisition flows.
- Real runtime data dispatch for completed runs.

## Gate Checklist
- [x] G0 Contract Freeze
- [x] G1 UI Contract Spec
- [x] G2 API Boundary Implementation
- [x] G3 Page Vertical Slice (Hidden)
- [x] G4 Environment Validation
- [x] G5 Quality Gate
- [ ] G6 Surface Promotion

## UI Contract Mapping
| UI Element | Contract Param/Field | Type | Notes |
|---|---|---|---|
| Route binding | `topic` | enum (`completed`) | Hard-coded in scaffold catalog query defaults. |
| Probe request | `limit`, `offset` | int | Default `50/0` from catalog for deterministic scaffold requests. |
| Probe header | `X-HOC-Scaffold-Fixture` | string | `pr1-runs-completed-v1` enables temporary preflight fixture payload. |
| Response preview | `runs` | array | Raw JSON payload preview rendered without client-side mutation. |
| Response preview | `meta.request_id` | string | Back-end request id remains visible in payload/headers for traceability. |
| Fallback warning | content-type / HTML check | bool | HTML body is flagged as gateway-proxy regression signal. |

## API Boundary Plan
- Typed API method: `buildRequestPath(slice)` + `fetch(requestPath, { credentials: 'include', headers })`.
- Runtime schema: probe captures `{ status, contentType, isJson, bodyPreview }`.
- Request/correlation ID propagation: backend `X-Request-ID` preserved; correlation id passed through when provided.
- Contract mismatch handling: non-JSON or HTML response triggers explicit scaffold warning state.
- Fixture safety: only allowlisted fixture ids are accepted; topic/fixture mismatch fails `400 INVALID_QUERY`.

## Determinism
- Backend ordering clause: `completed_at DESC NULLS LAST, run_id DESC` per PR1 contract addendum.
- Client-side ordering behavior: no client re-sorting; payload ordering is rendered exactly as returned.
- Pagination behavior: initial probe uses `limit=50&offset=0`; backend returns contract pagination metadata.

## Test Plan
- Contract facade tests: `cd backend && PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py`.
- Probe route checks: `curl` stagetest route + facade probe with/without fixture header.
- Quality checks: `cd website/app-shell && npm run build`.
- Docpack gate: `check_frontend_slice_docpack.py` for completed slice folder.
