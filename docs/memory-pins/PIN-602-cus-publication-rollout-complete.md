# PIN-602: CUS Publication Rollout Complete

## Metadata
- Date: 2026-02-21
- Scope: CUS grouped ledger + swagger publication endpoints live on stagetest
- PR: [#33](https://github.com/Xuniverzadmin/agenticverz_2.0/pull/33) (MERGED)
- Commits: `510a4587` (PR #33 merge), `835c7198` (RBAC fix + evidence)
- Plan: `backend/app/hoc/docs/architecture/usecases/HOC_CUS_APIs_Swagger_Stagetest_Rollout_2026_02_21_plan.md`
- Evidence: `backend/app/hoc/docs/architecture/usecases/HOC_CUS_APIs_Swagger_Stagetest_Rollout_2026_02_21_plan_implemented.md`

## What Was Fixed

### 1. Apache Proxy Misroute
The existing ProxyPass rule for `/apis/ledger` in `/etc/apache2/sites-available/stagetest.agenticverz.com.conf` mapped to `/hoc/api/stagetest/apis` (the wave1 stagetest snapshot endpoint), not the CUS publication router. Additionally, `/apis/swagger` had NO proxy rule, causing Apache SPA fallback to serve HTML.

**Fix:** Replaced stagetest alias with direct backend passthrough:
```
ProxyPass /apis/ledger  http://127.0.0.1:8000/apis/ledger
ProxyPass /apis/swagger http://127.0.0.1:8000/apis/swagger
```

### 2. RBAC Schema Gap
The gateway middleware (`app/auth/gateway_middleware.py`) loads public paths from `RBAC_RULES.yaml` via `rbac_rules_loader.get_public_paths()` (PIN-391 schema-driven auth). PR #33 only updated `gateway_policy.py` (the fallback), so the endpoints returned 403.

**Fix:** Added two rules to `design/auth/RBAC_RULES.yaml`:
- `CUS_PUBLICATION_LEDGER` — `path_prefix: /apis/ledger/`, `access_tier: PUBLIC`
- `CUS_PUBLICATION_SWAGGER` — `path_prefix: /apis/swagger/`, `access_tier: PUBLIC`

## Runtime Proof Matrix (2026-02-21 10:51:58 UTC)

| Endpoint | HTTP | Content-Type |
|----------|------|-------------|
| `https://stagetest.agenticverz.com/apis/ledger/cus` | 200 | application/json |
| `https://stagetest.agenticverz.com/apis/ledger/cus/activity` | 200 | application/json |
| `https://stagetest.agenticverz.com/apis/swagger/cus` | 200 | application/json |
| `https://stagetest.agenticverz.com/apis/swagger/cus/activity` | 200 | application/json |

### Domain Sweep (20/20)

| Domain | `/apis/ledger/cus/{d}` | `/apis/swagger/cus/{d}` |
|--------|------------------------|--------------------------|
| activity | 200 | 200 |
| account | 200 | 200 |
| api_keys | 200 | 200 |
| analytics | 200 | 200 |
| controls | 200 | 200 |
| incidents | 200 | 200 |
| integrations | 200 | 200 |
| logs | 200 | 200 |
| overview | 200 | 200 |
| policies | 200 | 200 |

### OpenAPI Parity (4/4 routes at 623 total)

```
/apis/ledger/cus
/apis/ledger/cus/{domain}
/apis/swagger/cus
/apis/swagger/cus/{domain}
```

## Key Pattern: Public Path Registration

New public endpoints require updates in **both** locations:
1. `gateway_policy.py` PUBLIC_PATHS — fallback (used if RBAC YAML fails)
2. `design/auth/RBAC_RULES.yaml` — primary (schema-driven via PIN-391)

## Files Changed
- `/etc/apache2/sites-available/stagetest.agenticverz.com.conf` (infra, not version-controlled)
- `design/auth/RBAC_RULES.yaml` (committed in `835c7198`)
- `backend/app/hoc/docs/architecture/usecases/HOC_CUS_APIs_Swagger_Stagetest_Rollout_2026_02_21_plan.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_CUS_APIs_Swagger_Stagetest_Rollout_2026_02_21_plan_implemented.md`

## Relationship to PIN-601
PIN-601 established the wave1 CUS ledger baseline and identified the runtime publication gap. This PIN closes that gap with live evidence.
