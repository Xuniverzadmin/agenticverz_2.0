# PIN-425: UI Plan Sync Closure

**Status:** COMPLETE
**Created:** 2026-01-15
**Category:** UI Pipeline / Automation
**Milestone:** AURORA L2
**Related PINs:** PIN-422, PIN-423, PIN-424

---

## Summary

Added Phase 6.5 to the HISAR pipeline to close the sync gap between SDSR observation and `ui_plan.yaml`.

---

## The Problem

### Sync Gap Discovered

During HISAR execution for OVR-SUM-HL-O3 and O4, we discovered that `ui_plan.yaml` was not being updated even after successful SDSR observation and projection compilation.

**What HISAR Updated:**

| Artifact | Updated By | Status |
|----------|------------|--------|
| Intent YAML | `aurora_apply_observation.py` | Updated |
| Capability YAML | `aurora_apply_observation.py` | Updated (OBSERVED) |
| Projection Lock | `SDSR_UI_AURORA_compiler.py` | Compiled |
| Public Projection | `cp` | Copied |
| **ui_plan.yaml** | **NOTHING** | **NOT UPDATED** |

### Impact

`ui_plan.yaml` is the **canonical source of truth** for panel state. When it's out of sync:

1. **False Progress Picture**: Shows 83 EMPTY when actual is 79 EMPTY, 4 BOUND
2. **Developer Confusion**: Source of truth disagrees with pipeline output
3. **Automation Gaps**: Scripts relying on ui_plan.yaml see stale state

---

## The Solution

### New Phase: 6.5 UI Plan Bind

Created `aurora_ui_plan_bind.py` to run after Aurora compilation, before Projection Diff Guard.

```
Phase 6    Aurora Compilation     → Compiles projection
Phase 6.5  UI Plan Bind           → Syncs ui_plan.yaml  ← NEW
Phase 7    Projection Diff Guard  → Validates projection
Phase 8    Rendering              → Copies to public/
```

### Script: `aurora_ui_plan_bind.py`

**Location:** `backend/aurora_l2/tools/aurora_ui_plan_bind.py`

**What It Does:**

1. Loads intent YAML for the panel
2. Verifies capability is OBSERVED or TRUSTED
3. Updates `ui_plan.yaml`:
   - `state`: EMPTY → BOUND
   - `intent_spec`: Path to intent YAML
   - `expected_capability`: Capability ID
4. Validates update succeeded

**Usage:**

```bash
# Single panel
python aurora_ui_plan_bind.py --panel OVR-SUM-HL-O4

# Dry run (preview changes)
python aurora_ui_plan_bind.py --panel OVR-SUM-HL-O4 --dry-run

# Verbose output
python aurora_ui_plan_bind.py --panel OVR-SUM-HL-O4 -v
```

**Execution Contract:**

- ONLY runs after successful SDSR observation (Phase 5)
- ONLY binds if capability status is OBSERVED or TRUSTED
- IDEMPOTENT: Safe to run multiple times
- ATOMIC: Updates single panel entry

---

## Changes Made

### 1. Created aurora_ui_plan_bind.py

```
backend/aurora_l2/tools/aurora_ui_plan_bind.py
```

Full automation script with:
- Intent YAML loading and validation
- Capability status verification
- ui_plan.yaml navigation and update
- Dry-run support
- Verbose output

### 2. Updated run_hisar.sh

Added Phase 6.5 between Phase 6 and Phase 7:

```bash
# Phase 6.5: UI Plan Bind
echo "▶ [A] Phase 6.5 — UI Plan Bind"

if [[ "$MODE" == "single" ]]; then
  python3 "$TOOLS_DIR/aurora_ui_plan_bind.py" --panel "$PANEL_ID"
else
  for intent in "$ROOT_DIR/design/l2_1/intents"/*.yaml; do
    panel=$(basename "$intent" .yaml)
    python3 "$TOOLS_DIR/aurora_ui_plan_bind.py" --panel "$panel" || true
  done
fi
```

Updated help text and summary to include Phase 6.5.

### 3. Updated PIN-422

Added Phase 6.5 documentation to HISAR Execution Doctrine:
- Phase list now shows 6.5
- Phase details section explains purpose
- Files table includes the new script
- References include this PIN

---

## Before and After

### Before (Sync Gap)

```
HISAR runs for OVR-SUM-HL-O4:
  Intent YAML      → Updated (capability.status: OBSERVED)
  Capability YAML  → Updated (status: OBSERVED)
  Projection       → Compiled (O4 panel visible)
  Public           → Copied
  ui_plan.yaml     → STILL SHOWS EMPTY  ← GAP!
```

### After (Sync Closed)

```
HISAR runs for OVR-SUM-HL-O4:
  Intent YAML      → Updated (capability.status: OBSERVED)
  Capability YAML  → Updated (status: OBSERVED)
  Projection       → Compiled (O4 panel visible)
  UI Plan          → Updated (state: BOUND)  ← CLOSED!
  Public           → Copied
```

---

## Verification

### Test the Script

```bash
# Dry run to see what would change
python3 backend/aurora_l2/tools/aurora_ui_plan_bind.py \
  --panel OVR-SUM-HL-O4 --dry-run

# Expected output:
# [DRY RUN] Binding panel: OVR-SUM-HL-O4
#   Intent YAML: Found
#   Capability ID: overview.policy_snapshot
#   Capability status: OBSERVED
#   Panel path: OVERVIEW.SUMMARY.HIGHLIGHTS
#   Current state: BOUND
#   [DRY RUN] Would update panel in ui_plan.yaml
```

### Full HISAR Run

```bash
./scripts/tools/run_hisar.sh OVR-SUM-HL-O5  # (when O5 exists)

# Should see:
# ▶ [A] Phase 6.5 — UI Plan Bind
# ──────────────────────────────────────────────────────────────────────
# Binding panel: OVR-SUM-HL-O5
#   Updating ui_plan.yaml:
#     state: EMPTY -> BOUND
#     intent_spec: null -> design/l2_1/intents/OVR-SUM-HL-O5.yaml
#     expected_capability: null -> overview.xxx
#   Updated ui_plan.yaml
# ✓ UI Plan synchronized
```

---

## Key Learnings

### 1. Source of Truth Must Be Updated

Every artifact that claims to be a source of truth must be updated by automation.
Manual updates are error-prone and unsustainable.

### 2. Pipeline Phases Must Be Complete

A pipeline is only as good as its weakest phase. Missing Phase 6.5 meant the
pipeline was incomplete even when it reported success.

### 3. Naming Matters

`aurora_ui_plan_bind.py` clearly indicates:
- **aurora_**: Part of AURORA L2 automation
- **ui_plan_**: Operates on ui_plan.yaml
- **bind**: Binds a panel (state → BOUND)

---

## Files

| File | Action | Purpose |
|------|--------|---------|
| `backend/aurora_l2/tools/aurora_ui_plan_bind.py` | CREATED | Phase 6.5 automation |
| `scripts/tools/run_hisar.sh` | UPDATED | Added Phase 6.5 call |
| `docs/memory-pins/PIN-422-hisar-execution-doctrine.md` | UPDATED | Documented Phase 6.5 |

---

## References

- PIN-422: HISAR Execution Doctrine
- PIN-423: HISAR OVR-SUM-HL-O3 Activity Snapshot
- PIN-424: HISAR OVR-SUM-HL-O4 Policy Snapshot
- `design/l2_1/ui_plan.yaml` — Canonical UI plan
- `backend/aurora_l2/tools/aurora_ui_plan_bind.py` — Phase 6.5 script
