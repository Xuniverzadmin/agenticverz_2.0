# Signal Circuit Discovery: L4↔L5 Boundary

**Status:** PHASE 1 DISCOVERY COMPLETE
**Date:** 2025-12-31
**Boundary:** L4 (Domain Engines) ↔ L5 (Execution & Workers)
**Reference:** PRODUCT_DEVELOPMENT_CONTRACT_V3.md, L5_L4_SEMANTIC_MAPPING.md

---

## 1. Boundary Lock

```yaml
boundary_pair: L4↔L5
from_layer: L4 — Domain Engines
to_layer: L5 — Execution & Workers
direction: bidirectional
crossing_type: invocation + data + event
```

---

## 2. Declared Intent

| Field | Value |
|-------|-------|
| Contract Document | `docs/architecture/EXECUTION_SEMANTIC_CONTRACT.md` |
| Contract Version | DRAFT (Phase 3.2) |
| Intent Statement | "L5 (Workers) executes under L4 (Domain) authority; decisions are sync+pure, operations are async" |
| Enforcement Level | ADVISORY (contract exists, not fully CI-enforced) |

**Secondary Contract:**
- `docs/architecture/L5_L4_SEMANTIC_MAPPING.md` — Maps all L5 actions to L4 authorities

---

## 3. Expected Signals

| Signal ID | Signal Name | Emitter (Layer) | Consumer (Layer) | Transport | Consequence |
|-----------|-------------|-----------------|------------------|-----------|-------------|
| EXP-L4L5-001 | Run Queued | L2→L4 (API creates Run) | L5 (WorkerPool polls) | Database (L6) | Worker picks up run |
| EXP-L4L5-002 | Authorization Decision | L4 (at submission time) | L5 (runner reads) | Database (L6) | GRANTED/DENIED/PENDING |
| EXP-L4L5-003 | Budget Context | L4 (CostWriteService) | L5 (RunRunner loads) | Database (L6) | Hard budget enforcement |
| EXP-L4L5-004 | Policy Evaluation | L4 (PolicyEngine) | L5 (SkillExecutor) | Function call | Step allowed/blocked |
| EXP-L4L5-005 | Run Completed | L5 (RunRunner) | L4 (services observe) | Event publisher | Provenance created |
| EXP-L4L5-006 | Checkpoint Written | L5 (WorkflowEngine) | L5 (resume) | Database (L6) | Exactly-once step execution |
| EXP-L4L5-007 | Recovery Trigger | L4 (RecoveryRuleEngine) | L5 (RecoveryClaimWorker) | Database (L6) | Auto-recovery attempted |

---

## 4. Reality Inspection

### 4.1 Emitter Audit (L4 side)

| Location | What it emits | Explicit? | Consumed by? |
|----------|---------------|-----------|--------------|
| `workflow/engine.py` | Checkpoint state | YES | L5 resume |
| `services/scoped_execution.py` | Execution scope | YES | L5 workers |
| `services/recovery_rule_engine.py` | Recovery decisions | YES | L5 RecoveryClaimWorker |
| `services/cost_write_service.py` | Budget limits | YES | L5 RunRunner |
| `api/runs.py` (L2) | Run row with authorization_decision | YES | L5 RunRunner |

### 4.2 Consumer Audit (L5 side)

| Location | What it consumes | Source? | Fails if missing? |
|----------|------------------|---------|-------------------|
| `worker/pool.py:97-109` | Queued runs from DB | L6 (Run table) | NO (just waits) |
| `worker/runner.py:175-275` | authorization_decision | L6 (Run.authorization_decision) | YES (defaults GRANTED) |
| `worker/runner.py:83-124` | Budget context | L6 (Agent table) | NO (defaults soft mode) |
| `worker/runner.py:379-409` | Planner, memory, skills | **L4 DIRECT IMPORT** | YES (planning fails) |

### 4.3 Transport Audit

