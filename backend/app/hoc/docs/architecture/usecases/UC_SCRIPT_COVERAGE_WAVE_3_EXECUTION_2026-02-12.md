# UC Script Coverage Wave-3 Execution (2026-02-12)

## Scope
- Domains: `controls` + `account`
- Canonical target source:
  - `app/hoc/docs/architecture/usecases/HOC_CUS_WAVE3_TARGET_UNLINKED_2026-02-12.txt`
- Expected target count:
  - `controls=21`
  - `account=31`
  - `total=52`

## Objective
Classify all Wave-3 target scripts and reduce Wave-3 residual unlinked core scripts to zero for these domains.

## Claude Execute Command
```bash
claude -p "In /root/agenticverz2.0/backend execute UC script coverage Wave-3 for controls+account using app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv and app/hoc/docs/architecture/usecases/HOC_CUS_WAVE3_TARGET_UNLINKED_2026-02-12.txt (expected scope: controls=21, account=31, total=52). For each target script classify as UC_LINKED, NON_UC_SUPPORT, or DEPRECATED with rationale; expand HOC_USECASE_CODE_LINKAGE.md with concrete script evidence; add/update tests for behavior gaps; preserve architecture constraints (L2->L4->L5->L6, no L6 cross-domain imports, no DB/ORM in L5). Run deterministic gates: cross-domain validator, layer boundaries, init hygiene --ci, pairing gap --json, uc_mon_validation --strict, pytest tests/governance/t4/test_uc018_uc032_expansion.py. Publish app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_implemented.md with before/after counts and residual list."
```

## Mandatory Deterministic Gates
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

## Wave-3 Acceptance Criteria
1. All six deterministic gates pass.
2. Wave-3 target scripts are fully classified (`0` unclassified in target scope).
3. `controls` and `account` target residuals are reduced to `0` for Wave-3 core scope.
4. `HOC_USECASE_CODE_LINKAGE.md` contains Wave-3 evidence section.
5. Tests added/updated for newly linked scripts and pass in governance suite.
6. Final results are documented in `UC_SCRIPT_COVERAGE_WAVE_3_implemented.md`.
