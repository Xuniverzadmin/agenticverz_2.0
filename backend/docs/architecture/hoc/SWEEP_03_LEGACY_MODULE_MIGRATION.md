# SWEEP-03: Legacy Module Migration

**Status:** IN PROGRESS
**Started:** 2026-01-25
**Invariant:** Any `app.services.*` import in HOC files must be migrated to HOC equivalent

## Critical Exclusion

**Models stay at `app/models/` and `app.services.*.models` - L6 drivers MAY import models.**

## Progress Log

### Starting Point
- Blocking imports: 66

### Migration Batch 1 (2026-01-25)

| Module | From | To | Imports Fixed |
|--------|------|-----|---------------|
| L4_runtime/facades/run_governance_facade | `app.services.policy_violation_service` | `app.hoc.cus.incidents.L5_engines.policy_violation_service` | 1 |
| L4_runtime/facades/run_governance_facade | `app.services.audit.store` | `app.hoc.cus.general.L5_engines.audit_store` | 1 |
| incidents/incident_engine | `app.services.policy.lessons_engine` | `app.hoc.cus.incidents.L5_engines.lessons_engine` | 1 |
| activity/run_governance_facade | `app.services.policy.lessons_engine` | `app.hoc.cus.incidents.L5_engines.lessons_engine` | 1 |
| general/L4_runtime/facades | `app.services.policy.lessons_engine` | `app.hoc.cus.incidents.L5_engines.lessons_engine` | 1 |
| policies/run_governance_facade | `app.services.policy.lessons_engine` | `app.hoc.cus.incidents.L5_engines.lessons_engine` | 1 |
| incidents/mapper | `app.services.soc2.control_registry` | `app.hoc.cus.general.L5_engines.control_registry` | 1 |
| policies/mapper | `app.services.soc2.control_registry` | `app.hoc.cus.general.L5_engines.control_registry` | 1 |
| general/L4_runtime/engines/__init__ | `app.services.governance.cross_domain` | `app.hoc.cus.general.L6_drivers.cross_domain` | 1 |
| duplicates/cost_anomaly_detector | `app.services.governance.cross_domain` | `app.hoc.cus.general.L6_drivers.cross_domain` | 1 |
| policies/certificate | `app.services.replay_determinism` | `app.hoc.cus.logs.L5_engines.replay_determinism` | 1 |
| analytics/detection_facade | `app.services.cost_anomaly_detector` | `app.hoc.cus.analytics.L5_engines.cost_anomaly_detector` | 2 |

**After Batch 1:** 55 blocking imports (-11)

### Migration Batch 2 (2026-01-25)

| Module | From | To | Imports Fixed |
|--------|------|-----|---------------|
| general/L6_drivers/cus_health_driver | `app.services.cus_credential_service` | `app.hoc.cus.general.L5_engines.cus_credential_service` | 1 |
| integrations/cus_health_engine | `app.services.cus_credential_service` | `app.hoc.cus.general.L5_engines.cus_credential_service` | 1 |
| integrations/datasources_facade | `app.services.datasources.datasource_model` | `app.hoc.cus.integrations.L5_schemas.datasource_model` | 1 |
| general/L5_lifecycle/onboarding | `app.services.lifecycle_stages.execution` | `app.hoc.cus.general.L5_lifecycle.drivers.execution` | 2 |
| int/general/retrieval_hook | `app.services.mediation.retrieval_mediator` | `app.hoc.cus.integrations.L5_engines.retrieval_mediator` | 1 |
| integrations/retrieval_facade | `app.services.mediation.retrieval_mediator` | `app.hoc.cus.integrations.L5_engines.retrieval_mediator` | 1 |
| integrations/connectors_facade | `app.services.connectors.connector_registry` | `app.hoc.cus.integrations.L6_drivers.connector_registry` | 1 |
| activity/activity_facade | `app.services.activity.*` | `app.hoc.cus.activity.L5_engines.*` | 5 |
| policies/policy_proposal_engine | `app.services.policy_graph_engine` | `app.hoc.cus.policies.L5_engines.policy_graph_engine` | 1 |
| general/transaction_coordinator | `app.services.observability.trace_facade` | `app.hoc.cus.logs.L5_engines.trace_facade` | 1 |
| activity/threshold_driver | `app.services.event_emitter` | `app.hoc.int.agent.drivers.event_emitter` | 1 |
| policies/llm_threshold_driver | `app.services.event_emitter` | `app.hoc.int.agent.drivers.event_emitter` | 1 |

**After Batch 2:** 40 blocking imports (-15)

### Migration Batch 3 (2026-01-25)

