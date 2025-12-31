# PIN-256: Raw Architecture Extraction Exercise

**Status:** ACTIVE
**Created:** 2025-12-31
**Category:** Governance / Architecture / Evidence-Based
**Reference:** PIN-254, PIN-255, SESSION_PLAYBOOK.yaml v2.19 Section 29
**Predecessor:** PIN-254 (Layered Semantic Completion — COMPLETE)

---

## Purpose

Track the raw architecture extraction exercise from evidence to truthful structure. This PIN remains ACTIVE until the exercise is complete.

**Core Principle:** Extract structure from evidence, not design from theory.

---

## Method Correction Applied

User-mandated method correction (2025-12-31):

> "You are NOT drawing an architecture diagram — you are excavating an archaeology site."
>
> **Correct order:**
> 1. Changes → Phases guide (anchors in operational reality)
> 2. Raw structure discovery (nodes from code, edges from imports)
> 3. Review: what's missing? what surprised us? what's implicit?
> 4. ONLY THEN: grouping, layering, diagrams

**Forbidden until review complete:**
- Layer names
- Boxes
- Mermaid diagrams
- Design from theory

---

## Artifacts Produced

### Phase 1: Operational Anchor (COMPLETE)

| Artifact | Location | Status |
|----------|----------|--------|
| CHANGES_TO_PHASES_GUIDE.md | `docs/governance/` | COMPLETE |

Maps 18 change types to required phases. Evidence-based, not theoretical.

### Phase 2: Raw Structure Extraction (COMPLETE → REFINED)

| Artifact | Location | Content | Status |
|----------|----------|---------|--------|
| RAW_ARCHITECTURE_NODES.md | `docs/governance/` | 112 nodes (v2) | REFINED |
| RAW_ARCHITECTURE_EDGES.md | `docs/governance/` | ~137 edges (v2) | REFINED |

**v2 Refinements Applied:**
1. Entry Points split into containers (12) + transactions (52)
2. External nodes expanded from 4 to 9 concrete systems
3. Scheduler nodes annotated with trigger semantics
4. Observer edges differentiated (telemetry vs governance control)

**Node Categories (v2):**
- Actors: 3
- Entry Containers: 12
- Transactional Entries: 52
- Domain Engines: 5
- Services: 8
- Workers: 6
- Adapters: 4
- External Systems: 9
- Stores: 6
- Schedulers: 3
- Observers: 4

**Edge Types (v2):**
- Actor → Entry Container: 9
- Container → Transaction: 52 (hosting)
- Transaction → Processor: 15+
- Processor → Processor: 13
- Processor → Store: 16
- Processor → External: 17
- Telemetry Edges: 6
- Governance Control Edges: 5
- Scheduler Edges: 4

### Phase 3: Review Questions (COMPLETE)

User review answered all questions:

| Question | Status | Findings |
|----------|--------|----------|
| What's missing? | COMPLETE | Nothing required for correctness. Optional: L1 intent ledger, L4→L7 domain readiness signal |
| What surprised us? | COMPLETE | Many hard authority actions at L2 (killswitches, freezes). Clean frontend authority avoidance. Controlled external WRITE blast radius. |
| What coupling is implicit? | COMPLETE | L7↔L4 via shared state (governed). External READ influencing engines indirectly (modeled). |

### Phase 4: ASCII Diagram (COMPLETE)

| Artifact | Location | Status |
|----------|----------|--------|
| RAW_ARCHITECTURE_DIAGRAM.md | `docs/governance/` | COMPLETE |

Diagram derived mechanically from nodes/edges v2:
- No layering applied
- Authority edges marked with `[!]`
- WRITE edges marked with `>>>`
- 5 hard-stop transactions identified
- Governance control vs telemetry observers differentiated

### Phase 5: Layered Structure (BLOCKED)

Diagramming complete. Layer projection **BLOCKED** until Phase E closure.

### Phase E: Semantic Closure & Promotion Enforcement (ACTIVE)

| Artifact | Location | Status |
|----------|----------|--------|
| PHASE_E_VIOLATIONS.md | `docs/governance/` | E-1 COMPLETE |

**E-1: Violation Discovery — COMPLETE**

Systematic scan of raw architecture against layer import rules.

