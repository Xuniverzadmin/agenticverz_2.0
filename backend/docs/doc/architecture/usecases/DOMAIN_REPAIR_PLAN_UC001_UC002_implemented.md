> **DEPRECATED (2026-02-11):** This file is NON-CANONICAL. The canonical usecase docs are at:
> `backend/app/hoc/docs/architecture/usecases/`
> Do not update this file. All changes must go to the canonical root.

# DOMAIN_REPAIR_PLAN_UC001_UC002 — Implementation Evidence

**Executed:** 2026-02-11
**Plan:** `docs/doc/architecture/usecases/DOMAIN_REPAIR_PLAN_UC001_UC002.md`

---

## Phase 1: Route Ownership Migration

| Step | Action | Files | Status |
|------|--------|-------|--------|
| 1.1 | Move `aos_accounts.py` | `policies/` -> `account/` (tombstone at source) | DONE |
| 1.2 | Move `aos_cus_integrations.py` | `policies/` -> `integrations/` (tombstone at source) | DONE |
| 1.3 | Move `aos_api_key.py` | `policies/` -> `api_keys/` (tombstone at source) | DONE |
| 1.4 | Extract API key writes | `logs/tenants.py` -> `api_keys/api_key_writes.py` | DONE |

**Facade updates:**
- `facades/cus/account.py` — import from `account/aos_accounts.py`
- `facades/cus/integrations.py` — import from `integrations/aos_cus_integrations.py`
- `facades/cus/api_keys.py` — import from `api_keys/aos_api_key.py` + `api_key_writes.py`

**Tombstones:** 3 files in `policies/` with `TOMBSTONE_EXPIRY: 2026-04-15`

---

## Phase 2: Onboarding Gate Fix

| Step | Action | File | Status |
|------|--------|------|--------|
| 2.1 | Add `/tenant/api-keys` mapping | `onboarding_policy.py` | DONE |
| 2.2 | Add activation predicate | `onboarding_policy.py` | DONE |

**Verification:** `/tenant/api-keys` resolves to `IDENTITY_VERIFIED` (not `COMPLETE`).

---

## Phase 3: Functional Fixes

| Step | Action | File(s) | Status |
|------|--------|---------|--------|
| 3.1 | Fix integration session wiring | `integrations_handler.py`, `connectors_facade.py`, `datasources_facade.py` | DONE |
| 3.2 | Wire connector persistence to L6 | `connectors_facade.py` | DONE |
| 3.3 | Add SDK attestation persistence | `sdk_attestation.py` (L5), `sdk_attestation_driver.py` (L6), `account_handler.py` (L4), `sdk.py` (L2) | DONE |
| 3.4 | Add project-create capability | `aos_accounts.py` (L2), `accounts_facade.py` (L5), `accounts_facade_driver.py` (L6), `account_handler.py` (L4) | DONE |

---

## Phase 4: INT/FDR Audit + Violation Fix

| Step | Action | File | Status |
|------|--------|------|--------|
| 4.1 | Fix `text()` -> `sql_text()` | `founder_review.py:75` | DONE |
| 4.1 | Remove `session.commit()` | `founder_review.py:95` | DONE |
| 4.2 | Document UC-001 audit results | `HOC_USECASE_CODE_LINKAGE.md` | DONE |

---

## Phase 5: CI Ownership Check

| Step | Action | File | Status |
|------|--------|------|--------|
| 5.1 | Add check 34 (`check_l2_domain_ownership`) | `check_init_hygiene.py` | DONE |
| 5.2 | Document minimum event schema | `HOC_USECASE_CODE_LINKAGE.md` | DONE |

---

## Phase 6: Index & Status Updates

| Step | Action | File | Status |
|------|--------|------|--------|
| 6.1 | Update usecase INDEX | `usecases/INDEX.md` | DONE |
| 6.2 | Update linkage doc | `usecases/HOC_USECASE_CODE_LINKAGE.md` | DONE |
| 6.3 | Create implemented doc | This file | DONE |

---

## Before/After Status Table

| Usecase | Before | After | Reason |
|---------|--------|-------|--------|
| UC-001 | YELLOW | YELLOW | All 3 audiences audited, purity fix applied, endpoint mapping pending |
| UC-002 | RED (unregistered) | YELLOW | Ownership migrated, functional fixes applied, activation predicate defined |

---

## Files Modified Summary

| Action | Count |
|--------|-------|
| MOVED (copy + tombstone) | 3 |
| CREATED | 5 |
| EDITED | 14 |
| **Total files touched** | **22** |

### Complete File List

**MOVED:**
1. `policies/aos_accounts.py` -> `account/aos_accounts.py`
2. `policies/aos_cus_integrations.py` -> `integrations/aos_cus_integrations.py`
3. `policies/aos_api_key.py` -> `api_keys/aos_api_key.py`