| Module | From | To | Imports Fixed |
|--------|------|-----|---------------|
| integrations/customer_incidents_adapter | `app.services.incident_read_service` | `app.hoc.cus.incidents.L5_engines.incident_read_engine` | 1 |
| integrations/customer_incidents_adapter | `app.services.incident_write_service` | `app.hoc.cus.incidents.L5_engines.incident_write_engine` | 1 |

**After Batch 3:** 38 blocking imports (-2)

### Migration Batch 4 (2026-01-25)

| Module | From | To | Imports Fixed |
|--------|------|-----|---------------|
| logs/certificate | `app.services.replay_determinism` | `app.hoc.cus.logs.L5_engines.replay_determinism` | 1 |
| logs/datasources_facade | `app.services.datasources.datasource_model` | `app.hoc.cus.integrations.L5_schemas.datasource_model` | 1 |
| logs/retrieval_facade | `app.services.mediation.retrieval_mediator` | `app.hoc.cus.integrations.L5_engines.retrieval_mediator` | 1 |
| logs/connectors_facade | `app.services.connectors.connector_registry` | `app.hoc.cus.integrations.L6_drivers.connector_registry` | 1 |
| logs/detection_facade | `app.services.cost_anomaly_detector` | `app.hoc.cus.analytics.L5_engines.cost_anomaly_detector` | 2 |

**After Batch 4:** 33 blocking imports (-5)

### Migration Batch 5 (2026-01-25)

