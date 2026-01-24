# Directory Reorganization Plan

**Status:** IN PROGRESS
**Date:** 2026-01-22
**Reference:** FACADE_CONSOLIDATION_PLAN.md, ui_plan.yaml, domain_intent_spec.yaml

---

## Executive Summary

This document defines the directory reorganization following **first-principles** design with an **isolated namespace** for safe migration.

```
app/hoc/{audience}/{domain}/{role}/{file}.py
```

Where:
- **hoc** = Isolated namespace (new structure)
- **audience** = `customer`, `internal`, `founder`
- **domain** = business area (policies, incidents, analytics, etc.)
- **role** = `facades`, `drivers`, `engines`, `schemas`

**Core Principles:**
- Path tells you what it does
- Topics encoded in filenames
- **COPY, don't move** - originals remain as fallback
- Isolated namespace prevents conflicts

---

## 1. Migration Strategy: Copy-First

### 1.1 Why Copy Instead of Move

| Benefit | Description |
|---------|-------------|
| **Zero risk** | Original files untouched, system keeps working |
| **Gradual migration** | Switch imports one at a time, test each |
| **Easy rollback** | Just delete hoc/ if something breaks |
| **Parallel testing** | Verify new structure before committing |

### 1.2 Namespace Isolation

```
app/
├── services/           ← ORIGINAL (unchanged, fallback)
│   ├── overview_facade.py
│   ├── incidents_facade.py
│   └── ...
│
└── hoc/       ← NEW (isolated copy)
    ├── customer/
    ├── internal/
    └── founder/
```

### 1.3 Migration Flow

```
STEP 2-11: COPY
├── Copy file to hoc/{audience}/{domain}/{role}/
├── Update header comments (new path)
├── Keep original unchanged
└── Test new imports work

STEP 14: CLEANUP (after validation)
├── Verify all callers use new paths
├── Run full test suite
└── Delete original files from services/
```

---

## 2. First-Principles Design

### 2.1 Why This Structure

| Principle | How It's Satisfied |
|-----------|-------------------|
| **Path tells role** | `policies/engines/lessons_engine.py` → domain logic |
| **Consistent pattern** | Every domain has same folder structure |
| **Flat** | Max 5 levels: `app/hoc/cus/policies/L5_engines/` |
| **Topic in filename** | `lessons_engine.py`, `killswitch_facade.py` |
| **Find all of type** | Want all facades? Look in `*/facades/` |
| **Isolated** | `hoc/` namespace prevents conflicts |

### 2.2 Role Definitions

| Role | Purpose | What Lives Here |
|------|---------|-----------------|
| `facades/` | Entry points - what L2 APIs call | Domain facades, topic facades |
| `drivers/` | Orchestrators - coordinate multiple engines | Drivers, coordinators |
| `engines/` | Pure domain logic - business rules | Engines, processors |
| `schemas/` | Data contracts | DTOs, types, result classes |

### 2.3 Audience Definitions

| Audience | Who Can Access | Examples |
|----------|----------------|----------|
| `customer/` | Customer console users | All UI-facing domains |
| `internal/` | System infrastructure | Recovery, agent planning |
| `founder/` | Admin/ops only | Ops tools, diagnostics |

---

## 3. Target Directory Structure

