# HOC_API_KEYS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan_implemented

**Created:** 2026-02-20 UTC
**Executor:** Claude
**Status:** DONE (corrective patch #2 applied 2026-02-20 — final: 29 tests, 222 t5 suite)

## 1. Execution Summary

- Overall result: ALL 5 TASKS COMPLETE + 2 CORRECTIVE PATCHES — api_keys domain runtime-invariant correctness closed with real-path enforcement, method-aware gating, and bypass-proof enrichment proven (final: 29 tests, 222 t5 suite)
- Scope delivered: BI-APIKEY-001 fail-closed enforcement on real dispatch path (`api_keys.write` → `api_key.create`), context enricher mechanism for authoritative tenant_status resolution, MONITOR/STRICT mode proofs, OperationRegistry dispatch proofs via enricher (no synthetic tenant_status), query non-trigger proof, tracker + docs updated
- Scope not delivered: None — full plan scope delivered

## 2. Task Completion Matrix

| Task ID | Status | Evidence | Notes |
|---------|--------|----------|-------|
| AK-DELTA-01 | DONE | `business_invariants.py`, `api_keys_handler.py` | Gap confirmed: `api_key.create` (invariant) vs `api_keys.write` (dispatch). Alias required. |
| AK-DELTA-02 | DONE | `business_invariants.py` — `INVARIANT_OPERATION_ALIASES["api_keys.write"] = "api_key.create"` | Alias added; smoke-tested: write triggers BI-APIKEY-001, query does not |
| AK-DELTA-03 | DONE | `tests/governance/t5/test_api_keys_runtime_delta.py` — 29 tests, 6 classes (final) | All 29 green. Covers fail-closed, positive, alias, MONITOR, STRICT, dispatch via enricher, bypass proof, method-aware gating |
| AK-DELTA-04 | DONE | Section 3 below | 5/5 verification commands pass: 29 domain, 222 t5 suite, CI all green (final) |
| AK-DELTA-05 | DONE | This file + tracker row updated | api_keys row DONE (2026-02-20), update log appended |

## 2a. Corrective Iteration (2026-02-20)

**Problem identified:** BI-APIKEY-001 checker depended on caller-supplied `tenant_status`, but the real `api_keys.write` dispatch path never includes `tenant_status` in params. The checker's `if tenant_status and tenant_status != "ACTIVE"` guard passed trivially when `tenant_status` was absent, making the invariant toothless on the real dispatch path.

**Approach chosen:** Preferred approach — enrich invariant context with authoritative tenant status before evaluation.

**Justification:** The alternative (make checker perform authoritative DB lookup) would violate the purity constraint of `business_invariants.py` (stdlib-only, no framework imports). The enricher approach keeps the checker pure while providing authoritative data at the L4 registry level.

**Three-part fix:**

| Part | Change | File |
|------|--------|------|
| 1. Fail-closed checker | Changed `api_key.create` checker to REQUIRE `tenant_status` — fails when absent | `business_invariants.py` |
| 2. Context enricher mechanism | Added `_context_enrichers` dict + `register_context_enricher()` + pre-invariant enrichment in `execute()` | `operation_registry.py` |
| 3. Authoritative enricher | Added `_enrich_api_keys_write_context()` — queries `tenants.status` via sync_session before invariant evaluation | `api_keys_handler.py` |

**Before vs After:**

| Aspect | Before (buggy) | After (corrected) |
|--------|----------------|-------------------|
| Checker behavior on missing `tenant_status` | PASS (guard skipped) | FAIL ("tenant_status is required but missing from context — fail-closed") |
| Real dispatch path | Invariant always passed trivially | Enricher resolves authoritative status; checker validates |
| Test proof | Synthetic `tenant_status` in params | Enricher-based or no-enricher (proves fail-closed) |
| Tests | 20 | 22 (intermediate; final after patch #2: 29) |

## 3. Evidence and Validation

### Files Changed (self-reported; see Repository State Disclosure below)

| File | Change | Git Status |
|------|--------|------------|
| `app/hoc/cus/hoc_spine/authority/business_invariants.py` | Added `"api_keys.write": "api_key.create"` to `INVARIANT_OPERATION_ALIASES`; changed `api_key.create` checker to require `tenant_status` (fail-closed); added method-aware gate | `M` (tracked, diffable) |
| `app/hoc/cus/hoc_spine/orchestrator/operation_registry.py` | Added `_context_enrichers` dict, `register_context_enricher()` method, pre-invariant enrichment call in `execute()` | `M` (tracked, diffable) |
| `app/hoc/cus/hoc_spine/orchestrator/handlers/api_keys_handler.py` | Added `_enrich_api_keys_write_context()` enricher; registered in `register()`; removed caller bypass; added method-aware gate | `M` (tracked, diffable) |
| `tests/governance/t5/test_api_keys_runtime_delta.py` | **CREATED** then **CORRECTED** twice — final: 29 tests across 6 classes (20 → 22 after patch #1 → 29 after patch #2) | `??` (untracked, not diffable) |
| `app/hoc/docs/architecture/usecases/HOC_DOMAIN_RUNTIME_INVARIANT_COMPLETION_TRACKER_2026_02_20.md` | api_keys test count 20→22→29, corrective log entries, fixed activity/analytics/logs anchors | `??` (untracked, not diffable) |
| `app/hoc/docs/architecture/usecases/HOC_API_KEYS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan.md` | Status: READY_FOR_EXECUTION → DONE (self-reported; file is untracked so change cannot be git-proven) | `??` (untracked, not diffable) |

### Test Coverage (final: 29 tests, 6 classes)

| Class | Count | Coverage |
|-------|-------|----------|
| `TestApiKeysInvariantContracts` | 8 | Fail-closed: missing tenant_id, empty tenant_id, missing tenant_status, SUSPENDED, CREATING. Method-aware: revoke passes, list passes. Positive: ACTIVE |
| `TestApiKeysInvariantAlias` | 3 | Alias exists, check_all resolves write → BI-APIKEY-001, query non-trigger |
| `TestApiKeysInvariantModes` | 5 | MONITOR: non-raise + details. STRICT: raises missing tenant, raises SUSPENDED, passes ACTIVE |
| `TestApiKeysRegistryDispatch` | 8 | Query dispatch, write dispatch via enricher, STRICT blocks without enricher, STRICT blocks with SUSPENDED enricher, MONITOR allows without enricher, MONITOR allows with SUSPENDED enricher, unregistered fail, real handler+enricher registration |
| `TestApiKeysEnricherBypassProof` | 2 | Enricher ignores caller-supplied tenant_status (proves bypass impossible), enricher skips non-create methods |
| `TestApiKeysMethodAwareDispatch` | 3 | STRICT allows revoke without enricher, STRICT allows list without enricher, STRICT still blocks create without enricher |

### Commands Executed (Corrective Iteration — intermediate, superseded by patch #2 below)

```bash
# 1. Domain-specific runtime delta proof (intermediate: 22; final after patch #2: 29)
$ cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/governance/t5/test_api_keys_runtime_delta.py
22 passed in 3.00s

# 2. Full governance t5 regression suite (intermediate: 215; final after patch #2: 222)
$ PYTHONPATH=. pytest -q tests/governance/t5
215 passed in 4.05s

# 3. CI: operation ownership
$ PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
Operations audited: 123, Conflicts found: 0

# 4. CI: transaction boundaries
$ PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
Files checked: 253, Violations found: 0

# 5. CI: init hygiene
$ PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
All checks passed
```

### STRICT Mode Proof — Without Enricher (Corrective: proves old bug is closed)

```python
# From test_strict_blocks_write_without_enricher:
registry.set_invariant_mode(InvariantMode.STRICT)
# No enricher registered — simulates pre-fix dispatch path
ctx = OperationContext(session=None, tenant_id="t-create-001",
    params={"method": "create_api_key"})
with pytest.raises(BusinessInvariantViolation) as exc_info:
    await registry.execute("api_keys.write", ctx)
assert "BI-APIKEY-001" in exc_info.value.invariant_id
assert not write_handler.execute.called
# PASS — pre-fix path is now blocked (was false-green before)
```

### STRICT Mode Proof — With Enricher Returning SUSPENDED

```python
# From test_strict_blocks_write_with_suspended_enricher:
registry.set_invariant_mode(InvariantMode.STRICT)
registry.register_context_enricher(
    "api_keys.write", lambda ctx: {"tenant_status": "SUSPENDED"}
)
ctx = OperationContext(session=None, tenant_id="t-bad-001",
    params={"method": "create_api_key"})
with pytest.raises(BusinessInvariantViolation):
    await registry.execute("api_keys.write", ctx)
assert not write_handler.execute.called
# PASS — enricher-provided SUSPENDED status blocks dispatch
```

### Happy Path — With Enricher Returning ACTIVE

```python
# From test_write_dispatch_with_enricher:
registry.register_context_enricher(
    "api_keys.write", lambda ctx: {"tenant_status": "ACTIVE"}
)
ctx = OperationContext(session=None, tenant_id="t-write-001",
    params={"method": "create_api_key"})
result = await registry.execute("api_keys.write", ctx)
assert result.success is True
assert write_handler.execute.called
# PASS — enricher provides ACTIVE, invariant passes, handler dispatches
```

### MONITOR Mode Proof — Without Enricher (fail-closed but non-blocking)

```python
# From test_monitor_allows_write_without_enricher:
registry.set_invariant_mode(InvariantMode.MONITOR)
# No enricher — invariant will fail, but MONITOR allows dispatch
ctx = OperationContext(session=None, tenant_id="t-monitor-001",
    params={"method": "create_api_key"})
result = await registry.execute("api_keys.write", ctx)
assert result.success is True
assert write_handler.execute.called
# PASS — MONITOR logs violation but does not block
```

## 4. Deviations from Plan

| Deviation | Reason | Impact |
|-----------|--------|--------|
| Added context enricher mechanism to OperationRegistry | Required to provide authoritative tenant_status before invariant evaluation without violating business_invariants.py purity | Positive — enables authoritative invariant context for any domain |
| Test count 20→22 (intermediate; final: 29 after patch #2) | Corrective iteration added `test_strict_blocks_write_without_enricher` and `test_monitor_allows_write_without_enricher` to prove the old false-green path is closed; replaced synthetic `tenant_status` tests with enricher-based proofs | Positive — stronger real-path coverage |
| Changed `test_bi_apikey_001_passes_tenant_without_status` to `test_bi_apikey_001_rejects_missing_tenant_status` | Checker now requires tenant_status (fail-closed), so absent status is a FAIL not a PASS | Corrective — the old assertion was testing the buggy behavior |

## 2b. Corrective Patch #2 (2026-02-20)

**Three audit findings addressed:**

| Finding | Severity | Fix |
|---------|----------|-----|
| Caller-supplied `tenant_status` bypass in enricher | HIGH | Removed `if ctx.params.get("tenant_status"): return {}` — enricher always queries DB |
| Over-broad invariant application to revoke/list | MEDIUM | Method-aware gate in both enricher (`_enrich_api_keys_write_context`) and checker (`_default_check`) |
| Docs truthfulness | LOW | Tracker updated with correct test count and corrective log |

**Four-part fix:**

| Part | Change | File |
|------|--------|------|
| 1. Remove bypass | Deleted `if ctx.params.get("tenant_status"): return {}` | `api_keys_handler.py` |
| 2. Enricher method gate | Added `if method and method != "create_api_key": return {}` | `api_keys_handler.py` |
| 3. Checker method gate | Added method-aware skip: non-create methods return True | `business_invariants.py` |
| 4. Tests | 7 new tests (29 total): bypass proof, enricher skip, revoke/list dispatch, create still blocked | `test_api_keys_runtime_delta.py` |

**New test classes (corrective patch #2):**

| Class | Count | Coverage |
|-------|-------|----------|
| `TestApiKeysEnricherBypassProof` | 2 | Enricher ignores caller-supplied tenant_status (proves bypass impossible), enricher skips non-create methods |
| `TestApiKeysMethodAwareDispatch` | 3 | STRICT allows revoke without enricher, STRICT allows list without enricher, STRICT still blocks create without enricher |
| `TestApiKeysInvariantContracts` (extended) | +2 | `test_bi_apikey_001_passes_revoke_method`, `test_bi_apikey_001_passes_list_method` |

**Verification (corrective patch #2):**

```bash
$ PYTHONPATH=. pytest -q tests/governance/t5/test_api_keys_runtime_delta.py
29 passed in 2.80s

$ PYTHONPATH=. pytest -q tests/governance/t5
222 passed in 3.67s

$ PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
Operations audited: 123, Conflicts found: 0

$ PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
Files checked: 253, Violations found: 0

$ PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
All checks passed
```

## 5. Repository State Disclosure

- **Workspace is dirty.** At time of writing, `git status --short` reports 40+ modified (`M`) and multiple untracked (`??`) files across the repository — this evidence document was produced in a multi-session workspace with accumulated changes from prior work (PR2 auth closure, runtime delta iterations, etc.).
- **Both API-keys plan files are untracked.** `git status --short` shows `??` for both `HOC_API_KEYS_..._plan.md` and `HOC_API_KEYS_..._plan_implemented.md`. They were created during these sessions and have never been committed.
- **Repo-level single-file-change proof is not derivable from git baseline here.** Because the workspace contains pre-existing dirty state and the target files are untracked, no `git diff` can prove that edits were confined to a single file. The "Files Changed" table above is self-reported by the executor, not git-proven.
- **What IS provable:** Runtime test evidence (29/29 domain tests pass, 222/222 t5 suite pass, CI green) is independently reproducible by re-running the verification commands.

```
# Captured 2026-02-20:
$ git status --short -- backend/app/hoc/docs/architecture/usecases/HOC_API_KEYS*
?? backend/app/hoc/docs/architecture/usecases/HOC_API_KEYS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan.md
?? backend/app/hoc/docs/architecture/usecases/HOC_API_KEYS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan_implemented.md
```

## 6. Open Blockers

None — all acceptance criteria met.

## 7. Handoff Notes

- **Follow-up recommendations:** 3 PENDING domains remain: `activity`, `analytics`, `logs`. All three have invariant anchors already defined in `business_invariants.py` (BI-ACTIVITY-001, BI-ANALYTICS-001, BI-LOGS-001). They need their domain delta iterations executed.
- **Risks remaining:** None for api_keys domain. The context enricher mechanism is generic and available for other domains that need authoritative invariant context enrichment.
- **Invariant alias registry:** 2 entries: `account.onboarding.advance → onboarding.activate`, `api_keys.write → api_key.create`.
- **Context enricher registry:** 1 entry: `api_keys.write → _enrich_api_keys_write_context` (resolves tenant status from DB).
- **Method-aware gating:** Dual gate in enricher (skip DB query for non-create) + checker (skip invariant evaluation for non-create). Both gates use `context.get("method") != "create_api_key"`.
