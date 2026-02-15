# UC Script Coverage Post-Execution Runbook (2026-02-12)

## Purpose
Codex post-execution audit workflow for step-3 and step-4 after each Claude wave.

## Step-3: Audit Execution Reality
Run and capture:
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

Recompute coverage deltas:
1. Refresh classification CSV.
2. Refresh unlinked gap lists.
3. Compare before/after counts by:
   - total scope
   - wave scope
   - domain
   - layer bucket

If failures exist:
- Patch only violating code/doc paths.
- Keep fixes architecture-safe and deterministic.
- Re-run gates until clean or report blockers with evidence.

## Step-4: Documentation and Readiness Updates
For domains touched in wave:
1. Update `HOC_USECASE_CODE_LINKAGE.md` with final evidence.
2. Update `INDEX.md` with new wave artifacts.
3. Update domain literature:
   - `literature/hoc_domain/<domain>/SOFTWARE_BIBLE.md`
   - `literature/hoc_domain/<domain>/<DOMAIN>_CANONICAL_SOFTWARE_LITERATURE.md`
4. Update `PROD_READINESS_TRACKER.md` notes for affected UC rows.
5. Publish wave audit summary artifact:
   - `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_<N>_audit.md`

## Wave Closure Acceptance
1. Deterministic gates all PASS.
2. No new architecture violations introduced.
3. Wave delta reduced (unlinked count strictly lower than pre-wave).
4. Literature and readiness docs are synchronized with final code reality.
