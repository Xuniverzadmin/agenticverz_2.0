# General Domain Wiring Analysis

**Date:** 2026-01-25
**Status:** RESEARCH COMPLETE
**Reference:** PIN-470, HOC Layer Topology V1

---

## Executive Summary

This report analyzes how the **general domain** (L4_runtime, L5_utils, L5_lifecycle, etc.) should serve as the triggering/orchestration mechanism for other customer domains. The analysis is **evidence-based** — every finding is backed by file paths and code patterns.

### Key Findings

| Category | Total Gaps | Critical | Medium | Low |
|----------|-----------|----------|--------|-----|
| DateTime Usage | 9 files | 0 | 9 | 0 |
| Governance/Orchestration | 21 files | 2 | 8 | 11 |
| Cross-Domain Transactions | 4 files | 2 | 2 | 0 |
| **TOTAL** | **34 files** | **4** | **19** | **11** |

---

## Part 1: What General Domain PROVIDES

### L4_RUNTIME (Authoritative Orchestration)

| Component | Purpose | Exports |
|-----------|---------|---------|
| `governance_orchestrator.py` | Contract activation, job tracking, audit triggering | `GovernanceOrchestrator`, `activate_contract()`, `start_job()`, `complete_job()` |
| `transaction_coordinator.py` | Atomic cross-domain writes | `RunCompletionTransaction`, `get_transaction_coordinator()` |
| `plan_generation_engine.py` | L4 entry for run creation | `PlanGenerationEngine`, `generate_plan_for_run()` |
| `constraint_checker.py` | Inspection constraints | `InspectionConstraintChecker`, `check_inspection_allowed()` |
| `phase_status_invariants.py` | Phase-status enforcement | `PhaseStatusInvariantChecker`, `check_phase_status_invariant()` |
| `run_governance_facade.py` | Centralized governance access | `RunGovernanceFacade`, `get_run_governance_facade()` |

### L5_UTILS (Shared Utilities)

| Component | Purpose | Exports |
|-----------|---------|---------|
| `time.py` | UTC time utility | `utc_now()` |

### L5_LIFECYCLE (Lifecycle Management)

| Component | Purpose | Exports |
|-----------|---------|---------|
| `base.py` | Stage handler protocol | `StageHandler`, `StageRegistry`, `StageResult`, `StageContext` |
| `onboarding.py` | Knowledge plane onboarding | `OnboardingOrchestrator` |
| `offboarding.py` | Knowledge plane offboarding | `OffboardingOrchestrator` |

### L5_CONTROLS (Control Mechanisms)

| Component | Purpose | Exports |
|-----------|---------|---------|
| `guard_write_engine.py` | Guard/killswitch operations | `GuardWriteService` |

### L6_DRIVERS (Data Access)

| Component | Purpose |
|-----------|---------|
| `transaction_coordinator.py` | Cross-domain atomic writes |
| `budget_tracker.py` | Budget enforcement |
| `cross_domain.py` | Cost anomaly → Incident linking |
| `decisions.py` | Decision contract enforcement |
| `ledger.py` | Audit ledger |

---

## Part 2: Current Imports FROM General (17 files)

**Pattern:** Only `utc_now` from `L5_utils.time` is being imported.

| Domain | Files | What They Import |
|--------|-------|------------------|
| **Activity** | 4 | `utc_now` |
| **Incidents** | 2 | `utc_now` |
| **Policies** | 6 | `utc_now` |
| **Analytics** | 2 | `utc_now` |
| **Account** | 2 | `utc_now` |
| **Overview** | 1 | `utc_now` |
| **Logs** | 0 | — |
| **API_Keys** | 0 | — |

**Critical Gap:** L4_runtime services (governance_orchestrator, transaction_coordinator) are NOT being imported by any domain.

---

## Part 3: GAPS — DateTime Usage (9 files)

Files using `datetime.now()` or `datetime.utcnow()` directly instead of `utc_now()`:

### Incidents Domain (3 files)

| File | Layer | Count | Pattern |
|------|-------|-------|---------|
| `L5_engines/hallucination_detector.py` | L5 | 2 | `datetime.now().year` |
| `L5_engines/evidence_report.py` | L5 | 2 | `datetime.utcnow().strftime()` |
| `L5_engines/runtime_switch.py` | L5 | 9 | `datetime.utcnow()` |

### Policies Domain (2 files)

| File | Layer | Count | Pattern |
|------|-------|-------|---------|
| `L5_engines/hallucination_detector.py` | L5 | 2 | `datetime.now().year` |
| `L6_drivers/orphan_recovery.py` | L6 | 2 | `datetime.utcnow()` |

### Analytics Domain (1 file)

| File | Layer | Count | Pattern |
|------|-------|-------|---------|
| `L5_engines/divergence.py` | L5 | 2 | `datetime.now()` |

