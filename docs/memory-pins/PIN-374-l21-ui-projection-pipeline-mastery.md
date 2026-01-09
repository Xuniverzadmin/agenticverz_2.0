# PIN-374: L2.1 UI Projection Pipeline Mastery

**Status:** ✅ COMPLETE
**Created:** 2026-01-09
**Category:** UI Architecture / Pipeline

---

## Summary

Canonical pipeline for UI panel creation: Intent CSV → Supertable → Projection → UI. Behavioral gate BL-UI-PIPELINE-001 prevents violations.

---

## Details

## Problem

Claude was editing projection files directly and adding UI panels without proper L2.1 intent backing. This violated the design-first architecture.

## Root Cause

The UI pipeline was not fully understood:
- Projection files are GENERATED, not edited
- Intent must be declared in CSV first
- Pipeline stages must run in order

## Solution

### Canonical Pipeline Flow

```
L2_1_UI_INTENT_SUPERTABLE.csv  ← EDIT HERE (source of truth)
        ↓
l2_pipeline.py generate v{N}   ← generates Excel supertable
        ↓
l2_raw_intent_parser.py        ← Excel → ui_intent_ir_raw.json
        ↓
intent_normalizer.py           ← → ui_intent_ir_normalized.json
        ↓
surface_to_slot_resolver.py    ← → ui_intent_ir_slotted.json
        ↓
intent_compiler.py             ← → ui_intent_ir_compiled.json
        ↓
ui_projection_builder.py       ← → ui_projection_lock.json
        ↓
Copy to public/projection/     ← Frontend reads from here
        ↓
PanelContentRegistry.tsx       ← ONLY NOW add renderers
```

### Behavioral Gate Added

BL-UI-PIPELINE-001 in CLAUDE.md blocks:
- Adding UI panels without projection backing
- Editing projection files directly
- Skipping pipeline stages

### Key Artifacts

| Artifact | Location |
|----------|----------|
| Intent CSV (SOURCE) | design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv |
| Pipeline Script | scripts/tools/l2_pipeline.py |
| Projection Lock | design/l2_1/ui_contract/ui_projection_lock.json |
| Panel Registry | src/components/panels/PanelContentRegistry.tsx |

## Invariant

> UI renders projection. UI does not bypass projection.

## Reference

- PIN-352 (L2.1 UI Projection Pipeline)
- PIN-370 (SDSR UI Architecture)
- CLAUDE.md Section: BL-UI-PIPELINE-001

---

## Related PINs

- [PIN-352](PIN-352-.md)
- [PIN-370](PIN-370-.md)
