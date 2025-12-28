# PIN-232: C5 Learning & Evolution — Entry Conditions

**Created:** 2025-12-28
**Frozen:** 2025-12-28
**Status:** FROZEN
**Phase:** C5_LOCKED
**Related PINs:** PIN-231, PIN-230, PIN-225

---

## Summary

This PIN establishes the entry conditions, invariants, and explicit non-goals for Phase C5 — Learning & Evolution. C5 is where the system may begin to **learn from historical outcomes** and **suggest policy changes**.

**CRITICAL:** C5 implementation remains LOCKED. This document defines the guardrails that must exist BEFORE any C5 code is written.

> **FREEZE NOTICE:** Entry conditions, invariants, and non-goals are now FROZEN.
> Any modification requires explicit human approval and re-certification justification.

---

## What C5 Is (Precise Definition)

C5 introduces **learning over time**, meaning the system may update:

- envelope defaults
- envelope bounds
- priority weights
- coordination policies

Based on **historical outcomes**, not just static rules.

**C5 is not optimization.**
**It is policy evolution.**

---

## Why C5 Is Different

Up to C4, the system:
- observes (C1)
- predicts (C2)
- acts safely (C3)
- coordinates safely (C4)

**C5 changes the nature of the system.**

C5 introduces memory, learning, and evolution. That means:
- behavior may change *over time*
- envelopes and priorities may adapt
- past outcomes influence future decisions

This is where most systems quietly lose:
- explainability
- auditability
- operator trust

---

## C5 Entry Conditions (ALL Required)

C5 may not be unlocked unless **every condition below is satisfied**.

### EC5-1 — Stable C4 Baseline

**Two Valid Modes:**

| Mode | When to Use | Criteria Document |
|------|-------------|-------------------|
| **Time-Based** | Real users, real traffic | `C4_OPERATIONAL_STABILITY_CRITERIA.md` |
| **Synthetic** | Founder-only, no users | `C4_FOUNDER_STABILITY_CRITERIA.md` |

**Runbook:** `docs/contracts/C4_SYNTHETIC_STABILITY_RUNBOOK.md`
**Evidence Pack:** `docs/contracts/C4_STABILITY_EVIDENCE_PACK.md`

#### Time-Based Requirements (7 days with traffic)

| Requirement | Status |
|-------------|--------|
| ≥7 continuous days | ⏳ PENDING |
| ≥2 envelopes simultaneously active | ⏳ PENDING |
| ≥2 different envelope classes | ⏳ PENDING |
| ≥10 coordination decisions | ⏳ PENDING |
| ≥1 priority preemption | ⏳ PENDING |
| ≥1 same-parameter rejection | ⏳ PENDING |
| Zero emergency kill-switch activations | ⏳ PENDING |
| 100% audit coverage | ⏳ PENDING |
| CI guardrails 100% passing | ⏳ PENDING |
| Replay determinism verified | ⏳ PENDING |

#### Synthetic Requirements (20 cycles with forced entropy)

| Requirement | Status |
|-------------|--------|
| ≥20 coordination cycles | ✅ SATISFIED (22 cycles) |
| ≥3 runtime sessions | ✅ SATISFIED (3 sessions) |
| ≥10 overlapping envelopes | ✅ SATISFIED (11 overlaps) |
| ≥3 priority preemptions | ✅ SATISFIED (3 preemptions) |
| ≥3 same-parameter rejections | ✅ SATISFIED (3 rejections) |
| ≥3 backend restarts mid-envelope | ✅ SATISFIED (4 restarts) |
| ≥2 kill-switch dry-runs | ✅ SATISFIED (2 dry-runs) |
| ≥5 replay verifications | ✅ SATISFIED (5 replays) |
| Zero emergency kill-switch activations | ✅ SATISFIED (0 emergency) |
| 100% CI guardrails passing | ✅ SATISFIED (6/6 passing) |

**Synthetic Stability Gate:** ✅ SATISFIED (2025-12-28)
**Evidence Pack:** `docs/contracts/C4_STABILITY_EVIDENCE_PACK_20251228.md`

**Reason:** Learning on unstable ground amplifies noise.

**Unlock Phrases:**
- Time-Based: "C5 stability gate satisfied. Evidence pack reviewed."
- Synthetic: "C4 synthetic stability gate satisfied under founder-only operation. Evidence pack reviewed."

---

