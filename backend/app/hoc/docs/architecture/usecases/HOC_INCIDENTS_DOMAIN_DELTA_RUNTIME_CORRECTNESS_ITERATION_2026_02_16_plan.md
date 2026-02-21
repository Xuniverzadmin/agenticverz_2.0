# HOC_INCIDENTS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan

**Created:** 2026-02-16 15:27:26 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION
**Parent references:**
- `backend/app/hoc/docs/architecture/usecases/HOC_POLICIES_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_BUSINESS_ASSURANCE_NEXT_PHASE_SIX_STEP_EXECUTION_2026_02_16_plan_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/BA_DELTA_RECONCILIATION_EXECUTION_2026_02_16.md`
- `docs/memory-pins/PIN-576-ba-n6-six-step-execution-audit-pass-2026-02-16.md`

## 1. Objective

- Primary outcome: execute a delta-only runtime correctness iteration for the `incidents` domain, adding only missing high-value controls and stronger in-process execution proof.
- Business/technical intent: improve confidence that incident lifecycle decisions (create/resolve) remain safe, deterministic, and architecture-compliant under failure and replay.

## 2. Scope

- In scope:
- Build incidents-domain gap matrix against existing controls (invariants/specs/runtime/property/replay/failure/mutation).
- Add only missing exact runtime contracts for incident operations and strengthen existing controls without duplication.
- Add deeper `OperationRegistry.execute(...)` assertions for incident operations (behavior, mode escalation, deterministic outcomes).
- Expand incident-focused failure-injection coverage and verify replay/data-quality/fitness gates remain green.

- Out of scope:
- Stage 2 real provider credentials and external environment dependencies.
- Broad refactors outside incidents domain and shared assurance infrastructure.
- Any HOC topology/authority model change.

## 3. Assumptions and Constraints

- Assumptions:
- `SPEC-012 incident.create` and `SPEC-013 incident.resolve` already exist in spec registry.
- `BI-INCIDENT-001` already exists for `incident.transition`; exact invariants for `incident.create`/`incident.resolve` are currently missing.
- Differential replay fixtures for incidents already exist (`REPLAY-002`, `REPLAY-013`).

