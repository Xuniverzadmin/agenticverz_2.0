# PIN-387: Canonical Projection Design Implementation

**Status:** COMPLETE
**Category:** Architecture / AURORA_L2 / UI Pipeline
**Created:** 2026-01-10
**Milestone:** Canonical Design Implementation (Phases 0-5)

## Summary

Complete implementation of the canonical UI projection design for the AURORA_L2 → SDSR → UI pipeline. This PIN documents the five-phase implementation that establishes a single, authoritative projection schema with full contract enforcement.

## Core Invariants

1. **Authority is declared, never inferred** (DB_AUTHORITY)
2. **UI consumes projection verbatim** (no inference, no fallbacks)
3. **Single source of truth** (`design/l2_1/ui_contract/ui_projection_lock.json`)
4. **Capabilities are not real because backend says so** — they are real only when the system demonstrates them (SDSR)

## Implementation Phases

### Phase 0: DB_AUTHORITY Enforcement ✓

**Files Modified:**
- `backend/aurora_l2/compiler.py` (lines 47-60)
- `scripts/tools/run_aurora_l2_pipeline.sh`

**Changes:**
- Compiler hard-fails if `DB_AUTHORITY` not declared
- Pipeline script enforces at shell level before any stage runs
- Authority written to `_meta.db_authority` in projection

**Enforcement:**
```python
DB_AUTHORITY = os.environ.get("DB_AUTHORITY")

def enforce_db_authority():
    if not DB_AUTHORITY:
        print("[FATAL] DB_AUTHORITY not declared.", file=sys.stderr)
        sys.exit(1)
    if DB_AUTHORITY not in ("neon", "local"):
        print(f"[FATAL] Invalid DB_AUTHORITY: {DB_AUTHORITY}", file=sys.stderr)
        sys.exit(1)
```

---

### Phase 1: Projection Canonicalization ✓

**Phase 1.1: Canonical Schema**

Added full schema to projection:
- `_meta`: Generator info, db_authority, frozen state, contract version
- `_statistics`: Panel/control/binding counts
- `_contract`: UI renderer constraints (no inference, explicit ordering)
- `domains[]`: Domain → Panel hierarchy

**Phase 1.2: Single File Output**

- Canonical source: `design/l2_1/ui_contract/ui_projection_lock.json`
- Pipeline copies verbatim to `public/projection/`
- No merge scripts, no adapters, no dual formats

**Phase 1.3: Obsolete Artifact Cleanup**

Removed:
- `design/l2_1/exports/AURORA_L2_UI_PROJECTION_LOCK.json`

Result: Exactly **one** projection file in the system.

---

### Phase 2: Panel Display Order ✓

**Files Modified:**
- `backend/aurora_l2/compiler.py` (lines 441-507)

**New Fields:**
- `panel_display_order`: Global sequential ordering (0-53)
- `topic_display_order`: Per-domain topic ordering (1, 2, 3...)

**Contract Updates:**
```json
"_contract": {
  "panel_display_order_required": true,
  "topic_display_order_required": true,
  "ordering_semantic": "numeric_only"
}
```

**Ordering Logic:**
- Panels sorted by O-level (O1 → O2 → O3 → O4 → O5)
- `panel_display_order` assigned globally across domains
- `topic_display_order` tracks unique subdomain::topic combinations per domain

---

### Phase 3: Content Blocks ✓

**Files Modified:**
- `backend/aurora_l2/compiler.py` (lines 513-610)

**New Structure:**
Each panel now has `content_blocks[]` defining in-panel layout:

| Block Type | Components | Present On |
|------------|------------|------------|
| HEADER | title, status_badge, binding_indicator | All panels |
| DATA | primary_display, ranking_indicator, filter_bar | All panels |
| CONTROLS | action_bar, bulk_actions | Panels with controls |
| FOOTER | replay_link, export_button, timestamp | All panels |

**Block Properties:**
- `type`: HEADER, DATA, CONTROLS, FOOTER
- `order`: Display order within panel (0, 1, 2, 3)
- `visibility`: ALWAYS or HIDDEN (based on binding_status)
- `enabled`: Whether block is interactive
- `components`: List of UI components

**Statistics:**
- HEADER: 54 (all panels)
- DATA: 54 (all panels)
- CONTROLS: 38 (panels with controls)
- FOOTER: 54 (all panels)

---

### Phase 4: SDSR Trace Finalization ✓

**Files Modified:**
- `backend/aurora_l2/compiler.py` (lines 274-275, 409-437, 490-497, 533-536, 550-551)

**New Fields in Compiled Intents:**
- `observation_trace`: Array from intent YAML (SDSR observation provenance)

