---
paths:
  - "design/**"
  - "website/**"
---

# UI Pipeline & Constraint Rules

## AURORA L2 Pipeline (BL-UI-PIPELINE-001)

Before writing ANY UI code for panels:
1. Check panel_id in projection: design/l2_1/ui_contract/ui_projection_lock.json
2. Check intent YAML: design/l2_1/intents/{panel_id}.yaml
3. Check capability status: OBSERVED or TRUSTED (not DECLARED)
4. Run pipeline: ./scripts/tools/run_aurora_l2_pipeline.sh
5. Verify projection copied to public/
6. ONLY THEN add to PanelContentRegistry

### Canonical Pipeline Flow

```
SDSR Scenario YAML → inject_synthetic.py --wait → SDSR_OBSERVATION_*.json
→ AURORA_L2_apply_sdsr_observations.py → Capability Registry (DECLARED → OBSERVED)
→ SDSR_UI_AURORA_compiler.py → ui_projection_lock.json
→ cp → website/app-shell/public/projection/
→ Frontend renderer → PanelContentRegistry.tsx
```

### Capability Binding Status

| Capability Status | Panel State |
|-------------------|-------------|
| DECLARED | Disabled (claim ≠ truth) |
| OBSERVED | Enabled (demonstrated) |
| TRUSTED | Enabled (stable) |
| DEPRECATED | Hidden |

## UI-as-Constraint Doctrine (BL-UI-CONSTRAINT-001)

> The UI plan defines the surface. Backend and SDSR exist only to fill declared gaps.

Authority Stack (Non-Negotiable):
1. ui_plan.yaml (human constraint)
2. Intent registry
3. Capability registry
4. SDSR scenarios
5. Backend endpoints
6. Compiler/projection
7. Frontend renderer (dumb consumer)

If lower contradicts higher → lower is wrong.

### Panel States

| State | Meaning | Rendering |
|-------|---------|-----------|
| EMPTY | Intent YAML missing | Empty state UX |
| UNBOUND | Capability missing | Empty state UX |
| DRAFT | SDSR not observed | Disabled controls |
| BOUND | Capability observed | Full functionality |
| DEFERRED | Governance decision | Hidden or disabled |

## SDSR UI Architecture Gate (BL-SDSR-UI-001 to UI-004)

| Rule ID | Name |
|---------|------|
| SDSR-UI-001 | Routes Use DomainPage |
| SDSR-UI-002 | Data Binding via PanelContentRegistry |
| SDSR-UI-003 | Panel ID Registration Required |
| SDSR-UI-004 | Projection Structure Preserved |

## Source Chain Discovery (BL-SOURCE-CHAIN-001)

Never edit generated files directly. Edit the SOURCE, then run the GENERATOR.

Key chains:
- INTENT_LEDGER.md → sync_from_intent_ledger.py → intents/*.yaml, ui_plan.yaml
- intents/*.yaml → SDSR_UI_AURORA_compiler.py → ui_projection_lock.json
- ui_projection_lock.json → run_aurora_l2_pipeline.sh → public/projection/

## Customer Console Governance (v1 FROZEN)

Five frozen domains: Overview, Activity, Incidents, Policies, Logs.
Cannot rename, merge, or modify. Account is NOT a domain.
Sidebar never changes with order depth (O1-O5).

## Architecture Constraints (BL-ARCH-CONSTRAINT-001)

Autonomous Fix Zones (AUTO-A to D): SDSR failure, script error, terminology drift, panel render.
Hard Stop Zones (STOP-A to D): Add/remove panels, new lifecycle states, bypass PDG, interpretation panels.

## DEPRECATED Artifacts (DO NOT USE)

L2_1_UI_INTENT_SUPERTABLE.csv, l2_pipeline.py, l2_raw_intent_parser.py, intent_normalizer.py, surface_to_slot_resolver.py, run_l2_pipeline.sh, design/l2_1/supertable/
