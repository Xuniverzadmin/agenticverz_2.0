# HOC Migration - Phase 2: Migration Execution Plan

**Date:** 2026-01-23
**Status:** STEP 1 COMPLETE - READY FOR STEP 2
**Prerequisites:** Phase 1 Complete (ITERATION2_AUDIT_REPORT.md)
**Input Inventory:** MIGRATION_INVENTORY_ITER3.csv (validated)

---

## Overview

Phase 2 executes the physical migration of **821 files** from legacy locations to `app/houseofcards/` based on the approved classification inventory.

**Key Principle:** COPY first, then validate, then cleanup in Phase 5.

---

## Step 0: Pre-Migration Audit ✅ COMPLETE

**Status:** COMPLETE
**Report:** `PHASE2_STEP0_AUDIT.md`

### 0.1 Duplicate Check ✅

**Finding:** 116 legacy files duplicate existing HOC files.

**Resolution:** Marked as `SKIP_HOC_EXISTS` in inventory.

### 0.2 Audit Document Cross-Reference ✅

**Audit Documents Found:** 10 domain audit documents at `backend/app/houseofcards/customer/{domain}/HOC_{domain}_*_audit_report.md`

| Domain | Audit Document | Files in HOC | Files to Transfer | Status |
|--------|---------------|--------------|-------------------|--------|
| activity | `HOC_activity_deep_audit_report.md` | 7 | 16 | ✅ CLEAN |
| incidents | `HOC_incidents_deep_audit_report.md` | 12 | 40 | ✅ CLEAN |
| policies | `HOC_policies_detailed_audit_report.md` | 28 | 150 | ✅ CLEAN |
| logs | `HOC_logs_detailed_audit_report.md` | 15 | 62 | ✅ CLEAN |
| analytics | `HOC_analytics_detailed_audit_report.md` | 7 | 40 | ✅ CLEAN |
| integrations | `HOC_integrations_detailed_audit_report.md` | 18 | 70 | ✅ CLEAN |
| api_keys | `HOC_api_keys_detailed_audit_report.md` | 2 | 10 | ✅ CLEAN |
| account | `HOC_account_detailed_audit_report.md` | 11 | 20 | ✅ CLEAN |
| overview | `HOC_overview_detailed_audit_report.md` | 1 | 8 | ✅ CLEAN |
| general | `HOC_general_deep_audit_report.md` | 31 | 69 | ✅ CLEAN |

**Quarantine Check:** 15 files in `houseofcards/duplicate/` correctly marked DELETE.

### 0.3 INTERNAL/FOUNDER Pre-Check ✅

| Audience | Already in HOC | To Migrate | Skip (duplicates) |
|----------|---------------|------------|-------------------|
| INTERNAL | 45 | 260 | 37 |
| FOUNDER | 12 | 10 | 8 |

### 0.4 Final Inventory Statistics

| Action | Count | Description |
|--------|-------|-------------|
| **TRANSFER** | 821 | Files to copy to HOC |
| SKIP_HOC_EXISTS | 116 | Legacy duplicates (HOC authoritative) |
| STAYS | 30 | L7 models (remain in app/) |
| SKIP_INIT_COLLISION | 24 | Init collisions (resolved) |
| DELETE | 18 | Deprecated/quarantine files |
| **Total** | 1,009 | All files accounted |

### Issues Found and Fixed

1. **Target path collisions** - Fixed L2/L4 path generation in `classify_inventory.py`
2. **Common filename collisions** - Added disambiguation for `facade.py`, `base.py`, etc.
3. **Init file collisions** - Resolved by keeping first, marking others SKIP

---

## Step 1: Copy Files to HOC ✅ COMPLETE

### Objective
Copy (not move) all 821 TRANSFER files from source to target paths.

### 1.1 Execution Summary

**Date:** 2026-01-23
**Script:** `scripts/migration/generate_copy_script.py`

| Metric | Count |
|--------|-------|
| Total TRANSFER in inventory | 821 |
| Already at target (skipped) | 248 |
| Files copied | 573 |

### 1.2 Copy by Layer

| Layer | Files Copied | Target Directory |
|-------|--------------|------------------|
| L6 | 113 | `drivers/` or `schemas/` |
| L5 | 291 | `engines/` |
| L4 | 85 | `engines/` |
| L3 | 47 | `facades/` |
| L2 | 33 | `api/{audience}/{domain}/` |
| L2-Infra | 4 | `api/infrastructure/` |

