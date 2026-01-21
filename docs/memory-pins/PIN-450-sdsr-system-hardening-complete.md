# PIN-450: SDSR System Hardening Complete

**Status:** ✅ COMPLETE
**Created:** 2026-01-19
**Category:** SDSR / System Hardening

---

## Summary

Comprehensive SDSR system hardening: fixed intent hygiene, migrated scenarios to invariant_ids format, resolved INT-007 violations, fixed malformed status values. Aurora pipeline passes Phase A with 88 panels.

---

## Details

## Overview

Completed SDSR system hardening to ensure governance compliance and pipeline integrity.

## Work Completed

### 1. Intent Hygiene (assumed_endpoint: null)
- **Fixed:** 30 of 33 panels with null endpoints
- **Root Cause:** 20 capability definitions were missing from INTENT_LEDGER.md
- **Resolution:** Added missing capability definitions with proper endpoints

### 2. SDSR Scenario Migration
- **Migrated:** 71 scenarios to new `invariant_ids` format
- **Old format:** Uses inline `invariants` with full definitions
- **New format:** Uses `invariant_ids` list, resolved at runtime

### 3. INT-007 Violations Fixed
- **Panels:** POL-GOV-LES-O6, POL-GOV-LES-O7
- **Issue:** Intent YAML files existed but not in registry
- **Resolution:** Ran `aurora_intent_registry_sync.py --all`

### 4. Malformed Status Values Fixed
- **Panel:** LOG-REC-AUD-O5
- **Issue:** Status contained NOTE comment: `DECLARED (endpoint exists) or DEFERRED...`
- **Resolution:** Fixed INTENT_LEDGER.md formatting, added section separator

### 5. Status Report Script Created
- **Location:** `backend/scripts/sdsr/report_status.py`
- **Features:** Domain stats, invariant counts, scenario format status, promotion readiness

## Final System State

| Metric | Value |
|--------|-------|
| Total Panels | 88 |
| OBSERVED | 7 (8.0%) |
| DECLARED | 32 |
| ASSUMED | 35 |
| DEFERRED | 14 |
| New format scenarios | 71 |
| Old format scenarios | 42 |

### Promotion Readiness by Domain

| Domain | Status | Notes |
|--------|--------|-------|
| ACTIVITY | READY | L0+L1 invariants present |
| INCIDENTS | PARTIAL | L1 invariants, no OBSERVED |
| LOGS | PARTIAL | L1 invariants, no OBSERVED |
| OVERVIEW | NOT READY | No L1 invariants defined |
| POLICIES | PARTIAL | L1 invariants, no OBSERVED |

## Pending To-Do Items

### P1: Sync Script Enhancement
**Issue:** 3 panels have `assumed_endpoint: null` despite capabilities having endpoints defined
- ACT-LLM-LIVE-O5 (topic-scoped capability)
- POL-GOV-LES-O1 (lessons.list)
- POL-GOV-LES-O2 (lessons.get)

**Root Cause:** `sync_from_intent_ledger.py` doesn't:
1. Handle topic-scoped endpoint definitions (LIVE/COMPLETED variants)
2. Map capability endpoints back to all referencing intent YAMLs

**Fix Required:** Enhance sync script to propagate endpoints from capability definitions

### P2: Old Format Scenario Migration
**Count:** 42 scenarios still use old `invariants` format
**Location:** `backend/scripts/sdsr/scenarios/`
**Action:** Run `aurora_sdsr_synth.py` to regenerate with `invariant_ids` format

### P3: Promotion Guard Violations
**Count:** 84 capabilities marked OBSERVED lack observation JSON files
**Cause:** Capabilities were promoted without running actual SDSR E2E validation
**Action:** Either:
1. Run SDSR scenarios against backend to generate observation evidence
2. Demote capabilities to DECLARED until properly validated

### P4: OVERVIEW Domain Invariants
**Issue:** OVERVIEW domain has no L1 invariants defined
**Location:** `backend/sdsr/invariants/`
**Action:** Create `overview.py` with domain-specific invariants

## Key Files Modified

- `design/l2_1/INTENT_LEDGER.md` - Added 20 capability definitions, fixed formatting
- `design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml` - Added POL-GOV-LES-O6/O7
- `backend/scripts/sdsr/report_status.py` - Created status dashboard
- 71 SDSR scenario files regenerated

## Commands Reference

```bash
# Run status report
python3 backend/scripts/sdsr/report_status.py

# Run Aurora pipeline
DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh

# Sync intent registry
python3 backend/aurora_l2/tools/aurora_intent_registry_sync.py --all

# Run promotion guard
python3 backend/scripts/sdsr/aurora_promotion_guard.py --all --ci
```

## References

- PIN-370: SDSR System Contract
- PIN-379: E2E Pipeline
- PIN-432: OBSERVED/TRUSTED status preservation
