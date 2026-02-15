# UC Script Coverage Wave-2 Audit (2026-02-12)

## Scope
- Audit Wave-2 implementation claim for `analytics + incidents + activity`.
- Re-run deterministic gates.
- Reconcile canonical coverage artifacts (classification + gap lists).

## Reality Check Summary
- `UC_SCRIPT_COVERAGE_WAVE_2_implemented.md` exists and reports:
  - `80` scripts classified in Wave-2 (`35 UC_LINKED + 45 NON_UC_SUPPORT`).
  - governance test expansion to `219` tests.
  - 6/6 architecture gates pass.
- `HOC_USECASE_CODE_LINKAGE.md` contains Wave-2 coverage section.
- `tests/governance/t4/test_uc018_uc032_expansion.py` contains `TestWave2ScriptCoverage`.

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
- Governance tests: `219 passed`

## Artifact Reconciliation Fix Applied
Issue found:
- Canonical classification CSV and unlinked gap lists still reflected post-Wave-1 state (not Wave-2), despite Wave-2 evidence doc and tests being present.

Fix applied:
- Updated `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv` for Wave-2 scope:
  - `activity`: `7 UC_LINKED`, `13 NON_UC_SUPPORT` in core scope (plus `1` non-core residual)
  - `analytics`: `22 UC_LINKED`, `19 NON_UC_SUPPORT` in core scope (plus `1` non-core residual)
  - `incidents`: `24 UC_LINKED`, `13 NON_UC_SUPPORT` in core scope (plus `1` non-core residual)
- Regenerated:
  - `HOC_CUS_SCRIPT_UC_GAP_UNLINKED_2026-02-12.txt`
  - `HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`

Post-fix counts (canonical):
- Total scripts: `573`
- `UC_LINKED`: `110`
- `NON_UC_SUPPORT`: `142`
- `UNLINKED` residual delta: `321`
- Core-6 residual delta (core-layer scope): `21` (controls only)

## Notes on Scope Alignment
- Wave-2 implementation counts are correct for the Wave-2 target scope (`80` core scripts).
- Canonical all-script inventory also includes one non-core residual (`layer_bucket=OTHER`) in each of:
  - `activity`
  - `analytics`
  - `incidents`
- Those three non-core files are intentionally outside Wave-2 core scope and remain in global residual.

## Wave-2 Audit Verdict
- Claim is **substantially correct** (gates/tests/linkage evidence all validated).
- One documentation-data consistency defect was fixed (stale classification/gap artifacts).
- Final Wave-2 state is now deterministic and self-consistent for program tracking.
