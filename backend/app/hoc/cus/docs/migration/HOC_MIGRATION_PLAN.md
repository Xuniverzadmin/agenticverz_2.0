# HOC Domain Migration & Cleanup Plan

**Created:** 2026-01-27
**Status:** PROPOSED
**Scope:** 84 misplaced files across 11 customer domains
**Reference:** `backend/app/hoc/cus/_domain_map/V3_MANUAL_AUDIT_WORKBOOK.md`

---

## Overview

```
Phase 0: Generate Migration Manifest
    ↓
Phase 1: Validate Migration Plan
    ↓
Phase 2: Execute Migration
    ↓
Phase 3: Lock Domains
    ↓
Phase 4: Post-Migration Validation
    ↓
Phase 5: Duplicate Detection
    ↓
Phase 6: Consolidate General
    ↓
Phase 7: Refactor Domain Clusters
    ↓
Phase 8: Audit & Import Path Normalization
```

### Target Domains

| Domain | Current Files | Issue Flag |
|--------|---------------|------------|
| policies | 120 | BLOATED (80 engines) |
| general | 72 | Baseline |
| integrations | 67 | Review needed |
| logs | 55 | Overlapping functions |
| incidents | 47 | Review needed |
| analytics | 42 | OK |
| account | 19 | OK |
| activity | 16 | OK |
| api_keys | 9 | OK |
| overview | 6 | OK |
| controls | 5 | OK |

---

## Phase 0: Generate Migration Manifest

**Purpose:** Parse audit workbook and generate deterministic migration manifest

**Script:** `scripts/ops/hoc_phase0_manifest_generator.py`

### Input

| Artifact | Path |
|----------|------|
| Audit Workbook | `backend/app/hoc/cus/_domain_map/V3_MANUAL_AUDIT_WORKBOOK.md` |

### Process

1. Parse markdown for `### [x]` and `### [~]` file entries
2. Extract: filename, current domain, DECISION target domain, reason
3. Filter only `⚠️ (MISPLACED)` entries
4. Resolve full current path from filesystem
5. Compute target path based on layer convention
6. Generate deterministic manifest (sorted by file path)

### Output

| Artifact | Path |
|----------|------|
| Migration Manifest | `backend/app/hoc/cus/_domain_map/MIGRATION_MANIFEST.csv` |
| Manifest Summary | `backend/app/hoc/cus/_domain_map/MIGRATION_SUMMARY.md` |

### CSV Schema

```csv
migration_id,current_path,current_domain,current_layer,target_domain,target_layer,target_path,reason,status,hash_before
001,activity/L6_drivers/threshold_driver.py,activity,L6_drivers,controls,L6_drivers,controls/L6_drivers/threshold_driver.py,"Accesses Limit tables",PENDING,<sha256>
```

### Validation

- [ ] All 84 MISPLACED files parsed
- [ ] All current paths exist on filesystem
- [ ] No duplicate migration_ids
- [ ] Hash computed for each file

### Exit Criteria

```python
assert manifest.count() == 84
assert manifest.all_files_exist() == True
assert manifest.duplicates() == 0
```

---

## Phase 1: Validate Migration Plan

**Purpose:** Pre-flight validation before any file moves

**Script:** `scripts/ops/hoc_phase1_migration_validator.py`

### Input

| Artifact | Path |
|----------|------|
| Migration Manifest | `backend/app/hoc/cus/_domain_map/MIGRATION_MANIFEST.csv` |

### Process

1. **File Existence Check:** Verify all source files exist
2. **Target Collision Check:** Ensure no target path already exists
3. **Import Graph Analysis:**
   - Parse AST of each file
   - Extract all imports
   - Build dependency graph
4. **Circular Dependency Detection:** Check for cycles in post-migration state
5. **Caller Impact Analysis:**
   - Find all files that import each migrating file
   - Estimate import update count
6. **Layer Compliance Check:** Verify target layer matches file type

