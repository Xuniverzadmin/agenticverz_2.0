# Part-2 Enforcement Index

**Status:** ACTIVE
**Effective:** 2026-01-04
**Reference:** part2-design-v1

---

## Purpose

This index maps Part-2 closure gates to their mechanical enforcement.

Enforcement exists to make violations **impossible by construction**,
not just detectable after the fact.

---

## Gate → Guard Mapping

| Gate | Risk | Guard | Type |
|------|------|-------|------|
| GATE-1 | Jobs without contracts | `part2_workflow_structure_guard.py` | Static |
| GATE-2 | UI mutates system | `part2_authority_boundary_guard.py` | Static |
| GATE-3 | Mutable contracts | `part2_workflow_structure_guard.py` | Static |
| GATE-4 | Override eligibility | Bootstrap + Test | Runtime |
| GATE-5 | Jobs bypass governance | `part2_authority_boundary_guard.py` | Static |
| GATE-6 | Manipulate health | `part2_health_supremacy_guard.py` | Static |
| GATE-7 | Rollout without audit | Test contract | Semantic |
| GATE-8 | Unaudited customer view | Test contract | Semantic |
| GATE-9 | Silent execution | Test contract | Semantic |
| GATE-10 | Design drift | `part2_design_freeze_guard.py` | Static |

---

## Static Guards (CI)

### part2_design_freeze_guard.py

**Purpose:** Prevent Part-2 design document modification

**Enforces:** GATE-10

**Frozen Files:**
- `PART2_CRM_WORKFLOW_CHARTER.md`
- `SYSTEM_CONTRACT_OBJECT.md`
- `ELIGIBILITY_RULES.md`
- `VALIDATOR_LOGIC.md`
- `GOVERNANCE_JOB_MODEL.md`
- `FOUNDER_REVIEW_SEMANTICS.md`
- `GOVERNANCE_AUDIT_MODEL.md`
- `END_TO_END_STATE_MACHINE.md`
- `PART2_CLOSURE_CRITERIA.md`
- `PART2_CLOSURE_NOTE.md`
- `INDEX.md`

**Run:** `python scripts/ci/part2_design_freeze_guard.py`

---

### part2_authority_boundary_guard.py

**Purpose:** Enforce import boundaries for authority separation

**Enforces:** GATE-2, GATE-5

**Boundaries:**
- UI/API cannot import governance execution
- Governance jobs cannot import CRM/UI
- Part-2 modules cannot write health directly

**Run:** `python scripts/ci/part2_authority_boundary_guard.py`

---

### part2_workflow_structure_guard.py

**Purpose:** Ensure workflow structure matches design

**Enforces:** GATE-1, GATE-3

**Checks:**
- Contract model has required fields
- Contract model has required states
- Job model references contract_id
- No contract mutation post-APPROVED

**Run:** `python scripts/ci/part2_workflow_structure_guard.py`

---

### part2_health_supremacy_guard.py

**Purpose:** Extend Phase-1 health supremacy to Part-2

**Enforces:** GATE-6

**Checks:**
- Part-2 modules do not write GovernanceSignal
- Only authorized modules write health
- Health read patterns are allowed

**Run:** `python scripts/ci/part2_health_supremacy_guard.py`

---

## Bootstrap Guards (Runtime)

*To be implemented when implementation begins*

### Contract Activation Guard

**Purpose:** Refuse to activate contracts without eligibility proof

**Enforces:** GATE-4

**Check:** `contract.eligibility_verdict.decision == MAY`

---

### Job Start Guard

**Purpose:** Refuse to start jobs for non-ACTIVE contracts

**Enforces:** GATE-1, GATE-5

**Check:** `contract.status == ACTIVE`

---

## Test Contracts (Semantic)

*To be implemented when implementation begins*

### Audit Rollout Contract

**Purpose:** No rollout without audit PASS

**Enforces:** GATE-7

**Test:** Reject rollout if `audit.verdict != PASS`

---

### Customer View Contract

**Purpose:** Customers see only ROLLED_OUT states

**Enforces:** GATE-8

**Test:** Customer API filters by rollout status

---

### Evidence Contract

**Purpose:** Terminal states emit evidence

**Enforces:** GATE-9

**Test:** COMPLETED/FAILED contracts have evidence records

---

## CI Workflow Integration

Add to `.github/workflows/governance.yml`:

```yaml
part2-enforcement:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Need tags

    - name: Part-2 Design Freeze Guard
      run: python scripts/ci/part2_design_freeze_guard.py

    - name: Part-2 Authority Boundary Guard
      run: python scripts/ci/part2_authority_boundary_guard.py

    - name: Part-2 Workflow Structure Guard
      run: python scripts/ci/part2_workflow_structure_guard.py

    - name: Part-2 Health Supremacy Guard
      run: python scripts/ci/part2_health_supremacy_guard.py
```

---

## Enforcement Phases

### Phase 1: Static Guards (CURRENT)

- Design freeze ✓
- Import boundaries ✓
- Workflow structure ✓
- Health supremacy ✓

### Phase 2: Bootstrap Guards (FUTURE)

- Contract activation
- Job start authorization
- Eligibility proof

### Phase 3: Semantic Tests (FUTURE)

- State transition tests
- Audit rollout contract
- Customer view contract
- Evidence contract

---

## Attestation

This index documents enforcement for Part-2 closure gates.
All guards reference `part2-design-v1` as the authoritative source.
Enforcement is mechanical, not advisory.