### Integrations Domain (1 file)

| File | Layer | Count | Pattern |
|------|-------|-------|---------|
| `L3_adapters/customer_logs_adapter.py` | L3 | 1 | `datetime.utcnow()` |

### General Domain (1 file — internal)

| File | Layer | Count | Pattern |
|------|-------|-------|---------|
| `L6_drivers/worker_write_service_async.py` | L6 | 6 | `datetime.utcnow()` |

### Fix Required

```python
# Before
from datetime import datetime
timestamp = datetime.utcnow()

# After
from app.hoc.cus.general.L5_utils.time import utc_now
timestamp = utc_now()
```

---

## Part 4: GAPS — Governance/Orchestration (21 files)

### CRITICAL: Duplicate Governance Orchestrator

**Authoritative (General):**
```
/root/agenticverz2.0/backend/app/hoc/cus/general/L4_runtime/engines/governance_orchestrator.py
```

**Duplicate (Policies):**
```
/root/agenticverz2.0/backend/app/hoc/cus/policies/L5_engines/governance_orchestrator.py
```

**Issue:** Policies domain has its own `governance_orchestrator.py` that does NOT import from general. This is a **duplication** of orchestration logic.

### CRITICAL: Duplicate Transaction Coordinator

**Authoritative (General):**
```
/root/agenticverz2.0/backend/app/hoc/cus/general/L4_runtime/drivers/transaction_coordinator.py
```

**Duplicate (Policies):**
```
/root/agenticverz2.0/backend/app/hoc/cus/policies/L6_drivers/transaction_coordinator.py
```

**Issue:** Both handle cross-domain atomic writes (incidents + policies + traces). Should be consolidated.

### Files Needing Governance Integration

#### Policies Domain (9 files)

| File | Pattern | Risk |
|------|---------|------|
| `L5_engines/governance_orchestrator.py` | Duplicate orchestrator | CRITICAL |
| `L6_drivers/transaction_coordinator.py` | Duplicate coordinator | CRITICAL |
| `L5_engines/contract_engine.py` | State machine | HIGH |
| `L5_engines/policy_proposal_engine.py` | Lifecycle management | MEDIUM |
| `L6_drivers/governance_signal_driver.py` | Governance signals | MEDIUM |
| `L5_engines/policy_driver.py` | Workflow mentions | MEDIUM |
| `L5_engines/validator_engine.py` | Governance validation | MEDIUM |
| `L5_engines/job_executor.py` | Workflow execution | MEDIUM |
| `L5_controls/drivers/runtime_switch.py` | Control mechanisms | LOW |

#### Incidents Domain (4 files)

| File | Pattern | Risk |
|------|---------|------|
| `L5_engines/incident_driver.py` | Orchestration | HIGH |
| `L5_engines/incident_write_engine.py` | Atomic transactions | HIGH |
| `L5_engines/lessons_engine.py` | Lifecycle | MEDIUM |
| `L5_engines/policy_violation_engine.py` | Cross-domain governance | MEDIUM |

#### Analytics Domain (3 files)

| File | Pattern | Risk |
|------|---------|------|
| `L5_engines/cost_anomaly_detector.py` | Multi-table writes | HIGH |
| `L5_engines/cost_write_engine.py` | Transaction coordination | HIGH |
| `L5_engines/pattern_detection.py` | Workflow orchestration | MEDIUM |

#### Account Domain (2 files)

| File | Pattern | Risk |
|------|---------|------|
| `L6_drivers/user_write_driver.py` | Dual session.commit() | MEDIUM |
| `L5_engines/tenant_engine.py` | Lifecycle | MEDIUM |

---

## Part 5: GAPS — Cross-Domain Transaction Consistency (4 files)

Files writing to multiple models without using `transaction_coordinator`:

### HIGH RISK

| File | Models Written | Transaction Coord? |
|------|----------------|-------------------|
| `policies/L6_drivers/policy_proposal_write_driver.py` | PolicyProposal, PolicyVersion, PolicyRules | NO |
| `analytics/L6_drivers/cost_write_driver.py` | FeatureTag, CostRecord, CostBudget | NO |

### MEDIUM RISK

| File | Models Written | Transaction Coord? |
|------|----------------|-------------------|
| `incidents/L6_drivers/incident_aggregator.py` | Incident, IncidentEvent | NO (same domain) |
| `analytics/L6_drivers/alert_driver.py` | CostSimAlertQueueModel, CostSimCBIncidentModel | NO |

---

## Part 6: Wiring Recommendations by Domain

### 1. Policies Domain

| Priority | Action | File(s) |
|----------|--------|---------|
| P0 | Evaluate consolidation of `governance_orchestrator.py` with general | L5_engines/governance_orchestrator.py |
| P0 | Evaluate consolidation of `transaction_coordinator.py` with general | L6_drivers/transaction_coordinator.py |
| P1 | Use `utc_now()` | L5_engines/hallucination_detector.py, L6_drivers/orphan_recovery.py |
| P2 | Evaluate transaction_coordinator usage | L6_drivers/policy_proposal_write_driver.py |

