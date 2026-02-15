# HANDOVER_BATCH_01_GOVERNANCE_BASELINE.md

## Objective
Establish strict, enforceable baseline for UC-MON execution and domain authority before feature closures.

## UC Scope
- Primary: `UC-003`..`UC-009`
- Foundation for: `UC-010`..`UC-017`

## Tasks
1. Lock domain authority rules in verifiers:
- proposals cannot mutate policy enforcement directly
- controls writes only via controls canonical paths
- incident lifecycle writes only via incidents canonical paths
2. Upgrade `uc_mon_validation.py` checks from advisory-to-eligible strict policy (no regressions).
3. Add/extend CI hygiene checks for new UC-MON boundaries in `scripts/ci/check_init_hygiene.py` (keep non-blocking until Batch-05 approval).
4. Ensure all UC-MON route mappings in `UC_MONITORING_ROUTE_OPERATION_MAP.md` remain current.

## Deliverables
1. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_01_GOVERNANCE_BASELINE_implemented.md`
2. Updated verifier outputs with PASS/WARN/FAIL summary.

## Validation Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_route_operation_map_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

## Exit Criteria
1. All commands pass with `0 FAIL`.
2. Strict mode returns exit `0`.
3. No new authority drift findings.
