# CONSTRAINT DECLARATION CONTRACT

> **FROZEN:** This contract is locked as of `contracts-stable-v1` (2025-12-25).
> No modifications without delta proposal and founder review.

**Version:** 0.1
**Created:** 2025-12-25
**Status:** FROZEN - Phase 4 complete

---

## Question This Contract Answers

> **What constraints apply, and how are they enforced?**

---

## Core Obligation

**Every constraint MUST be classified as HARD or SOFT before execution.**

A constraint without enforcement classification is undefined behavior.

---

## Constraint Classification (Mandatory)

### HARD Constraints

| Property | Definition |
|----------|------------|
| Behavior | Execution STOPS if violated |
| Timing | Checked BEFORE and DURING execution |
| Override | Cannot be overridden by caller |
| Example | Rate limit exceeded, authentication failed |

### SOFT Constraints (Advisory)

| Property | Definition |
|----------|------------|
| Behavior | Execution CONTINUES with warning |
| Timing | Checked BEFORE and AFTER execution |
| Override | Caller can acknowledge and proceed |
| Example | Budget exceeded (if declared advisory) |

---

## Required Declarations

### 1. Budget Constraint

| Field | Obligation |
|-------|------------|
| budget_amount | MUST declare budget value |
| budget_enforcement | MUST declare: HARD or SOFT |
| budget_unit | MUST declare unit (tokens, cents, calls) |

If `budget_enforcement = HARD`:
- Execution MUST STOP when budget exhausted
- No "advisory only" behavior

If `budget_enforcement = SOFT`:
- System MUST declare this upfront
- Caller knows budget is advisory
- No surprise overruns

### 2. Policy Constraint

| Field | Obligation |
|-------|------------|
| policy_id | MUST identify which policy |
| policy_enforcement | MUST declare: HARD or SOFT |
| violation_consequence | MUST declare what happens on violation |

### 3. Rate Limit Constraint

| Field | Obligation |
|-------|------------|
| rate_limit_type | MUST declare type (http_call, llm_invoke, etc.) |
| rate_limit_enforcement | ALWAYS HARD (no soft rate limits) |
| remaining | MUST declare remaining before execution |

---

## Simulation-Execution Consistency

**Obligation:** If simulation declares `feasible: false`, execution behavior MUST be defined.

| Simulation Result | Required Behavior |
|-------------------|-------------------|
| feasible: true | Execution may proceed |
| feasible: false, constraint: HARD | Execution MUST NOT proceed |
| feasible: false, constraint: SOFT | Execution MAY proceed with acknowledgment |

**Forbidden:** Simulation warns, execution ignores silently.

---

## What This Contract Does NOT Specify

- How constraints are computed
- UI for constraint display
- Storage format
- Constraint creation workflow

Those are implementation. This is obligation.

---

## Ledger Entries This Contract Addresses

| Entry | Surface | Gap | How Contract Addresses |
|-------|---------|-----|------------------------|
| S1: Budget contradictory | Constraint | Contradictory | budget_enforcement MUST be declared |
| S4: Simulation contradicts execution | Constraint | Contradictory | Simulation-Execution consistency rule |

---

## Contract Violation

If a constraint is enforced differently than declared:
- The run is **contract-violating**
- Trust is broken
- No "it's just advisory" excuses after the fact