| Module | From | To | Imports Fixed |
|--------|------|-----|---------------|
| policies/L5_engines/policy_limits_engine | `app.services.logs.audit_ledger_service_async` | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` | 1 |
| policies/L5_engines/policy_rules_engine | `app.services.logs.audit_ledger_service_async` | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` | 1 |
| policies/L5_engines/policy_proposal_engine | `app.services.logs.audit_ledger_service_async` | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` | 1 |
| policies/L5_engines/policy_limits_engine | `app.schemas.limits.policy_limits` | `app.hoc.cus.policies.L5_schemas.policy_limits` | 1 |
| policies/L5_engines/policy_rules_engine | `app.schemas.limits.policy_rules` | `app.hoc.cus.policies.L5_schemas.policy_rules` | 1 |
| policies/L6_drivers/override_driver | `app.schemas.limits.overrides` | `app.hoc.cus.policies.L5_schemas.overrides` | 1 |
| int/platform/engines/evaluator | `app.schemas.limits.simulation` | `app.hoc.cus.policies.L5_schemas.simulation` | 1 |
| api/cus/policies/simulate | `app.schemas.limits.simulation` | `app.hoc.cus.policies.L5_schemas.simulation` | 1 |

**Files Created:**
- `app/hoc/cus/logs/L6_drivers/audit_ledger_service_async.py` (new L6 driver)

**Header Fixes:**
- `policies/L5_schemas/policy_limits.py` (L6 → L5 Schema)
- `policies/L5_schemas/policy_rules.py` (L6 → L5 Schema)
- `policies/L5_schemas/overrides.py` (L6 → L5 Schema)
- `policies/L5_schemas/simulation.py` (L6 → L5 Schema)

**After Batch 5:** 30 blocking imports (-3 from Category 1)

### Migration Batch 6 (2026-01-25)

| Module | From | To | Imports Fixed |
|--------|------|-----|---------------|
| general/L4_runtime/drivers/transaction_coordinator | `app.services.audit` (RAC models) | `app.hoc.cus.general.L5_schemas.rac_models` | 1 |
| general/L5_engines/knowledge_sdk | `app.services.knowledge_lifecycle_manager` | `app.hoc.cus.general.L5_engines.knowledge_lifecycle_manager` | 1 |

**Files Created:**
- `app/hoc/cus/general/L5_schemas/rac_models.py` (RAC models migrated from app.services.audit.models)

**Notes:**
- Category 3 (RAC Audit Models): RESOLVED - `AckStatus`, `AuditAction`, `AuditDomain`, `DomainAck` now in HOC
- Category 4 (Knowledge Lifecycle): RESOLVED - Updated path, kept `KnowledgePlane` as alias to `KnowledgePlaneLifecycle`

**After Batch 6:** 28 blocking imports (-2)

### Migration Batch 7 (2026-01-25) — Category 5 Quick Wins

| Module | From | To | Imports Fixed |
|--------|------|-----|---------------|
| `integrations/L3_adapters/customer_killswitch_adapter` | `app.services.guard_write_service` | `app.hoc.cus.general.L5_controls.engines.guard_write_engine` | 1 |
| `integrations/L3_adapters/customer_killswitch_adapter` | `app.services.killswitch.*` | `app.hoc.cus.policies.L5_controls.engines.customer_killswitch_read_engine` | 1 |
| `integrations/L3_adapters/customer_policies_adapter` | `app.services.policy.*` | `app.hoc.cus.policies.L5_engines.customer_policy_read_engine` | 1 |
| `integrations/L3_adapters/customer_keys_adapter` | `app.services.keys_driver.*` | `app.hoc.cus.api_keys.L5_engines.keys_engine` | 1 |
| `integrations/L3_adapters/founder_ops_adapter` | `app.services.ops_domain_models` | `app.hoc.fdr.ops.schemas.ops_domain_models` | 1 |
| `integrations/L3_adapters/customer_logs_adapter` | `app.services.logs_read_service` | `app.hoc.cus.logs.L5_engines.logs_read_engine` | 1 |
| `integrations/L3_adapters/founder_contract_review_adapter` | `app.services.governance.contract_service` | `app.hoc.cus.policies.L5_engines.contract_engine` | 1 |

**After Batch 7:** 22 blocking imports (-6)

**Notes:**
- Category 5 quick wins completed (6 adapters)
- `customer_activity_adapter.py` NOT a quick win - interface mismatch requires deeper refactoring

### Current Status

| Domain | Blocking Imports | Status |
|--------|------------------|--------|
| general | 12 | BLOCKED |
| integrations | 2 | BLOCKED |
| logs | 0 | ✅ CLEAN |
| policies | 0 | ✅ CLEAN |
| incidents | 4 | BLOCKED |
| activity | 1 | BLOCKED |
| **Total** | **22** | |

**Note:** integrations has 2 remaining: `customer_activity_adapter` (interface mismatch), `integrations_facade` (needs CusIntegrationService)

## Deferred Modules - Detailed Breakdown

### Category 1: Non-Existent Module (3 imports) — ✅ RESOLVED (Batch 5)

**Module:** `app.services.logs.audit_ledger_service_async`
**Status:** RESOLVED - Created HOC L6 driver
**Action:** Created `app/hoc/cus/logs/L6_drivers/audit_ledger_service_async.py`

| File | Line | Import | Status |
|------|------|--------|--------|
| `policies/L5_engines/policy_limits_engine.py` | 75 | `AuditLedgerServiceAsync` | ✅ Fixed |
| `policies/L5_engines/policy_rules_engine.py` | 76 | `AuditLedgerServiceAsync` | ✅ Fixed |
| `policies/L5_engines/policy_proposal_engine.py` | 51 | `AuditLedgerServiceAsync` | ✅ Fixed |

---

### Category 2: Part-2 Governance Hub (10 imports)

**Location:** `general/L4_runtime/engines/__init__.py`
**Status:** Complex re-export hub - Part-2 CRM Workflow services
**Action:** Needs dedicated governance migration batch

| Line | Module | Exports |
|------|--------|---------|
| 34 | `governance.audit_service` | `AUDIT_SERVICE_VERSION`, `AuditCheck`, `AuditService`, etc. |
| 46 | `governance.contract_service` | `CONTRACT_SERVICE_VERSION`, `ContractService`, `ContractState`, etc. |
| 52 | `governance.eligibility_engine` | `EligibilityEngine`, `EligibilityDecision`, lookups |
| 66 | `governance.governance_orchestrator` | `GovernanceOrchestrator`, `JobStateMachine`, etc. |
| 79 | `governance.job_executor` | `JobExecutor`, `ExecutionContext`, handlers |
| 92 | `governance.rollout_projection` | `RolloutProjectionService`, `FounderRolloutView`, etc. |
| 109 | `governance.validator_service` | `ValidatorService`, `ValidatorVerdict`, enums |
| 128 | `governance.run_governance_facade` | `RunGovernanceFacade`, `get_run_governance_facade` |
| 134 | `governance.transaction_coordinator` | `TransactionResult`, `create_transaction_coordinator` |

**Additional governance imports:**
| File | Line | Import |
|------|------|--------|
| `L5_workflow/contracts/contract_engine.py` | 97 | `governance.eligibility_engine` |
| `L5_workflow/contracts/contract_engine.py` | 101 | `governance.validator_service` |
| `L4_runtime/engines/governance_orchestrator.py` | 81 | `governance.contract_service` |

---

### Category 3: RAC Audit Models (1 import) — ✅ RESOLVED (Batch 6)

**Module:** `app.services.audit`
**Status:** RESOLVED - RAC models migrated to HOC L5_schemas
**HOC Path:** `app.hoc.cus.general.L5_schemas.rac_models`

| File | Line | Import | Status |
|------|------|--------|--------|
| `L4_runtime/drivers/transaction_coordinator.py` | 93 | RAC models for rollback audit | ✅ Fixed |

---

### Category 4: Knowledge Lifecycle (1 import) — ✅ RESOLVED (Batch 6)

**Module:** `app.services.knowledge_lifecycle_manager`
**Status:** RESOLVED - Using HOC path with alias
**HOC Path:** `app.hoc.cus.general.L5_engines.knowledge_lifecycle_manager`
**Note:** `KnowledgePlaneLifecycle as KnowledgePlane` (alias preserves backwards compat)

| File | Line | Import | Status |
|------|------|--------|--------|
| `L5_engines/knowledge_sdk.py` | 62 | `KnowledgeLifecycleManager`, `KnowledgePlane`, etc. | ✅ Fixed |

---

### Category 5: L3 Adapter Read/Write Services (9 imports) — 8 RESOLVED (Batch 7+8)

**Status:** 8 fixed, 1 remaining

| File | Line | Module | Status |
|------|------|--------|--------|
| `customer_killswitch_adapter.py` | 45 | `guard_write_service` | ✅ Fixed |
| `customer_killswitch_adapter.py` | 46 | `killswitch.customer_killswitch_read_service` | ✅ Fixed |
| `customer_policies_adapter.py` | 44 | `policy.customer_policy_read_service` | ✅ Fixed |
| `customer_activity_adapter.py` | 44 | `activity.customer_activity_read_service` | ✅ Fixed (Batch 8) |
| `customer_keys_adapter.py` | 41 | `keys_driver` | ✅ Fixed |
| `customer_logs_adapter.py` | 132 | `logs_read_service` | ✅ Fixed |
| `founder_ops_adapter.py` | 37 | `ops_domain_models` | ✅ Fixed |
| `founder_contract_review_adapter.py` | 38 | `governance.contract_service` | ✅ Fixed |
| `integrations_facade.py` | 41 | `cus_integration_engine` | ⚠️ Not migrated |

**Batch 8 Notes (customer_activity_adapter):**
- Rewrote adapter to use HOC `ActivityFacade` with field translation
- Changed from sync to async (HOC facade is async)
- Added session parameter (HOC facade requires it)
- Field mapping: `RunSummaryResult` → `CustomerActivitySummary`, `RunDetailResult` → `CustomerActivityDetail`
- Note: The original service (`app.services.activity.customer_activity_read_service`) never existed - this was dead code

---

### Category 6: Incident Domain Services (4 imports)

| File | Line | Module | Status |
|------|------|--------|--------|
| `policy_violation_engine.py` | 276 | `incident_aggregator` | Not migrated |
| `incident_write_engine.py` | 58 | `logs.audit_ledger_service` | Sync version (different from async) |
| `recovery_evaluation_engine.py` | 54 | `recovery_matcher` | Not migrated |
| `recovery_evaluation_engine.py` | 55 | `recovery_rule_engine` | Not migrated |

---

### Category 7: Other Services (2 imports)

| File | Line | Module | Status |
|------|------|--------|--------|
| `transaction_coordinator.py` | 403 | `incidents.facade` | HOC has `get_incidents_facade` not `get_incident_facade` |
| `governance_facade.py` | 554 | `policy.facade` | Not migrated |
| `threshold_driver.py` | 360 | `activity.run_signal_service` | Not migrated |

---

### Category 8: Logs Domain Duplicates (5 imports) — ✅ RESOLVED (Batch 4)

**Note:** These exist in both `cus/logs/` and `cus/integrations/` - same modules, different locations

| File | Module | Status |
|------|--------|--------|
| `logs/certificate.py` | `replay_determinism` | ✅ Fixed in Batch 4 |
| `logs/detection_facade.py` | `cost_anomaly_detector` | ✅ Fixed in Batch 4 |
| `logs/datasources_facade.py` | `datasources.datasource_model` | ✅ Fixed in Batch 4 |
| `logs/retrieval_facade.py` | `mediation.retrieval_mediator` | ✅ Fixed in Batch 4 |
| `logs/connectors_facade.py` | `connectors.connector_registry` | ✅ Fixed in Batch 4 |

## Verification Command

```bash
python3 scripts/ops/sweep_03_module_blocker.py --count
python3 scripts/ops/sweep_03_module_blocker.py --domains
python3 scripts/ops/sweep_03_module_blocker.py --priority
```

## Files Modified

### Batch 1
- `app/hoc/cus/general/L4_runtime/facades/run_governance_facade.py`
- `app/hoc/cus/incidents/L5_engines/incident_engine.py`
- `app/hoc/cus/activity/L5_engines/run_governance_facade.py`
- `app/hoc/cus/policies/L5_engines/run_governance_facade.py`
- `app/hoc/cus/incidents/L5_engines/mapper.py`
- `app/hoc/cus/policies/L5_engines/mapper.py`
- `app/hoc/cus/general/L4_runtime/engines/__init__.py`
- `app/hoc/cus/duplicates/cost_anomaly_detector.py`
- `app/hoc/cus/policies/L5_engines/certificate.py`
- `app/hoc/cus/analytics/L5_engines/detection_facade.py`

### Batch 2
- `app/hoc/cus/general/L6_drivers/cus_health_driver.py`
- `app/hoc/cus/integrations/L5_engines/cus_health_engine.py`
- `app/hoc/cus/integrations/L5_engines/datasources_facade.py`
- `app/hoc/cus/general/L5_lifecycle/engines/onboarding.py`
- `app/hoc/int/general/engines/retrieval_hook.py`
- `app/hoc/cus/integrations/L5_engines/retrieval_facade.py`
- `app/hoc/cus/integrations/L5_engines/connectors_facade.py`
- `app/hoc/cus/activity/L5_engines/activity_facade.py`
- `app/hoc/cus/policies/L5_engines/policy_proposal_engine.py`
- `app/hoc/cus/general/L4_runtime/drivers/transaction_coordinator.py`
- `app/hoc/cus/activity/L6_drivers/threshold_driver.py`
- `app/hoc/cus/policies/L6_drivers/llm_threshold_driver.py`

### Batch 3
- `app/hoc/cus/integrations/L3_adapters/customer_incidents_adapter.py`

### Batch 4
- `app/hoc/cus/logs/L5_engines/certificate.py`
- `app/hoc/cus/logs/L5_engines/datasources_facade.py`
- `app/hoc/cus/logs/L5_engines/retrieval_facade.py`
- `app/hoc/cus/logs/L5_engines/connectors_facade.py`
- `app/hoc/cus/logs/L5_engines/detection_facade.py`

### Batch 5
- `app/hoc/cus/policies/L5_engines/policy_limits_engine.py`
- `app/hoc/cus/policies/L5_engines/policy_rules_engine.py`
- `app/hoc/cus/policies/L5_engines/policy_proposal_engine.py`
- `app/hoc/cus/policies/L6_drivers/override_driver.py`
- `app/hoc/int/platform/engines/evaluator.py`
- `app/hoc/api/cus/policies/simulate.py`
- `app/hoc/cus/policies/L5_schemas/policy_limits.py` (header fix)
- `app/hoc/cus/policies/L5_schemas/policy_rules.py` (header fix)
- `app/hoc/cus/policies/L5_schemas/overrides.py` (header fix)
- `app/hoc/cus/policies/L5_schemas/simulation.py` (header fix)

### Batch 6
- `app/hoc/cus/general/L4_runtime/drivers/transaction_coordinator.py`
- `app/hoc/cus/general/L5_engines/knowledge_sdk.py`

### Batch 7
- `app/hoc/cus/integrations/L3_adapters/customer_killswitch_adapter.py`
- `app/hoc/cus/integrations/L3_adapters/customer_policies_adapter.py`
- `app/hoc/cus/integrations/L3_adapters/customer_keys_adapter.py`
- `app/hoc/cus/integrations/L3_adapters/founder_ops_adapter.py`
- `app/hoc/cus/integrations/L3_adapters/customer_logs_adapter.py`
- `app/hoc/cus/integrations/L3_adapters/founder_contract_review_adapter.py`

### Batch 8
- `app/hoc/cus/integrations/L3_adapters/customer_activity_adapter.py` (full rewrite - async, field mapping)

## Files Created

- `scripts/ops/sweep_03_module_blocker.py` (tracking script)
- `app/hoc/cus/general/L5_engines/cus_credential_service.py` (migrated from app.services)
- `app/hoc/cus/logs/L6_drivers/audit_ledger_service_async.py` (new L6 driver)
- `app/hoc/cus/general/L5_schemas/rac_models.py` (RAC models migrated from app.services.audit.models)

## Knowledge Lifecycle Canonicalization (2026-02-08)

To prevent split-brain lifecycle imports, the canonical surfaces are now:

- Stage surface: `app.hoc.cus.hoc_spine.orchestrator.lifecycle.stages`
- Manager surface: `app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager`
- SDK surface: `app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_sdk`

Legacy `app.services.lifecycle_stages.*`, `app.services.knowledge_lifecycle_manager`, and `app.services.knowledge_sdk` remain only as compatibility shims (re-exports) and should not be used as canonical import sources for HOC.
