# PIN-395: SDSR Scenario Taxonomy and Capability Court of Law

**Status:** ✅ COMPLETE
**Created:** 2026-01-11
**Category:** SDSR / System Design
**Milestone:** Phase G Steady State

---

## Summary

Formalized SDSR from ad-hoc E2E tests into a complete system-truth exhaust with 13 scenario classes, capability coverage matrix, and concrete execution plan.

---

## Details

## Overview

Generalized SDSR from "a few E2E tests" into a **full system-truth exhaust** — a capability court of law where:

- **SDSR = Evidence** (observations of real system behavior)
- **Aurora = Belief System** (capability status based on evidence)
- **UI = Sentence Execution** (buttons enabled/disabled based on beliefs)

## Core Principle (Non-Negotiable)

> **Only the stimulus is synthetic. All effects, errors, traces, policies, incidents, logs, and side-effects must be REAL.**

## Scenario Taxonomy (13 Classes)

### I. Execution Outcome Scenarios
| Class | ID Pattern | Purpose |
|-------|------------|---------|
| 1. SUCCESSFUL_EXECUTION | SDSR-EXEC-SUCCESS-* | Clean path validation |
| 2. FAILED_EXECUTION | SDSR-EXEC-FAIL-* | Hard failure handling |
| 3. PARTIAL_SUCCESS | SDSR-EXEC-PARTIAL-* | Degraded execution |

### II. Threshold & Violation Scenarios
| Class | ID Pattern | Purpose |
|-------|------------|---------|
| 4. NEAR_VIOLATION | SDSR-THRESH-NEAR-* | Proves selectivity (NO buttons unlock) |
| 5. THRESHOLD_BREACH | SDSR-THRESH-BREACH-* | Incident triggers |
| 6. AUTO_POLICY_ACTION | SDSR-THRESH-AUTO-* | Automated policy responses |

### III. Policy Lifecycle Scenarios
| Class | ID Pattern | Purpose |
|-------|------------|---------|
| 7. HUMAN_APPROVAL | SDSR-POL-APPROVE-* | APPROVE capability |
| 8. HUMAN_REJECTION | SDSR-POL-REJECT-* | REJECT capability |
| 9. POLICY_ACTIVATION | SDSR-POL-ACTIVATE-* | ACTIVATE/DEACTIVATE |

### IV. Traceability & Audit Scenarios
| Class | ID Pattern | Purpose |
|-------|------------|---------|
| 10. FULL_TRACE_CHAIN | SDSR-TRACE-FULL-* | Correlation validation |
| 11. TRACE_GAP_DETECTION | SDSR-TRACE-GAP-* | Detect blind spots |

### V. Actor Differentiation Scenarios
| Class | ID Pattern | Purpose |
|-------|------------|---------|
| 12. HUMAN_ACTION_PATH | SDSR-ACTOR-HUMAN-* | Human audit trail |
| 13. AGENT_ACTION_PATH | SDSR-ACTOR-AGENT-* | Agent audit trail |

## Capability Coverage Matrix

### Current State
| Status | Count |
|--------|-------|
| OBSERVED | 2 (APPROVE, REJECT) |
| DISCOVERED | 8 (pending proof) |

### Capability → Scenario Mapping
| Capability | Required Scenario Class | Priority |
|------------|------------------------|----------|
| ACKNOWLEDGE | THRESHOLD_BREACH | P1 |
| RESOLVE | THRESHOLD_BREACH | P1 |
| ADD_NOTE | FAILED_EXECUTION | P2 |
| ACTIVATE | POLICY_ACTIVATION | P3 |
| DEACTIVATE | POLICY_ACTIVATION | P3 |
| UPDATE_* | POLICY_ACTIVATION | P4 |

## Execution Plan

### Immediate Actions
1. **Run SDSR-E2E-003** → ACKNOWLEDGE, ADD_NOTE
2. **Run SDSR-E2E-005** → Trace validation
3. **Create + Run SDSR-POL-ACTIVATE-001** → ACTIVATE, DEACTIVATE
4. **Create + Run SDSR-THRESH-NEAR-001** → Selectivity proof

### End State Target
- All 8 DISCOVERED capabilities → OBSERVED
- All 5 DRAFT panels → BOUND

## Artifacts Created

| Artifact | Location |
|----------|----------|
| Scenario Taxonomy | `docs/governance/SDSR_SCENARIO_TAXONOMY.md` |
| Coverage Matrix | `docs/governance/SDSR_CAPABILITY_COVERAGE_MATRIX.md` |
| Execution Plan | `docs/governance/SDSR_EXECUTION_PLAN.md` |

## Key Insight

> What you're building is **not an LLM evaluation system**.
> It's a **capability court of law**.

Most teams never get past belief.
This system proves guilt or innocence with artifacts.

---

## Related PINs

- [PIN-370](PIN-370-.md)
- [PIN-379](PIN-379-.md)
- [PIN-394](PIN-394-.md)
