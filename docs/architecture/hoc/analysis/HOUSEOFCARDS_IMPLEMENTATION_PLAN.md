# Houseofcards Implementation Plan

**Status:** PHASE 3 COMPLETE
**Created:** 2026-01-22
**Last Audit:** 2026-01-22
**Reference:** First-principles directory reorganization

---

## Completed Phases

### Phase 1: Structure Creation ✅

- Created `app/houseofcards/{audience}/{domain}/{role}/` structure
- Audiences: customer, internal, founder
- Roles: facades, engines, drivers, schemas

### Phase 2: File Copy ✅

- Copied **167 files** from `app/services/` to `app/houseofcards/`
- Original files preserved as fallback
- Iterative classification with user decisions
- 15 facade files renamed for clarity (`facade.py` → `{domain}_facade.py`)

### Phase 3: BLCA Validation ✅

- Layer validator passed: **0 violations**
- **1452 files** scanned
- Architecture clean

---

## Deep Audit Results (2026-01-22)

### Coverage Summary

| Metric | Value |
|--------|-------|
| app/services/ total files | 167 |
| app/houseofcards/ total files | 170 |
| Unique basenames in services | 153 |
| Files MISSING from houseofcards | **0** |
| BLCA Status | PASS |

### File Distribution

| Audience | Files |
|----------|-------|
| customer/ | 133 |
| internal/ | 30 |
| founder/ | 7 |
| **TOTAL** | **170** |

### Facade Renames

15 `facade.py` files were renamed for disambiguation:

| Source | Destination |
|--------|-------------|
| `services/alerts/facade.py` | `alerts_facade.py` |
| `services/compliance/facade.py` | `compliance_facade.py` |
| `services/connectors/facade.py` | `connectors_facade.py` |
| `services/controls/facade.py` | `controls_facade.py` |
| `services/datasources/facade.py` | `datasources_facade.py` |
| `services/detection/facade.py` | `detection_facade.py` |
| `services/evidence/facade.py` | `evidence_facade.py` |
| `services/governance/facade.py` | `governance_facade.py` |
| `services/lifecycle/facade.py` | `lifecycle_facade.py` |
| `services/limits/facade.py` | `limits_facade.py` |
| `services/monitors/facade.py` | `monitors_facade.py` |
| `services/notifications/facade.py` | `notifications_facade.py` |
| `services/ops/facade.py` | `ops_facade.py` |
| `services/retrieval/facade.py` | `retrieval_facade.py` |
| `services/scheduler/facade.py` | `scheduler_facade.py` |

### Subdirectory Coverage (40 total)

All subdirectories fully covered:

| Subdirectory | Files | Status |
|--------------|-------|--------|
| root level | 62 | ✅ |
| ai_console_panel_adapter/ | 17 | ✅ |
| governance/ | 13 | ✅ |
| activity/ | 5 | ✅ |
| connectors/ | 5 | ✅ |
| incidents/ | 5 | ✅ |
| limits/ | 5 | ✅ |
| audit/ | 4 | ✅ |
| lifecycle_stages/ | 4 | ✅ |
| policy/ | 4 | ✅ |
| scheduler/ | 4 | ✅ |
| mcp/ | 3 | ✅ |
| alerts/ | 2 | ✅ |
| credentials/ | 2 | ✅ |
| datasources/ | 2 | ✅ |
| iam/ | 2 | ✅ |
| notifications/ | 2 | ✅ |
| ops/ | 2 | ✅ |
| sandbox/ | 2 | ✅ |
| soc2/ | 2 | ✅ |
| compliance/ | 1 | ✅ |
| controls/ | 1 | ✅ |
| detection/ | 1 | ✅ |
| evidence/ | 1 | ✅ |
| export/ | 1 | ✅ |
| governance/degraded/ | 1 | ✅ |
| hallucination/ | 1 | ✅ |
| inspection/ | 1 | ✅ |
| killswitch/ | 1 | ✅ |
| knowledge/ | 1 | ✅ |
| lifecycle/ | 1 | ✅ |
| logging/ | 1 | ✅ |
| mediation/ | 1 | ✅ |
| monitors/ | 1 | ✅ |
| observability/ | 1 | ✅ |
| override/ | 1 | ✅ |
| platform/ | 1 | ✅ |
| pools/ | 1 | ✅ |
| retrieval/ | 1 | ✅ |
| rok/ | 1 | ✅ |

---

## Remaining Phases

### Phase 4: Consolidation (NEXT)

**Objective:** Remove duplicate logic, identify shared code.

#### Step 4.1: Identify Duplicates
```bash
# Find files with same name in both locations
comm -12 \
  <(find app/services -name "*.py" -exec basename {} \; | sort -u) \
  <(find app/houseofcards -name "*.py" -exec basename {} \; | sort -u)
```

