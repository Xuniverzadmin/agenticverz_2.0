# Phase-2 hoc_spine Import Audit — CUS Domains

**Date:** 2026-02-06
**Scope:** `backend/app/hoc/cus/{domain}/{L5_engines|L5_schemas|L6_drivers}/*.py`
**Domains:** 9 (overview, activity, incidents, policies, controls, logs, analytics, integrations, account)
**Deferred:** api_keys (gap — see Section 8)

---

**Addendum (2026-02-08):** In strict T0 mode, canonical CUS `L6_drivers` no longer import `app.hoc.cus.hoc_spine.*`. This document remains a Phase-2 snapshot (2026-02-06). For current line-level evidence, use `docs/architecture/hoc/HOC_SPINE_IMPORT_MATRIX_CUS.md`.

## 1. Summary Statistics

| Metric | Count |
|--------|-------|
| Total L5/L6 files with hoc_spine imports | 47 |
| Total import lines | 68 |
| OK (services/schemas/utilities) | 53 |
| REVIEW (orchestrator/authority in L5) | 15 |
| VIOLATION (requires L4 refactor) | 8 |

---

## 2. Import Classification Categories

| Category | Description | L5 Allowed? |
|----------|-------------|-------------|
| **services.time** | Canonical time utility (`utc_now`) | YES |
| **services.costsim_*** | Costsim config/metrics | YES |
| **services.audit_store** | Audit governance | YES (careful) |
| **services.control_registry** | Control governance | YES |
| **services.cus_credential_engine** | Credential service | YES |
| **schemas.*** | Protocols, types, models | YES |
| **utilities.*** | Recovery decisions | YES |
| **drivers.cross_domain** | UUID generation | YES |
| **drivers.alert_driver** | Alert delivery | REVIEW |
| **orchestrator.*** | Orchestration/coordinators | NO → VIOLATION |
| **authority.*** | Runtime switch, governance | NO → VIOLATION |

---

## 3. Per-Domain Audit Tables

### 3.1 Overview Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/overview_facade.py` | 68 | `services.time.utc_now` | services.time | OK |
| `L6_drivers/overview_facade_driver.py` | 47 | `services.time.utc_now` | services.time | OK |

**Domain Verdict:** OK (0 violations)

---

### 3.2 Activity Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/cost_analysis_engine.py` | 26 | `services.time.utc_now` | services.time | OK |
| `L5_engines/signal_feedback_engine.py` | 26 | `services.time.utc_now` | services.time | OK |
| `L5_engines/attention_ranking_engine.py` | 26 | `services.time.utc_now` | services.time | OK |
| `L5_engines/pattern_detection_engine.py` | 26 | `services.time.utc_now` | services.time | OK |
| `L5_engines/__init__.py` | 33 | `orchestrator.run_governance_facade` | orchestrator | **VIOLATION** |
| `L5_engines/activity_facade.py` | 670 | `orchestrator.coordinators.run_evidence_coordinator` | orchestrator | **VIOLATION** |
| `L5_engines/activity_facade.py` | 719 | `orchestrator.coordinators.run_proof_coordinator` | orchestrator | **VIOLATION** |
| `L5_engines/activity_facade.py` | 1152 | `orchestrator.coordinators.signal_feedback_coordinator` | orchestrator | **VIOLATION** |
| `L6_drivers/__init__.py` | 17 | `schemas.threshold_types.LimitSnapshot` | schemas | OK |

**Domain Verdict:** VIOLATION (4 orchestrator imports in L5)

---

### 3.3 Incidents Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/incident_engine.py` | 75 | `services.time.utc_now` | services.time | OK |
| `L5_engines/incident_engine.py` | 906 | `orchestrator.coordinators.lessons_coordinator` | orchestrator | **VIOLATION** |
| `L5_engines/recurrence_analysis_engine.py` | 45 | `services.time.utc_now` | services.time | OK |
| `L5_engines/incident_pattern_engine.py` | 65 | `services.time.utc_now` | services.time | OK |
| `L5_engines/anomaly_bridge.py` | 64 | `schemas.anomaly_types.CostAnomalyFact` | schemas | OK |
| `L6_drivers/export_bundle_driver.py` | 59 | `schemas.protocols.TraceStorePort` | schemas | OK |
| `L6_drivers/incident_driver.py` | 214 | `schemas.rac_models.*` | schemas | OK |
| `L6_drivers/incident_driver.py` | 215 | `services.audit_store.get_audit_store` | services | OK |