| Transport Type | Mechanism | Observable? | Documented? |
|----------------|-----------|-------------|-------------|
| Database poll | Run.status polling | YES (logs) | YES |
| Direct import | L5 imports L4 modules | NO (code-level) | PARTIAL |
| Event publisher | run.started, run.completed events | YES (logs) | YES |
| Checkpoint store | Redis/DB | YES (logs) | YES |

---

## 5. End-to-End Circuit Walk

### Circuit: Run Execution

```
SIGNAL: run.queued → run.completed

INTENT:
  → Declared at: EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 3)
  → Statement: "At-least-once worker dispatch"

EMISSION:
  → Emitter: api/runs.py (creates Run row)
  → Mechanism: Database INSERT with status="queued"
  → Explicit: YES

TRANSPORT:
  → Type: Database polling (WorkerPool polls Run table)
  → Observable: YES (worker logs)
  → Failure Mode: Run stays queued, re-picked

ADAPTER:
  → Location: worker/pool.py:97-109 (_fetch_queued_runs)
  → Purpose: SQL query translates DB state to Run objects

CONSUMPTION:
  → Consumer: worker/runner.py (RunRunner._execute)
  → Explicit: YES
  → Dependency Declared: YES (via contract)

CONSEQUENCE:
  → What happens on success: Run status → "succeeded", Provenance created
  → What happens on failure: Run status → "failed" or "retry"
  → Observable: YES (run.completed event, DB state)
```

### Circuit: Budget Enforcement

```
SIGNAL: budget.loaded → budget.halt

INTENT:
  → Declared at: EXECUTION_SEMANTIC_CONTRACT.md (hard budget)
  → Statement: "Hard budget enforcement at choke points"

EMISSION:
  → Emitter: services/cost_write_service.py (defines budget)
  → Mechanism: Agent.budget_cents, Agent.spent_cents in DB
  → Explicit: YES

TRANSPORT:
  → Type: Database read (RunRunner loads from Agent table)
  → Observable: YES (budget_context_loaded log)
  → Failure Mode: Defaults to soft mode (no enforcement)

ADAPTER:
  → Location: worker/runner.py:83-124 (_load_budget_context)
  → Purpose: Translates Agent row to BudgetContext dataclass

CONSUMPTION:
  → Consumer: worker/runner.py:637-744 (hard budget check loop)
  → Explicit: YES
  → Dependency Declared: YES (comments reference Phase 5A)

CONSEQUENCE:
  → What happens on success: Run continues if under budget
  → What happens on failure: Run halted with run.halted event
  → Observable: YES (hard_budget_halt log)
```

---

## 6. Failure Classification

| Gap ID | Gap Description | Classification | Severity |
|--------|-----------------|----------------|----------|
| GAP-L4L5-001 | L5 RunRunner directly imports L4 planners/memory | BYPASSED_BOUNDARY | P1 |
| GAP-L4L5-002 | Auto-execute confidence threshold (0.8) hardcoded in L5 | IMPLICIT_SIGNAL | P2 |
| GAP-L4L5-003 | Category/recovery suggestion heuristics in L5 | IMPLICIT_SIGNAL | P2 |
| GAP-L4L5-004 | No CI check for L5→L4 import direction | MISSING_CONSUMER | P1 |
| GAP-L4L5-005 | Redundant budget check in L5 vs L4 | IMPLICIT_SIGNAL | P3 |

### Classification Evidence

**GAP-L4L5-001 (BYPASSED_BOUNDARY):**
```python
# worker/runner.py:379-384
from ..memory import get_retriever
from ..planners import get_planner
from ..skills import get_skill_manifest
```
L5 directly imports L4 modules. Contract says L5 should only import L6.

**GAP-L4L5-002 (IMPLICIT_SIGNAL):**
```python
# recovery_evaluator.py:~180
if confidence >= 0.8:  # Hardcoded threshold
```
Threshold is domain policy but lives in L5, not L4.

