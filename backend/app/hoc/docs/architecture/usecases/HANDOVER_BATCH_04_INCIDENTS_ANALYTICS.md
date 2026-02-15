# HANDOVER_BATCH_04_INCIDENTS_ANALYTICS.md

## Objective
Close incident lifecycle and analytics reproducibility gaps.

## UC Scope
- `UC-007`, `UC-008`, `UC-011`, `UC-012`, `UC-016`

## Tasks
1. Implement incident resolution contract:
- required resolution payload
- state transition history
- postmortem stub artifact creation
2. Implement recurrence grouping:
- versioned recurrence signature
- deterministic group linking
3. Implement analytics reproducibility runtime wiring:
- persist `dataset_version`, `input_window_hash`, `compute_code_version`, `as_of`
- ensure derived metrics/anomalies reference artifact ids.
4. Emit required incident/analytics events per contract.

## Deliverables
1. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_04_INCIDENTS_ANALYTICS_implemented.md`
2. Evidence pack with sample incident and analytics lineage records.

## Validation Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

## Exit Criteria
1. Incident lifecycle and recurrence are fully auditable.
2. Analytics outputs are reproducible from persisted artifacts.
3. Determinism and authority constraints remain passing.
