# HANDOVER_BATCH_03_CONTROLS_POLICIES.md

## Objective
Close controls/policies authority and lifecycle gaps, including proposal acceptance boundary and override lifecycle.

## UC Scope
- `UC-004`, `UC-005`, `UC-009`, `UC-013`, `UC-014`, `UC-015`

## Tasks
1. Implement policy proposal canonical accept flow:
- proposal read/validate
- compile/version/create/activate through canonical policy path only
- enforce hard boundary: proposal generation never mutates enforcement
2. Implement controls override lifecycle:
- request, approve, reject, cancel, expire
- actor lineage and reasons required
3. Enforce per-run control binding fields in evaluation evidence:
- `control_set_version`
- `override_ids_applied[]`
- `resolver_version`
4. Emit required controls/policies events per contract.

## Deliverables
1. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_03_CONTROLS_POLICIES_implemented.md`
2. Authority boundary proof (grep/query evidence) showing no non-canonical mutation path.

## Validation Commands
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

## Exit Criteria
1. Proposal -> enforcement authority is strictly canonical.
2. Override lifecycle is complete and auditable.
3. Controls evaluation evidence always carries version binding fields.
