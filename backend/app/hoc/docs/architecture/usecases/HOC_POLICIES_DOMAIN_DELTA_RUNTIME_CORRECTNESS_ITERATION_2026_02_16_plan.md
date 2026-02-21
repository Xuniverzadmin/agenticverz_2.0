# HOC_POLICIES_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan

**Created:** 2026-02-16 14:30:52 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION
**Parent references:**
- `backend/app/hoc/docs/architecture/usecases/HOC_BUSINESS_ASSURANCE_GUARDRAILS_EXECUTION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/BA_DELTA_RECONCILIATION_EXECUTION_2026_02_16.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_BUSINESS_ASSURANCE_NEXT_PHASE_SIX_STEP_EXECUTION_2026_02_16_plan_implemented.md`
- `docs/memory-pins/PIN-576-ba-n6-six-step-execution-audit-pass-2026-02-16.md`

## 1. Objective

- Primary outcome: execute a delta-only runtime correctness iteration for the `policies` domain with stronger in-process proof, without duplicating already-existing controls.
- Business/technical intent: shift from "tests are green" to "policy decision logic is defensibly correct under faults, drift, and replay" while preserving HOC architecture boundaries.

## 2. Scope

- In scope:
- Build a policies-domain gap matrix against existing invariant/spec/property/replay/failure/mutation coverage.
- Add only missing or weak runtime contracts and operation-level assertions.
- Strengthen in-process operation execution proofs (real registry dispatch + decision assertions, not static token checks).
- Expand fault, replay, and mutation evidence only where current protection is weak.
- Re-run deterministic governance gates and publish exact evidence links.

- Out of scope:
- Stage 2 real provider credentials and external environment dependencies.
- Cross-domain feature work outside `policies` (except shared guardrail infrastructure already in place).
- Refactors that alter HOC layer topology or ownership model.

## 3. Assumptions and Constraints

- Assumptions:
- BA baseline is already green (`16/16` gatepack, invariant wiring active, replay framework active).
- `policy.activate` and `policy.deactivate` specs already exist in the operation spec registry.
- `policy.activate` business invariant already exists (`BI-POLICY-001`), so delta work must avoid duplicate IDs.

