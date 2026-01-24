# HOC Phase 1: Migration Plan

**Version:** 1.1.0
**Status:** ITERATION_1_IN_PROGRESS
**Created:** 2026-01-23
**Updated:** 2026-01-23
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (v1.2.0), HOC_MIGRATION_PLAN.md

---

## Current Progress

| Milestone | Status | Notes |
|-----------|--------|-------|
| Script Created | ✅ COMPLETE | `scripts/migration/generate_inventory.py` |
| Inventory Generated | ✅ COMPLETE | 1,009 files inventoried |
| Iteration 0 | ✅ COMPLETE | Auto-classification complete |
| Iteration 1 | ✅ COMPLETE | 958/1009 classified (94.9%) |
| Iteration 2 | ✅ COMPLETE | All 34 L5/L6 services resolved |
| Audit Approved | ✅ COMPLETE | Ready for Phase 2 execution |

### Iteration 1 Results (2026-01-23)

See: `docs/architecture/migration/ITERATION1_AUDIT_REPORT.md`

| Metric | Value |
|--------|-------|
| Ready for migration | 958 files (94.9%) |
| Needs manual review | 34 files (L5/L6 ambiguous) |
| Marked for deletion | 18 files |
| Models that stay | 30 files |

### Iteration 2 Results (2026-01-23)

See: `docs/architecture/migration/ITERATION2_AUDIT_REPORT.md`

| Metric | Value |
|--------|-------|
| L5/L6 Resolved | 34 → 0 ✅ |
| → L4 Domain Engines | 28 files |
| → L6 Platform Substrate | 4 files |
| → L3 Boundary Adapter | 1 file |
| → DELETE | 1 file |
| **Ready for Phase 2** | 1,009 files (100%) |

### Inventory Statistics (Iteration 0)

| auto_status | Count | % |
|-------------|-------|---|
| NEEDS_CLASSIFICATION | 976 | 96.7% |
| STAYS (L7 models) | 30 | 3.0% |
| DEPRECATED_DUPLICATE | 3 | 0.3% |
| ALREADY_IN_HOC | 0 | 0% |

**Note:** `ALREADY_IN_HOC = 0` because `houseofcards/` directory doesn't exist yet. This is expected.

---

## 1. Objective

Inventory all files in `app/` and create a canonical migration CSV that maps each file to its target location in `app/houseofcards/{audience}/{domain}/` following the 8-layer topology.

**Architectural Decision (Option B):** HOC files remain within `app/` directory as `app/houseofcards/`. Legacy code in `app/services/` will be deleted in Phase 5 after migration is complete and validated.

---

## 2. Scope

### 2.1 What STAYS (L7 Only)

| Location | Reason | Action |
|----------|--------|--------|
| `app/models/*.py` | Shared DB tables (tenant, audit_ledger, base) | STAYS |
| `app/customer/models/*.py` | Customer-specific DB tables | STAYS |
| `app/founder/models/*.py` | Founder-specific DB tables | STAYS |
| `app/internal/models/*.py` | Internal-specific DB tables | STAYS |

**Total:** ~30 files

### 2.2 What MIGRATES (Everything Else)

| Source | Target Pattern | Layer |
|--------|----------------|-------|
| `app/api/*.py` | `app/houseofcards/api/{audience}/{domain}.py` | L2 |
| `app/api/dependencies/*.py` | `app/houseofcards/api/dependencies/` | L2-Infra |
| `app/api/middleware/*.py` | `app/houseofcards/api/middleware/` | L2-Infra |
| `app/services/*_facade.py` | `app/houseofcards/{audience}/{domain}/adapters/` | L3 |
| `app/services/**/*_engine.py` | `app/houseofcards/{audience}/{domain}/engines/` | L5 |
| `app/services/**/*_service.py` | `app/houseofcards/{audience}/{domain}/engines/` or `drivers/` | L5/L6 |
| `app/services/**/schemas/*.py` | `app/houseofcards/{audience}/{domain}/schemas/` | L5 |
| `app/worker/*.py` | `app/houseofcards/{audience}/general/runtime/` or `{domain}/workers/` | L4/L5 |
| `app/auth/*.py` | `app/houseofcards/internal/platform/auth/` | L4-Internal |
| `app/core/*.py` | `app/houseofcards/internal/platform/core/` | L6-Internal |
| `app/events/*.py` | `app/houseofcards/internal/platform/events/` | L6-Internal |
| `app/middleware/*.py` | `app/houseofcards/api/middleware/` | L2-Infra |

