# Account — L2 Apis (1 files)

**Domain:** account  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## memory_pins.py
**Path:** `backend/app/hoc/api/cus/account/memory_pins.py`  
**Layer:** L2_api | **Domain:** account | **Lines:** 578

**Docstring:** Memory Pins API - M7 Implementation

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MemoryPinCreate` | validate_key | Schema for creating/upserting a memory pin. |
| `MemoryPinResponse` |  | Schema for memory pin response. |
| `MemoryPinListResponse` |  | Schema for listing memory pins. |
| `MemoryPinDeleteResponse` |  | Schema for delete response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_feature_enabled` | `()` | no | Check if memory pins feature is enabled. |
| `extract_tenant_from_request` | `(request: Request, tenant_id: Optional[str] = None) -> str` | no | Extract tenant ID from request or parameter. |
| `write_memory_audit` | `(db, operation: str, tenant_id: str, key: str, success: bool, latency_ms: float,` | no | Write an audit entry to system.memory_audit. |
| `create_or_upsert_pin` | `(pin: MemoryPinCreate, request: Request, db = Depends(get_db_session))` | yes | Create or upsert a memory pin. |
| `get_pin` | `(key: str, request: Request, tenant_id: str = Query(default='global', descriptio` | yes | Get a memory pin by key. |
| `list_pins` | `(request: Request, tenant_id: str = Query(default='global', description='Tenant ` | yes | List memory pins for a tenant. |
| `delete_pin` | `(key: str, request: Request, tenant_id: str = Query(default='global', descriptio` | yes | Delete a memory pin by key. |
| `cleanup_expired_pins` | `(request: Request, tenant_id: Optional[str] = Query(default=None, description='L` | yes | Clean up expired memory pins. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field, field_validator | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.exc` | IntegrityError | no |
| `db` | get_session | yes |
| `schemas.response` | wrap_dict | yes |
| `utils.metrics_helpers` | get_or_create_counter, get_or_create_histogram | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`MEMORY_PINS_ENABLED`, `MEMORY_PINS_OPERATIONS`, `MEMORY_PINS_LATENCY`

---