```
app/hoc/
├── __init__.py
│
├── customer/
│   ├── __init__.py
│   │
│   ├── overview/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── overview_facade.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── overview_types.py
│   │
│   ├── activity/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── activity_facade.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── activity_types.py
│   │
│   ├── incidents/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── incidents_facade.py
│   │   ├── drivers/
│   │   │   ├── __init__.py
│   │   │   └── incident_driver.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   └── incident_engine.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── incident_types.py
│   │
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   ├── policies_facade.py
│   │   │   ├── killswitch_facade.py
│   │   │   └── run_governance_facade.py
│   │   ├── drivers/
│   │   │   ├── __init__.py
│   │   │   └── policy_driver.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── graph_engine.py
│   │   │   ├── lessons_engine.py
│   │   │   ├── llm_engine.py
│   │   │   └── budget_engine.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── policy_types.py
│   │
│   ├── logs/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── logs_facade.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── logs_types.py
│   │
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── analytics_facade.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   └── cost_model_engine.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── analytics_types.py
│   │
│   ├── account/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── accounts_facade.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── account_types.py
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── integrations_facade.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── integration_types.py
│   │
│   ├── api_keys/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── api_keys_facade.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── api_key_types.py
│   │
│   └── general/
│       ├── __init__.py
│       ├── facades/
│       │   ├── __init__.py
│       │   └── general_facade.py
│       ├── drivers/
│       │   ├── __init__.py
│       │   └── runtime_spine.py
│       └── schemas/
│           ├── __init__.py
│           └── general_types.py
│
├── internal/
│   ├── __init__.py
│   │
│   ├── recovery/
│   │   ├── __init__.py
│   │   ├── facades/
│   │   │   ├── __init__.py
│   │   │   └── recovery_facade.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── claim_decision_engine.py
│   │   │   ├── recovery_evaluation_engine.py
│   │   │   └── recovery_rule_engine.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── recovery_types.py
│   │
│   └── agent/
│       ├── __init__.py
│       ├── facades/
│       │   ├── __init__.py
│       │   └── agent_facade.py
│       ├── engines/
│       │   ├── __init__.py
│       │   └── plan_generation_engine.py
│       └── schemas/
│           ├── __init__.py
│           └── agent_types.py
│
└── founder/
    ├── __init__.py
    │
    └── ops/
        ├── __init__.py
        ├── facades/
        │   ├── __init__.py
        │   └── ops_facade.py
        └── schemas/
            ├── __init__.py
            └── ops_types.py
```

---

## 4. Customer Domains (10)

| Domain | Intent | Topics (in filenames) | Roles Used |
|--------|--------|----------------------|------------|
| **overview** | System health at a glance | cost, decisions, highlights | facades, schemas |
| **activity** | Execution monitoring | completed, live, signals | facades, schemas |
| **incidents** | Exception management | active, historical, resolved | facades, drivers, engines, schemas |
| **policies** | Behavior control | active, lessons, library, controls, violations | facades, drivers, engines, schemas |
| **logs** | Evidence and audit | audit, llm_runs, system | facades, schemas |
| **analytics** | Usage and cost intelligence | usage, cost, trends | facades, engines, schemas |
| **account** | Identity and billing | projects, users, profile, billing, support | facades, schemas |
| **integrations** | LLM provider management | providers, health, limits | facades, schemas |
| **api_keys** | Programmatic access | keys, permissions, usage | facades, schemas |
| **general** | Runtime orchestration | runtime, orchestration | facades, drivers, schemas |

---

## 5. Internal Domains (2)

| Domain | Intent | Topics (in filenames) | Roles Used |
|--------|--------|----------------------|------------|
| **recovery** | Failure handling | claims, evaluation, rules | facades, engines, schemas |
| **agent** | Agent planning | planning | facades, engines, schemas |

---

## 6. Founder Domains (1)

| Domain | Intent | Topics (in filenames) | Roles Used |
|--------|--------|----------------------|------------|
| **ops** | Admin diagnostics | admin, diagnostics | facades, schemas |

---

## 7. File Copy Mapping

### 7.1 Customer Facades

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/overview_facade.py` | `hoc/cus/overview/facades/overview_facade.py` |
| `services/activity_facade.py` | `hoc/cus/activity/facades/activity_facade.py` |
| `services/incidents_facade.py` | `hoc/cus/incidents/facades/incidents_facade.py` |
| `services/policies_facade.py` | `hoc/cus/policies/facades/policies_facade.py` |
| `services/logs_facade.py` | `hoc/cus/logs/facades/logs_facade.py` |
| `services/analytics_facade.py` | `hoc/cus/analytics/facades/analytics_facade.py` |
| `services/accounts_facade.py` | `hoc/cus/account/facades/accounts_facade.py` |
| `services/integrations_facade.py` | `hoc/cus/integrations/facades/integrations_facade.py` |
| `services/api_keys_facade.py` | `hoc/cus/api_keys/facades/api_keys_facade.py` |
| `services/governance/facade.py` | `hoc/cus/policies/facades/killswitch_facade.py` |
| `services/governance/run_governance_facade.py` | `hoc/cus/policies/facades/run_governance_facade.py` |

### 7.2 Customer Drivers

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/incidents/incident_driver.py` | `hoc/cus/incidents/L6_drivers/incident_driver.py` |
| `services/policy/policy_driver.py` | `hoc/cus/policies/L6_drivers/policy_driver.py` |
| `services/governance/transaction_coordinator.py` | `hoc/cus/general/L6_drivers/runtime_spine.py` |

