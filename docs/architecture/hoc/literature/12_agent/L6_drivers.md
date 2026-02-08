# Agent — L6 Drivers (3 files)

**Domain:** agent  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## discovery_stats_driver.py
**Path:** `backend/app/hoc/cus/agent/L6_drivers/discovery_stats_driver.py`  
**Layer:** L6_drivers | **Domain:** agent | **Lines:** 119

**Docstring:** Discovery Stats Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DiscoveryStatsDriver` | get_stats, _get_by_artifact, _get_by_signal_type, _get_by_status | Pure data access for discovery_ledger statistics. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_discovery_stats_driver` | `() -> DiscoveryStatsDriver` | no | Get or create the singleton DiscoveryStatsDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## platform_driver.py
**Path:** `backend/app/hoc/cus/agent/L6_drivers/platform_driver.py`  
**Layer:** L6_drivers | **Domain:** agent | **Lines:** 196

**Docstring:** Platform Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlatformDriver` | __init__, _get_session, get_blca_status, get_lifecycle_coherence, get_blocked_scopes, get_capability_signals, count_blocked_for_capability | L6 driver for platform health queries. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_platform_driver` | `(session: Optional[Session] = None) -> PlatformDriver` | no | Get PlatformDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional, Set (+1) | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |
| `app.db` | get_session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`PlatformDriver`, `get_platform_driver`

---

## routing_driver.py
**Path:** `backend/app/hoc/cus/agent/L6_drivers/routing_driver.py`  
**Layer:** L6_drivers | **Domain:** agent | **Lines:** 186

**Docstring:** Routing Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RoutingDriver` | __init__, get_routing_stats, get_routing_decision, update_agent_sba | L6 driver for routing and agent strategy DB operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_routing_driver` | `(session: AsyncSession) -> RoutingDriver` | no | Get RoutingDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `typing` | Any, Dict, Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`RoutingDriver`, `get_routing_driver`

---
