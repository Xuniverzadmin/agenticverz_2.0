# Facade Consolidation Plan

**Status:** STAGE 0-2 COMPLETE (Customer Domains) | STOP FOR REVIEW
**Date:** 2026-01-22
**Reference:** Facade Architecture Analysis

---

## Executive Summary

This document defines the 6-stage plan to consolidate the facade architecture, eliminating dual facades and establishing clear semantic boundaries between CUSTOMER-facing facades and INTERNAL drivers.

**Core Principle:**
> A facade is either CUSTOMER or INTERNAL — never both.
> Facade == API projection only. Internal callers use drivers.

---

## Stage 0: Freeze + Document Headers ✅ COMPLETE

**Completed:** 2026-01-22

### Current State Snapshot

#### Dual Facades Identified (MUST CONSOLIDATE)

| Domain | CUSTOMER Facade | INTERNAL Facade | Action |
|--------|-----------------|-----------------|--------|
| **Incidents** | `services/incidents_facade.py` (1103 LOC) | `services/incidents/facade.py` (253 LOC) | Rename internal → driver |
| **Policies** | `services/policies_facade.py` (1496 LOC) | `services/policy/facade.py` (388 LOC) | Rename internal → driver |

#### Engines Identified (RENAME TO DRIVERS)

| Current Name | New Name | Domain |
|--------------|----------|--------|
| `incident_engine.py` | `incident_driver.py` | Incidents |
| `budget_enforcement_engine.py` | `budget_enforcement_driver.py` | Enforcement |
| `claim_decision_engine.py` | `claim_decision_driver.py` | Claims |
| `cost_model_engine.py` | `cost_model_driver.py` | Cost |
| `lessons_learned_engine.py` | `lessons_learned_driver.py` | Lessons |
| `llm_policy_engine.py` | `llm_policy_driver.py` | Policy |
| `plan_generation_engine.py` | `plan_generation_driver.py` | Planning |
| `policy_graph_engine.py` | `policy_graph_driver.py` | Policy |
| `recovery_evaluation_engine.py` | `recovery_evaluation_driver.py` | Recovery |
| `recovery_rule_engine.py` | `recovery_rule_driver.py` | Recovery |
| `governance/eligibility_engine.py` | `governance/eligibility_driver.py` | Governance |
| `ai_console_panel_adapter/ai_console_panel_engine.py` | `ai_console_panel_adapter/panel_driver.py` | UI Adapter |
| `ai_console_panel_adapter/panel_verification_engine.py` | `ai_console_panel_adapter/panel_verification_driver.py` | UI Adapter |
| `ai_console_panel_adapter/validator_engine.py` | `ai_console_panel_adapter/validator_driver.py` | UI Adapter |

#### Coordinators Identified (RENAME TO DRIVERS)

| Current Name | New Name | Domain |
|--------------|----------|--------|
| `governance/transaction_coordinator.py` | `governance/transaction_driver.py` | Governance |

---

## Stage 1: Facade Consolidation (DUAL → FACADE + DRIVER) ✅ COMPLETE

**Completed:** 2026-01-22

### Changes Made

1. **Incidents Domain:**
   - Created `services/incidents/incident_driver.py` (253 LOC)
   - Updated `services/incidents/__init__.py` to export IncidentDriver
   - Added backward compatibility aliases (IncidentFacade → IncidentDriver)
   - CUSTOMER facade: `services/incidents_facade.py` (unchanged)

2. **Policies Domain:**
   - Created `services/policy/policy_driver.py` (389 LOC)
   - Updated `services/policy/__init__.py` to export PolicyDriver
   - Added backward compatibility aliases (PolicyFacade → PolicyDriver)
   - CUSTOMER facade: `services/policies_facade.py` (unchanged)

### Incidents Domain

**Before:**
```
services/incidents_facade.py          → CUSTOMER (L2 API)
services/incidents/facade.py          → INTERNAL (worker, governance)
```

**After:**
```
services/incidents_facade.py          → CUSTOMER (L2 API) [KEEP]
services/incidents/incident_driver.py → INTERNAL (worker, governance) [RENAME]
```

**Changes Required:**
1. Rename `services/incidents/facade.py` → `services/incidents/incident_driver.py`
2. Rename class `IncidentFacade` → `IncidentDriver`
3. Rename accessor `get_incident_facade()` → `get_incident_driver()`
4. Update callers:
   - `worker/runner.py` (lines 48, 363, 479)
   - `governance/transaction_coordinator.py` (lines 393, 395)
   - `services/incidents/__init__.py`

### Policies Domain

**Before:**
```
services/policies_facade.py           → CUSTOMER (L2 API)
services/policy/facade.py             → INTERNAL (policy_layer, governance)
```

**After:**
```
services/policies_facade.py           → CUSTOMER (L2 API) [KEEP]
services/policy/policy_driver.py      → INTERNAL (policy_layer, governance) [RENAME]
```

**Changes Required:**
1. Rename `services/policy/facade.py` → `services/policy/policy_driver.py`
2. Rename class `PolicyFacade` → `PolicyDriver`
3. Rename accessor `get_policy_facade()` → `get_policy_driver()`
4. Update callers:
   - `api/policy_layer.py` (38 references)
   - `governance/facade.py` (lines 552, 553)
   - `services/policy/__init__.py`

---

## Stage 2: Engine Relocation (Customer Domains) ✅ COMPLETE

**Completed:** 2026-01-22

### Semantic Rule

> Engines stay as engines (domain logic). Drivers orchestrate.
> Engines move to their corresponding domain subdirectory.

### Decision: Relocate, Not Rename

