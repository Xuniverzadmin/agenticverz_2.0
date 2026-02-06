# HOC API Wiring Migration Plan

**Status:** EXECUTED - COMPLETE
**Created:** 2026-02-04
**Scope:** Migrate `app/main.py` router imports from legacy `app/api/*` to HOC `app/hoc/api/*`

---

## Audit Summary (2 Passes Complete)

### First Pass Findings
- ✅ HOC files export `router` as `APIRouter` instance
- ✅ Route prefixes match between legacy and HOC (e.g., both use `/guard`)
- ⚠️ `c2_predictions_router` comes from `app/predictions/api.py`, not `app/api/` - separate module

### Second Pass (Skeptical) Findings
- ❌ **3 files in Phase 3 are NOT routers** - they are dependency/helper modules:
  - `billing_dependencies.py` - FastAPI dependencies
  - `auth_helpers.py` - Auth helper utilities
  - `protection_dependencies.py` - FastAPI dependencies
- ✅ Total 73 actual routers in HOC (76 files - 3 non-routers)
- ✅ Prefix audit passed - no conflicts detected

### Corrections Applied
- Phase 3 reduced from 7 to 4 routers (removed 3 non-router files)
- Added special handling for `c2_predictions_router` (separate module)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Legacy routers to migrate | 68 |
| Legacy routers needing HOC creation | 3 |
| HOC routers already exist (new) | 4 |
| Total HOC routers after migration | 75 |

---

## Phase 0: Pre-Migration Verification

### 0.1 Verify HOC Router Exports

Each HOC router file must export `router` as an `APIRouter` instance.

**Action:** Run verification script to confirm all 68 HOC files export `router`.

```bash
# Verify each HOC file exports router
for f in $(find app/hoc/api/cus app/hoc/api/fdr -name "*.py" -type f | grep -v __init__); do
  grep -l "^router = APIRouter" "$f" || echo "MISSING: $f"
done
```

### 0.2 Identify Route Prefix Conflicts

Legacy and HOC routers may have different prefixes. Must audit.

**Action:** Extract `prefix=` from all routers and compare.

---

## Phase 1: Create Missing HOC Routers (3 files)

These legacy routers have no HOC equivalent and must be created:

| Legacy | HOC Location | Purpose |
|--------|--------------|---------|
| `app/api/legacy_routes.py` | `app/hoc/api/cus/general/legacy_routes.py` | 410 Gone for deprecated paths |
| `app/api/v1_killswitch.py` | `app/hoc/api/cus/policies/v1_killswitch.py` | Kill switch, incidents, replay |
| `app/api/v1_proxy.py` | `app/hoc/api/cus/integrations/v1_proxy.py` | OpenAI-compatible proxy |

**Action:** Copy files to HOC locations with proper L2 headers.

---

## Phase 2: Update `app/main.py` Imports

### 2.1 Import Mapping (68 routers)

