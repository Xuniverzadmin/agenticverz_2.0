# Controls — L2 Apis (1 files)

**Domain:** controls  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

---

## controls.py
**Path:** `backend/app/hoc/api/cus/controls/controls.py`  
**Layer:** L2_api | **Domain:** controls | **Lines:** 271

**Docstring:** Controls API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `UpdateControlRequest` |  | Request to update a control. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_controls` | `(control_type: Optional[str] = Query(None, description='Filter by type'), state:` | yes | List controls (GAP-123). |
| `get_status` | `(ctx: TenantContext = Depends(get_tenant_context), _tier: None = Depends(require` | yes | Get overall control status. |
| `get_control` | `(control_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None ` | yes | Get a specific control. |
| `update_control` | `(control_id: str, request: UpdateControlRequest, ctx: TenantContext = Depends(ge` | yes | Update a control. |
| `enable_control` | `(control_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None ` | yes | Enable a control. |
| `disable_control` | `(control_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None ` | yes | Disable a control. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

---
