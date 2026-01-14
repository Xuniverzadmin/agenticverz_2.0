# PIN-419: Intent Ledger & Coherency Gate Architecture

**Status:** DESIGN COMPLETE — AWAITING APPROVAL
**Created:** 2026-01-14
**Updated:** 2026-01-14 (Evolved to Intent Ledger model)
**Category:** Architecture / UI Pipeline
**Related:** PIN-370 (SDSR System Contract), PIN-379 (E2E Pipeline)

---

## Summary

Design for a **Coherency Gate System** where human intent is expressed in **natural language** (Intent Ledger), and AI/scripts generate the YAML artifacts (`ui_plan.yaml`, capability registry, SDSR scenarios). YAMLs are **compiled artifacts**, not human-edited sources.

---

## Problem Statement

### Current Pipeline Violations

| Problem | Impact | Severity |
|---------|--------|----------|
| **Frontend scaffolding** creates secondary structural authority | UI can invent structure projection doesn't authorize | CRITICAL |
| **Missing `AURORA_L2_apply_sdsr_observations.py`** | Capabilities stuck at DECLARED, never advance to OBSERVED | CRITICAL |
| **86/87 panels EMPTY/UNBOUND** | Pipeline works but operational coverage sparse | HIGH |
| **No coherency check** between ui_plan and SDSR scenarios | Gaps discovered at compile time, not divergence time | HIGH |

### Root Cause

Human intent diverges into two paths (structure + verification) but humans cannot maintain two synchronized YAMLs. YAML is a machine format, not a human intent format.

---

## Design Evolution

### Rejected Approaches

| Approach | Why Rejected |
|----------|--------------|
| Two human-maintained YAMLs | Humans cannot sync two files (GPT critique valid) |
| INTENT_SOURCE.yaml → machine split | Inverts authority (ui_plan becomes generated) |
| Extend ui_plan.yaml with verification | UI churn ≠ capability churn; would kill in long run |

### Final Architecture: Intent Ledger

**Key Insight:** Let humans express intent in natural language. AI/scripts produce the YAMLs.

```
═══════════════════════════════════════════════════════════════════════════════
                         HUMAN INTENT (NATURAL LANGUAGE)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTENT_LEDGER.md                                     │
│                                                                             │
│  Human writes:                                                              │
│  - "Add panel INC-AI-SUM-O1 in Incidents > AI Analysis > Summary"          │
│  - "Verify summary.incidents capability with SDSR scenario"                │
│  - "Expected: Summary reflects actual incident counts"                     │
│                                                                             │
│  Format: Markdown with structured intent blocks                             │
│  Authority: Human intent, single source of truth                           │
│  Location: design/l2_1/INTENT_LEDGER.md                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   AI/SCRIPT GENERATION                                      │
│                                                                             │
│  sync_from_intent_ledger.py (or AI-assisted workflow)                       │
│                                                                             │
│  GENERATES (not hand-edited):                                               │
│  • ui_plan.yaml (structural plane)                                         │
│  • SDSR scenario YAMLs (verification plane)                                │
│  • Capability registry entries                                              │
│  • Intent YAMLs for panels                                                  │
│                                                                             │
│  YAMLs are COMPILED ARTIFACTS, not human sources                           │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│     ui_plan.yaml         │    │    SDSR Scenarios        │
│     (GENERATED)          │    │    (GENERATED)           │
│                          │    │                          │
│  • What panels exist     │    │  • What we verify        │
│  • Domain hierarchy      │    │  • How we observe        │
│  • Panel classes         │    │  • Acceptance criteria   │
│                          │    │                          │
│  AUTHORITY: Structure    │    │  AUTHORITY: Verification │
│  MAINTAINER: Script/AI   │    │  MAINTAINER: Script/AI   │
└──────────────────────────┘    └──────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COHERENCY GATE (VALIDATION)                            │
│                                                                             │
│  Script: scripts/tools/coherency_gate.py                                    │
│                                                                             │
│  CHECKS (on generated artifacts):                                           │
│  □ CG-001: Every ui_plan panel with expected_capability has scenario        │
│  □ CG-002: Every scenario references existing ui_plan panel                 │
│  □ CG-003: No orphan scenarios                                              │
│  □ CG-004: Capability registry entries consistent                           │
│                                                                             │
│  DOES NOT: Read human intent (that's upstream)                              │
│  OUTPUT: PASS (proceed) or FAIL (block pipeline)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│  Capability Registry     │    │  SDSR Execution          │
│  (status tracking)       │    │  (verification)          │
└──────────────────────────┘    └──────────────────────────┘
              │                               │
              │     SDSR executes             │
              │     Observations emitted      │
              │◄──────────────────────────────┤
              │                               │
              │  AURORA_L2_apply_sdsr_        │
              │  observations.py              │
              │  (advances DECLARED→OBSERVED) │
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       compiler.py (DUMB, MECHANICAL)                        │
│                                                                             │
│  INPUTS (all generated, all coherent):                                      │
│  • ui_plan.yaml (structure)                                                │
│  • capability_registry/*.yaml (status)                                      │
│  • intents/*.yaml (panel details)                                          │
│                                                                             │
│  OUTPUT: ui_projection_lock.json                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (DUMB CONSUMER)                                 │
│                                                                             │
│  • Loads projection ONLY                                                   │
│  • NO scaffolding (DELETED)                                                │
│  • NO invention                                                            │
│  • Missing projection = HARD FAIL                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Intent Ledger is the ONLY Human Surface

Humans author `INTENT_LEDGER.md` in natural language. All YAMLs are generated.

Benefits:
- Single file to maintain
- Natural language is expressive
- AI can assist with generation
- No sync problem between structure and verification

### 2. YAMLs are Compiled Artifacts

`ui_plan.yaml`, capability registry, SDSR scenarios are all **generated outputs**, not human sources.

| Artifact | Old Model | New Model |
|----------|-----------|-----------|
| `ui_plan.yaml` | Human-edited | Generated from ledger |
| Capability registry | Human-edited | Generated from ledger |
| SDSR scenarios | Human-edited | Generated from ledger |
| Intent YAMLs | Human-edited | Generated from ledger |

### 3. Coherency Gate Validates Generated Artifacts

The coherency gate still exists but validates the generated artifacts, not human sources. It catches generation bugs, not human sync errors.

### 4. Compiler Remains Dumb

Compiler does NOT read intent ledger. It only reads generated YAMLs. This preserves mechanical purity.

### 5. Frontend Scaffolding Deleted Entirely

No fallback. No invention. Projection missing = hard fail.

---

## Intent Ledger Format (Proposed)

```markdown
# INTENT_LEDGER.md