### Output

| Artifact | Path |
|----------|------|
| Validation Report | `backend/app/hoc/cus/_domain_map/PHASE1_VALIDATION_REPORT.md` |
| Import Graph | `backend/app/hoc/cus/_domain_map/PHASE1_IMPORT_GRAPH.json` |
| Caller Map | `backend/app/hoc/cus/_domain_map/PHASE1_CALLER_MAP.csv` |

### Caller Map Schema

```csv
migrating_file,caller_file,import_statement,update_required
activity/L6_drivers/threshold_driver.py,activity/L5_engines/threshold_engine.py,"from ..L6_drivers.threshold_driver import",YES
```

### Validation Checks

| Check | Pass Criteria |
|-------|---------------|
| FILES_EXIST | 84/84 source files found |
| NO_COLLISION | 0 target paths already exist |
| NO_CYCLES | 0 circular dependencies detected |
| LAYER_COMPLIANT | 84/84 files match target layer convention |

### Exit Criteria

```python
assert validation_report.files_exist == 84
assert validation_report.collisions == 0
assert validation_report.cycles == 0
assert validation_report.status == "READY_FOR_MIGRATION"
```

---

## Phase 2: Execute Migration

**Purpose:** Move files and update all imports deterministically

**Script:** `scripts/ops/hoc_phase2_migration_executor.py`

### Input

| Artifact | Path |
|----------|------|
| Migration Manifest | `backend/app/hoc/cus/_domain_map/MIGRATION_MANIFEST.csv` |
| Caller Map | `backend/app/hoc/cus/_domain_map/PHASE1_CALLER_MAP.csv` |

### Process (Per File)

1. **Pre-Move Snapshot:**
   - Compute file hash
   - Record all current imports
2. **Move File:**
   - Create target directory if needed
   - Move file to target path
   - Preserve file permissions
3. **Update Self-Imports:**
   - Parse AST
   - Update relative imports to match new location
4. **Update Callers:**
   - For each caller in caller map
   - Update import statement
   - Verify import still resolves
5. **Post-Move Validation:**
   - Compute new hash (content unchanged except imports)
   - Verify file importable from new location

### Execution Modes

```bash
# Dry run - show what would happen
python scripts/ops/hoc_phase2_migration_executor.py --dry-run

# Execute with backup
python scripts/ops/hoc_phase2_migration_executor.py --execute --backup

# Execute single file (for debugging)
python scripts/ops/hoc_phase2_migration_executor.py --execute --file activity/L6_drivers/threshold_driver.py
```

### Output

| Artifact | Path |
|----------|------|
| Execution Log | `backend/app/hoc/cus/_domain_map/PHASE2_EXECUTION_LOG.csv` |
| Backup Archive | `backups/hoc_migration_<timestamp>.tar.gz` |
| Updated Manifest | `backend/app/hoc/cus/_domain_map/MIGRATION_MANIFEST.csv` (status updated) |

### Execution Log Schema

```csv
migration_id,timestamp,action,source_path,target_path,callers_updated,status,error
001,2026-01-27T10:00:00Z,MOVE,activity/L6_drivers/threshold_driver.py,controls/L6_drivers/threshold_driver.py,3,SUCCESS,
```

### Rollback Capability

```bash
# Rollback all migrations
python scripts/ops/hoc_phase2_migration_executor.py --rollback --backup backups/hoc_migration_<timestamp>.tar.gz
```

### Exit Criteria

```python
assert execution_log.success_count == 84
assert execution_log.failure_count == 0
assert all_imports_resolve() == True
```

---

## Phase 3: Lock Domains

**Purpose:** Freeze domain structure to prevent drift

**Script:** `scripts/ops/hoc_phase3_domain_locker.py`

### Input

| Artifact | Path |
|----------|------|
| Phase 2 Execution Log | `backend/app/hoc/cus/_domain_map/PHASE2_EXECUTION_LOG.csv` |

