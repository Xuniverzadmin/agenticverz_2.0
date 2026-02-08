# Api_Keys — L5 Engines (2 files)

**Domain:** api_keys  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## api_keys_facade.py
**Path:** `backend/app/hoc/cus/api_keys/L5_engines/api_keys_facade.py`  
**Layer:** L5_engines | **Domain:** api_keys | **Lines:** 237

**Docstring:** API Keys Domain Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `APIKeySummaryResult` |  | API key summary for list view. |
| `APIKeysListResult` |  | API keys list response. |
| `APIKeyDetailResult` |  | API key detail response. |
| `APIKeysFacade` | __init__, list_api_keys, get_api_key_detail | Unified facade for API key management. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_api_keys_facade` | `() -> APIKeysFacade` | no | Get the singleton APIKeysFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `json` | json | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.api_keys.L6_drivers.api_keys_facade_driver` | APIKeysFacadeDriver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`APIKeysFacade`, `get_api_keys_facade`, `APIKeySummaryResult`, `APIKeysListResult`, `APIKeyDetailResult`

---

## keys_engine.py
**Path:** `backend/app/hoc/cus/api_keys/L5_engines/keys_engine.py`  
**Layer:** L5_engines | **Domain:** api_keys | **Lines:** 234

**Docstring:** Keys Engine (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KeysReadEngine` | __init__, list_keys, get_key, get_key_usage_today | L4 engine for API key read operations. |
| `KeysWriteEngine` | __init__, freeze_key, unfreeze_key | L4 engine for API key write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_keys_read_engine` | `(session: Session) -> KeysReadEngine` | no | Factory function to get KeysReadEngine instance. |
| `get_keys_write_engine` | `(session: Session) -> KeysWriteEngine` | no | Factory function to get KeysWriteEngine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, List, Optional, Tuple | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.api_keys.L6_drivers.keys_driver` | KeysDriver, KeySnapshot, KeyUsageSnapshot, get_keys_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`KeysReadEngine`, `KeysWriteEngine`, `get_keys_read_engine`, `get_keys_write_engine`, `KeySnapshot`, `KeyUsageSnapshot`

---
