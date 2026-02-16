# HOC_TENANT_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan

**Created:** 2026-02-16 17:45:25 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION
**Parent references:**
- `backend/app/hoc/docs/architecture/usecases/HOC_INCIDENTS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_POLICIES_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_BUSINESS_ASSURANCE_NEXT_PHASE_SIX_STEP_EXECUTION_2026_02_16_plan_implemented.md`
- `docs/memory-pins/PIN-586-incidents-domain-delta-runtime-correctness-audit-pass-2026-02-16.md`

## 1. Objective

- Primary outcome: execute a delta-only runtime correctness iteration for the `tenant` operation scope (`tenant.create`, `tenant.delete`) with stronger in-process proof and no duplicate controls.
- Business/technical intent: harden tenant lifecycle decision correctness (creation/deletion safety, invariant enforcement, replay correctness, and failure behavior) while preserving HOC architecture constraints.

## 2. Scope

- In scope:
- Build tenant-domain gap matrix against existing controls (invariants/specs/runtime/property/replay/failure/mutation).
- Add only missing exact runtime contracts for `tenant.create` and `tenant.delete`.
- Add deeper in-process `OperationRegistry.execute(...)` assertions for tenant operations (MONITOR/STRICT behavior, deterministic outputs).
- Expand tenant-focused failure-injection and property-based lifecycle coverage where gaps exist.
- Re-run deterministic assurance gates and publish full evidence.

- Out of scope:
- Stage 2 real-provider/credential validation.
- Cross-domain product changes unrelated to tenant/account lifecycle correctness.
- Architecture/topology refactors.

## 3. Assumptions and Constraints

- Assumptions:
- Spec registry already includes:
  - `SPEC-001 tenant.create`
  - `SPEC-002 tenant.delete`
- Existing `BI-TENANT-001` guards `project.create`, not `tenant.create`/`tenant.delete`.
- Replay fixtures already include:
  - `REPLAY-001` (`tenant.create`)
  - `REPLAY-003` (`tenant.delete`)
- No `literature/hoc_domain/tenant/*` canon exists; use `literature/hoc_domain/account/*` as authoritative domain canon fallback.

