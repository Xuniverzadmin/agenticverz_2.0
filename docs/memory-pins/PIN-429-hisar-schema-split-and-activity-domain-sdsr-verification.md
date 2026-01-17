# PIN-429: HISAR Schema Split and Activity Domain SDSR Verification

**Status:** ✅ COMPLETE
**Created:** 2026-01-15
**Category:** HISAR / Schema Architecture

---

## Summary

Implemented schema split (assumed_endpoint vs observed_endpoint), automated semantic registry domains from topology, and verified Activity domain capabilities via SDSR

---

## Details

## Overview

This session resolved an architectural paradox in the HISAR pipeline and completed SDSR verification for the Activity domain.

## Problem Statement

The original schema had a single `endpoint` field that was overloaded:
- Human authors provide assumed endpoints (may be wrong)
- SDSR verifies and discovers actual endpoints

This created confusion about who owns the endpoint field and what it represents.

## Solution: Schema Split

Split the `endpoint` field into two distinct fields:

| Field | Owner | Purpose |
|-------|-------|---------|
| `assumed_endpoint` | Human (Intent Ledger) | What we think the endpoint is |
| `observed_endpoint` | Machine (SDSR) | What SDSR actually verified |

### Files Modified

1. **sync_from_intent_ledger.py**
   - Parse `Implementation:` block from ledger
   - Generate `assumed_endpoint` in Intent YAML
   - Generate `assumption`/`binding` blocks in Capability YAML

2. **aurora_sdsr_runner.py**
   - Updated Observation dataclass with both assumed and observed fields
   - Added `get_assumed_endpoint()` helper

3. **aurora_apply_observation.py**
   - Persist binding block with observed_endpoint
   - Status transition: ASSUMED → OBSERVED

4. **aurora_coherency_check.py**
   - COH-004/005: Check assumed_endpoint consistency
   - COH-009/010: Reality-check assumed endpoints

## Status Transition Change

Changed canonical status flow from:
```
DECLARED → OBSERVED
```
To:
```
ASSUMED → OBSERVED
```

This better reflects the semantic: humans *assume*, SDSR *observes*.

## Semantic Registry Automation

### Problem
The semantic registry had hardcoded domains that drifted from the topology template.

### Solution
Updated `sync_from_intent_ledger.py` to auto-populate domains from `UI_TOPOLOGY_TEMPLATE.yaml`:

```python
def update_semantic_registry_domains(topology_path, registry_path):
    # Extracts domains and their questions from topology
    # Updates semantic registry automatically
```

Also fixed `run_aurora_l2_pipeline.sh` to read domains from registry instead of hardcoded list.

## Activity Domain SDSR Verification

### Capabilities Verified

| Capability | Status | Bound Endpoint | Panel |
|------------|--------|----------------|-------|
| `activity.live_runs` | OBSERVED | `/api/v1/activity/runs` | ACT-LLM-LIVE-O1 |
| `activity.completed_runs` | OBSERVED | `/api/v1/activity/runs` | ACT-LLM-COMP-O1 |
| `activity.signals` | OBSERVED | `/api/v1/activity/runs` | ACT-LLM-SIG-O1 |

### Terminology Fix

Changed `activity.risk_signals` → `activity.signals` because the panel captures:
- Critical failures
- Critical successes  
- Near-threshold conditions

Not just "risk" - all signal types.

### SDSR Scenario Fixes

Updated stale scenario files to match Intent Ledger:
- `SDSR-ACT-LLM-COMP-O1-001.yaml`: capability `activity.runs_list` → `activity.completed_runs`
- `SDSR-ACT-LLM-SIG-O1-001.yaml`: capability `activity.feedback_list` → `activity.signals`, endpoint `/api/v1/feedback` → `/api/v1/activity/runs`

## Pipeline Run Results

```
✓ Semantic validation passed (0 errors, 0 warnings)
✓ Compiler succeeded
✓ Generated canonical projection: 87 panels, 4 BOUND
✓ Diff guard passed
✓ Deployed to frontend
```

## Key Artifacts

| Artifact | Location |
|----------|----------|
| Schema split implementation | `scripts/tools/sync_from_intent_ledger.py` |
| SDSR runner updates | `backend/aurora_l2/tools/aurora_sdsr_runner.py` |
| Observation applier updates | `backend/aurora_l2/tools/aurora_apply_observation.py` |
| Coherency check updates | `backend/aurora_l2/tools/aurora_coherency_check.py` |
| Semantic registry | `design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml` |
| Activity observations | `backend/scripts/sdsr/observations/SDSR_OBSERVATION_activity.*.json` |

## Lessons Learned

1. **Single source of truth**: Domains must come from topology, not hardcoded
2. **Schema clarity**: Separate human assumptions from machine observations
3. **Terminology matters**: `signals` captures all signal types, not just `risk_signals`
4. **Sync order**: Always re-apply observations after sync resets capability files


---

## Related PINs

- [PIN-427](PIN-427-.md)
- [PIN-428](PIN-428-.md)
