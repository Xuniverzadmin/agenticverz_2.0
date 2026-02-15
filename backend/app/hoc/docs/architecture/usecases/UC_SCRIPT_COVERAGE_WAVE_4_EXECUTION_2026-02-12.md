# UC Script Coverage Wave-4 Execution (2026-02-12)

## Scope
- Domains: `hoc_spine` + `integrations` + `agent` + `api_keys` + `apis` + `ops` + `overview`
- Canonical target source:
  - `app/hoc/docs/architecture/usecases/HOC_CUS_WAVE4_TARGET_UNLINKED_2026-02-12.txt`
- Expected target count:
  - `hoc_spine=78`
  - `integrations=48`
  - `api_keys=9`
  - `overview=5`
  - `agent=4`
  - `ops=4`
  - `apis=2`
  - `total=150`

## Objective
Classify all Wave-4 target scripts and reduce remaining core-layer residuals to zero for these domains.

## Claude Execute Command
```bash
claude -p "In /root/agenticverz2.0/backend execute UC script coverage Wave-4 for hoc_spine+integrations+agent+api_keys+apis+ops+overview using app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv and app/hoc/docs/architecture/usecases/HOC_CUS_WAVE4_TARGET_UNLINKED_2026-02-12.txt (expected scope total=150). For each target script classify as UC_LINKED, NON_UC_SUPPORT, or DEPRECATED with rationale; expand HOC_USECASE_CODE_LINKAGE.md with concrete script evidence; add/update tests for behavior gaps; preserve architecture constraints (L2->L4->L5->L6, no L6 cross-domain imports, no DB/ORM in L5). Run deterministic gates: cross-domain validator, layer boundaries, init hygiene --ci, pairing gap --json, uc_mon_validation --strict, pytest tests/governance/t4/test_uc018_uc032_expansion.py. Publish app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_implemented.md with before/after counts and residual list."
```
