# HOC_CONTROLS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan

**Created:** 2026-02-16 18:09:29 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION
**Parent references:**
- `backend/app/hoc/docs/architecture/usecases/HOC_TENANT_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_INCIDENTS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_POLICIES_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `docs/memory-pins/PIN-589-tenant-domain-delta-runtime-correctness-audit-pass-2026-02-16.md`

## 1. Objective

- Primary outcome: execute a delta-only runtime correctness iteration for `controls` with deeper in-process proof, without duplicating already-existing guardrails.
- Business/technical intent: increase confidence that threshold and control decisions are safe, deterministic, and fail-closed under faults while preserving HOC architecture boundaries.

## 2. Scope

- In scope:
- Build a controls-domain gap matrix over 7 assurance dimensions (invariants, specs, runtime assertions, mutation, property, replay, failure injection).
- Cover at least `control.set_threshold` plus two control-adjacent anchor operations (selected and justified from current runtime flow).
- Add only missing runtime contracts and operation assertions; reuse existing controls when already present.
- Strengthen in-process execution assertions through real `OperationRegistry.execute(...)` dispatch.
- Re-run strict deterministic gates and publish evidence.

- Out of scope:
- Stage 2 real-provider credentials or external environment dependencies.
- Topology refactors or cross-domain product feature work not required by this delta.
- Non-deterministic checks or manual-only acceptance.

## 3. Assumptions and Constraints

- Assumptions:
- `SPEC-011 (control.set_threshold)` and `BI-CTRL-001` already exist and are active baseline controls.
- Replay fixture coverage includes `REPLAY-012` for `control.set_threshold`.
- Controls canon is authoritative for this run:
  - `literature/hoc_domain/controls/SOFTWARE_BIBLE.md`
  - `literature/hoc_domain/controls/DOMAIN_CAPABILITY.md`

- Constraints:
- Preserve HOC layering: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7` only.
- `hoc_spine` remains execution authority; no direct L2->L5/L6 bypass.
- All new checks/tests must be deterministic and CI-runnable.

- Non-negotiables:
- Reuse existing controls as `PRESENT_REUSED`; add only true deltas.
- `DONE` requires both command evidence and file evidence.
- No docs-only closure for runtime-proof tasks.

## 4. Acceptance Criteria (Per Step)

1. **CTRL-DELTA-01 Baseline Gap Matrix**
- Artifact exists: `backend/app/hoc/docs/architecture/usecases/CONTROLS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md`.
- Matrix includes at minimum `control.set_threshold` plus two control-adjacent anchors and explicitly states why anchors were chosen.
- Every row is classified as one of:
  - `PRESENT_REUSED`
  - `PRESENT_STRENGTHEN`
  - `MISSING`

2. **CTRL-DELTA-02 Runtime Contract Delta (No Duplication)**
- Existing controls are reused where present (`BI-CTRL-001`, `SPEC-011`).
- Missing invariant/runtime contract coverage identified in step 1 is added without duplicate IDs.
- Positive and negative contract tests are added for all newly added controls.
- `PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict` passes.

3. **CTRL-DELTA-03 Deeper In-Process Execution Assertions**
- New/updated tests dispatch via real `OperationRegistry.execute(...)` and assert:
  - success path behavior for control operation(s),
  - invalid/fail path behavior,
  - mode behavior (`MONITOR` vs `STRICT`),
  - deterministic/idempotent behavior where applicable.
- Static token/import checks alone are insufficient for closure.

4. **CTRL-DELTA-04 Mutation + Property Strengthening**
- Strict mutation gate rerun passes:
  - `PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict`
- Control-threshold/state-machine property tests are added or strengthened based on step-1 gaps.
- Any survivors relevant to touched scope are documented with disposition.

5. **CTRL-DELTA-05 Replay + Failure Injection + Data Quality**
- Strict replay passes with zero drift:
  - `PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict`
- Controls-focused failure injection is added/expanded (timeout, invalid threshold payloads, stale-state/conflict behavior, connectivity failure).
- `PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict` remains pass.

6. **CTRL-DELTA-06 Architecture/Gate Closure + Defect Feedback**
- Architecture checks remain clean:
  - ownership,
  - transaction boundaries,
  - init hygiene.
- Full gatepack remains green (`16/16 PASS` minimum; if count changed, explain with evidence).
- Any discovered defect is linked to permanent guardrail artifacts (invariant/test/replay linkage), not patch-only.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| CTRL-DELTA-01 | Baseline | Build controls gap matrix and classify all control rows as REUSED/STRENGTHEN/MISSING | TODO | `backend/app/hoc/docs/architecture/usecases/CONTROLS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md` | Include operation-selection rationale |
| CTRL-DELTA-02 | Contracts | Add only missing controls invariants/contracts + tests, reusing BI-CTRL-001/SPEC-011 where already sufficient | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py`, `backend/tests/governance/t5/` | No duplicate invariant IDs |
| CTRL-DELTA-03 | Runtime Proof | Add in-process registry dispatch assertions for controls operations and mode behavior | TODO | `backend/tests/governance/t5/` | Real `OperationRegistry.execute` proof required |
| CTRL-DELTA-04 | Mutation/Property | Rerun strict mutation gate and add/strengthen controls property tests | TODO | `backend/reports/mutation_summary.json`, `backend/tests/property/` | Document survivors if any |
| CTRL-DELTA-05 | Replay/Failure/Data | Enforce strict replay + expand controls fault tests + keep data-quality strict green | TODO | `backend/tests/verification/`, `backend/tests/failure_injection/`, replay fixtures | Zero replay drift |
| CTRL-DELTA-06 | Closure | Rerun architecture + gatepack and populate return doc with complete evidence | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_CONTROLS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md` | Evidence-complete handoff |

## 6. Execution Order

1. CTRL-DELTA-01
2. CTRL-DELTA-02
3. CTRL-DELTA-03
4. CTRL-DELTA-04
5. CTRL-DELTA-05
6. CTRL-DELTA-06

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

# Controls delta runtime suite (new/expanded)
PYTHONPATH=. pytest -q tests/governance/t5/test_controls_runtime_delta.py

# Controls property proof (new or expanded)
PYTHONPATH=. pytest -q tests/property/test_controls_threshold_properties.py

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
- New controls invariants can over-block if runtime context contracts are incomplete.
- Replay fixture drift may appear when invariant linkage is corrected.
- Property/fault expansions may expose latent decision inconsistencies.

- Rollback plan:
- Revert only offending deltas while preserving evidence artifacts.
- Keep stricter behavior behind explicit mode/config toggles where needed.
- Convert rollback-triggering defects into permanent guardrails (invariant/tests/replay), never silent rollback.

## 9. Claude Fill Rules

1. Update each task status: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record exact evidence paths per task (files, commands, reports).
3. Mark each key control row as `PRESENT_REUSED`, `PRESENT_STRENGTHEN`, or `MISSING->ADDED`.
4. If blocked, include blocker, impact, and minimal next action.
5. Do not delete sections; append execution facts only.
6. Return completed results in `HOC_CONTROLS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`.
