# overview_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/overview_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-03
**Reference:** PIN-520 (L4 Uniformity Initiative), PIN-504 (C4 Loop Model)

---

## Placement Card

```
File:            overview_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Overview domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/overview_handler.py
Outbound:        overview/L5_engines/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for overview L5 engine access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for overview L5 engines.
Implements the Switchboard Pattern (Law 4 - PIN-507):

- Never accepts session parameters
- Returns module references for lazy access
- Handler binds session (Law 4 responsibility)
- No retry logic, no decisions, no state

Overview is a minimal domain serving as a dashboard aggregation point.
It has a single facade that aggregates data from other domains via hoc_spine coordinators.

## Capabilities

| Method | Returns | L5 Module |
|--------|---------|-----------|
| `overview_capability()` | `overview_facade` | `get_highlights`, `get_dashboard_data`, `get_summary` |
| `dashboard_capability()` | `overview_facade` | Semantic alias for dashboard-focused operations |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.overview_bridge import (
    get_overview_bridge,
)

bridge = get_overview_bridge()

# Get overview capability
facade = bridge.overview_capability()
highlights = await facade.get_highlights(session, tenant_id)

# Dashboard operations (same facade, semantic clarity)
dashboard = bridge.dashboard_capability()
data = await dashboard.get_dashboard_data(session, tenant_id)
```

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods | CI check 19 |
| Returns modules (not sessions) | Code review |
| Lazy imports only | No top-level L5 imports |
| L4 handlers only | Forbidden import check |

## Minimal Domain Note

Overview is intentionally minimal (2 capabilities) because:
1. It's an aggregation point, not a data owner
2. Cross-domain queries flow through L4 coordinators
3. Domain-specific data fetches use their own bridges

## PIN-520 Phase 2

This bridge was created as part of PIN-520 Phase 2 (Bridge Completion).
Completes the bridge coverage for all 10 customer domains.

## Singleton Access

```python
_bridge_instance: OverviewBridge | None = None

def get_overview_bridge() -> OverviewBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = OverviewBridge()
    return _bridge_instance
```

---

*Generated: 2026-02-03*
