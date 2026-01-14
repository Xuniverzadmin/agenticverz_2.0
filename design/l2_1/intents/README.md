# AURORA_L2 Intent Specs Directory

**Status:** CANONICAL (Source of Truth for UI Intents)
**Pipeline:** AURORA L2 (SDSR-Driven)
**Reference:** `design/l2_1/AURORA_L2.md`, PIN-370, PIN-379

---

## Purpose

This directory contains individual YAML intent spec files that define UI panels.
These files are the **source of truth** for the AURORA L2 pipeline.

## Pipeline Flow

```
design/l2_1/intents/*.yaml                 ← YOU ARE HERE (source of truth)
        ↓
backend/aurora_l2/compiler.py              ← Reads intents + capabilities
        ↓
design/l2_1/ui_contract/ui_projection_lock.json
        ↓
website/app-shell/public/projection/
        ↓
Frontend renderer
```

## File Naming Convention

```
{panel_id}.yaml
```

Examples:
- `POL-RU-O1.yaml` - Policy Rules Summary panel
- `POL-RU-O2.yaml` - Policy Rules List panel
- `INC-AI-OI-O2.yaml` - Open Incidents List panel

## Intent Spec Schema

```yaml
panel_id: POL-RU-O2
version: "1.0.0"

metadata:
  domain: POLICIES
  subdomain: RULES
  topic: ACTIVE_RULES
  order: O2
  migration_status: REVIEWED  # UNREVIEWED | REVIEWED

display:
  panel_name: "Policy Rules List"
  short_description: "List of active policy rules"
  expansion_mode: INLINE

data:
  endpoint: /api/v1/policy-rules
  capability: policies.rules.list

controls:
  - type: FILTER
    capability: policies.rules.filter
  - type: SORT
    capability: policies.rules.sort
  - type: NAVIGATE
    capability: policies.rules.navigate

visibility:
  enabled: true
  requires_permission: policies.rules.read

# Observation trace (appended by SDSR, never manually edited)
observation_trace: []
```

## Capability Binding

Each intent declares required capabilities. Panels are only enabled when capabilities
are **OBSERVED** (not just DECLARED). The capability lifecycle:

| Capability Status | Binding Status | Panel State |
|-------------------|----------------|-------------|
| DECLARED | DRAFT | Disabled |
| OBSERVED | BOUND | Enabled |
| TRUSTED | BOUND | Enabled |
| DEPRECATED | UNBOUND | Hidden |

## SDSR Integration

When an SDSR scenario successfully exercises a capability:

1. Observation is emitted: `SDSR_OBSERVATION_*.json`
2. `AURORA_L2_apply_sdsr_observations.py` runs
3. Capability advances: `DECLARED → OBSERVED`
4. Intent gets `observation_trace` appended (append-only, never edited)
5. Pipeline recompiles projection with updated binding status

## Migration Notes

All 55 CSV rows from the legacy `L2_1_UI_INTENT_SUPERTABLE.csv` were migrated here.
Each row became one YAML file with `migration_status: UNREVIEWED`.

The legacy CSV pipeline is **DEPRECATED**. Do not use:
- `design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv` (DEPRECATED)
- `scripts/tools/l2_pipeline.py` (DEPRECATED)
- `scripts/tools/run_l2_pipeline.sh` (DEPRECATED)

---

## Governance

- **DO NOT** edit intent YAMLs directly for capability observation (use SDSR)
- **DO NOT** edit `observation_trace` (append-only by SDSR applier)
- **DO** update `migration_status` to REVIEWED after human review
- **DO** refine semantics, controls, expansion modes during review
