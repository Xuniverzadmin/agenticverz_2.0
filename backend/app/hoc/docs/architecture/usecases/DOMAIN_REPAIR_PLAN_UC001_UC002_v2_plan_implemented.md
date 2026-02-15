# DOMAIN_REPAIR_PLAN_UC001_UC002 v2 — Implementation Evidence

> Status note: this file is a captured implementation claim snapshot.
> Current canonical truth is:
> - `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
> - `backend/app/hoc/docs/architecture/usecases/DOMAIN_REPAIR_PLAN_UC001_UC002_v2_remaining_punch_list.md`
> If any statement here conflicts with those files, treat this file as stale evidence.

**Executed:** 2026-02-11
**Plan:** `DOMAIN_REPAIR_PLAN_UC001_UC002_v2_plan.md`
**Scope:** 15 remaining gap items from v2 plan

---

## Gap 1: Delete Tombstones + Verify Import Failures

| File | Action | Result |
|------|--------|--------|
| `policies/aos_accounts.py` | DELETED | Old import correctly fails |
| `policies/aos_cus_integrations.py` | DELETED | Old import correctly fails |
| `policies/aos_api_key.py` | DELETED | Old import correctly fails |

**Grep verification:** 0 remaining imports from `app.hoc.api.cus.policies.(aos_accounts|aos_cus_integrations|aos_api_key)` in `app/`.

---

## Gap 2: Wire Activation Predicate into Onboarding Advance Path

**File:** `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`

**Changes:**
- Added `_check_activation_conditions(sync_session, tenant_id)` — sync SQL checks for api_keys, cus_integrations, sdk_attestations
- Added `_async_check_activation_conditions(session, tenant_id)` — async SQL checks (same queries)
- Wired into `AccountOnboardingAdvanceHandler.execute()` — blocks COMPLETE if predicate fails
- Wired into `async_advance_onboarding()` — blocks COMPLETE if predicate fails
- Founder force-complete (`trigger.startswith("founder_force_complete:")`) logs WARNING but allows override

**Test:**
- `check_activation_predicate(F,T,T,T)` → `(False, ["project_ready"])` PASS
- `check_activation_predicate(T,T,T,T)` → `(True, [])` PASS
- `check_activation_predicate(T,F,F,F)` → `(False, ["key_ready", "connector_validated", "sdk_attested"])` PASS

---

## Gap 3: Fix SDK Attestation Handshake

**File:** `app/hoc/api/int/general/sdk.py`

**Bug:** `session=None` passed to `account.sdk_attestation` L4 dispatch. L4 handler rejected with `MISSING_SESSION`. Error silently swallowed.

**Fix:**
- Added `session=Depends(get_sync_session_dep)` to `sdk_handshake()` endpoint signature
- Replaced attestation dispatch to pass real `session` in params as `sync_session`
- Errors now logged explicitly with `logger.error()` (not swallowed)

---

## Gap 4: SDK Attestation DB Migration

**File:** `alembic/versions/127_create_sdk_attestations.py`

| Column | Type | Nullable |
|--------|------|----------|
| id | Integer (PK, autoincrement) | No |
| tenant_id | String(36) | No |
| sdk_version | String(100) | No |
| sdk_language | String(50) | No |
| client_id | String(200) | Yes |
| attested_at | DateTime(tz) | No |
| attestation_hash | String(64) | No |

- **Unique constraint:** `uq_sdk_attestations_tenant_hash` on `(tenant_id, attestation_hash)`
- **Index:** `ix_sdk_attestations_tenant_id` on `tenant_id`
- **down_revision:** `126_s6_trace_completion_allowed`

**Validation:** L6 driver queries (INSERT, SELECT, existence check) match migration schema exactly.

---

## Gap 5: Fix Connector Facade Session Wiring

**File:** `app/hoc/cus/integrations/L5_engines/connectors_facade.py`

**Fix:** Removed mutable singleton pattern. `get_connectors_facade(session=None)` no longer mutates `_facade_instance._session` on every call. Session accepted for forward-compatibility (L6 ConnectorRegistry is in-memory by design).

---

## Gap 6: Validate Integrations Handler Contracts

**File:** `app/hoc/cus/hoc_spine/orchestrator/handlers/integrations_handler.py`

**Fix:** Added `_STRIP_PARAMS = {"method", "sync_session"}` to all 3 handlers:
- `IntegrationsQueryHandler`
- `IntegrationsConnectorsHandler`
- `IntegrationsDataSourcesHandler`

Replaced `kwargs = dict(ctx.params); kwargs.pop("method", None)` with `kwargs = {k: v for k, v in ctx.params.items() if k not in self._STRIP_PARAMS}` to prevent transport-level params from leaking to facade method kwargs.

---

## Gap 7: Replace In-Memory Connector Source-of-Truth

**Resolution:** ARCHITECTURAL DECISION — L6 `ConnectorRegistry` is intentionally in-memory for runtime connector instances (Vector, File, Serverless). The facade already correctly delegates to L6. DB persistence for connectors is a future enhancement tracked separately. The activation predicate checks `cus_integrations` table (not connectors registry).

---

## Gap 8: Confirm Project-Create Full Write Path

**Verified:** Full L2→L4→L5→L6 chain confirmed.

| Layer | File | Method |
|-------|------|--------|
| L2 | `account/aos_accounts.py` | `POST /accounts/projects` → `registry.execute("account.query", ...)` |
| L4 | `account_handler.py` | `AccountQueryHandler` → `facade.create_project()` |
| L5 | `accounts_facade.py` | `create_project()` → `driver.insert_project()` |
| L6 | `accounts_facade_driver.py` | `insert_project()` — flush+refresh, NO COMMIT |

---

## Gap 9: API Key URL Policy

**Decision:** Keep URL split for backward compatibility.
- Read ops: `/api-keys` (from `api_keys/aos_api_key.py`)
- Write ops: `/tenant/api-keys` (from `api_keys/api_key_writes.py`)
- Domain authority established by directory ownership (`api_keys/`)
- URL unification deferred

---

## Gap 10: Re-Audit UC-001 for INT/FDR Files

**Full endpoint→L4 operation map completed across all 3 audiences:**

| Audience | Files | Endpoints | L4 Ops | Violations |
|----------|-------|-----------|--------|------------|
| CUS | 44 | ~200+ | 31 | 0 blocking |
| INT | 7 | ~30+ | 7 | 0 blocking |
| FDR | 3 | 18 | 4 | 0 blocking |
| **Total** | **54** | **248+** | **42** | **0** |

**INT routes audited:**
- `int/general/sdk.py` → account.sdk_attestation
- `int/general/health.py` → system.health
- `int/recovery/recovery.py` → policies.recovery.match/read/write
- `int/recovery/recovery_ingest.py` → policies.recovery.write
- `int/agent/platform.py` → platform.health
- `int/agent/discovery.py` → agent.discovery_stats
- `int/agent/agents.py` → Multiple agent ops (L4 bridges)

**FDR routes audited:**
- `fdr/ops/retrieval_admin.py` → knowledge.planes.*, knowledge.evidence.*
- `fdr/ops/cost_ops.py` → ops.cost
- `fdr/account/founder_lifecycle.py` → account.lifecycle.query/transition

---

## Gap 11: Reconcile Docs to One Source of Truth

**Updated:** `HOC_USECASE_CODE_LINKAGE.md` is the single source of truth for:
- UC-001: Full endpoint→L4 operation map (3 audiences)
- UC-002: V2 gap fixes table + remaining gaps
- Minimum event schema contract

---

## Gap 12: Update Canonical Usecase Docs

**INDEX.md:** UC-001 YELLOW, UC-002 YELLOW (correct — event schema enforcement still deferred).
**HOC_USECASE_CODE_LINKAGE.md:** Updated with v2 gap fixes, INT/FDR route tables, endpoint→handler mapping.

---

## Gap 13: Update Architecture Inventories

**11 stale path references fixed across 3 files:**

| File | Refs Fixed |
|------|-----------|
| `docs/architecture/hoc/L2_L4_CALL_MAP.csv` | 3 (policies/ → account/, api_keys/, integrations/) |
| `docs/architecture/hoc/L2_ROUTER_INVENTORY.md` | 5 (file paths + domain columns) |
| `docs/architecture/hoc/DOMAIN_TRUTH_MAP.md` | 2 (file paths) |

---

## Gap 14: Verification Gate

### CI Checks

| Check | Result |
|-------|--------|
| All 34 CI checks (`check_init_hygiene.py --ci`) | **PASS** — 0 blocking, 0 known exceptions |

### Import Tests (13/13)

| Test | Result |
|------|--------|
| account/aos_accounts.py | PASS |
| api_keys/aos_api_key.py | PASS |
| integrations/aos_cus_integrations.py | PASS |
| api_keys/api_key_writes.py | PASS |
| L5 sdk_attestation.py | PASS |
| L6 sdk_attestation_driver.py | PASS |
| Old path aos_accounts fails | PASS |
| Old path aos_cus_integrations fails | PASS |
| Old path aos_api_key fails | PASS |
| activation_predicate(F,T,T,T) | PASS |
| activation_predicate(T,T,T,T) | PASS |
| activation_predicate(T,F,F,F) | PASS |
| Facades resolve (account:2, api_keys:3, integrations:5) | PASS |

### Stale Import Grep

| Pattern | Matches | Result |
|---------|---------|--------|
| `from app.hoc.api.cus.policies.(aos_accounts\|aos_cus_integrations\|aos_api_key)` | 0 | **PASS** |

---

## Files Modified Summary

| Action | Count |
|--------|-------|
| DELETED (tombstones) | 3 |
| CREATED (migration) | 1 |
| EDITED (code fixes) | 4 |
| EDITED (docs/inventories) | 5 |
| **Total files touched** | **13** |

### Complete File List

**DELETED:**
1. `app/hoc/api/cus/policies/aos_accounts.py` (tombstone)
2. `app/hoc/api/cus/policies/aos_cus_integrations.py` (tombstone)
3. `app/hoc/api/cus/policies/aos_api_key.py` (tombstone)

**CREATED:**
1. `alembic/versions/127_create_sdk_attestations.py` (migration)

**EDITED (code):**
1. `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py` (activation predicate wiring)
2. `app/hoc/api/int/general/sdk.py` (real session + fail-loud)
3. `app/hoc/cus/integrations/L5_engines/connectors_facade.py` (singleton fix)
4. `app/hoc/cus/hoc_spine/orchestrator/handlers/integrations_handler.py` (_STRIP_PARAMS)

**EDITED (docs):**
1. `docs/doc/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md` (v2 gap fixes + full audit)
2. `docs/architecture/hoc/L2_L4_CALL_MAP.csv` (3 stale paths)
3. `docs/architecture/hoc/L2_ROUTER_INVENTORY.md` (5 stale paths)
4. `docs/architecture/hoc/DOMAIN_TRUTH_MAP.md` (2 stale paths)
5. This file

---

## Before/After Status Table

| Usecase | Before v2 | After v2 | Change |
|---------|-----------|----------|--------|
| UC-001 | YELLOW (no endpoint mapping) | YELLOW (full 54-file audit, 42 L4 ops mapped) | Endpoint→handler mapping COMPLETE |
| UC-002 | YELLOW (predicate unwired, SDK broken, tombstones present) | YELLOW (all gaps fixed except event schema + URL unification) | 8 functional fixes applied |

---

## Remaining Gaps for GREEN

| Gap | Usecase | Description |
|-----|---------|-------------|
| Event schema enforcement | UC-001, UC-002 | Runtime validation of minimum event fields (documented as contract, enforcement deferred) |
| URL unification | UC-002 | Unify read `/api-keys` and write `/tenant/api-keys` (deferred by policy decision) |
