# Phase 3: Directory Restructure Plan

**Version:** 1.1.0
**Status:** APPROVED
**Date:** 2026-01-24
**Author:** Founder + Claude (Architecture Session)
**Reference:** HOC_LAYER_TOPOLOGY_V1.md

---

## 1. Executive Summary

This document defines the directory restructuring plan for HOC customer domains. The goal is to make layer membership explicit in folder names, eliminating HEADER_LOCATION_MISMATCH issues and improving code navigation.

**Key Principles:**
- **Package rename:** `hoc` → `hoc` (saves import path space)
- Layer prefix in folder names (L3_, L5_, L6_)
- L4 is centralized in `general/L4_runtime/` only
- L7 models stay centralized at `app/models/`
- L2/L2.1 APIs nest together at `hoc/api/cus/{domain}/`

---

## 1.1 Package & Audience Renames

**Rationale:** Shorter names save import path characters and improve readability.

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Package | `hoc` | `hoc` | 9 chars |
| Audience | `customer` | `cus` | 5 chars |
| **Total** | | | **14 chars per import** |

### Full Path Comparison

| Before | After | Savings |
|--------|-------|---------|
| `from hoc.cus.activity.L5_engines import ...` | `from hoc.cus.activity.L5_engines import ...` | 14 chars |
| `backend/app/hoc/cus/` | `backend/app/hoc/cus/` | 14 chars in path |

### Audience Rename Mapping

| Before | After |
|--------|-------|
| `customer/` | `cus/` |
| `founder/` | `fdr/` |
| `internal/` | `int/` |

**Migration Step:** Both renames are executed FIRST, before layer-prefix restructure.

---

## 2. Target Directory Structure

### 2.1 Standard Domains

Applies to: activity, analytics, incidents, policies, logs, overview, api_keys, account, integrations

```
hoc/cus/{domain}/
├── __init__.py
├── L3_adapters/           # L3 — Translation, bridges, cross-domain
│   └── __init__.py
├── L5_engines/            # L5 — Business logic (absorbs current facades)
│   └── __init__.py
├── L5_schemas/            # L5 — Dataclasses, types, enums
│   └── __init__.py
└── L6_drivers/            # L6 — Data access
    └── __init__.py
```

### 2.2 General Domain (Meta/Cross-Domain)

```
hoc/cus/general/
├── __init__.py
├── L4_runtime/            # L4 — Control plane, gateway (ONLY L4)
│   ├── __init__.py
│   ├── authority/
│   ├── execution/
│   ├── consequences/
│   └── contracts/
├── L3_mcp/                # L3 — Cross-domain MCP adapters
│   └── __init__.py
├── L5_controls/           # L5 — Control engines (killswitch, guards)
│   └── __init__.py
├── L5_lifecycle/          # L5 — Lifecycle management
│   └── __init__.py
├── L5_workflow/           # L5 — Workflow contracts
│   └── __init__.py
├── L5_schemas/            # L5 — Shared schemas
│   └── __init__.py
├── L5_utils/              # L5 — Shared utilities
│   └── __init__.py
├── L5_ui/                 # L5 — UI projection logic
│   └── __init__.py
└── L6_drivers/            # L6 — Shared data access
    └── __init__.py
```

### 2.3 API Layer Structure

```
hoc/api/cus/{domain}/
├── __init__.py
├── {domain}_facade.py     # L2.1 — API composition
└── {domain}_routes.py     # L2 — HTTP handlers
```

### 2.4 Centralized (Unchanged)

```
app/models/                # L7 — ORM models (centralized)
```

---

## 3. Migration Mapping

### 3.1 Standard Domains

| Current Folder | Action | New Folder |
|----------------|--------|------------|
| `{domain}/adapters/` | RENAME | `{domain}/L3_adapters/` |
| `{domain}/bridges/` | MERGE INTO | `{domain}/L3_adapters/` |
| `{domain}/facades/` | MERGE INTO | `{domain}/L5_engines/` |
| `{domain}/engines/` | RENAME | `{domain}/L5_engines/` |
| `{domain}/schemas/` | RENAME | `{domain}/L5_schemas/` |
| `{domain}/drivers/` | RENAME | `{domain}/L6_drivers/` |

### 3.2 General Domain

| Current Folder | Action | New Folder |
|----------------|--------|------------|
| `general/runtime/` | RENAME | `general/L4_runtime/` |
| `general/controls/` | RENAME | `general/L5_controls/` |
| `general/lifecycle/` | RENAME | `general/L5_lifecycle/` |
| `general/workflow/` | RENAME | `general/L5_workflow/` |
| `general/mcp/` | RENAME | `general/L3_mcp/` |
| `general/ui/` | RENAME | `general/L5_ui/` |
| `general/utils/` | RENAME | `general/L5_utils/` |
| `general/schemas/` | RENAME | `general/L5_schemas/` |
| `general/drivers/` | RENAME | `general/L6_drivers/` |
| `general/engines/` | DISTRIBUTE | `general/L5_*` (by function) |
| `general/facades/` | DISTRIBUTE | `general/L5_*` (by function) |

