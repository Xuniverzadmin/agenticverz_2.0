# General — L5 Schemas (8 files)

**Domain:** general  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## agent.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/agent.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 229

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AgentStatus` |  | Agent operational status. |
| `PlannerType` |  | Supported planner backends. |
| `PlannerConfig` |  | Configuration for the agent's planner. |
| `RateLimitConfig` |  | Rate limiting configuration for an agent. |
| `BudgetConfig` | remaining_cents, usage_percent | Budget tracking configuration for an agent. |
| `AgentCapabilities` | can_use_skill, can_access_domain | Defines what an agent can and cannot do. |
| `AgentConfig` |  | Complete configuration for an agent. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_utc_now` | `() -> datetime` | no | Return timezone-aware UTC datetime. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `pydantic` | BaseModel, ConfigDict, Field | no |
| `retry` | RetryPolicy | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## artifact.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/artifact.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 156

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ArtifactType` |  | Type of artifact produced by a run. |
| `StorageBackend` |  | Where the artifact is stored. |
| `Artifact` | is_inline, has_content, get_inline_content | An artifact produced by a run or step. |
| `ArtifactReference` | from_artifact | Lightweight reference to an artifact. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional | no |
| `pydantic` | BaseModel, ConfigDict, Field | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## common.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/common.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 155

**Docstring:** Common Data Contracts - Shared Infrastructure Types

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HealthDTO` |  | GET /health response. |
| `HealthDetailDTO` |  | GET /health/detail response (if authenticated). |
| `ErrorDTO` |  | Standard error response. |
| `ValidationErrorDTO` |  | 422 Validation error response. |
| `PaginationMetaDTO` |  | Pagination metadata. |
| `CursorPaginationMetaDTO` |  | Cursor-based pagination metadata. |
| `ActionResultDTO` |  | Generic action result (activate, deactivate, etc.). |
| `ContractVersionDTO` |  | GET /api/v1/contracts/version response. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `pydantic` | BaseModel, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## plan.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/plan.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 257

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OnErrorPolicy` |  | What to do when a step fails. |
| `StepStatus` |  | Execution status of a plan step. |
| `ConditionOperator` |  | Operators for step conditions. |
| `StepCondition` |  | Condition for conditional step execution. |
| `PlanStep` | validate_fallback | A single step in an execution plan. |
| `PlanMetadata` |  | Metadata about the plan and how it was created. |
| `Plan` | validate_step_ids_unique, validate_dependencies, get_step, get_ready_steps | Complete execution plan for achieving a goal. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `pydantic` | BaseModel, ConfigDict, Field, field_validator | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `retry` | RetryPolicy | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## rac_models.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/rac_models.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 408

**Docstring:** Runtime Audit Contract (RAC) Models

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuditStatus` |  | Status of an audit expectation. |
| `AuditDomain` |  | Domains that participate in the audit contract. |
| `AuditAction` |  | Actions that can be expected/acked. |
| `AuditExpectation` | to_dict, from_dict, key | An expectation that an action MUST happen for a run. |
| `AckStatus` |  | Status of a domain acknowledgment. |
| `DomainAck` | is_success, is_rolled_back, to_dict, from_dict, key | Acknowledgment that a domain action has completed. |
| `ReconciliationResult` | is_clean, has_missing, has_drift, to_dict | Result of reconciling expectations against acknowledgments. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_run_expectations` | `(run_id: UUID, run_timeout_ms: int = 30000, grace_period_ms: int = 5000) -> List` | no | Create the standard set of expectations for a run. |
| `create_domain_ack` | `(run_id: UUID, domain: AuditDomain, action: AuditAction, result_id: Optional[str` | no | Create a domain acknowledgment. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `uuid` | UUID, uuid4 | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

### __all__ Exports
`AckStatus`, `AuditAction`, `AuditDomain`, `AuditStatus`, `AuditExpectation`, `DomainAck`, `ReconciliationResult`, `create_domain_ack`, `create_run_expectations`

---

## response.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/response.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 340

**Docstring:** Standard API Response Envelope

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ResponseMeta` |  | Metadata included with every response. |
| `ResponseEnvelope` |  | Standard API response envelope. |
| `ErrorDetail` |  | Structured error information. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `ok` | `(data: Any, request_id: Optional[str] = None) -> ResponseEnvelope` | no | Create a successful response envelope. |
| `error` | `(message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = N` | no | Create an error response envelope. |
| `paginated` | `(items: List[Any], total: int, page: int = 1, page_size: int = 20, request_id: O` | no | Create a paginated response envelope. |
| `wrap_dict` | `(data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]` | no | Wrap a dictionary in the standard envelope format. |
| `wrap_list` | `(items: List[Any], total: Optional[int] = None, page: Optional[int] = None, page` | no | Wrap a list in the standard envelope format. |
| `wrap_error` | `(message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = N` | no | Create an error response as a dictionary. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, Generic, List, Optional (+1) | no |
| `pydantic` | BaseModel, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

### Constants
`T`

---

## retry.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/retry.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 88

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BackoffStrategy` |  | Backoff strategy for retries. |
| `RetryPolicy` | get_delay, _fibonacci | Retry policy configuration for skills and steps. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum | no |
| `typing` | Optional | no |
| `pydantic` | BaseModel, ConfigDict, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## skill.py
**Path:** `backend/app/hoc/cus/general/L5_schemas/skill.py`  
**Layer:** L5_schemas | **Domain:** general | **Lines:** 457

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SkillStatus` |  | Skill execution status. |
| `SkillInputBase` |  | Base class for all skill inputs. |
| `SkillOutputBase` |  | Base class for all skill outputs. |
| `HttpMethod` |  | Supported HTTP methods. |
| `HttpCallInput` | validate_url | Input schema for http_call skill. |
| `HttpCallOutput` |  | Output schema for http_call skill. |
| `LLMProvider` |  | Supported LLM providers. |
| `LLMMessage` |  | A single message in the LLM conversation. |
| `LLMInvokeInput` |  | Input schema for llm_invoke skill. |
| `LLMInvokeOutput` |  | Output schema for llm_invoke skill. |
| `FileReadInput` |  | Input schema for file_read skill. |
| `FileReadOutput` |  | Output schema for file_read skill. |
| `FileWriteInput` |  | Input schema for file_write skill. |
| `FileWriteOutput` |  | Output schema for file_write skill. |
| `PostgresQueryInput` |  | Input schema for postgres_query skill. |
| `PostgresQueryOutput` |  | Output schema for postgres_query skill. |
| `JsonTransformInput` |  | Input schema for json_transform skill. |
| `JsonTransformOutput` |  | Output schema for json_transform skill. |
| `EmailSendInput` | normalize_recipients | Input schema for email_send skill. |
| `EmailSendOutput` |  | Output schema for email_send skill. |
| `KVOperation` |  | KV store operations. |
| `KVStoreInput` |  | Input schema for kv_store skill. |
| `KVStoreOutput` |  | Output schema for kv_store skill. |
| `SlackSendInput` |  | Input schema for slack_send skill. |
| `SlackSendOutput` |  | Output schema for slack_send skill. |
| `WebhookSendInput` | validate_webhook_url | Input schema for webhook_send skill. |
| `WebhookSendOutput` |  | Output schema for webhook_send skill. |
| `VoyageModel` |  | Voyage AI embedding models. |
| `VoyageInputType` |  | Input type for Voyage embeddings. |
| `VoyageEmbedInput` |  | Input schema for voyage_embed skill. |
| `VoyageEmbedOutput` |  | Output schema for voyage_embed skill. |
| `SkillMetadata` |  | Metadata about a registered skill. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Union | no |
| `pydantic` | BaseModel, ConfigDict, Field, field_validator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---
