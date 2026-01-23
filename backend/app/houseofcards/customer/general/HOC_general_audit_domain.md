# GENERAL DOMAIN INTERNAL DUPLICATION AUDIT REPORT

**Domain:** `houseofcards/customer/general`
**Date:** 2026-01-23
**Scope:** Internal duplications only (within general domain)
**Audience:** CUSTOMER

---

## EXECUTIVE SUMMARY

| Severity | Count | Description |
|----------|-------|-------------|
| **CRITICAL** | 2 | Same class name in multiple files |
| **WARNING** | 0 | Similar functionality, different names |
| **CLEAN** | 3 | Verified distinct responsibilities |

---

## CRITICAL DUPLICATION #1: AlertFatigueController

### Collision Details

| Attribute | File 1 | File 2 |
|-----------|--------|--------|
| **Location** | `engines/alert_fatigue.py` | `engines/fatigue_controller.py` |
| **Class Name** | `AlertFatigueController` | `AlertFatigueController` |
| **Singleton** | `get_alert_fatigue_controller()` | `get_alert_fatigue_controller()` |
| **Reference** | PIN-454 Section 3.3 | GAP-049 |
| **LOC** | 528 | 735 |

### Functional Comparison

| Feature | alert_fatigue.py | fatigue_controller.py |
|---------|------------------|----------------------|
| Rate limiting | YES | YES |
| Suppression | YES | YES |
| Domain cooldowns | YES | YES |
| Tenant rate limits | YES | YES |
| Aggregation | NO | YES |
| Mode enum (MONITOR/WARN/ENFORCE/AGGREGATE) | NO | YES |
| Fatigue metrics | NO | YES |
| Suppression policies | NO | YES |

### Import Collision Risk

```python
# DANGER: Which one gets imported?
from app.houseofcards.customer.general.engines.alert_fatigue import get_alert_fatigue_controller
from app.houseofcards.customer.general.engines.fatigue_controller import get_alert_fatigue_controller
```

### Recommendation

**CONSOLIDATE** into `fatigue_controller.py` (more complete implementation):
1. `fatigue_controller.py` is the **superset** (735 LOC vs 528 LOC)
2. Has additional features: modes, metrics, suppression policies
3. Rename or delete `alert_fatigue.py` after verifying no unique logic

---

## CRITICAL DUPLICATION #2: KnowledgePlane

### Collision Details

| Attribute | File 1 | File 2 |
|-----------|--------|--------|
| **Location** | `engines/knowledge_lifecycle_manager.py` | `lifecycle/engines/knowledge_plane.py` |
| **Class Name** | `KnowledgePlane` | `KnowledgePlane` |
| **Reference** | GAP-086 | GAP-056 |
| **LOC** | 909 (file) | 468 (file) |
| **Purpose** | Lifecycle state machine | Knowledge graph abstraction |

### Semantic Distinction (CRITICAL)

These classes have the **SAME NAME** but **DIFFERENT purposes**:

| Aspect | knowledge_lifecycle_manager.py | lifecycle/engines/knowledge_plane.py |
|--------|-------------------------------|--------------------------------------|
| **Purpose** | Lifecycle representation (state machine) | Knowledge graph (nodes, embeddings) |
| **Core Data** | `state`, `bound_policies`, `transition_history` | `nodes`, `embedding`, `source_ids` |
| **Status Enum** | `KnowledgePlaneLifecycleState` | `KnowledgePlaneStatus` |
| **Node Type** | N/A | `KnowledgeNodeType` |
| **Registry** | `KnowledgeLifecycleManager` | `KnowledgePlaneRegistry` |

### Import Collision Risk

```python
# DANGER: Same class name, different behaviors!
from app.houseofcards.customer.general.engines.knowledge_lifecycle_manager import KnowledgePlane
from app.houseofcards.customer.general.lifecycle.engines.knowledge_plane import KnowledgePlane
```

### Recommendation

**RENAME** to clarify purpose:
- `knowledge_lifecycle_manager.py`: Rename class to `KnowledgePlaneLifecycle` or `LifecycleKnowledgePlane`
- `lifecycle/engines/knowledge_plane.py`: Keep as `KnowledgePlane` (more aligned with graph semantics)

---

## VERIFIED NO DUPLICATION: Governance Files

### Analysis

| File 1 | File 2 | Result |
|--------|--------|--------|
| `runtime/engines/run_governance_facade.py` | `runtime/engines/governance_orchestrator.py` | **DISTINCT** |

**run_governance_facade.py** (328 LOC):
- Role: L5 worker → L4 interface
- Responsibilities: Policy evaluation, lessons emission
- Methods: `create_policy_evaluation()`, `emit_near_threshold_lesson()`

**governance_orchestrator.py** (800 LOC):
- Role: Contract → job → audit orchestration
- Responsibilities: Job lifecycle, contract management
- Class: `GovernanceOrchestrator`