### 3.3 Special Cases

| Current | Action | Notes |
|---------|--------|-------|
| `{domain}/controls/` | MERGE INTO | `{domain}/L5_engines/` or `general/L5_controls/` |
| `{domain}/vault/` | RENAME | `{domain}/L5_vault/` or merge |
| `{domain}/notifications/` | RENAME | `{domain}/L5_notifications/` |
| `{domain}/support/` | RENAME | `{domain}/L5_support/` |

---

## 4. Import Update Rules

### 4.1 Package & Audience Rename (Step 1)

```python
# STEP 1: Package + audience rename (applied globally first)
# BEFORE
from hoc.cus.{domain}.engines import SomeEngine

# AFTER (renames only)
from hoc.cus.{domain}.engines import SomeEngine
```

### 4.2 Layer-Prefix Pattern Replacement (Step 2)

```python
# STEP 2: Layer-prefixed folders (applied per-domain)
# BEFORE (after package/audience rename)
from hoc.cus.{domain}.engines import SomeEngine
from hoc.cus.{domain}.drivers import SomeDriver
from hoc.cus.{domain}.adapters import SomeAdapter
from hoc.cus.{domain}.facades import SomeFacade
from hoc.cus.{domain}.schemas import SomeSchema

# AFTER (full migration)
from hoc.cus.{domain}.L5_engines import SomeEngine
from hoc.cus.{domain}.L6_drivers import SomeDriver
from hoc.cus.{domain}.L3_adapters import SomeAdapter
from hoc.cus.{domain}.L5_engines import SomeFacade  # Merged into engines
from hoc.cus.{domain}.L5_schemas import SomeSchema
```

### 4.3 Full Migration Example

```python
# ORIGINAL (current state)
from hoc.cus.activity.L5_engines import ActivityEngine
from hoc.cus.general.L4_runtime import Orchestrator

# FINAL (after Phase 3 complete)
from hoc.cus.activity.L5_engines import ActivityEngine
from hoc.cus.general.L4_runtime import Orchestrator
```

### 4.4 General Domain Patterns

```python
# BEFORE
from hoc.cus.general.L4_runtime import Orchestrator
from hoc.cus.general.L5_controls.engines import KillSwitch

# AFTER
from hoc.cus.general.L4_runtime import Orchestrator
from hoc.cus.general.L5_controls import KillSwitch
```

### 4.5 Other Audience Examples

```python
# Founder audience
# BEFORE: from hoc.fdr.ops.engines import OpsEngine
# AFTER:  from hoc.fdr.ops.L5_engines import OpsEngine

# Internal audience
# BEFORE: from hoc.int.platform.drivers import PlatformDriver
# AFTER:  from hoc.int.platform.L6_drivers import PlatformDriver
```

---

## 5. Migration Script Requirements

### 5.1 Script Features

The migration script (`scripts/ops/hoc_phase3_migrate.py`) must:

1. **DRY RUN MODE** — Preview changes without executing
2. **BACKUP** — Create backup before migration
3. **PACKAGE RENAME** — Rename `hoc/` to `hoc/` (global, first step)
4. **DOMAIN SELECTION** — Migrate one domain at a time
5. **IMPORT UPDATES** — Find and update all imports
6. **ROLLBACK** — Revert if errors detected
7. **REPORT** — Generate detailed migration report

### 5.2 Script Interface

```bash
# STEP 0: Package rename (run FIRST, once only)
python scripts/ops/hoc_phase3_migrate.py --rename-package --dry-run
python scripts/ops/hoc_phase3_migrate.py --rename-package

# Preview changes for activity domain
python scripts/ops/hoc_phase3_migrate.py --domain activity --dry-run

# Migrate activity domain
python scripts/ops/hoc_phase3_migrate.py --domain activity

# Migrate all domains
python scripts/ops/hoc_phase3_migrate.py --all

# Migrate general domain (special handling)
python scripts/ops/hoc_phase3_migrate.py --domain general

# Rollback last migration
python scripts/ops/hoc_phase3_migrate.py --rollback
```

### 5.3 Package & Audience Rename Steps (Global, Run First)

