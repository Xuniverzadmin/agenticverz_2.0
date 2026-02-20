# PR7_ANALYTICS_USAGE_FACADE_CONTRACT_ADDENDUM_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-7 contract lock for Analytics Usage Facade implementation
- Applies to: backend facade endpoint only (no frontend implementation)
- Version: v1.0-draft

## Source-of-Truth Hierarchy (Authoritative Precedence)
1. Governance + topology lock docs
2. L4 hoc_spine constitutional/contracts literature
3. Domain literature for analytics
4. Runtime wiring + code reality
5. This PR addendum (frozen PR-7 contract)
6. Acceptance tests as executable proof

Conflict resolution rule:
- If runtime behavior conflicts with governance/L4/domain contracts, treat runtime behavior as drift and align implementation to governance-first authority.

## 0. Facade Artifact and Dispatch Map
- Facade router module:
  - `backend/app/hoc/api/cus/analytics/analytics_public.py`
- Router registration:
  - `backend/app/hoc/api/facades/cus/analytics/analytics_fac.py`
  - included through `backend/app/hoc/api/facades/cus/__init__.py` and `backend/app/hoc/app.py`
- Facade endpoint:
  - `GET /cus/analytics/statistics/usage`
  - Gateway exposure: `GET /hoc/api/cus/analytics/statistics/usage`
- Dispatch mapping (exactly one registry call per request):
  - `registry.execute("analytics.query", method="get_usage_statistics", from_ts, to_ts, resolution, scope)`
- Facade does not proxy HTTP-to-HTTP and does not call L6 drivers directly.

## 1. Scope
- PR-7 is read-only.
- Endpoint provides analytics usage statistics only.
- Mutations and exports are out of scope.

## 2. Route Contract
- Backend canonical route: `GET /cus/analytics/statistics/usage`.
- Gateway path: `GET /hoc/api/cus/analytics/statistics/usage`.
- Exactly one backend route resolves; no duplicate/double-prefix alias.

## 3. Query Contract
Allowed params (strict allowlist):
- `from` (required, RFC3339 with timezone)
- `to` (required, RFC3339 with timezone)
- `resolution` (optional enum: `hour | day`, default `day`)
- `scope` (optional enum: `org | project | env`, default `org`)

Validation rules:
- Unknown params rejected with `400 INVALID_QUERY`.
- Repeated single-valued params rejected with `400 INVALID_QUERY`.
- `from` must be strictly before `to`.
- Maximum window size is 90 days.

`as_of`:
- Unsupported in PR-7.
- Any `as_of` usage -> `400 UNSUPPORTED_PARAM`.

## 4. Layering and Execution
- Facade responsibility: boundary validation + translation + one dispatch.
- Exactly one `analytics.query` registry call per request.
- No facade orchestration/composition.
- No direct database access from facade.

## 5. Determinism Contract
- Usage `series` ordering is preserved from `analytics.query` result.
- Facade does not re-order `series`.
- Repeated calls with same backend payload preserve response ordering.

## 6. Success Response Contract
Required fields:
- `window`
- `totals`
- `series`
- `signals`
- `generated_at`
- `meta`

`window` fields:
- `from_ts`
- `to_ts`
- `resolution`

`meta` fields:
- `request_id` = middleware request id (same as response header `X-Request-ID`)
- `correlation_id` = inbound `X-Correlation-ID` if present, else `null`
- `as_of` = `null` in PR-7

`generated_at`:
- UTC RFC3339 with `Z` suffix.
- In PR-7 this timestamp is generated at facade boundary.

## 7. Error Contract
- Error style remains `HTTPException(detail={...})`.
- Standardized detail keys:
  - `code`
  - `message`
  - `field_errors` (optional)

Error codes:
- `INVALID_QUERY`: unknown params, malformed/invalid values, date-window violations
- `UNSUPPORTED_PARAM`: known but unsupported parameter (`as_of`)
- `OPERATION_FAILED`: registry operation failure
- `CONTRACT_MISMATCH`: facade could not validate backend payload

## 8. Acceptance Matrix
| Area | Test | Expected |
|---|---|---|
| Route | Route registered once | `/cus/analytics/statistics/usage` exists once; no duplicate alias |
| Query | Unknown query param | `400 INVALID_QUERY` |
| Query | Missing/invalid `from`/`to` | `400 INVALID_QUERY` |
| Query | Invalid enum (`resolution`/`scope`) | `400 INVALID_QUERY` |
| Query | Invalid window (`from >= to` or >90 days) | `400 INVALID_QUERY` |
| As-of | `as_of` supplied | `400 UNSUPPORTED_PARAM` |
| Dispatch | Usage request | one `analytics.query` call with `method=get_usage_statistics` |
| Determinism | Same request repeated | stable `series` ordering retained |
| Tracing | `X-Request-ID` vs `meta.request_id` | Exact match |
| Tracing | `X-Correlation-ID` inbound | echoed in `meta.correlation_id` |
