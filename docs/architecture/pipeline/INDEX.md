# Pipeline Documentation Index

**Status:** ACTIVE
**Last Updated:** 2026-01-16

---

## Overview

This directory contains consolidated documentation for the AURORA L2 pipeline components:
- HISAR (Execution Doctrine)
- SDSR (System Realization)
- Semantic Validator (Authority Enforcement)
- AURORA L2 (UI Intent Pipeline)

---

## Pipeline Flow

```
Human Intent
     ↓
┌─────────────────────────────────────────────────────────────┐
│  HISAR: Human Intent → SDSR → Aurora → Rendering            │
│                                                             │
│  docs/governance/HISAR.md                                   │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│  SDSR: Scenario-Driven System Realization                   │
│                                                             │
│  "API works?" (Operational Truth)                           │
│                                                             │
│  docs/governance/SDSR.md                                    │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│  SEMANTIC VALIDATOR: Authority Enforcement Gate             │
│                                                             │
│  "Data correct for panel?" (Semantic Truth)                 │
│                                                             │
│  docs/architecture/pipeline/SEMANTIC_VALIDATOR.md  ◄── HERE │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│  AURORA L2: UI Intent Pipeline                              │
│                                                             │
│  Compilation → Projection → Rendering                       │
│                                                             │
│  design/l2_1/AURORA_L2.md                                   │
└─────────────────────────────────────────────────────────────┘
     ↓
Rendered UI (Truth-Grade)
```

---

## Documents

### In This Directory

| Document | Purpose |
|----------|---------|
| [SEMANTIC_VALIDATOR.md](SEMANTIC_VALIDATOR.md) | Semantic authority enforcement between SDSR and Aurora |

### Related Documents (Other Locations)

| Document | Location | Purpose |
|----------|----------|---------|
| HISAR.md | `docs/governance/HISAR.md` | Execution doctrine |
| SDSR.md | `docs/governance/SDSR.md` | System realization methodology |
| AURORA_L2.md | `design/l2_1/AURORA_L2.md` | UI intent pipeline specification |

### Supporting Documents

| Document | Location | Purpose |
|----------|----------|---------|
| SDSR_SYSTEM_CONTRACT.md | `docs/governance/` | SDSR system contract |
| SDSR_PIPELINE_CONTRACT.md | `docs/governance/` | SDSR pipeline contract |
| SDSR_E2E_TESTING_PROTOCOL.md | `docs/governance/` | E2E testing protocol |
| HISAR_UI_PLAN_SYNC.md | `docs/architecture/` | UI plan sync mechanism |
| HISAR_BACKEND_GAPS_TRACKER.md | `docs/tracking/` | Backend gaps dashboard |

---

## Phase Mapping

| HISAR Phase | Component | Document |
|-------------|-----------|----------|
| Phase 1-2 | Human Intent | HISAR.md |
| Phase 3 | Capability Declaration | HISAR.md, AURORA_L2.md |
| Phase 3.5 | Coherency Gate | HISAR.md |
| Phase 4 | SDSR Verification | SDSR.md |
| Phase 5 | Observation Application | SDSR.md, AURORA_L2.md |
| Phase 5.5 | Trust Evaluation | HISAR.md |
| **Phase 5.7** | **Semantic Validation** | **SEMANTIC_VALIDATOR.md** |
| Phase 6 | Aurora Compilation | AURORA_L2.md |
| Phase 6.5 | UI Plan Bind | HISAR.md |
| Phase 7 | Projection Diff Guard | HISAR.md |
| Phase 8 | Rendering | HISAR.md, AURORA_L2.md |

---

## Implementation Files

### Semantic Validator

| File | Purpose |
|------|---------|
| `backend/app/services/ai_console_panel_adapter/semantic_validator.py` | Main validator class |
| `backend/app/services/ai_console_panel_adapter/semantic_types.py` | Type definitions |
| `backend/app/services/ai_console_panel_adapter/semantic_failures.py` | Failure taxonomy |
| `backend/app/services/ai_console_panel_adapter/panel_signal_translator.py` | Signal translations |
| `backend/app/services/ai_console_panel_adapter/panel_signal_collector.py` | Integration point |

### HISAR/SDSR/Aurora

| File | Purpose |
|------|---------|
| `scripts/tools/run_hisar.sh` | HISAR canonical runner |
| `backend/scripts/sdsr/inject_synthetic.py` | SDSR injection script |
| `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` | Aurora compiler |
| `scripts/tools/AURORA_L2_apply_sdsr_observations.py` | Observation applier |

---

## Memory PINs

| PIN | Topic |
|-----|-------|
| PIN-370 | SDSR System Contract |
| PIN-420 | Semantic Authority and First SDSR Binding |
| PIN-422 | HISAR Execution Doctrine |
| PIN-394 | SDSR-Aurora One-Way Causality Pipeline |

---

## Quick Reference

### The Core Question Each Component Answers

| Component | Question |
|-----------|----------|
| **HISAR** | How does intent become rendered UI? |
| **SDSR** | Does the API work? |
| **Semantic Validator** | Is the data correct for this panel? |
| **AURORA L2** | How is the UI projection built? |

### The Truth Progression

```
Intent (what SHOULD exist)
        ↓
SDSR (what DOES exist - operational)
        ↓
Semantic Validator (data CORRECT for panel - semantic)
        ↓
Aurora (compilation)
        ↓
UI (truth-grade rendering)
```