- Constraints:
- Preserve HOC layering: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7` only.
- Keep default runtime behavior safe unless explicitly configured otherwise.
- All new tests/checks must be deterministic and CI-runnable.

- Non-negotiables:
- Reuse existing controls when present (`PRESENT_REUSED`) and strengthen proof instead of duplicating.
- Any `DONE` status requires command evidence + file evidence.
- No docs-only completion for runtime-proof tasks.

## 4. Acceptance Criteria (Per Step)

1. **TEN-DELTA-01 Baseline Gap Matrix**
- Artifact exists: `backend/app/hoc/docs/architecture/usecases/TENANT_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md`.
- Matrix covers at minimum:
  - `tenant.create`
  - `tenant.delete`
  - `project.create` (as existing tenant-adjacent control anchor)
- Every control row is classified as one of:
  - `PRESENT_REUSED`
  - `PRESENT_STRENGTHEN`
  - `MISSING`

2. **TEN-DELTA-02 Runtime Contract Delta (No Duplication)**
- Existing controls reused (`BI-TENANT-001`, `SPEC-001`, `SPEC-002`).
- Missing exact invariants for `tenant.create`/`tenant.delete` added (expected delta IDs) with positive/negative tests.
- `PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict` passes.

3. **TEN-DELTA-03 Deeper In-Process Execution Assertions**
- New/updated tests dispatch through real `OperationRegistry.execute(...)` and assert:
  - successful tenant create/delete path,
  - blocked/invalid path,
  - mode behavior (`MONITOR` vs `STRICT`),
  - deterministic/idempotent result behavior where applicable.
- Static token/import checks alone are insufficient for completion.

4. **TEN-DELTA-04 Mutation + Property Strengthening**
- Strict mutation gate rerun passes:
  - `PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict`
- Tenant lifecycle property coverage is validated and strengthened where gap matrix marks missing.
- Any surviving mutants relevant to touched scope are documented with disposition.

5. **TEN-DELTA-05 Replay + Failure Injection + Data Quality**
- Strict replay passes with zero drift:
  - `PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict`
- Tenant-focused failure-injection tests are added/expanded (timeouts, invalid deletes, stale state/conflict paths).
- `PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict` remains pass.

6. **TEN-DELTA-06 Architecture/Gate Closure + Defect Feedback**
- Architecture checks remain clean:
  - ownership,
  - transaction boundaries,
  - init hygiene.
- Full gatepack remains green (`16/16 PASS` minimum; if count changes, explain with evidence).
- Any defect discovered is linked to permanent guardrail artifacts (invariant/tests), not patch-only.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| TEN-DELTA-01 | Baseline | Build tenant gap matrix and classify all controls as REUSED/STRENGTHEN/MISSING | TODO | `backend/app/hoc/docs/architecture/usecases/TENANT_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md` | Include `tenant.create`, `tenant.delete`, `project.create` anchor |
| TEN-DELTA-02 | Contracts | Add missing exact tenant invariants (delta only) + runtime contract tests | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py`, `backend/tests/governance/t5/` | No duplicate invariant IDs |
| TEN-DELTA-03 | Runtime Proof | Add in-process registry dispatch assertions for tenant operations and mode behavior | TODO | `backend/tests/governance/t5/` | Real `OperationRegistry.execute` usage |
| TEN-DELTA-04 | Mutation/Property | Rerun strict mutation + validate/expand tenant lifecycle property tests | TODO | `backend/reports/mutation_summary.json`, `backend/tests/property/` | Record survivor disposition |
| TEN-DELTA-05 | Replay/Failure/Data | Enforce strict replay + expand tenant failure injection + keep data-quality strict pass | TODO | `backend/tests/verification/`, `backend/tests/failure_injection/` | Zero replay drift |
| TEN-DELTA-06 | Closure | Re-run architecture + gatepack and populate return doc with complete evidence | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_TENANT_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md` | Evidence complete |

## 6. Execution Order

1. TEN-DELTA-01
2. TEN-DELTA-02
3. TEN-DELTA-03
4. TEN-DELTA-04
5. TEN-DELTA-05
6. TEN-DELTA-06

## 7. Verification Commands

```bash
cd /root/agenticverz2.0
scripts/ops/hoc_session_bootstrap.sh --strict

cd /root/agenticverz2.0/backend

# Baseline checks
PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict
PYTHONPATH=. pytest -q tests/governance/t5/test_business_invariants_runtime.py
PYTHONPATH=. pytest -q tests/verification/test_differential_replay.py
PYTHONPATH=. pytest -q tests/failure_injection/test_driver_fault_safety.py

# Tenant delta runtime suite (new/expanded)
PYTHONPATH=. pytest -q tests/governance/t5/test_tenant_runtime_delta.py

# Property proof for tenant lifecycle (new or expanded)
PYTHONPATH=. pytest -q tests/property/test_tenant_lifecycle_properties.py

# Mutation gate strict
PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict

# Replay/data quality strict
PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict
PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict

# Architecture + final closure
PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
cd /root/agenticverz2.0 && bash backend/scripts/verification/run_business_assurance_gatepack.sh
```

## 8. Risks and Rollback

- Risks:
- Tenant invariants can over-block if context contracts are incomplete.
- Replay fixture contract drift may appear (naming/state normalization mismatches).
- New lifecycle property tests may reveal latent nondeterminism.

- Rollback plan:
- Revert only offending delta changes while preserving evidence docs.
- Keep strict behavior behind explicit configuration if runtime risk appears.
- Convert rollback-triggering defects into permanent invariant/test guardrails.

## 9. Claude Fill Rules

1. Update each task status: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record exact evidence paths per task (files, commands, reports).
3. Tag each key control as `PRESENT_REUSED`, `PRESENT_STRENGTHEN`, or `MISSING->ADDED`.
4. If blocked, include blocker, impact, and minimal next action.
5. Do not delete sections; append execution facts only.
6. Return completed results in `HOC_TENANT_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`.