#### Step 4.2: Compare Content
For each duplicate:
1. Compare file hashes (are they identical?)
2. If identical → safe to remove from services
3. If different → investigate which is canonical

#### Step 4.3: Mark Deprecated
Add deprecation header to `app/services/` files:
```python
# DEPRECATED: Use app.houseofcards.{audience}.{domain}.{role} instead
# Migration target: app/houseofcards/customer/policies/engines/limits_engine.py
```

#### Step 4.4: Audit Imports
Generate import dependency graph:
```bash
# Find all imports of app.services
grep -r "from app.services" app/ --include="*.py" | wc -l
grep -r "import app.services" app/ --include="*.py" | wc -l
```

---

### Phase 5: Wire Imports

**Objective:** Update all import statements to use new paths.

#### Step 5.1: Create Import Mapping
Generate mapping file:
```yaml
# import_mapping.yaml
mappings:
  - old: app.services.policies_facade
    new: app.houseofcards.customer.policies.facades.policies_facade
  - old: app.services.incident_aggregator
    new: app.houseofcards.customer.incidents.engines.incident_aggregator
  # ... etc
```

#### Step 5.2: Batch Update (Low Risk)
Start with internal imports within houseofcards:
```bash
# Update imports inside houseofcards first
find app/houseofcards -name "*.py" -exec grep -l "from app.services" {} \;
```

#### Step 5.3: Batch Update (Medium Risk)
Update L2 API imports:
```bash
# Find API files importing from services
find app/api -name "*.py" -exec grep -l "from app.services" {} \;
```

#### Step 5.4: Batch Update (High Risk)
Update worker/runtime imports:
```bash
# Find worker files importing from services
find app/worker -name "*.py" -exec grep -l "from app.services" {} \;
```

#### Step 5.5: Validate Each Batch
After each batch:
1. Run BLCA: `python3 scripts/ops/layer_validator.py --backend --ci`
2. Run tests: `pytest tests/ -x`
3. If failures → rollback batch, investigate

---

### Phase 6: Deprecate app/services/

**Objective:** Mark old location as deprecated, prevent new additions.

#### Step 6.1: Add __init__.py Warning
```python
# app/services/__init__.py
import warnings
warnings.warn(
    "app.services is deprecated. Use app.houseofcards instead. "
    "See docs/architecture/HOUSEOFCARDS_DIRECTORY_DESIGN.md",
    DeprecationWarning,
    stacklevel=2
)
```

#### Step 6.2: CI Guard
Add pre-commit hook to block new files in `app/services/`:
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: no-new-services
      name: Block new files in app/services
      entry: bash -c 'git diff --cached --name-only | grep "^backend/app/services/" && exit 1 || exit 0'
      language: system
```

#### Step 6.3: Documentation Update
- Update CLAUDE.md with new import paths
- Update API documentation
- Update SDK documentation

---

### Phase 7: Cleanup (Final)

**Objective:** Remove deprecated code after stabilization period.

#### Step 7.1: Stabilization Period
- Run in production for 2 weeks minimum
- Monitor for import errors
- Collect deprecation warnings

#### Step 7.2: Remove Deprecated Files
```bash
# Only after stabilization
rm -rf app/services/*.py  # Keep __init__.py with redirect
```

#### Step 7.3: Final Validation
- Full test suite
- BLCA validation
- Production smoke tests

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Broken imports | Keep originals as fallback during transition |
| Test failures | Batch updates with validation after each |
| Production issues | Deprecation warnings before removal |
| Lost changes | Git history preserved, files copied not moved |

---

## Rollback Plan

If issues arise during any phase:

1. **Phase 4-5**: Revert import changes via git
2. **Phase 6**: Remove deprecation warnings
3. **Phase 7**: Cannot rollback (files deleted) - restore from git

---

## Success Criteria

| Criterion | Metric |
|-----------|--------|
| All imports updated | 0 references to `app.services` |
| BLCA clean | 0 violations |
| Tests pass | 100% pass rate |
| No deprecation warnings | 0 warnings in logs |
| Documentation complete | All docs updated |

---

## Next Action

**Start Phase 4.1**: Identify duplicate files between `app/services/` and `app/houseofcards/`.

```bash
# Quick check for duplicates
cd /root/agenticverz2.0/backend
comm -12 \
  <(find app/services -type f -name "*.py" | grep -v __pycache__ | grep -v __init__ | sed 's|.*/||' | sort -u) \
  <(find app/houseofcards -type f -name "*.py" | grep -v __pycache__ | grep -v __init__ | sed 's|.*/||' | sort -u) | wc -l
```
