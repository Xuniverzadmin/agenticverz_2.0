# HOC_INTEGRATIONS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan

**Created:** 2026-02-18 05:31:49 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION
**Parent references:**
- `backend/app/hoc/docs/architecture/usecases/HOC_CONTROLS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `docs/memory-pins/PIN-590-controls-domain-delta-runtime-correctness-audit-pass-2026-02-16.md`
- `docs/memory-pins/PIN-585-integrations-list-facade-pr8-contract-hardening.md`
- `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`

## 1. Objective

- Primary outcome: execute a delta-only runtime correctness iteration for `integrations`, adding only missing controls and in-process runtime proof.
- Business/technical intent: increase confidence that integration activation/deactivation and PR-8 list dispatch boundaries are deterministic, fail-safe, and architecture-compliant.

## 2. Scope

- In scope:
- Build an integrations-domain gap matrix across 7 assurance dimensions (invariants, specs, runtime assertions, mutation, property, replay, failure injection).
- Cover at minimum three anchor operations/surfaces:
  - `integration.enable` (existing invariant anchor),
  - `integration.disable` (spec anchor and expected invariant delta),
  - `integrations.query` with `method=list_integrations` (PR-8 read boundary).
- Add only missing runtime contract checks and operation assertions; reuse existing controls where already present.
- Strengthen in-process assertions using real `OperationRegistry.execute(...)` dispatch.
- Re-run strict deterministic gates and capture reproducible evidence.

- Out of scope:
- Stage 2 external credentials/provider runtime.
- Cross-domain product refactors outside integrations runtime correctness.
- Non-deterministic/manual-only validation.

## 3. Assumptions and Constraints

- Assumptions:
- `BI-INTEG-001` exists and is the baseline invariant for `integration.enable`.
- `SPEC-007` (`integration.enable`) and `SPEC-008` (`integration.disable`) are active and strict-validated.
- Replay fixtures include integrations anchors:
  - `REPLAY-008` (`integration.enable`)
  - `REPLAY-009` (`integration.disable`)
- PR-8 read facade contract (`GET /cus/integrations/list`) is active with strict allowlist and one-dispatch semantics.

- Constraints:
- Preserve HOC topology: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7` only.
- Keep `hoc_spine` as single execution authority.
- Keep all new checks deterministic and CI-runnable.

- Non-negotiables:
- Mark existing controls as `PRESENT_REUSED`; add only true deltas.
- Every `DONE` requires both command evidence and file evidence.
- No docs-only completion for runtime-proof tasks.

## 4. Acceptance Criteria (Per Step)

1. **INT-DELTA-01 Baseline Gap Matrix**
- Artifact exists: `backend/app/hoc/docs/architecture/usecases/INTEGRATIONS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md`.
- Matrix includes the three required anchors (`integration.enable`, `integration.disable`, `integrations.query:list_integrations`) with rationale.
- Every row is classified as:
  - `PRESENT_REUSED`
  - `PRESENT_STRENGTHEN`
  - `MISSING`

2. **INT-DELTA-02 Runtime Contract Delta (No Duplication)**
- Existing controls/specs are reused where present (`BI-INTEG-001`, `SPEC-007`, `SPEC-008`).
- Missing integration invariant/runtime contract coverage identified in step 1 is added without duplicate IDs.
- Positive and negative contract tests are added for all newly added controls.
- `PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict` passes.

3. **INT-DELTA-03 Deeper In-Process Execution Assertions**
- New/updated tests dispatch via real `OperationRegistry.execute(...)` and assert:
  - integration enable/disable success paths,
  - invalid/blocked paths,
  - mode behavior (`MONITOR` vs `STRICT`),
  - deterministic one-dispatch behavior for PR-8 list operation.
- Static token/import checks alone are insufficient.

4. **INT-DELTA-04 Mutation + Property Strengthening**
- Strict mutation gate rerun passes:
  - `PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict`
- Integration lifecycle/property tests are added or strengthened from step-1 gaps.
- Any relevant survivors in touched scope are documented with disposition.

