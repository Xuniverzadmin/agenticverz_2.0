# Integrations — L6 Drivers (1 files)

**Domain:** integrations  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## worker_registry_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/worker_registry_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 424

**Docstring:** Worker Registry Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WorkerRegistryError` |  | Base exception for worker registry errors. |
| `WorkerNotFoundError` |  | Raised when a worker is not found. |
| `WorkerUnavailableError` |  | Raised when a worker is not available. |
| `WorkerRegistryService` | __init__, get_worker, get_worker_or_raise, list_workers, list_available_workers, is_worker_available, get_worker_details, get_worker_summary (+10 more) | Service for worker registry operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_worker_registry_service` | `(session: Session) -> WorkerRegistryService` | no | Get a WorkerRegistryService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlmodel` | Session, select | no |
| `app.models.tenant` | WorkerConfig, WorkerRegistry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`WorkerRegistryService`, `WorkerRegistryError`, `WorkerNotFoundError`, `WorkerUnavailableError`, `get_worker_registry_service`

---