| Violations Found | Patterns | Constraint Met |
|------------------|----------|----------------|
| 10 | 4 | YES |

**Violation Summary:**

| ID | Type | Source → Target |
|----|------|-----------------|
| VIOLATION-001 | L5 → L4 | Schedulers → Domain Engines |
| VIOLATION-002 | L5 → L4 | Workers → Domain Engines |
| VIOLATION-003 | L2 → L5 | API → Worker |
| VIOLATION-004 | L7 → L4 | BLCA → Domain (implicit) |
| VIOLATION-005 | L7 → L5 | CI → Execution (implicit) |
| VIOLATION-006 | No L4 Gate | TIME trigger without domain readiness |
| VIOLATION-007 | L6 → ? | External READ interpretation unclear |
| VIOLATION-008 | L6 = L4? | Service making domain decisions |
| VIOLATION-009 | L3 → L4 → L6 | Adapter orchestrating decisions |
| VIOLATION-010 | L6 → L4 | Implicit state coupling |

**Patterns Identified:**
- Pattern A: Inverted Control Flow (L5/L2 calling L4)
- Pattern B: Implicit Governance Influence (L7 → L4/L5)
- Pattern C: Orphan Authority (decisions without layer ownership)
- Pattern D: Semantic Interpretation Drift (external data → decisions)

**E-2: Fix Design — COMPLETE**

| Artifact | Location | Status |
|----------|----------|--------|
| PHASE_E_FIX_DESIGN.md | `docs/governance/` | E-2 COMPLETE |

**Root Cause Mapping:**

| Root Cause | Violations | Fix |
|------------|------------|-----|
| RC-1: Domain logic in L5 | 001, 002, 006 | FIX-01: Reclassify orchestrators to L4 |
| RC-2: L5 importing L4 | 002, 003 | FIX-02: Pre-computed authorization |
| RC-3: Implicit governance | 004, 005 | FIX-03: Governance signal persistence |
| RC-4: Interpretation drift | 007-010 | FIX-04: Interpretation ownership |

**Fix Summary:**
- 4 fixes for 10 violations (minimal)
- 2 new L6 artifacts (governance_signals, interpretation metadata)
- 6 file reclassifications (domain orchestrators)
- No behavior change, no new authority

**E-3 to E-5: PENDING RATIFICATION**

---

## Evidence Sources

All extraction derived from:

| Source | What It Provides |
|--------|------------------|
| Import statements | Edge connections |
| Phase A findings (SHADOW-001 to SHADOW-003) | L5 → L4 delegation paths |
| Phase B findings (B01-B05) | L3 → L4 delegation paths |
| Phase C findings (C01-C05) | API truthfulness evidence |
| Phase D findings (32 F1 entry points) | Frontend → API mapping |
| File system structure | Node existence |
| Function signatures | Caller relationships |

---

## Implicit Coupling (Known from User's Mental Map)

User-provided coupling concerns to investigate:

| Coupling | Current Status | Risk |
|----------|---------------|------|
| L7 → L4 feedback via L6 state | Implicit | Not broken; could add DomainReadinessSignal |
| L4 → L2 explanation gap | Acceptable | BLCA will catch drift |
| L1 → L4 (bypassing L2/L3) | Unknown | Need to verify no direct calls |
| L5 → L3 (worker using adapter) | Unknown | Need to verify translation purity |

---

## Completion Criteria

This PIN moves to COMPLETE when:

1. ~~Phase 3 review questions answered~~ ✓
2. ~~Implicit coupling documented~~ ✓
3. ~~Decision made on whether to proceed to layered diagrams~~ BLOCKED by Phase E
4. **Phase E complete:**
   - E-1: Violation discovery ✓
   - E-2: Fix proposals for each violation (PENDING)
   - E-3: Fixes applied (PENDING)
   - E-4: Re-extraction and BLCA re-audit (PENDING)
   - E-5: Governance ratification (PENDING)
5. Only then: layered structure preserves all extracted edges

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-254 | Predecessor (Phase A-D completion) |
| PIN-255 | Sibling (CI integration strategy, PENDING) |
| PIN-248 | Reference (Codebase Inventory & Layer System) |
| PIN-245 | Reference (Integration Integrity System) |

---

## Session Log