**CREATED:**
1. `api_keys/api_key_writes.py` (API key write endpoints)
2. `account/L5_schemas/sdk_attestation.py` (attestation schema)
3. `account/L6_drivers/sdk_attestation_driver.py` (attestation driver)
4. `docs/doc/architecture/usecases/INDEX.md`
5. `docs/doc/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`

**EDITED:**
1. `policies/aos_accounts.py` (tombstone)
2. `policies/aos_cus_integrations.py` (tombstone)
3. `policies/aos_api_key.py` (tombstone)
4. `facades/cus/account.py` (import fix)
5. `facades/cus/integrations.py` (import fix)
6. `facades/cus/api_keys.py` (import fix + add write router)
7. `logs/tenants.py` (remove API key endpoints)
8. `hoc_spine/authority/onboarding_policy.py` (gate fix + activation predicate)
9. `integrations_handler.py` (session wiring fix)
10. `connectors_facade.py` (L6 driver delegation)
11. `datasources_facade.py` (session param)
12. `account_handler.py` (SDK attestation op + create_project dispatch)
13. `int/general/sdk.py` (persist attestation)
14. `account/aos_accounts.py` (POST /projects endpoint)
15. `accounts_facade.py` (create_project method)
16. `accounts_facade_driver.py` (insert_project method)
17. `fdr/logs/founder_review.py` (purity fix)
18. `scripts/ci/check_init_hygiene.py` (check 34)

---

## Phase 7: Verification

**Executed:** 2026-02-11

### CI Checks

| Check | Result |
|-------|--------|
| All 34 CI checks (`check_init_hygiene.py --ci`) | **PASS** — 0 blocking violations, 0 known exceptions |
| Check 34 (`check_l2_domain_ownership`) | **PASS** — frozen allowlist for 4 pre-existing cross-domain files |

**Frozen allowlist (pre-existing, not part of migration):**
- `costsim.py` — dispatches to `controls.circuit_breaker`
- `v1_proxy.py` — dispatches to `proxy.ops`
- `v1_killswitch.py` — dispatches to `killswitch.read/write`
- `workers.py` — dispatches to `logs.capture`

### Python Import Tests

| Module | Result |
|--------|--------|
| `account.aos_accounts` (moved) | **PASS** |
| `integrations.aos_cus_integrations` (moved) | **PASS** |
| `api_keys.aos_api_key` (moved) | **PASS** |
| `api_keys.api_key_writes` (created) | **PASS** |
| `account.L5_schemas.sdk_attestation` (created) | **PASS** |
| `account.L6_drivers.sdk_attestation_driver` (created) | **PASS** |
| `policies.aos_accounts` (tombstone) | **PASS** |
| `policies.aos_cus_integrations` (tombstone) | **PASS** |
| `policies.aos_api_key` (tombstone) | **PASS** |

### Facade Resolution

| Facade | Routers | Result |
|--------|---------|--------|
| `facades/cus/account.py` | 2 | **PASS** |
| `facades/cus/integrations.py` | 5 | **PASS** |
| `facades/cus/api_keys.py` | 3 | **PASS** |
| `facades/cus/logs.py` | 4 | **PASS** |
| `facades/cus/activity.py` | 1 | **PASS** |

### Onboarding Gate Tests

| Test | Expected | Actual | Result |
|------|----------|--------|--------|
| `/tenant/api-keys` direct match | `IDENTITY_VERIFIED` | `IDENTITY_VERIFIED` | **PASS** |
| `/tenant/api-keys/abc123` pattern match | `IDENTITY_VERIFIED` | `IDENTITY_VERIFIED` | **PASS** |
| `check_activation_predicate(F,T,T,T)` | `(False, ["project_ready"])` | `(False, ["project_ready"])` | **PASS** |
| `check_activation_predicate(T,T,T,T)` | `(True, [])` | `(True, [])` | **PASS** |

### Purity Checks

| Check | Result |
|-------|--------|
| `founder_review.py` uses `sql_text()` | **PASS** |
| `founder_review.py` has no `session.commit()` | **PASS** |
| `connectors_facade.py` delegates to L6 driver | **PASS** |
| `connectors_facade.py` has no in-memory `_connectors` dict | **PASS** |

### Cross-Domain Import Grep

| Pattern | Matches Outside Tombstones | Result |
|---------|---------------------------|--------|
| `from app.hoc.api.cus.policies.(aos_accounts\|aos_cus_integrations\|aos_api_key)` | 0 | **PASS** |

---

## Remaining Gaps for GREEN

| Gap | Usecase | Description |
|-----|---------|-------------|
| Endpoint-to-handler mapping | UC-001 | Complete enumeration of all routes to L4 ops |
| Event schema enforcement | UC-001, UC-002 | Runtime validation of minimum event fields |
| Activation predicate wiring | UC-002 | Wire predicate to onboarding completion gate in L4 |
| SDK attestation migration | UC-002 | Create `sdk_attestations` table via Alembic |
| URL unification | UC-002 | Unify read `/api-keys` and write `/tenant/api-keys` prefixes |