5. **INT-DELTA-05 Replay + Failure Injection + Data Quality**
- Strict replay passes with zero drift:
  - `PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict`
- Integrations-focused failure injection is added/expanded (driver timeout, stale/invalid state, connector unregistered, downstream connectivity failure).
- `PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict` remains pass.

6. **INT-DELTA-06 Architecture/Gate Closure + Defect Feedback**
- Architecture checks remain clean:
  - ownership,
  - transaction boundaries,
  - init hygiene.
- Full gatepack remains green (`16/16 PASS` minimum; if count changed, explain with evidence).
- Any discovered defect is linked to permanent guardrail artifacts (invariant/test/replay), not patch-only.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| INT-DELTA-01 | Baseline | Build integrations gap matrix and classify all rows as REUSED/STRENGTHEN/MISSING | TODO | `backend/app/hoc/docs/architecture/usecases/INTEGRATIONS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md` | Must include enable/disable/list anchors |
| INT-DELTA-02 | Contracts | Add missing invariant/runtime contract deltas with no duplicate IDs; reuse BI-INTEG-001/SPEC-007/SPEC-008 | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py`, `backend/tests/governance/t5/` | Delta-only additions |
| INT-DELTA-03 | Runtime Proof | Add registry dispatch assertions for integrations operations and PR-8 list semantics | TODO | `backend/tests/governance/t5/test_integrations_runtime_delta.py`, `backend/tests/api/test_integrations_public_facade_pr8.py` | Real `OperationRegistry.execute` proof required |
| INT-DELTA-04 | Mutation/Property | Rerun strict mutation and add/strengthen integration lifecycle property tests | TODO | `backend/reports/mutation_summary.json`, `backend/tests/property/` | Document survivors if any |
| INT-DELTA-05 | Replay/Failure/Data | Enforce strict replay + expand integrations fault tests + keep data-quality strict green | TODO | `backend/tests/verification/`, `backend/tests/failure_injection/`, replay fixtures | Zero replay drift |
| INT-DELTA-06 | Closure | Rerun architecture + gatepack and complete evidence return doc | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_INTEGRATIONS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md` | Evidence-complete handoff |

## 6. Execution Order

1. INT-DELTA-01
2. INT-DELTA-02
3. INT-DELTA-03
4. INT-DELTA-04
5. INT-DELTA-05
6. INT-DELTA-06

## 7. Verification Commands

```bash
cd /root/agenticverz2.0
scripts/ops/hoc_session_bootstrap.sh --strict

cd /root/agenticverz2.0/backend

# Baseline checks
PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict
PYTHONPATH=. pytest -q tests/governance/t5/test_business_invariants_runtime.py
PYTHONPATH=. pytest -q tests/api/test_integrations_public_facade_pr8.py
PYTHONPATH=. pytest -q tests/verification/test_differential_replay.py
PYTHONPATH=. pytest -q tests/failure_injection/test_driver_fault_safety.py

# Integrations delta runtime suite (new/expanded)
PYTHONPATH=. pytest -q tests/governance/t5/test_integrations_runtime_delta.py

# Integrations property proof (new/expanded)
PYTHONPATH=. pytest -q tests/property/test_integrations_lifecycle_properties.py

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
- New disable/list invariants can over-block if transport context is incomplete.
- Replay drift may surface if invariant linkage is corrected.
- Added failure/property tests may expose latent connector state bugs.

- Rollback plan:
- Revert only offending delta changes while keeping evidence artifacts intact.
- Keep stricter behavior under explicit mode/config where required.
- Convert rollback-triggering defects into permanent guardrails (invariant/tests/replay), never silent rollback.

## 9. Claude Fill Rules

1. Update each task status: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record exact evidence paths per task (files, commands, reports).
3. Mark each key control row as `PRESENT_REUSED`, `PRESENT_STRENGTHEN`, or `MISSING->ADDED`.
4. If blocked, include blocker, impact, and minimal next action.
5. Do not delete sections; append execution facts only.
6. Return completed results in `HOC_INTEGRATIONS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`.
