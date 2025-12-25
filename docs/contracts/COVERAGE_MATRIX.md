# Contract Coverage Matrix

**Created:** 2025-12-25
**Purpose:** Verify all 13 ledger entries map to exactly one contract

---

## Complete Mapping

| # | Scenario | Ledger Entry | Surface | Gap | Contract | Obligation |
|---|----------|--------------|---------|-----|----------|------------|
| 1 | S1 | Pre-execution intent opaque | Intent | Opaque | PRE-RUN | stages + skill_sequence |
| 2 | S1 | Budget contradictory | Constraint | Contradictory | CONSTRAINT | budget_enforcement |
| 3 | S2 | CARE routing missing | Decision | Missing | DECISION | routing_occurred |
| 4 | S2 | routing_stability misleading | Decision | Misleading | DECISION | metric consistency |
| 5 | S3 | Recovery disconnected | Decision | Missing | DECISION | recovery_evaluated |
| 6 | S3 | recovery_log meaning opaque | Outcome | Opaque | OUTCOME | field semantics |
| 7 | S4 | Simulation contradicts execution | Constraint | Contradictory | CONSTRAINT | simulation-execution |
| 8 | S4 | Policy rules not queryable | Intent | Opaque | PRE-RUN | applicable_policies |
| 9 | S5 | Cost tables not populated | Outcome | Missing | OUTCOME | cost recording |
| 10 | S5 | Prometheus/Grafana undocumented | Outcome | Opaque | OUTCOME | observability surface |
| 11 | S5 | Ops console access missing | Outcome | Missing | OUTCOME | access paths |
| 12 | S6 | Memory injection invisible | Intent | Opaque | PRE-RUN | memory_injection_enabled |
| 13 | S6 | Memory fields missing | Decision | Missing | DECISION | memory_queried |

---

## Coverage Summary

| Contract | Entries Covered | Entry Numbers |
|----------|-----------------|---------------|
| PRE-RUN | 3 | 1, 8, 12 |
| CONSTRAINT | 2 | 2, 7 |
| DECISION | 4 | 3, 4, 5, 13 |
| OUTCOME | 4 | 6, 9, 10, 11 |
| **TOTAL** | **13** | All |

---

## Validation Checks

### Check 1: Every entry has exactly one contract

| Entry | Contracts Assigned | Valid |
|-------|-------------------|-------|
| 1 | PRE-RUN | ✓ |
| 2 | CONSTRAINT | ✓ |
| 3 | DECISION | ✓ |
| 4 | DECISION | ✓ |
| 5 | DECISION | ✓ |
| 6 | OUTCOME | ✓ |
| 7 | CONSTRAINT | ✓ |
| 8 | PRE-RUN | ✓ |
| 9 | OUTCOME | ✓ |
| 10 | OUTCOME | ✓ |
| 11 | OUTCOME | ✓ |
| 12 | PRE-RUN | ✓ |
| 13 | DECISION | ✓ |

**Result:** PASS - No entry maps to zero or multiple contracts.

### Check 2: No orphan contracts

| Contract | Has Entries | Valid |
|----------|-------------|-------|
| PRE-RUN | Yes (3) | ✓ |
| CONSTRAINT | Yes (2) | ✓ |
| DECISION | Yes (4) | ✓ |
| OUTCOME | Yes (4) | ✓ |

**Result:** PASS - All contracts have at least one mapped entry.

### Check 3: Gap type distribution

| Gap Type | Count | Contracts Affected |
|----------|-------|-------------------|
| Opaque | 6 | PRE-RUN (3), OUTCOME (2), DECISION (0), CONSTRAINT (0) |
| Missing | 5 | DECISION (3), OUTCOME (2), PRE-RUN (0), CONSTRAINT (0) |
| Contradictory | 2 | CONSTRAINT (2) |
| Misleading | 1 | DECISION (1) |

**Observation:** Opaque gaps concentrate in PRE-RUN and OUTCOME. Missing gaps concentrate in DECISION and OUTCOME. Contradictory gaps are exclusively CONSTRAINT.

---

## Contract Dependency Order (Confirmed)

```
PRE-RUN → CONSTRAINT → DECISION → OUTCOME
   ↓           ↓           ↓          ↓
 Intent    Limits      Choices    Results
```

This order is correct because:
1. Intent must be declared before constraints can be checked
2. Constraints must be known before decisions can be made
3. Decisions must be recorded before outcomes can be reconciled

---

## Phase 2 Status

**COMPLETE**

- 4 contracts drafted (skeletal)
- 13 ledger entries mapped
- 0 orphan entries
- 0 orphan contracts
- Coverage verified

---

## Phase 4A Amendment Validation

**Date:** 2025-12-25

### Amendment Applied

DECISION contract evolved from v0.1 to v0.2:
- Added: `decision_source` (human | system | hybrid)
- Added: `decision_trigger` (explicit | autonomous | reactive)

### Re-validation Results

| Check | Result |
|-------|--------|
| 13/13 ledger entries covered | PASS |
| 27/27 milestones covered | PASS |
| 0 new deltas | PASS |

### Why Coverage Is Preserved

1. Amendment only ADDED fields to DECISION contract
2. No existing obligations were removed or modified
3. The 4 DECISION ledger entries (3, 4, 5, 13) remain covered by original obligations
4. M10 and M14 now have their delta obligations formally incorporated

**Result:** Contract evolution successful. No coverage regression.
