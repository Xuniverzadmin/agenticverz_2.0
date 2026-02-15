# TODO_PLAN — Implementation Evidence

**Executed:** 2026-02-11
**Plan:** `TODO_PLAN.md`
**Scope:** Enforce DB as authoritative, keep ConnectorRegistry cache-only, add CI/test guardrails, runtime observability

---

## Step 1: Authority Contract Lock — DONE

### connector_registry_driver.py

**File:** `backend/app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py`

**Change:** Added `AUTHORITY CONTRACT (UC-002)` block to module docstring.

Contract states:
- This module is a RUNTIME CACHE ONLY
- `_connectors` / `_tenant_connectors` hold live connector instances with active methods
- NOT the source of truth for activation decisions
- Authoritative persistent evidence: `cus_integrations`, `sdk_attestations`, `api_keys`
- References CI check 35 for enforcement

### onboarding_handler.py

**File:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`

**Change:** Added `AUTHORITY CONTRACT` block above activation predicate section.

Contract states:
- Activation decisions use ONLY persistent DB evidence
- Lists exact tables: `api_keys`, `cus_integrations`, `sdk_attestations`
- NEVER import or query `connector_registry_driver`
- References CI check 35 for enforcement
- Added docstring clarification to both sync and async functions

---

## Step 2: Enforce Read Paths — DONE (9 tests)

**File:** `backend/tests/governance/t4/test_activation_predicate_authority.py`

| Test | Category | Result |
|------|----------|--------|
| `test_activation_predicate_all_true` | Pure predicate | PASS |
| `test_activation_predicate_missing_project` | Pure predicate | PASS |
| `test_activation_predicate_missing_all` | Pure predicate | PASS |
| `test_activation_predicate_missing_connector_only` | Pure predicate | PASS |
| `test_activation_section_no_cache_imports` | Static analysis | PASS |
| `test_activation_section_uses_only_db_tables` | Static analysis | PASS |
| `test_predicate_ignores_cache_state` | Semantic boundary | PASS |
| `test_predicate_fails_without_db_evidence` | Semantic boundary | PASS |
| `test_predicate_contract_comment_exists_in_registry_driver` | Contract check | PASS |

**Test categories:**
1. **Pure predicate tests** (4): Verify `check_activation_predicate()` is a pure function that returns `(passed, missing)` based only on its 4 boolean inputs.
2. **Static analysis tests** (2): Parse `onboarding_handler.py` source to verify the activation section contains no imports of `connector_registry_driver`, `ConnectorRegistry`, or `get_connector_registry`, and DOES reference `api_keys`, `cus_integrations`, `sdk_attestations` tables.
3. **Semantic boundary tests** (2): Verify that `connector_validated=True` (DB evidence) -> passes regardless of cache state, and `connector_validated=False` (no DB evidence) -> fails regardless of cache state.
4. **Contract check** (1): Verify `AUTHORITY CONTRACT` and `RUNTIME CACHE ONLY` comments exist in `connector_registry_driver.py`.

---

## Step 3: Persisted Connector Validation Evidence — ALREADY SATISFIED

**Analysis:** The `cus_integrations` table already provides persistent connector validation evidence:

| Column | Purpose | Evidence Role |
|--------|---------|---------------|
| `status` | 'created', 'enabled', 'disabled', 'error' | `status = 'enabled'` IS the validation evidence |
| `health_state` | 'unknown', 'healthy', 'degraded', 'failing' | Health check outcome |
| `health_checked_at` | Timestamp | When validation occurred |
| `health_message` | Text | Failure details |

The activation predicate queries:
```sql
SELECT COUNT(*) AS cnt FROM cus_integrations WHERE tenant_id = :tid AND status = 'enabled'
```

This IS persistent evidence of connector validation. No new migration or table needed.

**Decision:** No code change required. The existing `cus_integrations` table schema is the persistent store for validation evidence. Documented in authority contract comments.

---

## Step 4: CI Guardrail — DONE (Check 35)

**File:** `backend/scripts/ci/check_init_hygiene.py`

**Added:** `check_activation_no_cache_import()` — Check 35.

**Detection logic:**
1. Read `onboarding_handler.py`
2. Find the `ACTIVATION PREDICATE HELPERS` section
3. Scan all non-comment lines in that section
4. Fail if any line contains: `connector_registry_driver`, `connector_registry`, `get_connector_registry`, or `ConnectorRegistry`

**Category:** `ACTIVATION_CACHE_BOUNDARY` (BLOCKING)

**Wired into main():** After check 34 (`check_l2_domain_ownership`).

**Updated header:** Check 35 documented in file header comments.

**CI result:** 35/35 checks pass, 0 blocking violations.

---

## Step 5: Runtime Observability — DONE

**File:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`

**Added structured logging to both activation predicate functions:**

Sync (`_check_activation_conditions`):
```python
logger.info(
    "activation_predicate_evaluated",
    extra={
        "tenant_id": tenant_id,
        "source": "db_only",
        "evidence": {
            "project_ready": has_project,
            "key_ready": has_api_key,
            "connector_validated": has_validated_connector,
            "sdk_attested": has_sdk_attestation,
        },
        "passed": passed,
        "missing": missing,
    },
)
```

Async (`_async_check_activation_conditions`): Same structured log.

**Log fields:**
- `tenant_id`: Tenant context (no secrets)
- `source`: Always `"db_only"` — documents that evidence came from DB, not cache
- `evidence`: Dict of all 4 predicate inputs with boolean values
- `passed`: Overall predicate result
- `missing`: List of missing conditions (empty if passed)

---

## Verification Gate

| Check | Result |
|-------|--------|
| CI: `check_init_hygiene.py --ci` (35 checks) | **PASS** — 0 blocking |
| Pytest: 9 activation predicate authority tests | **PASS** — 9/9 |
| Contract: AUTHORITY CONTRACT in connector_registry_driver.py | **PRESENT** |
| Contract: AUTHORITY CONTRACT in onboarding_handler.py | **PRESENT** |
| Observability: structured log in sync activation predicate | **PRESENT** |
| Observability: structured log in async activation predicate | **PRESENT** |

---

## Acceptance Criteria Checklist

| Criterion | Status |
|-----------|--------|
| Activation path uses only persistent evidence for all 4 keys | **MET** — SQL queries against api_keys, cus_integrations, sdk_attestations |
| ConnectorRegistry is cache-only by contract and tests | **MET** — AUTHORITY CONTRACT comment + 3 static analysis tests |
| CI fails if authoritative flow uses in-memory cache | **MET** — Check 35 (ACTIVATION_CACHE_BOUNDARY) is BLOCKING |
| Usecase docs synchronized | **MET** — INDEX.md + HOC_USECASE_CODE_LINKAGE.md at canonical root |

---

## Files Modified Summary

| Action | File | Step |
|--------|------|------|
| EDITED | `app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py` | 1 |
| EDITED | `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py` | 1, 5 |
| CREATED | `tests/governance/t4/test_activation_predicate_authority.py` | 2 |
| EDITED | `scripts/ci/check_init_hygiene.py` | 4 |
| CREATED | This file | — |