### Process (Per Domain)

1. **Inventory Domain:**
   - List all `.py` files
   - Compute hash per file
   - Record layer distribution
2. **Generate Lock File:**
   - Domain metadata
   - File inventory with hashes
   - Layer structure
   - Authorized modification rules
3. **Create CI Guard:**
   - Generate domain-specific validation rules
   - Add to BLCA configuration

### Output

| Artifact | Path |
|----------|------|
| Domain Lock (per domain) | `backend/app/hoc/cus/{domain}/DOMAIN_LOCK_FINAL.md` |
| Lock Registry | `backend/app/hoc/cus/_domain_map/DOMAIN_LOCK_REGISTRY.json` |
| CI Guard Config | `backend/app/hoc/cus/_domain_map/DOMAIN_CI_GUARDS.yaml` |

### Domain Lock File Format

```markdown
# {DOMAIN} Domain Lock

**Locked:** 2026-01-27
**Lock Version:** 1.0
**Files:** 45
**Hash:** <sha256 of all file hashes>

## Layer Distribution
| Layer | Files |
|-------|-------|
| L5_engines | 30 |
| L6_drivers | 15 |

## File Inventory
| File | Layer | Hash |
|------|-------|------|
| threshold_driver.py | L6_drivers | abc123... |

## Modification Rules
- New files: ALLOWED (must follow layer convention)
- Delete files: REQUIRES_APPROVAL
- Move files: BLOCKED (use migration process)
- Rename files: BLOCKED
```

### CI Guard Rules

```yaml
domain_guards:
  controls:
    locked_at: "2026-01-27"
    file_count: 45
    allowed_operations:
      - ADD_FILE
    blocked_operations:
      - DELETE_FILE
      - MOVE_FILE
      - RENAME_FILE
```

### Exit Criteria

```python
assert all_domains_locked() == True
assert lock_registry.domains == 11  # all customer domains
assert ci_guards_generated() == True
```

---

## Phase 4: Post-Migration Validation

**Purpose:** Comprehensive validation that migration succeeded

**Script:** `scripts/ops/hoc_phase4_post_migration_validator.py`

### Input

| Artifact | Path |
|----------|------|
| Domain Lock Registry | `backend/app/hoc/cus/_domain_map/DOMAIN_LOCK_REGISTRY.json` |
| Migration Manifest | `backend/app/hoc/cus/_domain_map/MIGRATION_MANIFEST.csv` |

### Validation Suite

#### V1: Import Resolution

```python
# Every Python file must import without error
for file in all_hoc_files():
    assert importlib.import_module(file) succeeds
```

#### V2: BLCA Layer Validation

```bash
python scripts/ops/layer_validator.py --backend --ci
# Must return 0 violations
```

#### V3: Test Suite

```bash
cd backend && pytest tests/hoc/ -v
# All HOC tests must pass
```

#### V4: Circular Import Detection

```python
# No circular imports in HOC
assert detect_circular_imports("backend/app/hoc/cus/") == []
```

#### V5: Domain Integrity

```python
# Each file exists in exactly one domain
for file in migrated_files:
    assert file_exists_in_exactly_one_domain(file)
```

#### V6: Hash Verification

```python
# Lock file hashes match actual files
for domain in domains:
    assert verify_domain_hashes(domain) == True
```

### Output

| Artifact | Path |
|----------|------|
| Validation Report | `backend/app/hoc/cus/_domain_map/PHASE4_VALIDATION_REPORT.md` |
| Test Results | `backend/app/hoc/cus/_domain_map/PHASE4_TEST_RESULTS.xml` |
| Health Score | `backend/app/hoc/cus/_domain_map/PHASE4_HEALTH_SCORE.json` |

### Health Score Schema

