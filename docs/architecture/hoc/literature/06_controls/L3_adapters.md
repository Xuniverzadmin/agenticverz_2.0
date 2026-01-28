# Controls — L3 Adapters (1 files)

**Domain:** controls  
**Layer:** L3_adapters  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

---

## customer_killswitch_adapter.py
**Path:** `backend/app/hoc/cus/controls/L3_adapters/customer_killswitch_adapter.py`  
**Layer:** L3_adapters | **Domain:** controls | **Lines:** 259

**Docstring:** Customer Killswitch Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CustomerKillswitchStatus` |  | Customer-safe killswitch status. |
| `CustomerKillswitchAction` |  | Result of a killswitch action. |
| `CustomerKillswitchAdapter` | __init__, _get_read_service, get_status, activate, deactivate | Boundary adapter for customer killswitch operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_customer_killswitch_adapter` | `(session: Session) -> CustomerKillswitchAdapter` | no | Get a CustomerKillswitchAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | List, Optional | no |
| `pydantic` | BaseModel | no |
| `sqlmodel` | Session | no |
| `app.models.killswitch` | TriggerType | no |
| `app.hoc.cus.general.L5_controls.engines.guard_write_engine` | GuardWriteService | no |
| `app.hoc.cus.controls.L5_controls.engines.customer_killswitch_read_engine` | CustomerKillswitchReadService, get_customer_killswitch_read_service | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlmodel import Session` | L3 MUST NOT access DB | Delegate to L5 engine or L6 driver | 38 |
| `from app.models.killswitch import TriggerType` | L3 MUST NOT import L7 models | Use L5 schemas for data contracts | 42 |

### __all__ Exports
`CustomerKillswitchAdapter`, `get_customer_killswitch_adapter`, `CustomerKillswitchStatus`, `CustomerKillswitchAction`

---