## Structure Declarations

### Panel: INC-AI-SUM-O1
- **Domain:** Incidents
- **Subdomain:** AI Analysis
- **Topic:** Summary
- **Panel Class:** interpretation
- **Order:** O1
- **Expected Capability:** summary.incidents

### Panel: POL-PR-PP-O2
- **Domain:** Policies
- **Subdomain:** Proposals
- **Topic:** Pending Policies
- **Panel Class:** action
- **Order:** O2
- **Expected Capability:** APPROVE

---

## Verification Bindings

### Capability: summary.incidents
- **Panel:** INC-AI-SUM-O1
- **SDSR Scenario:** SDSR-HIL-INC-SUM-001
- **Acceptance Criteria:**
  - Summary reflects actual incident counts
- **Status:** VERIFIED (2026-01-14)

### Capability: APPROVE
- **Panel:** POL-PR-PP-O2
- **SDSR Scenario:** SDSR-E2E-004
- **Acceptance Criteria:**
  - policy_proposal.status: PENDING → APPROVED
- **Status:** VERIFIED (2026-01-11)

---

## Pending Work

### Capability: summary.activity
- **Panel:** ACT-EX-SUM-O1
- **SDSR Scenario:** (not yet written)
- **Status:** PENDING
```

---

## Implementation Checklist

### New Artifacts to Create

| # | Artifact | Location | Purpose |
|---|----------|----------|---------|
| 1 | `INTENT_LEDGER.md` | `design/l2_1/` | Human intent source |
| 2 | `sync_from_intent_ledger.py` | `scripts/tools/` | Generate YAMLs from ledger |
| 3 | `coherency_gate.py` | `scripts/tools/` | Validate generated artifacts |
| 4 | `AURORA_L2_apply_sdsr_observations.py` | `scripts/tools/` | Observation → status |
| 5 | `observations/` directory | `backend/scripts/sdsr/` | Store observation JSONs |

### Artifacts to Modify

| # | Artifact | Change |
|---|----------|--------|
| 6 | `ui_projection_loader.ts` | Remove scaffolding fallback |
| 7 | `ui_plan_scaffolding.ts` | **DELETE ENTIRELY** |
| 8 | `DomainPage.tsx` | Remove scaffolding imports |
| 9 | `run_aurora_l2_pipeline.sh` | Add coherency gate step |

### CI Changes

| # | Workflow | Change |
|---|----------|--------|
| 10 | `coherency-gate.yml` | New workflow: block on coherency failure |

---

## GPT Analysis Incorporated

| GPT Critique | Assessment | Resolution |
|--------------|------------|------------|
| Humans can't maintain two YAMLs | **VALID** | Intent Ledger as single human surface |
| YAMLs should be compiled artifacts | **VALID** | All YAMLs generated from ledger |
| Coherency gate still needed | **AGREED** | Validates generated artifacts |
| Frontend purge must be absolute | **AGREED** | No scaffolding, hard fail |

---

## Execution Order (When Approved)

```
Phase 1: Intent Ledger Bootstrap
├── Design INTENT_LEDGER.md format
├── Bootstrap from existing ui_plan + scenarios
└── Create initial ledger

Phase 2: Generation Pipeline
├── Create sync_from_intent_ledger.py
├── Validate generated artifacts match existing
└── Iterate until generation is correct

Phase 3: Observation Pipeline
├── Create AURORA_L2_apply_sdsr_observations.py
├── Create observations directory
└── Wire into pipeline

Phase 4: Frontend Cleanup
├── Delete ui_plan_scaffolding.ts
├── Modify ui_projection_loader.ts (remove fallback)
└── Modify DomainPage.tsx (remove scaffolding imports)

Phase 5: CI Integration
├── Add coherency-gate.yml workflow
└── Add generation validation to CI

Phase 6: Verification
├── Run full pipeline
├── Verify projection is clean
└── Verify frontend renders without scaffolding
```

---

## Open Questions (For Human Decision)

1. **Ledger format:** Markdown as proposed, or structured YAML with NL fields?
2. **Generation workflow:** Script-driven or AI-assisted (Claude/GPT)?
3. **Bootstrap strategy:** Generate from existing artifacts or start fresh?
4. **Orphan handling:** ERROR or WARNING for validation failures?

---

## References

- Molecular Pipeline Analysis (conversation)
- GPT review: Valid critiques incorporated
- Related: `CAPABILITY_STATUS_MODEL.yaml` (4-state model)
- Related: `UI_AS_CONSTRAINT_V1.md` (UI plan authority)

---

## Status

**DESIGN COMPLETE — AWAITING HUMAN APPROVAL**

Implementation blocked until:
- [ ] Human reviews and approves architecture
- [ ] Open questions resolved
- [ ] Execution order confirmed