### 1.3 Post-Copy Validation ✅

**HOC Directory Summary:**

| Metric | Count |
|--------|-------|
| Total Python files (with __init__) | 845 |
| Non-init Python files | 746 |

**By Top-Level Directory:**

| Directory | Non-init Files |
|-----------|----------------|
| api/ | 84 |
| customer/ | 390 |
| internal/ | 243 |
| founder/ | 14 |

### 1.4 Execution Log

```bash
# Script generated and executed
python3 scripts/migration/generate_copy_script.py > /tmp/copy_migration.sh
bash /tmp/copy_migration.sh
# Output: Migration complete: 573 files copied
```

---

## Step 1.5: Post-Migration Audit ✅ COMPLETE

### Objective
Verify no quarantined files were reintroduced and no duplicates exist after migration.

### 1.5.1 Audit Script

**Script:** `scripts/migration/post_migration_audit.py`

Checks each customer domain against audit reports for:
- Reintroduced quarantine files
- Duplicate files (same basename in multiple locations)
- Quarantine directory consistency

### 1.5.2 Initial Findings

| Issue Type | Count |
|------------|-------|
| Reintroduced files | 0 |
| Duplicate files | 15 |

**Duplicate Analysis:**
- 12 files were IDENTICAL (exact copies)
- 3 files were DIFFERENT (minor variations)

All duplicates caused by migration copying to wrong locations where files already existed.

### 1.5.3 Cleanup Executed

**Script:** `scripts/migration/cleanup_migration_copies.py`

Removed 15 files that were copied during migration (timestamp 2026-01-23 18:08).
Kept original files from Jan 22 (pre-migration).

| Domain | Files Removed |
|--------|---------------|
| incidents | 2 (drivers/) |
| policies | 4 (drivers/, engines/) |
| logs | 1 (engines/) |
| analytics | 1 (drivers/) |
| integrations | 3 (engines/) |
| general | 2 (engines/) |
| account | 2 (drivers/) |

### 1.5.4 Final Audit Results ✅

| Metric | Value |
|--------|-------|
| Domains audited | 10 |
| Domains CLEAN | 10 ✅ |
| Reintroduced files | 0 |
| Duplicate files | 0 |

**HOC Final State:**

| Directory | Non-init Files |
|-----------|----------------|
| customer/ | 375 |
| internal/ | 243 |
| api/ | 84 |
| founder/ | 14 |
| duplicate/ (quarantine) | 15 |
| **Total** | **731** |

---

## Step 2: Mark CSV Rows as Copied ✅ COMPLETE

### Objective
Update inventory CSV with copy status and actual target paths.

### 2.1 CSV Schema Update

Added columns to inventory:

| Column | Type | Description |
|--------|------|-------------|
| `copied` | ENUM | TRUE, FALSE, DEDUPLICATED, N/A |
| `copied_path` | STRING | Actual path in HOC |
| `copied_date` | DATE | Date of copy operation |
| `copy_status` | ENUM | SUCCESS, DEDUPLICATED, SKIPPED, FAILED, N/A |
| `skip_reason` | STRING | Reason if skipped/deduplicated |

### 2.2 Execution Summary

**Date:** 2026-01-23
**Script:** `scripts/migration/mark_copied.py`

| Metric | Count |
|--------|-------|
| Total rows processed | 1,009 |
| TRANSFER - SUCCESS | 806 |
| TRANSFER - DEDUPLICATED | 15 |
| TRANSFER - FAILED | 0 |
| **TRANSFER Total** | **821** |

**Non-TRANSFER Breakdown:**

| Action | Count |
|--------|-------|
| SKIP_HOC_EXISTS | 116 |
| STAYS | 30 |
| DELETE | 18 |
| SKIP_INIT_COLLISION | 24 |

### 2.3 Deduplicated Files (Step 1.5 Resolution)

15 files were marked DEDUPLICATED because their target locations were removed during Step 1.5 cleanup (duplicate files). The original files exist at different paths within HOC:

