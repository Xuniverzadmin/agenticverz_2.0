# PIN-562: Full-Scope UC Generation Across All hoc/cus Scripts (Including Waves)

**Status:** ✅ COMPLETE
**Created:** 2026-02-12
**Category:** Architecture / Usecase Governance

---

## Summary

Executed full-scope UC generation across all 573 hoc/cus scripts (including wave-covered). Produced deterministic proposal CSV with 176 KEEP_EXISTING_UC, 278 KEEP_NON_UC_SUPPORT, 31 RECLASSIFY_NON_UC_SUPPORT init files, and 88 NEW_UC_LINK mappings to proposed UC-033..UC-040; no manual-review rows remained. Registered artifacts and execution gates for Claude rollout.

---

## Details

### Why this PIN exists

Previous wave runs improved coverage but the ask was explicit: generate UC linkage from **full code reality**, including scripts already covered in waves, and produce a deterministic plan to turn additional script surfaces GREEN without force-fitting support files.

### Scope + Inputs

- Scope: `backend/app/hoc/cus/*` (all Python scripts in canonical classification)
- Baseline source:
  - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`
- Residual source:
  - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_GAP_UNLINKED_2026-02-12.txt`
- Existing UC linkage evidence:
  - `backend/tests/governance/t4/test_uc018_uc032_expansion.py`

### Baseline at execution time

- Total scripts: `573`
- `UC_LINKED`: `176`
- `NON_UC_SUPPORT`: `278`
- `UNLINKED`: `119`
- Of unlinked:
  - `31` were `__init__.py` package files
  - `88` were non-init behavioral/infrastructure files

### Deterministic generation method

1. Preserve existing mappings:
  - `UC_LINKED` -> `KEEP_EXISTING_UC`
  - `NON_UC_SUPPORT` -> `KEEP_NON_UC_SUPPORT`
2. Reclassify package init residuals:
  - `UNLINKED` `__init__.py` -> `RECLASSIFY_NON_UC_SUPPORT`
3. Cluster non-init residuals by architecture ownership and behavior:
  - `hoc_spine` operation/contracts/lifecycle/drivers/services
  - `integrations` vault + notifications + CLI
  - `account` CRM audit engine
4. Generate new UC candidates (`UC-033..UC-040`) and assign each residual non-init script to one candidate.
5. Remove ambiguity:
  - backfilled missing UC IDs for 29 existing `UC_LINKED` rows in proposal logic using deterministic mapping from governance test tuple anchors + explicit mapping table.
6. Enforce closure quality:
  - `manual_review_rows=0`
  - `uc_tbd_existing_rows=0`

### Full-scope result

- `KEEP_EXISTING_UC=176`
- `KEEP_NON_UC_SUPPORT=278`
- `RECLASSIFY_NON_UC_SUPPORT=31`
- `NEW_UC_LINK=88`

New UC candidate distribution:
- `UC-033=26`
- `UC-034=6`
- `UC-035=17`
- `UC-036=33`
- `UC-037=3`
- `UC-038=1`
- `UC-039=1`
- `UC-040=1`

### New UC intent map

- `UC-033`: spine operation governance + schema/contracts
- `UC-034`: spine lifecycle orchestration
- `UC-035`: spine execution safety + driver integrity
- `UC-036`: spine signals/evidence/alerting/compliance services
- `UC-037`: integrations secret vault lifecycle
- `UC-038`: integrations notification channel lifecycle
- `UC-039`: integrations CLI operational bootstrap
- `UC-040`: account CRM audit trail lifecycle

### Artifacts produced

- Proposal CSV:
  - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`
- Execution/audit narrative:
  - `backend/app/hoc/docs/architecture/usecases/UC_FULL_SCOPE_USECASE_GENERATION_2026-02-12.md`
- Registry synchronization:
  - `backend/app/hoc/docs/architecture/usecases/INDEX.md`
  - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_COVERAGE_AUDIT_2026-02-12.md`
  - `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_PROGRAM_2026-02-12.md`

### Deterministic gate contract for promoting UC-033..UC-040 to GREEN

Required on each promotion wave:
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

### Implementation notes

- This PIN does **not** claim all scripts are now GREEN by new UCs; it records deterministic generation and mapping artifacts required to execute that closure safely.
- Full-scope run intentionally included previously wave-covered scripts to avoid local optimizations and ensure global consistency.
