# Apis — L6 Drivers (1 files)

**Domain:** apis  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## keys_driver.py
**Path:** `backend/app/hoc/cus/apis/L6_drivers/keys_driver.py`  
**Layer:** L6_drivers | **Domain:** apis | **Lines:** 196

**Docstring:** Keys Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KeysDriver` | __init__, fetch_keys_paginated, fetch_key_by_id, fetch_key_usage_today, update_key_frozen | L6 driver for API key data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_keys_driver` | `(session: Session) -> KeysDriver` | no | Factory function for KeysDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | List, Optional, Tuple | no |
| `sqlalchemy` | and_, desc, func, select | no |
| `sqlmodel` | Session | no |
| `app.models.killswitch` | ProxyCall | no |
| `app.models.tenant` | APIKey | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`KeysDriver`, `get_keys_driver`

---