| Intended Target | Actual Location |
|-----------------|-----------------|
| `analytics/drivers/cost_write_service.py` | `analytics/engines/cost_write_service.py` |
| `integrations/engines/vault.py` | `integrations/vault/engines/vault.py` |
| `integrations/engines/cus_credential_service.py` | `integrations/vault/engines/cus_credential_service.py` |
| `integrations/engines/datasource_model.py` | `integrations/schemas/datasource_model.py` |
| `logs/engines/evidence_facade.py` | `logs/facades/evidence_facade.py` |
| `policies/engines/governance_facade.py` | `policies/facades/governance_facade.py` |
| `policies/engines/limits_facade.py` | `policies/facades/limits_facade.py` |
| `incidents/drivers/incident_read_service.py` | `incidents/engines/incident_read_service.py` |
| `incidents/drivers/incident_write_service.py` | `incidents/engines/incident_write_service.py` |
| `policies/drivers/customer_killswitch_read_service.py` | `policies/controls/engines/customer_killswitch_read_service.py` |
| `policies/drivers/customer_policy_read_service.py` | `policies/engines/customer_policy_read_service.py` |
| `general/engines/offboarding.py` | `general/lifecycle/engines/offboarding.py` |
| `general/engines/onboarding.py` | `general/lifecycle/engines/onboarding.py` |
| `account/drivers/tenant_service.py` | `account/engines/tenant_service.py` |
| `account/drivers/user_write_service.py` | `account/engines/user_write_service.py` |

### 2.4 Step 2 Deliverable

**Output:** `MIGRATION_INVENTORY_PHASE2.csv`
- ✅ All 1,009 rows updated with copy status
- ✅ 821 TRANSFER files verified (806 SUCCESS + 15 DEDUPLICATED)
- ✅ Ready for gap analysis

---

## Step 3: Layer Fit Analysis ✅ COMPLETE

### Objective

Analyze whether files in HOC truly belong to their declared/folder layers using automated signal detection and classification.

### 3.1 Two-Pass Analysis Architecture

**Pass 1 - Signal Detection (`layer_analysis.py`):**
- Scans HOC Python files for layer signals (imports, patterns, decorators)
- Extracts header metadata (Layer, AUDIENCE, Role declarations)
- Output: `signals_raw.json`

**Pass 2 - Classification (`layer_classifier.py`):**
- Applies layer rules to detected signals
- Identifies violations (DRIFT, DATA_LEAK, LAYER_JUMP, etc.)
- Output: `layer_fit_report.json`, `layer_fit_summary.md`

### 3.2 Execution Summary

**Date:** 2026-01-23
**Reference:** `PHASE2_STEP3_LAYER_CRITERIA.md`

| Metric | Count |
|--------|-------|
| Files Analyzed | 715 |
| Layer FIT | 155 (21.7%) |
| MISFIT | 560 (78.3%) |

### 3.3 Violation Breakdown

| Violation | Count | Severity | Description |
|-----------|-------|----------|-------------|
| DRIFT | 410 | HIGH | Declared layer ≠ detected dominant layer |
| DATA_LEAK | 266 | HIGH | Non-L6 files doing DB operations |
| LAYER_JUMP | 107 | HIGH | Folder layer ≠ declared layer |
| TEMPORAL_LEAK | 20 | MEDIUM | sleep/retry in wrong layers |
| AUTHORITY_LEAK_HTTP | 9 | HIGH | L4 doing HTTP things |

### 3.4 Layer Distribution (by dominant signals)

| Layer | Name | Files |
|-------|------|-------|
| L2 | APIs | 130 |
| L3 | Adapters | 12 |
| L4 | Engines | 21 |
| L5 | Workers | 0 |
| L6 | Drivers/Schemas | 480 |

**Key Insight:** Most files (480/715 = 67%) have L6 dominant signals, indicating widespread DB access in files that should be engines (L4) or adapters (L3). This is the primary remediation focus.

### 3.5 Work Backlog (Axis C - Refactor Actions)

Each file maps to exactly one canonical refactor action:

| # | Action | Files | Effort | Description |
|---|--------|-------|--------|-------------|
| 1 | **HEADER_FIX_ONLY** | 54 | LOW | Fix header/metadata only, no code changes |
| 2 | **RECLASSIFY_ONLY** | 222 | LOW | Move file to correct folder, update header |
| 3 | **EXTRACT_DRIVER** | 234 | MEDIUM | Extract DB operations to new L6 Driver |
| 4 | **EXTRACT_AUTHORITY** | 12 | HIGH | Move HTTP/decisions to appropriate layer |
| 5 | **SPLIT_FILE** | 20 | HIGH | Split into multiple single-responsibility files |
| 6 | **NO_ACTION** | 173 | NONE | Already correctly placed and classified |

