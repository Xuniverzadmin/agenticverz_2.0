# HOC Policies Domain Analysis v1

**Domain:** `app/houseofcards/customer/policies/`
**Audience:** CUSTOMER
**Date:** 2026-01-22
**Status:** CLEANUP COMPLETE
**Last Updated:** 2026-01-22

---

## 1. Final Structure (Post-Cleanup)

```
app/houseofcards/customer/policies/
├── __init__.py
├── controls/
│   ├── KillSwitch/
│   │   └── engines/
│   │       └── __init__.py               (EMPTY - facade.py DELETED as duplicate)
│   └── engines/
│       ├── customer_killswitch_read_service.py  # Customer killswitch reads
│       ├── degraded_mode_checker.py             # Degraded mode detection
│       └── runtime_switch.py                    # Runtime governance toggle
├── drivers/
│   └── __init__.py                       (EMPTY - policy_driver.py MOVED OUT)
├── engines/
│   ├── __init__.py
│   ├── authority_checker.py              # Authority validation
│   ├── budget_enforcement_engine.py      # Budget halt decisions (PIN-257)
│   ├── claim_decision_engine.py          # Recovery claim eligibility (PIN-257)
│   ├── control_registry.py               # Control registration
│   ├── customer_policy_read_service.py   # Customer policy reads
│   ├── eligibility_engine.py             # Eligibility determination (PIN-287)
│   ├── hallucination_detector.py         # Hallucination detection
│   ├── lessons_engine.py                 # Lessons learned (SDSR, PIN-411)
│   ├── llm_policy_engine.py              # LLM safety limits (PIN-254)
│   ├── llm_threshold_service.py          # LLM thresholds
│   ├── mapper.py                         # Generic mapper
│   ├── override_service.py               # Policy overrides
│   ├── policy_graph_engine.py            # Conflict/dependency graphs (PIN-411)
│   ├── policy_limits_service.py          # Policy limits
│   ├── policy_mapper.py                  # Policy-specific mapper
│   ├── policy_proposal.py                # Policy proposals (PB-S4)
│   ├── policy_rules_service.py           # Policy rules CRUD
│   ├── policy_violation_service.py       # S3 violation truth (PIN-242)
│   ├── simulation_service.py             # Policy simulation
│   ├── snapshot_service.py               # Policy snapshots
│   └── validator_service.py              # Policy validation
├── facades/
│   ├── __init__.py
│   ├── controls_facade.py                # Controls domain facade
│   ├── governance_facade.py              # Governance facade (CANONICAL)
│   ├── limits_facade.py                  # Limits facade
│   ├── policies_facade.py                # Main policies facade (1496 LOC)
│   └── run_governance_facade.py          # Run governance facade
└── schemas/
    └── __init__.py                       (EMPTY - reserved for DTOs)
```

**File Count:** 34 files (excluding moved/deleted)

---

## 2. Completed Actions (2026-01-22)

### 2.1 Files Moved Out of Domain

| File | From | To | Reason |
|------|------|-----|--------|
| `policy_driver.py` | `customer/policies/drivers/` | `internal/platform/policy/engines/` | AUDIENCE: INTERNAL in customer/ path |

### 2.2 Files Deleted

| File | Location | Reason |
|------|----------|--------|
| `facade.py` | `controls/KillSwitch/engines/` | 100% duplicate of `governance_facade.py` (MD5 identical) |

### 2.3 Decision Rationale

**policy_driver.py:**
- Header declared: `# AUDIENCE: INTERNAL`
- Header stated: *"CUSTOMER-facing CRUD operations use policies_facade.py"*
- Callers: policy_layer API, governance services, **worker runtime**
- Same pattern as `incident_driver.py` which was moved in incidents cleanup

**KillSwitch facade.py:**
- MD5 hash: `848340e237da4dc36169b49be2e599d6`
- Identical to `governance_facade.py` hash
- Maintaining duplicates creates drift risk

---

## 3. Files Kept (No Action - Rationale)

### 3.1 Large Facades (Acceptable)

| File | Lines | Reason to Keep |
|------|-------|----------------|
| `policies_facade.py` | 1496 | Orchestrates, doesn't decide. Split only for operational clarity. |

