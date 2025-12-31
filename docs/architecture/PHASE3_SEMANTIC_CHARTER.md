# Phase 3 Semantic Charter

**Status:** PROPOSED (v2 — 4-Axis Model)
**Date:** 2025-12-30
**Authority:** PIN-251 (Phase 3 Semantic Alignment)
**Predecessor:** PIN-250 (Structural Truth Extraction Lifecycle)

---

## Purpose

This charter defines **what Phase 3 will decide** and **what it will not touch**.

Phase 3 is where meaning is decided.
Only after meaning is stable does product make sense.

**Core Question:**
> "What does the system *mean* when it runs?"

---

## Ladder Context

```
STRUCTURE  ██████████  DONE — Phase 1 (truth map)
TRUTH      ██████████  DONE — Phase 2A (foundation)
ALIGNMENT  ██████████  DONE — Phase 2B (34 writes extracted)
CI SIGNALS █████░░░░░  DISCOVERED — 6 signals, 3 promoted
SEMANTICS  ░░░░░░░░░░  NOT STARTED ◄── THIS PHASE
PRODUCT    ░░░░░░░░░░  BLOCKED UNTIL SEMANTICS COMPLETE
```

---

## The 4-Axis Semantic Model

Phase 3 uses a **4-axis semantic model** to classify every executable file:

```
                ↑
                │  Y — Cross-Layer Semantics
                │     (meaning transfer, authority shift)
                │
                │
                │
                │
                └──────────────→ X — In-Layer Semantics
                     (role meaning inside a layer)

Z — Execution / Time Semantics (async, sync, lifecycle)
⊙ — State & Authority Semantics (who owns truth)
```

### Axis Definitions

| Axis | Question | Purpose |
|------|----------|---------|
| **X** | What does this file mean *inside* its layer? | Prevents role ambiguity |
| **Y** | What semantic responsibility is transferred across layers? | Prevents authority leakage |
| **Z** | When and how does this code run? | Prevents temporal bugs |
| **⊙** | What state does this file have the right to mutate or observe? | Prevents state corruption |

---

### X-Axis — In-Layer Semantic Role

> "What does this file mean *inside* its layer?"

| Layer | Example Roles |
|-------|---------------|
| L2 (API) | Orchestration, Routing, Request Handling |
| L3 (Boundary) | Verification, Translation, Adaptation |
| L4 (Domain) | Authority, Policy, Business Logic |
| L5 (Execution) | Executor, Scheduler, Worker |
| L6 (Platform) | Storage, Cache, External Service |

Every file must have **one primary X-role**.

---

### Y-Axis — Cross-Layer Semantic Contract

> "What semantic responsibility is transferred across layers?"

| Transfer | Meaning |
|----------|---------|
| L2→L3 | Request becomes verification context |
| L3→L4 | Verified identity becomes authority context |
| L4→L5 | Decision becomes execution intent |
| L5→L4 | Execution result becomes state mutation |
| L4→L6 | Authority becomes persistence |

This axis prevents policy leaks and authority confusion.

---

### Z-Axis — Execution & Temporal Semantics

> "When and how does this code run?"

| Value | Meaning |
|-------|---------|
| import-time | Executes when module is imported |
| request-time | Executes per HTTP request |
| async-task | Executes as background task |
| background-worker | Long-running background process |
| scheduled | Executes on schedule (cron, timer) |
| retryable | Can be safely retried |
| idempotent | Multiple executions = same result |
| compensating | Undoes previous action |

Without Z, async/sync problems reappear silently.

---

### ⊙ Axis — State & Authority Semantics

> "What state does this file have the right to mutate or observe?"

| Value | Meaning |
|-------|---------|
| State Authority | May mutate truth (DB writes) |
| State Observer | Read-only access |
| State Relay | Passes context without mutation |
| Stateless | No state interaction |

This is where transaction ownership lives.

---

## Phase 3 Desired Outcome

> **Every executable file in the codebase is classified across four semantic axes (X, Y, Z, ⊙), with no unknowns.
> Unknown semantics are allowed only if explicitly tagged and justified.**

---

## Required Artifact: SEMANTIC_COORDINATE_MAP.md

Phase 3 must produce a complete map:

| File | Layer | X: In-Layer Role | Y: Cross-Layer Contract | Z: Execution | ⊙: State Authority | Status |
|------|-------|------------------|-------------------------|--------------|--------------------| -------|
| api/auth.py | L3 | Verification | L3→L4 Auth Context | request-time | Stateless | In scope |
| services/user_write_service.py | L4 | Authority | L4→DB Mutation | sync | State Authority | In scope |
| workers/recovery.py | L5 | Executor | L5→L4 State Repair | async | State Authority | In scope |
| utils/time.py | L6 | Utility | None | import-time | Stateless | Semantically Neutral |

