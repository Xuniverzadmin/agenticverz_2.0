# PRE-RUN CONTRACT

> **FROZEN:** This contract is locked as of `contracts-stable-v1` (2025-12-25).
> No modifications without delta proposal and founder review.

**Version:** 0.1
**Created:** 2025-12-25
**Status:** FROZEN - Phase 4 complete

---

## Question This Contract Answers

> **What must the system declare before execution starts?**

---

## Core Obligation

**Execution MUST NOT begin unless this contract is acknowledged.**

A run request is invalid if the caller cannot observe:
1. What will happen
2. What constraints apply
3. What context is injected

---

## Required Declarations (Before Execution)

### 1. Execution Intent

| Field | Obligation |
|-------|------------|
| stages | MUST list all stages that will execute |
| skill_sequence | MUST declare which skills will be invoked |
| estimated_tokens | MUST provide token estimate before start |

### 2. Memory State

| Field | Obligation |
|-------|------------|
| memory_injection_enabled | MUST declare if memory will be injected |
| memory_context_summary | IF injection enabled, MUST summarize what will be injected |
| memory_sources | MUST list sources (pins, prior runs, none) |

### 3. Policy Applicability

| Field | Obligation |
|-------|------------|
| applicable_policies | MUST list policies that will be evaluated |
| policy_severity_levels | MUST declare which severities block vs warn |

---

## Mandatory vs Optional

| Declaration | Status |
|-------------|--------|
| stages | MANDATORY |
| skill_sequence | MANDATORY |
| estimated_tokens | MANDATORY |
| memory_injection_enabled | MANDATORY |
| memory_context_summary | MANDATORY if injection enabled |
| applicable_policies | MANDATORY |

---

## Acknowledgment Requirement

The caller MUST receive and acknowledge the pre-run declaration before execution begins.

Acknowledgment means:
- Declaration was delivered
- Caller can form hypothesis about outcome
- No silent starts

---

## What This Contract Does NOT Specify

- API shape
- UI representation
- How estimates are computed
- Storage format

Those are implementation. This is obligation.

---

## Ledger Entries This Contract Addresses

| Entry | Surface | Gap | How Contract Addresses |
|-------|---------|-----|------------------------|
| S1: Pre-execution intent opaque | Intent | Opaque | stages + skill_sequence mandatory |
| S4: Policy rules not queryable | Intent | Opaque | applicable_policies mandatory |
| S6: Memory injection invisible | Intent | Opaque | memory_injection_enabled + summary mandatory |

---

## Contract Violation

If execution begins without delivering these declarations:
- The run is **contract-violating**
- Outcomes cannot be reconciled
- Trust is undefined
