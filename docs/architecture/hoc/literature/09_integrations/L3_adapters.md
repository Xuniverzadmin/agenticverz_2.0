# Integrations — L3 Adapters (21 files)

**Domain:** integrations  
**Layer:** L3_adapters  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

---

## cloud_functions_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/cloud_functions_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 313

**Docstring:** Google Cloud Functions Serverless Adapter (GAP-150)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CloudFunctionsAdapter` | __init__, connect, disconnect, invoke, invoke_batch, get_function_info, list_functions, function_exists | Google Cloud Functions serverless adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `base` | FunctionInfo, InvocationRequest, InvocationResult, InvocationType, ServerlessAdapter | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## customer_activity_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/customer_activity_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 332

**Docstring:** Customer Activity Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CustomerActivitySummary` |  | Customer-safe activity summary for list view. |
| `CustomerActivityDetail` |  | Customer-safe activity detail. |
| `CustomerActivityListResponse` |  | Paginated list of customer activities. |
| `CustomerActivityAdapter` | __init__, _get_facade, list_activities, get_activity, _to_customer_summary, _to_customer_detail | L3 boundary adapter for customer activity operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_customer_activity_adapter` | `() -> CustomerActivityAdapter` | no | Get the singleton CustomerActivityAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | TYPE_CHECKING, List, Optional | no |
| `pydantic` | BaseModel, Field | no |
| `app.hoc.cus.activity.L5_engines.activity_facade` | ActivityFacade, RunDetailResult, RunListResult, RunSummaryResult, get_activity_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### __all__ Exports
`CustomerActivityAdapter`, `CustomerActivitySummary`, `CustomerActivityDetail`, `CustomerActivityListResponse`, `get_customer_activity_adapter`

---

## customer_incidents_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/customer_incidents_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 398

**Docstring:** Customer Incidents Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CustomerIncidentSummary` |  | Customer-safe incident summary for list view. |
| `CustomerIncidentEvent` |  | Customer-safe timeline event. |
| `CustomerIncidentDetail` |  | Customer-safe incident detail. |
| `CustomerIncidentListResponse` |  | Paginated customer incident list. |
| `CustomerIncidentsAdapter` | __init__, list_incidents, get_incident, acknowledge_incident, resolve_incident | Boundary adapter for customer incident operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_translate_severity` | `(internal_severity: str) -> str` | no | Translate internal severity to calm customer vocabulary. |
| `_translate_status` | `(internal_status: str) -> str` | no | Translate internal status to customer vocabulary. |
| `get_customer_incidents_adapter` | `(session: Session) -> CustomerIncidentsAdapter` | no | Get a CustomerIncidentsAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | List, Optional | no |
| `pydantic` | BaseModel | no |
| `sqlmodel` | Session | no |
| `app.hoc.cus.incidents.L5_engines.incident_read_engine` | get_incident_read_service | no |
| `app.hoc.cus.incidents.L5_engines.incident_write_engine` | get_incident_write_service | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlmodel import Session` | L3 MUST NOT access DB | Delegate to L5 engine or L6 driver | 39 |

### __all__ Exports
`CustomerIncidentsAdapter`, `get_customer_incidents_adapter`, `CustomerIncidentSummary`, `CustomerIncidentEvent`, `CustomerIncidentDetail`, `CustomerIncidentListResponse`

---

## customer_keys_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/customer_keys_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 305

