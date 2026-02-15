# UC Script Coverage Wave Taskpack (2026-02-12)

## Wave Order
1. Wave-1: `policies` + `logs`
2. Wave-2: `analytics` + `incidents`
3. Wave-3: `controls` + `account`
4. Wave-4: `hoc_spine`
5. Wave-5: `integrations` + `api_keys` + `overview` + `agent` + `apis` + `ops`

## Required Inputs
- `app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`
- `app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_GAP_UNLINKED_2026-02-12.txt`
- `app/hoc/docs/architecture/usecases/HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`
- `app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`

## Mandatory Deterministic Gates (Every Wave)
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

## Wave Acceptance Criteria
1. All deterministic gates pass.
2. Unlinked delta count decreases for wave scope.
3. New/expanded UC linkages include script references and evidence.
4. Any bug fix preserves HOC architecture constraints.
5. Domain literature and readiness tracker are updated.

## Claude Command: Wave-1 (policies + logs)
```bash
claude -p "In /root/agenticverz2.0/backend execute UC script coverage Wave-1 for policies+logs using app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv and app/hoc/docs/architecture/usecases/HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt. For each unlinked script in policies/logs classify as UC_LINKED, NON_UC_SUPPORT, or DEPRECATED with rationale; generate/expand UC sections in app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md with concrete file evidence; add or adjust tests for behavior gaps; fix only architecture-safe violations (L2->L4->L5->L6, no cross-domain L6 imports, no DB/ORM in L5). Run deterministic gates: cross-domain validator, layer boundaries, init hygiene --ci, pairing gap --json, uc_mon_validation --strict, pytest tests/governance/t4/test_uc018_uc032_expansion.py. Publish artifact app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_1_implemented.md with before/after counts, fixes, gate outputs, and residual gap list."
```

## Claude Command: Wave-2 (analytics + incidents)
```bash
claude -p "In /root/agenticverz2.0/backend execute UC script coverage Wave-2 for analytics+incidents following the same deterministic process and artifact format as Wave-1. Update HOC_USECASE_CODE_LINKAGE.md, relevant tests, and produce app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_implemented.md with before/after deltas and gate evidence."
```

## Claude Command: Wave-3 (controls + account)
```bash
claude -p "In /root/agenticverz2.0/backend execute UC script coverage Wave-3 for controls+account using app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv and app/hoc/docs/architecture/usecases/HOC_CUS_WAVE3_TARGET_UNLINKED_2026-02-12.txt (expected scope: controls=21, account=31, total=52). For each target script classify as UC_LINKED, NON_UC_SUPPORT, or DEPRECATED with rationale; expand HOC_USECASE_CODE_LINKAGE.md with concrete script evidence; add/update tests for behavior gaps; preserve architecture constraints (L2->L4->L5->L6, no L6 cross-domain imports, no DB/ORM in L5). Run deterministic gates: cross-domain validator, layer boundaries, init hygiene --ci, pairing gap --json, uc_mon_validation --strict, pytest tests/governance/t4/test_uc018_uc032_expansion.py. Publish app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_implemented.md with before/after counts and residual list."
```
