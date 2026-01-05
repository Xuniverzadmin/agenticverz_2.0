# PIN-296: Part-2 Rollout Projection - Read-Only Final Layer

**Status:** COMPLETE
**Created:** 2026-01-04
**Category:** Governance / Part-2 Implementation
**Milestone:** Part-2 CRM Workflow System

---

## Summary

Implemented the Rollout Projection Service - the **final layer** of Part-2 governance. This is a read-only projection layer that derives rollout views from governance state. It is "a lens, not a lever" - it has no execution, approval, or mutation authority.

---

## Key Design Decisions

### 1. Projection is Read-Only

The Rollout Projection Service is intentionally constrained:
- **Read**: Contract state, execution results, audit verdicts
- **Derive**: Rollout views, completion reports, customer stages
- **Write**: Nothing. Zero mutations.

```
Governance State ──► PROJECTION ──► FounderRolloutView
                                └──► CustomerRolloutView
                                └──► GovernanceCompletionReport
```

### 2. A Lens, Not a Lever

| Authority | Rollout Projection Has It? |
|-----------|---------------------------|
| Execution | NO |
| Approval | NO |
| Override | NO |
| Mutation | NO |
| Projection | YES (read-only) |

### 3. Founder vs Customer Views

**FounderRolloutView** (Full Lineage):
- Complete traceability: Issue → Contract → Approval → Execution → Audit → Rollout
- Includes issue_ids, contract_id, contract_state, approval details
- Shows execution_summary, audit_summary
- Full rollout_plan with all stages
- Has lineage_complete flag for verification