- Constraints:
- Preserve HOC layering: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7` only.
- Keep runtime-safe defaults unless explicitly configured otherwise.
- All additions must be deterministic and CI-runnable.

- Non-negotiables:
- If a contract already exists, mark `PRESENT_REUSED` and strengthen proof rather than duplicating.
- Every `DONE` requires command evidence + file evidence.
- No doc-only completion for runtime-proof tasks.

## 4. Acceptance Criteria (Per Step)

1. **INC-DELTA-01 Baseline Gap Matrix**
- Artifact exists: `backend/app/hoc/docs/architecture/usecases/INCIDENTS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md`.
- Matrix covers at least `incident.create`, `incident.resolve`, `incident.transition`.
- Every control row is classified as `PRESENT_REUSED`, `PRESENT_STRENGTHEN`, or `MISSING` (no uncategorized items).

2. **INC-DELTA-02 Runtime Contract Delta (No Duplication)**
- Existing contracts are reused (`BI-INCIDENT-001`, `SPEC-012`, `SPEC-013`).
- Missing exact invariants for incident lifecycle ops are added (expected: create/resolve contract coverage) with positive and negative tests.
- `PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict` passes.

3. **INC-DELTA-03 Deeper In-Process Execution Assertions**
- New tests dispatch through real `OperationRegistry.execute(...)` and assert incident behavior:
  - successful create/resolve path,
  - blocked/invalid path,
  - mode behavior (`MONITOR` vs `STRICT`) for new incident invariants,
  - deterministic repeatability/idempotency checks where applicable.
- Evidence is runtime assertions (not static anchor-only checks).

4. **INC-DELTA-04 Mutation + Property Strengthening**
- Strict mutation gate rerun passes:
  - `PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict`
- Incident lifecycle property tests pass and include gap-driven strengthening if needed.
- Any surviving mutants relevant to incident logic are documented with disposition.

5. **INC-DELTA-05 Replay + Failure Injection + Data Quality**
- Strict differential replay passes with zero drift:
  - `PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict`
- Incident-focused failure injection tests added/expanded (timeouts, stale data, invalid resolution, conflict paths).
- Data quality strict remains pass for modified scope.

6. **INC-DELTA-06 Architecture/Gate Closure + Defect Feedback**
- Architecture checks remain clean:
  - ownership,
  - transaction boundaries,
  - init hygiene.
- Full gatepack remains green (minimum `16/16 PASS`, or explain gate-count change).
- Any defect discovered is linked into permanent invariant/test guardrails and recorded in return doc.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| INC-DELTA-01 | Baseline | Build incidents gap matrix and classify all control rows as REUSED/STRENGTHEN/MISSING | TODO | `backend/app/hoc/docs/architecture/usecases/INCIDENTS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md` | Include create/resolve/transition rows |
| INC-DELTA-02 | Contracts | Add missing exact incident invariants (delta only) + runtime contract tests | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py`, `backend/tests/governance/t5/` | No duplicate IDs |
| INC-DELTA-03 | Runtime Proof | Add in-process registry dispatch assertions for incident operations and mode behavior | TODO | `backend/tests/governance/t5/` | Real `OperationRegistry.execute` calls |
| INC-DELTA-04 | Mutation/Property | Rerun strict mutation gate + strengthen incident lifecycle property proofs | TODO | `backend/reports/mutation_summary.json`, `backend/tests/property/` | Record survivor disposition |
| INC-DELTA-05 | Replay/Failure/Data | Enforce strict replay + expand incident fault-injection + keep data quality strict pass | TODO | `backend/tests/verification/`, `backend/tests/failure_injection/` | Zero replay drift |
| INC-DELTA-06 | Closure | Re-run architecture and gatepack; populate return doc with evidence/blockers/deviations | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_INCIDENTS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md` | Evidence complete |

## 6. Execution Order

1. INC-DELTA-01
2. INC-DELTA-02
3. INC-DELTA-03
4. INC-DELTA-04
5. INC-DELTA-05
6. INC-DELTA-06

## 7. Verification Commands

```bash
cd /root/agenticverz2.0
scripts/ops/hoc_session_bootstrap.sh --strict

cd /root/agenticverz2.0/backend

# Baseline checks
PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict
PYTHONPATH=. pytest -q tests/governance/t5/test_business_invariants_runtime.py
PYTHONPATH=. pytest -q tests/property/test_lifecycle_state_machine_properties.py
PYTHONPATH=. pytest -q tests/verification/test_differential_replay.py
PYTHONPATH=. pytest -q tests/failure_injection/test_driver_fault_safety.py

# Incident delta runtime contract + dispatch proof (new/expanded suite)
PYTHONPATH=. pytest -q tests/governance/t5/test_incidents_runtime_delta.py

# Mutation gate strict
PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict

# Replay/data quality strict
PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay --strict
PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict

# Architecture + full closure
PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py
PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
cd /root/agenticverz2.0 && bash backend/scripts/verification/run_business_assurance_gatepack.sh
```

## 8. Risks and Rollback

- Risks:
- Incident invariants may over-block if context contracts are underspecified.
- Expanded failure-path tests may expose latent incident workflow bugs.
- Mutation/property strengthening may increase CI runtime and flakiness if nondeterminism leaks in.

- Rollback plan:
- Revert only the offending delta task changes, keep artifacts and findings.
- Keep stricter behavior behind explicit config if production impact appears.
- Convert any rollback-triggering defect into permanent guardrail follow-up.

## 9. Claude Fill Rules

1. Update each task status: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record exact evidence paths per task (files, commands, reports).
3. Explicitly tag each key control as `PRESENT_REUSED`, `PRESENT_STRENGTHEN`, or `MISSING->ADDED`.
4. If blocked, include blocker, impact, and minimum next action.
5. Do not delete sections; append execution facts only.
6. Return completed results in `HOC_INCIDENTS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan_implemented.md`.