| Current Import | New Import |
|----------------|------------|
| `from .api.M25_integrations import router` | `from .hoc.api.cus.policies.M25_integrations import router` |
| `from .api.activity import router` | `from .hoc.api.cus.activity.activity import router` |
| `from .api.agents import router` | `from .hoc.api.cus.general.agents import router` |
| `from .api.alerts import router` | `from .hoc.api.cus.policies.alerts import router` |
| `from .api.analytics import router` | `from .hoc.api.cus.policies.analytics import router` |
| `from .api.aos_accounts import router` | `from .hoc.api.cus.policies.aos_accounts import router` |
| `from .api.aos_api_key import router` | `from .hoc.api.cus.policies.aos_api_key import router` |
| `from .api.aos_cus_integrations import router` | `from .hoc.api.cus.policies.aos_cus_integrations import router` |
| `from .api.authz_status import router` | `from .hoc.api.cus.agent.authz_status import router` |
| `from .api.compliance import router` | `from .hoc.api.cus.policies.compliance import router` |
| `from .api.controls import router` | `from .hoc.api.cus.policies.controls import router` |
| `from .api.cost_guard import router` | `from .hoc.api.cus.incidents.cost_guard import router` |
| `from .api.cost_intelligence import router` | `from .hoc.api.cus.logs.cost_intelligence import router` |
| `from .api.cost_ops import router` | `from .hoc.api.cus.ops.cost_ops import router` |
| `from .api.costsim import router` | `from .hoc.api.cus.analytics.costsim import router` |
| `from .api.cus_enforcement import router` | `from .hoc.api.cus.policies.cus_enforcement import router` |
| `from .api.cus_telemetry import router` | `from .hoc.api.cus.integrations.cus_telemetry import router` |
| `from .api.customer_visibility import router` | `from .hoc.api.cus.policies.customer_visibility import router` |
| `from .api.datasources import router` | `from .hoc.api.cus.policies.datasources import router` |
| `from .api.debug_auth import router` | `from .hoc.api.cus.general.debug_auth import router` |
| `from .api.detection import router` | `from .hoc.api.cus.policies.detection import router` |
| `from .api.discovery import router` | `from .hoc.api.cus.agent.discovery import router` |
| `from .api.embedding import router` | `from .hoc.api.cus.api_keys.embedding import router` |
| `from .api.evidence import router` | `from .hoc.api.cus.policies.evidence import router` |
| `from .api.feedback import router` | `from .hoc.api.cus.analytics.feedback import router` |
| `from .api.founder_actions import router` | `from .hoc.api.fdr.ops.founder_actions import router` |
| `from .api.founder_explorer import router` | `from .hoc.api.fdr.account.founder_explorer import router` |
| `from .api.founder_onboarding import router` | `from .hoc.api.fdr.incidents.founder_onboarding import router` |
| `from .api.founder_review import router` | `from .hoc.api.fdr.logs.founder_review import router` |
| `from .api.founder_timeline import router` | `from .hoc.api.fdr.logs.founder_timeline import router` |
| `from .api.guard import router` | `from .hoc.api.cus.policies.guard import router` |
| `from .api.guard_logs import router` | `from .hoc.api.cus.logs.guard_logs import router` |
| `from .api.guard_policies import router` | `from .hoc.api.cus.policies.guard_policies import router` |
| `from .api.health import router` | `from .hoc.api.cus.general.health import router` |
| `from .api.incidents import router` | `from .hoc.api.cus.incidents.incidents import router` |
| `from .api.legacy_routes import router` | `from .hoc.api.cus.general.legacy_routes import router` |
| `from .api.lifecycle import router` | `from .hoc.api.cus.policies.lifecycle import router` |
| `from .api.limits.override import router` | `from .hoc.api.cus.policies.override import router` |
| `from .api.limits.simulate import router` | `from .hoc.api.cus.policies.simulate import router` |
| `from .api.logs import router` | `from .hoc.api.cus.policies.logs import router` |
| `from .api.memory_pins import router` | `from .hoc.api.cus.account.memory_pins import router` |
| `from .api.monitors import router` | `from .hoc.api.cus.policies.monitors import router` |
| `from .api.notifications import router` | `from .hoc.api.cus.policies.notifications import router` |
| `from .api.onboarding import router` | `from .hoc.api.cus.agent.onboarding import router` |
| `from .api.ops import router` | `from .hoc.api.fdr.incidents.ops import router` |
| `from .api.overview import router` | `from .hoc.api.cus.overview.overview import router` |
| `from .api.platform import router` | `from .hoc.api.cus.agent.platform import router` |
| `from .api.policies import router` | `from .hoc.api.cus.policies.policies import router` |
| `from .api.policy import router` | `from .hoc.api.cus.policies.policy import router` |
| `from .api.policy_layer import router` | `from .hoc.api.cus.policies.policy_layer import router` |
| `from .api.policy_limits_crud import router` | `from .hoc.api.cus.policies.policy_limits_crud import router` |
| `from .api.policy_proposals import router` | `from .hoc.api.cus.policies.policy_proposals import router` |
| `from .api.policy_rules_crud import router` | `from .hoc.api.cus.policies.policy_rules_crud import router` |
| `from .api.predictions import router` | `from .hoc.api.cus.analytics.predictions import router` |
| `from .api.rate_limits import router` | `from .hoc.api.cus.policies.rate_limits import router` |
| `from .api.rbac_api import router` | `from .hoc.api.cus.policies.rbac_api import router` |
| `from .api.recovery import router` | `from .hoc.api.cus.recovery.recovery import router` |
| `from .api.recovery_ingest import router` | `from .hoc.api.cus.recovery/recovery_ingest import router` |
| `from .api.replay import router` | `from .hoc.api.cus.policies.replay import router` |
| `from .api.retrieval import router` | `from .hoc.api.cus.policies.retrieval import router` |
| `from .api.runtime import router` | `from .hoc.api.cus.policies.runtime import router` |
| `from .api.scenarios import router` | `from .hoc.api.cus.analytics.scenarios import router` |
| `from .api.scheduler import router` | `from .hoc.api.cus.policies.scheduler import router` |
| `from .api.sdk import router` | `from .hoc.api.cus.general.sdk import router` |
| `from .api.session_context import router` | `from .hoc.api.cus.integrations.session_context import router` |
| `from .api.status_history import router` | `from .hoc.api.cus.policies.status_history import router` |
| `from .api.tenants import router` | `from .hoc.api.cus.logs.tenants import router` |
| `from .api.traces import router` | `from .hoc.api.cus.logs.traces import router` |
| `from .api.v1_killswitch import router` | `from .hoc.api.cus.policies.v1_killswitch import router` |
| `from .api.v1_proxy import router` | `from .hoc.api.cus.integrations.v1_proxy import router` |
| `from .api.workers import router` | `from .hoc.api.cus.policies.workers import router` |