**Effort Summary:**

| Effort Level | Files |
|--------------|-------|
| LOW (quick wins) | 276 |
| MEDIUM (standard) | 241 |
| HIGH (complex) | 25 |
| **Total Work Items** | **542** |

**Recommended Execution Order:**
1. HEADER_FIX_ONLY → Fast wins, improves signal accuracy
2. RECLASSIFY_ONLY → Folder hygiene, zero logic risk
3. QUARANTINE_DUPLICATE → Reduces noise
4. EXTRACT_DRIVER → Main work, needs conventions first
5. EXTRACT_AUTHORITY → High risk, requires L4 stability
6. SPLIT_FILE → Last, architectural surgery

### 3.6 Step 3 Deliverables

**Scripts:**
- ✅ `scripts/migration/layer_analysis.py` - Pass 1 signal detection
- ✅ `scripts/migration/layer_classifier.py` - Pass 2 classification

**Reports:**
- ✅ `docs/architecture/migration/signals_raw.json` - Raw signal data
- ✅ `docs/architecture/migration/layer_fit_report.json` - Full classification results
- ✅ `docs/architecture/migration/layer_fit_summary.md` - Human-readable summary

**Documentation:**
- ✅ `docs/architecture/migration/PHASE2_STEP3_LAYER_CRITERIA.md` - Layer criteria reference

---

## Gap Analysis Audit ⏳ PENDING

### Objective
Identify missing components in HOC architecture through 3 manual audit iterations.

### Iteration 1: Layer-wise Gap Analysis (CUSTOMER)

For each CUSTOMER domain, audit by layer:

| Domain | L2 (API) | L3 (Facade) | L4 (Engine) | L5 (Logic) | L6 (Data) |
|--------|----------|-------------|-------------|------------|-----------|
| activity | | | | | |
| incidents | | | | | |
| policies | | | | | |
| logs | | | | | |
| analytics | | | | | |
| integrations | | | | | |
| api_keys | | | | | |
| account | | | | | |
| overview | | | | | |
| general | | | | | |

**For each cell, identify:**
- [ ] Files copied successfully
- [ ] Files missing (exist in legacy but not in CSV)
- [ ] Files incomplete (partial implementation)
- [ ] Files needing refactor (violate layer rules)

**Output:** `GAP_ANALYSIS_ITER1_LAYERS.md`

### Iteration 2: Domain Completeness Audit (CUSTOMER)

For each CUSTOMER domain, verify against HOC architecture plan:

```
Per domain checklist:
□ Has entry API (L2)
□ Has facade for boundary translation (L3)
□ Has domain engine for business logic (L4)
□ Has all required services (L5)
□ Has schemas defined (L6)
□ Has database drivers (L6)
□ Has __init__.py exports configured
□ Has domain audit report (HOC_{domain}_*_audit_report.md)
```

**Output:** `GAP_ANALYSIS_ITER2_DOMAINS.md`

### Iteration 3: Cross-Domain Integration Audit

Verify cross-domain interactions are properly handled:

| Source Domain | Target Domain | Integration Point | Status |
|---------------|---------------|-------------------|--------|
| Activity | Policies | Violation detection | |
| Incidents | Notifications | Alert dispatch | |
| Integrations | API Keys | Credential management | |
| Policies | Logs | Audit trail | |

**For each integration:**
- [ ] Facade exists at boundary
- [ ] No direct cross-domain imports
- [ ] Event/message contracts defined
- [ ] Error handling specified

**Output:** `GAP_ANALYSIS_ITER3_INTEGRATION.md`

---

## Phase 2 Deliverables ⏳ PENDING

### 1. Gap Inventory YAML

Complete list of missing components per domain.

**File:** `docs/architecture/migration/GAP_INVENTORY.yaml`

