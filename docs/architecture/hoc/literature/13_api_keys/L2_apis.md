# Api_Keys — L2 Apis (2 files)

**Domain:** api_keys  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

---

## auth_helpers.py
**Path:** `backend/app/hoc/api/cus/api_keys/auth_helpers.py`  
**Layer:** L2_api | **Domain:** api_keys | **Lines:** 78

**Docstring:** API Auth Helpers - Console Authentication

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `verify_console_api_key` | `(x_api_key: Optional[str] = Header(None, alias='X-API-Key')) -> str` | yes | Verify API key for console endpoints. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `os` | os | no |
| `typing` | Optional | no |
| `fastapi` | Header, HTTPException, status | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`AOS_API_KEY`

### __all__ Exports
`verify_console_api_key`

---

## embedding.py
**Path:** `backend/app/hoc/api/cus/api_keys/embedding.py`  
**Layer:** L2_api | **Domain:** api_keys | **Lines:** 513

**Docstring:** API endpoints for embedding operations and quota management.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EmbeddingQuotaResponse` |  | Response schema for embedding quota status. |
| `EmbeddingConfigResponse` |  | Response schema for embedding configuration. |
| `IAECComposeRequest` |  | Request schema for IAEC composition (v3.0). |
| `TemporalSignatureResponse` |  | Temporal signature for drift control. |
| `PolicyEncodingResponse` |  | Policy slot encoding. |
| `IAECComposeResponse` |  | Response schema for IAEC composition (v3.2). |
| `IAECDecomposeRequest` |  | Request schema for IAEC decomposition. |
| `IAECDecomposeResponse` |  | Response schema for IAEC decomposition (v3.0). |
| `IAECVerifyRequest` |  | Request for integrity verification. |
| `IAECVerifyResponse` |  | Response for integrity verification. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_embedding_quota` | `(_api_key: str = Depends(verify_api_key)) -> EmbeddingQuotaResponse` | yes | Get current embedding quota status. |
| `get_embedding_config` | `(_api_key: str = Depends(verify_api_key)) -> EmbeddingConfigResponse` | yes | Get embedding configuration. |
| `embedding_health` | `() -> dict` | yes | Quick health check for embedding subsystem. |
| `embedding_cache_stats` | `(_api_key: str = Depends(verify_api_key)) -> dict` | yes | Get embedding cache statistics. |
| `clear_embedding_cache` | `(_api_key: str = Depends(verify_api_key)) -> dict` | yes | Clear all embedding cache entries. |
| `compose_embedding` | `(request: IAECComposeRequest, _api_key: str = Depends(verify_api_key)) -> IAECCo` | yes | Compose an instruction-aware embedding using IAEC v3.0. |
| `decompose_embedding` | `(request: IAECDecomposeRequest, _api_key: str = Depends(verify_api_key)) -> IAEC` | yes | Decompose an IAEC embedding back into its constituent slots (v3.0). |
| `get_iaec_instructions` | `(_api_key: str = Depends(verify_api_key)) -> dict` | yes | Get available IAEC instruction types and their weights. |
| `get_iaec_segment_info` | `(_api_key: str = Depends(verify_api_key)) -> dict` | yes | Get IAEC v3.0 segmentation configuration. |
| `check_mismatch` | `(instruction: str, query: str, _api_key: str = Depends(verify_api_key)) -> dict` | yes | Check instruction-query semantic compatibility (v3.1). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends | no |
| `pydantic` | BaseModel | no |
| `app.auth` | verify_api_key | no |
| `app.schemas.response` | wrap_dict | no |
| `app.memory.embedding_metrics` | EMBEDDING_DAILY_QUOTA, VECTOR_SEARCH_ENABLED, VECTOR_SEARCH_FALLBACK, get_embedding_quota_status | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

---
