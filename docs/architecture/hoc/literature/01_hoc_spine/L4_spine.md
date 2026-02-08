# Hoc_Spine — L4 Spine (155 files)

**Domain:** hoc_spine  
**Layer:** L4_spine  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

---

## account_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/account_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 70

**Docstring:** Account Bridge (PIN-513)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccountBridge` | account_query_capability, notifications_capability, tenant_capability, billing_provider_capability, rbac_engine_capability | Capabilities for account domain. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_account_bridge` | `() -> AccountBridge` | no | Get the singleton AccountBridge instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AccountBridge`, `get_account_bridge`

---

## account_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/account_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 290

**Docstring:** Account Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccountQueryHandler` | execute | Handler for account.query operations. |
| `AccountNotificationsHandler` | execute | Handler for account.notifications operations. |
| `AccountBillingProviderHandler` | execute | Handler for account.billing.provider operations. |
| `AccountMemoryPinsHandler` | execute | Handler for account.memory_pins operations. |
| `AccountTenantHandler` | execute | Handler for account.tenant operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register account operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## activity_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/activity_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 100

**Docstring:** Activity Bridge (PIN-510)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ActivityBridge` | activity_query_capability | Capabilities for activity domain. Max 5 methods. |
| `ActivityEngineBridge` | run_evidence_coordinator_capability, run_proof_coordinator_capability, signal_feedback_coordinator_capability | Extended capabilities for activity domain coordinators. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_activity_bridge` | `() -> ActivityBridge` | no | Get the singleton ActivityBridge instance. |
| `get_activity_engine_bridge` | `() -> ActivityEngineBridge` | no | Get the singleton ActivityEngineBridge instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`ActivityBridge`, `get_activity_bridge`, `ActivityEngineBridge`, `get_activity_engine_bridge`

---

## activity_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 322

**Docstring:** Activity Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ActivityQueryHandler` | execute | Handler for activity.query operations. |
| `ActivitySignalFingerprintHandler` | execute | Handler for activity.signal_fingerprint operations. |
| `ActivitySignalFeedbackHandler` | execute | Handler for activity.signal_feedback operations. |
| `ActivityTelemetryHandler` | execute | Handler for activity.telemetry operations. |
| `ActivityDiscoveryHandler` | execute | Handler for activity.discovery operations. |
| `ActivityOrphanRecoveryHandler` | execute | Handler for activity.orphan_recovery operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register activity domain handlers. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## agent.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/agent.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 229

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## agent_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/agent_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 946

**Docstring:** Agent Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AgentDiscoveryStatsHandler` | execute | Handler for agent.discovery_stats operations. |
| `AgentRoutingHandler` | execute | Handler for agent.routing operations. |
| `AgentStrategyHandler` | execute | Handler for agent.strategy operations. |
| `AgentJobHandler` | execute, _simulate, _create, _get, _cancel, _claim_item, _complete_item, _fail_item | Handler for agents.job operations. |
| `AgentBlackboardHandler` | execute | Handler for agents.blackboard operations. |
| `AgentInstanceHandler` | execute | Handler for agents.instance operations. |
| `AgentMessageHandler` | execute | Handler for agents.message operations. |
| `AgentActivityHandler` | execute, _costs, _spending, _retries, _blockers | Handler for agents.activity operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register agent operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## alert_delivery.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/alert_delivery.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 168

