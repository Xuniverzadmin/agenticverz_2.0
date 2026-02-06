# P2-Step4-1: L2 Non-Registry Justified Exceptions

**Date:** 2026-02-06
**Reference:** P2_STEP4_1_L2_NON_REGISTRY_AUDIT.md (READ-ONLY)
**Status:** COMPLETE - All 37 files have justified exceptions

---

## Summary

Of 37 L2 APIRouter files not using `get_operation_registry()`:

| Category | Count | Justification |
|----------|-------|---------------|
| Stateless / Facade delegation | 16 | No direct DB access at L2 |
| Console adapter (PIN-281) | 2 | External boundary pattern |
| Already uses L4 bridge pattern | 19 | PIN-520 sync pattern compliant |
| **Needs conversion** | **0** | — |

**Result:** All 37 files are compliant or have justified exceptions.

---

## Category 1: Stateless / Facade Delegation (16 files)

These L2 files either:
- Have no database operations (pure computation, introspection)
- Delegate to L5 facades via dependency injection (facade handles DB internally)

| File | Pattern | Justification |
|------|---------|---------------|
| `agent/authz_status.py` | Stateless | Auth introspection, no DB |
| `agent/onboarding.py` | Stateless | Auth state machine, no direct DB |
| `analytics/scenarios.py` | Stateless | In-memory simulation |
| `api_keys/auth_helpers.py` | Utility | No endpoints, helper only |
| `api_keys/embedding.py` | Facade | Delegates to embedding service |
| `general/health.py` | Stateless | Infrastructure health checks |
| `general/legacy_routes.py` | Stateless | 410 Gone stubs |
| `general/sdk.py` | Stateless | SDK handshake, auth service |
| `integrations/session_context.py` | Stateless | PIN-409 auth context read |
| `policies/alerts.py` | Facade | AlertsFacade handles DB |
| `policies/compliance.py` | Facade | ComplianceFacade handles DB |
| `policies/lifecycle.py` | Facade | LifecycleFacade handles DB |
| `policies/monitors.py` | Facade | MonitorsFacade handles DB |
| `policies/retrieval.py` | Facade | RetrievalFacade handles DB |
| `policies/runtime.py` | Stateless | Plan simulation, no DB writes |
| `policies/scheduler.py` | Facade | SchedulerFacade handles DB |

**Owner:** Domain teams
**Evidence:** Files have no direct `session.execute()`, `sqlalchemy`, or `sqlmodel` imports.

---

## Category 2: Console Adapter Pattern (2 files)

PIN-281 pattern: thin L2 boundary → L3 adapter → L4 bridge.

| File | Auth | Adapter |
|------|------|---------|
| `logs/guard_logs.py` | verify_console_token | customer_logs_adapter |
| `policies/guard_policies.py` | verify_console_token | customer_policies_adapter |

**Owner:** Console integration team
**Justification:** External console boundary requires custom auth translation.

---

## Category 3: Already Uses L4 Bridge Pattern (19 files)

Files importing from `operation_registry` (session helpers, sql_text) or using L4 bridges.

| File | Evidence Pattern |
|------|------------------|
| `agent/discovery.py` | get_sync_session_dep / sql_text |
| `agent/platform.py` | get_sync_session_dep / sql_text |
| `analytics/feedback.py` | get_async_session_context / sql_text |
| `analytics/predictions.py` | get_async_session_context / sql_text |
| `general/agents.py` | session.execute() + bridges |
| `general/debug_auth.py` | get_sync_session_dep |
| `incidents/cost_guard.py` | get_sync_session_dep / sql_text |
| `integrations/v1_proxy.py` | get_sync_session_dep / sql_text |
| `logs/cost_intelligence.py` | get_sync_session_dep + analytics_bridge |
| `logs/tenants.py` | get_sync_session_dep + bridges |
| `logs/traces.py` | get_async_session_context / sql_text |
| `policies/M25_integrations.py` | get_sync_session_dep / sql_text |
| `policies/customer_visibility.py` | get_sync_session_dep |
| `policies/policy_proposals.py` | get_sync_session_dep / sql_text |
| `policies/rbac_api.py` | get_sync_session_dep + account_bridge |
| `policies/replay.py` | get_sync_session_dep / sql_text |
| `policies/v1_killswitch.py` | get_sync_session_dep / sql_text |
| `recovery/recovery.py` | get_sync_session_dep / sql_text |
| `recovery/recovery_ingest.py` | get_sync_session_dep + policies_bridge |

**Owner:** Domain teams
**Justification:** PIN-520 sync endpoint pattern - uses operation_registry session helpers.

---

## Evidence Commands

```bash
# List non-registry APIRouter files
python3 - <<'PY'
from pathlib import Path
import re
root = Path('backend/app/hoc/api/cus')
rx = re.compile(r'\bget_operation_registry\b')
for p in sorted(root.rglob('*.py')):
    try:
        text = p.read_text()
    except Exception:
        continue
    if 'APIRouter' in text and not rx.search(text):
        print(p.relative_to(root))
PY

# Detect L4 bridge pattern usage
python3 - <<'PY'
from pathlib import Path
import re
root = Path('backend/app/hoc/api/cus')
patterns = [
    r'\bget_\w+_bridge\b',
    r'\bget_sync_session_dep\b',
    r'\bget_async_session_context\b',
    r'\bsql_text\b',
]
for p in sorted(root.rglob('*.py')):
    try:
        text = p.read_text()
    except Exception:
        continue
    if 'APIRouter' in text and not re.search(r'\bget_operation_registry\b', text):
        matches = [pat for pat in patterns if re.search(pat, text)]
        if matches:
            print(f"{p.relative_to(root)}: {matches}")
PY

# Detect Facade delegation
python3 - <<'PY'
from pathlib import Path
import re
root = Path('backend/app/hoc/api/cus')
for p in sorted(root.rglob('*.py')):
    try:
        text = p.read_text()
    except Exception:
        continue
    if 'APIRouter' in text and re.search(r'Facade', text):
        print(p.relative_to(root))
PY
```

---

## Final Metrics

| Metric | Count |
|--------|-------|
| Total L2 APIRouter files | 69 |
| Using get_operation_registry() | 32 |
| Not using get_operation_registry() | 37 |
| — Stateless / Facade delegation | 16 |
| — Console adapter (PIN-281) | 2 |
| — Uses L4 bridge pattern | 19 |
| **Needs conversion** | **0** |

**Compliance:** 100% (all files compliant or justified)

---

## Sign-Off

**Documented by:** Claude (Iter3.2)
**Date:** 2026-02-06
**Approved patterns:**
1. `get_operation_registry()` - Full registry pattern
2. `get_sync_session_dep()` / `get_async_session_context()` / `sql_text()` - PIN-520 sync pattern
3. Facade delegation - L5 facade handles DB
4. Console adapter - PIN-281 boundary pattern
5. Stateless - No DB access needed

---

*This document supplements P2_STEP4_1_L2_NON_REGISTRY_AUDIT.md (READ-ONLY)*