**Total:** ~300 files

### 2.3 What Gets DELETED

| Location | Reason |
|----------|--------|
| `houseofcards/duplicate/**/*.py` | Legacy duplicates (already removed in prior audit) |
| `app/api/legacy_routes.py` | Deprecated |
| `app/api/v1_*.py` | Deprecated v1 proxy routes |

### 2.4 What's ALREADY IN HOC

Files already in `app/houseofcards/` structure (248 files).
Script will detect and mark as `ALREADY_IN_HOC` - these files stay in place.

---

## 3. Migration Inventory CSV

### 3.1 File Location

```
docs/architecture/migration/MIGRATION_INVENTORY.csv
```

### 3.2 CSV Schema

| Column | Type | Filled By | Description |
|--------|------|-----------|-------------|
| `s_no` | INT | Script | Sequential row number |
| `source_path` | TEXT | Script | Current file path |
| `audience` | ENUM | **Human** | CUSTOMER / FOUNDER / INTERNAL |
| `domain` | TEXT | **Human** | overview / activity / incidents / policies / logs / analytics / integrations / api_keys / account / general / ops / platform / recovery / agent |
| `layer` | ENUM | **Human** | L2 / L2-Infra / L3 / L4 / L5 / L6 / L7 |
| `target_path` | TEXT | **Human** | Target path in app/houseofcards/ |
| `file_header` | TEXT | Script | First 15 lines of file (for classification help) |
| `docstring` | TEXT | Script | Module/class docstring if exists |
| `existing_hoc_path` | TEXT | Script | Path if already exists in HOC |
| `auto_status` | ENUM | Script | NEEDS_CLASSIFICATION / ALREADY_IN_HOC / DEPRECATED_DUPLICATE / STAYS |
| `audit_status` | ENUM | **Human** | PENDING / ITERATION_1 / ITERATION_2 / APPROVED |
| `audit_notes` | TEXT | **Human** | Notes explaining classification decision |
| `action` | ENUM | **Human** | TRANSFER / STAYS / DELETE / SKIP / MERGE |

### 3.3 auto_status Values

| Value | Meaning | Human Action Required |
|-------|---------|----------------------|
| `NEEDS_CLASSIFICATION` | File needs audience/domain/layer assignment | Fill all columns |
| `ALREADY_IN_HOC` | Equivalent exists in houseofcards/ | Verify, mark SKIP or MERGE |
| `DEPRECATED_DUPLICATE` | Was in duplicate/ folder | Confirm DELETE |
| `STAYS` | L7 model file, stays in app/models/ | Verify, confirm STAYS |

### 3.4 action Values

| Value | Meaning |
|-------|---------|
| `TRANSFER` | Move file to target_path, insert header |
| `STAYS` | Keep in current location (L7 models only) |
| `DELETE` | Remove file (deprecated/duplicate) |
| `SKIP` | Don't migrate (already in HOC, no changes needed) |
| `MERGE` | Merge with existing HOC file |

---

## 4. Script: generate_inventory.py

### 4.1 Purpose

Mechanically inventory all files. Does NOT make classification decisions.

### 4.2 Script Behavior

```
INPUT:
  - backend/app/**/*.py
  - backend/houseofcards/**/*.py (for duplicate detection)

OUTPUT:
  - docs/architecture/migration/MIGRATION_INVENTORY.csv

LOGIC:
  1. Scan app/**/*.py recursively
  2. For each file:
     a. Extract source_path
     b. Extract file_header (first 15 lines)
     c. Extract docstring (module or first class)
     d. Check if similar file exists in houseofcards/
        - Match by filename
        - Match by class/function names
     e. Determine auto_status:
        - If in app/models/ or app/{audience}/models/ → STAYS
        - If match found in houseofcards/ → ALREADY_IN_HOC
        - If source was in duplicate/ folder → DEPRECATED_DUPLICATE
        - Else → NEEDS_CLASSIFICATION
  3. Output to CSV
  4. Print summary stats
```

### 4.3 Exclusions (Not Added to CSV)

| Pattern | Reason |
|---------|--------|
| `**/__pycache__/**` | Generated bytecode |
| `**/*.pyc` | Compiled Python |
| `**/__init__.py` (if empty) | Boilerplate |
| `**/test_*.py` | Test files (separate inventory) |
| `**/tests/**` | Test directories |
| `houseofcards/**/*.py` | Already in target (but used for matching) |

