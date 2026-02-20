# PR6_OVERVIEW_HIGHLIGHTS_FACADE_CONTRACT_ADDENDUM_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-6 contract lock for Overview Highlights Facade implementation
- Applies to: backend facade endpoint only (no frontend implementation)
- Version: v1.0-draft

## Source-of-Truth Hierarchy (Authoritative Precedence)
1. Governance + topology lock docs
2. L4 hoc_spine constitutional/contracts literature
3. Domain literature for overview
4. Runtime wiring + code reality
5. This PR addendum (frozen PR-6 contract)
6. Acceptance tests as executable proof

Conflict resolution rule:
- If runtime behavior conflicts with governance/L4/domain contracts, treat runtime behavior as drift and align implementation to governance-first authority.

## 0. Facade Artifact and Dispatch Map
- Facade router module:
  - `backend/app/hoc/api/cus/overview/overview_public.py`
- Router registration:
  - `backend/app/hoc/api/facades/cus/overview/overview_fac.py`
  - included through `backend/app/hoc/api/facades/cus/__init__.py` and `backend/app/hoc/app.py`
- Facade endpoint:
  - `GET /cus/overview/highlights`
  - Gateway exposure: `GET /hoc/api/cus/overview/highlights`
- Dispatch mapping (exactly one registry call per request):
  - `registry.execute("overview.query", method="get_highlights")`
- Facade does not proxy HTTP-to-HTTP and does not call L6 drivers directly.

## 1. Scope
- PR-6 is read-only.
- Endpoint provides overview highlights summary only.
- Mutations are out of scope.

## 2. Route Contract
- Backend canonical route: `GET /cus/overview/highlights`.
- Gateway path: `GET /hoc/api/cus/overview/highlights`.
- Exactly one backend route resolves; no duplicate/double-prefix alias.

## 3. Query Contract
- No query parameters are supported in PR-6.
- `as_of`:
  - Unsupported in PR-6
  - any `as_of` usage -> `400 UNSUPPORTED_PARAM`
- Unknown query params:
  - rejected with `400 INVALID_QUERY`

## 4. Layering and Execution
- Facade responsibility: boundary validation + translation + one dispatch.
- Exactly one `overview.query` registry call per request.
- No facade orchestration/composition.
- No direct database access from facade.

## 5. Determinism Contract
- Highlights payload ordering is preserved from `overview.query` result.
- Facade does not re-order `domain_counts`.
- Repeated calls with same backend payload preserve response ordering.

## 6. Success Response Contract
Required fields:
- `highlights`
- `generated_at`
- `meta`

`highlights` fields:
- `pulse`
- `domain_counts`
- `last_activity_at`

`meta` fields:
- `request_id` = middleware request id (same as response header `X-Request-ID`)
- `correlation_id` = inbound `X-Correlation-ID` if present, else `null`
- `as_of` = `null` in PR-6

`generated_at`:
- UTC RFC3339 with `Z` suffix.
- In PR-6 this timestamp is generated at facade boundary.

## 7. Error Contract
- Error style remains `HTTPException(detail={...})`.
- Standardized detail keys:
  - `code`
  - `message`
  - `field_errors` (optional)

Error codes:
- `INVALID_QUERY`: unknown query params
- `UNSUPPORTED_PARAM`: known but unsupported parameter (`as_of`)

## 8. Acceptance Matrix
| Area | Test | Expected |
|---|---|---|
| Route | Route registered once | `/cus/overview/highlights` exists once; no duplicate alias |
| Query | Unknown query param | `400 INVALID_QUERY` |
| As-of | `as_of` supplied | `400 UNSUPPORTED_PARAM` |
| Dispatch | Highlights request | one `overview.query` call with `method=get_highlights` |
| Determinism | Same request repeated | stable `domain_counts` ordering retained |
| Tracing | `X-Request-ID` vs `meta.request_id` | Exact match |
| Tracing | `X-Correlation-ID` inbound | echoed in `meta.correlation_id` |