### Status Values

| Status | Meaning |
|--------|---------|
| In scope | Must be resolved in Phase 3 |
| Deferred | Explicitly tied to Phase 4+ with reason |
| Semantically Neutral | Utility/glue, justified |
| **BLOCKING** | Cannot proceed until classified |

**No file may remain BLOCKING.**

---

### Semantically Neutral Invariant (MANDATORY)

> **Semantically Neutral files MUST satisfy ALL of the following:**
>
> 1. Do not mutate domain or platform state
> 2. Do not encode policy or decision logic
> 3. Do not initiate execution flows
> 4. Are pure utility, schema, or glue
>
> **Violation:** If a file violates any of these, it is NOT Semantically Neutral and must be reclassified as "In scope".

This invariant prevents "Semantically Neutral" from becoming a dumping ground.

---

### Deferred File Requirements (MANDATORY)

> **Deferred files MUST specify:**
>
> 1. **Target phase** (e.g., Phase 4, Phase 5)
> 2. **Reason** (e.g., deprecated path, external dependency, cleanup candidate)
>
> **Violation:** Unbounded deferral is forbidden. Every deferred file must have a resolution timeline.

This invariant prevents permanent limbo.

---

## Semantic Domains In Scope

Phase 3 owns **exactly these five domains**:

### Domain 1: Auth Semantics (L3 ↔ L4)

**Question:** What is *verification* vs *policy* vs *decision*?

| Concept | Semantic Question |
|---------|-------------------|
| Verification | Who confirms identity? Where does this happen? |
| Policy | What rules govern access? Who owns these rules? |
| Decision | When is access granted/denied? Who decides? |
| Enforcement | Where are decisions enforced? Who can override? |

**Why First:** Auth meaning leaks everywhere if wrong. Get this right first.

**Deliverable:** `AUTH_SEMANTIC_CONTRACT.md`

---

### Domain 2: Execution Model Semantics

**Question:** When is async *required* vs *optional*? What guarantees exist?

| Concept | Semantic Question |
|---------|-------------------|
| Async Boundary | When MUST execution be async? |
| Sync Authority | When is sync the authoritative path? |
| Ordering | What ordering guarantees exist? |
| Idempotency | What operations are idempotent? |
| Retry Semantics | What can be retried? What cannot? |

**Why Second:** After auth is clear, execution paths can be reasoned about.

**Deliverable:** `EXECUTION_MODEL_CONTRACT.md`

---

### Domain 3: Worker Lifecycle Semantics

**Question:** What does a worker *represent* in the system?

| Concept | Semantic Question |
|---------|-------------------|
| Worker Identity | What is a worker run? A unit of work? |
| Authoritative vs Best-Effort | When is a run authoritative? |
| Failure Meaning | What does failure mean? Retry? Abort? Record? |
| Completion Meaning | What does "done" mean? |
| Visibility | When is a worker visible to users? |

**Why Third:** Workers are the execution backbone. Semantics define boundaries.

**Deliverable:** `WORKER_LIFECYCLE_CONTRACT.md`

---

### Domain 4: Recovery & Consistency Semantics

**Question:** What is recovery allowed to overwrite?

| Concept | Semantic Question |
|---------|-------------------|
| Overwrite Authority | What can recovery modify? |
| Append-Only | What is immutable once written? |
| Compensating Action | What is compensating vs corrective? |
| Consistency Model | What consistency guarantees exist? |
| Truth Priority | When conflicts occur, what wins? |

**Why Fourth:** Recovery touches all prior domains. Needs auth, execution, worker clarity first.

**Deliverable:** `RECOVERY_CONSISTENCY_CONTRACT.md`

---

### Domain 5: Transaction Authority Semantics

**Question:** Which layer owns transaction boundaries?

| Concept | Semantic Question |
|---------|-------------------|
| Commit Ownership | Who can commit? L2? L4? Both? |
| Nested Writes | When are nested writes allowed? |
| Rollback Authority | Who can rollback? |
| Eventual Consistency | When is it acceptable? |
| Failure Propagation | How do failures propagate? |

**Why Fifth:** This is the integration layer. Needs all prior semantics defined.

**Deliverable:** `TRANSACTION_AUTHORITY_CONTRACT.md`

---

## Explicit Non-Goals

Phase 3 does **NOT** do the following:

| Non-Goal | Reason |
|----------|--------|
| AI Console work | Product, not semantics |
| UI/UX changes | Product, not semantics |
| New features | Product, not semantics |
| Performance optimization | Optimization, not semantics |
| CI hard gates | CI measures semantics; doesn't define them |
| Code refactoring for style | Style, not semantics |
| Cosmetic naming (planner/planners) | Deferred to Phase 4 |
| Business experiments | Product, not semantics |