### 7.3 Customer Engines

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/incidents/incident_engine.py` | `hoc/cus/incidents/L5_engines/incident_engine.py` |
| `services/policy/lessons_engine.py` | `hoc/cus/policies/L5_engines/lessons_engine.py` |
| `services/policy_graph_engine.py` | `hoc/cus/policies/L5_engines/graph_engine.py` |
| `services/llm_policy_engine.py` | `hoc/cus/policies/L5_engines/llm_engine.py` |
| `services/budget_enforcement_engine.py` | `hoc/cus/policies/L5_engines/budget_engine.py` |
| `services/cost_model_engine.py` | `hoc/cus/analytics/L5_engines/cost_model_engine.py` |

### 7.4 Internal Engines

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/claim_decision_engine.py` | `hoc/int/recovery/engines/claim_decision_engine.py` |
| `services/recovery_evaluation_engine.py` | `hoc/int/recovery/engines/recovery_evaluation_engine.py` |
| `services/recovery_rule_engine.py` | `hoc/int/recovery/engines/recovery_rule_engine.py` |
| `services/plan_generation_engine.py` | `hoc/int/agent/engines/plan_generation_engine.py` |

### 7.5 Founder Facades

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/ops/facade.py` | `hoc/fdr/ops/facades/ops_facade.py` |

### 7.6 Create New (Missing)

| Domain | Role | Target Location |
|--------|------|-----------------|
| general | facade | `hoc/cus/general/facades/general_facade.py` |
| recovery | facade | `hoc/int/recovery/facades/recovery_facade.py` |
| agent | facade | `hoc/int/agent/facades/agent_facade.py` |

### 7.7 Deferred (HOLD)

| File | Reason |
|------|--------|
| `services/governance/eligibility_engine.py` | Usage unclear — HOLD |

### 7.8 Unclear Facades (Classify in Step 12)

| Current Location | Likely Domain | Action |
|------------------|---------------|--------|
| `services/controls/facade.py` | policies? | ⏸️ STEP 12 |
| `services/limits/facade.py` | policies? | ⏸️ STEP 12 |
| `services/lifecycle/facade.py` | activity? | ⏸️ STEP 12 |
| `services/connectors/facade.py` | integrations? | ⏸️ STEP 12 |
| `services/monitors/facade.py` | ? | ⏸️ STEP 12 |
| `services/datasources/facade.py` | ? | ⏸️ STEP 12 |
| `services/scheduler/facade.py` | internal? | ⏸️ STEP 12 |
| `services/alerts/facade.py` | incidents? | ⏸️ STEP 12 |
| `services/notifications/facade.py` | ? | ⏸️ STEP 12 |
| `services/evidence/facade.py` | logs? | ⏸️ STEP 12 |
| `services/compliance/facade.py` | policies? | ⏸️ STEP 12 |
| `services/detection/facade.py` | incidents? | ⏸️ STEP 12 |
| `services/retrieval/facade.py` | ? | ⏸️ STEP 12 |
| `services/observability/trace_facade.py` | logs? | ⏸️ STEP 12 |

---

## 8. Stepwise Implementation Plan

### STEP 1: Create Directory Skeleton ✅ COMPLETE

**Goal:** Create hoc directory structure with `__init__.py` files.

**Result:**
- Created `app/hoc/` namespace
- Created 13 domain directories (10 customer + 2 internal + 1 founder)
- Created 52 role directories (facades, drivers, engines, schemas)
- Created 69 `__init__.py` files
- Verified imports work: `from app.hoc import customer`

---

### STEP 2: Copy Primary Customer Facades (5)

**Goal:** Copy the 5 primary UI-aligned domain facades.

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/overview_facade.py` | `hoc/cus/overview/facades/overview_facade.py` |
| `services/activity_facade.py` | `hoc/cus/activity/facades/activity_facade.py` |
| `services/incidents_facade.py` | `hoc/cus/incidents/facades/incidents_facade.py` |
| `services/policies_facade.py` | `hoc/cus/policies/facades/policies_facade.py` |
| `services/logs_facade.py` | `hoc/cus/logs/facades/logs_facade.py` |

**Actions per file:**
1. Copy file to target location
2. Update header comment with new path
3. Keep original unchanged
4. Update `__init__.py` exports in new location
5. Test new import works