### 2.2 Special Cases

| Import | Action |
|--------|--------|
| `from .predictions.api import router as c2_predictions_router` | **DO NOT MIGRATE** - This is a separate module (`app/predictions/`), not in legacy `app/api/`. Keep as-is. |
| `from .api.founder_contract_review import router` | Migrate to `from .hoc.api.fdr.agent.founder_contract_review import router` |

### 2.3 Typo Correction

In the mapping table above, this line has a typo:
- **Wrong:** `from .hoc.api.cus.recovery/recovery_ingest import router`
- **Correct:** `from .hoc.api.cus.recovery.recovery_ingest import router`

---

## Phase 3: Wire New HOC-Only Routers (4 routers)

These HOC routers exist but have no legacy equivalent (excluding `mcp_servers` already wired):

| HOC Router | Suggested Prefix | Purpose |
|------------|------------------|---------|
| `hoc/api/fdr/account/founder_lifecycle.py` | `/fdr/lifecycle` | Founder lifecycle management |
| `hoc/api/fdr/agent/founder_contract_review.py` | `/fdr/contracts` | Contract review |
| `hoc/api/cus/policies/connectors.py` | `/api/v1/connectors` | Connector management |
| `hoc/api/cus/policies/governance.py` | `/api/v1/governance` | Governance endpoints |

**NOT Routers (removed from Phase 3):**
- `api_keys/auth_helpers.py` - FastAPI dependency module, not a router
- `integrations/protection_dependencies.py` - FastAPI dependency module, not a router
- `policies/billing_dependencies.py` - FastAPI dependency module, not a router

**Action:** Add `include_router()` calls for the 4 routers above in `app/main.py`.

---

## Phase 4: Delete Dead Code

### 4.1 Delete `app/hoc/api/int/agent/main.py`

This file imports 72 non-existent modules from `hoc.api.int.agent.api.*`. It is dead code.

### 4.2 Deprecate Legacy `app/api/*` (PIN-511 Extension)

After Phase 2 completes successfully:

1. Add tombstone header to `app/api/__init__.py`:
   ```python
   # TOMBSTONE_EXPIRY: 2026-03-04
   # DEPRECATED: All routers migrated to app/hoc/api/
   # Do not add new code here. See PIN-526.
   ```

2. Update PIN-511 to include `app/api/*` in the legacy boundary.

---

## Phase 5: Verification

### 5.1 Startup Test

```bash
cd backend && python -c "from app.main import app; print('OK')"
```

### 5.2 Route Count Verification

```bash
# Before migration
curl -s http://localhost:8000/openapi.json | jq '.paths | keys | length'

# After migration (should be same)
curl -s http://localhost:8000/openapi.json | jq '.paths | keys | length'
```

### 5.3 Run API Tests

```bash
PYTHONPATH=. python3 -m pytest tests/api/ -v --tb=short
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Route prefix mismatch | Phase 0.2 prefix audit |
| Missing router exports | Phase 0.1 verification script |
| Import errors at startup | Incremental migration (batch of 10) |
| Breaking production | Deploy to staging first |

---

## Rollback Plan

If migration fails:
1. Revert `app/main.py` to previous commit
2. Keep `app/api/*` in place (not deleted in Phase 4)
3. Investigate specific import failure

---

## Execution Order

1. **Phase 0:** Pre-verification (30 min)
2. **Phase 1:** Create 3 missing HOC routers (1 hour)
3. **Phase 2:** Update imports in batches of 10 (2 hours)
4. **Phase 3:** Wire 7 new HOC routers (30 min)
5. **Phase 4:** Delete dead code, add tombstones (30 min)
6. **Phase 5:** Full verification (1 hour)

**Total Estimated Effort:** 5.5 hours

---

## Approval Required

- [ ] Architecture review
- [ ] Staging deployment test
- [ ] Production deployment approval

---

## References

- PIN-511: Legacy `app/services/*` Boundary
- PIN-516: MCP Server Management (already wired)
- HOC Layer Topology V2.0.0