- Constraints:
- Follow governance and topology: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7` only.
- Keep default runtime mode safe (`MONITOR`/non-blocking features default unless explicitly configured).
- All new assertions must be deterministic and CI-runnable.

- Non-negotiables:
- If an invariant/spec already exists, reuse it and add stronger proof; do not clone or rename equivalent controls.
- Every `DONE` task must include command evidence and file evidence.
- No "paper green": docs-only changes do not satisfy runtime-proof tasks.

## 4. Acceptance Criteria (Per Step)

1. **POL-DELTA-01 Baseline Gap Matrix**
- Artifact exists: `backend/app/hoc/docs/architecture/usecases/POLICIES_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md`.
- Matrix maps critical policies operations and lists coverage status per control type:
  - invariant contract,
  - operation spec,
  - in-process runtime assertion,
  - mutation resistance,
  - property-based checks,
  - differential replay,
  - failure injection.
- Every row is classified as one of: `PRESENT_REUSED`, `PRESENT_STRENGTHEN`, `MISSING` (no uncategorized rows).

2. **POL-DELTA-02 Runtime Contract Delta (No Duplication)**
- Existing invariants/specs are referenced and reused; duplicates are not introduced.
- Missing high-risk contract coverage is added (example: deactivation-side invariant if absent), with positive and negative tests.
- `PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict` passes.
- Policy invariant runtime tests include explicit fail-closed assertions for malformed/missing contract context.

3. **POL-DELTA-03 Deeper In-Process Execution Assertions**
- New/updated tests dispatch through real `OperationRegistry.execute(...)` on policy-related operations and assert:
  - decision outputs,
  - state transition correctness,
  - write/read side effects where applicable,
  - idempotency or deterministic repeatability.
- Static-only anchor checks are not counted toward completion for this step.
- Evidence includes direct pytest output for new runtime assertion suites.

4. **POL-DELTA-04 Mutation + Property Strengthening**
- Mutation gate executed in strict mode:
  - `PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict`
  - strict threshold met (or task marked `PARTIAL/BLOCKED` with survivor analysis).
- Property tests for policy thresholds/state transitions run green and include any gap-driven additions.
- Surviving mutants (if any) have documented disposition: fixed by tests/code or accepted with rationale.

5. **POL-DELTA-05 Differential Replay + Failure Injection + Data Quality**
- Replay validation for policy fixtures runs strict with zero drift:
  - `PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict`
- Failure injection tests cover policy fault scenarios (driver timeout/stale/missing data) with safe behavior assertions.
- `PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict` remains pass for modified scope.

6. **POL-DELTA-06 Architecture/Gate Closure + Defect Feedback**
- Architecture fitness checks remain clean for modified scope:
  - operation ownership,
  - transaction boundaries,
  - init hygiene.
- Full gatepack remains green (`16/16 PASS` minimum; if gate count changes, evidence must explain why).
- Any defect found during this run is linked into permanent guardrail artifacts (incident template + invariant/test linkage), not only patched.
- `*_plan_implemented.md` is fully populated with exact evidence paths and blocker disclosures.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| POL-DELTA-01 | Baseline | Build policies gap matrix and classify all critical control coverage as REUSED/STRENGTHEN/MISSING | TODO | `backend/app/hoc/docs/architecture/usecases/POLICIES_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md` | No uncategorized rows |
| POL-DELTA-02 | Contracts | Implement contract deltas only (reuse existing invariants/specs, add only missing coverage) + tests | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py`, `backend/tests/governance/t5/` | No duplicate invariant IDs |
| POL-DELTA-03 | Runtime Proof | Add deeper in-process execution assertions via real OperationRegistry dispatch for policies operations | TODO | `backend/tests/` (policy runtime suites) | Must assert behavior, not only imports/tokens |
| POL-DELTA-04 | Mutation/Property | Run strict mutation gate, strengthen policy property tests, resolve/document survivors | TODO | `backend/reports/mutation_summary.json`, `backend/tests/property/` | Strict threshold enforced |
| POL-DELTA-05 | Replay/Failure/Data | Run strict replay, add policy fault-injection proofs, keep data-quality strict pass | TODO | `backend/tests/verification/`, `backend/tests/failure_injection/` | Zero replay drift |
| POL-DELTA-06 | Closure | Re-run architecture + gatepack; link discovered defects to permanent guardrails; fill return doc | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_POLICIES_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md` | Evidence-complete handoff |

## 6. Execution Order

1. POL-DELTA-01
2. POL-DELTA-02
3. POL-DELTA-03
4. POL-DELTA-04
5. POL-DELTA-05
6. POL-DELTA-06

## 7. Verification Commands

```bash
cd /root/agenticverz2.0
scripts/ops/hoc_session_bootstrap.sh --strict

cd /root/agenticverz2.0/backend

# Baseline checks before edits
PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict
PYTHONPATH=. pytest -q tests/governance/t5/test_business_invariants_runtime.py tests/governance/t5/test_operation_specs_enforced.py
PYTHONPATH=. pytest -q tests/property/test_policies_threshold_properties.py
PYTHONPATH=. pytest -q tests/verification/test_differential_replay.py tests/failure_injection/test_driver_fault_safety.py

# Step POL-DELTA-04 mutation gate
PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict

# Step POL-DELTA-05 strict replay/data-quality
PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict
PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict

# Step POL-DELTA-06 closure gates
PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
cd /root/agenticverz2.0 && bash backend/scripts/verification/run_business_assurance_gatepack.sh
```

## 8. Risks and Rollback

- Risks:
- Mutation/failure/replay expansions may expose real policy defects and cause temporary CI churn.
- Over-aggressive invariant enforcement can block dispatch if context contracts are incomplete.
- Policy runtime assertions may reveal hidden nondeterminism in handlers.

- Rollback plan:
- Keep enforcement/behavioral hardening behind explicit configuration when feasible.
- If runtime regression appears, revert only the offending delta task commit while preserving evidence docs.
- Maintain a defect ledger entry for any rollback-triggering issue; do not drop findings silently.

## 9. Claude Fill Rules

1. Update each task status to `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record exact evidence paths (changed files, command logs, reports) per task.
3. If an invariant/spec already existed, explicitly mark it `PRESENT_REUSED` and show strengthened runtime proof instead of duplicate creation.
4. If blocked, include blocker reason, impact, and minimum next action.
5. Do not delete sections; append facts and keep this plan as the governing contract.
6. Return completed execution in `HOC_POLICIES_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`.