### 3.2 System-Wide Files (Correctly Placed)

| File | Reason |
|------|--------|
| `lessons_engine.py` | Policy domain owns lesson creation |
| `llm_policy_engine.py` | Policy domain owns LLM safety |
| `policy_violation_service.py` | Policy domain owns S3 violation truth |
| `budget_enforcement_engine.py` | Policy domain owns budget enforcement |
| `policy_graph_engine.py` | Policy domain owns conflict detection |

**Key Principle:** "system-wide" describes reuse, not ownership. Relocate only when responsibility is wrong.

### 3.3 Learning + Proposals (Defer Extraction)

| File | Future Consideration |
|------|---------------------|
| `lessons_engine.py` | Extract when learning becomes separate product |
| `policy_proposal.py` | Extract when proposals become separate product |

**Rationale:** Premature separation creates cross-domain chatter. Keep together until feedback loops are formalized.

### 3.4 Controls Subdomain (Transitional)

| File | Reason |
|------|--------|
| `runtime_switch.py` | KillSwitch semantics not finalized |
| `customer_killswitch_read_service.py` | Correctly placed |
| `degraded_mode_checker.py` | Correctly placed |

---

## 4. Domain Boundaries (Documented)

### 4.1 Question-Based Ownership

| Domain | Question Answered |
|--------|-------------------|
| **Policies** | "What should be enforced?" |
| **Controls** | "What can be turned on/off at runtime?" |
| **Governance** | "Who can override or suspend enforcement?" |

### 4.2 Facade Responsibility Matrix

| Facade | Primary Domain | Secondary | Callers |
|--------|----------------|-----------|---------|
| `policies_facade.py` | Policies | - | L2 policies API |
| `governance_facade.py` | Governance | Controls | L2 governance API, SDK |
| `controls_facade.py` | Controls | - | L2 controls API, SDK |
| `limits_facade.py` | Policies | - | L2 limits API, SDK |
| `run_governance_facade.py` | Governance | Policies | L5 runner |

---

## 5. Engine Inventory

### 5.1 System Truth Engines (L4)

| Engine | Role | Reference |
|--------|------|-----------|
| `lessons_engine.py` | Lesson creation from events (SDSR) | PIN-411 |
| `llm_policy_engine.py` | LLM safety & cost limits | PIN-254 |
| `policy_violation_service.py` | S3 violation truth model | PIN-242, PIN-195 |
| `budget_enforcement_engine.py` | Budget halt decisions | PIN-257 |
| `claim_decision_engine.py` | Recovery claim eligibility | PIN-257 |
| `eligibility_engine.py` | Deterministic eligibility rules | PIN-287 |
| `policy_graph_engine.py` | Conflict & dependency analysis | PIN-411 |

### 5.2 Service Engines (L4)

| Engine | Role |
|--------|------|
| `policy_rules_service.py` | Policy rules CRUD |
| `policy_limits_service.py` | Policy limits management |
| `customer_policy_read_service.py` | Customer policy reads |
| `policy_proposal.py` | Policy proposals (PB-S4) |
| `override_service.py` | Policy overrides |
| `simulation_service.py` | Policy simulation |
| `snapshot_service.py` | Policy snapshots |
| `validator_service.py` | Policy validation |

### 5.3 Controls Engines

| Engine | Role | Reference |
|--------|------|-----------|
| `runtime_switch.py` | Governance kill switch | GAP-069, GAP-070 |
| `customer_killswitch_read_service.py` | Customer killswitch reads | PIN-280 |
| `degraded_mode_checker.py` | Degraded mode detection | - |

---

## 6. Facade Inventory

### 6.1 `policies_facade.py` (Main Entry Point)

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine |
| **AUDIENCE** | CUSTOMER |
| **Product** | ai-console |
| **Lines** | 1496 |
| **Callers** | L2 policies API (policies.py) |

