# M0-M27 Contract Classification

**Created:** 2025-12-25
**Purpose:** Map each milestone to exactly one primary contract
**Mode:** Classification only. No fixes. No design.

---

## M0: Foundations & Contracts

```
Milestone: M0

Primary Contract:
  - PRE-RUN

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Declare deterministic seeds
  - Define structured outcome schema
  - Establish replay specification

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M1: Runtime & Execution Engine

```
Milestone: M1

Primary Contract:
  - DECISION

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Record execution path decisions
  - Surface heartbeat state
  - Record idempotency decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M2/M2.5: Skills Framework

```
Milestone: M2/M2.5

Primary Contract:
  - PRE-RUN

Secondary Contracts:
  - CONSTRAINT

Obligations Exercised:
  - Declare available skills (stages)
  - Declare typed I/O contracts
  - Declare planner abstraction

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M3/M3.5: Coordination & Messaging

```
Milestone: M3/M3.5

Primary Contract:
  - DECISION

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Record agent coordination decisions
  - Record message routing decisions
  - Surface blackboard state outcomes

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M4: Workflow Engine

```
Milestone: M4

Primary Contract:
  - PRE-RUN

Secondary Contracts:
  - CONSTRAINT
  - DECISION

Obligations Exercised:
  - Declare DAG structure (stages)
  - Declare dependency constraints
  - Record compensation decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M5: Policy API

```
Milestone: M5

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Declare policy constraints (hard/soft)
  - Surface audit log outcomes

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M6/M6.5: Feature Flags & Controls

```
Milestone: M6/M6.5

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - DECISION

Obligations Exercised:
  - Declare feature gate constraints
  - Record toggle decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M7: Memory & Observability

```
Milestone: M7

Primary Contract:
  - DECISION

Secondary Contracts:
  - OUTCOME
  - CONSTRAINT

Obligations Exercised:
  - Record memory injection decisions
  - Surface trace outcomes
  - Declare RBAC constraints

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M8: Externalization (SDK + Demo)

```
Milestone: M8

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - PRE-RUN

Obligations Exercised:
  - Declare rate limit constraints
  - Declare auth requirements
  - Declare SDK capabilities upfront

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M9: Failure Catalog & Matching

```
Milestone: M9

Primary Contract:
  - OUTCOME

Secondary Contracts:
  - DECISION

Obligations Exercised:
  - Surface failure outcomes (decomposed)
  - Record pattern matching decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M10: Recovery Suggestion Engine

```
Milestone: M10

Primary Contract:
  - DECISION

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Record recovery suggestion decisions
  - Record confidence scoring decisions
  - Surface approval outcomes

Does this introduce a NEW obligation?
  - YES

If Yes:
  - Which contract must evolve: DECISION
  - Why existing obligations are insufficient:
    Current DECISION contract requires recording "who decided" but does not
    distinguish decision_source (human | system | hybrid). Recovery engine
    introduces human-in-loop approval which needs explicit sourcing.
```

---

## M11: Skill Expansion & Reliability

```
Milestone: M11

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - PRE-RUN

Obligations Exercised:
  - Declare circuit breaker constraints
  - Declare skill availability (stages)
  - Declare idempotency requirements

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M12/M12.1: Multi-Agent System

```
Milestone: M12/M12.1

Primary Contract:
  - DECISION

Secondary Contracts:
  - CONSTRAINT

Obligations Exercised:
  - Record agent selection decisions
  - Record parallel execution decisions
  - Declare credit constraints

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M13: Cost Optimization

```
Milestone: M13

Primary Contract:
  - OUTCOME

Secondary Contracts:
  - CONSTRAINT

Obligations Exercised:
  - Surface spend attribution outcomes
  - Declare cost optimization constraints

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M14: Self-Improving Loop

```
Milestone: M14

Primary Contract:
  - DECISION

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Record learning decisions
  - Record drift detection decisions
  - Surface drift outcomes

Does this introduce a NEW obligation?
  - YES

If Yes:
  - Which contract must evolve: DECISION
  - Why existing obligations are insufficient:
    Current DECISION contract requires recording decisions but does not
    distinguish autonomous vs directed decisions. Self-improving loop makes
    decisions without explicit trigger. Need decision_trigger field.
```

---

## M15-M16: SBA (Spawn-time Blocking Agent)

```
Milestone: M15-M16

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - DECISION

Obligations Exercised:
  - Declare spawn blocking constraints
  - Record spawn validation decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M17: CARE Routing

```
Milestone: M17

Primary Contract:
  - DECISION

Secondary Contracts:
  - PRE-RUN

Obligations Exercised:
  - Record routing decisions (5-stage pipeline)
  - Record agent rejection decisions
  - Declare capability requirements upfront

Does this introduce a NEW obligation?
  - No

Note: This is the key invisible system from ledger entry S2.
Existing DECISION contract obligations COVER this if enforced.
The gap was enforcement, not obligation definition.
```

---

## M18: CARE-L + Evolution

```
Milestone: M18

Primary Contract:
  - DECISION

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Record evolution decisions
  - Record reputation adjustment decisions
  - Surface reputation outcomes

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M19: Policy Layer

```
Milestone: M19

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - DECISION

Obligations Exercised:
  - Declare constitutional governance constraints
  - Record policy evaluation decisions
  - Declare violation consequences

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M20: Policy Compiler