**Validation:** `from app.hoc.cus.overview.facades import overview_facade`

---

### STEP 3: Copy Secondary Customer Facades (4)

**Goal:** Copy the 4 additional customer domain facades.

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/analytics_facade.py` | `hoc/cus/analytics/facades/analytics_facade.py` |
| `services/accounts_facade.py` | `hoc/cus/account/facades/accounts_facade.py` |
| `services/integrations_facade.py` | `hoc/cus/integrations/facades/integrations_facade.py` |
| `services/api_keys_facade.py` | `hoc/cus/api_keys/facades/api_keys_facade.py` |

**Actions:** Same as Step 2.

**Validation:** New imports work.

---

### STEP 4: Copy Governance Facades to Policies

**Goal:** Copy governance facades to policies domain.

| Source (KEEP) | Target (COPY TO) | Rename |
|---------------|------------------|--------|
| `services/governance/facade.py` | `hoc/cus/policies/facades/killswitch_facade.py` | Yes |
| `services/governance/run_governance_facade.py` | `hoc/cus/policies/facades/run_governance_facade.py` | No |

**Actions:**
1. Copy and rename files
2. Rename class `GovernanceFacade` → `KillswitchFacade`
3. Update header comments
4. Update `__init__.py` exports

**Validation:** New imports work.

---

### STEP 5: Copy Incidents Domain (Driver + Engine)

**Goal:** Copy incidents driver and engine.

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/incidents/incident_driver.py` | `hoc/cus/incidents/L6_drivers/incident_driver.py` |
| `services/incidents/incident_engine.py` | `hoc/cus/incidents/L5_engines/incident_engine.py` |

**Actions:**
1. Copy files
2. Update header comments
3. Update `__init__.py` exports

**Validation:** New imports work.

---

### STEP 6: Copy Policies Domain (Driver + Engines)

**Goal:** Copy all policies domain files.

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/policy/policy_driver.py` | `hoc/cus/policies/L6_drivers/policy_driver.py` |
| `services/policy/lessons_engine.py` | `hoc/cus/policies/L5_engines/lessons_engine.py` |
| `services/policy_graph_engine.py` | `hoc/cus/policies/L5_engines/graph_engine.py` |
| `services/llm_policy_engine.py` | `hoc/cus/policies/L5_engines/llm_engine.py` |
| `services/budget_enforcement_engine.py` | `hoc/cus/policies/L5_engines/budget_engine.py` |

**Actions:**
1. Copy files (rename where indicated)
2. Update header comments
3. Update `__init__.py` exports

**Validation:** New imports work.

---

### STEP 7: Copy Analytics Engine

**Goal:** Copy cost_model_engine to analytics domain.

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/cost_model_engine.py` | `hoc/cus/analytics/L5_engines/cost_model_engine.py` |

**Actions:**
1. Copy file
2. Update header comments
3. Update `__init__.py` exports

**Validation:** New imports work.

---

### STEP 8: Copy General Domain (Runtime Spine)

**Goal:** Copy transaction coordinator to general domain.

| Source (KEEP) | Target (COPY TO) | Rename |
|---------------|------------------|--------|
| `services/governance/transaction_coordinator.py` | `hoc/cus/general/L6_drivers/runtime_spine.py` | Yes |

**Actions:**
1. Copy and rename file
2. Rename class `TransactionCoordinator` → `RuntimeSpine`
3. Update header comments
4. Update `__init__.py` exports

**Validation:** New imports work.

---

### STEP 9: Copy Internal Engines

