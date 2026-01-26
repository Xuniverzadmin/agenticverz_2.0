# General Domain Function Catalog & Wiring Candidates

**Date:** 2026-01-25
**Status:** RESEARCH COMPLETE
**Reference:** PIN-470, HOC Layer Topology V1

---

## Executive Summary

This report catalogs all functions/methods provided by the **general domain** (L4_runtime, L5_lifecycle, L5_controls, L5_workflow, L5_engines) and identifies candidates in other customer domains who could harness these centralized functions instead of domain-wise repeated development.

### Key Statistics

| Component | Files | Classes | Functions | Wiring Candidates |
|-----------|-------|---------|-----------|-------------------|
| L4_runtime | 6 | 12+ | 40+ | 21 files |
| L5_lifecycle | 6 | 15+ | 60+ | 0 (specialized) |
| L5_controls | 2 | 2 | 12 | 4 files |
| L5_workflow | 1 | 3 | 25+ | 9 files |
| L5_engines | 24 | 20+ | 100+ | 17 files |
| **TOTAL** | **39** | **52+** | **237+** | **51 files** |

---

## Part 1: L4_RUNTIME — Authoritative Orchestration

**Path:** `hoc/cus/general/L4_runtime/`

### 1.1 governance_orchestrator.py

**Purpose:** Orchestrates governance workflow from contract activation through audit triggering.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `HealthLookup` (Protocol) | Health state capture | `capture_health_snapshot()` |
| `JobState` | In-memory job representation | (dataclass) |
| `JobStateMachine` | Job lifecycle state machine | `can_transition()`, `validate_transition()`, `execute_transition()` |
| `ContractActivationService` | APPROVED → ACTIVE transitions | `activate_contract()` |
| `ExecutionOrchestrator` | Contract → job plan orchestration | `create_job_from_contract()`, `get_job_state()` |
| `AuditTrigger` | Evidence handoff to audit | `trigger_audit()` |
| `GovernanceOrchestrator` | Main facade | `activate_and_execute()`, `complete_job()`, `fail_job()` |

**Exports:**
```python
GovernanceOrchestrator
JobStateMachine
ContractActivationService
ExecutionOrchestrator
AuditTrigger
```

### 1.2 transaction_coordinator.py

**Purpose:** Atomic cross-domain writes for run completion.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `TransactionPhase` (Enum) | Transaction execution phases | NOT_STARTED → COMMITTED |
| `TransactionFailed` | Exception with phase context | (exception) |
| `DomainResult` | Single domain operation result | `to_dict()` |
| `TransactionResult` | Complete transaction result | `to_dict()` |
| `RunCompletionTransaction` | Main transaction executor | `execute()`, `_create_incident()`, `_evaluate_policy()`, `_complete_trace()` |

**Transaction Flow:**
```
1. Begin transaction
2. Create incident (via IncidentFacade)
3. Create policy evaluation (via GovernanceFacade)
4. Complete trace (via TraceFacade)
5. Commit transaction
6. Publish events (post-commit only)
```

**Exports:**
```python
RunCompletionTransaction
get_transaction_coordinator()
TransactionFailed
TransactionPhase
DomainResult
TransactionResult
```

### 1.3 constraint_checker.py

**Purpose:** Inspection constraint checking before execution.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `InspectionConstraintChecker` | Pre-execution validation | `check_inspection_allowed()`, `validate_budget()`, `validate_rate_limit()` |

**Exports:**
```python
InspectionConstraintChecker
check_inspection_allowed()
```

### 1.4 phase_status_invariants.py

**Purpose:** Phase-status enforcement for lifecycle states.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `PhaseStatusInvariantChecker` | Phase-status validation | `check_phase_status_invariant()`, `validate_transition()` |

**Exports:**
```python
PhaseStatusInvariantChecker
check_phase_status_invariant()
```

### 1.5 plan_generation_engine.py

**Purpose:** L4 entry point for run creation and plan generation.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `PlanGenerationEngine` | Plan creation and validation | `generate_plan_for_run()`, `validate_plan()`, `estimate_cost()` |

**Exports:**
```python
PlanGenerationEngine
generate_plan_for_run()
```