```json
{
  "overall": "HEALTHY",
  "score": 100,
  "checks": {
    "import_resolution": {"status": "PASS", "score": 100},
    "blca_validation": {"status": "PASS", "violations": 0},
    "test_suite": {"status": "PASS", "passed": 150, "failed": 0},
    "circular_imports": {"status": "PASS", "cycles": 0},
    "domain_integrity": {"status": "PASS", "orphans": 0},
    "hash_verification": {"status": "PASS", "mismatches": 0}
  }
}
```

### Exit Criteria

```python
assert health_score.overall == "HEALTHY"
assert health_score.score >= 95
assert blca_violations == 0
assert test_failures == 0
```

---

## Phase 5: Duplicate Detection

**Purpose:** Identify all duplicates across domains using 3 detection modes

**Script:** `scripts/ops/hoc_phase5_duplicate_detector.py`

### Input

| Artifact | Path |
|----------|------|
| Domain Lock Registry | `backend/app/hoc/cus/_domain_map/DOMAIN_LOCK_REGISTRY.json` |

### Detection Modes

#### Mode 1: Exact File Match (Hash)

```python
# Files with identical content (SHA-256)
for file_a, file_b in all_file_pairs():
    if sha256(file_a) == sha256(file_b):
        report_exact_duplicate(file_a, file_b)
```

#### Mode 2: Function Signature Match

```python
# Functions with identical signatures across domains
for func_a, func_b in all_function_pairs():
    sig_a = extract_signature(func_a)  # name, params, return type
    sig_b = extract_signature(func_b)
    if sig_a == sig_b:
        body_similarity = compare_ast(func_a.body, func_b.body)
        report_function_duplicate(func_a, func_b, body_similarity)
```

#### Mode 3: Block Similarity

```python
# Code blocks with >80% similarity (Rabin-Karp rolling hash)
BLOCK_SIZE = 10  # lines
SIMILARITY_THRESHOLD = 0.80

for block_a, block_b in all_block_pairs():
    similarity = sequence_matcher(block_a, block_b)
    if similarity >= SIMILARITY_THRESHOLD:
        report_block_duplicate(block_a, block_b, similarity)
```

### Output

| Artifact | Path |
|----------|------|
| Duplicate Report | `backend/app/hoc/cus/_domain_map/PHASE5_DUPLICATE_REPORT.csv` |
| Duplicate Summary | `backend/app/hoc/cus/_domain_map/PHASE5_DUPLICATE_SUMMARY.md` |
| Consolidation Candidates | `backend/app/hoc/cus/_domain_map/PHASE5_CONSOLIDATION_CANDIDATES.csv` |

### Duplicate Report Schema

```csv
duplicate_id,type,domain_a,file_a,location_a,domain_b,file_b,location_b,similarity_pct,recommendation
D001,EXACT_FILE,logs,idempotency.py,-,general,idempotency.py,-,100,DELETE_FROM_LOGS
D002,FUNCTION,incidents,pdf_renderer.py:45-80,logs,pdf_renderer.py:30-65,PDFRenderer.render(),95,EXTRACT_TO_GENERAL
D003,BLOCK,policies,engine.py:100-115,incidents,engine.py:200-215,-,87,REVIEW_FOR_SHARED_UTIL
```

### Consolidation Candidates Schema

```csv
candidate_id,duplicate_ids,canonical_location,delete_locations,estimated_savings_loc
C001,"D001",general/L6_drivers/idempotency.py,"logs/L6_drivers/idempotency.py",150
C002,"D002,D003",general/L5_engines/pdf_renderer.py,"logs/L5_engines/pdf_renderer.py,incidents/L5_engines/pdf_renderer.py",400
```

### Exit Criteria

```python
assert duplicate_report.generated == True
assert consolidation_candidates.count > 0
# Generates actionable list for Phase 6
```

---

## Phase 6: Consolidate General

**Purpose:** Remove duplicates from domain folders, keep canonical in general/

**Script:** `scripts/ops/hoc_phase6_consolidator.py`

### Input

