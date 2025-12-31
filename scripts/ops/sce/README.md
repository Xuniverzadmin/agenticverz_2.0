# Signal Circuit Enumerator (SCE)

**Status:** NOT IMPLEMENTED - CONTRACT ONLY
**Version:** 1.0.0
**Date:** 2025-12-31
**Reference:** SESSION_PLAYBOOK.yaml Section 32, PIN-262

---

## What This Document Is

This is the **authoritative contract** for the Signal Circuit Enumerator worker.
The contract MUST be ratified and understood BEFORE any implementation begins.

**This contract cannot be changed without human ratification.**

---

## Worker Identity

| Field | Value |
|-------|-------|
| Name | `signal_circuit_enumerator` |
| Class | Forensic / Evidence Generator |
| Phase Eligibility | Phase 1 ONLY |
| Authority | READ-ONLY |
| CI Blocking | FORBIDDEN |

---

## Purpose (Narrow Scope)

The SCE worker exists to:

1. Statically enumerate *candidate* signal emitters, consumers, and boundary crossings
2. Compare **declared semantics (metadata)** with **observed mechanics (code reality)**
3. Produce **evidence** for Phase 1 Signal Circuit Discovery (SCD)

The SCE worker does **NOT**:

- Decide correctness
- Enforce governance
- Block CI
- Replace human SCD

---

## Blast Radius (ABSOLUTE LIMIT)

```
Zero behavioral impact.
Zero enforcement impact.
Zero runtime impact.

If this worker breaks, nothing else must break.
```

This is non-negotiable. If the worker cannot satisfy this constraint, it must not be deployed.

---

## Allowed Access (Exhaustive List)

| Surface | Access Level |
|---------|--------------|
| Source code | Read |
| Metadata annotations | Read |
| AST | Parse |
| Import graph | Build |
| Call graph (shallow) | Build |
| CI configs | Read |
| Docs (contracts/playbooks) | Read |

Any access not listed here is **FORBIDDEN**.

---

## Forbidden Actions (Absolute)

| Action | Status |
|--------|--------|
| Modify code | FORBIDDEN |
| Modify CI | FORBIDDEN |
| Enforce rules | FORBIDDEN |
| Block builds | FORBIDDEN |
| Rewrite metadata | FORBIDDEN |
| Assign ownership | FORBIDDEN |
| Infer intent beyond metadata | FORBIDDEN |

If the implementation violates ANY of these, it must be killed immediately.

---

## Metadata Contract

The worker assumes metadata exists in code in a machine-readable form:

```python
# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: ...
# Callers: ...
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-XXX
```

Or structured decorators/YAML where available.

**Critical Rule:** Metadata is treated as a **claim**, never as fact.

---

## Internal Passes (Deterministic)

### PASS 1 — Layer & Boundary Indexing

- Assign each file/module to a layer (from metadata or path heuristic)
- Build import graph
- Detect boundary crossings

**Emits:** `BOUNDARY_CROSSING_OBSERVED`

### PASS 2 — Semantic Claim Extraction

From metadata only:
- Declared layer
- Declared role
- Declared emits
- Declared consumes
- Declared boundary

**Emits:** `DECLARED_SIGNAL_EMIT`, `DECLARED_SIGNAL_CONSUME`

### PASS 3 — Mechanical Observation

From AST / call graph:
- Object construction resembling signal payloads
- Dispatch/enqueue calls
- Return-based control signaling
- Exception-based signaling
- Log-only signaling

**Emits:** `OBSERVED_SIGNAL_EMIT`, `OBSERVED_SIGNAL_CONSUME`, `IMPLICIT_SIGNAL_PATTERN`

### PASS 4 — Diff & Drift Detection

Compare Declared vs Observed.

**Detects:**
- Declared but not observed
- Observed but not declared
- Direction mismatch
- Boundary bypass
- Half-circuits

**Emits:** `SEMANTIC_DRIFT`, `BROKEN_CANDIDATE_CIRCUIT`

---

## Output Artifacts (Canonical)

### Raw Evidence File (Per Run)

**File:** `docs/ci/scd/evidence/SCE_RUN_<timestamp>.json`

**Mode:** APPEND-ONLY HISTORICAL EVIDENCE

**Contains:**
- All declared signals
- All observed signal-like patterns
- All boundary crossings
- No judgments

### Boundary Summary Files (Generated)

**Example:** `docs/ci/scd/SCE-L4-L5-EVIDENCE.md`

**Contains:**

| Item | Content |
|------|---------|
| Declared Signals | From metadata |
| Observed Signals | From mechanics |
| Missing | Declared − Observed |
| Extra | Observed − Declared |
| Implicit Patterns | Calls, returns, exceptions |
| Boundary Violations | Imports / calls |

No conclusions. No fixes.

### Registry Hints (Non-Authoritative)

**File:** `docs/ci/scd/SCE_REGISTRY_HINTS.md`

**Mode:** NON-AUTHORITATIVE

Suggested additions only:
- Candidate signals
- Candidate gaps
- Candidate drift

**These are NOT applied automatically.**

---

## Output Classification Rules

### Absolute Rule

> **Worker output is evidence, not truth.**

### How Humans Must Treat Outputs

| Output Type | Human Action |
|-------------|--------------|
| Declared ≠ Observed | Review in SCD |
| Observed ≠ Declared | Decide relevance |
| Boundary violation | Record gap |
| Implicit signal | Classify risk |
| Missing emission | Mark `MISSING_EMITTER` |

No worker output may:
- Close a circuit
- Declare correctness
- Advance a phase

---

## Explicit Non-Goals

The worker does **NOT**:

- Prove signals fire
- Prove signals are complete
- Prove correctness
- Replace SCD
- Replace CI

If anyone uses it that way, they are **violating governance**.

---

## Sanity Test

Before deployment, ask:

> "If the worker produces zero output, does governance still function?"

- If **YES** → scope is correct
- If **NO** → worker is too powerful, kill it

---

## Governance Tasks (Recorded)

### TASK-GOV-010

Create and ratify **Signal Circuit Enumerator Contract**

- Evidence-only
- No enforcement
- Phase-1-only

**Status:** THIS DOCUMENT

### TASK-GOV-011

Add rule to SESSION_PLAYBOOK:

> "Automated signal enumeration output must never be treated as proof. Human SCD ratification is required."

**Status:** RECORDED in SESSION_PLAYBOOK.yaml v2.25 Section 32

---

## Implementation Checklist (For Future Developer)

Before writing any code, verify:

- [ ] This contract has been read and understood
- [ ] Blast radius constraint is satisfied
- [ ] No forbidden actions are possible in design
- [ ] Output is evidence-only by construction
- [ ] CI blocking is architecturally impossible
- [ ] Human ratification is required for any action

If any checkbox is unclear, STOP and ask for clarification.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| SESSION_PLAYBOOK.yaml Section 32 | Canonical governance block |
| PIN-262 | SCD governance clarification |
| docs/ci/scd/INDEX.md | SCD index and status |
| docs/ci/CI_SIGNAL_REGISTRY.md | CI signal inventory |
| docs/contracts/PRODUCT_DEVELOPMENT_CONTRACT_V3.md | Phase definitions |

---

## Bottom Line

This worker will:
- Expose blind spots
- Surface semantic lies
- Accelerate SCD
- Reduce human fatigue

It will **NOT**:
- Make the system safer by itself
- Replace discipline
- Give certainty

That's exactly the balance required.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Initial contract created |