### 1.6 run_governance_facade.py

**Purpose:** Centralized governance access for runs.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `RunGovernanceFacade` | Unified governance interface | `start_run()`, `complete_run()`, `fail_run()`, `get_governance_state()` |

**Exports:**
```python
RunGovernanceFacade
get_run_governance_facade()
```

---

## Part 2: L5_LIFECYCLE — Stage Handler Pattern

**Path:** `hoc/cus/general/L5_lifecycle/`

### 2.1 base.py — Stage Handler Protocol

**Purpose:** Defines the contract for lifecycle stage handlers.

**Key Invariant:**
> Stage handlers are DUMB PLUGINS. They do NOT manage state. They do NOT emit events. They do NOT check policies. The orchestrator does ALL of that.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `StageStatus` (Enum) | Stage result status | SUCCESS, FAILURE, PENDING, SKIPPED |
| `StageContext` | Context passed to handlers | (dataclass) |
| `StageResult` | Handler return value | `ok()`, `fail()`, `pending()`, `skipped()` |
| `StageHandler` (Protocol) | Handler contract | `execute()`, `can_rollback()`, `rollback()` |
| `StageRegistry` | Handler registration | `register()`, `get()`, `all()` |

**Exports:**
```python
StageHandler (Protocol)
StageContext
StageResult
StageStatus
StageRegistry
```

### 2.2 onboarding.py — 7 Onboarding Handlers

**Purpose:** Knowledge plane onboarding lifecycle.

**Handlers:**

| Handler | Transition | Purpose |
|---------|------------|---------|
| `RegisterHandler` | UNREGISTERED → PENDING_VERIFY | Initial registration |
| `VerifyHandler` | PENDING_VERIFY → VERIFIED | Connection verification |
| `IngestHandler` | VERIFIED → INGESTING | Data ingestion |
| `IndexHandler` | INGESTING → INDEXING | Build search index |
| `ClassifyHandler` | INDEXING → CLASSIFIED | Schema classification |
| `ActivateHandler` | CLASSIFIED → ACTIVE | Enable for queries |
| `GovernHandler` | ACTIVE → GOVERNED | Policy binding |

**Exports:**
```python
OnboardingOrchestrator
RegisterHandler
VerifyHandler
IngestHandler
IndexHandler
ClassifyHandler
ActivateHandler
GovernHandler
```

### 2.3 offboarding.py — 5 Offboarding Handlers

**Purpose:** Knowledge plane offboarding lifecycle.

**Handlers:**

| Handler | Transition | Purpose |
|---------|------------|---------|
| `DeregisterHandler` | GOVERNED → PENDING_DEACTIVATE | Begin deregistration |
| `VerifyDeactivateHandler` | * → DEACTIVATING | Verify deactivation safe |
| `DeactivateHandler` | DEACTIVATING → DEACTIVATED | Disable queries |
| `ArchiveHandler` | DEACTIVATED → ARCHIVED | Archive data |
| `PurgeHandler` | ARCHIVED → PURGED | Complete removal |

**Exports:**
```python
OffboardingOrchestrator
DeregisterHandler
VerifyDeactivateHandler
DeactivateHandler
ArchiveHandler
PurgeHandler
```

### 2.4 pool_manager.py — Connection Pool Management

**Purpose:** Unified connection pool management.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `ConnectionPoolManager` | Pool lifecycle | `acquire()`, `release()`, `close_all()`, `stats()` |

**Exports:**
```python
ConnectionPoolManager
get_pool_manager()
```

---

## Part 3: L5_CONTROLS — Guard/Killswitch Mechanisms

**Path:** `hoc/cus/general/L5_controls/`

### 3.1 guard_write_engine.py

**Purpose:** Guard write operations with L5→L6 delegation pattern.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `GuardWriteService` | Killswitch + Incident operations | See below |

**Killswitch Methods:**
```python
get_or_create_killswitch_state(entity_type, entity_id, tenant_id)
freeze_killswitch(state, by, reason, auto, trigger)
unfreeze_killswitch(state, by)
```

**Incident Methods:**
```python
acknowledge_incident(incident)
resolve_incident(incident)
create_demo_incident(...)
```

