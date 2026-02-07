# API v1 Global Severance Plan

**Date:** 2026-02-06
**Scope:** All `/api/v1` references in `backend/app/` outside legacy `app/api/` and `app/services/`
**Baseline (live scan):** 52 files, 426 matches (see Acceptance Commands #3)

---

## Acceptance Commands

```bash
# After each batch:
cd /root/agenticverz2.0/backend

# 1. CI hygiene green
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci

# 2. Legacy-only guard green
PYTHONPATH=. python3 -m pytest -q tests/hoc_spine/test_api_v1_legacy_only.py

# 3. Residual count (should decrease batch by batch)
python3 - <<'PY'
from __future__ import annotations

from pathlib import Path

ROOT = Path("app")
EXCLUDE_DIRS = {
    ROOT / "api",
    ROOT / "services",
    ROOT / "adapters",
    ROOT / "hoc" / "cus" / "_domain_map",
}
EXCLUDE_FILES = {
    ROOT / "hoc" / "api" / "cus" / "general" / "legacy_routes.py",
}

needle = "/api/v1"
per_file: dict[str, int] = {}

for p in ROOT.rglob("*.py"):
    if any(ex in p.parents for ex in EXCLUDE_DIRS):
        continue
    if p in EXCLUDE_FILES:
        continue
    c = p.read_text(errors="ignore").count(needle)
    if c:
        per_file[str(p)] = c

print(f"remaining: {sum(per_file.values())} ({len(per_file)} files)")
for path, c in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0]))[:40]:
    print(f\"{path}: {c}\")
PY
```

---

## Classification Summary

| Category | Files | Matches | Risk | Batch |
|----------|-------|---------|------|-------|
| A. Live auth/gateway path matching | 19 | ~280 | HIGH — stale paths never match real requests | 1-3 |
| B. Live code generating URLs | 2 | 2 | HIGH — produces broken client URLs | 1 |
| C. Unwired router prefix | 1 | 1 | MEDIUM — `app/predictions/api.py` defines `/api/v1/c2/predictions`, but is not mounted by `app.main` | defer/decide |
| D. Docstring/comment endpoint lists | 19 | ~120 | LOW — cosmetic only | 4 |
| E. Error message / curl example strings | 8 | 8 | LOW — cosmetic | 4 |
| F. Intentional legacy (legacy_routes.py) | 1 | 12 | NONE — keep | skip |
| G. Documentation-only (`runtime_projections`) | 1 | 7 | NONE — already documents deprecation | skip |

---

## Batch 1 — Live URL Generation (2 files, HIGHEST PRIORITY)

These files produce `/api/v1` URLs in runtime responses — clients will get broken links.

| # | File | Line | Current | Fix |
|---|------|------|---------|-----|
| 1 | `app/hoc/cus/logs/L5_engines/evidence_facade.py` | 491 | `download_url=f"/api/v1/evidence/exports/{export_id}/download"` | `download_url=f"/evidence/exports/{export_id}/download"` |
| 2 | `app/hoc/cus/controls/L6_drivers/scoped_execution_driver.py` | 614 | `"Create a scope with POST /api/v1/recovery/scope first. "` | `"Create a scope with POST /recovery/scope first. "` |

**Acceptance after batch 1:**
```bash
rg "download_url.*api/v1" app/hoc/cus/logs/L5_engines/evidence_facade.py  # 0 matches
```

---

## Batch 2 — Auth Infrastructure Path Matching (10 files, ~280 matches)

These files contain path-to-permission/plane/gate mappings. Since canonical
routes no longer use `/api/v1`, these path matchers are **stale** — they match
paths that all return 410. Note: these matchers are typically used by
middleware, so they still run for canonical routes; they must be updated to
match canonical paths (or explicitly scoped to legacy-only handling).

**CRITICAL:** Each HOC file has a parallel copy in `app/auth/`. Both must be
updated in lockstep (or the `app/auth/` copies must be deleted if they are
dead code — verify before patching).

### Dual-copy files (HOC + auth)

| # | HOC File | auth File | Matches | Nature |
|---|----------|-----------|---------|--------|
| 1 | `hoc/int/policies/engines/rbac_middleware.py` | `auth/rbac_middleware.py` | 40+40 | Path→permission mapping (`path.startswith("/api/v1/...")`) |
| 2 | `hoc/int/agent/engines/onboarding_gate.py` | `auth/onboarding_gate.py` | 37+37 | Path→onboarding-state mapping |
| 3 | `hoc/int/general/engines/gateway_config.py` | `auth/gateway_config.py` | 35+35 | Public path exemption lists |
| 4 | `hoc/int/general/engines/route_planes.py` | `auth/route_planes.py` | 19+19 | Path→plane classification |
| 5 | `hoc/int/integrations/engines/gateway_middleware.py` | `auth/gateway_middleware.py` | 4+4 | Public path list + doctest examples |
| 6 | `hoc/int/integrations/drivers/oauth_providers.py` | `auth/oauth_providers.py` | 2+2 | OAuth redirect URIs |
| 7 | `hoc/int/policies/engines/rbac.py` | `auth/rbac.py` | 1+1 | External API call URL |

### HOC-only files

| # | File | Matches | Nature |
|---|------|---------|--------|
| 8 | `hoc/int/account/engines/lifecycle_gate.py` | 6 | SDK path exemptions |
| 9 | `hoc/api/int/general/protection_gate.py` | 1 | Auth public path |
| 10 | `hoc/api/int/policies/billing_gate.py` | 1 | Auth public path |
| 11 | `hoc/api/cus/integrations/protection_dependencies.py` | 1 | Auth public path |
| 12 | `hoc/cus/account/auth/L5_engines/rbac_engine.py` | 5 | Path→permission mapping |

### Approach

For each path-matching file:
1. **Determine which file is authoritative** — HOC or `app/auth/`
2. **Strip `/api/v1` prefix** from all path patterns (e.g., `"/api/v1/incidents"` → `"/incidents"`)
3. **Keep patterns that genuinely still serve under `/api/v1`** — only `/api/v1/auth/` (Clerk callbacks) and `/api/v1/c2/predictions/` (predictions router)
4. **Verify** no RBAC rules break for canonical routes

### Sub-batch 2A: rbac_middleware.py (largest, 40 refs each)

Every `path.startswith("/api/v1/...")` branch needs a dual match:
```python
# BEFORE:
if path.startswith("/api/v1/incidents") or "/incidents" in path:

# AFTER (already handles both):
# This one already works. But others like:
if path.startswith("/api/v1/costsim"):
# must become:
if path.startswith("/costsim") or path.startswith("/api/v1/costsim"):
```

**Decision needed:** Should we keep backward compatibility (match both
`/api/v1/X` and `/X`) or just match `/X` since `/api/v1/*` returns 410?
If 410 routes never reach RBAC (caught earlier), just strip.

### Sub-batch 2B: onboarding_gate.py (37 refs each)

All `ONBOARDING_PATHS`, `STAGE_REQUIRED_PATHS`, `STAGE_REQUIRED_PATTERNS`
need `/api/v1` stripped from paths and regex patterns.

### Sub-batch 2C: gateway_config.py (35 refs each)

All public path exemption entries need `/api/v1` stripped.

### Sub-batch 2D: route_planes.py (19 refs each)

All `RoutePlane.pattern` values need `/api/v1` stripped. The
`is_worker_plane()` and `is_founder_plane()` helper functions also need
updated `path.startswith(...)` checks.

### Sub-batch 2E: oauth_providers.py (2 refs each)

```python
# BEFORE:
self.redirect_uri = f"{OAUTH_REDIRECT_BASE}/api/v1/auth/callback/google"

# DECISION: Does /api/v1/auth/* still exist as a live route (not 410)?
# If the auth callback route moved, update. If it stayed, keep.
```

**Acceptance after batch 2:**
```bash
rg "/api/v1" app/auth/ --type py -c | awk -F: '{sum += $NF} END {print sum}'
# Target: 0 or near-0 (only oauth callbacks if still /api/v1)
```

---

## Batch 3 — Other Live Config Files (5 files, ~10 matches)

| # | File | Line | Nature | Fix |
|---|------|------|--------|-----|
| 1 | `hoc/int/general/engines/rbac_rules_loader.py` | 26,284,307,310 | Docstring examples | Strip `/api/v1` from examples |
| 2 | `auth/rbac_rules_loader.py` | 26,284,307,310 | Docstring examples (dual copy) | Same |
| 3 | `hoc/int/policies/drivers/query_authority.py` | 103 | Docstring example | Same |
| 4 | `auth/query_authority.py` | 103 | Docstring example (dual copy) | Same |
| 5 | `hoc/int/recovery/drivers/scoped_execution.py` | 599 | Error message | Strip `/api/v1` |

---

## Batch 4 — Docstring/Comment Cleanup (19+ files, ~120 matches)

Low priority. These are L5 engine/facade docstrings listing endpoint paths
like `- GET /api/v1/controls (list controls)`. Cosmetic only — no runtime
impact. Each file's module docstring just needs `/api/v1` stripped from
endpoint listings.

| # | File | Matches | Type |
|---|------|---------|------|
| 1 | `hoc/cus/hoc_spine/services/lifecycle_facade.py` | 12 | Docstring |
| 2 | `hoc/cus/integrations/L5_engines/datasources_facade.py` | 9 | Docstring |
| 3 | `hoc/cus/hoc_spine/services/scheduler_facade.py` | 9 | Docstring |
| 4 | `hoc/cus/hoc_spine/services/monitors_facade.py` | 8 | Docstring |
| 5 | `hoc/cus/hoc_spine/services/alerts_facade.py` | 8 | Docstring |
| 6 | `hoc/cus/logs/L5_engines/evidence_facade.py` | 6 | Docstring (line 491 fixed in batch 1) |
| 7 | `hoc/cus/policies/L5_engines/limits_facade.py` | 6 | Docstring |
| 8 | `hoc/cus/overview/L5_engines/overview_facade.py` | 6 | Docstring |
| 9 | `hoc/cus/integrations/L5_engines/connectors_facade.py` | 6 | Docstring |
| 10 | `hoc/cus/controls/L5_engines/controls_facade.py` | 6 | Docstring |
| 11 | `hoc/cus/account/L5_engines/notifications_facade.py` | 6 | Docstring |
| 12 | `hoc/cus/hoc_spine/services/compliance_facade.py` | 5 | Docstring |
| 13 | `hoc/cus/analytics/L5_engines/detection_facade.py` | 5 | Docstring |
| 14 | `hoc/cus/policies/L5_engines/governance_facade.py` | 4 | Docstring |
| 15 | `hoc/cus/hoc_spine/services/retrieval_facade.py` | 3 | Docstring |
| 16 | `hoc/cus/hoc_spine/schemas/common.py` | 1 | Docstring |
| 17 | `hoc/cus/hoc_spine/services/retrieval_mediator.py` | 1 | Docstring |
| 18 | `hoc/cus/logs/L5_engines/trace_mismatch_engine.py` | 1 | Curl example |
| 19 | `hoc/int/platform/engines/customer_sandbox.py` | 1 | Curl example |
| 20 | `hoc/int/platform/drivers/care.py` | 1 | Actionable fix string |
| 21 | `hoc/int/agent/drivers/db.py` | 1 | Comment |
| 22 | `auth/customer_sandbox.py` | 1 | Curl example |

**Fix pattern:** `replace_all` of `/api/v1/` with `/` in docstrings only.
Do NOT touch `legacy_routes.py` or `runtime_projections/__init__.py`.

---

## Deferred — Predictions Router

| File | Line | Current |
|------|------|---------|
| `app/predictions/api.py` | 56 | `router = APIRouter(prefix="/api/v1/c2/predictions")` |

This is a **LIVE router** still serving under `/api/v1/c2/predictions`. The
gateway_config lists it as a public path exemption. Changing it requires:
1. Moving the router prefix to `/c2/predictions`
2. Updating all gateway/RBAC exemption lists
3. Updating any client code that calls this endpoint
4. Possibly the frontend

**Reality check:** `app/predictions/api.py` currently defines this router, but it is not mounted by `backend/app/main.py`.
**Recommendation:** Decide whether to delete/retire it, or re-home it into HOC (`backend/app/hoc/api/cus/analytics/predictions.py`) as the canonical predictions surface.

---

## Files Explicitly Skipped

| File | Reason |
|------|--------|
| `app/hoc/api/cus/general/legacy_routes.py` | Intentional 410 handlers — defines `/api/v1` on purpose |
| `app/runtime_projections/__init__.py` | Documents the deprecation itself |
| `app/discovery/__init__.py` | Fixture data in docstring |
| `app/contracts/common.py` | Docstring example |
| `app/db.py` | Comment (if any) |
| All `app/api/**` | Legacy routers, scheduled for deletion |
| All `app/services/**` | Legacy services, scheduled for deletion |
| All `app/hoc/cus/_domain_map/**` | Documentation workbook |
| All `app/adapters/**` | Legacy adapters |

---

## Execution Order

1. **Batch 1** (2 files) — Fix broken URLs in live responses
2. **Batch 2** (10-12 files × 2 copies) — Auth infrastructure path matching
3. **Batch 3** (5 files) — Config docstring examples
4. **Batch 4** (22 files) — Cosmetic docstring cleanup

---

## Open Questions (require user decision)

1. **Dual copies:** Are `app/auth/` files still authoritative, or are the
   `app/hoc/int/` copies the canonical versions? Should we fix both, or
   delete one set?

2. **OAuth redirect URIs:** Do `/api/v1/auth/callback/google` and
   `/api/v1/auth/callback/azure` still exist as live routes? If so, they
   must keep the `/api/v1` prefix. If the auth callback routes moved to
   `/auth/callback/*`, update the URIs.

3. **RBAC backward compat:** Should path matchers match BOTH `/api/v1/X`
   and `/X` during a transition period, or just `/X`? If the 410 catch-all
   handles `/api/v1/*` before RBAC runs, just `/X` is sufficient.

4. **Predictions router:** Should `app/predictions/api.py` keep its
   `/api/v1/c2/predictions` prefix or be migrated now?
