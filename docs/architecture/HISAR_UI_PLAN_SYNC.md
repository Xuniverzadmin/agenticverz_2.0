# HISAR UI Plan Sync Architecture

**Status:** ACTIVE
**Created:** 2026-01-15
**Reference:** PIN-425

---

## Overview

This document describes the sync mechanism between the HISAR pipeline and `ui_plan.yaml`, ensuring the canonical source of truth stays in sync with pipeline execution results.

---

## The Problem: Sync Gap

### What Was Happening

Before Phase 6.5, the HISAR pipeline updated multiple artifacts but **not** `ui_plan.yaml`:

```
HISAR Pipeline (Before)
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  Phase 5: Apply Observation                                         │
│  ├── Intent YAML ✅ Updated (capability.status → OBSERVED)          │
│  └── Capability YAML ✅ Updated (status → OBSERVED)                 │
│                                                                     │
│  Phase 6: Aurora Compilation                                        │
│  └── Projection Lock ✅ Compiled                                    │
│                                                                     │
│  Phase 8: Rendering                                                 │
│  └── Public Projection ✅ Copied                                    │
│                                                                     │
│  ❌ ui_plan.yaml NOT UPDATED                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Impact

`ui_plan.yaml` is the **canonical source of truth** for panel states. When out of sync:

| Problem | Effect |
|---------|--------|
| Progress Tracking | Shows 83 EMPTY when actual is 79 EMPTY, 4 BOUND |
| Developer Confusion | Source of truth disagrees with actual state |
| Automation Gaps | Scripts relying on ui_plan.yaml see stale data |
| CI/CD | Validation checks may use wrong baseline |

---

## The Solution: Phase 6.5

### New Phase Added

```
HISAR Pipeline (After)
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  Phase 6: Aurora Compilation                                        │
│  └── Projection Lock ✅ Compiled                                    │
│                                                                     │
│  Phase 6.5: UI Plan Bind (NEW)                                      │
│  └── ui_plan.yaml ✅ Updated                                        │
│      ├── state: EMPTY → BOUND                                       │
│      ├── intent_spec: → design/l2_1/intents/AURORA_L2_INTENT_{panel_id}.yaml │
│      └── expected_capability: → {capability_id}                     │
│                                                                     │
│  Phase 7: Projection Diff Guard                                     │
│  └── Validates projection                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Note:** Intent YAMLs use the naming convention `AURORA_L2_INTENT_{panel_id}.yaml` (generated from `INTENT_LEDGER.md`).

### Script: `aurora_ui_plan_bind.py`

**Location:** `backend/aurora_l2/tools/aurora_ui_plan_bind.py`

**Execution Contract:**

1. **Pre-requisites:**
   - Intent YAML must exist
   - Capability must be OBSERVED or TRUSTED

2. **Actions:**
   - Updates panel entry in ui_plan.yaml
   - Sets state to BOUND
   - Links intent_spec and expected_capability

3. **Properties:**
   - IDEMPOTENT: Safe to run multiple times
   - ATOMIC: Updates single panel entry
   - FAIL-SAFE: Does not modify if pre-requisites fail

---

## Data Flow

### Before Phase 6.5 (Sync Gap)

```
Intent YAML ──────────────┬──────────────────────────────────────────▶ UPDATED
                          │
Capability YAML ──────────┼──────────────────────────────────────────▶ UPDATED
                          │
                          ▼
                    SDSR Observation ───▶ Compiler ───▶ Projection ───▶ UPDATED
                          │
ui_plan.yaml ◀────────────┴─────────────────────────────────────────── NOT UPDATED
```

### After Phase 6.5 (Sync Closed)

```
Intent YAML ──────────────┬──────────────────────────────────────────▶ UPDATED
                          │
Capability YAML ──────────┼──────────────────────────────────────────▶ UPDATED
                          │
                          ▼
                    SDSR Observation ───▶ Compiler ───▶ Projection ───▶ UPDATED
                          │
                          ▼
                    aurora_ui_plan_bind.py
                          │
ui_plan.yaml ◀────────────┴─────────────────────────────────────────── UPDATED
```

---

## Artifact Relationships