**Docstring:** Customer Keys Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CustomerKeyInfo` |  | Customer-safe API key information. |
| `CustomerKeyListResponse` |  | Customer key list response. |
| `CustomerKeyAction` |  | Result of a key action (freeze/unfreeze). |
| `CustomerKeysAdapter` | __init__, list_keys, get_key, freeze_key, unfreeze_key | Boundary adapter for customer API key operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_customer_keys_adapter` | `(session: Session) -> CustomerKeysAdapter` | no | Get a CustomerKeysAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | List, Optional | no |
| `pydantic` | BaseModel | no |
| `sqlmodel` | Session | no |
| `app.hoc.cus.api_keys.L5_engines.keys_engine` | get_keys_read_engine, get_keys_write_engine | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlmodel import Session` | L3 MUST NOT access DB | Delegate to L5 engine or L6 driver | 38 |

### __all__ Exports
`CustomerKeysAdapter`, `get_customer_keys_adapter`, `CustomerKeyInfo`, `CustomerKeyListResponse`, `CustomerKeyAction`

---

## customer_logs_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/customer_logs_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 410

**Docstring:** Customer Logs Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CustomerLogSummary` |  | Customer-safe log summary for list view. |
| `CustomerLogStep` |  | Customer-safe log step for detail view. |
| `CustomerLogDetail` |  | Customer-safe log detail. |
| `CustomerLogListResponse` |  | Paginated customer log list. |
| `CustomerLogsAdapter` | __init__, _get_service, list_logs, get_log, export_logs | Boundary adapter for customer logs operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_customer_logs_adapter` | `() -> CustomerLogsAdapter` | no | Get the singleton CustomerLogsAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `pydantic` | BaseModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### __all__ Exports
`CustomerLogsAdapter`, `get_customer_logs_adapter`, `CustomerLogSummary`, `CustomerLogStep`, `CustomerLogDetail`, `CustomerLogListResponse`

---

## customer_policies_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/customer_policies_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 279

**Docstring:** Customer Policies Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CustomerBudgetConstraint` |  | Customer-visible budget constraint. |
| `CustomerRateLimit` |  | Customer-visible rate limit. |
| `CustomerGuardrail` |  | Customer-visible guardrail configuration. |
| `CustomerPolicyConstraints` |  | Customer-visible policy constraints summary. |
| `CustomerPoliciesAdapter` | __init__, _get_service, get_policy_constraints, get_guardrail_detail, _to_customer_policy_constraints, _to_customer_guardrail | Boundary adapter for customer policy constraints. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_customer_policies_adapter` | `() -> CustomerPoliciesAdapter` | no | Get the singleton CustomerPoliciesAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | List, Optional | no |
| `pydantic` | BaseModel | no |
| `app.hoc.cus.policies.L5_engines.customer_policy_read_engine` | CustomerPolicyReadService, GuardrailSummary, PolicyConstraints, get_customer_policy_read_service | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### __all__ Exports
`CustomerPoliciesAdapter`, `get_customer_policies_adapter`, `CustomerBudgetConstraint`, `CustomerRateLimit`, `CustomerGuardrail`, `CustomerPolicyConstraints`

---

## file_storage_base.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/file_storage_base.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 299

**Docstring:** File Storage Base Adapter

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FileMetadata` | to_dict | Metadata for a stored file. |
| `UploadResult` | success | Result of an upload operation. |
| `DownloadResult` | success | Result of a download operation. |
| `ListResult` |  | Result of a list operation. |
| `FileStorageAdapter` | connect, disconnect, upload, download, download_stream, delete, delete_many, exists (+5 more) | Abstract base class for file storage adapters. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime | no |
| `typing` | Any, AsyncIterator, BinaryIO, Dict, List (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## founder_ops_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/founder_ops_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 145

**Docstring:** Founder Ops Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FounderIncidentSummaryView` |  | Founder-facing incident summary. |
| `FounderIncidentsSummaryResponse` |  | Response for GET /ops/incidents/summary. |
| `FounderOpsAdapter` | to_summary_view, to_summary_response | Boundary adapter for Founder Ops incident views. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | List | no |
| `app.hoc.fdr.ops.schemas.ops_domain_models` | OpsIncident | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## gcs_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/gcs_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 442

**Docstring:** Google Cloud Storage File Storage Adapter (GAP-148)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GCSAdapter` | __init__, connect, disconnect, upload, download, download_stream, delete, delete_many (+5 more) | Google Cloud Storage file storage adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, AsyncIterator, BinaryIO, Dict, List (+1) | no |
| `base` | DownloadResult, FileMetadata, FileStorageAdapter, ListResult, UploadResult | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## lambda_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/lambda_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 281

**Docstring:** AWS Lambda Serverless Adapter (GAP-149)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LambdaAdapter` | __init__, connect, disconnect, invoke, invoke_batch, get_function_info, list_functions, function_exists | AWS Lambda serverless adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `base64` | base64 | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `base` | FunctionInfo, InvocationRequest, InvocationResult, InvocationType, ServerlessAdapter | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## pgvector_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/pgvector_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 378

**Docstring:** PGVector Production Adapter (GAP-146)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PGVectorAdapter` | __init__, connect, disconnect, upsert, query, delete, get_stats, create_namespace (+2 more) | PGVector production adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `base` | DeleteResult, IndexStats, QueryResult, UpsertResult, VectorRecord (+1) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## pinecone_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/pinecone_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 283

**Docstring:** Pinecone Vector Store Adapter (GAP-144)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PineconeAdapter` | __init__, connect, disconnect, upsert, query, delete, get_stats, create_namespace (+2 more) | Pinecone vector store adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `base` | DeleteResult, IndexStats, QueryResult, UpsertResult, VectorRecord (+1) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## runtime_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/runtime_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 215

**Docstring:** Runtime Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RuntimeAdapter` | __init__, query, get_supported_queries, describe_skill, list_skills, get_skill_descriptors, get_resource_contract, get_capabilities | L3 Boundary Adapter for runtime operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_runtime_adapter` | `() -> RuntimeAdapter` | no | Factory function to get RuntimeAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.commands.runtime_command` | CapabilitiesInfo, QueryResult, ResourceContractInfo, SkillInfo, execute_query (+6) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### __all__ Exports
`RuntimeAdapter`, `get_runtime_adapter`

---

## s3_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/s3_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 393

**Docstring:** AWS S3 File Storage Adapter (GAP-147)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `S3Adapter` | __init__, connect, disconnect, upload, download, download_stream, delete, delete_many (+5 more) | AWS S3 file storage adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, AsyncIterator, BinaryIO, Dict, List (+1) | no |
| `base` | DownloadResult, FileMetadata, FileStorageAdapter, ListResult, UploadResult | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## serverless_base.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/serverless_base.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 236

**Docstring:** Serverless Base Adapter

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `InvocationType` |  | Type of function invocation. |
| `InvocationRequest` | to_dict | Request to invoke a serverless function. |
| `InvocationResult` | success, to_dict | Result of a serverless function invocation. |
| `FunctionInfo` | to_dict | Information about a serverless function. |
| `ServerlessAdapter` | connect, disconnect, invoke, invoke_batch, get_function_info, list_functions, function_exists, health_check | Abstract base class for serverless adapters. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## slack_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/slack_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 305

**Docstring:** Slack Notification Adapter (GAP-152)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SlackAdapter` | __init__, connect, disconnect, send, _build_blocks, _get_priority_emoji, send_batch, get_status (+1 more) | Slack notification adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |
| `base` | NotificationAdapter, NotificationMessage, NotificationPriority, NotificationResult, NotificationStatus | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## smtp_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/smtp_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 259

**Docstring:** SMTP Notification Adapter (GAP-151)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SMTPAdapter` | __init__, connect, disconnect, send, _build_email, send_batch, get_status | SMTP notification adapter for email. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `os` | os | no |
| `email.mime.multipart` | MIMEMultipart | no |
| `email.mime.text` | MIMEText | no |
| `email.mime.base` | MIMEBase | no |
| `email` | encoders | no |
| `typing` | Dict, List, Optional | no |
| `uuid` | uuid | no |
| `base` | NotificationAdapter, NotificationMessage, NotificationResult, NotificationStatus | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## vector_stores_base.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/vector_stores_base.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 265

**Docstring:** Vector Store Base Adapter

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `VectorRecord` | to_dict | A single vector record. |
| `QueryResult` | to_dict | Result of a vector similarity query. |
| `UpsertResult` | success | Result of an upsert operation. |
| `DeleteResult` | success | Result of a delete operation. |
| `IndexStats` | to_dict | Statistics about a vector index. |
| `VectorStoreAdapter` | connect, disconnect, upsert, query, delete, get_stats, health_check, create_namespace (+2 more) | Abstract base class for vector store adapters. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## weaviate_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/weaviate_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 399

**Docstring:** Weaviate Vector Store Adapter (GAP-145)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WeaviateAdapter` | __init__, connect, _create_collection, disconnect, upsert, query, _build_filter, delete (+4 more) | Weaviate vector store adapter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `base` | DeleteResult, IndexStats, QueryResult, UpsertResult, VectorRecord (+1) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## webhook_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/webhook_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 472

**Docstring:** Webhook Notification Adapter with Retry Logic (GAP-153)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CircuitState` |  | Circuit breaker states. |
| `CircuitBreakerConfig` |  | Configuration for circuit breaker. |
| `CircuitBreaker` | can_execute, record_success, record_failure | Circuit breaker for webhook endpoint. |
| `WebhookDeliveryAttempt` |  | Record of a webhook delivery attempt. |
| `WebhookDelivery` | to_dict | Full record of webhook delivery with all attempts. |
| `WebhookAdapter` | __init__, connect, disconnect, _get_circuit_breaker, _sign_payload, send, _deliver_with_retry, _attempt_delivery (+4 more) | Webhook notification adapter with retry logic. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `time` | time | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, List, Optional | no |
| `uuid` | uuid | no |
| `base` | NotificationAdapter, NotificationMessage, NotificationResult, NotificationStatus, RetryConfig | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## workers_adapter.py
**Path:** `backend/app/hoc/cus/integrations/L3_adapters/workers_adapter.py`  
**Layer:** L3_adapters | **Domain:** integrations | **Lines:** 208

**Docstring:** Workers Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WorkersAdapter` | execute_worker, replay_execution, calculate_cost_cents, convert_brand_request | Boundary adapter for worker operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_workers_adapter` | `() -> WorkersAdapter` | no | Get the singleton WorkersAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Optional | no |
| `app.commands.worker_execution_command` | ReplayResult, WorkerExecutionResult, calculate_cost_cents, convert_brand_request, execute_worker (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### __all__ Exports
`WorkersAdapter`, `get_workers_adapter`, `WorkerExecutionResult`, `ReplayResult`

---
