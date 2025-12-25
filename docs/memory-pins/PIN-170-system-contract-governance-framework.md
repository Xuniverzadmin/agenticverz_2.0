## Overview

This PIN documents the establishment of a formal contract-based governance framework for AOS. The framework emerged from systematic analysis of visibility gaps identified in PIN-167 human testing.

## Problem Statement

PIN-167 human testing revealed that AOS capabilities exist but are invisible to users:
- CARE routing works but decisions aren't surfaced
- Recovery engine has 50+ candidates but is disconnected from workflows
- Memory injection is enabled but effects are unobservable
- Budget constraints are advisory, not enforced
- Cost tables exist but aren't populated

**Root Cause:** Missing truth surfaces, not missing capability.

## Solution: Contract Governance Framework

### Phase 1: Scenario Extraction (COMPLETE)

Processed 6 scenarios from PIN-167 using strict observation contract:
- No fixes, no suggestions, no UI proposals
- Extract system truth only
- Classify by truth surface (Intent, Decision, Constraint, Outcome)

**Result:** 13 ledger entries in `docs/SYSTEM_TRUTH_LEDGER.md`

### Phase 2: Contract Drafting (COMPLETE)

Created 4 skeletal contracts in exact dependency order:

| Order | Contract | Question Answered |
|-------|----------|-------------------|
| 1 | PRE-RUN | What must the system declare before execution starts? |
| 2 | CONSTRAINT | What constraints apply, and how are they enforced? |
| 3 | DECISION | What decisions must be surfaced when the system chooses a path? |
| 4 | OUTCOME | How do we reconcile what happened with what was promised? |

**Coverage:** All 13 ledger entries mapped to exactly one contract.

### Phase 3: M0-M27 Classification (COMPLETE)

Classified all 27 milestones against contracts:

| Metric | Value |
|--------|-------|
| Milestones classified | 27 |
| Collapsed cleanly | 25 (93%) |
| New obligations | 2 (7%) |
| Stabilization | M15-M27 (13 consecutive) |

**New Obligations Identified:**
1. `decision_source`: human | system | hybrid (from M10)
2. `decision_trigger`: explicit | autonomous | reactive (from M14)

## Contract Files

```
docs/contracts/
├── INDEX.md                         # Contract index
├── PRE_RUN_CONTRACT.md              # 3 ledger entries
├── CONSTRAINT_DECLARATION_CONTRACT.md  # 2 ledger entries
├── DECISION_RECORD_CONTRACT.md      # 4 ledger entries
├── OUTCOME_RECONCILIATION_CONTRACT.md  # 4 ledger entries
├── COVERAGE_MATRIX.md               # Validation proof
├── M0_M27_CLASSIFICATION.md         # Milestone mapping
└── OBLIGATION_DELTAS.md             # Proposed evolutions
```

## Contract Gate Rule

Before any new scenario or feature:

```
1. Which contract does this exercise?
2. Which obligation does it test?
3. Is this a new obligation or an existing one?
```

If these cannot be answered, the work is rejected.

## Key Principle

> **No code, no UI, no refactor is allowed unless you can name the contract obligation it satisfies.**

## Phase 4 Preview

When implementation begins:
1. Evolve DECISION contract to include `decision_source` and `decision_trigger`
2. Implement contract obligations in API responses
3. Surface truth at each contract boundary
4. No fixes outside contract scope

## Related Documents

- `docs/SCENARIO_OBSERVATION_CONTRACT.md` - Observation rules
- `docs/SYSTEM_TRUTH_LEDGER.md` - 13 truth gap entries
- PIN-167 - Source scenarios (human testing)
- PIN-163 - M0-M28 Utilization Report