**Exports (Result Types):**
- `PolicyRuleSummaryResult`, `PolicyRulesListResult`, `PolicyRuleDetailResult`
- `LimitSummaryResult`, `LimitsListResult`, `LimitDetailResult`
- `PolicyStateResult`, `PolicyMetricsResult`
- `PolicyConflictResult`, `ConflictsListResult`
- `PolicyNodeResult`, `PolicyDependencyEdge`, `DependencyGraphResult`
- `PolicyViolationResult`, `ViolationsListResult`
- `BudgetDefinitionResult`, `BudgetsListResult`
- `PolicyRequestResult`, `PolicyRequestsListResult`
- `LessonSummaryResult`, `LessonsListResult`, `LessonDetailResult`, `LessonStatsResult`
- `PoliciesFacade`, `get_policies_facade()`

**Key Methods:**

| Method | Order | Description |
|--------|-------|-------------|
| `list_policy_rules()` | O2 | List policy rules with filters |
| `get_policy_rule_detail()` | O3 | Get rule detail by ID |
| `list_limits()` | O2 | List rate limits/quotas |
| `get_limit_detail()` | O3 | Get limit detail by ID |
| `list_lessons()` | O2 | List lessons learned |
| `get_lesson_detail()` | O3 | Get lesson detail by ID |
| `get_lesson_stats()` | O1 | Get lesson statistics |
| `get_policy_state()` | O1 | Synthesized policy layer state |
| `get_policy_metrics()` | O1 | Enforcement effectiveness metrics |
| `list_policy_violations()` | O2 | List policy violations |
| `list_policy_conflicts()` | O4 | Detect policy conflicts |
| `get_policy_dependencies()` | O5 | Get dependency graph |
| `list_policy_requests()` | O3 | Pending approval requests |
| `list_budgets()` | O2 | Budget definitions |

---

### 6.2 `governance_facade.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine |
| **Product** | system-wide |
| **Lines** | 616 |
| **Reference** | GAP-090 to GAP-095 |

**Exports:**
- `GovernanceMode` (NORMAL, DEGRADED, KILL)
- `GovernanceStateResult`, `KillSwitchResult`, `ConflictResolutionResult`, `BootStatusResult`
- `GovernanceFacade`, `get_governance_facade()`

**Key Methods:**

| Method | GAP | Description |
|--------|-----|-------------|
| `enable_kill_switch()` | GAP-090 | Disable all governance (emergency) |
| `disable_kill_switch()` | GAP-090 | Re-enable governance |
| `set_mode()` | GAP-091 | Set NORMAL/DEGRADED/KILL mode |
| `get_governance_state()` | - | Get current state |
| `resolve_conflict()` | GAP-092 | Manually resolve policy conflict |
| `get_boot_status()` | GAP-095 | SPINE component health |

---

### 6.3 `limits_facade.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine |
| **AUDIENCE** | CUSTOMER |
| **Lines** | 454 |
| **Reference** | GAP-122 |

**Exports:**
- `LimitType`, `LimitPeriod`
- `LimitConfig`, `LimitCheckResult`, `UsageSummary`
- `LimitsFacade`, `get_limits_facade()`

---

### 6.4 `controls_facade.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine |
| **AUDIENCE** | CUSTOMER |
| **Lines** | 433 |
| **Reference** | GAP-123 |

**Exports:**
- `ControlType`, `ControlState`
- `ControlConfig`, `ControlStatusSummary`
- `ControlsFacade`, `get_controls_facade()`

---

### 6.5 `run_governance_facade.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine |
| **Product** | system-wide |
| **Lines** | 328 |
| **Reference** | PIN-454 |

**Exports:**
- `RunGovernanceFacade`, `get_run_governance_facade()`

---

## 7. Key Engine Details

### 7.1 `lessons_engine.py` (SDSR)

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Contract** | SDSR (PIN-370), PB-S4 |
| **Reference** | PIN-411 |

**Exports:**
```python
# Constants
LESSON_TYPE_FAILURE, LESSON_TYPE_NEAR_THRESHOLD, LESSON_TYPE_CRITICAL_SUCCESS
LESSON_STATUS_PENDING, LESSON_STATUS_CONVERTED, LESSON_STATUS_DEFERRED, LESSON_STATUS_DISMISSED

# State Machine
VALID_TRANSITIONS

# Metrics
LESSONS_CREATION_FAILED  # Prometheus Counter

# Engine
LessonsLearnedEngine, get_lessons_learned_engine()
```

