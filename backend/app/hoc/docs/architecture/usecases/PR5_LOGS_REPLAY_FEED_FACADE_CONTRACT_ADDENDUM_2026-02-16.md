# PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-5 contract lock for Logs Replay Feed Facade implementation
- Applies to: backend facade endpoint only (no frontend implementation)
- Version: v1.0-draft

## Source-of-Truth Hierarchy (Authoritative Precedence)
1. Governance + topology lock docs
2. L4 hoc_spine constitutional/contracts literature
3. Domain literature for logs
4. Runtime wiring + code reality
5. This PR addendum (frozen PR-5 contract)
6. Acceptance tests as executable proof

Conflict resolution rule:
- If runtime behavior conflicts with governance/L4/domain contracts, treat runtime behavior as drift and align implementation to governance-first authority.

## 0. Facade Artifact and Dispatch Map
- Facade router module:
  - `backend/app/hoc/api/cus/logs/logs_public.py`
- Router registration:
  - `backend/app/hoc/api/facades/cus/logs/logs_fac.py`
  - included through `backend/app/hoc/api/facades/cus/__init__.py` and `backend/app/hoc/app.py`
- Facade endpoint:
  - `GET /cus/logs/list`
  - Gateway exposure: `GET /hoc/api/cus/logs/list`
- Dispatch mapping (exactly one registry call per request):
  - `topic=llm_runs` -> `registry.execute("logs.query", method="list_llm_run_records", limit, offset)`
  - `topic=system_records` -> `registry.execute("logs.query", method="list_system_records", limit, offset)`
- Facade does not proxy HTTP-to-HTTP and does not call L6 drivers directly.

## 1. Scope
- PR-5 is read-only.
- Supported topics: `llm_runs`, `system_records`.
- Mutations are out of scope.

## 2. Route Contract
- Backend canonical route: `GET /cus/logs/list`.
- Gateway path: `GET /hoc/api/cus/logs/list`.
- Exactly one backend route resolves; no duplicate/double-prefix alias.

## 3. Query Contract
- Required:
  - `topic` enum: `llm_runs | system_records`
- Pagination:
  - `limit` default `20`
  - `limit` min `1`, max `100`
  - `offset` min `0`
  - out-of-range values -> `400 INVALID_QUERY`
- `as_of`:
  - Unsupported in PR-5
  - any `as_of` usage -> `400 UNSUPPORTED_PARAM`
- Unknown query params:
  - rejected with `400 INVALID_QUERY`

## 4. Allowed Filters by Topic
For both topics (`llm_runs`, `system_records`):
- `limit`, `offset`

## 5. Layering and Execution
- Facade responsibility: boundary validation + translation + one dispatch.
- Exactly one `logs.query` registry call per request.
- No facade orchestration/composition.
- No direct database access from facade.

## 6. Determinism Contract
- No caller-controlled sorting in PR-5.
- Canonical ordering is fixed at L6:
  - LLM runs: `created_at desc, id desc`
  - System records: `created_at desc, id desc`
- Response order must match backend query order exactly.

## 7. Pagination and Total Semantics
- `total` is taken from backend operation result.
- Facade computes:
  - `has_more = (offset + len(records) < total)`
  - `next_offset = offset + len(records)` when `has_more=true`, else `null`

## 8. Success Response Contract
Required fields:
- `topic`
- `records`
- `total`
- `has_more`
- `pagination`
- `generated_at`
- `meta`

`meta` fields:
- `request_id` = middleware request id (same as response header `X-Request-ID`)
- `correlation_id` = inbound `X-Correlation-ID` if present, else `null`
- `as_of` = `null` in PR-5

`generated_at`:
- UTC RFC3339 with `Z` suffix.
- In PR-5 this timestamp is generated at facade boundary.

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
| Route | Route registered once | `/cus/logs/list` exists once; no duplicate alias |
| Topic | Missing topic | `400 INVALID_QUERY` |
| Topic | Invalid topic | `400 INVALID_QUERY` |
| Unknown params | Add undocumented query key | `400 INVALID_QUERY` |
| As-of | `as_of` supplied | `400 UNSUPPORTED_PARAM` |
| Pagination | `limit=0` or `limit>100` | `400 INVALID_QUERY` |
| Pagination | `offset<0` | `400 INVALID_QUERY` |
| Determinism | Same request repeated | Stable ordering retained |
| Tracing | `X-Request-ID` vs `meta.request_id` | Exact match |
| Tracing | `X-Correlation-ID` inbound | echoed in `meta.correlation_id` |