| Artifact | Path |
|----------|------|
| Consolidation Candidates | `backend/app/hoc/cus/_domain_map/PHASE5_CONSOLIDATION_CANDIDATES.csv` |
| Duplicate Report | `backend/app/hoc/cus/_domain_map/PHASE5_DUPLICATE_REPORT.csv` |

### Process (Per Consolidation Candidate)

1. **Identify Canonical Version:**
   - Prefer `general/` if exists
   - Otherwise, pick most complete version (superset of functions)
   - Record decision rationale

2. **Merge Functions (if needed):**
   - If versions have different functions, merge into canonical
   - Track added functions

3. **Update Callers:**
   - Find all imports of non-canonical versions
   - Update to import from canonical location

4. **Delete Non-Canonical:**
   - Remove duplicate files from domain folders
   - Update domain lock files

5. **Verify:**
   - All callers still resolve
   - No broken imports

### Execution Modes

```bash
# Dry run
python scripts/ops/hoc_phase6_consolidator.py --dry-run

# Execute specific candidate
python scripts/ops/hoc_phase6_consolidator.py --execute --candidate C001

# Execute all
python scripts/ops/hoc_phase6_consolidator.py --execute --all
```

### Output

| Artifact | Path |
|----------|------|
| Consolidation Log | `backend/app/hoc/cus/_domain_map/PHASE6_CONSOLIDATION_LOG.csv` |
| Updated Domain Locks | `backend/app/hoc/cus/{domain}/DOMAIN_LOCK_FINAL.md` (updated) |
| LOC Savings Report | `backend/app/hoc/cus/_domain_map/PHASE6_LOC_SAVINGS.md` |

### Consolidation Log Schema

```csv
candidate_id,timestamp,canonical_path,deleted_paths,callers_updated,functions_merged,status
C001,2026-01-27T12:00:00Z,general/L6_drivers/idempotency.py,"logs/L6_drivers/idempotency.py",5,0,SUCCESS
```

### Exit Criteria

```python
assert consolidation_log.success_count == total_candidates
assert consolidation_log.failure_count == 0
assert all_imports_resolve() == True
assert loc_savings > 0
```

---

## Phase 7: Refactor Domain Clusters

**Purpose:** Consolidate related files within domains (e.g., logs export/evidence cluster)

**Script:** `scripts/ops/hoc_phase7_cluster_refactor.py`

### Input

| Artifact | Path |
|----------|------|
| Domain Lock Registry | `backend/app/hoc/cus/_domain_map/DOMAIN_LOCK_REGISTRY.json` |
| Cluster Definitions | `backend/app/hoc/cus/_domain_map/CLUSTER_DEFINITIONS.yaml` |

### Cluster Definitions (Manual Input Required)

```yaml
clusters:
  logs_export_evidence:
    domain: logs
    description: "Export/Evidence/PDF/Compliance cluster"
    current_files:
      - L5_engines/evidence_facade.py
      - L5_engines/evidence_report.py
      - L5_engines/export_bundle_adapter.py
      - L5_engines/export_bundle_store.py
      - L5_engines/export_completeness_checker.py
      - L5_engines/compliance_facade.py
      - L5_engines/pdf_renderer.py
      - L5_engines/certificate.py
      - L5_engines/audit_evidence.py
    target_structure:
      evidence_engine.py:
        - EvidenceFacade
        - EvidenceChain
        - EvidenceExport
      export_engine.py:
        - ExportBundleAdapter
        - ExportBundleStore
        - ExportCompletenessChecker
        - PDFRenderer
      compliance_engine.py:
        - ComplianceFacade
        - CertificateGenerator

  policies_dsl_infrastructure:
    domain: policies
    description: "DSL/Compiler infrastructure"
    current_files:
      - L5_engines/compiler_parser.py
      - L5_engines/grammar.py
      - L5_engines/tokenizer.py
      - L5_engines/ast.py
      - L5_engines/ir_builder.py
      - L5_engines/ir_compiler.py
      - L5_engines/ir_nodes.py
    target_domain: general
    target_structure:
      L5_dsl/parser.py: [compiler_parser, grammar, tokenizer]
      L5_dsl/ast.py: [ast, ir_nodes]
      L5_dsl/compiler.py: [ir_builder, ir_compiler]
```