**Exports:**
```python
GuardWriteService
get_guard_write_engine()
```

### 3.2 guard_write_driver.py (L6)

**Purpose:** Pure DB operations for guard writes.

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `GuardWriteDriver` | DB-only operations | (mirrors GuardWriteService) |

---

## Part 4: L5_WORKFLOW — Contract State Machine

**Path:** `hoc/cus/general/L5_workflow/contracts/engines/`

### 4.1 contract_engine.py

**Purpose:** System Contract state machine with MAY_NOT enforcement.

**Invariants (LOCKED):**
- CONTRACT-001: Status transitions must follow state machine
- CONTRACT-002: APPROVED requires approved_by
- CONTRACT-003: ACTIVE requires job exists
- CONTRACT-004: COMPLETED requires audit_verdict = PASS
- CONTRACT-005: Terminal states are immutable

**Classes:**

| Class | Purpose | Methods |
|-------|---------|---------|
| `ContractState` | In-memory contract state | (dataclass) |
| `ContractStateMachine` | State machine logic | `can_transition()`, `transition()`, `validate_invariants()` |
| `ContractService` | Main facade | `create_from_proposal()`, `approve()`, `activate()`, `complete()`, `reject()` |

**State Transitions:**
```
DRAFT → PENDING_REVIEW → APPROVED → ACTIVE → COMPLETED
                      ↘         ↘
                     REJECTED   EXPIRED/CANCELLED/FAILED
```

**MAY_NOT Enforcement:**
> MAY_NOT verdicts are mechanically un-overridable. No constructor, method, or bypass can create contracts from MAY_NOT.

**Exports:**
```python
ContractService
ContractStateMachine
ContractState
CONTRACT_SERVICE_VERSION
```

---

## Part 5: L5_ENGINES — Shared Business Logic (24 files)

**Path:** `hoc/cus/general/L5_engines/`

### 5.1 Utilities (Pure Computation)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `canonical_json.py` | Deterministic JSON serialization | `canonical_dumps()`, `canonical_loads()` |
| `deterministic.py` | Deterministic execution utilities | `DeterministicClock`, `DeterministicRandom` |
| `db_helpers.py` | Row extraction utilities | `extract_row()`, `extract_rows()` |
| `metrics_helpers.py` | Prometheus metrics helpers | `counter()`, `histogram()`, `gauge()` |

### 5.2 Rate Limiting & Concurrency

| File | Purpose | Key Exports |
|------|---------|-------------|
| `rate_limiter.py` | Redis-backed rate limiting | `RateLimiter`, `check_rate_limit()` |
| `concurrent_runs.py` | Redis-backed concurrent run limits | `ConcurrentRunLimiter`, `acquire_slot()`, `release_slot()` |

### 5.3 Security & Validation

| File | Purpose | Key Exports |
|------|---------|-------------|
| `input_sanitizer.py` | Prompt injection protection | `sanitize_input()`, `detect_injection()` |
| `webhook_verify.py` | Webhook signature verification | `verify_signature()`, `generate_signature()` |

### 5.4 Alert & Fatigue Management

| File | Purpose | Key Exports |
|------|---------|-------------|
| `fatigue_controller.py` | Alert fatigue management | `AlertFatigueController`, `should_suppress()` |
| `alert_log_linker.py` | Alert-to-log correlation | `AlertLogLinker`, `link_alert_to_log()` |
| `alerts_facade.py` | Alerts unified interface | `AlertsFacade` |

### 5.5 Lifecycle & Knowledge Management

| File | Purpose | Key Exports |
|------|---------|-------------|
| `knowledge_lifecycle_manager.py` | THE ORCHESTRATOR | `KnowledgeLifecycleManager`, `onboard()`, `offboard()` |
| `knowledge_sdk.py` | Knowledge SDK facade | `KnowledgeSDK`, `query()`, `ingest()` |
| `lifecycle_facade.py` | Lifecycle unified interface | `LifecycleFacade` |
| `lifecycle_stages_base.py` | Stage handler re-export | `StageHandler`, `StageContext`, `StageResult` |

### 5.6 Panel & Monitor Support

