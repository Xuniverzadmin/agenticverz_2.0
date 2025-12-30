# PIN-250: Structural Truth Extraction Lifecycle

**Status:** ACTIVE
**Created:** 2025-12-30
**Category:** Architecture / Governance
**Scope:** Repository-wide

---

## Purpose

This PIN tracks the **Structural Truth Extraction** lifecycle — a systematic process to understand what the codebase *is*, not what it *claims to be*.

**Core Principle:**
> Metadata is not truth. Only behavior, dependencies, and call graphs are truth.
> CI encodes assumptions. If assumptions are wrong, CI enforces lies at scale.
> Business logic is a privilege earned only after structure is understood.

---

## Phase Tracker

| Phase | Name | Status | Started | Completed |
|-------|------|--------|---------|-----------|
| 0 | Governance Lock | DONE | 2025-12-30 | 2025-12-30 |
| 1 | Structural Truth Extraction | IN_PROGRESS | 2025-12-30 | - |
| 2 | Structural Alignment | PENDING | - | - |
| 3 | CI Derivation | PENDING | - | - |
| 4 | CI Sanity Pass | PENDING | - | - |
| 5 | Business Logic Eligibility | PENDING | - | - |

**Current Phase:** Phase 1 IN_PROGRESS — Scope: Backend Only (~400 Python files)

---

## Phase 0: Governance Lock (DONE)

**Status:** DONE
**Date:** 2025-12-30

### Deliverables

- [x] Architecture frozen
- [x] Layer model defined (L1-L8)
- [x] ARCH-GOV rules established (001-007)
- [x] SESSION_PLAYBOOK v2.8 with Layer Classification Gate
- [x] No new code allowed without governance

### Artifacts

- `docs/playbooks/SESSION_PLAYBOOK.yaml` — Section 26 (ARCH-GOV-007)
- `docs/technical-debt/QUARANTINE_LEDGER.md` — 7 TD entries
- `mypy.ini` — Quarantine configuration
- PIN-249 — Protective Governance & Housekeeping Normalization

---

## Phase 1: Structural Truth Extraction (IN_PROGRESS)

**Status:** IN_PROGRESS
**Started:** 2025-12-30
**Scope:** Backend only (~400 Python files)
**Goal:** Understand what the codebase *is*, not what it *claims to be*.

This phase explicitly **ignores business intent**.

### What Is Allowed

- Reading code
- Tracing dependencies
- Mapping call graphs
- Observing runtime wiring
- Reclassifying layers
- Moving files *only to restore structural truth*
- Fixing linkages and routes

### What Is Forbidden

- Feature changes
- Optimizations
- Behavior refactors
- "Since we're here..." edits
- AI Console work
- Business logic changes

**Rule:** If behavior changes, it must be a *side-effect of reclassification*, not intent.

### Deliverables

- [x] Directory-level truth map — `docs/architecture/STRUCTURAL_TRUTH_MAP.md`
- [x] Dependency-direction map — included in truth map
- [ ] Runtime-trigger map (import-time / request-time / async)
- [ ] State ownership map
- [ ] Policy enforcement map
- [ ] Glue vs Domain classification

### Artifacts Created

- `docs/architecture/STRUCTURAL_TRUTH_MAP.md` — Comprehensive layer classification for 36 directories
- Dependency matrix showing import flow (L2→L6)
- Critical structural issues identified (14 total: 5 P1, 5 P2, 4 P3)
- Architectural health score: 9.2/10 (zero circular dependencies)

### Scope Options

| Option | Scope | Estimated Files |
|--------|-------|-----------------|
| A | Full repo | ~600 Python files |
| B | Backend only | ~400 Python files |
| C | AI Console slice | ~100 files |

---

## Phase 2: Structural Alignment (PENDING)

**Status:** PENDING
**Prerequisite:** Phase 1 complete
**Goal:** Make structure match reality, with minimal semantic churn.

### Activities

