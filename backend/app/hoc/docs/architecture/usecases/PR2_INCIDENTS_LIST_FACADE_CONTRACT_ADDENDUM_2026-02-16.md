# PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-2 contract lock for Incidents List Facade implementation
- Applies to: backend facade endpoint only (no frontend implementation)
- Version: v1.0-draft

## Source-of-Truth Hierarchy (Authoritative Precedence)
1. Governance + topology lock docs
2. L4 hoc_spine constitutional/contracts literature
3. Domain literature for incidents
4. Runtime wiring + code reality
5. This PR addendum (frozen PR-2 contract)
6. Acceptance tests as executable proof

Conflict resolution rule:
- If runtime behavior conflicts with governance/L4/domain contracts, treat runtime behavior as drift and align implementation to governance-first authority.

## 0. Facade Artifact and Dispatch Map
- Facade router module:
  - `backend/app/hoc/api/cus/incidents/incidents_public.py`
- Router registration:
  - `backend/app/hoc/api/facades/cus/incidents/incidents_fac.py`
  - included through `backend/app/hoc/api/facades/cus/__init__.py` and `backend/app/hoc/app.py`
- Facade endpoint:
  - `GET /cus/incidents/list`
  - Gateway exposure: `GET /hoc/api/cus/incidents/list`
- Dispatch mapping (exactly one registry call per request):
  - `topic=active` -> `registry.execute("incidents.query", method="list_active_incidents", ...)`
  - `topic=resolved` -> `registry.execute("incidents.query", method="list_resolved_incidents", ...)`
  - `topic=historical` -> `registry.execute("incidents.query", method="list_historical_incidents", ...)`
- Facade does not proxy HTTP-to-HTTP and does not call L6 drivers directly.

## 1. Scope
- PR-2 is read-only.
- Supported topics: `active`, `resolved`, `historical`.
- Mutations are out of scope.

## 2. Route Contract
- Backend canonical route: `GET /cus/incidents/list`.
- Gateway path: `GET /hoc/api/cus/incidents/list`.
- Exactly one backend route resolves; no duplicate/double-prefix alias.

## 3. Query Contract
- Required:
  - `topic` enum: `active | resolved | historical`
- Pagination:
  - `limit` default `20`
  - `limit` min `1`, max `100`
  - `offset` min `0`
  - out-of-range values -> `400 INVALID_QUERY`
- `as_of`:
  - Unsupported in PR-2
  - any `as_of` usage -> `400 UNSUPPORTED_PARAM`
- Datetime filters:
  - RFC3339/ISO8601 with timezone required
  - naive datetime -> `400 INVALID_QUERY`
  - `created_after <= created_before`
  - `resolved_after <= resolved_before`
- Unknown query params:
  - rejected with `400 INVALID_QUERY`

## 4. Allowed Filters by Topic
- `topic=active`:
  - `severity: Severity`
  - `category: str`
  - `cause_type: CauseType`
  - `is_synthetic: bool`
  - `created_after: datetime(tz)`
  - `created_before: datetime(tz)`
  - `limit`, `offset`
- `topic=resolved`:
  - `severity: Severity`
  - `category: str`
  - `cause_type: CauseType`
  - `is_synthetic: bool`
  - `resolved_after: datetime(tz)`
  - `resolved_before: datetime(tz)`
  - `limit`, `offset`
- `topic=historical`:
  - `retention_days: int` (min `7`, max `365`, default `30`)
  - `severity: Severity`
  - `category: str`
  - `cause_type: CauseType`
  - `limit`, `offset`

## 5. Layering and Execution
- Facade responsibility: boundary validation + translation + one dispatch.
- Exactly one `incidents.query` registry call per request.
- No facade orchestration/composition.
- No direct database access from facade.

## 6. Determinism Contract
- `topic=active` ordering params fixed to `created_at desc`.
- `topic=resolved` and `topic=historical` ordering params fixed to `resolved_at desc`.
- No caller-controlled sort in PR-2.
- Response order must match backend query order exactly.

## 7. Pagination and Total Semantics
- Total is exact integer from backend operation result.
- Facade computes:
  - `has_more = (offset + len(incidents) < total)`
  - `next_offset = offset + len(incidents)` when `has_more=true`, else `null`

## 8. Success Response Contract
Required fields:
- `topic`
- `incidents`
- `total`
- `has_more`
- `pagination`
- `generated_at`
- `meta`

`meta` fields:
- `request_id` = middleware request id (same as response header `X-Request-ID`)
- `correlation_id` = inbound `X-Correlation-ID` if present, else `null`
- `as_of` = `null` in PR-2

`generated_at`:
- UTC RFC3339 with `Z` suffix.

## 9. Error Contract
- Error style remains `HTTPException(detail={...})`.
- Standardized detail keys:
  - `code`
  - `message`
  - `field_errors` (optional)

Error codes:
- `INVALID_QUERY`: unknown params, invalid values/types/ranges
- `UNSUPPORTED_PARAM`: known but unsupported parameter (`as_of`)

## 10. Acceptance Matrix
| Area | Test | Expected |
|---|---|---|
| Route | Route registered once | `/cus/incidents/list` exists once; no duplicate alias |
| Topic | Missing topic | `400 INVALID_QUERY` |
| Topic | Invalid topic | `400 INVALID_QUERY` |
| Unknown params | Add undocumented query key | `400 INVALID_QUERY` |
| As-of | `as_of` supplied | `400 UNSUPPORTED_PARAM` |
| Pagination | `limit=0` or `limit>100` | `400 INVALID_QUERY` |
| Pagination | `offset<0` | `400 INVALID_QUERY` |
| Historical | `retention_days` out of range | `400 INVALID_QUERY` |
| Date range | invalid date window | `400 INVALID_QUERY` |
| Determinism | Same request repeated | Stable ordering retained |
| Tracing | `X-Request-ID` vs `meta.request_id` | Exact match |
| Tracing | `X-Correlation-ID` inbound | echoed in `meta.correlation_id` |
