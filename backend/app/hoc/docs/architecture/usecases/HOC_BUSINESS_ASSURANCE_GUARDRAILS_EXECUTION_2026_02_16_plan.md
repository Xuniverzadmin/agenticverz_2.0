# HOC_BUSINESS_ASSURANCE_GUARDRAILS_EXECUTION_2026_02_16_plan

**Created:** 2026-02-16 04:37:36 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION

## 1. Objective

- Primary outcome: Implement a production-grade business assurance program that goes beyond wiring/trace evidence and continuously catches business-logic defects.
- Business/technical intent: enforce runtime invariants, spec contracts, mutation resistance, property guarantees, replay diffs, data-quality gates, architecture fitness rules, failure safety drills, canary/shadow rollout, and incident-to-guardrail feedback.

## 2. Scope

- In scope:
- HOC assurance framework and validation tooling under `/root/agenticverz2.0/backend`.
- Governance-safe additions to L4/L5/L6 verification scripts and tests.
- New assurance docs, checklists, scripts, and CI command targets.
- Deterministic artifacts proving each workstream is active and enforceable.

- Out of scope:
- Stage 2 real-provider credential rollout execution.
- Non-HOC product domains.
- Destructive refactors of existing runtime ownership.

## 3. Assumptions and Constraints

- Assumptions:
- Existing governance baseline remains authoritative (`L2.1 -> L2 -> L4 -> L5 -> L6 -> L7`).
- Existing UC docs and route-operation manifests are canonical sources.
- CI can run Python tools and pytest in backend workspace.

- Constraints:
- Do not break topology authority boundaries.
- No new `*_service.py` in HOC.
- Keep changes additive/minimal; do not delete legacy evidence docs.

- Non-negotiables:
- `hoc_spine` remains single execution authority.
- Engines decide; drivers perform effects.
- Any new gate must be deterministic and scriptable.

## 4. Acceptance Criteria

1. Runtime business invariants are codified, executable, and enforced in CI.
2. Critical operations have explicit spec contracts: preconditions, postconditions, forbidden states.
3. Mutation testing runs against selected L5 engines with baseline threshold and fail-on-regression rule.
4. Property-based tests exist for policy/threshold/state-machine behavior and pass.
5. Differential replay script compares baseline vs candidate decisions and reports drift deterministically.
6. Data-quality gates check schema/nullability/cardinality/semantic drift and fail on violations.
7. Architecture fitness functions include operation ownership + transaction boundary checks.
8. Failure-injection drills validate safe behavior for driver faults/timeouts/stale reads.
9. Canary + shadow execution mode exists for selected risky operations and emits comparability evidence.
10. Incident feedback loop requires each incident to produce a guardrail/invariant artifact.
11. All new scripts/tests documented with exact commands and output evidence paths.
12. Deterministic gate pack exits zero in local run (except explicitly deferred items with reason).

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| BA-01 | Setup | Create assurance index doc and link all new artifacts | TODO | `backend/app/hoc/docs/architecture/usecases/BUSINESS_ASSURANCE_INDEX_2026-02-16.md` | Master table of workstreams, files, commands |
| BA-02 | Setup | Add CI entrypoint script for full assurance gate pack | TODO | `backend/scripts/verification/run_business_assurance_gatepack.sh` | Deterministic sequence with fail-fast |
| BA-03 | Invariants | Define runtime invariant model + schema (operation, invariant_id, severity, condition, remediation) | TODO | `backend/app/hoc/cus/hoc_spine/authority/business_invariants.py` | Keep layer-safe, no DB logic in invariant predicates |
| BA-04 | Invariants | Implement invariant evaluation hook for selected critical operations | TODO | `backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py` (or dedicated validator module) | Non-blocking mode + blocking mode by config |
| BA-05 | Invariants | Add invariant test suite (positive/negative) | TODO | `backend/tests/governance/t5/test_business_invariants_runtime.py` | Include deterministic fixtures |
| BA-06 | Spec Contracts | Create operation spec registry format and canonical spec doc | TODO | `backend/app/hoc/docs/architecture/usecases/OPERATION_SPEC_REGISTRY_V1.md` | Each spec includes pre/post/forbidden |
| BA-07 | Spec Contracts | Implement static checker: every critical op has complete spec fields | TODO | `backend/scripts/verification/check_operation_specs.py` | Fails on missing fields or invalid states |
| BA-08 | Spec Contracts | Implement runtime checker binding operation result to postconditions | TODO | `backend/tests/governance/t5/test_operation_specs_enforced.py` | Assert forbidden states unreachable |
| BA-09 | Mutation Testing | Add mutation tool config and scope (targeted L5 engines only) | TODO | `backend/pyproject.toml` and/or `backend/.mutmut-config` | Scope: policies, controls, incidents, logs engines |
| BA-10 | Mutation Testing | Add mutation runner + threshold policy script | TODO | `backend/scripts/verification/run_mutation_gate.py` | Output score JSON + markdown summary |
| BA-11 | Mutation Testing | Add CI gate for mutation regression | TODO | `backend/scripts/verification/run_business_assurance_gatepack.sh` | Baseline threshold + delta threshold |
| BA-12 | Property-Based | Add Hypothesis-based tests for threshold monotonicity and policy conflict resolution | TODO | `backend/tests/property/test_policies_threshold_properties.py` | Include shrinking-friendly assertions |
| BA-13 | Property-Based | Add state-machine property tests for onboarding/incidents lifecycle transitions | TODO | `backend/tests/property/test_lifecycle_state_machine_properties.py` | Validate forbidden transitions |
| BA-14 | Differential Replay | Define replay input contract for captured traces/decisions | TODO | `backend/scripts/verification/replay_contract_schema.json` | Deterministic schema |
| BA-15 | Differential Replay | Implement replay-diff runner comparing baseline commit vs current decision outputs | TODO | `backend/scripts/verification/uc_differential_replay.py` | Produces diff report with severity |
| BA-16 | Differential Replay | Add replay fixtures and golden expectations | TODO | `backend/tests/fixtures/replay/` + `backend/tests/verification/test_differential_replay.py` | Must include no-drift case |
| BA-17 | Data Quality Gates | Implement schema drift gate (model vs DB introspection source) | TODO | `backend/scripts/verification/check_schema_drift.py` | Deterministic report |
| BA-18 | Data Quality Gates | Implement nullability/cardinality/semantic drift checks | TODO | `backend/scripts/verification/check_data_quality.py` | Contract-driven assertions |
| BA-19 | Data Quality Gates | Add tests for drift gate behavior | TODO | `backend/tests/verification/test_data_quality_gates.py` | Includes fail fixtures |
| BA-20 | Fitness Functions | Extend architecture gate: operation ownership map and boundary checks | TODO | `backend/scripts/ci/check_operation_ownership.py` | Operation->domain owner uniqueness |
| BA-21 | Fitness Functions | Add transaction-boundary validator (L4 owns commit/rollback) | TODO | `backend/scripts/ci/check_transaction_boundaries.py` | Detect forbidden commit in L6/L5 |
| BA-22 | Failure Injection | Add deterministic fault injection harness for driver exceptions/timeouts/stale reads | TODO | `backend/tests/failure_injection/test_driver_fault_safety.py` | Assert safe fallback decisions |
| BA-23 | Failure Injection | Add scenario matrix and expected safety outcomes doc | TODO | `backend/app/hoc/docs/architecture/usecases/FAILURE_INJECTION_MATRIX_V1.md` | Map scenario->expected behavior |
| BA-24 | Canary/Shadow | Add shadow decision comparator for selected risky operations | TODO | `backend/app/hoc/cus/hoc_spine/authority/shadow_compare.py` | Current vs candidate decision diff |
| BA-25 | Canary/Shadow | Add canary policy config + staged rollout contract | TODO | `backend/app/hoc/docs/architecture/usecases/CANARY_SHADOW_ROLLOUT_CONTRACT_V1.md` | Percentage + auto-rollback triggers |
| BA-26 | Defect Feedback | Define incident->guardrail template and mandatory fields | TODO | `backend/app/hoc/docs/architecture/usecases/INCIDENT_GUARDRAIL_TEMPLATE.md` | incident_id, invariant, test, owner |
| BA-27 | Defect Feedback | Implement validation script: incidents must map to new/updated invariant | TODO | `backend/scripts/verification/check_incident_guardrail_linkage.py` | Fail if missing linkage |
| BA-28 | Defect Feedback | Add governance test enforcing linkage rule | TODO | `backend/tests/governance/t5/test_incident_guardrail_linkage.py` | Deterministic fixture set |
| BA-29 | Documentation | Publish consolidated execution evidence + reality audit | TODO | `backend/app/hoc/docs/architecture/usecases/BUSINESS_ASSURANCE_IMPLEMENTED_2026-02-16.md` | Include command output excerpts |
| BA-30 | Closure | Run full assurance + existing governance packs and record pass/fail | TODO | `backend/app/hoc/docs/architecture/usecases/BUSINESS_ASSURANCE_REALITY_AUDIT_2026-02-16.md` | Explicit blockers and next actions |

