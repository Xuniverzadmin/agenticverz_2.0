# Account — L2 Apis (1 files)

**Domain:** account  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

---

## memory_pins.py
**Path:** `backend/app/hoc/api/cus/account/memory_pins.py`  
**Layer:** L2_api | **Domain:** account | **Lines:** 363

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
| `extract_tenant_from_request` | `(request: Request, tenant_id: Optional[str] = None) -> str` | no | Extract tenant ID from request or parameter. |
| `_pin_row_to_response` | `(pin: Any) -> MemoryPinResponse` | no | Convert a MemoryPinRow dataclass to response model. |
| `create_or_upsert_pin` | `(pin: MemoryPinCreate, request: Request, session = Depends(get_session_dep))` | yes | Create or upsert a memory pin. |
| `get_pin` | `(key: str, request: Request, tenant_id: str = Query(default='global', descriptio` | yes | Get a memory pin by key. |
| `list_pins` | `(request: Request, tenant_id: str = Query(default='global', description='Tenant ` | yes | List memory pins for a tenant. |
| `delete_pin` | `(key: str, request: Request, tenant_id: str = Query(default='global', descriptio` | yes | Delete a memory pin by key. |
| `cleanup_expired_pins` | `(request: Request, tenant_id: Optional[str] = Query(default=None, description='L` | yes | Clean up expired memory pins. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field, field_validator | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

---