| File | Purpose | Key Exports |
|------|---------|-------------|
| `panel_invariant_monitor.py` | Panel invariant monitoring | `PanelInvariantMonitor`, `check_invariants()` |
| `monitors_facade.py` | Monitors unified interface | `MonitorsFacade` |

### 5.7 Other Facades

| File | Purpose | Key Exports |
|------|---------|-------------|
| `compliance_facade.py` | Compliance unified interface | `ComplianceFacade` |
| `scheduler_facade.py` | Scheduler unified interface | `SchedulerFacade` |
| `control_registry.py` | SOC2 Trust Service Criteria | `ControlRegistry`, `get_control()` |
| `plan_inspector.py` | Plan validation before execution | `PlanInspector`, `validate_plan()` |
| `runtime.py` | Runtime utilities | `RuntimeContext` |
| `guard.py` | Guard contract DTOs | `GuardDTO`, `GuardConfig` |
| `cus_health_shim.py` | DEPRECATED health shim | `CusHealthShim` |

---

## Part 6: WIRING CANDIDATES BY DOMAIN

### 6.1 Policies Domain (21 files)

**CRITICAL: Duplicate Components**

| Duplicate File | General Authoritative | Action |
|----------------|----------------------|--------|
| `policies/L5_engines/governance_orchestrator.py` | `general/L4_runtime/governance_orchestrator.py` | CONSOLIDATE |
| `policies/L6_drivers/transaction_coordinator.py` | `general/L4_runtime/transaction_coordinator.py` | CONSOLIDATE |

**High-Priority Wiring:**

| File | Current State | Wiring Target | Priority |
|------|---------------|---------------|----------|
| `contract_engine.py` | Own state machine | Evaluate reuse from `L5_workflow/contract_engine.py` | HIGH |
| `policy_proposal_engine.py` | Own lifecycle | Wire to `KnowledgeLifecycleManager` pattern | MEDIUM |
| `governance_signal_driver.py` | Own governance | Wire to `RunGovernanceFacade` | MEDIUM |
| `job_executor.py` | Own execution | Wire to `GovernanceOrchestrator` | MEDIUM |
| `validator_engine.py` | Own validation | Evaluate `PlanInspector` reuse | MEDIUM |

**DateTime Standardization:**

| File | Pattern | Fix |
|------|---------|-----|
| `hallucination_detector.py` | `datetime.now().year` | Use `utc_now()` |
| `orphan_recovery.py` | `datetime.utcnow()` | Use `utc_now()` |

### 6.2 Incidents Domain (4 files)

**High-Priority Wiring:**

| File | Current State | Wiring Target | Priority |
|------|---------------|---------------|----------|
| `incident_driver.py` | Own orchestration | Wire to `GovernanceOrchestrator` | HIGH |
| `incident_write_engine.py` | Own transactions | Wire to `RunCompletionTransaction` | HIGH |
| `lessons_engine.py` | Own lifecycle | Evaluate `StageHandler` pattern | MEDIUM |
| `policy_violation_engine.py` | Own governance | Wire to `RunGovernanceFacade` | MEDIUM |

**DateTime Standardization:**

| File | Pattern | Fix |
|------|---------|-----|
| `hallucination_detector.py` | `datetime.now().year` | Use `utc_now()` |
| `evidence_report.py` | `datetime.utcnow().strftime()` | Use `utc_now()` |
| `runtime_switch.py` | `datetime.utcnow()` (9 occurrences) | Use `utc_now()` |

### 6.3 Analytics Domain (3 files)

**High-Priority Wiring:**

| File | Current State | Wiring Target | Priority |
|------|---------------|---------------|----------|
| `cost_anomaly_detector.py` | Multi-table writes | Wire to `RunCompletionTransaction` | HIGH |
| `cost_write_engine.py` | Own transactions | Wire to `RunCompletionTransaction` | HIGH |
| `pattern_detection.py` | Own orchestration | Evaluate `GovernanceOrchestrator` | MEDIUM |

**DateTime Standardization:**

| File | Pattern | Fix |
|------|---------|-----|
| `divergence.py` | `datetime.now()` | Use `utc_now()` |

### 6.4 Integrations Domain (1 file)