**CustomerRolloutView** (Facts Only):
- Capability name and current stage
- Visible features (what's live)
- Generic timeline (no internal details)
- Customers see FACTS, never intent

### 4. Completion Report Generation

GovernanceCompletionReport is generated ONLY when:
- `audit_verdict == PASS`

If audit failed or is inconclusive, no completion report is generated.

```python
def generate_completion_report(self, ...) -> Optional[GovernanceCompletionReport]:
    if audit_verdict != AuditVerdict.PASS:
        return None  # No report for failed/inconclusive audits
    # ... generate report
```

### 5. Rollout Stages (Monotonic)

```python
class RolloutStage(str, Enum):
    NOT_VISIBLE = "not_visible"  # Customer doesn't know it exists
    PLANNED = "planned"          # Announced, not available
    INTERNAL = "internal"        # Internal testing only
    LIMITED = "limited"          # Limited rollout (beta)
    GENERAL = "general"          # General availability
```

Stage order is monotonic: stages can only advance forward, never regress without a new contract.

### 6. Stabilization Windows

Before advancing to the next stage, the system must wait for a stabilization window:
- `minimum_duration_hours`: Minimum time at current stage
- `health_threshold`: Required health score to advance
- `required_metrics`: Specific metrics that must pass

```python
@dataclass(frozen=True)
class StabilizationWindow:
    minimum_duration_hours: int
    health_threshold: float
    required_metrics: frozenset[str]
```

### 7. Blast Radius

Each rollout stage has a defined blast radius:

```python
@dataclass(frozen=True)
class BlastRadius:
    stage: RolloutStage
    affected_customers: int      # Count or estimate
    affected_percentage: float   # 0.0 to 100.0
    geographic_scope: str        # e.g., "region-us-east"
    tier_scope: str              # e.g., "enterprise", "all"
```

---

## Six Core Invariants (ROLLOUT-001 to ROLLOUT-006)

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| ROLLOUT-001 | Projection has no mutation authority | Pure functions, frozen dataclasses |
| ROLLOUT-002 | Founder view requires complete lineage | lineage_complete check |
| ROLLOUT-003 | Customer view shows facts only | No internal details exposed |
| ROLLOUT-004 | Completion report requires PASS verdict | Conditional generation |
| ROLLOUT-005 | Stages are monotonic | can_advance_stage validation |
| ROLLOUT-006 | Stabilization gates advancement | Window duration check |

---

## What Rollout Projection IS

| Property | Description |
|----------|-------------|
| Lens | Derives views from governance state |
| Read-Only | Zero mutations to any state |
| Derived | All data computed from existing state |
| Transparent | Full lineage for founders |
| Fact-Based | Customers see reality, not plans |

## What Rollout Projection IS NOT

| Property | Description |
|----------|-------------|
| Executor | Cannot execute anything |
| Approver | Cannot approve anything |
| Override | Cannot override verdicts |
| State Machine | Has no state of its own |
| Decision Maker | Reflects decisions, doesn't make them |

---

## Components Implemented

### 1. Rollout Projection Service

`backend/app/services/governance/rollout_projection.py` (~550 lines)

**Data Types:**
- `RolloutStage` - Enum: NOT_VISIBLE, PLANNED, INTERNAL, LIMITED, GENERAL
- `BlastRadius` - Impact scope for each stage
- `StabilizationWindow` - Gating requirements for advancement
- `RolloutPlan` - Complete plan with stages and windows
- `ContractSummary` - Contract details for views
- `ExecutionSummary` - Execution details for views
- `AuditSummary` - Audit details for views
- `FounderRolloutView` - Full lineage view for founders
- `CustomerRolloutView` - Facts-only view for customers
- `GovernanceCompletionReport` - Machine-generated on PASS

**Service Class:**
- `RolloutProjectionService` - Main projection service

**Helpers:**
- `founder_view_to_dict()` - Convert view to dict
- `completion_report_to_dict()` - Convert report to dict

### 2. Invariant Tests

`backend/tests/governance/test_rollout_projection_invariants.py` (~600 lines)

36 tests covering:
- ROLLOUT-001: No mutation authority
- ROLLOUT-002: Complete lineage required
- ROLLOUT-003: Customer facts only
- ROLLOUT-004: Completion requires PASS
- ROLLOUT-005: Monotonic stages
- ROLLOUT-006: Stabilization gates

---

## Files Created

```
backend/app/services/governance/rollout_projection.py (~550 lines)
  - RolloutProjectionService
  - Data types: RolloutStage, BlastRadius, StabilizationWindow, RolloutPlan
  - Views: FounderRolloutView, CustomerRolloutView
  - Report: GovernanceCompletionReport
  - Helpers: founder_view_to_dict, completion_report_to_dict

backend/tests/governance/test_rollout_projection_invariants.py (~600 lines)
  - 36 invariant tests
  - ROLLOUT-001 to ROLLOUT-006 coverage
  - Stage advancement tests
  - Stabilization tests
```

**Updated:**
```
backend/app/services/governance/__init__.py (added exports, marked Part-2 COMPLETE)
```

**Total:** ~1,150 lines (implementation + tests)

---

## Test Coverage

36 invariant tests covering:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestROLLOUT001NoMutationAuthority | 5 | Pure functions, frozen types |
| TestROLLOUT002CompleteLineageRequired | 4 | Lineage verification |
| TestROLLOUT003CustomerFactsOnly | 4 | No internal details |
| TestROLLOUT004CompletionRequiresPASS | 4 | Conditional report |
| TestROLLOUT005MonotonicStages | 5 | Stage ordering |
| TestROLLOUT006StabilizationGates | 4 | Window enforcement |
| TestBlastRadius | 3 | Impact scope |
| TestStabilizationWindow | 3 | Window validation |
| TestRolloutProjectionIntegration | 4 | Full flow |

All 36 tests passing.

---

## Combined Governance Tests

```
322 tests passing (31 validator + 48 eligibility + 43 contract + 51 orchestrator + 38 founder review + 33 executor + 42 audit + 36 rollout)
```

---

## Authority Chain (COMPLETE)

```
CRM Event (no authority)
    ↓
Validator (machine, advisory) [PIN-288]
    ↓
Eligibility (machine, deterministic gate) [PIN-289]
    ↓
Contract (machine, state authority) [PIN-291]
    ↓
Founder Review (human, approval authority) [PIN-293]
    ↓
Governance Orchestrator (machine, coordination) [PIN-292]
    ↓
Job Executor (machine, execution authority) [PIN-294]
    ↓
Audit Service (machine, verification authority) [PIN-295]
    ↓
Rollout Projection (machine, read-only projection) [PIN-296] ← THIS PIN

*** PART-2 COMPLETE ***
```

---

## Stage Advancement Logic

```python
def can_advance_stage(
    self,
    current_stage: RolloutStage,
    target_stage: RolloutStage,
    audit_verdict: AuditVerdict,
    stabilization_complete: bool,
    health_degraded: bool
) -> tuple[bool, str]:
    # Must have PASS verdict
    if audit_verdict != AuditVerdict.PASS:
        return False, "Audit verdict must be PASS"

    # Cannot advance if health degraded
    if health_degraded:
        return False, "Health degraded, cannot advance"

    # Cannot regress stages
    if STAGE_ORDER[target_stage] <= STAGE_ORDER[current_stage]:
        return False, "Cannot regress stages"

    # Must complete stabilization
    if not stabilization_complete:
        return False, "Stabilization window not complete"

    return True, "Advancement authorized"
```

---

## Part-2 Governance Complete

### Final Metrics

| Component | Tests | Lines | PIN |
|-----------|-------|-------|-----|
| Validator | 31 | ~400 | PIN-288 |
| Eligibility | 48 | ~600 | PIN-289 |
| Contract | 43 | ~600 | PIN-291 |
| Orchestrator | 51 | ~550 | PIN-292 |
| Founder Review | 38 | ~640 | PIN-293 |
| Job Executor | 33 | ~400 | PIN-294 |
| Audit Service | 42 | ~550 | PIN-295 |
| **Rollout Projection** | **36** | **~550** | **PIN-296** |
| **Total** | **322** | **~4,290** | - |

### Part-2 Design Principles Honored

1. **Authority is explicit** - Each layer has defined authority boundaries
2. **State changes require contracts** - No unilateral mutations
3. **Human approval gates machine execution** - Founder review is mandatory
4. **Audit is terminal** - Verdicts cannot be overridden
5. **Projection is read-only** - No mutation authority in final layer
6. **Lineage is preserved** - Full traceability from event to rollout

---

## References

- Tag: `part2-design-v1`
- GOVERNANCE_AUDIT_MODEL.md
- PIN-284: Part-2 Design Documentation
- PIN-287: CRM Event Schema
- PIN-288: Validator Service
- PIN-289: Eligibility Engine
- PIN-291: Contract Model
- PIN-292: Governance Services
- PIN-293: Founder Review
- PIN-294: Job Executor
- PIN-295: Audit Wiring
- PART2_CRM_WORKFLOW_CHARTER.md

---

## Related PINs

- [PIN-288](PIN-288-part-2-validator-service---pure-analysis-implementation.md)
- [PIN-289](PIN-289-part-2-eligibility-engine---pure-rules-implementation.md)
- [PIN-291](PIN-291-part-2-contract-model---first-stateful-governance-component.md)
- [PIN-292](PIN-292-part-2-governance-services---workflow-orchestration.md)
- [PIN-293](PIN-293-part-2-founder-review---last-human-authority-gate.md)
- [PIN-294](PIN-294-part-2-job-executor---machine-execution-layer.md)
- [PIN-295](PIN-295-part-2-audit-wiring---verification-layer.md)

---

## Part-2 Closure Statement

With PIN-296 complete, the Part-2 CRM Workflow Governance System is fully implemented:

- **8 components** spanning L4-L8 layers
- **322 invariant tests** ensuring correctness
- **~4,290 lines** of governance code
- **Full authority chain** from CRM event to rollout projection

The system enforces:
- Explicit contracts for all state changes
- Human approval before machine execution
- Terminal audit verdicts
- Read-only projection for visibility

**Part-2 Status: COMPLETE**
