# Panel Structure Pipeline

**Status:** PHASE 2 COMPLETE
**Created:** 2026-01-16
**Authority:** Governance Document
**Reference:** PIN-420 (Semantic Authority), SEMANTIC_VALIDATOR.md, HISAR.md

---

## Overview

This document defines the **phased approach** to panel structure management in the AURORA L2 pipeline. It addresses the tension between:

- **Human cognitive load** — Defining 148+ panels manually is exhausting
- **Machine determinism** — Automation must not introduce authority leaks
- **Pipeline integrity** — Phase A validation must remain the single gate

**Core Principle:**

> **Stabilize semantics first. Automate later.**
> **If automation creates structure before humans feel pain, it will break authority.**
> **If automation relieves proven pain, it will scale the system.**

---

## Current Architecture (Baseline)

```
INTENT_LEDGER.md (Human Intent - Single Source of Truth)
        ↓
sync_from_intent_ledger.py
        ↓
├── ui_plan.yaml (UI structure)
├── intents/AURORA_L2_INTENT_*.yaml (Intent YAMLs)
└── AURORA_L2_CAPABILITY_REGISTRY/*.yaml (Capabilities)
        ↓
Phase A: validate_all_intents.py (INT-001 to INT-008)
        ↓
Aurora Compilation
        ↓
ui_projection_lock.json
```

**Key Constraints:**

| Artifact | Authority | Status |
|----------|-----------|--------|
| `UI_TOPOLOGY_TEMPLATE.yaml` | FROZEN | Defines panel_slots per topic |
| `INTENT_LEDGER.md` | Human | Panel-centric declarations |
| `ui_plan.yaml` | Generated | Single UI authority |
| Phase A | Blocking Gate | Validates intent guardrails |

---

## The Problem

### Pain Points

1. **Panel-centric abstraction is low-level**
   - Humans must decide panel count upfront
   - "Why does this panel exist?" becomes unclear over time

2. **Semantic drift risk**
   - Panels with similar purposes scattered across topics
   - No grouping mechanism for related information

3. **Exploration is unsafe**
   - Any experimentation requires manual edits
   - Fear of breaking Phase A discourages iteration

### What We Do NOT Want

- ML/AI-based panel generation
- Confidence scores or non-deterministic selection
- Duplicate authority (facet_rules vs panel_slots conflict)
- Bypass of Phase A validation
- Premature automation

---

## Phased Implementation Plan

### Phase 1: Facets as Semantic Overlay (CURRENT)

**Goal:** Introduce semantic grouping without changing pipeline mechanics.

**Status:** `COMPLETE`

**What Changes:**

| Component | Change | Authority Impact |
|-----------|--------|------------------|
| `INTENT_LEDGER_GRAMMAR.md` | Add facet syntax | Documentation only |
| `INTENT_LEDGER.md` | Add facet sections | Human-authored |
| `sync_from_intent_ledger.py` | Propagate facet to intent YAMLs | Optional metadata |
| `validate_all_intents.py` | No change | Facets are non-authoritative |
| `run_aurora_l2_pipeline.sh` | No change | Pipeline unchanged |

**Facet Definition:**

A facet is a **semantic grouping of information needs** that may span multiple panels.

```yaml
# Example facet in INTENT_LEDGER.md
## Facet: error_visibility

Purpose: Operators must understand system error health and failure causes

Criticality: HIGH

Panels:
  - LOG-REC-SYS-O1 (status summary)
  - LOG-REC-SYS-O2 (error list)
  - LOG-REC-SYS-O3 (error details)
```

**Key Invariants:**

1. Facets are **non-authoritative** — Phase A ignores them
2. Facets are **human-defined** — No machine generation
3. Facets are **additive** — Don't change existing panel semantics
4. Facets exist in **source only** — INTENT_LEDGER.md, propagated to intent YAMLs

**Implementation Steps:**

- [x] Create this governance document
- [x] Add facet syntax to `INTENT_LEDGER_GRAMMAR.md`
- [x] Add facet sections to `INTENT_LEDGER.md`
- [x] Update `sync_from_intent_ledger.py` to propagate facets
- [x] Verify Phase A still passes (no regression)

---

### Phase 2: Read-Only Tooling (CURRENT)

**Goal:** Build diagnostic tools that read facet structure without modifying pipeline.

**Status:** `COMPLETE`

**Implemented Tools:**

| Tool | Purpose | Output |
|------|---------|--------|
| `facet_slot_pressure.py` | Identify topics with slot pressure | JSON/Markdown |
| `facet_overlap_detector.py` | Detect overlapping panels | JSON/Markdown |
| `facet_completeness_checker.py` | Find underrepresented facets | JSON/Markdown |

**Key Constraints:**

- Tools **read only** — Never write to intent/projection
- Tools **report gaps** — Human decides action
- Tools **respect authority** — No auto-fixing

**Usage:**

```bash
# Slot pressure analysis
python scripts/tools/facet_slot_pressure.py --format markdown

# Overlap detection
python scripts/tools/facet_overlap_detector.py --format markdown

# Completeness check
python scripts/tools/facet_completeness_checker.py --format markdown
```

**Sample Output (2026-01-16):**

| Metric | Value |
|--------|-------|
| High pressure topics | 14 (at 100% utilization) |
| Panel overlaps detected | 0 |
| Facets with issues | 3 (1 HIGH criticality) |
| Overall slot utilization | 68% |

---