```
┌──────────────────────────────────────────────────────────────────────┐
│                   PRIMARY SOURCE OF TRUTH                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  INTENT_LEDGER.md (Human Intent)                               │  │
│  │  - Panel definitions                                           │  │
│  │  - Panel classifications (evidence/interpretation/execution)   │  │
│  │  - Domain → Subdomain → Topic → Panel hierarchy                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              │ sync_from_intent_ledger.py            │
│                              ▼                                       │
│  ┌─────────────────────────────────┬──────────────────────────────┐  │
│  │                                 │                              │  │
│  │  ui_plan.yaml                   │  Intent YAMLs               │  │
│  │  - Panel states                 │  - AURORA_L2_INTENT_*.yaml  │  │
│  │  - Hierarchy                    │  - Panel definitions        │  │
│  │                                 │  - Capability refs          │  │
│  └─────────────────────────────────┴──────────────────────────────┘  │
│                              │                                       │
│                              │ Phase 6.5: aurora_ui_plan_bind.py     │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Intent YAML (design/l2_1/intents/AURORA_L2_INTENT_*.yaml)     │  │
│  │  - Panel definition                                            │  │
│  │  - Capability reference                                        │  │
│  │  - SDSR verification status                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              │ Phase 5: aurora_apply_observation.py  │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Capability YAML (AURORA_L2_CAPABILITY_{id}.yaml)              │  │
│  │  - Capability status (DECLARED, OBSERVED, TRUSTED)             │  │
│  │  - Observation trace                                           │  │
│  │  - Coherency verification                                      │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Usage

### Single Panel

```bash
# Bind a single panel after HISAR
python3 backend/aurora_l2/tools/aurora_ui_plan_bind.py --panel OVR-SUM-HL-O4

# Preview (dry run)
python3 backend/aurora_l2/tools/aurora_ui_plan_bind.py --panel OVR-SUM-HL-O4 --dry-run
```

### Via run_hisar.sh

```bash
# Phase 6.5 is automatically invoked
./scripts/tools/run_hisar.sh OVR-SUM-HL-O4
```

---

## Verification

### Check ui_plan.yaml State

```bash
# After HISAR, verify the panel is BOUND
grep -A5 "panel_id: OVR-SUM-HL-O4" design/l2_1/ui_plan.yaml

# Expected output:
# - panel_id: OVR-SUM-HL-O4
#   slot: 4
#   panel_class: interpretation
#   state: BOUND
#   intent_spec: design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O4.yaml
#   expected_capability: overview.policy_snapshot
```

### Count Bound Panels

```bash
# Count panel states
grep "state:" design/l2_1/ui_plan.yaml | sort | uniq -c

# Example output:
#   4 state: BOUND
#  83 state: EMPTY
```

---

## Error Handling

### Capability Not OBSERVED

```
ERROR: Capability status is DECLARED, must be OBSERVED or TRUSTED
Hint: Run SDSR first to observe the capability
```

**Resolution:** Run phases 4-5 first to observe the capability via SDSR.

### Intent YAML Missing

```
ERROR: Intent YAML not found for OVR-SUM-HL-O5
Path: design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O5.yaml
```

**Resolution:**
1. Add panel to `INTENT_LEDGER.md` (primary source of truth)
2. Run `python3 scripts/tools/sync_from_intent_ledger.py` to generate the intent YAML
3. Or use `aurora_intent_scaffold.py` for manual creation

### Panel Not in ui_plan.yaml

```
ERROR: Panel OVR-SUM-HL-O5 not found in ui_plan.yaml
```

**Resolution:** The panel must be declared in ui_plan.yaml topology first.

---

## References

- **PIN-425:** UI Plan Sync Closure
- **PIN-422:** HISAR Execution Doctrine
- **Script:** `backend/aurora_l2/tools/aurora_ui_plan_bind.py`
- **Ledger Sync:** `scripts/tools/sync_from_intent_ledger.py`
- **Primary Source of Truth:** `design/l2_1/INTENT_LEDGER.md`
- **Derived Source:** `design/l2_1/ui_plan.yaml`
- **Intent Naming:** `AURORA_L2_INTENT_{panel_id}.yaml`