```yaml
# GAP_INVENTORY.yaml
version: "2.0"
generated: "2026-01-XX"
total_gaps: TBD

domains:
  activity:
    layer_gaps:
      L2: []
      L3: []
      L4: []
      L5: []
      L6: []
    integration_gaps: []

  # ... all 10 customer domains

internal:
  # Platform gaps

founder:
  # Admin gaps
```

### 2. Priority Matrix

Which gaps to fill first based on impact and effort.

**File:** `docs/architecture/migration/PRIORITY_MATRIX.md`

| Factor | Weight | Description |
|--------|--------|-------------|
| Business Impact | 40% | User-facing functionality affected |
| Dependency Count | 30% | Other components blocked |
| Effort Estimate | 20% | Development complexity |
| Risk | 10% | Migration risk if not addressed |

### 3. Development Estimates

Scope for Phase 3 gap implementation.

**File:** `docs/architecture/migration/PHASE3_SCOPE.md`

---

## Progress Tracker

| Step | Description | Status | Date |
|------|-------------|--------|------|
| Step 0 | Pre-Migration Audit | ✅ COMPLETE | 2026-01-23 |
| Step 1 | Copy Files to HOC | ✅ COMPLETE | 2026-01-23 |
| Step 1.5 | Post-Migration Audit & Cleanup | ✅ COMPLETE | 2026-01-23 |
| Step 2 | Mark CSV Rows | ✅ COMPLETE | 2026-01-23 |
| Step 3 | Layer Fit Analysis | ✅ COMPLETE | 2026-01-23 |
| Step 3.5 | Extraction Playbook & CI | ✅ COMPLETE | 2026-01-23 |
| Gap Iter 1 | Layer Audit | ⏳ PENDING | - |
| Gap Iter 2 | Domain Audit | ⏳ PENDING | - |
| Gap Iter 3 | Integration Audit | ⏳ PENDING | - |
| Deliverables | Generate YAML/Matrix/Scope | ⏳ PENDING | - |

---

## Success Criteria

Phase 2 is complete when:

- [x] Step 0: All duplicates identified and resolved
- [x] Step 0: CUSTOMER domains verified against audit docs
- [x] Step 1: All TRANSFER files copied to HOC (573 copied, 248 already at target)
- [x] Step 1.5: Post-migration audit passed (10/10 domains CLEAN, 15 duplicates removed)
- [x] Step 2: CSV updated with copy status (806 SUCCESS + 15 DEDUPLICATED = 821 verified)
- [x] Step 3: Layer fit analysis completed (715 files analyzed, 155 fit, 560 misfit)
- [ ] Gap Iter 1: Layer gaps documented for all domains
- [ ] Gap Iter 2: Domain completeness verified
- [ ] Gap Iter 3: Cross-domain integrations audited
- [ ] Deliverable 1: GAP_INVENTORY.yaml generated
- [ ] Deliverable 2: PRIORITY_MATRIX.md completed
- [ ] Deliverable 3: PHASE3_SCOPE.md estimated

---

## Step 3.5: Extraction Playbook & CI Enforcement ✅ COMPLETE

### Objective

Establish operational playbook and CI guardrails for executing the 542 work items identified in Step 3.

### 3.5.1 Core Diagnosis

> **82% of L4 "engines" are actually L6 DB code.**

The system does not currently have an L4 layer in practice. Migration creates L4 by **removing DB gravity**.

**Key Numbers:**
- 348 files declare L4
- Only 13 behave like L4
- 285 (82%) behave like L6 (DB operations)

### 3.5.2 Extraction Playbook

**Reference:** `PHASE2_EXTRACTION_PLAYBOOK.md`

| Phase | Work | Files | Duration |
|-------|------|-------|----------|
| Phase 0 | Stabilize measurement | - | 2-3 days |
| Phase 1 | LOW effort cleanup | 276 | Week 1 |
| Phase 2 | EXTRACT_DRIVER | 234 | Week 2-3 |
| Phase 3 | HIGH effort (complex) | 32 | Week 4 |

**Stop Condition for Phase 2:**
> Engines with DB signals ≤ 5%

### 3.5.3 CI Enforcement

**Script:** `scripts/migration/layer_compliance_check.py`

| Rule | Enforcement |
|------|-------------|
| No regression (FIT → MISFIT) | BLOCKING |
| No MISFIT count increase | BLOCKING |
| New files must have declared layer | BLOCKING |
| Engine purity (no SQLAlchemy) | WARNING (BLOCKING in Phase 2) |
| No expired violations | BLOCKING |

