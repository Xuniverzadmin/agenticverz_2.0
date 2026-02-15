> **DEPRECATED (2026-02-11):** This file is NON-CANONICAL. The canonical usecase docs are at:
> `backend/app/hoc/docs/architecture/usecases/`
> Do not update this file. All changes must go to the canonical root.

# Execution Plan: DOMAIN_REPAIR_PLAN_UC001_UC002 (v2 — corrected)

**Created:** 2026-02-11
**Status:** EXECUTED
**Evidence:** `DOMAIN_REPAIR_PLAN_UC001_UC002_v2_plan_implmented.md`

---

## Context

The repair plan addresses domain authority drift and functional gaps across UC-001 (LLM Run Monitoring) and UC-002 (Customer Onboarding).

**This is NOT structural-only.** Exploration revealed functional bugs and missing capabilities alongside the ownership drift:
- Onboarding gate does not map `/tenant/api-keys` (defaults to COMPLETE — too restrictive)
- Integration session wiring is broken (`get_integrations_facade()` ignores session param)
- Connector persistence is in-memory only (driver exists but facade doesn't use it)
- SDK attestation has no persistence or verification
- No project-create endpoint in account domain
- `fdr/logs/founder_review.py` has `text()` + `session.commit()` purity violations

**Canonical namespace decision:** `account` (singular) is the directory name at all layers. HTTP prefix `/accounts` (plural) is the URL convention. This plan uses `account` for all path references.

---

## Phase 1: UC-002 — Route Ownership Migration (structural moves)

All moves target `backend/app/hoc/api/cus/`.

### Step 1.1: Move `aos_accounts.py` -> `account/aos_accounts.py`

- Copy `policies/aos_accounts.py` (1,476 lines) to `account/aos_accounts.py`
- Replace old file with tombstone wrapper (TOMBSTONE_EXPIRY: 2026-04-15)
- Update `facades/cus/account.py` import to `app.hoc.api.cus.account.aos_accounts`

### Step 1.2: Move `aos_cus_integrations.py` -> `integrations/aos_cus_integrations.py`

- Copy `policies/aos_cus_integrations.py` (674 lines) to `integrations/aos_cus_integrations.py`
- Replace old file with tombstone wrapper (TOMBSTONE_EXPIRY: 2026-04-15)
- Update `facades/cus/integrations.py` import to `app.hoc.api.cus.integrations.aos_cus_integrations`

### Step 1.3: Move `aos_api_key.py` -> `api_keys/aos_api_key.py`

- Copy `policies/aos_api_key.py` (298 lines, read-only) to `api_keys/aos_api_key.py`
- Replace old file with tombstone wrapper (TOMBSTONE_EXPIRY: 2026-04-15)
- Update `facades/cus/api_keys.py` import to `app.hoc.api.cus.api_keys.aos_api_key`

### Step 1.4: Extract API key writes from `logs/tenants.py` -> `api_keys/api_key_writes.py`

Extract from `logs/tenants.py`:
- `_api_keys_op()` helper
- `_maybe_advance_to_api_key_created()`
- API key request/response models
- `GET /tenant/api-keys`
- `POST /tenant/api-keys`
- `DELETE /tenant/api-keys/{key_id}`

Create `api_keys/api_key_writes.py` — router prefix stays `/tenant/api-keys` for URL compatibility.
Remove extracted code from `logs/tenants.py`.
Update `facades/cus/api_keys.py` to include `api_key_writes_router`.

**URL consolidation note:** Read ops live at `/api-keys` (from `aos_api_key.py`), write ops at `/tenant/api-keys` (from `api_key_writes.py`). Both now under `api_keys/` domain directory. URL unification deferred — canonical authority is established by directory ownership, not URL prefix.

---

## Phase 2: UC-002 — Onboarding Gate Fix (functional)

### Step 2.1: Add `/tenant/api-keys` to `onboarding_policy.py`

**File:** `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`

**Bug:** `/tenant/api-keys` is NOT in `ENDPOINT_STATE_REQUIREMENTS` or `ENDPOINT_PATTERN_REQUIREMENTS`. It falls through to the default `COMPLETE` state, blocking onboarding users who are only at `IDENTITY_VERIFIED`.

Add to `ENDPOINT_STATE_REQUIREMENTS`:
```python
"/tenant/api-keys": OnboardingState.IDENTITY_VERIFIED,
```

Add to `ENDPOINT_PATTERN_REQUIREMENTS`:
```python
(re.compile(r"^/tenant/api-keys(/.*)?$"), OnboardingState.IDENTITY_VERIFIED),
```

### Step 2.2: Add activation predicate checks

The repair spec requires the activation predicate to require: project ready, key/integration ready, connector validated, SDK attested.

**File:** `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`

Add:

```python
ACTIVATION_REQUIREMENTS = {
    "project_ready": "Tenant has at least one active project",
    "key_ready": "At least one active API key exists",
    "connector_validated": "At least one connector passed validation",
    "sdk_attested": "SDK handshake completed and persisted",
}

def check_activation_predicate(
    has_project: bool,
    has_api_key: bool,
    has_validated_connector: bool,
    has_sdk_attestation: bool,
) -> tuple[bool, list[str]]:
    """Check whether all activation conditions are met. Returns (pass, missing)."""
    missing = []
    if not has_project:
        missing.append("project_ready")
    if not has_api_key:
        missing.append("key_ready")
    if not has_validated_connector:
        missing.append("connector_validated")
    if not has_sdk_attestation:
        missing.append("sdk_attested")
    return (len(missing) == 0, missing)
```

Pure policy data (no DB, no framework imports). The L4 handler that advances onboarding to COMPLETE will call this predicate.

---

## Phase 3: UC-002 — Functional Fixes

### Step 3.1: Fix integration session wiring

**Bug:** `integrations_handler.py` passes `session=` to `get_integrations_facade()`, but the facade factory ignores it — singleton with no session.

**Files:** `integrations_handler.py`, `connectors_facade.py`, `datasources_facade.py`

Fix: Update facade factories to accept optional session parameter and pass through.

### Step 3.2: Wire connector persistence to existing driver

**Bug:** `connectors_facade.py` uses in-memory `self._connectors: Dict = {}` instead of the existing `connector_registry_driver.py` which has full DB persistence.

**File:** `backend/app/hoc/cus/integrations/L5_engines/connectors_facade.py`

Fix: Replace in-memory store methods with delegation to L6 driver:
- `register_connector()` -> `connector_registry_driver.create()`
- `list_connectors()` -> `connector_registry_driver.list_all()`
- `get_connector()` -> `connector_registry_driver.get_by_id()`
- `update_connector()` -> `connector_registry_driver.update()`
- `delete_connector()` -> `connector_registry_driver.delete()`
- Remove `self._connectors` dict

**Existing driver:** `backend/app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py` (840 lines, full implementation)

### Step 3.3: Add SDK attestation persistence

**Current state:** `sdk.py` `/sdk/handshake` endpoint logs SDK info but persists nothing.

Create:
1. **L5 schema:** `backend/app/hoc/cus/account/L5_schemas/sdk_attestation.py`
   - `SDKAttestationRecord` dataclass: `tenant_id`, `sdk_version`, `sdk_language`, `client_id`, `attested_at`, `attestation_hash`

2. **L6 driver:** `backend/app/hoc/cus/account/L6_drivers/sdk_attestation_driver.py`
   - `write_attestation(session, record)` — raw SQL INSERT/UPSERT
   - `fetch_attestation(session, tenant_id)` — raw SQL SELECT
   - `has_attestation(session, tenant_id)` — existence check

3. **L4 handler update:** Add `account.sdk_attestation` operation to `account_handler.py`
   - `AccountSdkAttestationHandler` with write/query/has_attestation methods

4. **L2 fix:** Update `sdk.py` handshake endpoint to persist attestation via L4 dispatch after state transition

### Step 3.4: Add project-create capability in account domain

**Current state:** `aos_accounts.py` has `GET /accounts/projects` (list) and `GET /accounts/projects/{id}` (detail) but no POST.

Add:
- `POST /accounts/projects` endpoint in `account/aos_accounts.py`
- Request model: `ProjectCreateRequest(name, description)`
- Dispatch via L4: `registry.execute("account.tenant", ctx)` with `method="create_project"`
- L5 `accounts_facade.py`: `create_project()` method
- L6 `accounts_facade_driver.py`: `insert_project()` method

---

## Phase 4: UC-001 — INT/FDR Audit + Violation Fix

### Step 4.1: Fix `founder_review.py` purity violations

**File:** `backend/app/hoc/api/fdr/logs/founder_review.py`

Two violations found:
1. Uses `text()` instead of `sql_text()` — replace with `sql_text()`
2. Direct `session.commit()` in L2 — remove it (L4 owns transaction)

### Step 4.2: Document UC-001 audit results in linkage doc

**File:** `docs/doc/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`

Update UC-001 audit result:
- **CUS routes** (activity, incidents, logs): 0 bypasses verified
- **INT routes** (recovery, lifecycle_gate, sdk, billing_gate, onboarding): 0 L5/L6 bypasses; 1 advisory (billing_gate L5_schemas enum import — allowed per Phase 4 pattern)
- **FDR routes** (ops, founder_onboarding, founder_timeline, founder_review): 0 L5/L6 bypasses; 1 CRITICAL purity violation in `founder_review.py` (fixed in Step 4.1)
- Status: stays `YELLOW` — all three audiences now audited; endpoint-to-handler mapping not yet enumerated

---

## Phase 5: CI Ownership Check (BLOCKING)

### Step 5.1: Add blocking CI check for domain ownership violations

**File:** `scripts/ci/check_init_hygiene.py`

Add check 34: `check_l2_domain_ownership` — **BLOCKING** (not advisory).

Detection logic:
- Scan each L2 file in `backend/app/hoc/api/cus/{domain}/`
- Extract L4 operation names from `registry.execute("X.Y", ...)` calls
- If operation prefix `X` does not match the directory `{domain}`, flag as violation
- Example: file in `policies/` calling `api_keys.write` -> FAIL

Frozen allowlist for pre-existing cross-domain files:
- `costsim.py` — dispatches to `controls.circuit_breaker`
- `v1_proxy.py` — dispatches to `proxy.ops`
- `v1_killswitch.py` — dispatches to `killswitch.read/write`
- `workers.py` — dispatches to `logs.capture`

### Step 5.2: Document minimum event schema

Add shared section to `HOC_USECASE_CODE_LINKAGE.md`:
- Required fields: `event_id`, `event_type`, `tenant_id`, `project_id`, `actor_type`, `actor_id`, `decision_owner`, `sequence_no`, `schema_version`
- Runtime enforcement deferred; documented as contract for UC-001 and UC-002

---

## Phase 6: Index, Status & Implemented Doc

### Step 6.1: Update `usecases/INDEX.md`

- UC-002: `RED` -> `YELLOW` (ownership migrated, functional fixes applied, activation predicate defined)
- UC-001: stays `YELLOW` (all three audiences audited, purity fix applied, endpoint mapping pending)

### Step 6.2: Update `HOC_USECASE_CODE_LINKAGE.md`

- Add UC-002 full section using audit template
- Update UC-001 with INT/FDR audit evidence

### Step 6.3: Create implementation evidence doc

Post-execution evidence doc with:
- Per-phase execution log
- Files moved/created/modified with line counts
- CI verification results (34 checks)
- Before/after status table
- Remaining gaps for GREEN gate

---

## Phase 7: Verification

1. **CI checks:** `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci` — all 34 checks pass
2. **Purity audit:** 0 blocking, 0 advisory
3. **Import test:** Python import of all moved/created modules — no errors
4. **Facade resolution:** All 5 cus facades resolve correctly
5. **Onboarding gate test:** `/tenant/api-keys` resolves to `IDENTITY_VERIFIED` (not `COMPLETE`)
6. **Activation predicate test:** `check_activation_predicate(False, True, True, True)` returns `(False, ["project_ready"])`
7. **Grep verification:** No remaining cross-domain facade imports (only tombstone wrappers)
8. **founder_review.py:** Verify `sql_text()` used, no `session.commit()`
9. **Connector persistence:** Verify `connectors_facade` delegates to `connector_registry_driver`

---

## Files Modified (Summary)

| Action | File | Phase |
|--------|------|-------|
| MOVE | `policies/aos_accounts.py` -> `account/aos_accounts.py` | 1.1 |
| MOVE | `policies/aos_cus_integrations.py` -> `integrations/aos_cus_integrations.py` | 1.2 |
| MOVE | `policies/aos_api_key.py` -> `api_keys/aos_api_key.py` | 1.3 |
| CREATE | `api_keys/api_key_writes.py` | 1.4 |
| EDIT | `logs/tenants.py` — remove API key endpoints | 1.4 |
| TOMBSTONE | 3 old files in `policies/` (2026-04-15) | 1.1-1.3 |
| EDIT | `facades/cus/account.py` — fix import | 1.1 |
| EDIT | `facades/cus/integrations.py` — fix import | 1.2 |
| EDIT | `facades/cus/api_keys.py` — fix import + add write router | 1.3-1.4 |
| EDIT | `hoc_spine/authority/onboarding_policy.py` — gate fix + activation predicate | 2.1-2.2 |
| EDIT | `integrations_handler.py` — session wiring fix | 3.1 |
| EDIT | `connectors_facade.py` — wire to L6 driver | 3.2 |
| EDIT | `datasources_facade.py` — session param | 3.1 |
| CREATE | `account/L5_schemas/sdk_attestation.py` | 3.3 |
| CREATE | `account/L6_drivers/sdk_attestation_driver.py` | 3.3 |
| EDIT | `account_handler.py` — SDK attestation op + create_project dispatch | 3.3-3.4 |
| EDIT | `int/general/sdk.py` — persist attestation via L4 | 3.3 |
| EDIT | `account/aos_accounts.py` — POST /accounts/projects | 3.4 |
| EDIT | `accounts_facade.py` — create_project method | 3.4 |
| EDIT | `accounts_facade_driver.py` — insert_project method | 3.4 |
| EDIT | `fdr/logs/founder_review.py` — fix text() + commit() | 4.1 |
| EDIT | `scripts/ci/check_init_hygiene.py` — add check 34 | 5.1 |
| EDIT | `usecases/INDEX.md` — status updates | 6.1 |
| EDIT | `usecases/HOC_USECASE_CODE_LINKAGE.md` — UC-002 section + UC-001 audit | 6.2 |
| CREATE | `usecases/DOMAIN_REPAIR_PLAN_UC001_UC002_implemented.md` | 6.3 |

---

## Remaining Gaps for GREEN

| Gap | Usecase | Description |
|-----|---------|-------------|
| Endpoint-to-handler mapping | UC-001 | Complete enumeration of all routes to L4 ops |
| Event schema enforcement | UC-001, UC-002 | Runtime validation of minimum event fields |
| Activation predicate wiring | UC-002 | Wire predicate to onboarding completion gate in L4 |
| SDK attestation migration | UC-002 | Create `sdk_attestations` table via Alembic |
| URL unification | UC-002 | Unify read `/api-keys` and write `/tenant/api-keys` prefixes |
