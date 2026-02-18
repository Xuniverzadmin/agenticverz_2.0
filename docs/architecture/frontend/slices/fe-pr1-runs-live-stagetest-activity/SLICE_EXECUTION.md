# FE-PR1-RUNS-LIVE-STAGETEST Frontend Slice Execution

## Metadata
- Slice ID: FE-PR1-RUNS-LIVE-STAGETEST
- Domain: activity
- Route: `/page/activity/runs-live`
- Backend Endpoint: `/hoc/api/cus/activity/runs`
- Backend Contract: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- Owner: Codex
- Date: 2026-02-18

## Objective
- Implement a contract-respecting frontend vertical slice for `activity`.
- Keep scope small and reviewable.

## Scope
- In scope:
- `/page/activity/runs-live` scaffold route and domain/subpage mapping.
- Facade probe wiring to `/hoc/api/cus/activity/runs?topic=live&limit=50&offset=0`.
- Contract metadata display for PR1 addendum.
- Out of scope:
- Non-scaffold production UX for runs list/detail.
- Auth/session acquisition flows.
- `topic=completed` and other PR slices.

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
| Route binding | `topic` | enum (`live`) | Hard-coded in scaffold catalog query defaults. |
| Probe request | `limit`, `offset` | int | Default `50/0` from catalog for deterministic scaffold requests. |
| Probe header | `X-HOC-Scaffold-Fixture` | string | `pr1-runs-live-v1` enables temporary preflight fixture payload. |
| Response preview | `runs` | array | Raw JSON preview shown without client-side resort/mutation. |
| Response preview | `meta.request_id` | string | Expected from backend contract; visible in JSON preview when authenticated data is available. |
| Fallback warning | content-type / HTML check | bool | If HTML body detected, render gateway proxy warning. |

## API Boundary Plan
- Typed API method: `buildRequestPath(slice)` + `fetch(requestPath, { credentials: 'include' })`.
- Runtime schema: probe captures `{ status, contentType, isJson, bodyPreview }`.
- Request/correlation ID propagation: browser request carries session cookies; backend `X-Request-ID` is validated via response headers.
- Contract mismatch handling: non-JSON or HTML fallback is surfaced as explicit warning on page.
- Fixture gating: header-gated PR1 live fixture is used for scaffold validation in preflight.

## Determinism
- Backend ordering clause: `started_at DESC NULLS LAST, run_id DESC` per `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`.
- Client-side ordering behavior: no client resorting; payload order is rendered as returned.
- Pagination behavior: request defaults `limit=50`, `offset=0`; pagination UI deferred to later iteration.

## Test Plan
- Contract parse test: `pytest tests/api/test_runs_facade_pr1.py -q`.
- Page render tests (loading/empty/error/contract mismatch): manual probe on `/page/activity/runs-live` with endpoint status + fallback detection.
- Stage and preflight checks: `npm run build` in `website/app-shell`; live curl checks against stagetest URL and facade path.
