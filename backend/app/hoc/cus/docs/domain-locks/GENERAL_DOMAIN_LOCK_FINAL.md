# GENERAL DOMAIN LOCK — FINAL

**Status:** LOCKED
**Date:** 2026-01-24
**Reference:** Phase-2.5A Layer Reclassification

---

## 1. Structural Guarantee

| Component | State | Invariant |
|-----------|-------|-----------|
| All engines/ files | L5 | Pure business logic, zero DB Session imports |
| All facades/ files | L3 | Thin translation layer, < 200 LOC |
| All schemas/ files | L5 | Pure dataclass/Pydantic definitions |
| All drivers/ files with DB | L6 | Has sqlmodel Session imports |
| utils/time.py | L5 | Pure datetime utility |

---

## 2. Layer Classification Summary

### Engines → L5 (13 files)

All engine files reclassified from L4 → L5 per HOC Topology V1:

| File | Previous | Current | Reason |
|------|----------|---------|--------|
| `engines/alert_log_linker.py` | L4 | L5 | Pure business logic |
| `engines/control_registry.py` | L4 | L5 | Pure registry logic |
| `engines/knowledge_lifecycle_manager.py` | L4 | L5 | Pure lifecycle logic |
| `engines/lifecycle_stages_base.py` | L4 | L5 | Pure base class definitions |
| `controls/engines/guard_write_service.py` | L4 | L5 | Pure guard logic |
| `lifecycle/engines/base.py` | L4 | L5 | Pure base definitions |
| `lifecycle/engines/offboarding.py` | L4 | L5 | Pure offboarding logic |
| `lifecycle/engines/onboarding.py` | L4 | L5 | Pure onboarding logic |
| `lifecycle/engines/pool_manager.py` | L4 | L5 | Pure pool management logic |
| `runtime/engines/constraint_checker.py` | L4 | L5 | Pure constraint checking |
| `runtime/engines/phase_status_invariants.py` | L4 | L5 | Pure invariant definitions |
| `ui/engines/rollout_projection.py` | L4 | L5 | Pure projection logic |
| `workflow/contracts/engines/contract_service.py` | L4 | L5 | Pure state machine logic |

### Facades → L3 (5 files)

All facade files reclassified to L3 per HOC Topology V1:

| File | Previous | Current | Reason |
|------|----------|---------|--------|
| `facades/monitors_facade.py` | L4 | L3 | Thin translation layer |
| `facades/scheduler_facade.py` | L4 | L3 | Thin translation layer |
| `facades/alerts_facade.py` | L6 | L3 | Thin translation layer |
| `facades/compliance_facade.py` | L6 | L3 | Thin translation layer |
| `facades/lifecycle_facade.py` | L6 | L3 | Thin translation layer |

### Schemas → L5 (6 files)

All schema files reclassified to L5 (pure dataclass definitions):

| File | Previous | Current | Reason |
|------|----------|---------|--------|
| `schemas/agent.py` | L6 | L5 | Pure Pydantic schemas |
| `schemas/artifact.py` | L6 | L5 | Pure Pydantic schemas |
| `schemas/plan.py` | L6 | L5 | Pure Pydantic schemas |
| `schemas/response.py` | L2 | L5 | Pure Pydantic schemas |
| `schemas/skill.py` | L6 | L5 | Pure Pydantic schemas |
| `schemas/common.py` | L6 | L5 | Pure Pydantic schemas |

### Drivers/Utils → L5 (4 files)

Files in drivers/ that are actually L5 (no direct DB session):

| File | Previous | Current | Reason |
|------|----------|---------|--------|
| `drivers/db_helpers.py` | L6 | L5 | Operates on Row objects, no Session |
| `lifecycle/drivers/execution.py` | L6 | L5 | Business logic, no direct DB |
| `lifecycle/drivers/knowledge_plane.py` | L6 | L5 | Pure dataclass definitions |
| `utils/time.py` | L6 | L5 | Pure datetime utility |

### File Moved (1 file)

| Old Location | New Location | Reason |
|--------------|--------------|--------|
| `engines/cus_health_service.py` | `drivers/cus_health_driver.py` | Has `from sqlmodel import Session, select` — belongs in L6 |

