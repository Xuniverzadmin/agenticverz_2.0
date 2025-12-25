# DECISION RECORD CONTRACT

> **FROZEN:** This contract is locked as of `contracts-stable-v1` (2025-12-25).
> No modifications without delta proposal and founder review.

**Version:** 0.2
**Created:** 2025-12-25
**Amended:** 2025-12-25
**Status:** FROZEN - Phase 4 complete (includes decision_source/trigger deltas)

---

## Question This Contract Answers

> **What decisions must be surfaced when the system chooses a path?**

---

## Core Obligation

**When the system makes a decision, evidence of that decision MUST be recorded.**

Silence is not allowed. If no decision occurred, that MUST be stated explicitly.

---

## Decision Metadata (MANDATORY for all decisions)

Every decision record MUST include these two fields:

### decision_source

| Value | Meaning |
|-------|---------|
| human | Decision authority originated from human actor |
| system | Decision made autonomously by system |
| hybrid | System suggested, human approved |

**Origin:** M10 (Recovery Suggestion Engine) - Human-in-loop approval workflow

### decision_trigger

| Value | Meaning |
|-------|---------|
| explicit | Decision triggered by direct request |
| autonomous | Decision triggered by internal system logic |
| reactive | Decision triggered by external event |

**Origin:** M14 (Self-Improving Loop) - Autonomous learning decisions

---

## Decision Types (Exhaustive List)

### 1. Routing Decisions

| Field | Obligation |
|-------|------------|
| routing_occurred | MUST be true or false (never null) |
| routing_method | IF occurred, MUST state method (CARE, direct, fallback) |
| agents_considered | IF occurred, MUST list agents evaluated |
| agents_rejected | IF any rejected, MUST list with rejection reason |
| agent_selected | IF occurred, MUST identify selected agent |

**Forbidden:** `routing_decisions: []` when routing occurred internally.

### 2. Recovery Decisions

| Field | Obligation |
|-------|------------|
| recovery_evaluated | MUST be true or false (never null) |
| recovery_triggered | IF evaluated, MUST state if recovery was triggered |
| recovery_action | IF triggered, MUST state action taken |
| recovery_source | IF triggered, MUST identify rule or heuristic used |

**Forbidden:** `recovery_log: []` when recovery was evaluated but not triggered.

### 3. Memory Injection Decisions

| Field | Obligation |
|-------|------------|
| memory_queried | MUST be true or false (never null) |
| memory_matched | IF queried, MUST state if matches found |
| memory_injected | IF matched, MUST state what was injected |
| memory_sources | IF injected, MUST list source pins/runs |

**Forbidden:** Claiming memory injection is enabled but providing no evidence.

---

## The "No Decision" Obligation

If a decision point exists but no decision was made:

| Scenario | Required Record |
|----------|-----------------|
| Routing not needed | `routing_occurred: false, reason: "direct_execution"` |
| Recovery not evaluated | `recovery_evaluated: false, reason: "success_path"` |
| Memory not queried | `memory_queried: false, reason: "injection_disabled"` |

**Forbidden:** Null fields. Empty arrays with no explanation.

---

## Metric Consistency

If a metric implies activity, the decision record MUST confirm it:

| Metric | Decision Record Requirement |
|--------|----------------------------|
| routing_stability: 1.0 | routing_occurred MUST be true |
| routing_stability: N/A | routing_occurred MUST be false |

**Forbidden:** Metrics that imply activity when no decision occurred.

---

## What This Contract Does NOT Specify

- How decisions are made (algorithms)
- Where decisions are stored
- How to display decisions
- Decision optimization

Those are implementation. This is obligation.

---

## Ledger Entries This Contract Addresses

| Entry | Surface | Gap | How Contract Addresses |
|-------|---------|-----|------------------------|
| S2: CARE routing missing | Decision | Missing | routing_occurred + agents_considered mandatory |
| S2: routing_stability misleading | Decision | Misleading | Metric consistency rule |
| S3: Recovery disconnected | Decision | Missing | recovery_evaluated mandatory in workflow |
| S6: Memory fields missing | Decision | Missing | memory_queried + memory_injected mandatory |

---

## Contract Violation

If a decision occurred but was not recorded:
- The run is **contract-violating**
- Outcomes cannot be explained
- Debugging is impossible
