# Business Assurance Index (2026-02-16)

**Status:** ACTIVE
**Created:** 2026-02-16
**Purpose:** Master table of all business assurance workstreams, artifacts, and verification commands.

---

## Workstream Registry

| ID | Workstream | Artifact(s) | Command | Status |
|----|-----------|-------------|---------|--------|
| BA-01 | Setup | This file | N/A | DONE |
| BA-02 | Setup | `scripts/verification/run_business_assurance_gatepack.sh` | `bash scripts/verification/run_business_assurance_gatepack.sh` | DONE |
| BA-03 | Invariants | `app/hoc/cus/hoc_spine/authority/business_invariants.py` | N/A (library) | DONE |
| BA-04 | Invariants | `app/hoc/cus/hoc_spine/authority/invariant_evaluator.py` | N/A (library) | DONE |
| BA-05 | Invariants | `tests/governance/t5/test_business_invariants_runtime.py` | `PYTHONPATH=. pytest tests/governance/t5/test_business_invariants_runtime.py -v` | DONE |
| BA-06 | Spec Contracts | `app/hoc/docs/architecture/usecases/OPERATION_SPEC_REGISTRY_V1.md` | N/A (doc) | DONE |
| BA-07 | Spec Contracts | `scripts/verification/check_operation_specs.py` | `PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict` | DONE |
| BA-08 | Spec Contracts | `tests/governance/t5/test_operation_specs_enforced.py` | `PYTHONPATH=. pytest tests/governance/t5/test_operation_specs_enforced.py -v` | DONE |
| BA-09 | Mutation Testing | `pyproject.toml` (mutmut config) | N/A (config) | DONE |
| BA-10 | Mutation Testing | `scripts/verification/run_mutation_gate.py` | `PYTHONPATH=. python3 scripts/verification/run_mutation_gate.py --strict` | DONE |
| BA-11 | Mutation Testing | `scripts/verification/run_business_assurance_gatepack.sh` (mutation step) | `bash scripts/verification/run_business_assurance_gatepack.sh` | DONE |
| BA-12 | Property-Based | `tests/property/test_policies_threshold_properties.py` | `PYTHONPATH=. pytest tests/property/test_policies_threshold_properties.py -v` | DONE |
| BA-13 | Property-Based | `tests/property/test_lifecycle_state_machine_properties.py` | `PYTHONPATH=. pytest tests/property/test_lifecycle_state_machine_properties.py -v` | DONE |
| BA-14 | Differential Replay | `scripts/verification/replay_contract_schema.json` | N/A (schema) | DONE |
| BA-15 | Differential Replay | `scripts/verification/uc_differential_replay.py` | `PYTHONPATH=. python3 scripts/verification/uc_differential_replay.py --input tests/fixtures/replay/` | DONE |
| BA-16 | Differential Replay | `tests/fixtures/replay/` + `tests/verification/test_differential_replay.py` | `PYTHONPATH=. pytest tests/verification/test_differential_replay.py -v` | DONE |
| BA-17 | Data Quality Gates | `scripts/verification/check_schema_drift.py` | `PYTHONPATH=. python3 scripts/verification/check_schema_drift.py --strict` | DONE |
| BA-18 | Data Quality Gates | `scripts/verification/check_data_quality.py` | `PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict` | DONE |
| BA-19 | Data Quality Gates | `tests/verification/test_data_quality_gates.py` | `PYTHONPATH=. pytest tests/verification/test_data_quality_gates.py -v` | DONE |
| BA-20 | Fitness Functions | `scripts/ci/check_operation_ownership.py` | `PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py --strict` | DONE |
| BA-21 | Fitness Functions | `scripts/ci/check_transaction_boundaries.py` | `PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py --strict` | DONE |
| BA-22 | Failure Injection | `tests/failure_injection/test_driver_fault_safety.py` | `PYTHONPATH=. pytest tests/failure_injection/test_driver_fault_safety.py -v` | DONE |
| BA-23 | Failure Injection | `app/hoc/docs/architecture/usecases/FAILURE_INJECTION_MATRIX_V1.md` | N/A (doc) | DONE |
| BA-24 | Canary/Shadow | `app/hoc/cus/hoc_spine/authority/shadow_compare.py` | N/A (library) | DONE |
| BA-25 | Canary/Shadow | `app/hoc/docs/architecture/usecases/CANARY_SHADOW_ROLLOUT_CONTRACT_V1.md` | N/A (doc) | DONE |
| BA-26 | Defect Feedback | `app/hoc/docs/architecture/usecases/INCIDENT_GUARDRAIL_TEMPLATE.md` | N/A (doc) | DONE |
| BA-27 | Defect Feedback | `scripts/verification/check_incident_guardrail_linkage.py` | `PYTHONPATH=. python3 scripts/verification/check_incident_guardrail_linkage.py --strict` | DONE |
| BA-28 | Defect Feedback | `tests/governance/t5/test_incident_guardrail_linkage.py` | `PYTHONPATH=. pytest tests/governance/t5/test_incident_guardrail_linkage.py -v` | DONE |
| BA-29 | Documentation | This index + implementation evidence | N/A (doc) | DONE |
| BA-30 | Closure | `app/hoc/docs/architecture/usecases/BUSINESS_ASSURANCE_REALITY_AUDIT_2026-02-16.md` | `bash scripts/verification/run_business_assurance_gatepack.sh` | DONE |

## Verification Commands (Quick Reference)

```bash
cd /root/agenticverz2.0/backend

# Full gatepack (all assurance gates)
bash scripts/verification/run_business_assurance_gatepack.sh

# Individual gates
PYTHONPATH=. pytest tests/governance/t5/ -v
PYTHONPATH=. pytest tests/property/ -v
PYTHONPATH=. pytest tests/failure_injection/ -v
PYTHONPATH=. pytest tests/verification/ -v
PYTHONPATH=. python3 scripts/verification/check_operation_specs.py --strict
PYTHONPATH=. python3 scripts/verification/check_schema_drift.py --strict
PYTHONPATH=. python3 scripts/verification/check_data_quality.py --strict
PYTHONPATH=. python3 scripts/ci/check_operation_ownership.py --strict
PYTHONPATH=. python3 scripts/ci/check_transaction_boundaries.py --strict
PYTHONPATH=. python3 scripts/verification/check_incident_guardrail_linkage.py --strict
```

## Architecture Rules

- All invariants are pure Python (stdlib only) — no DB/ORM/framework imports
- Invariant evaluation is non-blocking by default, blocking via `--strict`
- All gates are deterministic and exit 0/1
- No new `*_service.py` in HOC
- hoc_spine remains single execution authority