**Enhanced `binding_metadata` for BOUND Panels:**
```json
"binding_metadata": {
  "scenario_ids": ["SDSR-TEST-001"],
  "observed_at": "2026-01-10T15:00:00Z",
  "capability_ids": ["APPROVE"],
  "trace_count": 1,
  "observed_effects": [
    {
      "entity": "policy_proposal",
      "field": "status",
      "from": "PENDING",
      "to": "APPROVED"
    }
  ]
}
```

**New Statistics:**
```json
"_statistics": {
  "sdsr_trace_count": 1,
  "panels_with_traces": 1,
  "unique_scenario_count": 1
}
```

**Contract Updates:**
```json
"_contract": {
  "binding_metadata_on_bound_panels": true,
  "sdsr_trace_provenance": true
}
```

---

### Phase 5: Contract Enforcement ✓

**Files Created:**
- `scripts/ci/validate_projection_contract.py`
- `.github/workflows/projection-contract.yml`

**Validator Checks:**
1. `_meta` block: type, generator, db_authority, frozen, editable
2. `_statistics` block: all counts including SDSR traces
3. `_contract` block: all required flags set to true
4. Domains structure: required fields
5. Panel structure: all 17 required fields
6. Ordering: unique sequential `panel_display_order`
7. Content blocks: HEADER, DATA, FOOTER required
8. Binding metadata: present on all BOUND panels
9. SDSR traces: statistics match actual trace counts

**CI Workflow Triggers:**
- Push/PR to main, develop
- Changes to `design/l2_1/**`, `backend/aurora_l2/**`, `scripts/tools/run_aurora_l2_pipeline.sh`

**CI Jobs:**
1. `validate-projection`: Run contract validator, verify DB_AUTHORITY, check frozen state
2. `regenerate-check`: Verify projection regeneration is stable

---

## Final Schema

```json
{
  "_meta": {
    "type": "ui_projection_lock",
    "version": "1.0.0",
    "generator": "AURORA_L2_COMPILER",
    "generator_version": "2.0.0",
    "db_authority": "neon",
    "contract_version": "ui_projection@2.0",
    "processing_stage": "LOCKED",
    "frozen": true,
    "editable": false
  },
  "_statistics": {
    "domain_count": 5,
    "panel_count": 54,
    "control_count": 101,
    "bound_panels": 1,
    "draft_panels": 5,
    "info_panels": 48,
    "unbound_panels": 0,
    "sdsr_trace_count": 1,
    "panels_with_traces": 1,
    "unique_scenario_count": 1
  },
  "_contract": {
    "renderer_must_consume_only_this_file": true,
    "no_optional_fields": true,
    "explicit_ordering_everywhere": true,
    "all_controls_have_type": true,
    "all_panels_have_render_mode": true,
    "all_items_have_visibility": true,
    "binding_status_required": true,
    "ordering_semantic": "numeric_only",
    "panel_display_order_required": true,
    "topic_display_order_required": true,
    "content_blocks_required": true,
    "binding_metadata_on_bound_panels": true,
    "sdsr_trace_provenance": true,
    "ui_must_not_infer": true
  },
  "domains": [...]
}
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/aurora_l2/compiler.py` | Canonical projection generator |
| `scripts/tools/run_aurora_l2_pipeline.sh` | Pipeline orchestration |
| `design/l2_1/ui_contract/ui_projection_lock.json` | Canonical projection (source of truth) |
| `website/app-shell/public/projection/ui_projection_lock.json` | Frontend copy (verbatim) |
| `scripts/ci/validate_projection_contract.py` | Contract validator |
| `.github/workflows/projection-contract.yml` | CI enforcement |

---

## Usage

**Run Pipeline:**
```bash
DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh
```

**Validate Contract:**
```bash
python3 scripts/ci/validate_projection_contract.py --verbose --check-public
```

**Apply SDSR Observations:**
```bash
python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py \
    --observation sdsr/observations/SDSR_OBSERVATION_*.json
```

---


---

## Status

### Update (2026-01-10)

COMPLETE

## Related PINs

- PIN-370: SDSR - Scenario Driven System Realization
- PIN-371: SDSR UI Pipeline Integration
- PIN-386: SDSR AURORA L2 Observation Schema Contract
- PIN-385: SDSR UI Pipeline Integration Status

---

## Validation Results

```
============================================================
VALIDATION SUMMARY
============================================================
Errors:   0
Warnings: 0

✓ All contract validations PASSED
✓ Public projection matches canonical
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-10 | Phase 0: DB_AUTHORITY enforcement |
| 2026-01-10 | Phase 1: Canonical schema implementation |
| 2026-01-10 | Phase 2: Panel display order |
| 2026-01-10 | Phase 3: Content blocks |
| 2026-01-10 | Phase 4: SDSR trace finalization |
| 2026-01-10 | Phase 5: Contract enforcement CI |