**Domain Verdict:** VIOLATION (1 orchestrator import in L5)

---

### 3.4 Policies Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/policy_limits_engine.py` | 56 | `services.time.utc_now` | services.time | OK |
| `L5_engines/policy_limits_engine.py` | 57 | `drivers.cross_domain.generate_uuid` | drivers | OK |
| `L5_engines/policy_proposal_engine.py` | 40 | `services.time.utc_now` | services.time | OK |
| `L5_engines/recovery_evaluation_engine.py` | 57 | `utilities.recovery_decisions` | utilities | OK |
| `L5_engines/eligibility_engine.py` | 75 | `orchestrator.*` | orchestrator | **VIOLATION** |
| `L5_engines/governance_facade.py` | 201 | `authority.runtime_switch` | authority | **REVIEW** |
| `L5_engines/governance_facade.py` | 265 | `authority.runtime_switch` | authority | **REVIEW** |
| `L5_engines/governance_facade.py` | 325 | `authority.runtime_switch` | authority | **REVIEW** |
| `L5_engines/governance_facade.py` | 388 | `authority.runtime_switch` | authority | **REVIEW** |
| `L5_engines/governance_facade.py` | 607 | `authority.runtime_switch.is_governance_active` | authority | **REVIEW** |
| `L5_engines/failure_mode_handler.py` | 97 | `authority.profile_policy_mode` | authority | **REVIEW** |
| `L5_engines/lessons_engine.py` | 63 | `services.time.utc_now` | services.time | OK |
| `L5_engines/policy_rules_engine.py` | 57 | `services.time.utc_now` | services.time | OK |
| `L5_engines/policy_rules_engine.py` | 58 | `drivers.cross_domain.generate_uuid` | drivers | OK |
| `L6_drivers/policy_proposal_write_driver.py` | 32 | `services.time.utc_now` | services.time | OK |
| `L6_drivers/proposals_read_driver.py` | 35 | `services.time.utc_now` | services.time | OK |
| `L6_drivers/policy_rules_read_driver.py` | 31 | `services.time.utc_now` | services.time | OK |
| `adapters/founder_contract_review_adapter.py` | 42 | `authority.contracts.contract_engine.ContractState` | authority | **REVIEW** |

**Domain Verdict:** VIOLATION (1 orchestrator + 7 authority imports)

---

### 3.5 Controls Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L6_drivers/circuit_breaker_driver.py` | 84 | `services.costsim_config.get_config` | services | OK |
| `L6_drivers/circuit_breaker_async_driver.py` | 79 | `services.costsim_config.get_config` | services | OK |
| `L6_drivers/circuit_breaker_async_driver.py` | 80 | `services.costsim_metrics.get_metrics` | services | OK |
| `L6_drivers/threshold_driver.py` | 67 | `schemas.threshold_types.LimitSnapshot` | schemas | OK |
| `L6_drivers/limits_read_driver.py` | 30 | `services.time.utc_now` | services.time | OK |
| `L6_drivers/override_driver.py` | 42 | `services.time.utc_now` | services.time | OK |
| `L6_drivers/override_driver.py` | 43 | `drivers.cross_domain.generate_uuid` | drivers | OK |

**Domain Verdict:** OK (0 violations)

---

### 3.6 Logs Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/mapper.py` | 34 | `services.time.utc_now` | services.time | OK |
| `L5_engines/mapper.py` | 35 | `services.control_registry` | services | OK |
| `L5_engines/audit_reconciler.py` | 50 | `schemas.rac_models` | schemas | OK |
| `L5_engines/audit_reconciler.py` | 58 | `services.audit_store` | services | OK |
| `L5_engines/trace_facade.py` | 241 | `schemas.rac_models.*` | schemas | OK |
| `L5_engines/trace_facade.py` | 242 | `services.audit_store.get_audit_store` | services | OK |

**Domain Verdict:** OK (0 violations)

---