```
Milestone: M20

Primary Contract:
  - PRE-RUN

Secondary Contracts:
  - CONSTRAINT

Obligations Exercised:
  - Declare compiled policies upfront
  - Declare deterministic evaluation guarantees

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M21: Tenant, Auth & Billing

```
Milestone: M21

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Declare tenant isolation constraints
  - Declare auth requirements
  - Declare billing limits
  - Surface billing outcomes

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
Note: Tenant router currently disabled (intentional beta constraint).
```

---

## M22: KillSwitch

```
Milestone: M22

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - DECISION

Obligations Exercised:
  - Declare killswitch as HARD constraint
  - Record killswitch activation decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M23: Guard Console

```
Milestone: M23

Primary Contract:
  - OUTCOME

Secondary Contracts:
  - DECISION

Obligations Exercised:
  - Surface guard monitoring outcomes
  - Record guard intervention decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M24: Ops Console

```
Milestone: M24

Primary Contract:
  - OUTCOME

Secondary Contracts:
  - (all - console surfaces all truth surfaces)

Obligations Exercised:
  - Surface operational outcomes
  - Surface customer visibility
  - Surface infrastructure state

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
Note: Console is visualization of existing contracts.
```

---

## M25: Integration Loop

```
Milestone: M25

Primary Contract:
  - DECISION

Secondary Contracts:
  - OUTCOME

Obligations Exercised:
  - Record incident → prevention decisions
  - Record graduation decisions
  - Surface loop outcomes

Does this introduce a NEW obligation?
  - No

Note: Initially considered for "meta-decision" obligation,
but existing DECISION contract covers feedback loop decisions
if decision_source and decision_trigger fields are added (from M10, M14).
```

---

## M26: Cost Intelligence

```
Milestone: M26

Primary Contract:
  - OUTCOME

Secondary Contracts:
  - PRE-RUN

Obligations Exercised:
  - Surface cost analysis outcomes
  - Declare cost predictions upfront

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## M27: Cost Loop

```
Milestone: M27

Primary Contract:
  - CONSTRAINT

Secondary Contracts:
  - DECISION

Obligations Exercised:
  - Declare cost guard constraints
  - Record cost intervention decisions

Does this introduce a NEW obligation?
  - No

Existing obligations cover this milestone.
```

---

## Classification Summary

| Milestone | Primary | Secondary | New Obligation? |
|-----------|---------|-----------|-----------------|
| M0 | PRE-RUN | OUTCOME | No |
| M1 | DECISION | OUTCOME | No |
| M2/M2.5 | PRE-RUN | CONSTRAINT | No |
| M3/M3.5 | DECISION | OUTCOME | No |
| M4 | PRE-RUN | CONSTRAINT, DECISION | No |
| M5 | CONSTRAINT | OUTCOME | No |
| M6/M6.5 | CONSTRAINT | DECISION | No |
| M7 | DECISION | OUTCOME, CONSTRAINT | No |
| M8 | CONSTRAINT | PRE-RUN | No |
| M9 | OUTCOME | DECISION | No |
| M10 | DECISION | OUTCOME | **YES** |
| M11 | CONSTRAINT | PRE-RUN | No |
| M12/M12.1 | DECISION | CONSTRAINT | No |
| M13 | OUTCOME | CONSTRAINT | No |
| M14 | DECISION | OUTCOME | **YES** |
| M15-M16 | CONSTRAINT | DECISION | No |
| M17 | DECISION | PRE-RUN | No |
| M18 | DECISION | OUTCOME | No |
| M19 | CONSTRAINT | DECISION | No |
| M20 | PRE-RUN | CONSTRAINT | No |
| M21 | CONSTRAINT | OUTCOME | No |
| M22 | CONSTRAINT | DECISION | No |
| M23 | OUTCOME | DECISION | No |
| M24 | OUTCOME | All | No |
| M25 | DECISION | OUTCOME | No |
| M26 | OUTCOME | PRE-RUN | No |
| M27 | CONSTRAINT | DECISION | No |

---

## Contract Distribution

| Contract | Primary Count | Milestones |
|----------|---------------|------------|
| PRE-RUN | 4 | M0, M2/M2.5, M4, M20 |
| CONSTRAINT | 9 | M5, M6/M6.5, M8, M11, M15-M16, M19, M21, M22, M27 |
| DECISION | 9 | M1, M3/M3.5, M7, M10, M12, M14, M17, M18, M25 |
| OUTCOME | 5 | M9, M13, M23, M24, M26 |

---

## New Obligations Identified

| Milestone | Contract | Proposed Obligation | Status |
|-----------|----------|---------------------|--------|
| M10 | DECISION | decision_source: human \| system \| hybrid | INCORPORATED (v0.2) |
| M14 | DECISION | decision_trigger: explicit \| autonomous \| reactive | INCORPORATED (v0.2) |

**Total new obligations: 2 → 0 outstanding (both incorporated)**
**Consecutive milestones without new obligation: M15 → M27 (13 milestones)**

---

## Phase 3 Completion Status

- All M0-M27 mapped: ✓
- Delta list stabilized: ✓ (13 consecutive milestones with no new obligations)
- Ready for OBLIGATION_DELTAS.md: ✓

---

## Phase 4A Validation

**Date:** 2025-12-25

After DECISION contract evolution to v0.2:

| Check | Before | After | Result |
|-------|--------|-------|--------|
| M10 new obligation | YES | NO (incorporated) | PASS |
| M14 new obligation | YES | NO (incorporated) | PASS |
| Outstanding deltas | 2 | 0 | PASS |
| Milestones covered | 27/27 | 27/27 | PASS |

All milestones now map cleanly to existing obligations.
