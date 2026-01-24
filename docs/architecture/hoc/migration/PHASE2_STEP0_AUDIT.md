# Phase 2 Step 0: Pre-Migration Audit Report

**Date:** 2026-01-23
**Status:** COMPLETE - READY FOR STEP 1
**Input:** MIGRATION_INVENTORY_ITER2.csv
**Output:** MIGRATION_INVENTORY_ITER3.csv (final)

---

## Executive Summary

Pre-migration audit complete. The inventory has been validated and corrected. **821 files are ready for migration.**

| Action | Count | Description |
|--------|-------|-------------|
| **TRANSFER** | 821 | Files to copy to HOC |
| **SKIP_HOC_EXISTS** | 116 | Legacy duplicates (HOC version exists) |
| **STAYS** | 30 | L7 models (remain in app/) |
| **SKIP_INIT_COLLISION** | 24 | Init file collisions (resolved) |
| **DELETE** | 18 | Deprecated files |
| **Total** | 1,009 | All files accounted |

---

## Step 0.1: Duplicate Check (CUSTOMER Domains)

### HOC Structure Status

The HOC directory exists at `backend/app/hoc/` with:
- **187 non-init Python files** already in HOC
- Established structure for: customer, internal, founder audiences
- Domain subdirectories with facades/, engines/, drivers/, schemas/

### Duplicates Found

**116 legacy files duplicate existing HOC files.**

These are files in `app/services/`, `app/adapters/`, etc. that have equivalent versions already migrated to HOC.

**Resolution:** Marked as `SKIP_HOC_EXISTS` - will not be copied (HOC version is authoritative).

**Sample duplicates:**

| Legacy Source | HOC Version |
|--------------|-------------|
| `app/services/accounts_facade.py` | `app/hoc/cus/account/facades/accounts_facade.py` |
| `app/services/incident_aggregator.py` | `app/hoc/cus/incidents/L5_engines/incident_aggregator.py` |
| `app/services/policy_proposal.py` | `app/hoc/cus/policies/L5_engines/policy_proposal.py` |

---

## Step 0.2: Audit Document Cross-Reference (CUSTOMER)

### Audit Documents Found

Domain audit documents located at `backend/app/hoc/cus/{domain}/HOC_{domain}_*_audit_report.md`:

| Domain | Audit Document | Status |
|--------|---------------|--------|
| activity | `HOC_activity_deep_audit_report.md` | CLEAN |
| incidents | `HOC_incidents_deep_audit_report.md` | CLEAN |
| policies | `HOC_policies_detailed_audit_report.md` | CLEAN |
| logs | `HOC_logs_detailed_audit_report.md` | CLEAN |
| analytics | `HOC_analytics_detailed_audit_report.md` | CLEAN |
| integrations | `HOC_integrations_detailed_audit_report.md` | CLEAN |
| api_keys | `HOC_api_keys_detailed_audit_report.md` | CLEAN |
| account | `HOC_account_detailed_audit_report.md` | CLEAN |
| overview | `HOC_overview_detailed_audit_report.md` | CLEAN |
| general | `HOC_general_deep_audit_report.md` | CLEAN |

### Cross-Reference Results

| Domain | Files in HOC | Files to Transfer | Discrepancies |
|--------|-------------|-------------------|---------------|
| activity | 7 | 16 | 0 |
| incidents | 12 | 40 | 0 |
| policies | 28 | 150 | 0 |
| logs | 15 | 62 | 0 |
| analytics | 7 | 40 | 0 |
| integrations | 18 | 70 | 0 |
| api_keys | 2 | 10 | 0 |
| account | 11 | 20 | 0 |
| overview | 1 | 8 | 0 |
| general | 31 | 69 | 0 |

### Quarantine Files Check

All 15 non-init quarantine files in `hoc/duplicate/` are correctly marked DELETE:

- `duplicate/policies/` - 4 files (POL-DUP-001 to POL-DUP-004)
- `duplicate/incidents/` - 7 files (quarantined duplicates)
- `duplicate/analytics/` - 1 file
- `duplicate/integrations/` - 2 files
- `duplicate/general/` - 1 file

**Status:** All quarantine files correctly marked for deletion.

---

## Step 0.3: INTERNAL/FOUNDER Pre-Check

### INTERNAL Files

| Metric | Count |
|--------|-------|
| Total INTERNAL | 342 |
| Already in HOC | 45 |
| To migrate | 260 |
| Skip (duplicates) | 37 |