### 2. Incidents Domain

| Priority | Action | File(s) |
|----------|--------|---------|
| P1 | Use `utc_now()` | L5_engines/hallucination_detector.py, L5_engines/evidence_report.py, L5_engines/runtime_switch.py |
| P2 | Evaluate RunGovernanceFacade integration | L5_engines/incident_driver.py |
| P2 | Evaluate transaction_coordinator usage | L5_engines/incident_write_engine.py |

### 3. Analytics Domain

| Priority | Action | File(s) |
|----------|--------|---------|
| P1 | Use `utc_now()` | L5_engines/divergence.py |
| P2 | Evaluate transaction_coordinator usage | L6_drivers/cost_write_driver.py, L6_drivers/alert_driver.py |

### 4. Integrations Domain

| Priority | Action | File(s) |
|----------|--------|---------|
| P1 | Use `utc_now()` | L3_adapters/customer_logs_adapter.py |

### 5. Account Domain

| Priority | Action | File(s) |
|----------|--------|---------|
| P2 | Evaluate transaction_coordinator usage | L6_drivers/user_write_driver.py |

### 6. General Domain (Self-fix)

| Priority | Action | File(s) |
|----------|--------|---------|
| P1 | Use `utc_now()` | L6_drivers/worker_write_service_async.py |

---

## Part 7: Execution Order

### Step 1: DateTime Standardization (9 files)
Low risk, mechanical fix. Update all files to use `utc_now()` from general.

### Step 2: Governance Integration Analysis (Critical files)
Deep analysis required before wiring:
1. Compare `policies/governance_orchestrator.py` vs `general/governance_orchestrator.py`
2. Compare `policies/transaction_coordinator.py` vs `general/transaction_coordinator.py`
3. Determine: Merge, delegate, or domain-specific variation?

### Step 3: Transaction Coordinator Wiring
After Step 2 analysis, wire multi-model write operations to appropriate coordinator.

---

## Appendix: File Paths

### DateTime Gaps (Full Paths)

```
/root/agenticverz2.0/backend/app/hoc/cus/incidents/L5_engines/hallucination_detector.py
/root/agenticverz2.0/backend/app/hoc/cus/incidents/L5_engines/evidence_report.py
/root/agenticverz2.0/backend/app/hoc/cus/incidents/L5_engines/runtime_switch.py
/root/agenticverz2.0/backend/app/hoc/cus/analytics/L5_engines/divergence.py
/root/agenticverz2.0/backend/app/hoc/cus/policies/L5_engines/hallucination_detector.py
/root/agenticverz2.0/backend/app/hoc/cus/policies/L6_drivers/orphan_recovery.py
/root/agenticverz2.0/backend/app/hoc/cus/integrations/L3_adapters/customer_logs_adapter.py
/root/agenticverz2.0/backend/app/hoc/cus/general/L6_drivers/worker_write_service_async.py
```

### Governance Gaps (Full Paths)

```
# CRITICAL DUPLICATES
/root/agenticverz2.0/backend/app/hoc/cus/policies/L5_engines/governance_orchestrator.py
/root/agenticverz2.0/backend/app/hoc/cus/policies/L6_drivers/transaction_coordinator.py

# HIGH PRIORITY
/root/agenticverz2.0/backend/app/hoc/cus/policies/L5_engines/contract_engine.py
/root/agenticverz2.0/backend/app/hoc/cus/incidents/L5_engines/incident_driver.py
/root/agenticverz2.0/backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py
/root/agenticverz2.0/backend/app/hoc/cus/analytics/L5_engines/cost_anomaly_detector.py
/root/agenticverz2.0/backend/app/hoc/cus/analytics/L5_engines/cost_write_engine.py
```

### Transaction Gaps (Full Paths)

```
/root/agenticverz2.0/backend/app/hoc/cus/policies/L6_drivers/policy_proposal_write_driver.py
/root/agenticverz2.0/backend/app/hoc/cus/analytics/L6_drivers/cost_write_driver.py
/root/agenticverz2.0/backend/app/hoc/cus/incidents/L6_drivers/incident_aggregator.py
/root/agenticverz2.0/backend/app/hoc/cus/analytics/L6_drivers/alert_driver.py
```

---

## References

- **PIN-470:** HOC Layer Inventory
- **PIN-454:** Cross-Domain Orchestration Audit
- **HOC_LAYER_TOPOLOGY_V1.md:** Layer architecture
- **DRIVER_ENGINE_CONTRACT.md:** L5/L6 boundary rules

---

**Report Generated:** 2026-01-25
**Author:** Claude (Evidence-Based Analysis)
