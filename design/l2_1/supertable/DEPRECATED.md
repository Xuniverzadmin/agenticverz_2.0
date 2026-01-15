# DEPRECATED — Supertable Directory

**Status:** DEPRECATED (2026-01-14)
**Replaced By:** `design/l2_1/intents/*.yaml`
**Reference:** `design/l2_1/AURORA_L2.md`, PIN-370, PIN-379

---

## Warning

This directory and its contents are **DEPRECATED** and should not be used.

The CSV-based L2.1 intent pipeline has been replaced by the AURORA L2 SDSR-driven pipeline.

## What Was Here

- `L2_1_UI_INTENT_SUPERTABLE.csv` — The original source of truth for UI intents
- `l2_supertable_manifest.json` — Version tracking for supertable
- `l2_supertable_v*_cap_expanded.xlsx` — Generated Excel versions

## What Replaced It

| Legacy Artifact | Current Replacement |
|-----------------|---------------------|
| `L2_1_UI_INTENT_SUPERTABLE.csv` | `design/l2_1/intents/*.yaml` |
| `l2_supertable_manifest.json` | `design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml` |
| Excel versions | Not needed (YAML is directly consumed) |

## Current Pipeline

```
SDSR Scenario YAML (Human Intent Entry)
        ↓
inject_synthetic.py --wait
        ↓
SDSR_OBSERVATION_*.json
        ↓
AURORA_L2_apply_sdsr_observations.py
        ↓
backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml
design/l2_1/intents/*.yaml
        ↓
backend/aurora_l2/SDSR_UI_AURORA_compiler.py
        ↓
design/l2_1/ui_contract/ui_projection_lock.json
```

## Do Not Use

The following scripts are DEPRECATED and will error if run:

- `scripts/tools/l2_pipeline.py` — DEPRECATED
- `scripts/tools/l2_raw_intent_parser.py` — DEPRECATED
- `scripts/tools/run_l2_pipeline.sh` — DEPRECATED
- `scripts/tools/intent_normalizer.py` — DEPRECATED
- `scripts/tools/surface_to_slot_resolver.py` — DEPRECATED

## Use Instead

```bash
./scripts/tools/run_aurora_l2_pipeline.sh
```

Requires `DB_AUTHORITY=neon` environment variable.

---

**This directory is preserved for historical reference only.**
