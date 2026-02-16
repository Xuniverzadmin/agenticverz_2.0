# PR0_FRONTEND_ENDPOINT_COMPAT_MATRIX_2026-02-16

## Status
- Date: 2026-02-16
- Purpose: classify current frontend endpoint usage against live HOC exposure.
- Scope: compatibility planning for PR-1 and PR-2.

## Data Sources
- Frontend endpoint references:
  - `website/app-shell/src/api/*`
  - `website/app-shell/src/pages/*`
  - `website/app-shell/src/features/*`
- Live HOC routers and facades:
  - `backend/app/hoc/api/facades/cus/*`
  - `backend/app/hoc/api/cus/*`
- Legacy prefix behavior:
  - `backend/app/hoc/api/int/general/legacy_routes.py`

## Snapshot Metrics
- `/api/v1/` references in current frontend source: `191`
- Direct `fetch(...)` calls in current frontend source: `19`
- `apiClient.<method>(...)` calls in current frontend source: `209`

## Classification Rules
- `CANONICAL`: live HOC route exists with stable non-legacy path and clear migration target.
- `LEGACY`: frontend points to version-prefixed or deprecated path not accepted as target for new work.
- `UNKNOWN`: endpoint shape appears custom/older and needs explicit backend confirmation before migration.

## Endpoint Group Matrix

| Frontend Endpoint Pattern | Current Use | Live HOC Status | Class | Migration Target | Notes |
|---|---|---|---|---|---|
| `/api/v1/runtime/activity/runs*` | `RunsListPage`, `RunDetailPage` | No matching `/runtime/activity/*` in live HOC CUS surface | LEGACY | `/activity/live`, `/activity/completed`, `/activity/signals`, `/activity/runs/{run_id}` | Current page path is drifted from live routes |
| `/api/v1/activity/runs*` | `src/api/activity.ts` | Live path exists as `/activity/runs*` but marked deprecated in docs/comments | LEGACY | Prefer topic-scoped `/activity/live` + `/activity/completed`; detail `/activity/runs/{run_id}` | Keep only as temporary bridge if needed |
| `/api/v1/incidents*` | `src/api/incidents.ts` | Live domain exists under `/incidents*` | LEGACY | `/incidents/*` (non-versioned) | Needs full parameter parity validation |
| `/api/v1/runtime/overview/*` | `src/api/overview.ts` | Live overview exists under `/overview/*` | LEGACY | `/overview/highlights`, `/overview/decisions`, `/overview/costs` | Frontend currently targets old runtime projection path |
| `/api/v1/runtime/traces*` + `/api/v1/traces*` | `src/api/runtime.ts`, `src/api/traces.ts` | Live traces exposed via `/runtime/traces*` and `/traces*` depending surface | LEGACY | `/runtime/traces*` or `/traces*` (to be frozen in PR-1+) | Some frontend endpoints (`/summary`, `by-incident`) lack clear live counterpart |
| `/api/v1/analytics/statistics/*` | analytics pages | Live analytics is split across `/analytics`, `/cost`, `/predictions`, `/feedback`, etc. | UNKNOWN | TBD in feature-pack planning | Requires endpoint-by-endpoint contract mapping |
| `/api/v1/policy-proposals*` | `src/api/proposals.ts` | Live policies domain includes `/policy-proposals` (non-versioned) | LEGACY | `/policy-proposals*` | Needs response schema parity check |
| `/api/v1/session/context` | `src/api/session.ts` | Session context exists under integrations session surface (`/session/*`) | UNKNOWN | TBD | Path-level parity not yet confirmed |
| `/api/v1/founder/*`, `/api/v1/explorer/*` | founder tooling | Founder surface is present under FDR/OPS routers | LEGACY | `/fdr/*`, `/ops/*`, `/explorer/*` (exact mapping TBD) | Needs founder route matrix |
| `/api/v1/auth/*`, `/api/v1/tenants*`, `/api/v1/users/me` | auth client | Auth stack exists but path contracts need explicit freeze | UNKNOWN | TBD (outside PR-1 runs scope) | Must be planned as dedicated auth slice |
| `/api/v1/workers*`, `/api/v1/sba*`, `/api/v1/recovery*`, `/api/v1/failures*` | worker/sba/recovery tooling | Mixed legacy/internal feature areas; not primary CUS runs slice | UNKNOWN | TBD | Not in PR-1 scope |

## Immediate Priority for PR-1
1. Freeze Runs canonical facade contract first (read-only).
2. Remove frontend dependency on `/api/v1/runtime/activity/runs*`.
3. Define explicit query model for live/completed/signals topic selection with server pagination.

## Risks
- Hidden dependency on versioned paths that will return legacy/410 behavior.
- Incomplete parity for historic analytics/traces helper endpoints.
- Non-centralized direct `fetch` usage bypassing typed boundary constraints.

## PR-0 Output Requirement
This matrix is the baseline input for:
- `PR1_RUNS_FACADE_HARDENING_PLAN_2026-02-16.md`
- `PR1_RUNS_FACADE_VERIFICATION_2026-02-16.md`
