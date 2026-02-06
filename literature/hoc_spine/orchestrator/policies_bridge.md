# policies_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/policies_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-03
**Reference:** PIN-510 Phase 0A, PIN-520 Phase 1 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            policies_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Policies domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/policies_*.py, L2 APIs (sync capabilities)
Outbound:        policies/L5_engines/*, policies/L6_drivers/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for policies L5 engine and L6 driver access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for policies domain.
Provides both async handler capabilities and sync bridge capabilities
for FastAPI endpoints that cannot use the async registry pattern.

## Capabilities

### PoliciesBridge (L4 → L5/L6, sync capabilities)

| Method | Returns | Module | Session |
|--------|---------|--------|---------|
| `customer_policy_read_capability(session)` | `CustomerPolicyReadService` | L5 engine | yes |
| `policy_evaluations_capability(session)` | `PolicyEnforcementReadDriver` | L6 driver | yes |
| `recovery_write_capability(session)` | `RecoveryWriteService` | L6 driver | yes |
| `recovery_matcher_capability(session)` | `RecoveryMatcher` | L6 driver | yes |

### PoliciesEngineBridge (L4 → L5 engine access, sync capabilities)

| Method | Returns | Module | Session |
|--------|---------|--------|---------|
| `prevention_hook_capability()` | `prevention_hook` module | L5 engine | no |
| `policy_engine_capability()` | `get_policy_engine()` | L5 engine | no |
| `policy_engine_class_capability()` | `PolicyEngine` class | L5 engine | no |
| `governance_runtime_capability()` | `runtime_switch` module | L5 GovernanceFacade - PIN-520 Iter3.1 (2026-02-06) | no |
| `governance_config_capability()` | Governance config getter | L5 failure_mode_handler - PIN-520 Iter3.1 (2026-02-06) | no |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.policies_bridge import (
    get_policies_bridge,
    get_policies_engine_bridge,
)

# Sync API endpoint usage (PIN-520 Phase 1)
bridge = get_policies_bridge()
write_service = bridge.recovery_write_capability(session)
candidate_id, is_insert, count = write_service.upsert_recovery_candidate(...)

# L2 sync policy engine access (PIN-L2-PURITY)
engine_bridge = get_policies_engine_bridge()
policy_engine = engine_bridge.policy_engine_capability()
PolicyEngine = engine_bridge.policy_engine_class_capability()
prevention_hook = engine_bridge.prevention_hook_capability()
```

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods | CI check 19 |
| Session parameter for sync caps | Required for L2 sync APIs |
| Lazy imports only | No top-level L5/L6 imports |
| L4 handlers + L2 APIs | Callers validation |

**Note:** `PoliciesEngineBridge` exists to keep the base bridge within the 5-method limit.

## PIN-520 Phase 1 (L4 Uniformity Initiative)

Added recovery capabilities to support L2→L4 migration:

- `recovery_write_capability(session)` - Used by `recovery_ingest.py` for
  atomic upsert operations on recovery candidates
- `recovery_matcher_capability(session)` - Used by `recovery.py` for
  failure pattern matching and suggestion generation

**Callers:**
- `app/hoc/api/cus/recovery/recovery_ingest.py`
- `app/hoc/api/cus/policies/recovery.py` (pending migration)

## Singleton Access

```python
_instance = None

def get_policies_bridge() -> PoliciesBridge:
    global _instance
    if _instance is None:
        _instance = PoliciesBridge()
    return _instance
```

---

*Generated: 2026-02-03*