### Phase 3: Deterministic Generator (FUTURE, CONDITIONAL)

**Goal:** Automate panel suggestions ONLY when human bottleneck is proven.

**Status:** `NOT STARTED`

**Prerequisites (all must be true):**

- [ ] Facets are stable across 3+ sprints
- [ ] Slot pressure is painful (human feedback)
- [ ] Phase A has been stable for 30+ days
- [ ] Human approval for generator introduction

**Hard Constraints (non-negotiable):**

| Constraint | Rationale |
|------------|-----------|
| No confidence scores | Preserves determinism |
| No ML/AI | Zero-AI compiler principle |
| `facet_rules ≤ panel_slots` | Respects topology authority |
| Output must pass Phase A | No bypass of validation |
| Generated panels = hand-written | No special treatment |

**Generator Architecture (if implemented):**

```
Facets + Observed Capabilities
        ↓
Panel Candidate Generator (deterministic rules only)
        ↓
Candidates (advisory, never authoritative)
        ↓
Human Review (approve/reject/modify)
        ↓
UI Plan Materialiser (writes to ui_plan.yaml)
        ↓
Phase A Validation (same as always)
```

**The generator is just a code generator for intent YAMLs, not a new authority.**

---

## Authority Model

```
┌─────────────────────────────────────────────────────────────┐
│  AUTHORITY HIERARCHY (IMMUTABLE)                            │
├─────────────────────────────────────────────────────────────┤
│  1. UI_TOPOLOGY_TEMPLATE.yaml — Slot constraints            │
│  2. INTENT_LEDGER.md — Panel declarations + facets          │
│  3. ui_plan.yaml — Generated UI structure                   │
│  4. Phase A — Validation gate                               │
│  5. Aurora Compilation — Projection output                  │
└─────────────────────────────────────────────────────────────┘

Facets exist at level 2 (INTENT_LEDGER.md) as semantic metadata.
Facets never override levels 1, 3, 4, or 5.
```

---

## Integration with Phase A/B Validation

### Phase A (Intent Guardrails)

| Check | Facet Impact |
|-------|--------------|
| INT-001 (Signal provable) | No change — validates panels |
| INT-002 (Capability cardinality) | No change — validates panels |
| INT-007 (Semantic contract exists) | No change — validates panels |
| INT-008 (Capability reference valid) | No change — validates panels |

**Facets are invisible to Phase A.** This is intentional.

### Phase B (Semantic Reality)

| Check | Facet Impact |
|-------|--------------|
| SEM-001 to SEM-008 | No change — validates runtime signals |

**Facets have no runtime impact.**

---

## Implementation Status

| Phase | Component | Status | Date |
|-------|-----------|--------|------|
| 1 | `PANEL_STRUCTURE_PIPELINE.md` | COMPLETE | 2026-01-16 |
| 1 | `INTENT_LEDGER_GRAMMAR.md` — facet syntax | COMPLETE | 2026-01-16 |
| 1 | `INTENT_LEDGER.md` — facet sections | COMPLETE | 2026-01-16 |
| 1 | `sync_from_intent_ledger.py` — facet propagation | COMPLETE | 2026-01-16 |
| 1 | Phase A regression test | COMPLETE | 2026-01-16 |
| 2 | `facet_slot_pressure.py` | COMPLETE | 2026-01-16 |
| 2 | `facet_overlap_detector.py` | COMPLETE | 2026-01-16 |
| 2 | `facet_completeness_checker.py` | COMPLETE | 2026-01-16 |
| 3 | Panel Candidate Generator | NOT STARTED | - |
| 3 | UI Plan Materialiser | NOT STARTED | - |

**Phase 1 Summary:**
- 12 facets defined in INTENT_LEDGER.md
- 50 panels have facet assignments
- Facet metadata propagates to intent YAMLs
- Phase A validation passes (0 violations)
- Facets are non-authoritative — Phase A ignores them as designed

**Phase 2 Summary:**
- 3 read-only diagnostic tools implemented
- Tools expose pressure points without modifying pipeline
- 14 topics at 100% slot utilization identified
- 3 facets requiring attention (1 HIGH criticality)
- 0 panel overlaps detected (panels are well-differentiated)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Facets become authoritative | Phase A ignores facets — mechanical enforcement |
| Premature generator introduction | Prerequisites gate — human approval required |
| Topology authority duplication | facet_rules ≤ panel_slots constraint |
| Non-deterministic selection | No confidence scores allowed |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-16 | Defer generator, proceed with facets only | Stabilize semantics first |
| 2026-01-16 | Facets are non-authoritative | Preserve Phase A as single gate |
| 2026-01-16 | No confidence scores | Maintain zero-AI compiler principle |

---

## References

- [SEMANTIC_VALIDATOR.md](SEMANTIC_VALIDATOR.md) — Phase A/B validation
- [HISAR.md](../../governance/HISAR.md) — Execution doctrine
- [AURORA_L2.md](../../../design/l2_1/AURORA_L2.md) — Pipeline specification
- `UI_TOPOLOGY_TEMPLATE.yaml` — Slot constraints
- `INTENT_LEDGER.md` — Panel declarations

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial creation — phased plan documented |
| 2026-01-16 | Phase 1 implementation started |
| 2026-01-16 | Phase 1 COMPLETE — facet grammar, 12 facets defined, sync script updated, Phase A verified |
| 2026-01-16 | Phase 2 COMPLETE — 3 read-only diagnostic tools implemented |