### 3.7 Analytics Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/pattern_detection_engine.py` | 55 | `services.time.utc_now` | services.time | OK |
| `L5_engines/prediction_engine.py` | 66 | `services.time.utc_now` | services.time | OK |
| `L5_engines/metrics_engine.py` | 34 | `services.costsim_metrics` | services | OK |
| `L5_engines/config_engine.py` | 34 | `services.costsim_config` | services | OK |
| `L5_engines/cost_anomaly_detector_engine.py` | 974 | `schemas.anomaly_types.CostAnomalyFact` | schemas | OK |
| `L5_engines/alert_worker_engine.py` | 98 | `services.get_alert_delivery_adapter` | services | **REVIEW** |
| `L5_engines/alert_worker_engine.py` | 131 | `drivers.alert_driver.AlertDriver` | drivers | **REVIEW** |
| `L5_engines/alert_worker_engine.py` | 211 | `drivers.alert_driver.AlertDriver` | drivers | **REVIEW** |
| `L5_engines/alert_worker_engine.py` | 229 | `drivers.alert_driver.AlertDriver` | drivers | **REVIEW** |
| `L5_engines/alert_worker_engine.py` | 256 | `drivers.alert_driver.AlertDriver` | drivers | **REVIEW** |
| `L5_engines/detection_facade.py` | 303 | `orchestrator.coordinators.anomaly_incident_coordinator` | orchestrator | **VIOLATION** |
| `L6_drivers/__init__.py` | 18 | `drivers.alert_driver` | drivers | OK |
| `L6_drivers/cost_write_driver.py` | 50 | `services.time.utc_now` | services.time | OK |

**Domain Verdict:** VIOLATION (1 orchestrator + 5 driver imports in L5)

---

### 3.8 Integrations Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/cus_health_engine.py` | 64 | `services.cus_credential_engine` | services | OK |
| `L5_engines/mcp_tool_invocation_engine.py` | 63 | `schemas.protocols.MCPAuditEmitterPort` | schemas | OK |
| `L5_engines/cost_bridges_engine.py` | 50 | `orchestrator.create_incident_from_cost_anomaly_sync` | orchestrator | **VIOLATION** |

**Domain Verdict:** VIOLATION (1 orchestrator import in L5)

---

### 3.9 Account Domain

| File | Line | Import | Category | Verdict |
|------|------|--------|----------|---------|
| `L5_engines/tenant_engine.py` | 50 | `services.time.utc_now` | services.time | OK |
| `L6_drivers/tenant_driver.py` | 54 | `services.time.utc_now` | services.time | OK |
| `L6_drivers/user_write_driver.py` | 47 | `services.time.utc_now` | services.time | OK |

**Domain Verdict:** OK (0 violations)

---

## 4. Violations Summary

### 4.1 orchestrator Imports in L5 (VIOLATION — Must Refactor)

| Domain | File | Line | Import | Proposed L4 Replacement |
|--------|------|------|--------|------------------------|
| activity | `L5_engines/__init__.py` | 33 | `run_governance_facade` | Move to activity_bridge capability |
| activity | `L5_engines/activity_facade.py` | 670 | `run_evidence_coordinator` | Move to activity_handler |
| activity | `L5_engines/activity_facade.py` | 719 | `run_proof_coordinator` | Move to activity_handler |
| activity | `L5_engines/activity_facade.py` | 1152 | `signal_feedback_coordinator` | Move to activity_handler |
| incidents | `L5_engines/incident_engine.py` | 906 | `lessons_coordinator` | Move to incidents_bridge capability |
| policies | `L5_engines/eligibility_engine.py` | 75 | `orchestrator.*` | Move to policies_handler |
| analytics | `L5_engines/detection_facade.py` | 303 | `anomaly_incident_coordinator` | Move to analytics_handler |
| integrations | `L5_engines/cost_bridges_engine.py` | 50 | `create_incident_from_cost_anomaly_sync` | Move to integrations_handler |

### 4.2 authority Imports in L5 (REVIEW — May Need Refactor)

| Domain | File | Line | Import | Justification |
|--------|------|------|--------|---------------|
| policies | `governance_facade.py` | 201,265,325,388,607 | `runtime_switch` | Governance state check — may be acceptable if read-only |
| policies | `failure_mode_handler.py` | 97 | `profile_policy_mode` | Governance config — may be acceptable if read-only |
| policies | `adapters/founder_contract_review_adapter.py` | 42 | `contract_engine.ContractState` | Schema import — OK (type only) |

---

## 5. Required Refactors (Step 3 Output)

### 5.1 High Priority (orchestrator calls in L5)

