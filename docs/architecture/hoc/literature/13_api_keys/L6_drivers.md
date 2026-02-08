# Api_Keys — L6 Drivers (2 files)

**Domain:** api_keys  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## api_keys_facade_driver.py
**Path:** `backend/app/hoc/cus/api_keys/L6_drivers/api_keys_facade_driver.py`  
**Layer:** L6_drivers | **Domain:** api_keys | **Lines:** 209

**Docstring:** API Keys Facade Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `APIKeySnapshot` |  | Raw API key data from DB for list view. |
| `APIKeyDetailSnapshot` |  | Detailed API key data from DB. |
| `APIKeysFacadeDriver` | fetch_api_keys, count_api_keys, fetch_api_key_by_id | API Keys Facade Driver - Pure data access layer. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | List, Optional | no |
| `sqlalchemy` | func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.tenant` | APIKey | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`APIKeysFacadeDriver`, `APIKeySnapshot`, `APIKeyDetailSnapshot`

---

## keys_driver.py
**Path:** `backend/app/hoc/cus/api_keys/L6_drivers/keys_driver.py`  
**Layer:** L6_drivers | **Domain:** api_keys | **Lines:** 297

**Docstring:** Keys Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KeySnapshot` |  | API key snapshot for engine operations. |
| `KeyUsageSnapshot` |  | Key usage statistics from DB. |
| `KeysDriver` | __init__, fetch_keys, count_keys, fetch_key_by_id, fetch_key_usage, fetch_key_for_update, update_key_frozen, update_key_unfrozen | Keys Driver - Pure data access layer. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_keys_driver` | `(session: Session) -> KeysDriver` | no | Factory function to get KeysDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | List, Optional, Tuple | no |
| `sqlalchemy` | and_, desc, func, select | no |
| `sqlmodel` | Session | no |
| `app.models.killswitch` | ProxyCall | no |
| `app.models.tenant` | APIKey | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`KeysDriver`, `get_keys_driver`, `get_keys_read_driver`, `get_keys_write_driver`, `KeySnapshot`, `KeyUsageSnapshot`

---