```
1. BACKUP backend/app/hoc/ to backup/
2. RENAME package folder: backend/app/hoc/ → backend/app/hoc/
3. RENAME audience folders:
   - hoc/cus/ → hoc/cus/
   - hoc/fdr/  → hoc/fdr/
   - hoc/int/ → hoc/int/
4. SCAN entire codebase for import patterns
5. REPLACE all:
   - "from hoc." → "from hoc."
   - "import hoc" → "import hoc"
   - ".cus." → ".cus."
   - ".fdr." → ".fdr."
   - ".int." → ".int."
6. UPDATE documentation references
7. VERIFY no broken imports (run tests)
8. GENERATE rename report
```

### 5.4 Migration Steps (Per Domain)

```
1. CREATE new folder structure (L3_adapters/, L5_engines/, etc.)
2. MOVE files from old folders to new folders
3. UPDATE __init__.py exports in new folders
4. SCAN entire codebase for imports from old paths
5. UPDATE imports to new paths
6. DELETE empty old folders
7. VERIFY no broken imports (run tests)
8. GENERATE migration report
```

---

## 6. File Header Updates

### 6.1 New Header Format

After migration, file headers should reflect new location:

```python
# Layer: L5 — Domain Engine
# Location: hoc/cus/{domain}/L5_engines/
# AUDIENCE: CUSTOMER
# Role: {description}
```

### 6.2 Header Location Field

The `Location:` field becomes redundant when folder name includes layer, but keep for clarity during transition.

---

## 7. Execution Order

### 7.0 Package & Audience Rename (FIRST)

```
0. Package + audience rename: hoc → hoc, customer → cus, founder → fdr, internal → int
   a. Run: python scripts/ops/hoc_phase3_migrate.py --rename-all --dry-run
   b. Review changes (expect ~500+ import updates)
   c. Execute: python scripts/ops/hoc_phase3_migrate.py --rename-all
   d. Run full test suite
   e. Commit: "chore: rename hoc → hoc, customer → cus, founder → fdr, internal → int"
```

### 7.1 Domain Migration Order

```
1. overview     (smallest, 6 files)
2. api_keys     (9 files)
3. account      (17 files)
4. activity     (15 files)
5. analytics    (41 files)
6. incidents    (47 files)
7. logs         (53 files)
8. integrations (62 files, has debt)
9. policies     (106 files, largest)
10. general     (59 files, special handling)
```

### 7.2 Per-Domain Process

```
1. Run migration script with --dry-run
2. Review changes
3. Execute migration
4. Run BLCA validation
5. Run test suite
6. Manual audit of complex files
7. Update domain lock document
8. Commit with migration message
```

---

## 8. Validation Checklist

### 8.1 Post-Migration Validation

For each domain:

- [ ] All files moved to new folders
- [ ] All imports updated
- [ ] `__init__.py` exports correct
- [ ] BLCA passes (0 violations)
- [ ] Test suite passes
- [ ] No orphaned files in old folders
- [ ] Lock document updated

### 8.2 Full Migration Validation

- [ ] All 10 customer domains migrated
- [ ] HOC_LAYER_TOPOLOGY_V1.md updated
- [ ] CLAUDE.md references updated
- [ ] HOC INDEX.md updated
- [ ] All lock documents updated

---

## 9. Rollback Plan

If migration fails:

1. **Restore from backup** — Script creates timestamped backup
2. **Git revert** — If committed, use git revert
3. **Manual restore** — Old folder names documented

---

## 10. Post-Migration Benefits

| Benefit | Description |
|---------|-------------|
| **Shorter imports** | 14 chars saved per import (`hoc.cus.` vs `hoc.cus.`) |
| **No HEADER_LOCATION_MISMATCH** | Folder name = Layer |
| **Self-documenting** | `L5_engines/` is clearly L5 |
| **Easier navigation** | Find L6 code → look in `L6_drivers/` |
| **CI enforcement** | Can validate layer from path alone |
| **Reduced confusion** | No "is this L5 or L6?" questions |
| **Import readability** | `from hoc.cus.activity.L5_engines` is compact and clear |
| **Consistent abbreviations** | `cus`/`fdr`/`int` match 3-char pattern |

---

## 11. Timeline

| Phase | Scope | Status |
|-------|-------|--------|
| Planning | This document | COMPLETE |
| Script Development | `hoc_phase3_migrate.py` | PENDING |
| **Package & Audience Rename** | `hoc` → `hoc`, `customer` → `cus`, etc. | PENDING |
| Pilot Migration | overview domain | PENDING |
| Full Migration | All domains | PENDING |
| Validation | BLCA + Tests | PENDING |
| Documentation | Lock docs, INDEX | PENDING |

---

## 12. References

- HOC_LAYER_TOPOLOGY_V1.md — Canonical layer architecture
- Phase 2.5E BLCA Report — Current compliance status
- Domain Lock Documents — Current file inventory

---

**END OF PLAN**