### 2025-12-31: Phase E-2 Fix Design Complete

E-1 ratified. Proceeded to E-2 with constraints:
- Design minimal promotion mechanisms
- Group by root cause, not violation ID
- Eliminate by construction, not annotation

**Root Cause Analysis:**
- 10 violations collapsed into 4 root causes
- RC-1: Domain logic misplaced in execution layer
- RC-2: Execution importing domain directly
- RC-3: Governance influence without formal signals
- RC-4: Semantic interpretation without ownership

**Fixes Designed:**

| Fix | Mechanism | Violations Resolved |
|-----|-----------|---------------------|
| FIX-01 | Reclassify domain orchestrators L5 → L4 | 001, 002 (partial), 006 |
| FIX-02 | Pre-computed authorization in L6 | 002 (remaining), 003 |
| FIX-03 | governance_signals table in L6 | 004, 005 |
| FIX-04 | interpretation_owner metadata | 007, 008, 009, 010 |

**Artifacts introduced:**
- 2 new L6 constructs (governance_signals, interpretation metadata)
- 6 file reclassifications (orchestrators to L4)
- No behavior change, no new authority

Created: `docs/governance/PHASE_E_FIX_DESIGN.md`

**AWAITING RATIFICATION before E-3**

---

### 2025-12-31: Phase E-1 Violation Discovery Complete

User-mandated Phase E: Semantic Closure & Promotion Enforcement.

**Directive received:**
> "All known semantic bypasses MUST be eliminated by introducing formal promotion semantics, not documented, tolerated, or watch-listed."
> "No layer may consume semantics from a non-adjacent authority layer."

**E-1 Execution:**
- Mapped all 112 nodes to layers L1-L7
- Applied allowed import matrix to all ~137 edges
- Identified 10 semantic promotion violations
- Grouped into 4 patterns

**Key findings:**
- Inverted control flow: L5 calls L4 directly (should be L4 → L5)
- Implicit governance: L7 influences L4/L5 without formal signals
- Orphan authority: Schedulers and services making domain decisions
- Interpretation drift: External READ results interpreted outside L4

**Constraints met:**
- No fixes proposed
- No reclassifications as "acceptable"
- No annotations, notes, or watchlists
- Completeness over speed

Created: `docs/governance/PHASE_E_VIOLATIONS.md`

**AWAITING RATIFICATION before E-2**

---

### 2025-12-31: ASCII Diagram Generated

User approved extraction as diagram source of truth.
Phase 3 review questions answered:
- Nothing structurally missing
- Surprises: hard authority actions, clean frontend, controlled blast radius
- Implicit coupling: L7↔L4 via state, external READ influence

Created RAW_ARCHITECTURE_DIAGRAM.md mechanically from nodes/edges v2:
- Full system diagram with all 112 nodes
- Authority edges marked [!]
- 5 hard-stop transactions highlighted
- Governance control vs telemetry observers separated
- Blast radius reference for external systems

Phase 5 (layered structure) now eligible.

### 2025-12-31: Refinement (v2)

User scrutiny identified 4 gaps in v1 extraction:
1. Entry Points were module-level, not transactional-level
2. "External" was a black hole node
3. Scheduler nodes lacked trigger semantics
4. Observer edges conflated telemetry with governance control

Applied all 4 refinements:
- Split Entry Points: 12 containers + 52 transactions
- Expanded External: 9 concrete systems with read/write semantics
- Annotated Schedulers: TIME-BASED triggers, can fire without human intent
- Differentiated Observers: BLCA/CI as CONTROL, Prometheus/Alertmanager as TELEMETRY

v2 totals: 112 nodes, ~137 edges

### 2025-12-31: Initial Extraction

- Created CHANGES_TO_PHASES_GUIDE.md (18 change types → phases)
- Created RAW_ARCHITECTURE_NODES.md (50 nodes from code)
- Created RAW_ARCHITECTURE_EDGES.md (63 edges from imports)
- Method correction applied: evidence-based extraction, no design from theory
- Awaiting user review before proceeding to Phase 3 questions

---

**Contract Authority:** SESSION_PLAYBOOK.yaml v2.19 Section 29
**Baseline Reference:** Truthful Architecture v1 (2025-12-31)
