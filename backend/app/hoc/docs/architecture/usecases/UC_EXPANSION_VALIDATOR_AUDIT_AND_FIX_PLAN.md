# UC Expansion Validator Audit and Fix Plan

- Date: 2026-02-12
- Scope: audit validator correctness vs reported claims for UC-018..UC-032 closure, define fix+retest plan.
- Related artifacts:
  - `app/hoc/docs/architecture/usecases/UC_EXPANSION_UC018_UC032_implemented.md`
  - `tests/governance/t4/test_uc018_uc032_expansion.py`
  - `scripts/ops/hoc_cross_domain_validator.py`

## 1) Validator Logic Audit (Source-Level)

File: `scripts/ops/hoc_cross_domain_validator.py`

Confirmed behavior:
1. Rule `E2` marks L6 cross-domain import as `HIGH` severity (`check_e2`, lines 191-214).
2. Exception for `E2` only allows `hoc_spine.schemas` imports (lines 203-205).
3. Process exits with code `1` when any finding exists (`sys.exit(1 if findings else 0)`, line 532).
4. There is no advisory severity type in this validator; only `HIGH` and `MEDIUM` are emitted by rule checks.

Conclusion:
- A reported `E2 HIGH` is not advisory by validator semantics.
- `violations=0` is incompatible with any emitted finding.

## 2) Claim Correctness Audit

Claimed in evidence artifact:
- `app/hoc/docs/architecture/usecases/UC_EXPANSION_UC018_UC032_implemented.md:53-57`
- Stated:
  - `violations=0`
  - "1 pre-existing advisory (sdk_attestation_driver.py E2 HIGH ...)"

Observed current reality:
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json` returns:
   - `status: VIOLATIONS`
   - `count: 1`
   - Finding: `E2 HIGH` at `app/hoc/cus/account/L6_drivers/sdk_attestation_driver.py:32`
2. Offending import:
   - `app/hoc/cus/account/L6_drivers/sdk_attestation_driver.py:32`
   - `from app.hoc.cus.hoc_spine.orchestrator.operation_registry import sql_text`

Audit verdict:
1. The gate claim is incorrect.
2. The issue is real and currently failing cross-domain gate.
3. The statement "advisory" is inaccurate for this validator.

## 3) Corrective Fix (Architecture-Safe)

Objective:
- Remove cross-domain L6 import from account driver without violating L2/L4/L5/L6 contracts.

Required code fix:
1. In `app/hoc/cus/account/L6_drivers/sdk_attestation_driver.py`, replace L4 import:
   - remove: `from app.hoc.cus.hoc_spine.orchestrator.operation_registry import sql_text`
   - use local L6-appropriate SQL text import:
     - `from sqlalchemy import text as sql_text`
2. Keep all transaction authority at L4 (no commit/rollback in driver).
3. Do not introduce any cross-domain imports in L6.

Why this is safe:
1. Driver remains L6 and DB-focused.
2. Eliminates forbidden cross-domain dependency.
3. Preserves existing query semantics and L4 transaction ownership.

## 4) Deterministic Retest Gate Pack (Post-Fix)

Run in `backend/`:

1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
   - Expected: `status: CLEAN`, `count: 0`, exit `0`.
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

Optional domain purity confirmation:
1. `PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain account --json --advisory`
2. `PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain logs --json --advisory`

## 5) Artifact Corrections Required

After fix and retest:
1. Update `app/hoc/docs/architecture/usecases/UC_EXPANSION_UC018_UC032_implemented.md`:
   - Correct Gate 3 block from `violations=0` + advisory note to actual validated post-fix output.
2. Add a short correction note:
   - prior mismatch found in cross-domain claim
   - fixed by removing cross-domain import from `sdk_attestation_driver.py`.
3. Record command outputs for all gates in the artifact.

## 6) Done Criteria

1. Cross-domain validator returns zero findings.
2. All deterministic gates pass.
3. Governance test file still passes fully.
4. Evidence artifact is corrected and internally consistent with gate outputs.