**GAP-L4L5-003 (IMPLICIT_SIGNAL):**
```python
# failure_aggregation.py:~120-140
if "timeout" in error_code.lower(): return "TRANSIENT"
if "429" in error_code: return "RATE_LIMITED"
```
Category detection is domain logic but lives in L5.

---

## 7. Risk Statement

```
RISK SUMMARY:
  - Circuit Status: PARTIAL
  - Gap Count: 5
  - Critical Gaps: GAP-L4L5-001 (L5→L4 direct imports), GAP-L4L5-004 (no CI)
  - Blocking for Phase 2: NO (documented, not blocking)
  - Human Action Required: YES (owner assignment for SIG-008, SIG-013)

RISK NARRATIVE:
  The L4↔L5 boundary is well-documented (L5_L4_SEMANTIC_MAPPING.md) and mostly closed.
  However, L5 directly imports L4 modules (planners, memory) which violates the declared
  layer dependency rule. This is not CI-enforced. The gap is known and documented but
  creates fragility if L4 modules change without considering L5 consumers.
```

---

## 8. Registry Entry

```yaml
boundary: L4↔L5
circuit_status: PARTIAL
signals_expected: 7
signals_found: 7
gaps:
  - id: GAP-L4L5-001
    type: BYPASSED_BOUNDARY
    severity: P1
    description: L5 RunRunner directly imports L4 planners/memory
  - id: GAP-L4L5-002
    type: IMPLICIT_SIGNAL
    severity: P2
    description: Auto-execute confidence threshold hardcoded in L5
  - id: GAP-L4L5-003
    type: IMPLICIT_SIGNAL
    severity: P2
    description: Category/recovery heuristics in L5 instead of L4
  - id: GAP-L4L5-004
    type: MISSING_CONSUMER
    severity: P1
    description: No CI check validates L5→L4 import direction
  - id: GAP-L4L5-005
    type: IMPLICIT_SIGNAL
    severity: P3
    description: Redundant budget check in L5 vs L4
enforcement:
  ci_coverage: PARTIAL
  blocking_workflow: integration-integrity.yml (SIG-005)
  advisory_workflow: m4-ci.yml (SIG-013), determinism-check.yml (SIG-008)
phase_1_complete: YES
phase_1_blocker: NONE (gaps documented, not blocking)
```

---

## 9. Hard Rules (Verification)

| Rule | Check | Status |
|------|-------|--------|
| Did I observe, not fix? | Documented gaps, did not modify code | YES |
| Did I document what IS, not what SHOULD BE? | Reality section reflects actual code | YES |
| Did I trace at least one full circuit? | 2 circuits traced (run execution, budget) | YES |
| Did I classify all gaps found? | 5 gaps classified with codes | YES |
| Did I note human-only signals? | No human-only signals found at this boundary | YES |
| Did I check both directions if bidirectional? | L4→L5 and L5→L4 both inspected | YES |

---

## 10. Completion Test

| Question | Can Answer? |
|----------|-------------|
| What signals cross this boundary? | YES (7 signals documented) |
| Where are they emitted? | YES (emitter locations in Reality section) |
| Where are they consumed? | YES (consumer locations in Reality section) |
| What happens if any signal is missing? | YES (failure modes documented per circuit) |
| Which gaps block Phase 2? | YES (NONE blocking, all documented) |

**Checklist Status: COMPLETE**

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| L5_L4_SEMANTIC_MAPPING.md | Detailed L5→L4 authority mapping (56 actions) |
| EXECUTION_SEMANTIC_CONTRACT.md | Execution guarantees contract |
| CI_SIGNAL_REGISTRY.md | CI signal inventory |
| SIG-005 (integration-integrity.yml) | LIT tests for layer seams |
| SIG-008 (determinism-check.yml) | Determinism verification |
| SIG-013 (m4-ci.yml) | Workflow engine CI |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Initial SCD for L4↔L5 boundary |
