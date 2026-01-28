# Controls — L5 Other (2 files)

**Domain:** controls  
**Layer:** L5_other  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## customer_killswitch_read_engine.py
**Path:** `backend/app/hoc/cus/controls/L5_controls/engines/customer_killswitch_read_engine.py`  
**Layer:** L5_other | **Domain:** controls | **Lines:** 179

**Docstring:** Customer Killswitch Read Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KillswitchState` |  | Killswitch state information. |
| `GuardrailInfo` |  | Active guardrail information. |
| `IncidentStats` |  | Incident statistics for a tenant. |
| `KillswitchStatusInfo` |  | Complete killswitch status information. |
| `CustomerKillswitchReadService` | __init__, get_killswitch_status | Read operations for customer killswitch status. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_customer_killswitch_read_service` | `() -> CustomerKillswitchReadService` | no | Get the singleton CustomerKillswitchReadService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, List, Optional | no |
| `pydantic` | BaseModel | no |
| `app.hoc.cus.policies.controls.drivers.killswitch_read_driver` | KillswitchReadDriver, get_killswitch_read_driver | no |

### __all__ Exports
`CustomerKillswitchReadService`, `get_customer_killswitch_read_service`, `KillswitchState`, `GuardrailInfo`, `IncidentStats`, `KillswitchStatusInfo`

---

## killswitch_read_driver.py
**Path:** `backend/app/hoc/cus/controls/L5_controls/drivers/killswitch_read_driver.py`  
**Layer:** L5_other | **Domain:** controls | **Lines:** 229

**Docstring:** Killswitch Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KillswitchStateDTO` |  | Killswitch state information. |
| `GuardrailInfoDTO` |  | Active guardrail information. |
| `IncidentStatsDTO` |  | Incident statistics for a tenant. |
| `KillswitchStatusDTO` |  | Complete killswitch status information. |
| `KillswitchReadDriver` | __init__, _get_session, get_killswitch_status, _get_killswitch_state, _get_active_guardrails, _get_incident_stats | L6 driver for killswitch read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_killswitch_read_driver` | `(session: Optional[Session] = None) -> KillswitchReadDriver` | no | Get KillswitchReadDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | List, Optional | no |
| `pydantic` | BaseModel | no |
| `sqlalchemy` | and_, desc, func, select | no |
| `sqlmodel` | Session | no |
| `app.db` | get_session | no |
| `app.models.killswitch` | DefaultGuardrail, Incident, KillSwitchState | no |

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlalchemy import and_, desc, func, select` | L5 MUST NOT import sqlalchemy | Move DB logic to L6 driver | 36 |
| `from sqlmodel import Session` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver | 37 |
| `from app.models.killswitch import DefaultGuardrail, Incident, KillSwitchState` | L5 MUST NOT import L7 models directly | Route through L6 driver | 40 |

### __all__ Exports
`KillswitchReadDriver`, `get_killswitch_read_driver`, `KillswitchStateDTO`, `GuardrailInfoDTO`, `IncidentStatsDTO`, `KillswitchStatusDTO`

---