### EC5-2 — Immutable C4 Replay Baseline

| Requirement | Status |
|-------------|--------|
| A frozen replay baseline must exist | ✅ SATISFIED |
| Learning must be replayable against old policies | ✅ SATISFIED |

**Reason:** If you can't replay learning, you can't trust it.

**Evidence:** `suggestions.py` stores all observation data immutably. AC-S1-I7 tests verify replayability.

---

### EC5-3 — Learning Must Be Advisory First

| Requirement | Status |
|-------------|--------|
| All learning outputs must start as advisory | ✅ SATISFIED |
| Learning outputs must be non-authoritative | ✅ SATISFIED |
| Learning outputs must be non-applying | ✅ SATISFIED |

**Learning cannot immediately affect envelopes.**

**Evidence:** `suggestion_type` is `Literal["advisory"]`. All suggestions start as `PENDING_REVIEW`. CI-C5-1 enforces.

---

### EC5-4 — Explicit Learning Boundary

Learning must operate on:
- metadata ✅
- policy suggestions ✅

Learning must NOT operate on:
- runtime parameters ✅ (CI-C5-3 enforces)
- live envelopes ✅ (CI-C5-6 enforces)
- kill-switch logic ✅ (CI-C5-6 enforces)

**Evidence:** `tables.py` defines LEARNING_ALLOWED_TABLES and LEARNING_FORBIDDEN_TABLES.

---

### EC5-5 — Human Approval Gate

| Requirement | Status |
|-------------|--------|
| Any learned change affecting bounds requires human approval | ✅ SATISFIED |
| Any learned change affecting priorities requires human approval | ✅ SATISFIED |
| Any learned change affecting coordination rules requires human approval | ✅ SATISFIED |

**No silent learning allowed.**

**Evidence:** All suggestions start as `PENDING_REVIEW`. CI-C5-2 enforces. H-series tests verify.

---

### EC5-6 — Learning Rollback Guarantee

| Requirement | Status |
|-------------|--------|
| Learned changes must be versioned | ✅ SATISFIED |
| Learned changes must be reversible | ✅ SATISFIED |
| Learned changes must be independently disableable | ✅ SATISFIED |

**If learning can't be rolled back → C5 forbidden.**

**Evidence:** `LEARNING_ENABLED` flag (D-series tests). `version` field on suggestions. Database immutability trigger.

---

## C5 Invariants (FROZEN)

| ID | Invariant |
|----|-----------|
| I-C5-1 | Learning suggests, humans decide |
| I-C5-2 | No learned change applies without approval |
| I-C5-3 | Learning operates on metadata, not runtime |
| I-C5-4 | All learned suggestions are versioned |
| I-C5-5 | Learning can be disabled without affecting coordination |
| I-C5-6 | Kill-switch supremacy is unchanged |
| I-C5-7 | Learned policies are replayable |
| I-C5-8 | No autonomous policy mutation |

---

## Explicit C5 Non-Goals (LOCKED)

C5 does **NOT** allow:

| Capability | Status | Reason |
|------------|--------|--------|
| Autonomous policy mutation | FORBIDDEN | Loss of human control |
| Self-modifying coordination rules | FORBIDDEN | Unpredictable behavior |
| Reinforcement learning on production behavior | FORBIDDEN | Opaque optimization |
| Live envelope tuning | FORBIDDEN | Bypasses coordination |
| Confidence-driven priority reordering | FORBIDDEN | Semantic drift |
| Opaque models influencing control paths | FORBIDDEN | Unexplainable decisions |

If any of these appear, you are **outside C5** and into an unsafe system.

---

## C5 Safety Principle (Single Sentence)

> **Learning may suggest. Humans decide. Systems apply through existing envelopes.**

If this sentence ever becomes false, certification is invalid.

---

## Potential C5 Scenarios (Design Only)

Only after C5 entry conditions are frozen should you consider:

### C5-S1: Learning from Rollback Frequency
- Observe: How often do envelopes rollback?
- Suggest: Should bounds be tighter?
- Output: Advisory recommendation to human

### C5-S2: Learning from Envelope Expiry Patterns
- Observe: Do envelopes expire before effect?
- Suggest: Should timeboxes be shorter?
- Output: Advisory recommendation to human

### C5-S3: Learning from Cost vs Reliability Outcomes
- Observe: What's the cost/reliability tradeoff?
- Suggest: Should priority weights adjust?
- Output: Advisory recommendation to human