### Process (Per Cluster)

1. **Analyze Cluster:**
   - Parse all files in cluster
   - Extract classes/functions
   - Build internal dependency graph

2. **Generate Refactor Plan:**
   - Map current -> target structure
   - Identify function movements
   - Calculate merge strategy

3. **Execute Refactor:**
   - Create new consolidated files
   - Move functions/classes
   - Update internal imports
   - Update external callers

4. **Cleanup:**
   - Delete original fragmented files
   - Update domain lock

### Output

| Artifact | Path |
|----------|------|
| Refactor Plan | `backend/app/hoc/cus/_domain_map/PHASE7_REFACTOR_PLAN.md` |
| Refactor Log | `backend/app/hoc/cus/_domain_map/PHASE7_REFACTOR_LOG.csv` |
| Updated Domain Locks | `backend/app/hoc/cus/{domain}/DOMAIN_LOCK_FINAL.md` |

### Refactor Log Schema

```csv
cluster_id,timestamp,original_files,new_files,functions_moved,callers_updated,loc_before,loc_after,status
logs_export_evidence,2026-01-27T14:00:00Z,9,3,45,23,2500,1800,SUCCESS
```

### Exit Criteria

```python
assert refactor_log.all_clusters_processed == True
assert refactor_log.failure_count == 0
assert all_imports_resolve() == True
assert loc_reduction > 0
```

---

## Phase 8: Audit & Import Path Normalization

**Purpose:** Final audit and normalize all import paths to use general/ for shared utilities

**Script:** `scripts/ops/hoc_phase8_import_normalizer.py`

### Input

| Artifact | Path |
|----------|------|
| Domain Lock Registry | `backend/app/hoc/cus/_domain_map/DOMAIN_LOCK_REGISTRY.json` |
| General Exports | `backend/app/hoc/cus/general/__init__.py` |

### Process

#### Step 1: Build General Export Registry

```python
# Catalog all public exports from general/
general_exports = {
    "runtime_switch": "general.L5_engines.runtime_switch",
    "lifecycle_facade": "general.L5_engines.lifecycle_facade",
    "idempotency": "general.L6_drivers.idempotency",
    ...
}
```

#### Step 2: Scan All Domain Imports

```python
# Find imports that should use general/
for domain in domains:
    for file in domain.files:
        for import_stmt in file.imports:
            if import_stmt.target in general_exports:
                if import_stmt.source != general_exports[import_stmt.target]:
                    report_non_canonical_import(file, import_stmt)
```

#### Step 3: Normalize Imports

```python
# Update imports to use canonical general/ paths
for file, import_stmt in non_canonical_imports:
    old_import = import_stmt.source
    new_import = general_exports[import_stmt.target]
    update_import(file, old_import, new_import)
```

#### Step 4: Generate Dependency Matrix

```python
# Domain -> Domain dependency matrix
matrix[domain_a][domain_b] = count_of_imports
```

#### Step 5: Validate Architecture

```python
# Check import direction compliance
# Domains should import FROM general, not from each other
for import_stmt in all_imports:
    if is_cross_domain(import_stmt) and not is_from_general(import_stmt):
        report_architecture_violation(import_stmt)
```

### Output

| Artifact | Path |
|----------|------|
| General Export Registry | `backend/app/hoc/cus/general/EXPORT_REGISTRY.yaml` |
| Import Normalization Log | `backend/app/hoc/cus/_domain_map/PHASE8_IMPORT_LOG.csv` |
| Dependency Matrix | `backend/app/hoc/cus/_domain_map/PHASE8_DEPENDENCY_MATRIX.csv` |
| Architecture Compliance Report | `backend/app/hoc/cus/_domain_map/PHASE8_ARCHITECTURE_REPORT.md` |
| Final Domain Health | `backend/app/hoc/cus/_domain_map/PHASE8_FINAL_HEALTH.json` |

