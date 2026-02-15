# UC Script Coverage Wave-1 Audit (2026-02-12)

## Scope
- Audit the Wave-1 implementation claim for `policies + logs`.
- Re-run deterministic gates.
- Reconcile canonical coverage artifacts (classification + gap lists).

## Reality Check Summary
- `UC_SCRIPT_COVERAGE_WAVE_1_implemented.md` exists and reports:
  - 130 scripts classified in Wave-1 (`33 UC_LINKED + 97 NON_UC_SUPPORT`).
  - governance test expansion to `163` tests.
  - 6/6 architecture gates pass.
- `HOC_USECASE_CODE_LINKAGE.md` includes Wave-1 section and script evidence.
- `tests/governance/t4/test_uc018_uc032_expansion.py` includes `TestWave1ScriptCoverage`.

## Deterministic Re-Validation (Codex)
Commands run:
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

Results:
- Cross-domain: `CLEAN`, `count=0`
- Layer boundaries: `CLEAN`
- Init hygiene: `0 blocking violations`
- Pairing gap: `total_l5_engines=70`, `wired=70`, `orphaned=0`, `direct=0`
- UC-MON strict: `32 PASS`, `0 WARN`, `0 FAIL`
- Governance tests: `163 passed`

## Artifact Reconciliation Fix Applied
Issue found:
- Canonical classification CSV and unlinked gap lists were still at pre-Wave-1 baseline, despite Wave-1 evidence doc being present.

Fix applied:
- Updated `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv` for Wave-1 scope:
  - `policies`: `25 UC_LINKED`, `75 NON_UC_SUPPORT`
  - `logs`: `22 UC_LINKED`, `22 NON_UC_SUPPORT`
- Regenerated:
  - `HOC_CUS_SCRIPT_UC_GAP_UNLINKED_2026-02-12.txt`
  - `HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`

Post-fix counts (canonical):
- Total scripts: `573`
- `UC_LINKED`: `75`
- `NON_UC_SUPPORT`: `97`
- `UNLINKED` residual delta: `401`
- Core-6 residual delta (core-layer scope): `101`

## Notes on Residual Count Differences
- Residual counts in `UC_SCRIPT_COVERAGE_WAVE_1_implemented.md` use a different domain/scoping frame.
- Canonical backlog for program tracking must use the regenerated classification/gap artifacts above.

## Wave-1 Audit Verdict
- Claim is **substantially correct** (gates/tests/linkage evidence all validated).
- One documentation-data consistency defect was fixed (stale classification/gap artifacts).
- Final Wave-1 state is now deterministic and self-consistent.