All of these would:
- produce *suggestions*
- never apply automatically
- require human approval

---

## C5 CI Guardrails (Implemented)

**Design Document:** `docs/contracts/C5_CI_GUARDRAILS_DESIGN.md`
**Runner Script:** `scripts/ci/c5_guardrails/run_all.sh`

| Guard | Description | Status |
|-------|-------------|--------|
| CI-C5-1 | Learning outputs are advisory only | ✅ IMPLEMENTED |
| CI-C5-2 | No learned change applies without approval flag | ✅ IMPLEMENTED |
| CI-C5-3 | Learning operates on metadata tables only | ✅ IMPLEMENTED |
| CI-C5-4 | All learned suggestions are versioned | ✅ IMPLEMENTED |
| CI-C5-5 | Learning disable flag exists and works | ✅ IMPLEMENTED |
| CI-C5-6 | Kill-switch behavior unchanged by learning | ✅ IMPLEMENTED |

**CI Run Result:** 6/6 PASS (2025-12-28)

---

## Current C5 Status

| Item | State |
|------|-------|
| C5 Entry Conditions | 🔒 FROZEN |
| C5 Non-Goals | 🔒 FROZEN |
| C5 Invariants | 🔒 FROZEN |
| C5 CI Guardrails | ✅ IMPLEMENTED |
| C5-S1 Implementation | ✅ COMPLETE |
| C5 Certification | ⏳ PENDING |
| C5 Risk | CONTAINED |

---

## Implementation Order

| Step | Description | Status |
|------|-------------|--------|
| 1 | Freeze C5 Entry Conditions | ✅ COMPLETE (2025-12-28) |
| 2 | Design C5 CI guardrails | ✅ COMPLETE (2025-12-28) |
| 3 | Stable C4 operational baseline | ✅ COMPLETE (2025-12-28, synthetic mode) |
| 4 | Design C5-S1 scenario (advisory only) | ✅ FROZEN (2025-12-28) |
| 5 | Implement C5 learning layer | ✅ COMPLETE (2025-12-28) |
| 6 | C5 Certification | ⏳ PENDING |

### C5-S1 Design Artifacts (FROZEN)

| Document | Status | Contents |
|----------|--------|----------|
| `C5_S1_LEARNING_SCENARIO.md` | FROZEN | Purpose, inputs, outputs, boundaries |
| `C5_S1_ACCEPTANCE_CRITERIA.md` | FROZEN | 26 pass/fail criteria (I/B/M/O/H/D series) |
| `C5_S1_CI_ENFORCEMENT.md` | FROZEN | CI-C5-1 to CI-C5-6 mapping to S1 |

### C5-S1 Implementation Artifacts

| Artifact | Location |
|----------|----------|
| Learning config | `backend/app/learning/config.py` |
| Learning suggestions | `backend/app/learning/suggestions.py` |
| Table boundaries | `backend/app/learning/tables.py` |
| Rollback observer | `backend/app/learning/s1_rollback.py` |
| Database migration | `backend/alembic/versions/062_c5_learning_suggestions.py` |
| CI guardrails | `scripts/ci/c5_guardrails/` (6 scripts) |
| Tests | `backend/tests/learning/test_s1_rollback.py` (27 tests) |

### C5-S1 Test Results (2025-12-28)

| Test Series | Tests | Status |
|-------------|-------|--------|
| I-Series (Invariant) | 8 | ✅ ALL PASS |
| B-Series (Boundary) | 4 | ✅ ALL PASS |
| M-Series (Immutability) | 3 | ✅ ALL PASS |
| O-Series (Observation) | 4 | ✅ ALL PASS |
| H-Series (Human Interaction) | 4 | ✅ ALL PASS |
| D-Series (Disable Flag) | 3 | ✅ ALL PASS |
| Text Generation | 1 | ✅ PASS |
| **Total** | **27** | ✅ **ALL PASS** |

---

## Truth Anchor

> C5 is where systems become unpredictable if not governed.
> Learning introduces temporal coupling.
> If learning can change behavior without approval, you have lost control.
>
> The only safe learning is learning that suggests but never decides.

---

## Re-Certification Triggers (Future)

When C5 is implemented, certification becomes invalid if:

