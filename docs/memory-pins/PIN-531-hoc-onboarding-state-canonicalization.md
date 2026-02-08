# PIN-531 — HOC Onboarding State Canonicalization (No Legacy Duplicates)

**Date:** 2026-02-08  
**Status:** COMPLETE ✅  
**Scope:** Onboarding enum SSOT under HOC + L2 purity (no `app.models.*` imports in HOC L2)

---

## What Was Completed

1. **Onboarding state machine is now canonical in HOC**
   - Canonical enum + transition metadata:
     - `backend/app/hoc/cus/account/L5_schemas/onboarding_state.py`
   - All call sites rewired to import `OnboardingState` / `OnboardingStatus` from the HOC canonical path.

2. **Legacy duplicates removed (no tombstones)**
   - Deleted:
     - `backend/app/auth/onboarding_state.py`
     - `backend/app/hoc/cus/account/L5_schemas/onboarding_enums.py`

3. **HOC L2 routers no longer import L7 ORM models**
   - `backend/app/hoc/api/cus/policies/aos_accounts.py` no longer imports `app.models.tenant.*`
   - `backend/app/hoc/api/cus/policies/guard.py` now uses `IncidentSeverity` from:
     - `backend/app/hoc/cus/hoc_spine/schemas/domain_enums.py`

4. **Freeze enforcement updated to match new canon**
   - Updated frozen onboarding file list:
     - `docs/governance/FREEZE.md`
   - Updated CI frozen-file enforcement list:
     - `backend/scripts/ci/check_frozen_files.py`

---

## Canonical Import Rules (Post-Change)

- Onboarding enum import (canonical):
  - `from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState`
- L2 routers must not import ORM (`app.models.*`); use:
  - L4-safe schema mirrors under `app.hoc.cus.hoc_spine.schemas.*`
  - L4 operations via `OperationRegistry`

---

## Evidence (Mechanical Gates)

Post-change verification (local):
- `pytest -q tests/governance/t0` → `601 passed, 18 xfailed, 1 xpassed`
- `python3 scripts/ci/check_init_hygiene.py --ci` → `0 blocking violations`
- `python3 scripts/ci/check_layer_boundaries.py --ci` → `CLEAN`
- `python3 scripts/ops/hoc_cross_domain_validator.py` → `CLEAN`
- `python3 scripts/ops/hoc_l5_l6_purity_audit.py --all-domains --advisory` → `0 blocking, 0 advisory`
- `python3 scripts/ops/l5_spine_pairing_gap_detector.py` → `69 wired, 0 orphaned, 0 direct`

---

## Commit

- `9ac85f8e` — `refactor(hoc): canonicalize onboarding state + clear L2 model imports (PIN-399)`

