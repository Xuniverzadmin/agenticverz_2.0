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

| Gate | Risk | Guard | Type | Status |
|------|------|-------|------|--------|
| GATE-1 | Jobs without contracts | `part2_workflow_structure_guard.py` | Static | ✅ Pass 1 |
| GATE-2 | UI mutates system | `part2_authority_boundary_guard.py` | Static | ✅ Pass 1 |
| GATE-3 | Mutable contracts | `part2_workflow_structure_guard.py` | Static | ✅ Pass 1 |
| GATE-4 | Override eligibility | `part2_contract_activation_guard.py` | Bootstrap | ✅ Pass 2 |
| GATE-5 | Jobs bypass governance | `part2_job_start_guard.py` | Bootstrap | ✅ Pass 2 |
| GATE-6 | Manipulate health | `part2_health_supremacy_guard.py` | Static | ✅ Pass 1 |
| GATE-7 | Rollout without audit | `part2_semantic_contracts.py` | Semantic | ✅ Pass 2 |
| GATE-8 | Unaudited customer view | `part2_semantic_contracts.py` | Semantic | ✅ Pass 2 |
| GATE-9 | Silent execution | `part2_semantic_contracts.py` | Semantic | ✅ Pass 2 |
| GATE-10 | Design drift | `part2_design_freeze_guard.py` | Static | ✅ Pass 1 |

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

## Bootstrap Guards (Runtime) — Pass 2

### part2_contract_activation_guard.py

**Purpose:** Refuse to activate contracts without eligibility proof

**Enforces:** GATE-4

**Prerequisites:**
- `eligibility_verdict.decision == MAY`
- `approved_by IS NOT NULL`
- `approved_at IS NOT NULL`
- `NOW() >= activation_window_start`

**Bypass patterns detected:**
- Direct ACTIVE assignment without eligibility check
- Force/bypass functions
- Explicit bypass comments

**Run:** `python scripts/ci/part2_contract_activation_guard.py`

---

### part2_job_start_guard.py

**Purpose:** Refuse to start jobs for non-ACTIVE contracts

**Enforces:** GATE-5

**Prerequisites:**
- `job.contract_id IS NOT NULL`
- `contract.status == ACTIVE`
- `job.scope ⊆ contract.affected_capabilities`
- `system_health != UNHEALTHY`

**Bypass patterns detected:**
- Execution without contract check
- Job RUNNING without contract status check
- Orphan job creation

**Run:** `python scripts/ci/part2_job_start_guard.py`

---

## Semantic Contract Tests — Pass 2

### part2_semantic_contracts.py

**Purpose:** Define and verify behavioral contracts

**Enforces:** GATE-7, GATE-8, GATE-9

**Contracts defined:**

#### GATE-7: Rollout Requires Audit PASS

**Invariant:** `rollout_status = DEPLOYED` requires `audit.verdict == PASS`

**Violation:** Deployment occurs without audit PASS

---

#### GATE-8: Customer View Only COMPLETED

**Invariant:** Customer APIs only return contracts with `status == COMPLETED`

**Violation:** Customer sees DRAFT, ACTIVE, or any intermediate state

---

#### GATE-9: Terminal States Emit Evidence

**Invariant:** COMPLETED/FAILED contracts must have evidence records

**Violation:** Terminal state without evidence (silent execution)

**Run:** `python scripts/ci/part2_semantic_contracts.py`

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

    # Pass 1: Static Guards
    - name: Part-2 Design Freeze Guard
      run: python scripts/ci/part2_design_freeze_guard.py

    - name: Part-2 Authority Boundary Guard
      run: python scripts/ci/part2_authority_boundary_guard.py

    - name: Part-2 Workflow Structure Guard
      run: python scripts/ci/part2_workflow_structure_guard.py

    - name: Part-2 Health Supremacy Guard
      run: python scripts/ci/part2_health_supremacy_guard.py

    # Pass 2: Bootstrap Guards
    - name: Part-2 Contract Activation Guard
      run: python scripts/ci/part2_contract_activation_guard.py

    - name: Part-2 Job Start Guard
      run: python scripts/ci/part2_job_start_guard.py

    # Pass 2: Semantic Contracts
    - name: Part-2 Semantic Contracts
      run: python scripts/ci/part2_semantic_contracts.py
```

---

## Enforcement Phases

### Pass 1: Static Guards ✅ COMPLETE

- Design freeze ✅
- Import boundaries ✅
- Workflow structure ✅
- Health supremacy ✅

### Pass 2: Bootstrap + Semantic ✅ COMPLETE

- Contract activation guard ✅
- Job start guard ✅
- Audit rollout contract ✅
- Customer view contract ✅
- Evidence contract ✅

### Implementation Phase: UNLOCKED

With Pass 1 and Pass 2 complete, implementation may begin:
- CRM Event Schema (L8)
- Contract models
- Governance services
- Founder review UI

All implementation must satisfy the guards defined above.

---

## Attestation

This index documents enforcement for Part-2 closure gates.
All guards reference `part2-design-v1` as the authoritative source.
Enforcement is mechanical, not advisory.