**Docstring:** Alert Delivery Adapter (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DeliveryResult` |  | Result of alert delivery attempt. |
| `AlertDeliveryAdapter` | __init__, _get_client, close, send_alert | Adapter for HTTP alert delivery. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_delivery_adapter` | `(alertmanager_url: Optional[str] = None, timeout_seconds: float = 30.0) -> Alert` | no | Factory function to get AlertDeliveryAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `httpx` | httpx | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AlertDeliveryAdapter`, `DeliveryResult`, `get_alert_delivery_adapter`

---

## alert_driver.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/alert_driver.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 342

**Docstring:** Alert Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertDriver` | __init__, fetch_pending_alerts, fetch_queue_stats, update_alert_sent, update_alert_retry, update_alert_failed, mark_incident_alert_sent, insert_alert (+2 more) | L6 driver for alert queue data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_driver` | `(session: AsyncSession) -> AlertDriver` | no | Factory function to get AlertDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | and_, delete, func, select, update | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.costsim_cb` | CostSimAlertQueueModel, CostSimCBIncidentModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AlertDriver`, `get_alert_driver`

---

## alert_emitter.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/alert_emitter.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 479

**Docstring:** Alert Emitter Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertEmitter` | __init__, emit_near_threshold, emit_breach, _send_via_channel, _send_ui_notification, _send_webhook, _send_slack, _send_email (+2 more) | Emits alerts for threshold events. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_emitter` | `() -> AlertEmitter` | no | Get or create AlertEmitter singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Optional | no |
| `httpx` | httpx | no |
| `sqlmodel` | Session | no |
| `app.db` | engine | no |
| `app.models.alert_config` | AlertChannel, AlertConfig | no |
| `app.models.threshold_signal` | SignalType, ThresholdSignal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## alerts_facade.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/alerts_facade.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 679

**Docstring:** Alerts Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertSeverity` |  | Alert severity levels. |
| `AlertStatus` |  | Alert status. |
| `AlertRule` | to_dict | Alert rule definition. |
| `AlertEvent` | to_dict | Alert event (history entry). |
| `AlertRoute` | to_dict | Alert routing rule. |
| `AlertsFacade` | __init__, create_rule, list_rules, get_rule, update_rule, delete_rule, list_history, get_event (+7 more) | Facade for alert operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alerts_facade` | `() -> AlertsFacade` | no | Get the alerts facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## analytics_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/analytics_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 221

**Docstring:** Analytics Bridge (L4 Coordinator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsBridge` | config_capability, sandbox_capability, canary_capability, divergence_capability, datasets_capability, cost_write_capability | Analytics domain capability factory. |
| `AnalyticsEngineBridge` | anomaly_coordinator_capability, detection_facade_capability, alert_driver_capability, alert_adapter_factory_capability | Extended capabilities for analytics domain coordinators. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_analytics_bridge` | `() -> AnalyticsBridge` | no | Get the analytics bridge singleton. |
| `get_analytics_engine_bridge` | `() -> AnalyticsEngineBridge` | no | Get the singleton AnalyticsEngineBridge instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AnalyticsBridge`, `get_analytics_bridge`, `AnalyticsEngineBridge`, `get_analytics_engine_bridge`

---

## analytics_config_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_config_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 62

**Docstring:** Analytics Config Handler (PIN-513 Batch 3A2 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsConfigHandler` | get_config, is_v2_sandbox_enabled, is_v2_disabled_by_drift, get_commit_sha | L4 handler: CostSim configuration read logic. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## analytics_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 478

**Docstring:** Analytics Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FeedbackReadHandler` | execute | Handler for analytics.feedback operations. |
| `AnalyticsQueryHandler` | execute | Handler for analytics.query operations. |
| `AnalyticsDetectionHandler` | execute | Handler for analytics.detection operations. |
| `CanaryReportHandler` | execute | Handler for analytics.canary_reports operations. |
| `CanaryRunHandler` | execute | Handler for analytics.canary operations. |
| `CostsimStatusHandler` | execute | Handler for analytics.costsim.status operations. |
| `CostsimSimulateHandler` | execute | Handler for analytics.costsim.simulate operations. |
| `CostsimDivergenceHandler` | execute | Handler for analytics.costsim.divergence operations. |
| `CostsimDatasetsHandler` | execute | Handler for analytics.costsim.datasets operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register analytics operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## analytics_metrics_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_metrics_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 40

**Docstring:** Analytics Metrics Handler (PIN-513 Batch 3A4 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsMetricsHandler` | get_metrics, get_alert_rules | L4 handler: CostSim metrics and alert rules. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## analytics_prediction_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_prediction_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 239

**Docstring:** Analytics Prediction Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsPredictionHandler` | execute, _predict_failure, _predict_cost_overrun, _run_cycle, _get_summary | Handler for analytics.prediction operations. |
| `AnalyticsPredictionReadHandler` | execute, _list_predictions, _get_prediction, _get_for_subject, _get_stats | Handler for analytics.prediction_read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register analytics prediction operations with the OperationRegistry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## analytics_sandbox_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_sandbox_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 67

**Docstring:** Analytics Sandbox Handler (PIN-513 Batch 3A5 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsSandboxHandler` | simulate, get_sandbox | L4 handler: CostSim sandbox experimentation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## analytics_snapshot_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_snapshot_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 142

**Docstring:** Analytics Snapshot Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsSnapshotHandler` | execute, _run_hourly, _run_daily, _evaluate_anomalies | Handler for analytics.snapshot operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register analytics.snapshot operation with the OperationRegistry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## analytics_validation_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_validation_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 91

**Docstring:** Analytics Validation Handler (PIN-513 Batch 3A3 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsValidationHandler` | get_validator, validate_dataset, validate_all, generate_divergence_report | L4 handler: dataset validation and divergence reporting. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## anomaly_incident_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 182

**Docstring:** Anomaly Incident Coordinator (PIN-510 Phase 1C)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnomalyIncidentCoordinator` | detect_and_ingest, detect_only, persist_coordination_audit | L4 coordinator: analytics anomaly detection → incidents bridge. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_anomaly_incident_coordinator` | `() -> AnomalyIncidentCoordinator` | no | Get the singleton AnomalyIncidentCoordinator instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Optional | no |
| `uuid` | uuid4 | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AnomalyIncidentCoordinator`, `get_anomaly_incident_coordinator`

---

## anomaly_types.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/anomaly_types.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 57

**Docstring:** Anomaly Types (Spine Schemas)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostAnomalyFact` |  | Pure fact emitted by analytics when a cost anomaly is detected. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`CostAnomalyFact`

---

## api_keys_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/api_keys_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 40

**Docstring:** API Keys Bridge (PIN-510)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ApiKeysBridge` | keys_read_capability, keys_write_capability | Capabilities for api_keys domain. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_api_keys_bridge` | `() -> ApiKeysBridge` | no | Get the singleton ApiKeysBridge instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`ApiKeysBridge`, `get_api_keys_bridge`

---

## api_keys_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/api_keys_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 143

**Docstring:** API Keys Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ApiKeysQueryHandler` | execute | Handler for api_keys.query operations. |
| `ApiKeysWriteHandler` | execute | Handler for api_keys.write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register api_keys operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## artifact.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/artifact.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 158

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ArtifactType` |  | Type of artifact produced by a run. |
| `StorageBackend` |  | Where the artifact is stored. |
| `Artifact` | is_inline, has_content, get_inline_content | An artifact produced by a run or step. |
| `ArtifactReference` | from_artifact | Lightweight reference to an artifact. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_utc_now` | `() -> datetime` | no | UTC timestamp (inlined to keep schemas pure — no service imports). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional | no |
| `pydantic` | BaseModel, ConfigDict, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## audit_durability.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/audit_durability.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 325

**Docstring:** Module: durability

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DurabilityCheckResult` |  | Result of a durability check. |
| `RACDurabilityEnforcementError` | __init__, to_dict | Raised when RAC durability enforcement fails. |
| `DurabilityCheckResponse` | to_dict | Response from a durability check. |
| `RACDurabilityChecker` | __init__, from_governance_config, from_audit_store, is_durable, enforcement_enabled, check, ensure_durable, should_allow_operation | Checks and enforces RAC durability constraints. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_rac_durability` | `(enforcement_enabled: bool = True, durability_mode: str = 'MEMORY') -> Durabilit` | no | Quick helper to check RAC durability. |
| `ensure_rac_durability` | `(operation: str, enforcement_enabled: bool = True, durability_mode: str = 'MEMOR` | no | Quick helper to ensure RAC durability or raise error. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## audit_store.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/audit_store.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 526

**Docstring:** Audit Store

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StoreDurabilityMode` |  | Durability mode for the audit store. |
| `RACDurabilityError` |  | Raised when RAC requires durable storage but none is available. |
| `AuditStore` | __init__, durability_mode, is_durable, add_expectations, get_expectations, update_expectation_status, add_ack, get_acks (+8 more) | Storage for audit expectations and acknowledgments. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_determine_durability_mode` | `(redis_client) -> StoreDurabilityMode` | no | Determine the durability mode based on environment and Redis availability. |
| `get_audit_store` | `(redis_client = None) -> AuditStore` | no | Get the audit store singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `threading` | Lock | no |
| `typing` | Dict, List, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.hoc_spine.schemas.rac_models` | AuditExpectation, AuditStatus, DomainAck | no |
| `app.hoc.cus.hoc_spine.services.dispatch_audit` | DispatchRecord | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`REDIS_TTL_SECONDS`, `AUDIT_REDIS_ENABLED`, `RAC_ENABLED`, `AOS_MODE`

---

## auth_wiring.py
**Path:** `backend/app/hoc/cus/hoc_spine/auth_wiring.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 55

**Docstring:** Auth Wiring — main.py Import Aggregator

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `app.hoc.cus.hoc_spine.authority.gateway_policy` | AUTH_GATEWAY_ENABLED | no |
| `app.auth.gateway_config` | configure_auth_gateway, setup_auth_middleware | no |
| `app.auth.rbac_middleware` | RBACMiddleware | no |
| `app.auth.onboarding_gate` | OnboardingGateMiddleware | no |
| `app.auth` | verify_api_key | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AUTH_GATEWAY_ENABLED`, `configure_auth_gateway`, `setup_auth_middleware`, `RBACMiddleware`, `OnboardingGateMiddleware`, `verify_api_key`

---

## authority_decision.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/authority_decision.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 238

**Docstring:** AuthorityDecision — Unified Schema for L4 Authority Gates

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuthorityDecision` | allow, deny, allow_with_degraded_flag, with_condition, combine, to_dict, __str__ | Unified authority decision returned by all L4 authority checks. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## canary_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/canary_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 72

**Docstring:** Canary Coordinator (PIN-513 Batch 3A1 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CanaryCoordinator` | run | L4 coordinator: canary validation scheduling and execution. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## canonical_json.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/canonical_json.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 294

**Docstring:** Canonical JSON serialization for AOS.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `canonical_json` | `(obj: Any, exclude_fields: Optional[Set[str]] = None) -> str` | no | Serialize object to canonical JSON format. |
| `canonical_json_bytes` | `(obj: Any, exclude_fields: Optional[Set[str]] = None) -> bytes` | no | Serialize object to canonical JSON bytes (UTF-8). |
| `content_hash` | `(obj: Any, exclude_fields: Optional[Set[str]] = None, length: int = 16) -> str` | no | Compute deterministic content hash. |
| `content_hash_full` | `(obj: Any, exclude_fields: Optional[Set[str]] = None) -> str` | no | Compute full SHA-256 content hash. |
| `deterministic_hash` | `(obj: Any, length: int = 16) -> str` | no | Compute hash excluding allowed variance fields. |
| `_json_serializer` | `(obj: Any) -> Any` | no | Custom JSON serializer for non-standard types. |
| `_filter_fields` | `(obj: Any, exclude: Set[str]) -> Any` | no | Recursively filter out excluded fields from an object. |
| `is_canonical` | `(json_str: str) -> bool` | no | Check if a JSON string is in canonical format. |
| `canonicalize_file` | `(filepath: str) -> None` | no | Rewrite a JSON file in canonical format. |
| `assert_canonical` | `(filepath: str) -> None` | no | Assert that a JSON file is in canonical format. |
| `compare_deterministic` | `(actual: Dict[str, Any], expected: Dict[str, Any], deterministic_fields: Optiona` | no | Compare two outputs, checking only deterministic fields. |
| `_get_nested` | `(obj: Dict[str, Any], path: str) -> Any` | no | Get nested value using dot notation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `datetime` | date, datetime | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Set | no |
| `uuid` | UUID | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`ALLOWED_VARIANCE_FIELDS`

---

## circuit_breaker_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/circuit_breaker_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 291

**Docstring:** Circuit Breaker Handler (PIN-513 Batch 2A Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CircuitBreakerHandler` | get_state, is_v2_disabled, disable_v2, enable_v2, report_drift, report_schema_error, get_incidents, get_singleton (+7 more) | L4 handler: circuit breaker control plane. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## common.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/common.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 155

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## compliance_facade.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/compliance_facade.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 518

**Docstring:** Compliance Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ComplianceScope` |  | Compliance verification scope. |
| `ComplianceStatus` |  | Compliance status. |
| `ComplianceRule` | to_dict | Compliance rule definition. |
| `ComplianceViolation` | to_dict | A compliance violation. |
| `ComplianceReport` | to_dict | Compliance verification report. |
| `ComplianceStatusInfo` | to_dict | Overall compliance status. |
| `ComplianceFacade` | __init__, _init_default_rules, verify_compliance, _check_rule_compliance, list_reports, get_report, list_rules, get_rule (+1 more) | Facade for compliance verification operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_compliance_facade` | `() -> ComplianceFacade` | no | Get the compliance facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## concurrent_runs.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/concurrent_runs.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 247

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConcurrentRunsLimiter` | __init__, _get_client, acquire, release, get_count, slot | Limits concurrent runs using Redis-based semaphore. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_concurrent_limiter` | `() -> ConcurrentRunsLimiter` | no | Get the singleton concurrent runs limiter. |
| `acquire_slot` | `(key: str, max_slots: int)` | no | Convenience context manager for acquiring a slot. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `contextlib` | contextmanager | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`REDIS_URL`, `DEFAULT_SLOT_TIMEOUT`

---

## conftest.py
**Path:** `backend/app/hoc/cus/hoc_spine/tests/conftest.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 9

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## constraint_checker.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/constraint_checker.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 310

**Docstring:** Module: constraint_checker

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `InspectionOperation` |  | Operations that require inspection constraint checks. |
| `InspectionConstraintViolation` | to_dict | Record of an inspection constraint violation. |
| `InspectionConstraintChecker` | __init__, from_monitor_config, from_snapshot, is_allowed, check, check_all, get_allowed_operations, get_denied_operations (+1 more) | Enforces inspection constraints from MonitorConfig. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_inspection_allowed` | `(operation: InspectionOperation, allow_prompt_logging: bool = False, allow_respo` | no | Quick helper to check if an operation is allowed. |
| `get_constraint_violations` | `(operations: list[InspectionOperation], allow_prompt_logging: bool = False, allo` | no | Get all constraint violations for a set of operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## contract_engine.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/contracts/contract_engine.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 741

**Docstring:** Part-2 Contract Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `_EligibilityDecisionValue` | __init__, __eq__ | Enum-like value wrapper for string comparison. |
| `_EligibilityDecision` |  | Local proxy for EligibilityDecision enum values used in contract logic. |
| `ContractState` |  | In-memory representation of contract state. |
| `ContractStateMachine` | can_transition, validate_transition, transition | State machine for System Contract lifecycle. |
| `ContractService` | __init__, version, create_contract, approve, reject, activate, complete, fail (+5 more) | Part-2 Contract Service (L4) |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID, uuid4 | no |
| `app.models.contract` | TERMINAL_STATES, VALID_TRANSITIONS, AuditVerdict, ContractApproval, ContractImmutableError (+8) | no |
| `app.hoc.cus.hoc_spine.schemas.protocols` | EligibilityVerdictPort, ValidatorVerdictPort | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`CONTRACT_SERVICE_VERSION`

---

## control_registry.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/control_registry.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 455

**Docstring:** Module: control_registry

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SOC2Category` |  | SOC2 Trust Service Categories. |
| `SOC2ComplianceStatus` |  | Compliance status for a control mapping. |
| `SOC2Control` | __post_init__ | SOC2 Trust Service Criteria control definition. |
| `SOC2ControlMapping` | to_dict | Mapping of incident/evidence to a SOC2 control. |
| `SOC2ControlRegistry` | __init__, _register_all_controls, _register_incident_response_controls, _register_access_controls, _register_change_management_controls, _register_processing_integrity_controls, _register_availability_controls, _register_communication_controls (+6 more) | Registry of SOC2 Trust Service Criteria controls. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_control_registry` | `() -> SOC2ControlRegistry` | no | Get or create the singleton control registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## controls_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/controls_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 63

**Docstring:** Controls Bridge (PIN-510)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ControlsBridge` | limits_query_capability, policy_limits_capability, killswitch_capability, limit_breaches_capability, scoped_execution_capability | Capabilities for controls domain. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_controls_bridge` | `() -> ControlsBridge` | no | Get the singleton ControlsBridge instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`ControlsBridge`, `get_controls_bridge`

---

## controls_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 521

**Docstring:** Controls Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ControlsQueryHandler` | execute | Handler for controls.query operations. |
| `ControlsThresholdHandler` | execute | Handler for controls.thresholds operations. |
| `ControlsOverrideHandler` | execute | Handler for controls.overrides operations. |
| `CircuitBreakerHandler` | execute | Handler for controls.circuit_breaker operations. |
| `KillswitchReadHandler` | execute | Handler for controls.killswitch.read operations. |
| `KillswitchWriteHandler` | execute | Handler for controls.killswitch.write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register controls operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## costsim_config.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/costsim_config.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 184

**Docstring:** CostSim V2 Configuration - HOC Spine Shared Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostSimConfig` | from_env | Configuration for CostSim V2. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_config` | `() -> CostSimConfig` | no | Get the global CostSim configuration. |
| `is_v2_sandbox_enabled` | `() -> bool` | no | Check if V2 sandbox is enabled. |
| `is_v2_disabled_by_drift` | `() -> bool` | no | Check if V2 was auto-disabled due to drift. |
| `get_commit_sha` | `() -> str` | no | Get current git commit SHA. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`CostSimConfig`, `get_config`, `is_v2_sandbox_enabled`, `is_v2_disabled_by_drift`, `get_commit_sha`

---

## costsim_metrics.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/costsim_metrics.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 394

**Docstring:** CostSim V2 Prometheus Metrics - HOC Spine Shared Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostSimMetrics` | __init__, _init_metrics, record_drift, record_cost_delta, record_schema_error, record_simulation_duration, record_simulation, set_circuit_breaker_state (+10 more) | Prometheus metrics for CostSim V2. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_metrics` | `() -> CostSimMetrics` | no | Get the global CostSim metrics instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `typing` | Optional | no |
| `app.hoc.cus.hoc_spine.services.costsim_config` | get_config | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`DRIFT_SCORE_BUCKETS`, `COST_DELTA_BUCKETS`, `DURATION_BUCKETS`

### __all__ Exports
`CostSimMetrics`, `get_metrics`, `DRIFT_SCORE_BUCKETS`, `COST_DELTA_BUCKETS`, `DURATION_BUCKETS`

---

## cross_domain.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/cross_domain.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 506

**Docstring:** Cross-Domain Governance Functions (Mandatory)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `utc_now` | `() -> datetime` | no | Return timezone-aware UTC datetime. |
| `generate_uuid` | `() -> str` | no | Generate a UUID string. |
| `create_incident_from_cost_anomaly` | `(session: AsyncSession, tenant_id: str, anomaly_id: str, anomaly_type: str, seve` | yes | Create an incident from a cost anomaly. MANDATORY. |
| `record_limit_breach` | `(session: AsyncSession, tenant_id: str, limit_id: str, breach_type: str, value_a` | yes | Record a limit breach. MANDATORY. |
| `table_exists` | `(session: AsyncSession, table_name: str) -> bool` | yes | Check if a table exists in the database. |
| `create_incident_from_cost_anomaly_sync` | `(session: Session, tenant_id: str, anomaly_id: str, anomaly_type: str, severity:` | no | Create an incident from a cost anomaly (SYNC version). MANDATORY. |
| `record_limit_breach_sync` | `(session: Session, tenant_id: str, limit_id: str, breach_type: str, value_at_bre` | no | Record a limit breach (SYNC version). MANDATORY. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Optional, Union | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `sqlmodel` | Session | no |
| `app.errors.governance` | GovernanceError | no |
| `app.metrics` | governance_incidents_created_total, governance_limit_breaches_recorded_total | no |
| `app.models.killswitch` | Incident | no |
| `app.models.policy_control_plane` | LimitBreach | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`ANOMALY_SEVERITY_MAP`, `ANOMALY_TRIGGER_TYPE_MAP`

---

## cross_domain_gateway.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/cross_domain_gateway.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 38

**Docstring:** Cross-Domain Gateway (L4)

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver` | get_circuit_breaker, is_v2_disabled, report_drift | no |
| `app.hoc.cus.incidents.L5_engines.recovery_rule_engine` | evaluate_rules | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`get_circuit_breaker`, `is_v2_disabled`, `report_drift`, `evaluate_rules`

---

## cus_credential_engine.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/cus_credential_engine.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 570

**Docstring:** Customer Credential Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CusCredentialService` | __init__, _derive_dev_key, _derive_tenant_key, encrypt_credential, decrypt_credential, resolve_credential, _resolve_vault_credential, resolve_cus_vault_credential (+5 more) | Service for managing customer LLM credentials. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `base64` | base64 | no |
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `logging` | logging | no |
| `os` | os | no |
| `secrets` | secrets | no |
| `typing` | Dict, Optional, Tuple | no |
| `cryptography.hazmat.primitives.ciphers.aead` | AESGCM | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## dag_executor.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/dag_executor.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 325

**Docstring:** DAG-based executor for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StageResult` | success, was_blocked | Result of executing a single stage. |
| `ExecutionTrace` | to_dict | Full execution trace across all stages. |
| `DAGExecutor` | __init__, execute, _execute_stage, _execute_policy, _is_more_restrictive, get_execution_plan, visualize_plan | Executes policies in DAG order. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.policy.compiler.grammar` | ActionType | no |
| `app.policy.ir.ir_nodes` | IRModule | no |
| `app.policy.optimizer.dag_sorter` | DAGSorter, ExecutionPlan | no |
| `app.hoc.cus.policies.L5_engines.deterministic_engine` | DeterministicEngine, ExecutionContext, ExecutionResult | no |
| `app.hoc.cus.policies.L5_engines.intent` | Intent | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## dag_sorter.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/dag_sorter.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 318

**Docstring:** DAG-based execution ordering for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExecutionPhase` |  | Execution phases in deterministic order. |
| `ExecutionNode` | __hash__, __eq__ | A node in the execution DAG. |
| `ExecutionDAG` | add_node, add_edge, get_roots, get_leaves | Directed Acyclic Graph of policy execution. |
| `ExecutionPlan` | to_dict | A deterministic execution plan. |
| `DAGSorter` | __init__, build_dag, _get_phase, _add_category_dependencies, _add_routing_dependencies, sort, get_execution_order, visualize | Sorts policies into deterministic execution order. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `enum` | Enum, auto | no |
| `typing` | Any, Dict, List, Optional, Set (+1) | no |
| `app.policy.compiler.grammar` | PolicyCategory | no |
| `app.policy.ir.ir_nodes` | IRFunction, IRGovernance, IRModule | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## db_helpers.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/db_helpers.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 437

**Docstring:** Database helper functions for SQLModel row extraction.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `scalar_or_default` | `(row: Optional[Any], default: Any = 0) -> Any` | no | Extract scalar value from Row or return default. |
| `scalar_or_none` | `(row: Optional[Any]) -> Optional[Any]` | no | Extract scalar value from Row, returning None if unavailable. |
| `extract_model` | `(row: Any, model_attr: str = 'id') -> Any` | no | Extract model instance from Row or return as-is. |
| `extract_models` | `(results: List[Any], model_attr: str = 'id') -> List[Any]` | no | Extract model instances from a list of results. |
| `count_or_zero` | `(row: Optional[Any]) -> int` | no | Extract count value, guaranteed to return int. |
| `sum_or_zero` | `(row: Optional[Any]) -> float` | no | Extract sum value, guaranteed to return numeric. |
| `query_one` | `(session: Any, statement: Any, model_class: Optional[type] = None) -> Optional[A` | no | Safe single-row query with automatic Row/Model detection. |
| `query_all` | `(session: Any, statement: Any, model_class: Optional[type] = None) -> list` | no | Safe multi-row query with automatic Row/Model detection. |
| `model_to_dict` | `(model: Any, include: Optional[list] = None, exclude: Optional[list] = None) -> ` | no | Convert ORM model to dict to prevent DetachedInstanceError. |
| `models_to_dicts` | `(models: list, include: Optional[list] = None, exclude: Optional[list] = None) -` | no | Convert list of ORM models to list of dicts. |
| `safe_get` | `(session: Any, model_class: type, id: Any, to_dict: bool = False, include: Optio` | no | Safe session.get() wrapper with optional dict conversion. |
| `get_or_create` | `(session: Any, model_class: type, defaults: Optional[dict] = None, **kwargs) -> ` | no | Get existing model or create new one. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, List, Optional, TypeVar | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`T`

---

## decisions.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/decisions.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 1291

**Docstring:** Phase 4B: Decision Record Models and Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DecisionType` |  | Types of decisions that must be recorded. |
| `DecisionSource` |  | Who originated the decision authority. |
| `DecisionTrigger` |  | Why the decision occurred. |
| `DecisionOutcome` |  | Result of the decision. |
| `CausalRole` |  | When in the lifecycle this decision occurred. |
| `DecisionRecord` | to_dict | Contract-aligned decision record. |
| `DecisionRecordService` | __init__, _bridge_to_taxonomy, emit | Append-only sink for decision records. |
| `CARESignalAccessError` |  | Raised when attempting to access a forbidden CARE signal. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_decision_service` | `() -> DecisionRecordService` | no | Get singleton decision record service. |
| `emit_routing_decision` | `(connection: Any, run_id: Optional[str], routed: bool, selected_agent: Optional[` | no | Emit a routing decision record. |
| `emit_recovery_decision` | `(connection: Any, run_id: Optional[str], evaluated: bool, triggered: bool, actio` | no | Emit a recovery decision record. |
| `emit_memory_decision` | `(connection: Any, run_id: Optional[str], queried: bool, matched: bool, injected:` | no | Emit a memory injection decision record. |
| `emit_policy_decision` | `(connection: Any, run_id: Optional[str], policy_id: str, evaluated: bool, violat` | no | Emit a policy enforcement decision record. |
| `emit_budget_decision` | `(connection: Any, run_id: Optional[str], budget_requested: int, budget_available` | no | Emit a budget handling decision record. |
| `_check_budget_enforcement_exists` | `(connection: Any, run_id: str) -> bool` | no | Check if a budget_enforcement decision already exists for this run. |
| `emit_budget_enforcement_decision` | `(connection: Any, run_id: str, budget_limit_cents: int, budget_consumed_cents: i` | no | Emit a budget enforcement decision record when hard limit halts execution. |
| `_check_policy_precheck_exists` | `(connection: Any, request_id: str, outcome: str) -> bool` | no | Check if a policy_pre_check decision already exists for this request+outcome. |
| `emit_policy_precheck_decision` | `(connection: Any, request_id: str, posture: str, passed: bool, service_available` | no | Emit a policy pre-check decision record. |
| `_check_recovery_evaluation_exists` | `(connection: Any, run_id: str, failure_type: str) -> bool` | no | Check if a recovery_evaluation decision already exists for this run+failure. |
| `emit_recovery_evaluation_decision` | `(connection: Any, run_id: str, request_id: str, recovery_class: str, recovery_ac` | no | Emit a recovery evaluation decision record. |
| `backfill_run_id_for_request` | `(connection: Any, request_id: str, run_id: str) -> int` | no | Backfill run_id for all decisions with matching request_id. |
| `check_signal_access` | `(signal_name: str) -> bool` | no | Check if a signal is allowed for CARE optimization. |
| `activate_care_kill_switch` | `() -> bool` | no | Activate the CARE optimization kill-switch. |
| `deactivate_care_kill_switch` | `() -> bool` | no | Deactivate the CARE optimization kill-switch. |
| `is_care_kill_switch_active` | `() -> bool` | no | Check if CARE kill-switch is currently active. |
| `_check_care_optimization_exists` | `(connection: Any, request_id: str) -> bool` | no | Check if a care_routing_optimized decision already exists for this request. |
| `emit_care_optimization_decision` | `(connection: Any, request_id: str, baseline_agent: str, optimized_agent: str, co` | no | Emit a CARE routing optimization decision record. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional | no |
| `pydantic` | BaseModel, Field | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.exc` | SQLAlchemyError | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`CARE_ALLOWED_SIGNALS`, `CARE_FORBIDDEN_SIGNALS`, `CARE_CONFIDENCE_THRESHOLD`

---

## degraded_mode_checker.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/degraded_mode_checker.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 676

**Docstring:** Module: degraded_mode_checker

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DegradedModeCheckResult` |  | Result of a degraded mode check. |
| `DegradedModeState` |  | Possible degraded mode states. |
| `GovernanceDegradedModeError` | __init__, to_dict | Raised when governance degraded mode blocks an operation. |
| `DegradedModeStatus` | to_dict | Current degraded mode status. |
| `DegradedModeCheckResponse` | to_dict | Response from a degraded mode check. |
| `DegradedModeIncident` |  | Incident data for degraded mode transition. |
| `DegradedModeIncidentCreator` | __init__, create_degraded_incident, create_recovery_incident | Creates incidents for degraded mode transitions. |
| `GovernanceDegradedModeChecker` | __init__, from_governance_config, check_enabled, get_current_status, check, ensure_not_degraded, enter_degraded, exit_degraded (+2 more) | Checks and manages governance degraded mode. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_degraded_mode` | `(check_enabled: bool = True) -> DegradedModeCheckResponse` | no | Quick helper to check degraded mode. |
| `ensure_not_degraded` | `(operation: str, check_enabled: bool = True) -> None` | no | Quick helper to ensure not in degraded mode or raise error. |
| `enter_degraded_with_incident` | `(state: DegradedModeState, reason: str, entered_by: str, new_runs_action: str = ` | no | Quick helper to enter degraded mode with incident. |
| `_reset_degraded_mode_state` | `() -> None` | no | Reset global state (for testing only). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `threading` | Lock | no |
| `typing` | Any, Dict, FrozenSet, Optional | no |
| `logging` | logging | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## deterministic.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/deterministic.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 143

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `seeded_jitter` | `(workflow_run_id: str, attempt: int) -> float` | no | Generate deterministic jitter value from workflow ID and attempt number. |
| `deterministic_backoff_ms` | `(workflow_run_id: str, attempt: int, initial_ms: int = 200, multiplier: float = ` | no | Calculate exponential backoff with deterministic jitter. |
| `deterministic_timestamp` | `(workflow_run_id: str, step_index: int, base_time: Optional[float] = None) -> in` | no | Generate a deterministic timestamp for replay scenarios. |
| `generate_idempotency_key` | `(workflow_run_id: str, skill_name: str, step_index: int) -> str` | no | Generate a deterministic idempotency key for a skill execution. |
| `hash_params` | `(params: dict) -> str` | no | Generate a hash of skill parameters for idempotency comparison. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `struct` | struct | no |
| `time` | time | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## dispatch_audit.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/dispatch_audit.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 139

**Docstring:** Dispatch Audit Record — pure builder for operation dispatch records.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DispatchRecord` | to_dict | Immutable record of a single operation dispatch. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `build_dispatch_record` | `(operation: str, tenant_id: str, success: bool, duration_ms: float, authority_al` | no | Build a DispatchRecord from dispatch parameters. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## dispatch_metrics_adapter.py
**Path:** `backend/app/hoc/cus/hoc_spine/consequences/adapters/dispatch_metrics_adapter.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 154

**Docstring:** Dispatch Metrics Adapter.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OperationMetrics` | avg_latency_ms, error_rate, to_dict | Aggregated metrics for a single operation name. |
| `DispatchMetricsAdapter` | __init__, name, handle, get_operation_metrics, get_tenant_counts, get_summary | Post-dispatch consequence: aggregate operation metrics. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_dispatch_metrics_adapter` | `() -> DispatchMetricsAdapter` | no | Get the dispatch metrics adapter singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `collections` | defaultdict | no |
| `dataclasses` | dataclass | no |
| `threading` | Lock | no |
| `typing` | Dict, Optional | no |
| `app.hoc.cus.hoc_spine.services.dispatch_audit` | DispatchRecord | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## domain_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/domain_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 110

**Docstring:** Domain Bridge (C4 — Loop Model)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DomainBridge` | logs_read_service, lessons_driver_factory, limits_read_driver_factory, policy_limits_driver_factory, lessons_capability, limits_query_capability, policy_limits_capability | Cross-domain service accessor — backward-compat facade. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_domain_bridge` | `() -> DomainBridge` | no | Get the singleton DomainBridge instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`DomainBridge`, `get_domain_bridge`

---

## domain_enums.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/domain_enums.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 106

**Docstring:** Domain-level enum mirrors.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ActorType` |  | Types of actors performing actions. |
| `AuditEntityType` |  | Entity types tracked in audit ledger. |
| `AuditEventType` |  | Canonical audit events — only these create audit rows. |
| `IncidentSeverity` |  | Incident severity levels. |
| `AuditVerdict` |  | Audit verification verdict. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## evidence_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/evidence_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 222

**Docstring:** Evidence Coordinator (PIN-513 Batch 3B1 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EvidenceCoordinator` | capture_environment, capture_activity, capture_provider, capture_policy_decision, capture_integrity, compute_integrity, hash_prompt | L4 coordinator: evidence capture orchestration. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## execution.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/drivers/execution.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 1332

**Docstring:** Module: execution

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IngestionSourceType` |  | Types of data sources for ingestion. |
| `IngestionBatch` | __post_init__ | A batch of ingested records. |
| `IngestionResult` | to_dict | Result of data ingestion operation. |
| `DataIngestionExecutor` | __init__, execute, _get_connector, _ingest_from_http, _ingest_from_sql, _ingest_from_file, _ingest_from_vector, _simulate_ingestion | Real data ingestion executor (GAP-159). |
| `IndexingResult` | to_dict | Result of indexing operation. |
| `IndexingExecutor` | __init__, execute, _get_vector_connector, _extract_documents, _chunk_documents, _generate_embeddings, _simulate_embedding, _call_embedding_api | Real indexing executor (GAP-160). |
| `SensitivityLevel` |  | Data sensitivity levels. |
| `PIIType` |  | Types of PII detected. |
| `PIIDetection` |  | A detected PII instance. |
| `ClassificationResult` | to_dict | Result of classification operation. |
| `ClassificationExecutor` | __init__, execute, _sample_records, _detect_pii, _redact, _detect_categories, _determine_sensitivity | Real classification executor (GAP-161). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_ingestion_executor` | `() -> DataIngestionExecutor` | no | Get or create the singleton DataIngestionExecutor. |
| `get_indexing_executor` | `() -> IndexingExecutor` | no | Get or create the singleton IndexingExecutor. |
| `get_classification_executor` | `() -> ClassificationExecutor` | no | Get or create the singleton ClassificationExecutor. |
| `reset_executors` | `() -> None` | no | Reset all singletons (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `re` | re | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Iterator, List, Optional (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## execution_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/execution_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 263

**Docstring:** Execution Coordinator (PIN-513 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExecutionCoordinator` | create_scope, execute_with_scope, should_retry, track_progress, emit_audit_created, emit_audit_completed, emit_audit_failed | L4 coordinator: pre-execution scoping + job lifecycle. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## export_bundle_adapter.py
**Path:** `backend/app/hoc/cus/hoc_spine/consequences/adapters/export_bundle_adapter.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 431

**Docstring:** Export Bundle Adapter (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExportBundleAdapter` | __init__, create_evidence_bundle, create_soc2_bundle, create_executive_debrief, _compute_bundle_hash, _generate_attestation, _assess_risk_level, _generate_incident_summary (+2 more) | Adapter for generating export bundles. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_export_bundle_adapter` | `() -> ExportBundleAdapter` | no | Get or create ExportBundleAdapter singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `app.models.export_bundles` | DEFAULT_SOC2_CONTROLS, EvidenceBundle, ExecutiveDebriefBundle, PolicyContext, SOC2Bundle (+1) | no |
| `app.hoc.cus.logs.L6_drivers.export_bundle_store` | IncidentSnapshot, RunSnapshot, TraceSummarySnapshot | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`ExportBundleAdapter`, `get_export_bundle_adapter`

---

## fatigue_controller.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/fatigue_controller.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 749

**Docstring:** AlertFatigueController - Alert fatigue management service.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertFatigueMode` |  | Operating modes for fatigue control. |
| `AlertFatigueAction` |  | Actions taken by the fatigue controller. |
| `AlertFatigueConfig` | to_dict | Configuration for alert fatigue thresholds. |
| `AlertFatigueState` | record_alert, reset_window, start_suppression, end_suppression, start_cooldown, end_cooldown, add_to_aggregation, flush_aggregation (+4 more) | State tracking for an alert source. |
| `AlertFatigueStats` | update_rates, to_dict | Statistics from fatigue controller. |
| `AlertFatigueError` | __init__, to_dict | Exception for fatigue controller errors. |
| `FatigueCheckResult` | to_dict | Result of a fatigue check. |
| `AlertFatigueController` | __init__, _get_state_key, _generate_source_id, configure_tenant, get_config, get_or_create_state, get_state, check_alert (+6 more) | Controller for managing alert fatigue. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_fatigue_controller` | `() -> AlertFatigueController` | no | Get the singleton controller instance. |
| `_reset_controller` | `() -> None` | no | Reset the singleton (for testing). |
| `check_alert_fatigue` | `(tenant_id: str, alert_type: str, source_id: Optional[str] = None, source_data: ` | no | Check if an alert should be allowed or suppressed. |
| `suppress_alert` | `(tenant_id: str, source_id: str, alert_type: str, duration_seconds: Optional[int` | no | Manually suppress an alert source. |
| `get_fatigue_stats` | `(tenant_id: Optional[str] = None) -> AlertFatigueStats` | no | Get fatigue statistics. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `hashlib` | hashlib | no |
| `json` | json | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## gateway_policy.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/gateway_policy.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 159

**Docstring:** Gateway Public-Path Policy (Canonical)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_public_paths` | `() -> list[str]` | no | Return the canonical public path exemption list. |
| `get_public_patterns` | `() -> list[str]` | no | Return the canonical public pattern list. |
| `get_gateway_policy_config` | `() -> dict` | no | Return kwargs for AuthGatewayMiddleware initialization. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `os` | os | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AUTH_GATEWAY_ENABLED`, `PUBLIC_PATHS`, `PUBLIC_PATTERNS`, `get_public_paths`, `get_public_patterns`, `get_gateway_policy_config`

---

## governance_audit_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/governance_audit_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 117

**Docstring:** Governance Audit Handler (Part-2 CRM)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceAuditJobHandler` | execute | Handler for governance.audit_job. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_parse_uuid` | `(val: Any, label: str) -> tuple[Optional[UUID], Optional[OperationResult]]` | no |  |
| `_parse_dt` | `(val: Any, label: str) -> tuple[Optional[datetime], Optional[OperationResult]]` | no |  |
| `register` | `(registry: OperationRegistry) -> None` | no | Register governance audit operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## governance_orchestrator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/governance_orchestrator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 829

**Docstring:** Part-2 Governance Orchestrator (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HealthLookup` | capture_health_snapshot | Protocol for capturing health state (read-only). |
| `JobState` |  | In-memory representation of job state. |
| `JobStateMachine` | can_transition, validate_transition, transition | State machine for Governance Job lifecycle. |
| `ExecutionOrchestrator` | create_job_plan, _parse_change_to_step | Translates contract → job plan. |
| `JobStateTracker` | record_step_result, calculate_completion_status | Observes job state - does NOT control execution. |
| `AuditEvidence` |  | Evidence package for audit layer. |
| `AuditTrigger` | prepare_evidence, should_trigger_audit | Prepares and hands evidence to audit layer. |
| `ContractActivationError` | __init__ | Raised when contract activation fails. |
| `ContractActivationService` | __init__, activate_contract | Activates approved contracts (APPROVED → ACTIVE). |
| `GovernanceOrchestrator` | __init__, version, activate_contract, start_job, record_step_result, complete_job, cancel_job, should_trigger_audit (+4 more) | Facade for all governance orchestration services. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_audit_service` | `()` | no | Return singleton AuditService (L8) implementation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional, Protocol | no |
| `uuid` | UUID, uuid4 | no |
| `app.models.contract` | ContractStatus | no |
| `app.models.governance_job` | JOB_TERMINAL_STATES, JOB_VALID_TRANSITIONS, HealthSnapshot, InvalidJobTransitionError, JobImmutableError (+5) | no |
| `app.hoc.cus.hoc_spine.authority.contracts.contract_engine` | ContractService, ContractState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`ORCHESTRATOR_VERSION`

---

## governance_signal_driver.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/governance_signal_driver.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 293

**Docstring:** Governance Signal Service (Phase E FIX-03)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceSignalService` | __init__, record_signal, _supersede_existing_signals, check_governance, is_blocked, get_active_signals, clear_signal | Service for governance signal operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_governance_status` | `(session: Session, scope: str, signal_type: Optional[str] = None) -> GovernanceC` | no | Check governance status for a scope. |
| `is_governance_blocked` | `(session: Session, scope: str, signal_type: Optional[str] = None) -> bool` | no | Quick check if scope is blocked. |
| `record_governance_signal` | `(session: Session, signal_type: str, scope: str, decision: str, recorded_by: str` | no | Record a governance signal. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `sqlalchemy` | and_, or_, select, update | no |
| `sqlalchemy.orm` | Session | no |
| `app.models.governance` | GovernanceCheckResult, GovernanceSignal, GovernanceSignalResponse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## guard.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/guard.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 622

**Docstring:** Guard Console Data Contracts - Customer-Facing API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardStatusDTO` |  | GET /guard/status response. |
| `TodaySnapshotDTO` |  | GET /guard/snapshot/today response. |
| `IncidentSummaryDTO` |  | Incident list item. |
| `IncidentEventDTO` |  | Timeline event within an incident. |
| `IncidentDetailDTO` |  | GET /guard/incidents/{id} response. |
| `IncidentListDTO` |  | GET /guard/incidents response (paginated). |
| `CustomerIncidentImpactDTO` |  | Impact assessment for customers - calm, explicit. |
| `CustomerIncidentResolutionDTO` |  | Resolution status for customers - reassuring. |
| `CustomerIncidentActionDTO` |  | Customer action item - only if necessary. |
| `CustomerIncidentNarrativeDTO` |  | GET /guard/incidents/{id} enhanced response. |
| `ApiKeyDTO` |  | API key response (masked). |
| `ApiKeyListDTO` |  | GET /guard/keys response. |
| `GuardrailConfigDTO` |  | Individual guardrail configuration. |
| `TenantSettingsDTO` |  | GET /guard/settings response. |
| `ReplayCallSnapshotDTO` |  | Original call context for replay. |
| `ReplayCertificateDTO` |  | Cryptographic proof of replay (M23). |
| `ReplayResultDTO` |  | POST /guard/replay/{call_id} response. |
| `KillSwitchActionDTO` |  | POST /guard/killswitch/activate and /deactivate response. |
| `OnboardingVerifyResponseDTO` |  | POST /guard/onboarding/verify response. |
| `CustomerCostSummaryDTO` |  | GET /guard/costs/summary response. |
| `CostBreakdownItemDTO` |  | Individual cost breakdown item. |
| `CustomerCostExplainedDTO` |  | GET /guard/costs/explained response. |
| `CustomerCostIncidentDTO` |  | Cost-related incident visible to customer. |
| `CustomerCostIncidentListDTO` |  | GET /guard/costs/incidents response. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Literal, Optional | no |
| `pydantic` | BaseModel, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## guard_cache.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/guard_cache.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 253

**Docstring:** Redis-based cache for Guard Console endpoints.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardCache` | __init__, get_instance, _get_redis, _make_key, get, set, invalidate, get_status (+6 more) | Redis-based cache for Guard Console API. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_guard_cache` | `() -> GuardCache` | no | Get guard cache singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Dict, Optional | no |
| `app.hoc.cus.hoc_spine.services.metrics_helpers` | get_or_create_counter, get_or_create_histogram | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`GUARD_CACHE_ENABLED`, `GUARD_STATUS_TTL`, `GUARD_SNAPSHOT_TTL`, `GUARD_INCIDENTS_TTL`, `GUARD_CACHE_PREFIX`, `GUARD_CACHE_HITS`, `GUARD_CACHE_MISSES`, `GUARD_CACHE_LATENCY`

### __all__ Exports
`GuardCache`, `get_guard_cache`, `GUARD_STATUS_TTL`, `GUARD_SNAPSHOT_TTL`, `GUARD_INCIDENTS_TTL`

---

## guard_write_driver.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/guard_write_driver.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 267

**Docstring:** Guard Write Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardWriteDriver` | __init__, get_or_create_killswitch_state, freeze_killswitch, unfreeze_killswitch, acknowledge_incident, resolve_incident, create_demo_incident | L6 driver for guard write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_guard_write_driver` | `(session: Session) -> GuardWriteDriver` | no | Factory function to get GuardWriteDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | List, Optional, Tuple | no |
| `sqlalchemy` | and_, select | no |
| `sqlmodel` | Session | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.models.killswitch` | Incident, IncidentEvent, IncidentSeverity, IncidentStatus, KillSwitchState (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`GuardWriteDriver`, `get_guard_write_driver`

---

## guard_write_engine.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/guard_write_engine.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 154

**Docstring:** Guard Write Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardWriteService` | __init__, get_or_create_killswitch_state, freeze_killswitch, unfreeze_killswitch, acknowledge_incident, resolve_incident, create_demo_incident | DB write operations for Guard Console. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, List, Optional, Tuple | no |
| `app.hoc.cus.hoc_spine.drivers.guard_write_driver` | GuardWriteDriver, get_guard_write_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## idempotency.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/idempotency.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 161

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IdempotencyResult` |  | Result of idempotency check. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_existing_run` | `(idempotency_key: str, tenant_id: Optional[str] = None, agent_id: Optional[str] ` | no | Check if a run with this idempotency key already exists. |
| `check_idempotency` | `(idempotency_key: str, tenant_id: Optional[str] = None, agent_id: Optional[str] ` | no | Check idempotency and return result with status. |
| `should_return_cached` | `(result: IdempotencyResult) -> bool` | no | Determine if we should return cached result. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `sqlmodel` | Session, select | no |
| `app.db` | Run, engine | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`IDEMPOTENCY_TTL_SECONDS`

---

## idempotency_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/idempotency_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 49

**Docstring:** Idempotency Handler (PIN-513 Batch 3B3 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IdempotencyHandler` | get_store, canonical_json, hash_request | L4 handler: request idempotency. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## incidents_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/incidents_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 173

**Docstring:** Incidents Bridge (PIN-510)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentsBridge` | incident_read_capability, incident_write_capability, lessons_capability, export_capability, incidents_for_run_capability | Capabilities for incidents domain. Max 5 methods. |
| `IncidentsEngineBridge` | recovery_rule_engine_capability, evidence_recorder_capability | Extended capabilities for incidents domain engines. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incidents_bridge` | `() -> IncidentsBridge` | no | Get the singleton IncidentsBridge instance. |
| `get_incident_driver` | `(db_url = None)` | no | Get the singleton IncidentDriver, wired with IncidentEngine via Protocol. |
| `get_incidents_engine_bridge` | `() -> IncidentsEngineBridge` | no | Get the singleton IncidentsEngineBridge instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`IncidentsBridge`, `get_incidents_bridge`, `get_incident_driver`, `get_incident_facade`, `IncidentsEngineBridge`, `get_incidents_engine_bridge`

---

## incidents_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 385

**Docstring:** Incidents Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentsQueryHandler` | execute | Handler for incidents.query operations. |
| `IncidentsExportHandler` | execute | Handler for incidents.export operations. |
| `IncidentsWriteHandler` | execute | Handler for incidents.write operations. |
| `IncidentsRecoveryRuleHandler` | execute | Handler for incidents.recovery_rules operations. |
| `CostGuardQueryHandler` | execute | Handler for incidents.cost_guard operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register incidents operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## input_sanitizer.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/input_sanitizer.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 260

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SanitizationResult` | __post_init__ | Result of input sanitization. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `detect_injection_patterns` | `(text: str) -> List[tuple]` | no | Detect prompt injection patterns in text. |
| `extract_urls` | `(text: str) -> List[str]` | no | Extract all URLs from text. |
| `is_url_safe` | `(url: str) -> tuple[bool, Optional[str]]` | no | Check if a URL is safe (not targeting internal resources). |
| `sanitize_goal` | `(goal: str) -> SanitizationResult` | no | Sanitize a goal string before processing. |
| `validate_goal` | `(goal: str) -> tuple[bool, Optional[str], List[str]]` | no | Convenience function to validate a goal. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `re` | re | no |
| `dataclasses` | dataclass | no |
| `typing` | List, Optional, Set | no |
| `urllib.parse` | urlparse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`MAX_GOAL_LENGTH`, `ENABLE_INJECTION_DETECTION`, `ENABLE_URL_SANITIZATION`, `INJECTION_PATTERNS`

---

## integration_bootstrap_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/integration_bootstrap_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 165

**Docstring:** Integration Bootstrap Handler (PIN-513 Batch 1D Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntegrationBootstrapHandler` | initialize, send_notification, check_health, get_channel_config | L4 handler: integration subsystem bootstrap and notification dispatch. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## integrations_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/integrations_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 190

**Docstring:** Integrations Bridge (L4 Coordinator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntegrationsBridge` | mcp_capability, connector_capability, health_capability, datasources_capability, credentials_capability | Integrations domain capability factory. |
| `IntegrationsDriverBridge` | worker_registry_capability, worker_registry_exceptions, incident_creator_capability | Extended capabilities for integrations L6 drivers. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_integrations_bridge` | `() -> IntegrationsBridge` | no | Get the integrations bridge singleton. |
| `get_integrations_driver_bridge` | `() -> IntegrationsDriverBridge` | no | Get the singleton IntegrationsDriverBridge instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`IntegrationsBridge`, `get_integrations_bridge`, `IntegrationsDriverBridge`, `get_integrations_driver_bridge`

---

## integrations_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/integrations_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 229

**Docstring:** Integrations Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntegrationsQueryHandler` | execute | Handler for integrations.query operations. |
| `IntegrationsConnectorsHandler` | execute | Handler for integrations.connectors operations. |
| `IntegrationsDataSourcesHandler` | execute | Handler for integrations.datasources operations. |
| `IntegrationsWorkersHandler` | execute | Handler for integrations.workers operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register integrations operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## integrity_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/integrity_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 38

**Docstring:** Integrity Handler (PIN-513 Batch 3B1 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntegrityHandler` | compute | L4 handler: V2 integrity computation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## job_executor.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/execution/job_executor.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 837

**Docstring:** Part-2 Job Executor (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HealthObserver` | observe_health | Protocol for observing health state (read-only). |
| `StepHandler` | execute | Protocol for step type handlers. |
| `StepOutput` |  | Output from executing a single step. |
| `ExecutionContext` |  | Context passed to step handlers during execution. |
| `ExecutionResult` |  | Result of executing a job. |
| `JobExecutor` | __init__, version, register_handler, execute_job, _execute_step | Part-2 Job Executor (L5) |
| `NoOpHandler` | execute | No-op handler for testing. |
| `FailingHandler` | __init__, execute | Failing handler for testing. |
| `CoordinatedJobExecutor` | __init__, _get_coordinator, execute_job_with_audit, execute_scoped_job, get_retry_advice, track_job_progress | JobExecutor with ExecutionCoordinator integration. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_default_executor` | `() -> JobExecutor` | no | Create a JobExecutor with default handlers. |
| `create_coordinated_executor` | `() -> CoordinatedJobExecutor` | no | Create a CoordinatedJobExecutor with default handlers. |
| `execution_result_to_evidence` | `(result: ExecutionResult) -> dict[str, Any]` | no | Convert ExecutionResult to audit evidence format. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Optional, Protocol | no |
| `uuid` | UUID | no |
| `app.models.governance_job` | JobStatus, JobStep, StepResult, StepStatus | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`EXECUTOR_VERSION`

---

## killswitch_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/killswitch_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 207

**Docstring:** Killswitch Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KillswitchReadHandler` | execute | Handler for killswitch.read operations. |
| `KillswitchWriteHandler` | execute | Handler for killswitch.write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register killswitch operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## knowledge_lifecycle_manager.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_lifecycle_manager.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 908

**Docstring:** GAP-086: Knowledge Lifecycle Manager

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GateDecision` |  | Policy gate decision. |
| `GateResult` | __bool__, allowed, blocked, pending | Result of a policy gate check. |
| `LifecycleAuditEventType` |  | Types of lifecycle audit events. |
| `LifecycleAuditEvent` | to_dict | Audit event for lifecycle transitions (GAP-088). |
| `KnowledgePlane` | record_state_change | In-memory representation of a knowledge plane. |
| `TransitionRequest` |  | Request to transition a knowledge plane to a new state. |
| `TransitionResponse` | to_dict | Response from a transition attempt. |
| `KnowledgeLifecycleManager` | __init__, handle_transition, _handle_register, get_state, get_plane, get_history, get_audit_log, get_next_action (+14 more) | GAP-086: Knowledge Lifecycle Manager — THE ORCHESTRATOR. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `utc_now` | `() -> datetime` | no | Return timezone-aware UTC datetime. |
| `generate_id` | `(prefix: str = 'kp') -> str` | no | Generate a unique ID with prefix. |
| `get_knowledge_lifecycle_manager` | `() -> KnowledgeLifecycleManager` | no | Get the singleton KnowledgeLifecycleManager instance. |
| `reset_manager` | `() -> None` | no | Reset the singleton instance (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, List, Optional | no |
| `uuid` | uuid4 | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState, LifecycleAction, TransitionResult, is_valid_transition, validate_transition (+4) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`KnowledgeLifecycleManager`, `KnowledgePlane`, `TransitionRequest`, `TransitionResponse`, `GateDecision`, `GateResult`, `LifecycleAuditEventType`, `LifecycleAuditEvent`, `get_knowledge_lifecycle_manager`, `reset_manager`

---

## knowledge_plane.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/drivers/knowledge_plane.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 482

**Docstring:** KnowledgePlane - Knowledge plane models and registry.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KnowledgePlaneStatus` |  | Status of a knowledge plane. |
| `KnowledgeNodeType` |  | Types of knowledge nodes. |
| `KnowledgeNode` | add_child, add_related, to_dict | A node in the knowledge graph. |
| `KnowledgePlane` | add_node, get_node, remove_node, add_source, remove_source, activate, deactivate, start_indexing (+4 more) | Representation of a knowledge plane. |
| `KnowledgePlaneError` | __init__, to_dict | Exception for knowledge plane errors. |
| `KnowledgePlaneStats` | to_dict | Statistics for knowledge planes. |
| `KnowledgePlaneRegistry` | __init__, register, get, get_by_name, list, delete, get_statistics, clear_tenant (+1 more) | Registry for managing knowledge planes. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_knowledge_plane_registry` | `() -> KnowledgePlaneRegistry` | no | Get the singleton registry instance. |
| `_reset_registry` | `() -> None` | no | Reset the singleton (for testing). |
| `create_knowledge_plane` | `(tenant_id: str, name: str, description: Optional[str] = None) -> KnowledgePlane` | no | Create a new knowledge plane using the singleton registry. |
| `get_knowledge_plane` | `(plane_id: str) -> Optional[KnowledgePlane]` | no | Get a knowledge plane by ID using the singleton registry. |
| `list_knowledge_planes` | `(tenant_id: Optional[str] = None) -> list[KnowledgePlane]` | no | List knowledge planes using the singleton registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## knowledge_sdk.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_sdk.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 971

**Docstring:** GAP-083-085: Knowledge SDK Façade

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KnowledgePlaneConfig` |  | Configuration for creating a knowledge plane. |
| `WaitOptions` |  | Options for wait operations. |
| `SDKResult` | from_transition_response, error, to_dict | Structured result from SDK operations. |
| `PlaneInfo` | from_plane, to_dict | Information about a knowledge plane for SDK consumers. |
| `KnowledgeSDK` | __init__, register, verify, ingest, index, classify, request_activation, activate (+16 more) | GAP-083-085: Knowledge SDK Façade. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_knowledge_sdk` | `(tenant_id: str, actor_id: Optional[str] = None) -> KnowledgeSDK` | no | Create a KnowledgeSDK instance for a tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `time` | time | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState, LifecycleAction | no |
| `app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager` | KnowledgeLifecycleManager, KnowledgePlane, TransitionRequest, TransitionResponse, GateDecision (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`KnowledgeSDK`, `KnowledgePlaneConfig`, `WaitOptions`, `SDKResult`, `PlaneInfo`, `create_knowledge_sdk`

---

## leadership_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/leadership_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 123

**Docstring:** Leadership Coordinator (PIN-513 Batch 3A6 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LeadershipCoordinator` | try_acquire, release, is_held, with_lock, with_canary_lock, with_alert_worker_lock, with_archiver_lock | L4 coordinator: distributed locking primitives. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Callable | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## ledger.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/ledger.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 251

**Docstring:** Discovery Ledger - signal recording helpers (pure driver).

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DiscoverySignal` |  | Discovery signal data model. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `emit_signal` | `(connection: Any, artifact: str, signal_type: str, evidence: dict[str, Any], det` | no | Record a discovery signal to the ledger. |
| `get_signals` | `(connection: Any, artifact: Optional[str] = None, signal_type: Optional[str] = N` | no | Query discovery signals from the ledger. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `decimal` | Decimal | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `pydantic` | BaseModel, Field | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.exc` | SQLAlchemyError | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## lessons_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/lessons_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 92

**Docstring:** Lessons Coordinator (C4 — Loop Model)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LessonsCoordinator` | record_evidence | Cross-domain evidence recorder. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_lessons_coordinator` | `() -> LessonsCoordinator` | no | Get the singleton LessonsCoordinator instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`LessonsCoordinator`, `get_lessons_coordinator`

---

## lifecycle_facade.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/lifecycle_facade.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 709

**Docstring:** Lifecycle Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AgentState` |  | Agent lifecycle states. |
| `RunState` |  | Run lifecycle states. |
| `AgentLifecycle` | to_dict | Agent lifecycle information. |
| `RunLifecycle` | to_dict | Run lifecycle information. |
| `LifecycleSummary` | to_dict | Summary of lifecycle entities. |
| `LifecycleFacade` | __init__, create_agent, list_agents, get_agent, start_agent, stop_agent, terminate_agent, create_run (+6 more) | Facade for lifecycle operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_lifecycle_facade` | `() -> LifecycleFacade` | no | Get the lifecycle facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## lifecycle_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/lifecycle_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 170

**Docstring:** Lifecycle Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccountLifecycleQueryHandler` | execute | Handler for account.lifecycle.query operations. |
| `AccountLifecycleTransitionHandler` | execute | Handler for account.lifecycle.transition operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register lifecycle operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## lifecycle_harness.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/lifecycle_harness.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 86

**Docstring:** Lifecycle Harness Kit

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LifecycleReaderPort` | get_state | Behavioral contract for lifecycle state reads. |
| `LifecycleWriterPort` | transition | Behavioral contract for lifecycle state mutations. |
| `LifecycleGateDecision` |  | Decision from lifecycle gate evaluation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, Optional, Protocol, runtime_checkable | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`LifecycleReaderPort`, `LifecycleWriterPort`, `LifecycleGateDecision`

---

## lifecycle_provider.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/lifecycle_provider.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 363

**Docstring:** Phase-9 Tenant Lifecycle Provider (Canonical)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ActorType` |  | Who initiated the lifecycle action. |
| `ActorContext` |  | Context about who is performing the action. |
| `TransitionResult` | to_audit_record | Result of a lifecycle transition attempt. |
| `LifecycleTransitionRecord` |  | Historical record of a lifecycle transition. |
| `TenantLifecycleProvider` | get_state, transition, suspend, resume, terminate, archive, get_history, allows_sdk_execution (+2 more) | Protocol for tenant lifecycle operations. |
| `MockTenantLifecycleProvider` | __init__, get_state, _emit_event, transition, _record_history, suspend, resume, terminate (+7 more) | Deterministic mock implementation of TenantLifecycleProvider. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_lifecycle_provider` | `() -> TenantLifecycleProvider` | no |  |
| `set_lifecycle_provider` | `(provider: TenantLifecycleProvider) -> None` | no |  |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Callable, Dict, List, Optional, Protocol | no |
| `app.hoc.cus.account.L5_schemas.tenant_lifecycle_state` | LifecycleAction, TenantLifecycleState, get_action_for_transition, is_valid_transition | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`ActorType`, `ActorContext`, `TransitionResult`, `LifecycleTransitionRecord`, `TenantLifecycleProvider`, `MockTenantLifecycleProvider`, `get_lifecycle_provider`, `set_lifecycle_provider`

---

## lifecycle_stages_base.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/lifecycle_stages_base.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 317

**Docstring:** Stage Handler Protocol and Base Types

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StageStatus` |  | Result status from stage execution. |
| `StageContext` |  | Context passed to stage handlers. |
| `StageResult` | success, is_async, ok, fail, pending, skipped | Result returned by stage handlers. |
| `StageHandler` | stage_name, handles_states, execute, validate | Protocol for stage handlers. |
| `BaseStageHandler` | stage_name, handles_states, validate, execute | Base class for stage handlers. |
| `StageRegistry` | __init__, register, get_handler, has_handler, create_default | Registry of stage handlers. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional, Protocol, runtime_checkable | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## logs_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 91

**Docstring:** Logs Bridge (PIN-510)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LogsBridge` | logs_read_service, traces_store_capability, audit_ledger_read_capability, capture_driver_capability, cost_intelligence_capability | Capabilities for logs domain. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_logs_bridge` | `() -> LogsBridge` | no | Get the singleton LogsBridge instance. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`LogsBridge`, `get_logs_bridge`

---

## logs_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/logs_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 389

**Docstring:** Logs Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LogsQueryHandler` | execute | Handler for logs.query operations. |
| `LogsEvidenceHandler` | execute | Handler for logs.evidence operations. |
| `LogsCertificateHandler` | execute | Handler for logs.certificate operations. |
| `LogsReplayHandler` | execute | Handler for logs.replay operations. |
| `LogsEvidenceReportHandler` | execute | Handler for logs.evidence_report operations. |
| `LogsPdfHandler` | execute | Handler for logs.pdf operations. |
| `LogsCaptureHandler` | execute | Handler for logs.capture operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register logs operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## m25_integration_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/m25_integration_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 407

**Docstring:** M25 Integration Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `M25ReadStagesHandler` | execute | Handler for m25.read_stages operation. |
| `M25ReadCheckpointHandler` | execute | Handler for m25.read_checkpoint operation. |
| `M25ReadStatsHandler` | execute | Handler for m25.read_stats operation — combines all 6 stats queries. |
| `M25ReadSimulationStateHandler` | execute | Handler for m25.read_simulation_state operation. |
| `M25ReadTimelineHandler` | execute | Handler for m25.read_timeline operation — combines incident + events + preventions + regrets. |
| `M25WritePreventionHandler` | execute | Handler for m25.write_prevention operation. |
| `M25WriteRegretHandler` | execute | Handler for m25.write_regret operation. |
| `M25WriteTimelineViewHandler` | execute | Handler for m25.write_timeline_view operation. |
| `M25WriteGraduationHistoryHandler` | execute | Handler for m25.write_graduation_history operation. |
| `M25UpdateGraduationStatusHandler` | execute | Handler for m25.update_graduation_status operation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register M25 integration operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## mcp_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/mcp_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 264

**Docstring:** MCP Servers Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `McpServersHandler` | execute | Handler for integrations.mcp_servers operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register MCP server operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## metrics_helpers.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/metrics_helpers.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 210

**Docstring:** Prometheus Metrics Helpers - Idempotent Registration

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_find_existing_metric` | `(name: str)` | no | Find an existing metric in the registry by name. |
| `get_or_create_counter` | `(name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Count` | no | Get existing counter or create new one - idempotent. |
| `get_or_create_gauge` | `(name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Gauge` | no | Get existing gauge or create new one - idempotent. |
| `get_or_create_histogram` | `(name: str, documentation: str, labelnames: Optional[List[str]] = None, buckets:` | no | Get existing histogram or create new one - idempotent. |
| `validate_metric_name` | `(name: str) -> bool` | no | Validate metric name follows conventions. |
| `reset_metrics_registry` | `()` | no | Reset the Prometheus registry for test isolation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | List, Optional | no |
| `prometheus_client` | REGISTRY, Counter, Gauge, Histogram | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`VALID_SUFFIXES`

---

## monitors_facade.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/monitors_facade.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 541

**Docstring:** Monitors Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MonitorType` |  | Types of monitors. |
| `MonitorStatus` |  | Monitor status. |
| `CheckStatus` |  | Health check result status. |
| `MonitorConfig` | to_dict | Monitor configuration. |
| `HealthCheckResult` | to_dict | Health check result. |
| `MonitorStatusSummary` | to_dict | Overall monitoring status summary. |
| `MonitorsFacade` | __init__, create_monitor, list_monitors, get_monitor, update_monitor, delete_monitor, run_check, get_check_history (+1 more) | Facade for monitor operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_monitors_facade` | `() -> MonitorsFacade` | no | Get the monitors facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## offboarding.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/offboarding.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 537

**Docstring:** Offboarding Stage Handlers

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DeregisterHandler` | stage_name, handles_states, validate, execute, _check_active_references, _check_dependents | GAP-078: Start offboarding process. |
| `VerifyDeactivateHandler` | stage_name, handles_states, validate, execute, _check_active_usage | GAP-079: Verify deactivation is safe. |
| `DeactivateHandler` | stage_name, handles_states, validate, execute, _perform_deactivation | GAP-080: Deactivate knowledge plane (soft delete). |
| `ArchiveHandler` | stage_name, handles_states, validate, execute, _perform_archive | GAP-081: Archive knowledge plane to cold storage. |
| `PurgeHandler` | stage_name, handles_states, validate, execute, _perform_purge | GAP-082: Purge knowledge plane (permanent deletion). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState | no |
| `app.hoc.cus.hoc_spine.services.lifecycle_stages_base` | BaseStageHandler, StageContext, StageResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## onboarding.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/onboarding.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 709

**Docstring:** Onboarding Stage Handlers

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RegisterHandler` | stage_name, handles_states, validate, execute | GAP-071: Register knowledge plane. |
| `VerifyHandler` | stage_name, handles_states, validate, execute, _simulate_verification | GAP-072: Verify knowledge plane connectivity. |
| `IngestHandler` | stage_name, handles_states, validate, execute | GAP-073: Ingest data from knowledge source. |
| `IndexHandler` | stage_name, handles_states, validate, execute | GAP-074: Create indexes and embeddings. |
| `ClassifyHandler` | stage_name, handles_states, validate, execute | GAP-075: Classify data sensitivity and schema. |
| `ActivateHandler` | stage_name, handles_states, validate, execute, _simulate_activation | GAP-076: Activate knowledge plane. |
| `GovernHandler` | stage_name, handles_states, validate, execute | GAP-077: Runtime governance hooks. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, Optional | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState | no |
| `app.hoc.cus.hoc_spine.services.lifecycle_stages_base` | BaseStageHandler, StageContext, StageResult, StageStatus | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## onboarding_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 317

**Docstring:** Onboarding Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccountOnboardingQueryHandler` | execute | Handler for account.onboarding.query operations. |
| `AccountOnboardingAdvanceHandler` | execute | Handler for account.onboarding.advance operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `async_advance_onboarding` | `(tenant_id: str, target_state: int, trigger: str) -> dict` | yes | L4-owned async onboarding advance for middleware/async call sites. |
| `async_get_onboarding_state` | `(tenant_id: str) -> Optional[int]` | yes | L4-owned async onboarding state read. |
| `async_detect_stalled_onboarding` | `(threshold_hours: int = 24) -> list[dict]` | yes | L4-owned stalled onboarding detection. |
| `register` | `(registry: OperationRegistry) -> None` | no | Register onboarding operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `typing` | Optional | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## onboarding_policy.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 185

**Docstring:** Onboarding Gate Policy (Canonical)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_required_state` | `(path: str) -> Optional[OnboardingState]` | no | Get the required onboarding state for a path. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `re` | re | no |
| `typing` | Optional, Tuple | no |
| `app.hoc.cus.account.L5_schemas.onboarding_state` | OnboardingState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AUTH_EXEMPT_PREFIXES`, `NON_TENANT_PREFIXES`, `INFRA_PATHS`, `ENDPOINT_STATE_REQUIREMENTS`, `ENDPOINT_PATTERN_REQUIREMENTS`, `get_required_state`

---

## operation_registry.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 620

**Docstring:** Operation Registry (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OperationContext` |  | Immutable context passed to every operation handler. |
| `OperationResult` | ok, fail | Outcome of an operation dispatch. |
| `OperationHandler` | execute | Protocol for domain operation handlers. |
| `OperationRegistry` | __init__, register, freeze, execute, _check_authority, _audit_dispatch, operations, operation_count (+4 more) | Central dispatch for domain operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_session_dep` | `() -> AsyncGenerator[AsyncSession, None]` | yes | L4-provided session dependency for L2 endpoints. |
| `get_sync_session_dep` | `() -> Generator` | no | L4-provided SYNC session dependency for L2 endpoints that use |
| `sql_text` | `(sql: str)` | no | L4-provided wrapper for sqlalchemy text(). |
| `get_async_session_context` | `()` | yes | L4-provided async session context manager for L2 endpoints that |
| `get_operation_registry` | `() -> OperationRegistry` | no | Get the operation registry singleton. |
| `reset_operation_registry` | `() -> None` | no | Reset the registry singleton. FOR TESTING ONLY. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `time` | time | no |
| `dataclasses` | dataclass, field | no |
| `contextlib` | asynccontextmanager | no |
| `typing` | TYPE_CHECKING, Any, AsyncGenerator, Generator, Optional (+2) | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`REGISTRY_VERSION`

---

## ops_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/ops_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 102

**Docstring:** Ops Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostOpsHandler` | execute | Handler for ops.cost operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register ops domain handlers. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## orphan_recovery_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/orphan_recovery_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 202

**Docstring:** Orphan Recovery Handler (PIN-513 Batch 1A Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OrphanRecoveryHandler` | execute, get_summary | L4 handler: orphan recovery orchestration. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`ORPHAN_THRESHOLD_MINUTES`, `RECOVERY_ENABLED`

---

## overview_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/overview_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 105

**Docstring:** Overview Bridge (L4 Coordinator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OverviewBridge` | overview_capability, dashboard_capability | Overview domain capability factory. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_overview_bridge` | `() -> OverviewBridge` | no | Get the overview bridge singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`OverviewBridge`, `get_overview_bridge`

---

## overview_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/overview_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 73

**Docstring:** Overview Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OverviewQueryHandler` | execute | Handler for overview.query operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register overview operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## phase_status_invariants.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/phase_status_invariants.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 361

**Docstring:** Module: phase_status_invariants

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `InvariantCheckResult` |  | Result of an invariant check. |
| `PhaseStatusInvariantEnforcementError` | __init__, to_dict | Raised when phase-status invariant enforcement fails. |
| `InvariantCheckResponse` | to_dict | Response from an invariant check. |
| `PhaseStatusInvariantChecker` | __init__, from_governance_config, enforcement_enabled, get_allowed_statuses, is_valid_combination, check, ensure_valid, should_allow_transition | Checks and enforces phase-status invariants. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_phase_status_invariant` | `(phase: str, status: str, enforcement_enabled: bool = True) -> InvariantCheckRes` | no | Quick helper to check a phase-status invariant. |
| `ensure_phase_status_invariant` | `(phase: str, status: str, enforcement_enabled: bool = True) -> None` | no | Quick helper to ensure phase-status invariant or raise error. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, FrozenSet, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## pipeline.py
**Path:** `backend/app/hoc/cus/hoc_spine/consequences/pipeline.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 140

**Docstring:** Consequences Pipeline.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConsequencePipeline` | __init__, register, freeze, is_frozen, adapter_count, adapter_names, run | Post-dispatch consequence pipeline. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_consequence_pipeline` | `() -> ConsequencePipeline` | no | Get the consequence pipeline singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Optional | no |
| `app.hoc.cus.hoc_spine.consequences.ports` | ConsequenceAdapter | no |
| `app.hoc.cus.hoc_spine.services.dispatch_audit` | DispatchRecord | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## plan.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/plan.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 259

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

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_utc_now` | `() -> datetime` | no | UTC timestamp (inlined to keep schemas pure — no service imports). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `pydantic` | BaseModel, ConfigDict, Field, field_validator | no |
| `retry` | RetryPolicy | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## plan_generation_engine.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/plan_generation_engine.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 265

**Docstring:** Domain engine for plan generation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlanGenerationContext` |  | Context for plan generation. |
| `PlanGenerationResult` |  | Result of plan generation. |
| `PlanGenerationEngine` | __init__, generate | L4 Domain Engine for plan generation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_plan_for_run` | `(agent_id: str, goal: str, run_id: str) -> PlanGenerationResult` | no | Convenience function to generate a plan for a run. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.memory` | get_retriever | no |
| `app.planners` | get_planner | no |
| `app.skills` | get_skill_manifest | no |
| `app.utils.budget_tracker` | get_budget_tracker | no |
| `app.utils.plan_inspector` | validate_plan | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`PlanGenerationContext`, `PlanGenerationResult`, `PlanGenerationEngine`, `generate_plan_for_run`

---

## platform_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/platform_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 90

**Docstring:** Platform Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlatformHealthHandler` | execute | Handler for platform.health operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register platform operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## policies_bridge.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/policies_bridge.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 180

**Docstring:** Policies Bridge (PIN-510)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PoliciesBridge` | customer_policy_read_capability, policy_evaluations_capability, recovery_write_capability, recovery_matcher_capability, recovery_read_capability | Capabilities for policies domain. Max 5 methods. |
| `PoliciesEngineBridge` | prevention_hook_capability, policy_engine_capability, policy_engine_class_capability, governance_runtime_capability, governance_config_capability, sandbox_engine_capability, policy_engine_write_context | Extended capabilities for policies domain engines. Max 5 methods. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policies_engine_bridge` | `() -> PoliciesEngineBridge` | no | Get the singleton PoliciesEngineBridge instance. |
| `get_policies_bridge` | `() -> PoliciesBridge` | no | Get the singleton PoliciesBridge instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `contextlib` | contextmanager | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`PoliciesBridge`, `get_policies_bridge`, `PoliciesEngineBridge`, `get_policies_engine_bridge`

---

## policies_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 1658

**Docstring:** Policies Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PoliciesQueryHandler` | execute | Handler for policies.query operations. |
| `PoliciesEnforcementHandler` | execute | Handler for policies.enforcement operations. |
| `PoliciesGovernanceHandler` | execute | Handler for policies.governance operations. |
| `PoliciesLessonsHandler` | execute | Handler for policies.lessons operations. |
| `PoliciesPolicyFacadeHandler` | execute | Handler for policies.policy_facade operations. |
| `PoliciesLimitsHandler` | execute | Handler for policies.limits operations. |
| `PoliciesRulesHandler` | execute | Handler for policies.rules operations. |
| `PoliciesRateLimitsHandler` | execute | Handler for policies.rate_limits operations. |
| `PoliciesSimulateHandler` | execute | Handler for policies.simulate operations. |
| `PoliciesLimitsQueryHandler` | execute | Handler for policies.limits_query operations (PIN-513 Batch 2B). |
| `PoliciesProposalsQueryHandler` | execute | Handler for policies.proposals_query operations (PIN-513 Batch 2B). |
| `PoliciesRulesQueryHandler` | execute | Handler for policies.rules_query operations (PIN-513 Batch 2B). |
| `PoliciesHealthHandler` | execute | Handler for policies.health operations (PIN-520 Phase 1). |
| `PoliciesRecoveryMatchHandler` | execute | Handler for policies.recovery.match operations. |
| `PoliciesRecoveryWriteHandler` | execute | Handler for policies.recovery.write operations. |
| `PoliciesGuardReadHandler` | execute | Handler for policies.guard_read operations. |
| `PoliciesSyncGuardReadHandler` | execute | Handler for policies.sync_guard_read operations. |
| `PoliciesCustomerVisibilityHandler` | execute | Handler for policies.customer_visibility operations. |
| `PoliciesRecoveryReadHandler` | execute | Handler for policies.recovery.read operations. |
| `PoliciesReplayHandler` | execute | Handler for policies.replay operations. |
| `RbacAuditHandler` | execute | Handler for rbac.audit_query and rbac.audit_cleanup operations. |
| `PoliciesWorkersHandler` | execute | Handler for policies.workers operations. |
| `PoliciesEnforcementWriteHandler` | execute | Handler for policies.enforcement_write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_policy_write_ctx` | `(facade)` | no | L4 transaction context for PolicyEngine write operations. |
| `register` | `(registry: OperationRegistry) -> None` | no | Register policies domain handlers. |
| `record_enforcement_standalone` | `(tenant_id: str, rule_id: str, action_taken: str, run_id: Optional[str] = None, ` | yes | Record a policy enforcement event via L4 handler (L4 owns commit). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `contextlib` | contextmanager | no |
| `typing` | Any, Dict, Optional | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## policies_sandbox_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_sandbox_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 75

**Docstring:** Policies Sandbox Handler (GAP-174)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PoliciesSandboxExecuteHandler` | execute | Handler for policies.sandbox_execute. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register policies sandbox operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## policy_approval_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policy_approval_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 446

**Docstring:** Policy Approval Handler (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyApprovalHandler` | execute, _get_approval_level_config, _create_approval_request, _get_approval_request, _get_approval_request_for_action, _get_approval_request_for_reject, _update_approval_request_status, _update_approval_request_approved (+10 more) | L4 handler: policy approval workflow operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_approval_handler` | `() -> PolicyApprovalHandler` | no | Factory function for PolicyApprovalHandler. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationHandler, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`PolicyApprovalHandler`, `get_policy_approval_handler`

---

## policy_governance_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policy_governance_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 257

**Docstring:** Policy Governance Handler (PIN-513 Batch 2B Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyGovernanceHandler` | check_eligibility, create_proposal, review_proposal, delete_rule, get_summary, generate_rule_template, create_snapshot, get_active_snapshot (+3 more) | L4 handler: policy proposal lifecycle + snapshot governance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | UUID | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## pool_manager.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/pool_manager.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 606

**Docstring:** Connection Pool Manager (GAP-172)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PoolType` |  | Types of connection pools. |
| `PoolStatus` |  | Pool health status. |
| `PoolConfig` |  | Configuration for a connection pool. |
| `PoolStats` | to_dict | Statistics for a connection pool. |
| `PoolHandle` |  | Handle to a managed connection pool. |
| `ConnectionPoolManager` | __init__, start, stop, create_database_pool, create_redis_pool, create_http_pool, get_pool, acquire_connection (+6 more) | Unified connection pool manager. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## ports.py
**Path:** `backend/app/hoc/cus/hoc_spine/consequences/ports.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 60

**Docstring:** Consequence Adapter Protocol.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConsequenceAdapter` | name, handle | Port for post-dispatch consequence adapters. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Protocol, runtime_checkable | no |
| `app.hoc.cus.hoc_spine.services.dispatch_audit` | DispatchRecord | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## profile_policy_mode.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/profile_policy_mode.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 459

**Docstring:** Governance Profile Configuration

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceProfile` |  | Pre-defined governance profiles. |
| `GovernanceConfig` | to_dict | Complete governance configuration derived from profile + overrides. |
| `GovernanceConfigError` | __init__ | Raised when governance configuration is invalid. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_bool_env` | `(name: str, default: bool) -> bool` | no | Get boolean from environment variable. |
| `get_governance_profile` | `() -> GovernanceProfile` | no | Get the current governance profile from environment. |
| `load_governance_config` | `() -> GovernanceConfig` | no | Load complete governance configuration. |
| `validate_governance_config` | `(config: Optional[GovernanceConfig] = None) -> List[str]` | no | Validate governance configuration for invalid combinations. |
| `get_governance_config` | `() -> GovernanceConfig` | no | Get the validated governance configuration singleton. |
| `reset_governance_config` | `() -> None` | no | Reset the singleton (for testing). |
| `validate_governance_at_startup` | `() -> None` | no | Validate governance configuration at application startup. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Dict, FrozenSet, List, Optional, Tuple | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## protocols.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/protocols.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 335

**Docstring:** L1 Re-wiring Protocol Interfaces (PIN-513)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LessonsEnginePort` | emit_near_threshold, emit_critical_success | Behavioral contract for lessons learned engine. |
| `PolicyEvaluationPort` | __call__ | Behavioral contract for policy evaluation service. |
| `TraceFacadePort` | complete_trace_sync | Behavioral contract for trace facade. |
| `ConnectorLookupPort` | get_connector | Behavioral contract for connector registry lookup. |
| `ValidatorVerdictPort` | issue_type, severity, affected_capabilities, recommended_action, confidence_score, reason, analyzed_at | Behavioral contract for CRM validator verdict type. |
| `EligibilityVerdictPort` | decision, reason, decided_at, rule_results | Behavioral contract for eligibility verdict type. |
| `TraceStorePort` | get_trace, list_traces, get_trace_summary, get_trace_steps | Behavioral contract for trace storage. |
| `CircuitBreakerPort` | is_v2_disabled, report_drift, get_circuit_breaker_state | Behavioral contract for circuit breaker operations. |
| `IntegrityDriverPort` | verify_integrity, get_integrity_proof | Behavioral contract for integrity verification. |
| `MCPAuditEmitterPort` | emit_tool_requested, emit_tool_allowed, emit_tool_denied, emit_tool_started, emit_tool_completed, emit_tool_failed | Behavioral contract for MCP audit event emission. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `typing` | Any, Dict, Optional, Protocol, runtime_checkable | no |
| `uuid` | UUID | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`LessonsEnginePort`, `PolicyEvaluationPort`, `TraceFacadePort`, `ConnectorLookupPort`, `ValidatorVerdictPort`, `EligibilityVerdictPort`, `TraceStorePort`, `CircuitBreakerPort`, `IntegrityDriverPort`, `MCPAuditEmitterPort`

---

## provenance_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/provenance_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 176

**Docstring:** Provenance Coordinator (PIN-513 Batch 3A5 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProvenanceCoordinator` | write, write_batch, query, count, get_drift_stats, check_duplicate, compute_input_hash, backfill_v1_baseline | L4 coordinator: provenance logging DB operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## proxy_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/proxy_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 151

**Docstring:** Proxy Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProxyHandler` | execute | Handler for proxy.* operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register proxy operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## rac_models.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/rac_models.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 409

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AckStatus`, `AuditAction`, `AuditDomain`, `AuditStatus`, `AuditExpectation`, `DomainAck`, `ReconciliationResult`, `create_domain_ack`, `create_run_expectations`

---

## rate_limiter.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/rate_limiter.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 184

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RateLimiter` | __init__, _get_client, allow, get_remaining | Token bucket rate limiter using Redis. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_rate_limiter` | `() -> RateLimiter` | no | Get the singleton rate limiter instance. |
| `allow_request` | `(key: str, rate_per_min: int) -> bool` | no | Convenience function to check rate limit. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `time` | time | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`REDIS_URL`, `TOKEN_BUCKET_LUA`

---

## rbac_policy.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/rbac_policy.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 544

**Docstring:** RBAC Policy (Canonical)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyObject` |  | Represents an authorization policy for a resource action. |
| `Decision` |  | Result of an authorization decision. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_for_path` | `(path: str, method: str) -> Optional[PolicyObject]` | no | Map request path and method to a PolicyObject. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`CURRENT_ENVIRONMENT`

### __all__ Exports
`PolicyObject`, `Decision`, `RBAC_MATRIX`, `CURRENT_ENVIRONMENT`, `get_policy_for_path`

---

## recovery_decisions.py
**Path:** `backend/app/hoc/cus/hoc_spine/utilities/recovery_decisions.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 97

**Docstring:** Recovery Decision Utilities (Spine Utility)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `combine_confidences` | `(rule_confidence: float, match_confidence: float) -> float` | no | Combine rule and matcher confidence scores. |
| `should_select_action` | `(combined_confidence: float) -> bool` | no | Determine if an action should be selected based on combined confidence. |
| `should_auto_execute` | `(confidence: float) -> bool` | no | Determine if a recovery action should be auto-executed based on confidence. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`AUTO_EXECUTE_CONFIDENCE_THRESHOLD`, `ACTION_SELECTION_THRESHOLD`, `combine_confidences`, `should_select_action`, `should_auto_execute`

---

## replay_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/replay_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 130

**Docstring:** Replay Coordinator (PIN-513 Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ReplayCoordinator` | __init__, _get_enforcer, enforce_step, enforce_trace | L4 coordinator: deterministic replay enforcement. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Awaitable, Callable, Dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## response.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/response.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 340

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`T`

---

## retrieval_facade.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/retrieval_facade.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 518

**Docstring:** Retrieval Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccessResult` | to_dict | Result of a mediated data access. |
| `PlaneInfo` | to_dict | Information about a knowledge plane. |
| `EvidenceInfo` | to_dict | Evidence record information. |
| `RetrievalFacade` | __init__, mediator, access_data, list_planes, register_plane, get_plane, list_evidence, get_evidence (+1 more) | Facade for mediated data retrieval operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_retrieval_facade` | `() -> RetrievalFacade` | no | Get the retrieval facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## retrieval_mediator.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/retrieval_mediator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 471

**Docstring:** Module: retrieval_mediator

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MediationAction` |  | Allowed mediation actions. |
| `MediatedResult` |  | Result of a mediated data access. |
| `PolicyCheckResult` |  | Result of policy check. |
| `EvidenceRecord` |  | Evidence record for a mediated access. |
| `MediationDeniedError` | __init__ | Raised when mediation denies access. |
| `Connector` | execute | Protocol for connectors. |
| `ConnectorRegistry` | resolve | Protocol for connector registry. |
| `PolicyChecker` | check_access | Protocol for policy checking. |
| `EvidenceService` | record | Protocol for evidence recording. |
| `RetrievalMediator` | __init__, access, _check_policy, _resolve_connector, _record_evidence, _hash_payload | Unified mediation layer for all external data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_retrieval_mediator` | `() -> RetrievalMediator` | no | Get or create the singleton RetrievalMediator. |
| `configure_retrieval_mediator` | `(policy_checker: Optional[PolicyChecker] = None, connector_registry: Optional[Co` | no | Configure the singleton RetrievalMediator with dependencies. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional, Protocol (+1) | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## retry.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/retry.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 89

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## route_planes.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/route_planes.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 257

**Docstring:** Route Plane Policy (Canonical)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlaneRequirement` |  | What authentication plane(s) a route accepts. |
| `RoutePlaneRule` | __post_init__, matches | A rule mapping route pattern to plane requirement. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_plane_requirement` | `(path: str) -> PlaneRequirement` | no | Get the plane requirement for a path. |
| `check_plane_match` | `(path: str, actual_plane: AuthPlane) -> tuple[bool, Optional[str]]` | no | Check if the actual auth plane matches the route requirement. |
| `is_worker_path` | `(path: str) -> bool` | no | Check if path is a worker execution path (MACHINE_ONLY). |
| `is_admin_path` | `(path: str) -> bool` | no | Check if path is an admin/founder path (HUMAN_ONLY). |
| `enforce_plane_requirement` | `(path: str, actual_plane: AuthPlane) -> Optional[dict]` | yes | Enforce plane requirement for a path. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `re` | re | no |
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Optional | no |
| `app.auth.contexts` | AuthPlane | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`PlaneRequirement`, `RoutePlaneRule`, `ROUTE_PLANE_RULES`, `get_plane_requirement`, `check_plane_match`, `is_worker_path`, `is_admin_path`, `enforce_plane_requirement`

---

## run_evidence_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_evidence_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 239

**Docstring:** Run Evidence Coordinator (PIN-519)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunEvidenceCoordinator` | get_run_evidence, _get_incidents_for_run, _get_policy_evaluations_for_run, _get_limit_breaches_for_run, _derive_decisions | L4 coordinator: Compose run impact from multiple domains. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_run_evidence_coordinator` | `() -> RunEvidenceCoordinator` | no | Get the singleton RunEvidenceCoordinator instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any | no |
| `app.hoc.cus.hoc_spine.schemas.run_introspection_protocols` | DecisionSummary, IncidentSummary, LimitHitSummary, PolicyEvaluationSummary, RunEvidenceResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`RunEvidenceCoordinator`, `get_run_evidence_coordinator`

---

## run_governance_facade.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 422

**Docstring:** Run Governance Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunGovernanceFacade` | __init__, _lessons, create_policy_evaluation, _emit_ack, emit_near_threshold_lesson, emit_critical_success_lesson | Facade for run governance operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `wire_run_governance_facade` | `() -> RunGovernanceFacade` | no | Wire the RunGovernanceFacade singleton with real L5 engines. |
| `get_run_governance_facade` | `() -> RunGovernanceFacade` | no | Get the run governance facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.hoc_spine.schemas.protocols` | LessonsEnginePort, PolicyEvaluationPort | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`RAC_ENABLED`

---

## run_governance_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/run_governance_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 210

**Docstring:** Run Governance Handler (PIN-513 Batch 1B Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunGovernanceHandler` | evaluate_run, report_violation, create_evaluation | L4 handler: run governance policy evaluation and violation handling. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## run_introspection_protocols.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/run_introspection_protocols.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 257

**Docstring:** Run Introspection Protocol Interfaces (PIN-519)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentSummary` |  | Summary of an incident caused by a run. |
| `PolicyEvaluationSummary` |  | Summary of a policy evaluation for a run. |
| `LimitHitSummary` |  | Summary of a limit breach for a run. |
| `DecisionSummary` |  | Summary of a decision made during a run. |
| `RunEvidenceResult` |  | Cross-domain impact evidence for a run. |
| `IntegrityVerificationResult` |  | Integrity verification status for a run's trace chain. |
| `TraceSummary` |  | Summary of a trace record. |
| `TraceStepSummary` |  | Summary of a trace step. |
| `RunProofResult` |  | Integrity proof for a run. |
| `SignalFeedbackResult` |  | Feedback status for a signal from audit ledger. |
| `RunEvidenceProvider` | get_run_evidence | Behavioral contract for run evidence queries. |
| `RunProofProvider` | get_run_proof | Behavioral contract for run integrity proof queries. |
| `SignalFeedbackProvider` | get_signal_feedback | Behavioral contract for signal feedback queries. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Literal, Protocol, runtime_checkable | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`INTEGRITY_CONFIG`

### __all__ Exports
`INTEGRITY_CONFIG`, `IncidentSummary`, `PolicyEvaluationSummary`, `LimitHitSummary`, `DecisionSummary`, `RunEvidenceResult`, `IntegrityVerificationResult`, `TraceSummary`, `TraceStepSummary`, `RunProofResult`, `SignalFeedbackResult`, `RunEvidenceProvider`, `RunProofProvider`, `SignalFeedbackProvider`

---

## run_proof_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_proof_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 255

**Docstring:** Run Proof Coordinator (PIN-519)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunProofCoordinator` | get_run_proof, _compute_integrity, _compute_hash_chain | L4 coordinator: Verify run integrity via traces. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_run_proof_coordinator` | `() -> RunProofCoordinator` | no | Get the singleton RunProofCoordinator instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any | no |
| `app.hoc.cus.hoc_spine.schemas.run_introspection_protocols` | INTEGRITY_CONFIG, IntegrityVerificationResult, RunProofResult, TraceStepSummary, TraceSummary | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`RunProofCoordinator`, `get_run_proof_coordinator`

---

## runtime.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/runtime.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 68

**Docstring:** Runtime Utilities - Centralized Shared Helpers

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_uuid` | `() -> str` | no | Generate a UUID string. |
| `utc_now` | `() -> datetime` | no | Return timezone-aware UTC datetime. |
| `utc_now_naive` | `() -> datetime` | no | Return timezone-naive UTC datetime (for asyncpg raw SQL compatibility). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `uuid` | uuid4 | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## runtime_adapter.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/runtime_adapter.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 217

**Docstring:** Runtime Adapter (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RuntimeAdapter` | __init__, query, get_supported_queries, describe_skill, list_skills, get_skill_descriptors, get_resource_contract, get_capabilities | Adapter for runtime operations. |

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`RuntimeAdapter`, `get_runtime_adapter`

---

## runtime_switch.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/runtime_switch.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 279

**Docstring:** Module: runtime_switch

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceState` |  | Current governance state. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `is_governance_active` | `() -> bool` | no | Check if governance is currently active. |
| `is_degraded_mode` | `() -> bool` | no | Check if system is in degraded mode (GAP-070). |
| `disable_governance_runtime` | `(reason: str, actor: str) -> None` | no | Emergency kill switch. Disables governance enforcement. |
| `enable_governance_runtime` | `(actor: str) -> None` | no | Re-enable governance after emergency. |
| `enter_degraded_mode` | `(reason: str, actor: str) -> None` | no | GAP-070: Enter degraded mode. |
| `exit_degraded_mode` | `(actor: str) -> None` | no | Exit degraded mode, return to normal operation. |
| `get_governance_state` | `() -> dict` | no | Get current governance state for health checks. |
| `reset_governance_state` | `() -> None` | no | Reset governance state to defaults (for testing). |
| `_emit_governance_event` | `(event_type: str, reason: str, actor: str) -> None` | no | Emit governance state change event. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `threading` | threading | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## s1_retry_backoff.py
**Path:** `backend/app/hoc/cus/hoc_spine/utilities/s1_retry_backoff.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 150

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_s1_envelope` | `(baseline_value: float = 100.0, reference_id: str = 'retry_policy_v3') -> Envelo` | no | Create a fresh S1 envelope instance with specified baseline. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.optimization.envelope` | BaselineSource, DeltaType, Envelope, EnvelopeBaseline, EnvelopeBounds (+5) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`S1_RETRY_BACKOFF_ENVELOPE`

---

## scheduler_facade.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/scheduler_facade.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 552

**Docstring:** Scheduler Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `JobStatus` |  | Job status. |
| `JobRunStatus` |  | Job run status. |
| `ScheduledJob` | to_dict | Scheduled job definition. |
| `JobRun` | to_dict | Job run history entry. |
| `SchedulerFacade` | __init__, create_job, list_jobs, get_job, update_job, delete_job, trigger_job, pause_job (+4 more) | Facade for scheduled job operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_scheduler_facade` | `() -> SchedulerFacade` | no | Get the scheduler facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## schema_parity.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/schema_parity.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 166

**Docstring:** M26 Prevention Mechanism #2: Startup Schema Parity Guard

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SchemaParityError` |  | Raised when model schema doesn't match database schema. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_schema_parity` | `(engine: Engine, models: Optional[List[type]] = None, hard_fail: bool = True) ->` | no | Check that SQLModel definitions match actual database schema. |
| `check_m26_cost_tables` | `(engine: Engine) -> Tuple[bool, List[str]]` | no | Specific check for M26 cost tables - the most critical. |
| `run_startup_parity_check` | `(engine: Engine) -> None` | no | Run full schema parity check on startup. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | List, Optional, Tuple | no |
| `sqlalchemy` | inspect | no |
| `sqlalchemy.engine` | Engine | no |
| `sqlmodel` | SQLModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## signal_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/signal_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 112

**Docstring:** Signal Coordinator (C4 — Loop Model)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SignalCoordinator` | emit_and_update_risk | Context-free cross-domain signal dispatch coordinator. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_signal_coordinator` | `() -> SignalCoordinator` | no | Get the signal coordinator singleton. |
| `emit_and_persist_threshold_signal` | `(session: Any, tenant_id: str, run_id: str, state: str, signals: list, params_us` | no | L4 orchestration — binds session to callables, delegates to coordinator. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Callable, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## signal_feedback_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/signal_feedback_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 137

**Docstring:** Signal Feedback Coordinator (PIN-519)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SignalFeedbackCoordinator` | get_signal_feedback, _parse_datetime | L4 coordinator: Query signal feedback from audit ledger. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_signal_feedback_coordinator` | `() -> SignalFeedbackCoordinator` | no | Get the singleton SignalFeedbackCoordinator instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any | no |
| `app.hoc.cus.hoc_spine.schemas.run_introspection_protocols` | SignalFeedbackResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`SignalFeedbackCoordinator`, `get_signal_feedback_coordinator`

---

## skill.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/skill.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 457

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## snapshot_scheduler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/snapshot_scheduler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 95

**Docstring:** Snapshot Scheduler (PIN-513 Batch 4 Final Wiring)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SnapshotScheduler` | run_hourly, run_daily | L4 coordinator: scheduled snapshot batch execution. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, List | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## stages.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/stages.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 105

**Docstring:** Canonical stage surface for the knowledge plane lifecycle.

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.services.lifecycle_stages_base` | BaseStageHandler, StageContext, StageHandler, StageRegistry, StageResult (+1) | no |
| `app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.onboarding` | ActivateHandler, ClassifyHandler, GovernHandler, IndexHandler, IngestHandler (+2) | no |
| `app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.offboarding` | ArchiveHandler, DeactivateHandler, DeregisterHandler, PurgeHandler, VerifyDeactivateHandler | no |
| `app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution` | ClassificationExecutor, ClassificationResult, DataIngestionExecutor, IndexingExecutor, IndexingResult (+10) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### __all__ Exports
`BaseStageHandler`, `StageContext`, `StageHandler`, `StageRegistry`, `StageResult`, `StageStatus`, `RegisterHandler`, `VerifyHandler`, `IngestHandler`, `IndexHandler`, `ClassifyHandler`, `ActivateHandler`, `GovernHandler`, `DeregisterHandler`, `VerifyDeactivateHandler`, `DeactivateHandler`, `ArchiveHandler`, `PurgeHandler`, `DataIngestionExecutor`, `IngestionBatch`, `IngestionResult`, `IngestionSourceType`, `get_ingestion_executor`, `IndexingExecutor`, `IndexingResult`, `get_indexing_executor`, `ClassificationExecutor`, `ClassificationResult`, `SensitivityLevel`, `PIIType`, `PIIDetection`, `get_classification_executor`, `reset_executors`

---

## system_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/system_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 99

**Docstring:** System Runtime Health Handler

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SystemHealthHandler` | execute | Handler for system.health. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register` | `(registry: OperationRegistry) -> None` | no | Register system operations with the registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `os` | os | no |
| `typing` | Any | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationRegistry, OperationResult, get_async_session_context, get_operation_registry (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## test_operation_registry.py
**Path:** `backend/app/hoc/cus/hoc_spine/tests/test_operation_registry.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 305

**Docstring:** Operation Registry Tests

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StubHandler` | __init__, execute | Test handler that returns fixed data. |
| `FailingStubHandler` | execute | Test handler that raises an exception. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `registry` | `()` | no | Fresh registry for each test. |
| `mock_session` | `()` | no | Mock AsyncSession. |
| `ctx` | `(mock_session)` | no | Basic operation context. |
| `test_register_and_execute` | `(registry, ctx)` | yes | REG-001: Registered handler is found and executed. |
| `test_unknown_operation` | `(registry, ctx)` | yes | REG-002: Unknown operation returns error, not exception. |
| `test_duplicate_registration_raises` | `(registry)` | no | REG-003: Cannot register same operation name twice. |
| `test_frozen_registry_rejects` | `(registry)` | no | REG-004: Frozen registry refuses new registrations. |
| `test_freeze_sets_flag` | `(registry)` | no | REG-004: freeze() sets is_frozen flag. |
| `test_handler_exception_wrapped` | `(registry, ctx)` | yes | REG-005: Handler exceptions become OperationResult.fail(). |
| `test_operations_list` | `(registry)` | no | REG-006: operations returns sorted list. |
| `test_operation_count` | `(registry)` | no | REG-006: operation_count is accurate. |
| `test_has_operation` | `(registry)` | no | REG-006: has_operation checks correctly. |
| `test_get_handler` | `(registry)` | no | REG-006: get_handler returns handler or None. |
| `test_result_ok` | `()` | no | REG-007: OperationResult.ok() creates success result. |
| `test_result_fail` | `()` | no | REG-007: OperationResult.fail() creates failure result. |
| `test_status` | `(registry)` | no | REG-008: status() returns correct diagnostics. |
| `test_singleton` | `()` | no | Singleton returns same instance. |
| `test_reset_singleton` | `()` | no | Reset creates new instance. |
| `test_invalid_handler_rejected` | `(registry)` | no | Handler without execute() method is rejected. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `unittest.mock` | MagicMock | no |
| `pytest` | pytest | no |
| `importlib.util` | importlib.util | no |
| `sys` | sys | no |
| `pathlib` | Path | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## threshold_types.py
**Path:** `backend/app/hoc/cus/hoc_spine/schemas/threshold_types.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 40

**Docstring:** Threshold Types (Spine Schemas)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitSnapshot` |  | Immutable snapshot of a Limit record returned to engines. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## time.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/time.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 25

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `utc_now` | `() -> datetime` | no | Get current UTC time. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## traces_handler.py
**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/traces_handler.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 361

**Docstring:** Traces Handler (L4 Orchestrator)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ListAllMismatchesHandler` | execute | Handler for listing all mismatches. |
| `ListTraceMismatchesHandler` | execute | Handler for listing mismatches for a specific trace. |
| `ReportMismatchHandler` | execute | Handler for reporting a mismatch. |
| `ResolveMismatchHandler` | execute | Handler for resolving a mismatch. |
| `BulkReportMismatchesHandler` | execute | Handler for bulk reporting mismatches. |
| `VerifyTraceTenantHandler` | execute | Handler for verifying trace tenant ownership. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `register_traces_handlers` | `() -> None` | no | Register all trace mismatch handlers with the operation registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationHandler, OperationResult, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## transaction_coordinator.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/transaction_coordinator.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 823

**Docstring:** Transaction Coordinator for Cross-Domain Writes

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TransactionPhase` |  | Phases of transaction execution. |
| `TransactionFailed` | __init__ | Raised when cross-domain transaction fails. |
| `RollbackNotSupportedError` |  | Raised when rollback is attempted but the target model does not support it. |
| `DomainResult` | to_dict | Result from a single domain operation. |
| `TransactionResult` | is_complete, all_domains_succeeded, to_dict | Result of a successful cross-domain transaction. |
| `RollbackAction` |  | Describes a rollback action for a domain operation. |
| `RunCompletionTransaction` | __init__, execute, _create_incident, _create_policy_evaluation, _complete_trace, _publish_events, _execute_rollback, _emit_rollback_ack (+2 more) | Atomic cross-domain transaction for run completion. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_transaction_coordinator` | `() -> RunCompletionTransaction` | no | Get the singleton transaction coordinator instance. |
| `create_transaction_coordinator` | `(publisher = None) -> RunCompletionTransaction` | no | Create a new transaction coordinator instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, List, Optional | no |
| `uuid` | UUID | no |
| `sqlmodel` | Session | no |
| `app.db` | engine | no |
| `app.events` | get_publisher | no |
| `app.hoc.cus.hoc_spine.schemas.rac_models` | AckStatus, AuditAction, AuditDomain, DomainAck | no |
| `app.hoc.cus.hoc_spine.services.audit_store` | get_audit_store | no |
| `app.hoc.cus.hoc_spine.schemas.protocols` | TraceFacadePort | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

### Constants
`RAC_ROLLBACK_AUDIT_ENABLED`, `TRANSACTION_COORDINATOR_ENABLED`

---

## veil_policy.py
**Path:** `backend/app/hoc/cus/hoc_spine/authority/veil_policy.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 70

**Docstring:** Veil controls reduce attack-surface observability.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_mode` | `() -> str` | no |  |
| `is_prod` | `() -> bool` | no |  |
| `fastapi_schema_urls` | `() -> dict[str, object]` | no | Return FastAPI docs/openapi configuration. |
| `deny_as_404_enabled` | `() -> bool` | no | If enabled, deny responses avoid revealing existence of protected resources. |
| `unauthorized_http_status_code` | `(default: int = 403) -> int` | no |  |
| `unauthenticated_http_status_code` | `(default: int = 401) -> int` | no |  |
| `probe_rate_limit_enabled` | `() -> bool` | no |  |
| `probe_rate_per_minute` | `() -> int` | no |  |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `os` | os | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## webhook_verify.py
**Path:** `backend/app/hoc/cus/hoc_spine/services/webhook_verify.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 294

**Docstring:** Webhook Signature Verification Utility

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WebhookVerifier` | __init__, _parse_grace_env, _get_key, _compute_signature, verify, sign | Webhook signature verifier with key version support. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_file_key_loader` | `(keys_path: str) -> Callable[[str], Optional[str]]` | no | Create a key loader that reads from files. |
| `create_vault_key_loader` | `(mount_path: str = 'secret', secret_path: str = 'webhook/keys') -> Callable[[str` | no | Create a key loader that reads from Vault. |
| `verify_webhook` | `(body: bytes, signature: str, key_version: Optional[str], keys: Dict[str, str], ` | no | Quick verification without creating a WebhookVerifier instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Callable, Dict, List, Optional, Union | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---

## worker_write_driver_async.py
**Path:** `backend/app/hoc/cus/hoc_spine/drivers/worker_write_driver_async.py`  
**Layer:** L4_spine | **Domain:** hoc_spine | **Lines:** 222

**Docstring:** Worker Write Service (Async) - DB write operations for Worker API.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WorkerWriteServiceAsync` | __init__, upsert_worker_run, insert_cost_record, insert_cost_advisory, delete_worker_run, get_worker_run | Async DB write operations for Worker API. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, Optional | no |
| `sqlalchemy` | select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.db` | CostAnomaly, CostRecord | no |
| `app.models.tenant` | WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Single orchestrator — authority/execution/consequences, owns commit/begin, cross-domain owner

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L7_models
**Called by:** L2_api

---
