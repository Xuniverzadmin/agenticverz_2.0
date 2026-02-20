# PR2 Auth-Positive Closure Evidence

**Date:** 2026-02-20
**PIN:** PIN-578
**Status:** COMPLETE

## Summary

PR2 removes the `/cus/` public-path exemption from the auth gateway, requiring all CUS
endpoints to authenticate via `X-AOS-Key` (machine) or `Authorization: Bearer` (human JWT).

## Changes Applied

### 1. gateway_policy.py — Remove `/cus/` bypass

**File:** `app/hoc/cus/hoc_spine/authority/gateway_policy.py`

- Removed `"/cus/"` from `PUBLIC_PATHS` list (was line 96)
- Comment added: `# "/cus/" removed — PR2: CUS endpoints require gateway auth (PIN-578)`

### 2. RBAC_RULES.yaml — Remove scaffold preflight rule

**File:** `design/auth/RBAC_RULES.yaml`

- Removed `CUS_ACTIVITY_RUNS_SCAFFOLD_PREFLIGHT` rule (was lines 623-634)
- This was a temporary `access_tier: PUBLIC` rule for `/cus/activity/runs` (expires 2026-03-15)
- Comment added: `# CUS_ACTIVITY_RUNS_SCAFFOLD_PREFLIGHT removed — PR2: CUS runs require auth (PIN-578)`

### 3. db.py — asyncpg/PgBouncer compatibility fixes

**File:** `app/db.py`

- `get_async_database_url()`: Strip `connect_timeout` and `sslmode` from async URL
  (asyncpg 0.31+ rejects these as unknown kwargs)
- `get_async_engine()`: Added `prepared_statement_cache_size=0` and `statement_cache_size=0`
  to `connect_args` (required for PgBouncer transaction mode)

## Auth Chain Verified

```
Request → Apache (/hoc/api/cus → /cus) → AuthGatewayMiddleware
  → _is_public_path() → FALSE (no /cus/ in PUBLIC_PATHS)
  → _authenticate_machine() → X-AOS-Key header → SHA256 hash → DB lookup
  → MachineCapabilityContext(tenant_id, scopes=["*"])
  → RBACMiddleware → required: runtime:query → derived: ["*"] → PASS
  → L2 runs_facade → L4 activity.query → L5 ActivityFacade → L6 ActivityReadDriver → DB
```

## Verification Matrix

| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 1 | No auth header | 401 | 401 | PASS |
| 2 | Valid API key + topic=live | 200 | 200 (6 runs) | PASS |
| 3 | Valid API key + topic=completed | 200 | 200 (0 runs) | PASS |
| 4 | Legacy X-AOS-Fixture header | 401 | 401 | PASS |
| 5 | Invalid API key | 401 | 401 | PASS |

**All 5 tests pass.** Evidence artifacts:
`backend/artifacts/stagetest/20260220T101339Z_pr2_auth_closure/`

## API Key Used for Evidence

- **Key ID:** `137fcf40-e4e9-4801-935f-601c48eefe9c`
- **Tenant:** `a1b2c3d4-e5f6-7890-abcd-ef1234567890` (Demo Tenant)
- **Permissions:** `["*"]` (wildcard)
- **Created:** 2026-02-19 (DB-backed, production path)
- **Revoked:** 2026-02-20T10:55:56.072460Z — post-validation hardening
- **Revocation reason:** `PR2 evidence complete - post closure hardening`

## Deployment Notes

- `gateway_policy.py` is NOT volume-mounted — changes require `docker cp` + restart
- `RBAC_RULES.yaml` IS volume-mounted at `/design:/design` — changes are live on restart
- `db.py` is NOT volume-mounted — changes require `docker cp` + restart
- After restart, allow ~20s for PgBouncer connection pool warm-up before testing