### FOUNDER Files

| Metric | Count |
|--------|-------|
| Total FOUNDER | 30 |
| Already in HOC | 12 |
| To migrate | 10 |
| Skip (duplicates) | 8 |

---

## Issues Found and Resolved

### Issue 1: Target Path Collisions (CRITICAL - FIXED)

**Problem:** Original classification script generated incorrect target paths:
- L2 (API) files mapped to single domain file (e.g., all policy APIs → `policies.py`)
- Multiple source files mapped to same target path

**Root Cause:** `generate_target_path()` in `classify_inventory.py` used `{domain}.py` instead of preserving filename.

**Fix Applied:**
```python
# Before (wrong)
"L2": f"app/hoc/api/{aud_lower}/{domain}.py"

# After (correct)
"L2": f"app/hoc/api/{aud_lower}/{domain}/{filename}"
```

**Verification:** 0 collisions after fix (was 67 collisions before).

### Issue 2: Common Filename Collisions (FIXED)

**Problem:** Files like `facade.py`, `base.py`, `provider.py` from different source directories collided.

**Fix Applied:** Added filename disambiguation for common names:
```python
COMMON_NAMES = {'facade.py', 'base.py', 'provider.py', 'parser.py', ...}
# Results in: app/services/audit/facade.py → audit_facade.py
```

### Issue 3: __init__.py Collisions (RESOLVED)

**Problem:** 24 `__init__.py` files from different source directories mapped to same target.

**Resolution:** Keep first (alphabetically), mark others as `SKIP_INIT_COLLISION`.

---

## Final Inventory Statistics

### By Action

| Action | Count | % |
|--------|-------|---|
| TRANSFER | 821 | 81.4% |
| SKIP_HOC_EXISTS | 116 | 11.5% |
| STAYS | 30 | 3.0% |
| SKIP_INIT_COLLISION | 24 | 2.4% |
| DELETE | 18 | 1.8% |

### TRANSFER Files by Audience

| Audience | Count |
|----------|-------|
| CUSTOMER | 503 |
| INTERNAL | 308 |
| FOUNDER | 10 |

### TRANSFER Files by Layer

| Layer | Count | Target Directory |
|-------|-------|------------------|
| L5 | 385 | `engines/` |
| L6 | 131 | `drivers/` or `schemas/` |
| L4 | 106 | `engines/` |
| L2 | 79 | `api/{audience}/{domain}/` |
| L3 | 68 | `facades/` |
| L2-Infra | 4 | `api/infrastructure/` |

---

## Classification Script Updates

The following fixes were applied to `scripts/migration/classify_inventory.py`:

1. **L2 target path**: Preserve filename instead of consolidating to domain file
2. **L3 target path**: Use `facades/` instead of `adapters/` (matches HOC structure)
3. **L4 target path**: Respect domain instead of all going to `general/runtime`
4. **Filename disambiguation**: Added `get_source_subdirectory()` for common names
5. **Extended COMMON_NAMES**: Added `conflict_resolver.py`, `store.py`, etc.

---

## Validation Checklist

### Automated Checks

- [x] No target path collisions (verified: 0 collisions)
- [x] All 1,009 files have action assigned
- [x] All TRANSFER files have valid target_path
- [x] No DEPRECATED files marked TRANSFER
- [x] HOC duplicates identified and marked SKIP

### Manual Verification

- [x] Reviewed target path generation logic
- [x] Verified HOC structure matches expected layout
- [x] Confirmed L7 models have action=STAYS

---

## Artifacts

| Artifact | Location |
|----------|----------|
| Final Inventory | `docs/architecture/migration/MIGRATION_INVENTORY_ITER3.csv` |
| Classification Script | `scripts/migration/classify_inventory.py` |
| This Report | `docs/architecture/migration/PHASE2_STEP0_AUDIT.md` |

---

## Approval for Step 1

### Pre-Conditions Met

- [x] Inventory validated (0 collisions)
- [x] HOC duplicates identified (116 files marked SKIP)
- [x] Init collisions resolved (24 files marked SKIP)
- [x] Classification script fixed and tested

### Ready for Execution

**821 files are ready for migration to HOC.**

Proceed to **Step 1: Copy Files to HOC** when ready.

---

**Report Status:** COMPLETE
**Next Step:** Step 1 - Copy Files
