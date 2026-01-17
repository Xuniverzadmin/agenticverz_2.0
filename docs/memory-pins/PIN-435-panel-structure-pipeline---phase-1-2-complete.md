# PIN-435: Panel Structure Pipeline - Phase 1 & 2 Complete

**Status:** ✅ COMPLETE
**Created:** 2026-01-16
**Category:** Architecture / Pipeline

---

## Summary

Implemented facet semantic overlay (Phase 1) and read-only diagnostic tooling (Phase 2) for panel structure management. Phase 3 deferred pending sustained pressure evidence.

---

## Details

## Overview

Implemented the Panel Structure Pipeline as defined in PANEL_STRUCTURE_PIPELINE.md.

**Core Principle:**
> Stabilize semantics first. Automate later.
> If automation creates structure before humans feel pain, it will break authority.

---

## Phase 1: Facets as Semantic Overlay (COMPLETE)

**Goal:** Introduce semantic grouping without changing pipeline mechanics.

**Artifacts Modified:**
- `design/l2_1/INTENT_LEDGER_GRAMMAR.md` — Added facet entry grammar (V1.1)
- `design/l2_1/INTENT_LEDGER.md` — Added 12 facets
- `scripts/tools/sync_from_intent_ledger.py` — Facet parsing and propagation

**Key Metrics:**
- 12 facets defined
- 50 panels have facet assignments
- Phase A validation: PASS (0 violations)
- Facets are non-authoritative — Phase A ignores them

**Facets Defined:**
1. system_health_overview (HIGH)
2. cost_intelligence (HIGH)
3. active_execution_monitoring (HIGH)
4. execution_signals (MEDIUM)
5. incident_lifecycle (HIGH)
6. policy_governance (HIGH)
7. limit_violations (HIGH)
8. execution_traces (MEDIUM)
9. audit_trail (HIGH)
10. account_identity (MEDIUM)
11. billing_usage (MEDIUM)
12. connectivity_health (HIGH)

---

## Phase 2: Read-Only Diagnostic Tooling (COMPLETE)

**Goal:** Expose where the current panel model is under strain, without changing behavior, structure, or authority.

**Tools Implemented:**

| Tool | Purpose | Location |
|------|---------|----------|
| `facet_slot_pressure.py` | Identify topics with slot pressure | scripts/tools/ |
| `facet_overlap_detector.py` | Detect overlapping panels | scripts/tools/ |
| `facet_completeness_checker.py` | Find underrepresented facets | scripts/tools/ |

**Tool Characteristics (Non-Negotiable):**
- Read-only — Never write to intent/projection
- Deterministic — Same input → same output
- JSON + Markdown output
- Never affect pipeline exit codes

**Initial Findings (2026-01-16):**
- High pressure topics: 14 (at 100% utilization)
- Panel overlaps: 0 (well-differentiated)
- Facets with issues: 3 (1 HIGH criticality)
- Overall slot utilization: 68%

---

## Phase 3: Deterministic Generator (NOT STARTED)

**Prerequisites (all must be true):**
- [ ] Facets stable across 3+ sprints
- [ ] Slot pressure painful (human feedback)
- [ ] Phase A stable for 30+ days
- [ ] Human approval for generator introduction

**Hard Rule:**
> No system may create or modify panels until Phase 2 reports demonstrate sustained pressure across releases.

---

## Key Files

| File | Role |
|------|------|
| `docs/architecture/pipeline/PANEL_STRUCTURE_PIPELINE.md` | Governance document |
| `design/l2_1/INTENT_LEDGER_GRAMMAR.md` | Facet grammar spec (V1.1) |
| `design/l2_1/INTENT_LEDGER.md` | Facet declarations |
| `scripts/tools/sync_from_intent_ledger.py` | Facet propagation |
| `scripts/tools/facet_slot_pressure.py` | Slot pressure analyzer |
| `scripts/tools/facet_overlap_detector.py` | Overlap detector |
| `scripts/tools/facet_completeness_checker.py` | Completeness checker |

---

## Authority Model (Preserved)

```
1. UI_TOPOLOGY_TEMPLATE.yaml — Slot constraints
2. INTENT_LEDGER.md — Panel declarations + facets
3. ui_plan.yaml — Generated UI structure
4. Phase A — Validation gate
5. Aurora Compilation — Projection output
```

Facets exist at level 2 as semantic metadata. They never override levels 1, 3, 4, or 5.

---

## Next Steps

- Return to HISAR topic (awaiting)
- Monitor Phase 2 reports for sustained pressure
- Phase 3 only if justified by evidence