**State Machine:**
```
pending → converted_to_draft (TERMINAL)
pending → deferred → pending (via reactivation)
pending → dismissed (TERMINAL)
```

---

### 7.2 `llm_policy_engine.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Reference** | PIN-254 |

**Exports:**
```python
# Limits (env-configurable)
LLM_MAX_TOKENS_PER_REQUEST   # 16000
LLM_MAX_COST_CENTS_PER_REQUEST  # 50
LLM_REQUESTS_PER_MINUTE      # 60

# Model Policy
LLM_COST_MODEL, SYSTEM_ALLOWED_MODELS, EXPENSIVE_MODELS, TASK_MODEL_POLICY

# Classes
SafetyCheckResult, LLMRateLimiter

# Functions
check_safety_limits(), is_model_allowed(), get_model_for_task()
estimate_tokens(), estimate_cost_cents()
```

---

### 7.3 `policy_violation_service.py` (S3 Truth)

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Reference** | PIN-242, PIN-195, PIN-407 |

**Exports:**
```python
VERIFICATION_MODE
ViolationFact, ViolationIncident
PolicyViolationService
handle_policy_violation(), create_policy_evaluation_record()
```

**Critical Invariants:**
- No incident without persisted violation fact
- Policy must be enabled for tenant
- Evidence must exist before incident creation
- One incident per (run_id, policy_id)

---

### 7.4 `policy_graph_engine.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engines |
| **Reference** | PIN-411, DFT-O4, DFT-O5 |

**Exports:**
```python
# Enums
ConflictType     # SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE
ConflictSeverity # BLOCKING, WARNING
DependencyType   # EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT

# Classes
PolicyConflict, PolicyDependency, DependencyGraphResult
PolicyConflictEngine, PolicyDependencyEngine
get_conflict_engine(), get_dependency_engine()
```

---

## 8. Import Inventory

### 8.1 External Imports (Phase 5 Updates)

| File | Old Import | New Import |
|------|------------|------------|
| All engines | `app.services.policy.*` | `app.houseofcards.customer.policies.engines.*` |
| `run_governance_facade.py` | `app.services.policy.lessons_engine` | `app.houseofcards.customer.policies.engines.lessons_engine` |

### 8.2 L6 Imports (Correct)

| File | Import |
|------|--------|
| Most facades/engines | `sqlalchemy`, `sqlmodel` |
| `lessons_engine.py` | `prometheus_client` |
| `policy_violation_service.py` | `app.utils.runtime` |

---

## 9. Domain Summary

| Metric | Value |
|--------|-------|
| **Purpose** | Policies, rules, limits, lessons, violations, controls, governance |
| **Total Files** | 34 |
| **Facades** | 5 |
| **Engines** | 21 |
| **Drivers** | 0 (moved out) |
| **Controls subdomain** | 3 |
| **Schemas** | 0 (reserved) |
| **External Dependencies** | sqlalchemy, sqlmodel, prometheus_client |
| **Callers** | L2 APIs, L5 runner |

---

## 10. Deferred Actions

| Action | Condition for Execution |
|--------|------------------------|
| Split large facades | When operational clarity demands it |
| Extract schemas to `schemas/` | When API contracts stabilize |
| Separate learning/proposals | When they become separate products |
| Normalize controls subdomain | When KillSwitch semantics finalize |

---

## 11. Related Domains Affected

Files moved out of policies now reside in:

| File | New Location | Domain |
|------|--------------|--------|
| `policy_driver.py` | `internal/platform/policy/engines/` | internal/platform/policy |

---

## 12. Change Log

| Date | Action | Details |
|------|--------|---------|
| 2026-01-22 | Initial analysis | 36 files documented |
| 2026-01-22 | Violation detected | `policy_driver.py` - AUDIENCE: INTERNAL |
| 2026-01-22 | Duplicate detected | `controls/KillSwitch/engines/facade.py` |
| 2026-01-22 | File moved | `policy_driver.py` → `internal/platform/policy/engines/` |
| 2026-01-22 | File deleted | `controls/KillSwitch/engines/facade.py` (duplicate) |
| 2026-01-22 | Status updated | CLEANUP COMPLETE |

---

*Generated: 2026-01-22*
*Version: v1.1*
