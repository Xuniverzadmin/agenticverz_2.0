# PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-3 contract lock for Policies List Facade implementation
- Applies to: backend facade endpoint only (no frontend implementation)
- Version: v1.0-draft

## Source-of-Truth Hierarchy (Authoritative Precedence)
1. Governance + topology lock docs
2. L4 hoc_spine constitutional/contracts literature
3. Domain literature for policies
4. Runtime wiring + code reality
5. This PR addendum (frozen PR-3 contract)
6. Acceptance tests as executable proof

Conflict resolution rule:
- If runtime behavior conflicts with governance/L4/domain contracts, treat runtime behavior as drift and align implementation to governance-first authority.

## 0. Facade Artifact and Dispatch Map
- Facade router module:
  - `backend/app/hoc/api/cus/policies/policies_public.py`
- Router registration:
  - `backend/app/hoc/api/facades/cus/policies/policies_fac.py`
  - included through `backend/app/hoc/api/facades/cus/__init__.py` and `backend/app/hoc/app.py`
- Facade endpoint:
  - `GET /cus/policies/list`
  - Gateway exposure: `GET /hoc/api/cus/policies/list`
- Dispatch mapping (exactly one registry call per request):
  - `topic=active` -> `registry.execute("policies.query", method="list_policy_rules", status="ACTIVE", ...)`
  - `topic=retired` -> `registry.execute("policies.query", method="list_policy_rules", status="RETIRED", ...)`
- Facade does not proxy HTTP-to-HTTP and does not call L6 drivers directly.

## 1. Scope
- PR-3 is read-only.
- Supported topics: `active`, `retired`.
- Mutations are out of scope.

## 2. Route Contract
- Backend canonical route: `GET /cus/policies/list`.
- Gateway path: `GET /hoc/api/cus/policies/list`.
- Exactly one backend route resolves; no duplicate/double-prefix alias.

## 3. Query Contract
- Required:
  - `topic` enum: `active | retired`
- Pagination:
  - `limit` default `20`
  - `limit` min `1`, max `100`
  - `offset` min `0`
  - out-of-range values -> `400 INVALID_QUERY`
- `as_of`:
  - Unsupported in PR-3
  - any `as_of` usage -> `400 UNSUPPORTED_PARAM`
- Datetime filters:
  - RFC3339/ISO8601 with timezone required
  - naive datetime -> `400 INVALID_QUERY`
  - `created_after <= created_before`
- Unknown query params:
  - rejected with `400 INVALID_QUERY`

## 4. Allowed Filters by Topic
- `topic=active`:
  - `enforcement_mode: BLOCK | WARN | AUDIT | DISABLED`
  - `scope: GLOBAL | TENANT | PROJECT | AGENT`
  - `source: MANUAL | SYSTEM | LEARNED`
  - `rule_type: SYSTEM | SAFETY | ETHICAL | TEMPORAL`
  - `created_after: datetime(tz)`
  - `created_before: datetime(tz)`
  - `limit`, `offset`
- `topic=retired`:
  - `enforcement_mode: BLOCK | WARN | AUDIT | DISABLED`
  - `scope: GLOBAL | TENANT | PROJECT | AGENT`
  - `source: MANUAL | SYSTEM | LEARNED`
  - `rule_type: SYSTEM | SAFETY | ETHICAL | TEMPORAL`
  - `created_after: datetime(tz)`
  - `created_before: datetime(tz)`
  - `limit`, `offset`

## 5. Layering and Execution
- Facade responsibility: boundary validation + translation + one dispatch.
- Exactly one `policies.query` registry call per request.
- No facade orchestration/composition.
- No direct database access from facade.

## 6. Determinism Contract
- No caller-controlled sort in PR-3.
- Upstream canonical ordering for rules query (L6):
  - `last_triggered_at desc nulls last`
  - `created_at desc`
  - `rule_id desc` (stable tie-break)
- Response order must match backend query order exactly.

## 7. Pagination and Total Semantics
- Total is exact integer from backend operation result.
- Facade computes:
  - `has_more = (offset + len(rules) < total)`
  - `next_offset = offset + len(rules)` when `has_more=true`, else `null`

## 8. Success Response Contract
Required fields:
- `topic`
- `rules`
- `total`
- `has_more`
- `pagination`
- `generated_at`
- `meta`

`meta` fields:
- `request_id` = middleware request id (same as response header `X-Request-ID`)
- `correlation_id` = inbound `X-Correlation-ID` if present, else `null`
- `as_of` = `null` in PR-3

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
| Route | Route registered once | `/cus/policies/list` exists once; no duplicate alias |
| Topic | Missing topic | `400 INVALID_QUERY` |
| Topic | Invalid topic | `400 INVALID_QUERY` |
| Unknown params | Add undocumented query key | `400 INVALID_QUERY` |
| As-of | `as_of` supplied | `400 UNSUPPORTED_PARAM` |
| Pagination | `limit=0` or `limit>100` | `400 INVALID_QUERY` |
| Pagination | `offset<0` | `400 INVALID_QUERY` |
| Date range | invalid date window | `400 INVALID_QUERY` |
| Determinism | Same request repeated | Stable ordering retained |
| Tracing | `X-Request-ID` vs `meta.request_id` | Exact match |
| Tracing | `X-Correlation-ID` inbound | echoed in `meta.correlation_id` |
