# Integrations — L2 Apis (3 files)

**Domain:** integrations  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## cus_telemetry.py
**Path:** `backend/app/hoc/api/cus/integrations/cus_telemetry.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 337

**Docstring:** Customer LLM Telemetry Ingestion API

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_telemetry_service` | `() -> CusTelemetryService` | no | Dependency to get telemetry service instance. |
| `get_integration_context` | `(request: Request, x_cus_integration_key: Optional[str] = Header(None, alias='X-` | yes | Extract and validate integration context from request. |
| `ingest_llm_usage` | `(payload: CusLLMUsageIngest, ctx: dict = Depends(get_integration_context), servi` | yes | Ingest a single LLM usage telemetry record. |
| `ingest_llm_usage_batch` | `(payload: CusLLMUsageBatchIngest, ctx: dict = Depends(get_integration_context), ` | yes | Ingest a batch of LLM usage telemetry records. |
| `get_usage_summary` | `(request: Request, integration_id: Optional[str] = Query(None, description='Filt` | yes | Get aggregated usage summary for dashboard. |
| `get_usage_history` | `(request: Request, integration_id: Optional[str] = Query(None, description='Filt` | yes | Get detailed usage history records. |
| `get_daily_aggregates` | `(request: Request, integration_id: Optional[str] = Query(None, description='Filt` | yes | Get daily aggregated usage for charts. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | date, timedelta | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, Header, HTTPException, Query (+1) | no |
| `app.schemas.cus_schemas` | CusLLMUsageBatchIngest, CusLLMUsageIngest, CusLLMUsageResponse, CusUsageSummary | no |
| `app.schemas.response` | wrap_dict, wrap_error, wrap_list | no |
| `app.hoc.cus.activity.L5_engines.cus_telemetry_service` | CusTelemetryService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.hoc.cus.activity.L5_engines.cus_telemetry_service import CusTelemetryService` | L2 MUST NOT import L5 directly | Route through L3 adapter | 47 |

---

## protection_dependencies.py
**Path:** `backend/app/hoc/api/cus/integrations/protection_dependencies.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 242

**Docstring:** Phase-7 Protection Dependencies — FastAPI Integration

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProtectionContext` |  | Protection context for a request. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `is_exempt_endpoint` | `(path: str) -> bool` | no | Check if an endpoint is exempt from protection. |
| `check_protection` | `(request: Request) -> ProtectionContext` | no | FastAPI dependency: Run protection checks for current request. |
| `require_protection_allow` | `(request: Request) -> ProtectionContext` | no | FastAPI dependency: Require protection checks to pass. |
| `emit_protection_event` | `(context: ProtectionContext) -> dict` | no | Emit a structured protection event for observability. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |
| `fastapi` | Request, HTTPException | no |
| `logging` | logging | no |
| `app.protection.decisions` | Decision, ProtectionResult, AnomalySignal, allow | no |
| `app.protection.provider` | get_protection_provider | no |
| `app.auth.onboarding_state` | OnboardingState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`EXEMPT_PREFIXES`

### __all__ Exports
`ProtectionContext`, `check_protection`, `require_protection_allow`, `emit_protection_event`, `is_exempt_endpoint`, `EXEMPT_PREFIXES`

---

## session_context.py
**Path:** `backend/app/hoc/api/cus/integrations/session_context.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 156

**Docstring:** Session Context API

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_session_context` | `(request: Request) -> Dict[str, Any]` | yes | Get verified session context for the current authenticated user. |
| `_get_onboarding_state` | `(tenant_id: str) -> str` | no | Get onboarding state for a tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Request, HTTPException | no |
| `app.auth.contexts` | FounderAuthContext, HumanAuthContext, MachineCapabilityContext | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.auth.lifecycle_provider` | get_lifecycle_provider | no |
| `app.auth.onboarding_state` | OnboardingState | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---