**Conclusion:** Different responsibilities, no collision.

---

## VERIFIED NO DUPLICATION: Alert Files

### Analysis

| File | Class | Responsibility |
|------|-------|----------------|
| `engines/alert_emitter.py` | `AlertEmitter` | Emit alerts via channels (UI, webhook, slack, email) |
| `engines/alert_fatigue.py` | `AlertFatigueController` | Rate limiting and suppression |
| `engines/fatigue_controller.py` | `AlertFatigueController` | Rate limiting and suppression (DUPLICATE - see above) |
| `facades/alerts_facade.py` | `AlertsFacade` | L4 facade for alert operations |

**Note:** `AlertEmitter` and `AlertsFacade` are **DISTINCT** from fatigue controllers.

---

## VERIFIED NO DUPLICATION: Knowledge Files

### Analysis

| File | Class | Responsibility |
|------|-------|----------------|
| `engines/knowledge_lifecycle_manager.py` | `KnowledgePlane`, `KnowledgeLifecycleManager` | Lifecycle state machine |
| `engines/knowledge_sdk.py` | `KnowledgeSDK` | SDK facade for lifecycle operations |
| `lifecycle/engines/knowledge_plane.py` | `KnowledgePlane`, `KnowledgePlaneRegistry` | Knowledge graph abstraction |

**knowledge_sdk.py** imports from `app.services.knowledge_lifecycle_manager` (external to houseofcards).

---

## SUMMARY OF FINDINGS

### Critical Duplications Requiring Action

| ID | Collision | Files | Recommendation |
|----|-----------|-------|----------------|
| **GEN-DUP-001** | `AlertFatigueController` class | `alert_fatigue.py`, `fatigue_controller.py` | CONSOLIDATE into `fatigue_controller.py` |
| **GEN-DUP-002** | `KnowledgePlane` class | `knowledge_lifecycle_manager.py`, `knowledge_plane.py` | RENAME one to distinguish |

### Singleton Function Collisions

| Function | Files |
|----------|-------|
| `get_alert_fatigue_controller()` | `alert_fatigue.py`, `fatigue_controller.py` |

### No Action Required

| Files | Status |
|-------|--------|
| `run_governance_facade.py` vs `governance_orchestrator.py` | CLEAN - different responsibilities |
| `alert_emitter.py` vs `alerts_facade.py` | CLEAN - emitter vs facade |
| `knowledge_sdk.py` | CLEAN - SDK wrapper only |

---

## CONSOLIDATION PRIORITY

1. **HIGH PRIORITY:** `AlertFatigueController` duplication
   - Risk: Runtime import confusion
   - Action: Delete `alert_fatigue.py` after merging any unique logic into `fatigue_controller.py`

2. **MEDIUM PRIORITY:** `KnowledgePlane` name collision
   - Risk: Developer confusion, wrong import
   - Action: Rename lifecycle class to `KnowledgePlaneLifecycle`

---

## FILES AUDITED

### Facades
- `facades/alerts_facade.py` (671 LOC)
- `facades/compliance_facade.py`
- `facades/lifecycle_facade.py` (701 LOC)
- `facades/monitors_facade.py`
- `facades/scheduler_facade.py`

### Engines
- `engines/alert_emitter.py` (412 LOC)
- `engines/alert_fatigue.py` (528 LOC) **[DUPLICATE]**
- `engines/fatigue_controller.py` (735 LOC) **[DUPLICATE]**
- `engines/alert_log_linker.py`
- `engines/cus_health_service.py`
- `engines/cus_telemetry_service.py`
- `engines/cus_enforcement_service.py`
- `engines/knowledge_lifecycle_manager.py` (909 LOC) **[NAME COLLISION]**
- `engines/knowledge_sdk.py` (972 LOC)
- `engines/panel_invariant_monitor.py`

### Lifecycle Engines
- `lifecycle/engines/onboarding.py`
- `lifecycle/engines/offboarding.py`
- `lifecycle/engines/pool_manager.py`
- `lifecycle/engines/base.py`
- `lifecycle/engines/knowledge_plane.py` (468 LOC) **[NAME COLLISION]**
- `lifecycle/engines/execution.py`

### Runtime Engines
- `runtime/engines/run_governance_facade.py` (328 LOC)
- `runtime/engines/transaction_coordinator.py`
- `runtime/engines/phase_status_invariants.py`
- `runtime/engines/plan_generation_engine.py`
- `runtime/engines/constraint_checker.py`
- `runtime/engines/governance_orchestrator.py` (800 LOC)

### Other
- `controls/engines/guard_write_service.py`
- `cross-domain/engines/cross_domain.py`
- `workflow/contracts/engines/contract_service.py`
- `ui/engines/rollout_projection.py`

---

## NEXT STEPS

1. Review and approve consolidation plan for `AlertFatigueController`
2. Decide on rename strategy for `KnowledgePlane` collision
3. Proceed to audit next domain (if applicable)