**Issue:** After Stage 1, we have:
- `incidents/incident_driver.py` (INTERNAL orchestrator - created in Stage 1)
- `incident_engine.py` (domain logic - at services root)

If we rename `incident_engine.py` → `incident_driver.py`, there's a collision.

**Resolution:** Keep engine name, move to corresponding directory:
```
services/incident_engine.py → services/incidents/incident_engine.py
services/lessons_learned_engine.py → services/policy/lessons_engine.py
```

### Customer Domain Engine Relocation ✅ COMPLETE

| Original Location | New Location | Status |
|------------------|--------------|--------|
| `services/incident_engine.py` | `services/incidents/incident_engine.py` | ✅ Moved |
| `services/lessons_learned_engine.py` | `services/policy/lessons_engine.py` | ✅ Moved |

### Resulting Hierarchy

```
INCIDENTS DOMAIN:
incidents_facade.py (CUSTOMER - L2 API projection)
  └── incidents/incident_driver.py (INTERNAL orchestrator)
        └── incidents/incident_engine.py (domain logic)

POLICIES DOMAIN:
policies_facade.py (CUSTOMER - L2 API projection)
  └── policy/policy_driver.py (INTERNAL orchestrator)
        └── policy/lessons_engine.py (lessons domain logic)
```

### Import Updates Applied

| File | Occurrences Updated |
|------|---------------------|
| `app/main.py` | 1 |
| `app/services/governance/run_governance_facade.py` | 1 |
| `app/services/policies_facade.py` | 4 |
| `app/api/policy.py` | 2 |
| `app/api/policy_layer.py` | 6 |
| `app/services/incidents/incident_driver.py` | 1 |
| `app/services/policy/__init__.py` | Added exports |

### W4/Governance Engine Renaming ⏸️ DEFERRED

The following engines are W4/Governance domain and explicitly deferred per governance review:

| File | Status |
|------|--------|
| `budget_enforcement_engine.py` | ⏸️ DEFERRED |
| `claim_decision_engine.py` | ⏸️ DEFERRED |
| `cost_model_engine.py` | ⏸️ DEFERRED |
| `llm_policy_engine.py` | ⏸️ DEFERRED |
| `plan_generation_engine.py` | ⏸️ DEFERRED |
| `policy_graph_engine.py` | ⏸️ DEFERRED |
| `recovery_evaluation_engine.py` | ⏸️ DEFERRED |
| `recovery_rule_engine.py` | ⏸️ DEFERRED |
| `governance/eligibility_engine.py` | ⏸️ DEFERRED |
| `governance/transaction_coordinator.py` | ⏸️ DEFERRED |

**Note:** W4/Governance consolidation will be reviewed separately after customer domain work is validated.

---

## Stage 3: Worker Isolation (ASYNC ONLY)

### Rule
> If it runs in a queue/scheduler → worker
> If it touches retries/progress → worker

### Current Workers (services/)
- `worker_registry_service.py` - OK (registry)
- `worker_write_service_async.py` - OK (async write)

### Worker Pattern
```
{domain}_worker.py → {domain}_driver.py → {domain}_kernel.py (optional)
```

---

## Stage 4: Kernel Extraction (OPTIONAL)

### Criteria for Kernel Creation
1. Logic reused in ≥2 places
2. Deterministic
3. No I/O
4. No DB session ownership

### Candidates
- `incident_kernel.py` - Incident classification logic
- `policy_kernel.py` - Policy evaluation logic

---

## Stage 5: API Surface Alignment

### Target State
```
L2 API                    FACADE
api/incidents.py      →   incidents_facade.py
api/policies.py       →   policies_facade.py
api/overview.py       →   overview_facade.py
api/activity.py       →   activity_facade.py
api/logs.py           →   logs_facade.py
api/analytics.py      →   analytics_facade.py
api/aos_accounts.py   →   accounts_facade.py
api/aos_cus_integrations.py → integrations_facade.py
api/aos_api_key.py    →   api_keys_facade.py
```

---

## Stage 6: Enforcement Rules

### Import Rules (Lightweight CI)

| Layer | May Import |
|-------|------------|
| Facades | drivers, read models |
| Workers | drivers |
| Drivers | kernels, repositories |
| Kernels | nothing domain-external |

---

## Final Architecture

```
CUSTOMER PATH:
L2 API
  ↓
FACADE (projection only)
  ↓
DRIVER (orchestration)
  ↓
KERNEL (rules) ← optional
  ↓
DB / Logs / Events

ASYNC PATH:
Worker
  ↓
Driver
  ↓
Kernel (optional)
  ↓
DB / Logs / Events
```

---

## Implementation Order

| Stage | Action | Status |
|-------|--------|--------|
| 0 | Freeze + document headers | ✅ COMPLETE |
| 1 | Dual facade consolidation | ✅ COMPLETE |
| 2 | Engine relocation (customer domains) | ✅ COMPLETE |
| 2b | W4/Governance engine renaming | ⏸️ DEFERRED |
| STOP | Re-evaluate before continuing | ⬅️ CURRENT |
| 3 | Worker isolation | PENDING |
| 4 | Kernel extraction | PENDING |
| 5 | API surface alignment | PENDING |
| 6 | Enforcement rules | PENDING |

---

## Change Log

| Date | Stage | Changes |
|------|-------|---------|
| 2026-01-22 | 0 | Initial plan created |
| 2026-01-22 | 1 | Dual facades consolidated: incidents/facade.py → incident_driver.py, policy/facade.py → policy_driver.py |
| 2026-01-22 | 2 | Customer domain engines relocated: incident_engine.py → incidents/, lessons_learned_engine.py → policy/lessons_engine.py |
| 2026-01-22 | 2b | W4/Governance engines deferred for separate review |
