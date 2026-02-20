# PR10_ACCOUNT_USERS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-10 contract lock for Account Users List Facade implementation
- Applies to: backend facade endpoint only (no frontend implementation)
- Version: v1.0-draft

## Source-of-Truth Hierarchy (Authoritative Precedence)
1. Governance + topology lock docs
2. L4 hoc_spine constitutional/contracts literature
3. Domain literature for account
4. Runtime wiring + code reality
5. This PR addendum (frozen PR-10 contract)
6. Acceptance tests as executable proof

Conflict resolution rule:
- If runtime behavior conflicts with governance/L4/domain contracts, treat runtime behavior as drift and align implementation to governance-first authority.

## 0. Facade Artifact and Dispatch Map
- Facade router module:
  - `backend/app/hoc/api/cus/account/account_public.py`
- Router registration:
  - `backend/app/hoc/api/facades/cus/account/account_fac.py`
  - included through `backend/app/hoc/api/facades/cus/__init__.py` and `backend/app/hoc/app.py`
- Facade endpoint:
  - `GET /cus/account/users/list`
  - Gateway exposure: `GET /hoc/api/cus/account/users/list`
- Dispatch mapping (exactly one registry call per request):
  - `registry.execute("account.query", method="list_users", role, status, limit, offset)`
- Facade does not proxy HTTP-to-HTTP and does not call L6 drivers directly.

## 1. Scope
- PR-10 is read-only.
- Endpoint provides tenant user list summary only.
- Mutations are out of scope.

## 2. Route Contract
- Backend canonical route: `GET /cus/account/users/list`.
- Gateway path: `GET /hoc/api/cus/account/users/list`.
- Exactly one backend route resolves; no duplicate/double-prefix alias.

## 3. Query Contract
Allowed params (strict allowlist):
- `role` (optional enum: `owner | admin | member | viewer`)
- `status` (optional enum: `active | invited | suspended`)
- `limit` (optional integer, default `50`, bounds `1..100`)
- `offset` (optional integer, default `0`, bounds `0..2147483647`)

Validation rules:
- Unknown params rejected with `400 INVALID_QUERY`.
- Repeated single-valued params rejected with `400 INVALID_QUERY`.

`as_of`:
- Unsupported in PR-10.
- Any `as_of` usage -> `400 UNSUPPORTED_PARAM`.

## 4. Layering and Execution
- Facade responsibility: boundary validation + translation + one dispatch.
- Exactly one `account.query` registry call per request.
- No facade orchestration/composition.
- No direct database access from facade.

## 5. Determinism Contract
- Facade preserves backend list ordering and does not re-order users.
- L6 list ordering is hardened to stable sort key:
  - `email asc, id asc`.
- Repeated calls with same backend payload preserve response ordering.

## 6. Success Response Contract
Required fields:
- `users`
- `total`
- `has_more`
- `pagination`
- `generated_at`
- `meta`

`pagination` fields:
- `limit`
- `offset`
- `next_offset`

`meta` fields:
- `request_id` = middleware request id (same as response header `X-Request-ID`)
- `correlation_id` = inbound `X-Correlation-ID` if present, else `null`
- `as_of` = `null` in PR-10

`generated_at`:
- UTC RFC3339 with `Z` suffix.
- In PR-10 this timestamp is generated at facade boundary.

## 7. Error Contract
- Error style remains `HTTPException(detail={...})`.
- Standardized detail keys:
  - `code`
  - `message`
  - `field_errors` (optional)

Error codes:
- `INVALID_QUERY`: unknown params, malformed/invalid values, bounds violations
- `UNSUPPORTED_PARAM`: known but unsupported parameter (`as_of`)
- `OPERATION_FAILED`: registry operation failure
- `CONTRACT_MISMATCH`: facade could not validate backend payload

## 8. Acceptance Matrix
| Area | Test | Expected |
|---|---|---|
| Route | Route registered once | `/cus/account/users/list` exists once; no duplicate alias |
| Query | Unknown query param | `400 INVALID_QUERY` |
| Query | Invalid `role` | `400 INVALID_QUERY` |
| Query | Invalid `status` | `400 INVALID_QUERY` |
| Query | Invalid `limit`/`offset` bounds | `400 INVALID_QUERY` |
| As-of | `as_of` supplied | `400 UNSUPPORTED_PARAM` |
| Dispatch | List request | one `account.query` call with `method=list_users` |
| Pagination | Page math | `has_more` and `next_offset` derived from `total` and returned count |
| Determinism | Same request repeated | stable backend ordering retained |
| Tracing | `X-Request-ID` vs `meta.request_id` | Exact match |
| Tracing | `X-Correlation-ID` inbound | echoed in `meta.correlation_id` |
| Contract | Backend enum drift | `500 CONTRACT_MISMATCH` |