**Backward Compatibility:** `engines/cus_health_service.py` now re-exports from new location with deprecation warning.

---

## 3. BLCA Verification

```bash
python3 scripts/ops/layer_validator.py --backend --ci 2>&1 | grep -E "customer/general"
```

**Results:**
- **Errors:** 0
- **Warnings:** 9 (all HEADER_LOCATION_MISMATCH — expected since Layer ≠ Directory)

The 9 warnings are expected because files like `lifecycle/drivers/knowledge_plane.py` claim L5 but are in a `drivers/` directory. Per HOC Topology V1, Layer is determined by code behavior (imports), not directory location.

---

## 4. Key Principle Applied

**Layer ≠ Directory**

Per HOC Topology V1.2.0:
- **L5 (Engine):** Pure business logic, NO `Session`, `AsyncSession`, `sqlmodel.select` imports
- **L6 (Driver):** Has DB boundary crossing imports (`Session`, `AsyncSession`, `select`)
- **L3 (Facade):** Thin translation layer, < 200 LOC

Files are classified by their CODE BEHAVIOR, not their directory name. A file in `drivers/` that has no DB Session imports is correctly L5, not L6.

---

## 5. Forbidden Actions

| Action | Enforcement |
|--------|-------------|
| Add Session/AsyncSession imports to L5 files | BLCA BLOCK |
| Add business logic to L6 driver files | GOVERNANCE BLOCK |
| Create `*_service.py` files | CI BLOCK |
| Reclassify without code behavior analysis | GOVERNANCE BLOCK |
| Move files without backward-compat redirect | GOVERNANCE BLOCK |

---

## 6. Ownership

| Role | Owner |
|------|-------|
| Engine logic (L5) | Individual engine classes |
| Driver persistence (L6) | Individual driver classes |
| Facade translation (L3) | Individual facade files |
| Schema definitions (L5) | Individual schema files |
| Governance | This document |

---

## 7. Expected Warnings (Tolerated)

The following HEADER_LOCATION_MISMATCH warnings are expected and tolerated:

1. `lifecycle/drivers/execution.py` — L5 in drivers/ (no Session imports)
2. `lifecycle/drivers/knowledge_plane.py` — L5 in drivers/ (pure dataclass)
3. `drivers/db_helpers.py` — L5 in drivers/ (Row operations only)
4. Other files where Layer ≠ Directory

These are NOT violations. They demonstrate correct application of the principle that Layer is determined by code behavior, not directory name.

---

## 8. Verification Command

```bash
# Full BLCA check
python3 scripts/ops/layer_validator.py --backend --ci

# Filter to customer/general only
python3 scripts/ops/layer_validator.py --backend --ci 2>&1 | grep -E "customer/general"

# Count warnings (expect 9)
python3 scripts/ops/layer_validator.py --backend --ci 2>&1 | grep -E "customer/general" | wc -l
```

---

## 9. Deprecation Notices

### cus_health_service.py → cus_health_driver.py

**Old import (deprecated):**
```python
from app.houseofcards.customer.general.engines.cus_health_service import CusHealthService
```

**New import (recommended):**
```python
from app.houseofcards.customer.general.drivers.cus_health_driver import CusHealthDriver
```

The old import path continues to work but emits a `DeprecationWarning`.

---

## 10. Cross-Domain Authority

The general domain provides cross-domain services for all customer domains. Per HOC Topology V1:

> Respective cross-domain items shall be in `{audience}/general/` and not outside `{audience}/` folder.

All cross-domain utilities remain in `customer/general/` and are correctly layered.

---

**This document is the line in the sand.**

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock | Claude |
| 2026-01-24 | 1.1.0 | Phase 2.5E BLCA verification: 0 errors, 0 warnings across all 6 check types | Claude |
| 2026-01-24 | 1.2.0 | **Phase 3 Directory Restructure** — 13 L5 engine files relocated from L6_drivers/ to L5_engines/ based on content analysis (no DB ops). PIN-470. | Claude |
