# PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-1 contract lock for Runs Facade implementation
- Applies to: backend facade endpoint only (no frontend implementation)

## 0. Facade Artifact and Dispatch Map
- PR-1 introduces facade router module:
  - `backend/app/hoc/api/cus/activity/runs_facade.py`
- Router registration:
  - `backend/app/hoc/api/facades/cus/activity.py`
- Facade endpoint:
  - `GET /cus/activity/runs`
  - Gateway exposure: `/hoc/api/cus/activity/runs`
- Dispatch mapping (exactly one registry call per request):
  - `topic=live` -> `registry.execute("activity.query", method="get_live_runs", ...)`
  - `topic=completed` -> `registry.execute("activity.query", method="get_completed_runs", ...)`
- Facade does not proxy HTTP-to-HTTP and does not call L6 drivers directly.

## 1. Scope
- PR-1 is read-only.
- Supported topics: `live`, `completed`.
- `signals` topic is explicitly out of scope for PR-1.

## 2. Route Contract
- Backend canonical route: `GET /cus/activity/runs`.
- Gateway path: `GET /hoc/api/cus/activity/runs`.
- Exactly one route resolves in backend routing; no duplicate/double-prefix alias is allowed.

## 3. Query Contract
- Required:
  - `topic` enum: `live | completed`
- Pagination:
  - `limit` default `50`
  - `limit` min `1`, max `200`
  - `limit` out of range -> `400 INVALID_QUERY`
  - `offset` min `0`
  - `offset` out of range -> `400 INVALID_QUERY`
- Arrays:
  - Repeated query params only, example `risk_level=A&risk_level=B`
  - Duplicate repeated values are deduplicated before dispatch
- Datetime filters:
  - RFC3339/ISO8601 with timezone required
  - Naive datetime (without timezone) -> `400 INVALID_QUERY`
  - `completed_after <= completed_before` required
  - Bounds are inclusive: `>= completed_after` and `<= completed_before`
- `as_of`:
  - Unsupported in PR-1
  - Any `as_of` usage -> `400 UNSUPPORTED_PARAM`

## 4. Allowed Filters by Topic
- `topic=live`:
  - `project_id: str`
  - `risk_level: List[RiskLevel]`
  - `evidence_health: List[EvidenceHealth]`
  - `source: List[RunSource]`
  - `provider_type: List[ProviderType]`
  - `limit: int`
  - `offset: int`
- `topic=completed`:
  - `project_id: str`
  - `status: List[RunStatus]`
  - `risk_level: List[RiskLevel]`
  - `completed_after: datetime(tz)`
  - `completed_before: datetime(tz)`
  - `limit: int`
  - `offset: int`
- Any unknown query parameter -> `400 INVALID_QUERY`.

## 5. Layering and Execution
- Facade responsibility: boundary validation + translation + one dispatch.
- Exactly one `activity.query` registry call per request.
- No facade orchestration/composition.
- No direct database access from facade.

## 6. Determinism Contract
- `topic=live` ordering:
  - `started_at DESC NULLS LAST, run_id DESC`
- `topic=completed` ordering:
  - `completed_at DESC NULLS LAST, run_id DESC`
- No caller-controlled primary sort in PR-1.
- Response order must match backend query order exactly (no application-layer resorting).
- `run_id` must be non-null and unique for tie-break determinism.

## 7. Pagination and Total Semantics
- Total is exact integer.
- Total count and page data use the same constraints in this order:
  1. tenant scope
  2. topic scope
  3. allowed filters
  4. pagination
- `has_more = (offset + len(runs) < total)`
- `next_offset = offset + len(runs)` when `has_more=true`, else `null`

## 8. Success Response Contract
Required fields:
- `topic`
- `runs`
- `total`
- `has_more`
- `pagination`
- `generated_at`
- `meta`

`meta` fields:
- `request_id` = middleware request id (same as response header `X-Request-ID`)
- `correlation_id` = inbound `X-Correlation-ID` if present, else `null`
- `as_of` = `null` in PR-1

`generated_at`:
- UTC RFC3339 format with `Z` suffix.

## 9. Error Contract
- Error style remains `HTTPException(detail={...})` to match existing activity API style.
- Standardized `detail` keys for this facade:
  - `code`
  - `message`
  - `field_errors` (optional)

Error code table:
- `INVALID_QUERY`: unknown params, invalid values/types/ranges
- `UNSUPPORTED_PARAM`: known but unsupported parameter in PR-1 (`as_of`)

## 10. Acceptance Matrix
| Area | Test | Expected |
|---|---|---|
| Route | Route registered once | `/cus/activity/runs` exists once; no duplicate alias |
| Topic | Missing topic | `400 INVALID_QUERY` |
| Topic | Invalid topic | `400 INVALID_QUERY` |
| Unknown params | Add undocumented query key | `400 INVALID_QUERY` |
| As-of | `as_of` supplied | `400 UNSUPPORTED_PARAM` |
| Pagination | `limit=0` or `limit>200` | `400 INVALID_QUERY` |
| Pagination | `offset<0` | `400 INVALID_QUERY` |
| Date range | `completed_after > completed_before` | `400 INVALID_QUERY` |
| Determinism | Same request repeated | Stable ordering retained |
| Tracing | `X-Request-ID` vs `meta.request_id` | Exact match |
| Tracing | `X-Correlation-ID` inbound | echoed in `meta.correlation_id` |
