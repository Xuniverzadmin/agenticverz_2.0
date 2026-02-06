# account_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/account_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-03
**Reference:** PIN-513 Phase 2, PIN-520 Phase 1 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            account_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Account domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/account_*.py, L2 APIs (sync capabilities)
Outbound:        account/L5_engines/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for account L5 engine access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for account domain.
Provides both async handler capabilities and sync bridge capabilities
for FastAPI endpoints that cannot use the async registry pattern.

## Capabilities

| Method | Returns | Module | Session |
|--------|---------|--------|---------|
| `account_query_capability(session)` | `AccountsFacade` | L5 engine | yes |
| `notifications_capability(session)` | `NotificationsFacade` | L5 engine | yes |
| `tenant_capability(session)` | `TenantEngine` | L5 engine | yes |
| `billing_provider_capability()` | `BillingProvider` | L5 engine | no (stateless) |
| `rbac_engine_capability()` | `get_rbac_engine()` | L5 engine | no |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.account_bridge import (
    get_account_bridge,
)

# Sync API dependency usage (PIN-520 Phase 1)
def _get_billing_provider():
    bridge = get_account_bridge()
    return bridge.billing_provider_capability()

# Get billing state
provider = _get_billing_provider()
billing_state = provider.get_billing_state(tenant_id)
```

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods | CI check 19 |
| Lazy imports only | No top-level L5 imports |
| L4 handlers + L2 APIs | Callers validation |

## PIN-520 Phase 1 (L4 Uniformity Initiative)

Added `billing_provider_capability()` to support L2→L4 migration for
billing dependencies. This capability is stateless and does NOT require
a session parameter since the billing provider manages its own state.

**Callers:**
- `app/hoc/api/cus/policies/billing_dependencies.py`
- `app/hoc/api/int/policies/billing_gate.py`

## PIN-L2-PURITY (L2 Bypass Removal)

Added `rbac_engine_capability()` to support L2 policy RBAC endpoints without
direct L5 imports.

**Caller:**
- `app/hoc/api/cus/policies/rbac_api.py`

## Singleton Access

```python
_instance = None

def get_account_bridge() -> AccountBridge:
    global _instance
    if _instance is None:
        _instance = AccountBridge()
    return _instance
```

---

*Generated: 2026-02-03*