### 4.4 Duplicate Detection Logic

```python
def find_hoc_equivalent(source_path, hoc_files):
    """
    Find if source file has equivalent in HOC.

    Matching strategies:
    1. Exact filename match
    2. Similar filename (e.g., overview_facade.py → overview_adapter.py)
    3. Class name match (extract class names, compare)
    """
    source_filename = os.path.basename(source_path)
    source_classes = extract_class_names(source_path)

    for hoc_path in hoc_files:
        hoc_filename = os.path.basename(hoc_path)
        hoc_classes = extract_class_names(hoc_path)

        # Strategy 1: Exact filename
        if source_filename == hoc_filename:
            return hoc_path

        # Strategy 2: Similar filename (facade → adapter)
        if normalize_filename(source_filename) == normalize_filename(hoc_filename):
            return hoc_path

        # Strategy 3: Class name overlap
        if source_classes & hoc_classes:  # Set intersection
            return hoc_path

    return None
```

---

## 5. Audit Process

### 5.1 Iteration 0: Script Generation

**Executor:** Script
**Output:** CSV with 1,009 rows
**Status:** ✅ COMPLETE (2026-01-23)

| auto_status | Actual Count |
|-------------|--------------|
| NEEDS_CLASSIFICATION | 976 |
| ALREADY_IN_HOC | 0 (HOC dir doesn't exist yet) |
| STAYS | 30 |
| DEPRECATED_DUPLICATE | 3 |

### 5.2 Iteration 1: Initial Classification

**Executor:** Human
**Duration:** 2-4 hours
**Focus:**

For each `NEEDS_CLASSIFICATION` row:
1. Read `file_header` column
2. Read `docstring` column
3. Open file if needed to understand purpose
4. Determine:
   - `audience`: Who is this for?
   - `domain`: Which domain does this belong to?
   - `layer`: What layer is this?
   - `target_path`: Where should it go?
5. Fill columns
6. Set `audit_status` = `ITERATION_1`
7. Add `audit_notes` if uncertain

### 5.3 Iteration 2: Cross-Verification

**Executor:** Human (or second reviewer)
**Duration:** 1-2 hours
**Focus:**

1. Review all `ITERATION_1` rows
2. Verify layer assignments match HOC_LAYER_TOPOLOGY_V1.md:
   - Facades → L3 adapters (not L5 engines)
   - Read services → L6 drivers (not L5 engines)
   - Write services → L6 drivers (not L5 engines)
   - Business logic → L5 engines
3. Verify no cross-audience violations
4. Verify target_path follows pattern: `app/houseofcards/{audience}/{domain}/{layer}/`
5. Set `audit_status` = `APPROVED`

### 5.4 Validation Checklist

Before marking `APPROVED`:

- [ ] Every `NEEDS_CLASSIFICATION` row has audience, domain, layer, target_path
- [ ] No `*_facade.py` mapped to L5 (should be L3)
- [ ] No `*_read_service.py` mapped to L5 (should be L6)
- [ ] No `*_write_service.py` mapped to L5 (should be L6)
- [ ] No CUSTOMER files mapped to FOUNDER paths
- [ ] No FOUNDER files mapped to CUSTOMER paths
- [ ] All `ALREADY_IN_HOC` rows have action = SKIP or MERGE
- [ ] All `DEPRECATED_DUPLICATE` rows have action = DELETE
- [ ] All `STAYS` rows are in app/models/ or app/{audience}/models/

---

## 6. Domain Classification Guide

### 6.1 Customer Domains

| Domain | Keywords/Patterns | Example Files |
|--------|-------------------|---------------|
| `overview` | overview, dashboard, summary, health | overview_facade.py |
| `activity` | activity, run, execution, trace, signal | activity_facade.py, attention_ranking_service.py |
| `incidents` | incident, failure, recovery, postmortem | incident_engine.py, postmortem_service.py |
| `policies` | policy, rule, limit, constraint, control, killswitch, governance | policies_facade.py, policy_limits_service.py |
| `logs` | log, trace, audit, evidence, export, certificate | logs_facade.py, audit_evidence.py |
| `analytics` | analytics, cost, anomaly, prediction, pattern | analytics_facade.py, cost_anomaly_detector.py |
| `integrations` | integration, connector, credential, datasource, mcp, webhook | connectors_facade.py, http_connector.py |
| `api_keys` | api_key, key_service | api_keys_facade.py, key_service.py |
| `account` | account, tenant, user, profile, billing, notification | accounts_facade.py, tenant_service.py |
| `general` | shared utilities, cross-domain | time.py, utils.py |

### 6.2 Founder Domains

| Domain | Keywords/Patterns | Example Files |
|--------|-------------------|---------------|
| `ops` | ops, founder, admin, cross-tenant | ops_facade.py, founder_action_write_service.py |

### 6.3 Internal Domains

| Domain | Keywords/Patterns | Example Files |
|--------|-------------------|---------------|
| `platform` | platform, scheduler, sandbox, pool, health | scheduler_facade.py, sandbox_executor.py |
| `recovery` | recovery, orphan, compensation | orphan_recovery.py, recovery_matcher.py |
| `agent` | agent, worker, panel, validation | ai_console_panel_engine.py, worker_registry.py |

### 6.4 Layer Classification Guide

| Pattern | Layer | Reasoning |
|---------|-------|-----------|
| `*_facade.py` | L3 | Boundary adapter (NOT L5 engine) |
| `*_adapter.py` | L3 | Boundary adapter |
| `*_engine.py` | L5 | Business logic |
| `*_worker.py` | L5 | Heavy computation |
| `*_service.py` (domain logic) | L4 | Domain engine |
| `*_service.py` (data access) | L6 | Database driver |
| `*_driver.py` | L6 | Database driver |
| `schemas/*.py` | L6 | Data contracts (merged into L6 Data Layer) |
| `*_schema.py` | L6 | Data contracts (merged into L6 Data Layer) |
| `models/*.py` | L7 | Database tables |
| `governance_*.py` | L4 | Runtime governance |
| `orchestrator.py` | L4 | Runtime orchestration |
| `lifecycle_*.py` | L4 | Runtime lifecycle |

**Note:** L5-Schema was merged into L6. L6 is now the "Data Layer" containing:
- Schemas (data contracts, Pydantic models)
- Drivers (database read/write operations)
- Platform substrate (storage, external services)

---

## 7. Target Path Patterns

### 7.1 Standard Patterns

| Layer | Target Path Pattern |
|-------|---------------------|
| L2 API | `app/houseofcards/api/{audience}/{domain}.py` |
| L2 Middleware | `app/houseofcards/api/middleware/{name}.py` |
| L2 Dependencies | `app/houseofcards/api/dependencies/{name}.py` |
| L3 Adapter | `app/houseofcards/{audience}/{domain}/adapters/{name}_adapter.py` |
| L4 Runtime | `app/houseofcards/{audience}/general/runtime/{part}/{name}.py` |
| L5 Engine | `app/houseofcards/{audience}/{domain}/engines/{name}.py` |
| L5 Worker | `app/houseofcards/{audience}/{domain}/workers/{name}.py` |
| L6 Schema | `app/houseofcards/{audience}/{domain}/schemas/{name}.py` |
| L6 Driver | `app/houseofcards/{audience}/{domain}/drivers/{name}_driver.py` |
| L7 Model | `app/{audience}/models/{name}.py` (STAYS) |

**Note:** L6 Data Layer includes both schemas and drivers. Both go under their respective subdirectories.

### 7.2 Special Cases

| Source | Target | Notes |
|--------|--------|-------|
| `app/auth/*.py` | `app/houseofcards/internal/platform/auth/` | Auth infrastructure |
| `app/core/*.py` | `app/houseofcards/internal/platform/core/` | Core utilities |
| `app/events/*.py` | `app/houseofcards/internal/platform/events/` | Event bus |
| `app/worker/*.py` | Depends on content | May be L4 runtime or L5 workers |

---

## 8. Execution Steps

### Step 0: Create Directory Structure

```bash
mkdir -p docs/architecture/migration
mkdir -p scripts/migration
```

### Step 1: Run Inventory Script

```bash
cd backend
python scripts/migration/generate_inventory.py \
    --output ../docs/architecture/migration/MIGRATION_INVENTORY.csv
```

### Step 2: Review Script Output

- Verify row count matches expectations (~330)
- Spot-check auto_status assignments
- Verify no obvious misclassifications

### Step 3: Audit Iteration 1

- Open CSV in spreadsheet editor
- Filter by `auto_status = NEEDS_CLASSIFICATION`
- Fill in audience, domain, layer, target_path for each
- Mark `audit_status = ITERATION_1`

### Step 4: Audit Iteration 2

- Filter by `audit_status = ITERATION_1`
- Cross-verify against HOC_LAYER_TOPOLOGY_V1.md
- Fix any misclassifications
- Mark `audit_status = APPROVED`

### Step 5: Generate Migration Script

After audit complete, generate migration script from approved CSV:

```bash
python scripts/migration/generate_migration_script.py \
    --input ../docs/architecture/migration/MIGRATION_INVENTORY.csv \
    --output ../docs/architecture/migration/execute_migration.sh
```

---

## 9. Success Criteria

Phase 1 is complete when:

- [ ] MIGRATION_INVENTORY.csv exists with all files
- [ ] All `NEEDS_CLASSIFICATION` rows have audit_status = APPROVED
- [ ] All `ALREADY_IN_HOC` rows have action = SKIP or MERGE confirmed
- [ ] All `DEPRECATED_DUPLICATE` rows have action = DELETE confirmed
- [ ] All `STAYS` rows are confirmed L7 models only
- [ ] No unclassified files remain
- [ ] Layer assignments verified against HOC_LAYER_TOPOLOGY_V1.md

---

## 10. Deliverables

| Deliverable | Location |
|-------------|----------|
| Migration Inventory CSV | `docs/architecture/migration/MIGRATION_INVENTORY.csv` |
| Inventory Script | `scripts/migration/generate_inventory.py` |
| Audit Log | `docs/architecture/migration/MIGRATION_AUDIT_LOG.md` |
| This Plan | `docs/architecture/migration/PHASE1_MIGRATION_PLAN.md` |

---

## Appendix A: CSV Sample Rows

```csv
s_no,source_path,audience,domain,layer,target_path,file_header,docstring,existing_hoc_path,auto_status,audit_status,audit_notes,action
1,app/services/overview_facade.py,CUSTOMER,overview,L3,app/houseofcards/customer/overview/adapters/overview_adapter.py,"# Overview facade module\nfrom typing import...","OverviewFacade: Aggregates dashboard data from multiple domains",,NEEDS_CLASSIFICATION,APPROVED,Aggregates cross-domain data - L3 adapter,TRANSFER
2,app/services/activity/attention_ranking_service.py,,,,,,"# Attention ranking\n...","AttentionRankingService: Ranks activity items by importance",app/houseofcards/customer/activity/engines/attention_ranking_service.py,ALREADY_IN_HOC,APPROVED,Exact match in HOC,SKIP
3,app/models/tenant.py,INTERNAL,,L7,app/models/tenant.py,"# Tenant model\n...","Tenant: Multi-tenant base model",,STAYS,APPROVED,INTERNAL L7 model,STAYS
4,app/services/incidents/incident_engine.py,CUSTOMER,incidents,L5,app/houseofcards/customer/incidents/engines/incident_engine.py,"# Incident engine\n...","IncidentEngine: Creates and manages incidents",app/houseofcards/customer/incidents/engines/incident_engine.py,ALREADY_IN_HOC,APPROVED,Already migrated,SKIP
5,app/api/legacy_routes.py,,,,,,"# Legacy routes - deprecated\n...","Deprecated v1 routes",,DEPRECATED_DUPLICATE,APPROVED,Deprecated,DELETE
6,app/services/logs_read_service.py,CUSTOMER,logs,L6,app/houseofcards/customer/logs/drivers/logs_driver.py,"# Logs read service\n...","LogsReadService: Queries log records from database",,NEEDS_CLASSIFICATION,APPROVED,Read service = L6 driver,TRANSFER
```

---

## Appendix B: Common Classification Mistakes to Avoid

| Mistake | Correct Classification |
|---------|------------------------|
| `*_facade.py` → L5 Engine | Should be L3 Adapter |
| `*_read_service.py` → L5 Engine | Should be L6 Driver |
| `*_write_service.py` → L5 Engine | Should be L6 Driver |
| `governance_*` → L5 Engine | Should be L4 Runtime |
| `orchestrator.py` → L5 Engine | Should be L4 Runtime |
| Mixed read/write service → Single layer | Split into L5 (logic) + L6 (data) |

---

**Document Status:** PHASE_1_COMPLETE
**Next Step:** Phase 2 - Migration Execution (generate migration script, execute moves, update imports)