## 6. Execution Order

1. BA-01, BA-02
2. BA-03, BA-04, BA-05
3. BA-06, BA-07, BA-08
4. BA-09, BA-10, BA-11
5. BA-12, BA-13
6. BA-14, BA-15, BA-16
7. BA-17, BA-18, BA-19
8. BA-20, BA-21
9. BA-22, BA-23
10. BA-24, BA-25
11. BA-26, BA-27, BA-28
12. BA-29, BA-30

## 7. Verification Commands

```bash
cd /root/agenticverz2.0/backend

# Existing governance baseline (must stay green)
PYTHONPATH=. python3 scripts/verification/uc_operation_manifest_check.py --strict
PYTHONPATH=. pytest -q tests/governance/t4/test_uc_mapping_decision_table.py tests/governance/t4/test_uc_operation_manifest_integrity.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci

# New assurance checks (to be implemented by this plan)
PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict
PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict
PYTHONPATH=. pytest -q tests/property/
PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --baseline-ref <base_sha> --candidate-ref HEAD --input tests/fixtures/replay/
PYTHONPATH=. python3 scripts/verification/check_schema_drift.py --strict
PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict
PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py --strict
PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py --strict
PYTHONPATH=. pytest -q tests/failure_injection/
PYTHONPATH=. python3 scripts/verification/check_incident_guardrail_linkage.py --strict

# Unified gatepack
bash scripts/verification/run_business_assurance_gatepack.sh
```

## 8. Risks and Rollback

- Risks:
- Mutation/property tests may increase CI duration and flakiness if not bounded.
- Replay diff may produce noisy mismatches without stable normalization.
- Overly strict invariants can block legitimate operations.

- Rollback plan:
- Gate new checks behind explicit `--strict` switch and CI job feature flag initially.
- Introduce monitor-only mode for runtime invariant evaluation before hard-block mode.
- Keep all new assurance modules additive; revert by removing new CI entrypoint and modules if necessary.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. If blocked, include blocker reason and minimal next action.
4. Do not delete plan sections; append execution facts.
5. Return completed results in `HOC_BUSINESS_ASSURANCE_GUARDRAILS_EXECUTION_2026_02_16_plan_implemented.md`.
6. Keep architecture invariants intact (no L2->L5/L6 direct calls, no new `*_service.py` in HOC).
7. Include exact command outputs for every gate in section 3 of implemented file.
