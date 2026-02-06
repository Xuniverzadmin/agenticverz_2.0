# analytics_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/analytics_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-03
**Reference:** PIN-520 (L4 Uniformity Initiative), PIN-504 (C4 Loop Model)

---

## Placement Card

```
File:            analytics_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Analytics domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/analytics_*.py
Outbound:        analytics/L5_engines/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for analytics L5 engine access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for analytics L5 engines.
Implements the Switchboard Pattern (Law 4 - PIN-507):

- Never accepts session parameters
- Returns module references for lazy access
- Handler binds session (Law 4 responsibility)
- No retry logic, no decisions, no state

## Capabilities

| Method | Returns | L5/L6 Module |
|--------|---------|--------------|
| `config_capability()` | `config_engine` | `is_v2_disabled_by_drift`, `is_v2_sandbox_enabled`, `get_config` |
| `sandbox_capability()` | `sandbox_engine` | `simulate_with_sandbox` |
| `canary_capability()` | `canary_engine` | `run_canary` |
| `divergence_capability()` | `divergence_engine` | `generate_divergence_report` |
| `datasets_capability()` | `datasets_engine` | `get_dataset_validator`, `validate_all_datasets`, `validate_dataset` |
| `cost_write_capability(session)` | `CostWriteDriver` | PIN-520 Phase 1: Sync DB writes for cost records, feature tags, budgets |
| `anomaly_coordinator_capability()` | Anomaly coordinator factory | L5 DetectionFacade - PIN-520 Iter3.1 (2026-02-06) |
| `detection_facade_capability()` | Detection facade factory | L4 handlers - PIN-520 Iter3.1 (2026-02-06) |
| `alert_driver_capability()` | `AlertDriver` class | L5 AlertWorkerEngine - PIN-520 Iter3.1 (2026-02-06) |
| `alert_adapter_factory_capability()` | `get_alert_delivery_adapter` | L5 AlertWorkerEngine - PIN-520 Iter3.1 (2026-02-06) |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.analytics_bridge import (
    get_analytics_bridge,
)

bridge = get_analytics_bridge()

# Get config capability
config = bridge.config_capability()
if config.is_v2_disabled_by_drift():
    return OperationResult.fail("V2 disabled by drift")

# Get sandbox capability
sandbox = bridge.sandbox_capability()
result = await sandbox.simulate_with_sandbox(session, params)
```

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods (6 with PIN-520 exception) | CI check 19 |
| Returns modules (not sessions) | Code review (exception: cost_write_capability) |
| Lazy imports only | No top-level L5 imports |
| L4 handlers only + L2 APIs (for sync bridge caps) | Forbidden import check |

## PIN-520 Phase 1 (L4 Uniformity Initiative)

Added `cost_write_capability(session)` to provide L4 bridge access for
`cost_intelligence.py`. This is a sync bridge capability that accepts a
session parameter for FastAPI sync endpoints that cannot use async registry.

**Callers:** `app/hoc/api/cus/logs/cost_intelligence.py`

## PIN-520 Phase 2 (Bridge Completion)

This bridge was created as part of PIN-520 Phase 2 (Bridge Completion).
Resolves the missing bridge for analytics domain, which was causing
L5→L5 direct imports for cost anomaly detection.

## Singleton Access

```python
_bridge_instance: AnalyticsBridge | None = None

def get_analytics_bridge() -> AnalyticsBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = AnalyticsBridge()
    return _bridge_instance
```

---

*Generated: 2026-02-03*