| Trigger | Severity |
|---------|----------|
| Learning output becomes non-advisory | CRITICAL |
| Approval gate bypassed | CRITICAL |
| Learning operates on runtime parameters | CRITICAL |
| Kill-switch behavior affected by learning | CRITICAL |
| Learning rollback fails | HIGH |
| Replay with learning produces different results | HIGH |
---

## Implementation Complete

### Update (2025-12-28)

## 2025-12-28: C5-S1 Implementation Complete

### Summary
C5-S1 (Learning from Rollback Frequency) has been fully implemented, tested, and frozen.

### Verification Results
- **Acceptance Criteria:** 46/46 checks PASS (100% compliant)
- **CI Guardrails:** 6/6 PASS
- **Unit Tests:** 27/27 PASS
- **Migration:** Applied to Neon (062_c5_learning_suggestions)

### Implementation Artifacts
| Component | Location |
|-----------|----------|
| Learning Config | `backend/app/learning/config.py` |
| Suggestions Model | `backend/app/learning/suggestions.py` |
| Table Boundaries | `backend/app/learning/tables.py` |
| Rollback Observer | `backend/app/learning/s1_rollback.py` |
| Migration | `backend/alembic/versions/062_c5_learning_suggestions.py` |
| CI Scripts | `scripts/ci/c5_guardrails/` (7 scripts) |
| Tests | `backend/tests/learning/test_s1_rollback.py` |

### Key Safety Properties Verified
1. **Advisory Only** - All suggestions use `Literal["advisory"]`
2. **Human Approval Gate** - Default status is `pending_review`
3. **Metadata Boundary** - Zero imports from runtime tables
4. **Kill-Switch Isolation** - Zero imports from killswitch/coordinator
5. **Immutability** - DB trigger prevents mutation of core fields
6. **Disable Flag** - `LEARNING_ENABLED=false` stops all observation

### Certification Statement
> "C5-S1 provides advisory insights derived from rollback frequency, without influencing system behavior, requiring explicit human approval for any downstream action."

### Commit
`a0cd6cb` - C5-S1: Learning from Rollback Frequency - FROZEN
---

## Architectural Gap Identified

### Update (2025-12-28)

## 2025-12-28: C4 Audit Persistence Gap Identified

### Discovery
During C5-S1 implementation verification, a structural gap was identified:

> **C4 coordination is certified but its audit trail is in-memory, not persisted.**

### Impact Assessment

| Item | Status |
|------|--------|
| C4 coordination logic | ✅ Certified |
| C4 audit observability | ⚠️ **Incomplete** |
| C5-S1 design | ✅ Solid |
| C5-S1 implementation | ⚠️ Premature without audit persistence |

### Why This Matters
C5-S1 explicitly depends on metadata persistence:
- Learning observes `coordination_audit_records` (must exist)
- Rollback frequency requires historical data (must be durable)
- Advisory suggestions must reference real decisions (not simulated)

### Current State
- C4 coordination decisions are: enforced, deterministic, replay-safe
- But audited only in memory/logs, not a first-class DB artifact
- C5-S1 test harness uses simulated data (acceptable for unit tests only)

### Decision
**Proceed with Option A: Formalize C4 Coordination Audit Persistence**

This requires:
1. Draft `C4_COORDINATION_AUDIT_SCHEMA.md`
2. Define immutability + replay guarantees  
3. Add single append-only `coordination_audit_records` table
4. C4 minor re-certification (narrow scope)
5. C5-S1 remains unchanged

### What This Does NOT Change
- C4 behavior (already certified)
- C5-S1 logic (already verified)
- Replay determinism (already guaranteed)
- Learning isolation (already enforced)

### What This Enables
- C5-S1 can observe *real history*, not fabricated data
- Learning suggestions become production-legitimate
- Evidence packs reference actual coordination decisions

### Status Update

| Component | Previous | Current |
|-----------|----------|---------|
| C5-S1 Implementation | ✅ COMPLETE | ⚠️ BLOCKED (pending C4 audit) |
| C5-S1 Certification | ⏳ PENDING | 🔒 LOCKED (pending C4 audit) |
| C4 Audit Persistence | N/A | 📋 DESIGN REQUIRED |

### Next Steps
1. Design `C4_COORDINATION_AUDIT_SCHEMA.md`
2. Implement `coordination_audit_records` table
3. Wire C4 coordinator to emit audit records
4. Narrow C4 re-certification
5. Unlock C5-S1 certification