**Goal:** Copy recovery and agent engines.

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/claim_decision_engine.py` | `hoc/int/recovery/engines/claim_decision_engine.py` |
| `services/recovery_evaluation_engine.py` | `hoc/int/recovery/engines/recovery_evaluation_engine.py` |
| `services/recovery_rule_engine.py` | `hoc/int/recovery/engines/recovery_rule_engine.py` |
| `services/plan_generation_engine.py` | `hoc/int/agent/engines/plan_generation_engine.py` |

**Actions:**
1. Copy files
2. Update header comments
3. Update `__init__.py` exports

**Validation:** New imports work.

---

### STEP 10: Copy Founder Facade

**Goal:** Copy ops facade to founder domain.

| Source (KEEP) | Target (COPY TO) |
|---------------|------------------|
| `services/ops/facade.py` | `hoc/fdr/ops/facades/ops_facade.py` |

**Actions:**
1. Copy file
2. Update header comments
3. Update `__init__.py` exports

**Validation:** New imports work.

---

### STEP 11: Create Missing Facades

**Goal:** Create facades for domains without one.

| Domain | Target |
|--------|--------|
| general | `hoc/cus/general/facades/general_facade.py` |
| recovery | `hoc/int/recovery/facades/recovery_facade.py` |
| agent | `hoc/int/agent/facades/agent_facade.py` |

**Validation:** New facades can be imported.

---

### STEP 12: Classify Unclear Facades

**Goal:** Audit and classify remaining subdomain facades.

**Facades to audit:** (14 files - see Section 7.8)

**Actions per facade:**
1. Grep for callers
2. Determine audience (customer/int/founder)
3. Determine domain
4. Copy to `hoc/{audience}/{domain}/facades/`
5. Update header and exports

**Validation:** Each facade classified and copied.

---

### STEP 13: Extract Schemas

**Goal:** Extract DTOs and result types to schemas folders.

**Actions per domain:**
1. Identify dataclasses/DTOs in facade files
2. Extract to `{domain}/schemas/{domain}_types.py`
3. Update imports in facades

**Validation:** All DTOs in schemas folders.

---

### STEP 14: Switch Callers to New Imports

**Goal:** Update L2 APIs and other callers to use hoc paths.

**Actions:**
1. Update L2 API imports one by one
2. Test each change
3. Run full test suite

**Validation:** All callers use new paths, tests pass.

---

### STEP 15: Cleanup Originals

**Goal:** Remove original files after validation period.

**Actions:**
1. Verify all imports use hoc paths
2. Run full test suite
3. Delete original files from services/
4. Remove empty directories

**Validation:** Tests pass, no old imports remain.

---

### STEP 16: Update BLCA Rules

**Goal:** Add layer rules for new structure.

**Actions:**
1. Update `scripts/ops/layer_validator.py` with hoc paths
2. Add audience-based import rules:
   - `customer/*` may not import from `founder/*`
   - `internal/*` may not import from `founder/*`
   - `facades/` may import from `drivers/`, `engines/`, `schemas/`
   - `drivers/` may import from `engines/`, `schemas/`
   - `engines/` may import from `schemas/`
3. Run BLCA, fix any violations

**Validation:** BLCA passes with 0 violations.

---

## 9. Import Rules

### 9.1 Audience Rules

| From | May Import |
|------|------------|
| `hoc/cus/*` | `customer/*`, `internal/*` (not `founder/*`) |
| `hoc/int/*` | `internal/*` (not `customer/*`, `founder/*`) |
| `hoc/fdr/*` | `founder/*`, `customer/*`, `internal/*` |

### 9.2 Role Rules (within domain)

| From | May Import |
|------|------------|
| `facades/` | `drivers/`, `engines/`, `schemas/` |
| `drivers/` | `engines/`, `schemas/` |
| `engines/` | `schemas/` |
| `schemas/` | (nothing domain-internal) |

---

## 10. Validation Checklist (Per Step)

- [ ] File copied to correct location
- [ ] Header comment updated with new path
- [ ] Original file unchanged
- [ ] `__init__.py` exports updated
- [ ] New import works in Python REPL
- [ ] No circular import errors

---

## 11. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Import breakage | Originals unchanged - fallback available |
| Circular imports | Copy in dependency order (engines → drivers → facades) |
| Test failures | Run tests after each step |
| BLCA violations | Update rules in Step 16 |
| Rollback needed | Delete hoc/ folder, originals intact |

---

## 12. Summary Statistics

| Metric | Count |
|--------|-------|
| Customer domains | 10 |
| Internal domains | 2 |
| Founder domains | 1 |
| Total facades to copy | 15 |
| Total drivers to copy | 3 |
| Total engines to copy | 10 |
| Facades to create | 3 |
| Unclear facades to classify | 14 |
| Total implementation steps | 16 |

---

## 13. Change Log

| Date | Step | Changes |
|------|------|---------|
| 2026-01-22 | 0 | Initial plan created |
| 2026-01-22 | 0 | Updated to first-principles structure (audience/domain/role) |
| 2026-01-22 | 0 | Changed to COPY approach with `hoc/` namespace |
| 2026-01-22 | 1 | ✅ COMPLETE: Created hoc directory skeleton (69 __init__.py files) |

