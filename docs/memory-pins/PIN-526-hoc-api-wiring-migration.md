# PIN-526: HOC API Wiring Migration

**Status:** COMPLETE
**Created:** 2026-02-04
**Category:** Architecture Migration
**Severity:** High
**Author:** Claude Opus 4.5

---

## Summary

Migrated all 68 legacy API routers from `app/api/*` to `app/hoc/api/*`, completing the HOC (Hierarchical Operations Console) API layer consolidation. This migration enables future deletion of the legacy `app/api/` package.

---

## Problem Statement

The codebase had two parallel API structures:
1. Legacy: `app/api/*.py` - Original flat structure
2. HOC: `app/hoc/api/{cus,fdr}/*` - New hierarchical domain-based structure

This duplication caused:
- Confusion about canonical import paths
- Inconsistent routing patterns
- Blocked cleanup of legacy code (PIN-511)
- 73 HOC routers existed but only 5 were wired to main.py

---

## Solution

### Phase 0: Pre-Migration Verification
- Verified all HOC files export `router` as `APIRouter`
- Audited route prefixes for conflicts
- Identified 3 non-router files (dependencies, not routers)

### Phase 1: Create Missing HOC Routers
Created 3 HOC equivalents for routers that only existed in legacy:
- `app/hoc/api/cus/general/legacy_routes.py` (410 Gone handlers)
- `app/hoc/api/cus/policies/v1_killswitch.py` (KillSwitch MVP)
- `app/hoc/api/cus/integrations/v1_proxy.py` (OpenAI proxy)

### Phase 2: Update main.py Imports
Migrated 68 router imports from legacy to HOC paths:
```python
# Before
from .api.health import router as health_router

# After
from .hoc.api.cus.general.health import router as health_router
```

### Phase 3: Wire New HOC-Only Routers
Added 4 HOC routers that had no legacy equivalent:
- `founder_lifecycle.py` → `/fdr/lifecycle/*`
- `connectors.py` → `/api/v1/connectors/*`
- `governance.py` → `/api/v1/governance/*`

### Phase 4: Dead Code Cleanup
- Deleted `app/hoc/api/int/agent/main.py` (85KB duplicate)
- Added tombstone to `app/api/__init__.py` (expiry: 2026-03-04)

### Phase 5: Verification
- App imports successfully with 688 API routes
- Created canonical literature documentation

---

## Import Fixes Required

During migration, 25+ broken imports were fixed:

### Relative Import Fixes
Many HOC files had broken relative imports copied from legacy:
```python
# Broken (looking for non-existent path)
from ..auth.console_auth import verify_fops_token

# Fixed (absolute import)
from app.auth.console_auth import verify_fops_token
```

### Missing Module Shims
Created `app/services/_audit_shim.py` as no-op stub to break circular dependency chain in legacy services.

### Legacy __init__.py Cleanup
- Disabled broken `customer_incidents_adapter` import in `app/adapters/__init__.py`
- Removed legacy re-exports from `app/hoc/api/cus/policies/__init__.py`

---

## Domain Mapping

### Customer (CUS) Domains
| Domain | Primary Routes | Router Count |
|--------|---------------|--------------|
| policies | `/api/v1/policies/*`, `/guard/*`, `/v1/killswitch/*` | 35 |
| logs | `/api/v1/logs/*`, `/guard/logs/*` | 4 |
| incidents | `/api/v1/incidents/*` | 2 |
| integrations | `/api/v1/integrations/*`, `/v1/*` | 5 |
| analytics | `/api/v1/analytics/*`, `/cost/*` | 4 |
| agent | `/api/v1/agents/*`, `/api/v1/discovery/*` | 4 |
| general | `/health`, `/api/v1/sdk/*` | 5 |
| account | `/api/v1/accounts/*` | 1 |
| activity | `/api/v1/activity/*` | 1 |
| overview | `/api/v1/overview/*` | 1 |
| ops | `/ops/cost/*` | 1 |
| recovery | `/api/v1/recovery/*` | 2 |

### Founder (FDR) Domains
| Domain | Primary Routes | Router Count |
|--------|---------------|--------------|
| account | `/explorer/*`, `/fdr/lifecycle/*` | 2 |
| agent | `/fdr/contracts/*` | 1 |
| incidents | `/fdr/onboarding/*`, `/ops/*` | 2 |
| logs | `/fdr/review/*`, `/fdr/timeline/*` | 2 |
| ops | `/ops/actions/*` | 1 |

---

## Tombstone Registry

| File | Expiry | Action |
|------|--------|--------|
| `app/api/__init__.py` | 2026-03-04 | Delete entire package |
| `app/hoc/api/cus/policies/__init__.py` | 2026-03-04 | Review re-exports |
| `app/services/_audit_shim.py` | 2026-03-04 | Delete shim |

---

## Metrics

| Metric | Value |
|--------|-------|
| Legacy routers migrated | 68 |
| New HOC routers wired | 4 |
| Total API routes | 688 |
| Broken imports fixed | 25+ |
| Dead code deleted | 85KB |
| Files with tombstones | 3 |

---

## Verification Commands

```bash
# Startup test
cd backend && DATABASE_URL="..." python -c "from app.main import app; print('OK')"

# Route count
cd backend && DATABASE_URL="..." python -c "
from app.main import app
print(f'Routes: {len([r for r in app.routes if hasattr(r, \"methods\")])}')"

# API tests
cd backend && PYTHONPATH=. python -m pytest tests/api/ -v --tb=short
```

---

## Related Artifacts

- **Migration Plan:** `app/hoc/_migration/PLAN-HOC-API-WIRING.md`
- **Canonical Docs:** `app/hoc/api/hoc_api_canonical_literature.md`
- **Layer Topology:** HOC Layer Topology V2.0.0 (PIN-484)
- **Legacy Boundary:** PIN-511 (`app/services/*` scheduled for deletion)

---

## Future Work

1. **Delete legacy `app/api/*`** after tombstone expiry (2026-03-04)
2. **Migrate remaining adapters** from `app/adapters/` to HOC equivalents
3. **Fix remaining type errors** in HOC API files (pre-existing)
4. **Remove `_audit_shim.py`** once services layer deleted

---

## Lessons Learned

1. **Relative imports break on copy** - When copying files to HOC, relative imports become invalid. Always use absolute imports in HOC.

2. **Legacy __init__.py side effects** - Python evaluates `__init__.py` when importing any module from a package. Broken imports in `__init__.py` break all submodule imports.

3. **Audit twice** - The initial plan had 76 HOC files but only 73 were actual routers. Second-pass audit caught 3 non-router files.

4. **Shims unblock progress** - Creating temporary shims (like `_audit_shim.py`) allows migration to proceed while deferring full legacy cleanup.

---

## Sign-off

- [x] Migration plan approved
- [x] Phase 0-5 executed
- [x] App imports successfully
- [x] Documentation created
- [x] PIN recorded