---

## Order of Resolution (Fixed)

Phase 3 is **sequential**, not parallel.

| Order | Phase | Domain | Duration Estimate |
|-------|-------|--------|-------------------|
| 1 | 3.1 | Auth Semantics | Discovery + Contract |
| 2 | 3.2 | Execution Model Semantics | Discovery + Contract |
| 3 | 3.3 | Worker Lifecycle Semantics | Discovery + Contract |
| 4 | 3.4 | Recovery & Consistency Semantics | Discovery + Contract |
| 5 | 3.5 | Transaction Authority Semantics | Discovery + Contract |

**No parallel execution.** Each domain builds on the previous.

---

## Completion Criteria

Phase 3 is complete when:

### Per-Domain Completion

| Domain | Completion Criteria |
|--------|---------------------|
| Auth Semantics | Contract produced, reviewed, accepted |
| Execution Model | Contract produced, reviewed, accepted |
| Worker Lifecycle | Contract produced, reviewed, accepted |
| Recovery & Consistency | Contract produced, reviewed, accepted |
| Transaction Authority | Contract produced, reviewed, accepted |

### Phase-Level Completion

1. All 5 semantic contracts exist
2. All contracts are reviewed and accepted
3. No semantic ambiguity remains in scope
4. CI signals can now be refined with semantic backing
5. Phase 3 Completion Gate signed

---

## Product Unlock Conditions

Product work (AI Console, features, UX) is **blocked** until:

1. All 5 semantic domains are resolved
2. Phase 3 Completion Gate is signed
3. Human explicitly unlocks product work

**No exceptions.** Partial semantic alignment does not unlock product.

---

## Governance Rules

This charter requires the following governance rules:

**ARCH-GOV-012: Semantic Alignment Gate**

```yaml
ARCH-GOV-012:
  name: Semantic Alignment Gate
  purpose: Ensure semantic meaning is defined before product work
  status: BLOCKING
  rule: |
    Product work is forbidden until Phase 3 (Semantic Alignment) is formally complete.
    No AI Console, features, UX, or business experiments until all semantic contracts are accepted.
  unlock_conditions:
    - All 5 semantic contracts accepted
    - SEMANTIC_COORDINATE_MAP.md complete (no BLOCKING files)
    - Phase 3 Completion Gate signed
    - Human explicit unlock
```

**ARCH-GOV-013: Semantic Coordinate Requirement**

```yaml
ARCH-GOV-013:
  name: Semantic Coordinate Requirement
  purpose: Ensure every executable file has explicit semantic classification
  status: BLOCKING
  rule: |
    Every executable file must be classified along four semantic axes
    (In-Layer, Cross-Layer, Execution, State Authority)
    before Phase 3 may be declared complete.
  axes:
    X: In-Layer Semantic Role
    Y: Cross-Layer Semantic Contract
    Z: Execution / Temporal Semantics
    ⊙: State & Authority Semantics
  allowed_unknowns:
    - Semantically Neutral (justified)
    - Deferred (with reason)
  blocking_unknowns:
    - Any file with unknown semantics on any axis
```

---

## What This Charter Does NOT Do

- ❌ Define semantic answers (Phase 3 execution does that)
- ❌ Change any code
- ❌ Add CI checks
- ❌ Fix any issues
- ❌ Enable product work

This charter **only** defines scope, order, and completion criteria.

---

## Per-Phase Workflow

Each Phase 3.x follows this workflow:

```
1. DISCOVERY
   - Read existing code for domain
   - Document current implicit semantics
   - Identify ambiguities and conflicts

2. PROPOSAL
   - Propose semantic definitions
   - Document alternatives considered
   - Await human review

3. CONTRACT
   - Produce semantic contract
   - Contract is governance-level
   - Await acceptance

4. COMPLETION
   - Mark phase complete
   - Update PIN-251
   - Proceed to next phase
```

---

## Entry Approval

This charter requires human approval before Phase 3.1 begins.

**Approval Checklist:**

- [ ] Semantic domains in scope are correct
- [ ] Order of resolution is correct
- [ ] Non-goals are correctly excluded
- [ ] Completion criteria are sufficient
- [ ] Product unlock conditions are acceptable
- [ ] ARCH-GOV-012 rule is approved

---

## Next Steps (For Human Review)

1. Review this charter
2. Confirm scope, order, and completion criteria
3. Approve or revise
4. Upon approval, Phase 3.1 (Auth Semantics) begins

---

## References

- PIN-250: Structural Truth Extraction Lifecycle
- PIN-251: Phase 3 Semantic Alignment
- PHASE2_COMPLETION_GATE.md: Structural guarantees
- CI_CANDIDATE_MATRIX.md: Why semantics matter for CI