**DateTime Standardization:**

| File | Pattern | Fix |
|------|---------|-----|
| `customer_logs_adapter.py` | `datetime.utcnow()` | Use `utc_now()` |

### 6.5 Account Domain (2 files)

**Medium-Priority Wiring:**

| File | Current State | Wiring Target | Priority |
|------|---------------|---------------|----------|
| `user_write_driver.py` | Dual `session.commit()` | Evaluate transaction pattern | MEDIUM |
| `tenant_engine.py` | Own lifecycle | Evaluate `StageHandler` pattern | MEDIUM |

### 6.6 General Domain (Self-Fix)

**DateTime Standardization:**

| File | Pattern | Fix |
|------|---------|-----|
| `worker_write_service_async.py` | `datetime.utcnow()` (6 occurrences) | Use `utc_now()` |

---

## Part 7: WIRING PRIORITY MATRIX

### P0 — CRITICAL (Architectural Consistency)

| Action | Files | Risk |
|--------|-------|------|
| Consolidate governance orchestrators | 2 | CRITICAL |
| Consolidate transaction coordinators | 2 | CRITICAL |

### P1 — HIGH (DateTime Standardization)

| Action | Files | Risk |
|--------|-------|------|
| Replace `datetime.now/utcnow()` with `utc_now()` | 9 | LOW |

### P2 — MEDIUM (Governance Integration)

| Action | Files | Risk |
|--------|-------|------|
| Wire to `RunGovernanceFacade` | 4 | MEDIUM |
| Wire to `RunCompletionTransaction` | 4 | MEDIUM |
| Evaluate `StageHandler` pattern adoption | 3 | MEDIUM |

### P3 — LOW (Pattern Adoption)

| Action | Files | Risk |
|--------|-------|------|
| Evaluate `PlanInspector` reuse | 2 | LOW |
| Evaluate `KnowledgeLifecycleManager` pattern | 2 | LOW |

---

## Part 8: RECOMMENDED EXECUTION ORDER

### Step 1: DateTime Standardization (9 files)
Low risk, mechanical fix. Update all files to use `utc_now()` from general.

### Step 2: Governance Consolidation Analysis (Critical files)
Deep analysis required before wiring:
1. Compare `policies/governance_orchestrator.py` vs `general/governance_orchestrator.py`
2. Compare `policies/transaction_coordinator.py` vs `general/transaction_coordinator.py`
3. Determine: Merge, delegate, or domain-specific variation?

### Step 3: Transaction Coordinator Wiring
After Step 2 analysis, wire multi-model write operations to appropriate coordinator.

### Step 4: Pattern Adoption
Evaluate and adopt shared patterns where beneficial:
- `StageHandler` for lifecycle operations
- `RunGovernanceFacade` for governance access
- `PlanInspector` for validation

---

## Appendix: Import Patterns

### Current (17 files import from general)

All 17 files only import `utc_now()`:
```python
from app.hoc.cus.general.L5_utils.time import utc_now
```

### Target (After Wiring)

**For Governance:**
```python
from app.hoc.cus.general.L4_runtime.engines.governance_orchestrator import GovernanceOrchestrator
from app.hoc.cus.general.L4_runtime.facades.run_governance_facade import get_run_governance_facade
```

**For Transactions:**
```python
from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import (
    RunCompletionTransaction,
    get_transaction_coordinator,
)
```

**For Lifecycle:**
```python
from app.hoc.cus.general.L5_lifecycle.engines.base import StageHandler, StageContext, StageResult
```

**For Controls:**
```python
from app.hoc.cus.general.L5_controls.engines.guard_write_engine import GuardWriteService
```

---

## References

- **PIN-470:** HOC Layer Inventory
- **PIN-454:** Cross-Domain Orchestration Audit
- **HOC_LAYER_TOPOLOGY_V1.md:** Layer architecture
- **DRIVER_ENGINE_CONTRACT.md:** L5/L6 boundary rules
- **GENERAL_DOMAIN_WIRING_PHASE1.md:** Phase 1 gap analysis

---

**Report Generated:** 2026-01-25
**Author:** Claude (Evidence-Based Analysis)