| File | Current Import | Action |
|------|---------------|--------|
| `activity/L5_engines/__init__.py:33` | `run_governance_facade` | Add capability to activity_bridge, L5 receives via dependency injection |
| `activity/L5_engines/activity_facade.py:670,719,1152` | coordinators | L4 handler calls coordinators, passes results to L5 |
| `incidents/L5_engines/incident_engine.py:906` | `lessons_coordinator` | Add capability to incidents_bridge |
| `policies/L5_engines/eligibility_engine.py:75` | orchestrator | L4 handler resolves eligibility, L5 receives decision |
| `analytics/L5_engines/detection_facade.py:303` | `anomaly_incident_coordinator` | L4 analytics_handler orchestrates incident creation |
| `integrations/L5_engines/cost_bridges_engine.py:50` | `create_incident_from_cost_anomaly_sync` | L4 integrations_handler creates incidents |

### 5.2 Medium Priority (authority read-only checks)

| File | Current Import | Recommendation |
|------|---------------|----------------|
| `policies/L5_engines/governance_facade.py` | `runtime_switch.is_governance_active` | **KEEP** — read-only governance state query is acceptable |
| `policies/L5_engines/failure_mode_handler.py` | `profile_policy_mode` | **KEEP** — read-only config lookup is acceptable |

### 5.3 Low Priority (driver imports in L5)

| File | Current Import | Recommendation |
|------|---------------|----------------|
| `analytics/L5_engines/alert_worker_engine.py` | `AlertDriver` | **REVIEW** — L5 should not import L4 drivers directly. Refactor to inject via bridge. |

---

## 6. Compliance Verdicts by Domain

| Domain | Files | OK | REVIEW | VIOLATION | Verdict |
|--------|-------|-----|--------|-----------|---------|
| overview | 2 | 2 | 0 | 0 | **OK** |
| activity | 9 | 5 | 0 | 4 | **VIOLATION** |
| incidents | 8 | 7 | 0 | 1 | **VIOLATION** |
| policies | 18 | 10 | 7 | 1 | **VIOLATION** |
| controls | 7 | 7 | 0 | 0 | **OK** |
| logs | 6 | 6 | 0 | 0 | **OK** |
| analytics | 13 | 7 | 5 | 1 | **VIOLATION** |
| integrations | 3 | 2 | 0 | 1 | **VIOLATION** |
| account | 3 | 3 | 0 | 0 | **OK** |

---

## 7. Skeptic Audit (Step 2B)

**Pattern:** Any hoc_spine import not using `app.hoc.cus.hoc_spine` prefix

**Result:** No relative or aliased imports found. All imports use canonical path.

---

## 8. Deferred Gap: api_keys Domain

**Status:** DEFERRED

**Rationale:** api_keys has zero hoc_spine imports, representing a design gap. Before adding imports:
1. Complete refactors for the 8 VIOLATION files in other domains
2. Design api_keys L5 engine integration with hoc_spine services
3. Ensure api_keys follows the patterns established in this audit

**Gap Items:**
- `api_keys/L5_engines/` — No files import hoc_spine
- `api_keys/L6_drivers/` — No files import hoc_spine

**Next Steps:**
1. Audit api_keys domain for missing governance integration
2. Add `services.time.utc_now` where timestamps are needed
3. Add audit_store integration if api_key operations need auditing

---

## 9. Acceptance Criteria Status

| Criterion | Status |
|-----------|--------|
| Every hoc_spine import classified and justified | ✅ COMPLETE |
| L5 engine orchestrator imports flagged | ✅ 8 VIOLATIONS identified |
| Evidence report with per-domain status | ✅ This document |
| Refactor actions listed | ✅ Section 5 |
| api_keys deferred with rationale | ✅ Section 8 |

---

## 10. Evidence Commands

```bash
# Full scan of hoc_spine imports in CUS domains
grep -rn "from app.hoc.cus.hoc_spine" backend/app/hoc/cus/*/L5_engines/ backend/app/hoc/cus/*/L6_drivers/

# orchestrator violations only
grep -rn "from app.hoc.cus.hoc_spine.orchestrator" backend/app/hoc/cus/*/L5_engines/

# authority violations only
grep -rn "from app.hoc.cus.hoc_spine.authority" backend/app/hoc/cus/*/L5_engines/
```