### Dependency Matrix Schema

```csv
from_domain,to_domain,import_count,compliant
activity,general,15,YES
activity,policies,0,YES
incidents,general,12,YES
incidents,logs,2,VIOLATION
```

### Architecture Compliance Rules

| Rule | Description |
|------|-------------|
| ARCH-001 | Domains MAY import from `general/` |
| ARCH-002 | Domains MUST NOT import from other domains (except via general) |
| ARCH-003 | `general/` MUST NOT import from any domain |
| ARCH-004 | All shared utilities MUST be in `general/` |

### Final Health Report

```json
{
  "overall": "COMPLIANT",
  "domains": 11,
  "total_files": 458,
  "total_imports": 2340,
  "canonical_imports": 2340,
  "violations": 0,
  "dependency_matrix": "CLEAN",
  "architecture_compliance": 100,
  "phases_completed": ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
}
```

### Exit Criteria

```python
assert final_health.overall == "COMPLIANT"
assert final_health.violations == 0
assert final_health.architecture_compliance == 100
assert all_phases_completed() == True
```

---

## Script Inventory

| Phase | Script | Purpose |
|-------|--------|---------|
| P0 | `scripts/ops/hoc_phase0_manifest_generator.py` | Parse workbook -> migration manifest |
| P1 | `scripts/ops/hoc_phase1_migration_validator.py` | Validate plan, build import graph |
| P2 | `scripts/ops/hoc_phase2_migration_executor.py` | Move files, update imports |
| P3 | `scripts/ops/hoc_phase3_domain_locker.py` | Lock domains, generate CI guards |
| P4 | `scripts/ops/hoc_phase4_post_migration_validator.py` | Full validation suite |
| P5 | `scripts/ops/hoc_phase5_duplicate_detector.py` | 3-mode duplicate detection |
| P6 | `scripts/ops/hoc_phase6_consolidator.py` | Merge duplicates into general/ |
| P7 | `scripts/ops/hoc_phase7_cluster_refactor.py` | Refactor domain clusters |
| P8 | `scripts/ops/hoc_phase8_import_normalizer.py` | Normalize imports, final audit |

## Execution Sequence

```bash
# Phase 0
python scripts/ops/hoc_phase0_manifest_generator.py

# Phase 1
python scripts/ops/hoc_phase1_migration_validator.py

# Phase 2 (with backup)
python scripts/ops/hoc_phase2_migration_executor.py --execute --backup

# Phase 3
python scripts/ops/hoc_phase3_domain_locker.py

# Phase 4
python scripts/ops/hoc_phase4_post_migration_validator.py

# Phase 5
python scripts/ops/hoc_phase5_duplicate_detector.py

# Phase 6
python scripts/ops/hoc_phase6_consolidator.py --execute --all

# Phase 7 (requires cluster definitions)
python scripts/ops/hoc_phase7_cluster_refactor.py --execute

# Phase 8
python scripts/ops/hoc_phase8_import_normalizer.py --execute
```

---

## Dependencies Between Phases

```
P0 ──→ P1 ──→ P2 ──→ P3 ──→ P4
                                ↓
                           P5 ──→ P6 ──→ P7 ──→ P8
```

- P0-P4: Migration pipeline (sequential, blocking)
- P5-P8: Cleanup pipeline (sequential, blocking)
- P4 must pass before P5 begins

## Rollback Strategy

Each phase produces artifacts that enable rollback:

| Phase | Rollback Method |
|-------|-----------------|
| P2 | `--rollback --backup <archive>` |
| P6 | Re-run P5, restore from domain locks |
| P7 | Restore from pre-refactor backup |
| P8 | Re-run P8 with `--revert` flag |