- Reassign layers where misclassified
- Fix directory naming lies
- Split hybrid files
- Repair dependency direction violations
- Make routing explicit
- Remove accidental coupling

### Constraints

- Still **no new business logic**
- Changes must be structural, not behavioral
- Each change must reference Phase 1 finding

### Deliverables

- [ ] Truth vs Claim Diff document
- [ ] Layer reclassification log
- [ ] Hybrid split log
- [ ] Dependency repair log

---

## Phase 3: CI Derivation (PENDING)

**Status:** PENDING
**Prerequisite:** Phase 2 complete
**Goal:** Derive CI rules from structural truth, not assumptions.

At this point CI becomes a *measurement* of truth, not a *creator* of truth.

### CI Questions That Become Meaningful

- Did the layer graph change?
- Did a forbidden dependency appear?
- Did a route lose its domain handler?
- Did an async boundary collapse?
- Did a state owner change?

### Deliverables

- [ ] Layer dependency CI check
- [ ] Route wiring CI check
- [ ] Async boundary CI check
- [ ] State ownership CI check

---

## Phase 4: CI Sanity Pass (PENDING)

**Status:** PENDING
**Prerequisite:** Phase 3 complete
**Goal:** Validate CI catches real issues without blocking truth discovery.

### Expectations

- Some failures (expected)
- Some unknowns (expected)
- Some "we didn't know this existed" (success signal)

### Activities

- Run CI suite
- Classify failures: real vs false positive
- Tune thresholds
- Document known exceptions

### Deliverables

- [ ] CI failure classification
- [ ] Exception registry
- [ ] Tuned CI configuration

---

## Phase 5: Business Logic Eligibility (PENDING)

**Status:** PENDING
**Prerequisite:** Phase 4 complete
**Goal:** Earn the right to touch business logic.

### Unlocked Activities

- AI Console development
- Product features
- Domain behavior changes
- Feature optimization

### Prerequisites Check

- [ ] Structure is understood
- [ ] Layers are real (not aspirational)
- [ ] Routes and linkages are explicit
- [ ] CI catches regressions
- [ ] Technical debt is registered

---

## Lifecycle Diagram

```
[DONE] Phase 0 — Governance Lock
          │
          ▼
[IN_PROGRESS] Phase 1 — Structural Truth Extraction   ◄── CURRENT
          │
          ▼
[PENDING] Phase 2 — Structural Alignment
          │
          ▼
[PENDING] Phase 3 — CI Derivation
          │
          ▼
[PENDING] Phase 4 — CI Sanity Pass
          │
          ▼
[PENDING] Phase 5 — Business Logic Eligibility
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-30 | Phase 0 complete | Governance, layers, ARCH-GOV rules established |
| 2025-12-30 | Created PIN-250 | Track lifecycle formally |
| 2025-12-30 | Phase 1 started (backend only) | Backend has structural complexity; ~400 files tractable |
| 2025-12-30 | Directory truth map complete | 36 directories classified, 14 structural issues identified |
| 2025-12-30 | Dependency map complete | Zero circular deps, 9.2/10 architectural health |

---

## Rules (Non-Negotiable)

1. **No phase skipping** — Each phase has prerequisites
2. **No "while we're here"** — Scope creep is forbidden
3. **Behavior changes are side-effects** — Never intent
4. **CI comes from truth** — Not assumptions
5. **Business logic is earned** — Not assumed

---

## References

- PIN-245: Integration Integrity System
- PIN-248: Codebase Inventory & Layer System
- PIN-249: Protective Governance & Housekeeping Normalization
- SESSION_PLAYBOOK Section 26: Layer Classification Gate
- docs/REPO_STRUCTURE.md: Repository structure map

---

## Next Action

To proceed, select Phase 1 scope:

1. **"Start Phase 1: structural truth extraction — repo-wide"**
2. **"Start Phase 1 on backend only"**
3. **"Start Phase 1 on AI Console slice only"**

Phase 1 rules will be strictly enforced.
