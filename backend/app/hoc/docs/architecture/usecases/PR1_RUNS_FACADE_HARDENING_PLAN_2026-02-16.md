# PR1_RUNS_FACADE_HARDENING_PLAN_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-1 backend hardening plan (no frontend implementation)
- Feature pack: Runs (read-only)

## Objective
Create the first hardened CUS facade entry for Runs so frontend can consume a stable, domain-grouped HTTP surface without relying on legacy `/api/v1/*` endpoints.

## Problem Statement
Current frontend runs views depend on `/api/v1/runtime/activity/runs*`, while live HOC customer activity APIs are non-versioned and topic-scoped (`/activity/live`, `/activity/completed`, `/activity/signals`) with `/activity/runs` marked deprecated.

## PR-1 Target Contract (Proposed)

### External Facade Surface (CUS)
- `GET /cus/activity/runs`

### Query Contract
- `topic`: `live | completed | signals` (default: `live`)
- `limit`: integer (server-side pagination)
- `offset`: integer
- `as_of`: optional deterministic read watermark
- Additional topic-specific filters passed through allowlist.

### Response Contract
- Envelope includes:
  - `items` (or `signals` for signals topic)
  - pagination: `limit`, `offset`, `next_offset`
  - `total`
  - `has_more` where applicable
  - request correlation (`X-Request-ID` header and/or `meta.request_id`)

## Routing Strategy
1. Keep existing live HOC activity handlers unchanged for business logic.
2. Add façade-level dispatcher at CUS namespace that routes by `topic`:
- `topic=live` -> internal activity live query path
- `topic=completed` -> internal activity completed query path
- `topic=signals` -> internal activity signals query path
3. Keep deprecated `/activity/runs` as compatibility bridge only during migration window.

## Guardrails
- L2.1 must stay orchestration/aggregation only (no business logic).
- No new `/api/v1/*` endpoints.
- Preserve tenant isolation from auth context.
- Deterministic sorting for timeline/replay fields remains explicit (not timestamp-only).

## Implementation Delta (Minimal)
1. Add CUS facade router module for runs entry (single endpoint).
2. Register router in CUS facade wiring path.
3. Add contract tests for topic routing + pagination + request-id propagation.
4. Add legacy mapping note in docs (old endpoint -> new facade endpoint).

## Out of Scope
- Replay mutations and incident workflows.
- Frontend migration/cutover.
- Deletion of legacy routes in PR-1.

## Acceptance Criteria
1. `GET /cus/activity/runs` exists and is read-only.
2. Pagination is server-side and deterministic per topic query.
3. Legacy frontend runs path has documented migration target.
4. Verification checklist in PR-1 verification doc passes.
