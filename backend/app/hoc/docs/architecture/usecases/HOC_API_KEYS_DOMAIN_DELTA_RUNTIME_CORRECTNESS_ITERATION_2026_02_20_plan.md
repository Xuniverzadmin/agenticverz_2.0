# HOC_API_KEYS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan

**Created:** 2026-02-20 16:52:39 UTC
**Executor:** Claude
**Status:** DONE
**Parent references:**
- `backend/app/hoc/docs/architecture/usecases/HOC_ACCOUNT_ONBOARDING_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_INTEGRATIONS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_DOMAIN_RUNTIME_INVARIANT_COMPLETION_TRACKER_2026_02_20.md`
- `docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md`

## 1. Objective

- Primary outcome: close API keys runtime-invariant correctness for the real dispatch path and deliver evidence-complete domain closure artifacts.
- Business/technical intent: prove `BI-APIKEY-001` is enforced fail-closed where writes execute (`api_keys.write` create path), while preserving non-blocking read/query paths and HOC layer boundaries.

## 2. Scope

- In scope:
- Validate invariant anchor and dispatch-path mapping:
  - invariant anchor: `BI-APIKEY-001` (`api_key.create`)
  - dispatch operations: `api_keys.write` (create/revoke/list), `api_keys.query` (read)
- Add delta runtime proofs in `tests/governance/t5/test_api_keys_runtime_delta.py` covering:
  - fail-closed negatives for create path (missing tenant context, non-ACTIVE tenant),
  - positive pass case for ACTIVE tenant,
  - `MONITOR` non-blocking behavior,
  - `STRICT` blocking behavior,
  - real `OperationRegistry.execute(...)` pre-dispatch enforcement for create path,
  - explicit proof that query/read path does not incorrectly trigger create invariant.
- If needed, add minimal invariant-alias wiring (`api_keys.write` create method -> `api_key.create`) without broad refactor.
- Update domain tracker status and append UTC evidence entry.
- Out of scope:
- Stage-2 provider/env validation.
- Cross-domain rewiring beyond minimal alias or invariant wiring required for this domain.
- Non-deterministic/manual-only checks.

## 3. Assumptions and Constraints

- Assumptions:
- `BI-APIKEY-001` remains canonical and must not be deleted/renamed.
- API key writes are routed through `api_keys.write` in L4 handler.
- Full t5 + CI scripts remain mandatory pass gates for closure.
- Constraints:
- Maintain HOC topology: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7`.
- No direct L2 -> L5/L6 calls introduced.
- Keep `hoc_spine` as single execution authority.
- Keep changes minimal and domain-scoped.
- Non-negotiables:
- No regression in already-closed domains.
- Query/read routes must not be blocked by create-only invariant checks.
- Every completed task must include file evidence + command evidence.

## 4. Acceptance Criteria

1. `tests/governance/t5/test_api_keys_runtime_delta.py` exists and is green.
2. `BI-APIKEY-001` enforcement is proven on real create dispatch path (`api_keys.write` create flow) in STRICT mode.
3. MONITOR mode on same bad context does not block dispatch.
4. `api_keys.query` path is proven non-triggering for create invariant checks.
5. `PYTHONPATH=. pytest -q tests/governance/t5` is fully green.
6. CI checks pass:
   - `check_operation_ownership.py`
   - `check_transaction_boundaries.py`
   - `check_init_hygiene.py --ci`
7. Tracker row for `api_keys` is updated with invariant IDs, test count, status/date, and implemented plan path.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| AK-DELTA-01 | Baseline | Analyze current invariant anchor (`BI-APIKEY-001`) vs real dispatch operations (`api_keys.write`, `api_keys.query`) and classify delta gap | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py`, `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/api_keys_handler.py` | Must explicitly state if alias mapping is required |
| AK-DELTA-02 | Runtime Contracts | Implement minimal invariant wiring needed for create dispatch enforcement (alias or equivalent), preserving query non-trigger behavior | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py` | Do not broaden invariant scope unintentionally |
| AK-DELTA-03 | Runtime Proof | Add `test_api_keys_runtime_delta.py` with fail-closed/positive/mode/dispatch coverage | TODO | `backend/tests/governance/t5/test_api_keys_runtime_delta.py` | Real `OperationRegistry.execute(...)` assertions required |
| AK-DELTA-04 | Validation | Run mandated tests and CI scripts; capture exact outputs | TODO | Command outputs + this implemented doc | Must include exact pass counts |
| AK-DELTA-05 | Documentation | Update tracker row + append UTC log entry; complete implemented report with final counts and any deviations | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_DOMAIN_RUNTIME_INVARIANT_COMPLETION_TRACKER_2026_02_20.md`, `backend/app/hoc/docs/architecture/usecases/HOC_API_KEYS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan_implemented.md` | Keep counts and status internally consistent |

## 6. Execution Order

1. AK-DELTA-01
2. AK-DELTA-02
3. AK-DELTA-03
4. AK-DELTA-04
5. AK-DELTA-05

## 7. Verification Commands

```bash
cd /root/agenticverz2.0/backend

# Domain-specific runtime delta proof
PYTHONPATH=. pytest -q tests/governance/t5/test_api_keys_runtime_delta.py

# Full governance t5 regression suite
PYTHONPATH=. pytest -q tests/governance/t5

# Architecture/CI guards
PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
```

## 8. Risks and Rollback

- Risks:
- Over-broad alias mapping could apply create invariant to non-create API key methods and cause false blocking.
- Missing method-level guard in tests could allow silent drift in handler behavior.
- STRICT-mode coverage may pass unit-level checks but miss registry pre-dispatch behavior if tests do not assert handler-not-called.
- Rollback plan:
- Revert only domain-specific delta commits/files for API keys.
- Keep tracker/update-log entries truthful; if rollback occurs, mark domain row back to `PENDING` with reason.
- Preserve any non-API-keys changes made earlier in the branch.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. Include exact command outputs for all verification commands in Section 3 of implemented doc.
4. If blocked, include blocker reason and minimal next action.
5. Do not delete plan sections; append execution facts.
6. Return completed results in `HOC_API_KEYS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_20_plan_implemented.md`.
