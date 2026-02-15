# HANDOVER_BATCH_05_GREEN_PROMOTION.md

## Objective
Run final hardening and promote eligible UC statuses to `GREEN`.

## UC Scope
- `UC-003`..`UC-017`

## Tasks
1. Add synthetic Scenario A/B parity tests (configured controls vs baseline path).
2. Add canonical evidence query checklist entries in linkage docs for each UC.
3. Run full regression suite:
- UC-MON verifiers
- UC-001/UC-002 regression verifier
- CI hygiene checks
4. Prepare status promotion proposal:
- list UCs with objective evidence
- list UCs blocked and exact remaining gap
5. Update docs only after verifiers/tests confirm closure:
- `INDEX.md`
- `HOC_USECASE_CODE_LINKAGE.md`

## Deliverables
1. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_05_GREEN_PROMOTION_implemented.md`
2. Final promotion table (`UC`, current, target, evidence refs, decision).

## Validation Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. python3 scripts/verification/uc_mon_route_operation_map_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
PYTHONPATH=. python3 scripts/verification/uc001_uc002_validation.py
```

## Exit Criteria
1. Promotion decisions are evidence-backed and reproducible.
2. No `GREEN` status is set without passing strict validation.
3. Remaining non-green UCs are blocked with explicit, auditable reasons.
