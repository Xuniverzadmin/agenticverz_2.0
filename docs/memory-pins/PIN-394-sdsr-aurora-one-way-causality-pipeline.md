# PIN-394: SDSR-Aurora One-Way Causality Pipeline

**Status:** ✅ COMPLETE
**Created:** 2026-01-11
**Category:** SDSR / Pipeline Architecture
**Milestone:** Phase G Steady State

---

## Summary

Implemented clean one-way causality architecture for SDSR-Aurora pipeline. inject_synthetic.py now emits signal only, sdsr_observation_watcher.sh handles downstream orchestration.

---

## Details

## Overview

Refactored the SDSR-Aurora pipeline to enforce one-way causality, eliminating architectural overload in `inject_synthetic.py`.

## Problem Solved

GPT analysis identified that `inject_synthetic.py` was doing too much orchestration:
- Creating state
- Waiting for execution
- Observing effects
- Materializing truth
- **AND calling Aurora scripts directly** (architectural overload)

This violated the principle of separation of concerns and made the injector do downstream orchestration.

## Solution: Signal-Based Decoupling

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    SDSR LAYER (Upstream)                     │
│                                                              │
│  inject_synthetic.py                                         │
│    ├─ Creates state (tenant, agent, etc.)                   │
│    ├─ Waits for backend execution                            │
│    ├─ Observes effects                                       │
│    ├─ Calls Scenario_SDSR_output.py (materialize truth)     │
│    └─ Writes .sdsr_observation_ready signal  ◄── ONLY OUTPUT│
│                                                              │
│  DOES NOT: Call Aurora scripts directly                      │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼ signal file

┌──────────────────────────────────────────────────────────────┐
│              ORCHESTRATION LAYER (Downstream)                │
│                                                              │
│  sdsr_observation_watcher.sh (NEW)                          │
│    ├─ Detects .sdsr_observation_ready                        │
│    ├─ Calls apply_sdsr_observations.py                       │
│    │     └─ Updates capability registry                      │
│    │     └─ Writes .aurora_needs_preflight                   │
│    ├─ Calls run_aurora_l2_pipeline_preflight                 │
│    │     └─ Compiles Aurora                                  │
│    │     └─ Builds frontend (PREFLIGHT)                      │
│    │     └─ Deploys to dist-preflight/                       │
│    └─ Clears all signals                                     │
└──────────────────────────────────────────────────────────────┘
```

### Signal Flow

```
inject_synthetic.py → .sdsr_observation_ready → watcher → downstream
       │                                                       │
       │  (observation_path, scenario_id, class, count)       │
       │                                                       │
       └── NO direct calls to Aurora scripts ◄─────────────────┘
```

## Files Modified/Created

| File | Action | Role |
|------|--------|------|
| `backend/scripts/sdsr/inject_synthetic.py` | Modified | Emits `.sdsr_observation_ready` signal only |
| `scripts/tools/sdsr_observation_watcher.sh` | **Created** | Downstream orchestrator |
| `scripts/tools/AURORA_L2_apply_sdsr_observations.py` | Unchanged | Creates `.aurora_needs_preflight_recompile` |
| `scripts/tools/run_aurora_l2_pipeline_preflight.sh` | Unchanged | Detects signal, compiles, deploys |

## Signal File Formats

### .sdsr_observation_ready (from inject_synthetic.py)

```
observation_path=/path/to/SDSR_OBSERVATION_*.json
scenario_id=SDSR-E2E-004
observation_class=EFFECT
capabilities_count=1
```

### .aurora_needs_preflight_recompile (from apply_observations.py)

```
Triggered by observation application
Observation: /path/to/observation.json
```

## Usage

```bash
# Step 1: Run SDSR scenario (manual)
python3 backend/scripts/sdsr/inject_synthetic.py --scenario SDSR-E2E-004

# Step 2: Process observation (via watcher)
./scripts/tools/sdsr_observation_watcher.sh

# Step 2 (dry run mode):
./scripts/tools/sdsr_observation_watcher.sh --dry-run

# Step 2 (skip preflight compile):
./scripts/tools/sdsr_observation_watcher.sh --skip-preflight

# Step 3: Verify at preflight
# URL: https://preflight-console.agenticverz.com/precus/policies

# Step 4: Promote to production (manual)
./scripts/tools/promote_projection.sh
```

## Pipeline Chain Reaction

| Step | Script | Trigger | Output |
|------|--------|---------|--------|
| 1 | `inject_synthetic.py` | Manual | `.sdsr_observation_ready` signal |
| 2 | `sdsr_observation_watcher.sh` | Manual / Cron / CI | Orchestrates downstream |
| 3 | `AURORA_L2_apply_sdsr_observations.py` | Called by watcher | Registry + `.aurora_needs_preflight_recompile` |
| 4 | `run_aurora_l2_pipeline_preflight.sh` | Called by watcher | Aurora compile + preflight deploy |
| 5 | Signal cleanup | Automatic | Signals cleared |

## Manual vs Automatic

| Operation | Type | Rationale |
|-----------|------|-----------|
| Scenario selection | **MANUAL** | Human judgment |
| inject_synthetic.py execution | **MANUAL** | Human initiates test |
| Truth materialization | **AUTO** | inject_synthetic.py calls Scenario_SDSR_output.py |
| Signal emission | **AUTO** | inject_synthetic.py writes .sdsr_observation_ready |
| Observation → Registry | **AUTO** | watcher calls apply_observations.py |
| Preflight compile | **AUTO** | watcher calls preflight pipeline |
| Preflight verification | **MANUAL** | Human verifies |
| Production promotion | **MANUAL** | Human runs promote_projection.sh |

## Key Principles Enforced

1. **One-way causality** — inject_synthetic.py does NOT call Aurora scripts
2. **Signal-based decoupling** — Upstream emits signals, downstream reacts
3. **Clean authority boundaries** — Each script has one clear responsibility
4. **Automation where safe** — Truth + registry updates are automatic
5. **Manual gates preserved** — Scenario selection, verification, production promotion

## Verification

Dry run successful:
```
[OK] Signal detection: Working
[OK] Signal parsing: Working
[OK] Observation applier: Working
[OK] Preflight trigger: Would execute
[OK] Signal cleanup: Would execute
```

---

## Related PINs

- [PIN-370](PIN-370-.md)
- [PIN-379](PIN-379-.md)
- [PIN-391](PIN-391-.md)