**Current Status:**
```
✅ PASSED: All checks pass
  - Total files: 715
  - FIT: 155 (21.7%)
  - MISFIT: 560 (78.3%)
  - Work items: 542
  - Impure engines: 333 (warning only until Phase 2)
```

### 3.5.4 Allowed Violations Registry

**File:** `ALLOWED_VIOLATIONS.yaml`

Temporary escape hatch for HIGH effort files requiring architect review:
- 5 EXTRACT_AUTHORITY files (expires: 2026-04-15)
- 4 SPLIT_FILE files (expires: 2026-04-15)

CI fails if:
- Expiry date passes
- New violation added without entry

### 3.5.5 Step 3.5 Deliverables

**Playbook:**
- ✅ `PHASE2_EXTRACTION_PLAYBOOK.md` - Operational execution guide

**CI Scripts:**
- ✅ `scripts/migration/layer_compliance_check.py` - CI guard
- ✅ `scripts/migration/generate_domain_report.py` - Domain report generator

**Reports:**
- ✅ `layer_fit_detailed_report.md` - Comprehensive breakdown
- ✅ `layer_fit_customer_domains.md` - Domain-wise analysis

**Registry:**
- ✅ `ALLOWED_VIOLATIONS.yaml` - Temporary exception registry

---

## Next Phase

Upon Phase 2 completion, proceed to:

**Phase 3: Gap Implementation**
- Implement missing components identified in GAP_INVENTORY.yaml
- Follow PRIORITY_MATRIX.md order
- Track against PHASE3_SCOPE.md estimates

**Phase 4: Import Remediation**
- Update all import statements
- Run BLCA validation
- Fix any violations

**Phase 5: Legacy Cleanup**
- Delete `app/services/*` after full validation
- Remove deprecated files
- Archive migration artifacts

---

## Artifacts

| Artifact | Location | Status |
|----------|----------|--------|
| Phase 1 Report | `ITERATION2_AUDIT_REPORT.md` | ✅ Complete |
| Step 0 Report | `PHASE2_STEP0_AUDIT.md` | ✅ Complete |
| Source Inventory | `MIGRATION_INVENTORY_ITER3.csv` | ✅ Validated |
| Phase 2 Inventory | `MIGRATION_INVENTORY_PHASE2.csv` | ✅ Generated |
| Classification Script | `scripts/migration/classify_inventory.py` | ✅ Fixed |
| Copy Script | `scripts/migration/generate_copy_script.py` | ✅ Created |
| Post-Migration Audit | `scripts/migration/post_migration_audit.py` | ✅ Created |
| Duplicate Cleanup | `scripts/migration/cleanup_migration_copies.py` | ✅ Created |
| Mark Copied Script | `scripts/migration/mark_copied.py` | ✅ Created |
| Layer Criteria | `PHASE2_STEP3_LAYER_CRITERIA.md` | ✅ Created |
| Signal Detection Script | `scripts/migration/layer_analysis.py` | ✅ Created |
| Classification Script | `scripts/migration/layer_classifier.py` | ✅ Created |
| Signals Raw | `signals_raw.json` | ✅ Generated |
| Layer Fit Report | `layer_fit_report.json` | ✅ Generated |
| Layer Fit Summary | `layer_fit_summary.md` | ✅ Generated |
| Layer Fit Detailed | `layer_fit_detailed_report.md` | ✅ Generated |
| Customer Domains | `layer_fit_customer_domains.md` | ✅ Generated |
| Extraction Playbook | `PHASE2_EXTRACTION_PLAYBOOK.md` | ✅ Created |
| Allowed Violations | `ALLOWED_VIOLATIONS.yaml` | ✅ Created |
| CI Compliance Check | `scripts/migration/layer_compliance_check.py` | ✅ Created |
| Domain Report Gen | `scripts/migration/generate_domain_report.py` | ✅ Created |
| This Plan | `PHASE2_MIGRATION_PLAN.md` | ✅ Updated |

---

**Document Status:** STEP 3.5 COMPLETE - EXTRACTION PLAYBOOK & CI READY
**Next Action:** Execute extraction phases per PHASE2_EXTRACTION_PLAYBOOK.md
