# HOC Layer + Capability Remediation Wave 1 — Implemented (2026-02-20)

## Scope
- HOC only (`backend/app/hoc/**`)
- Wave 1 target: largest layer-segregation hotspot in `backend/app/hoc/int/agent/engines/*`

## Changes Implemented
Replaced DB-heavy engine implementations with compatibility wrappers delegating to canonical service/driver modules:

1. `backend/app/hoc/int/agent/engines/job_engine.py` -> `app.agents.services.job_service`
2. `backend/app/hoc/int/agent/engines/worker_engine.py` -> `app.agents.services.worker_service`
3. `backend/app/hoc/int/agent/engines/credit_engine.py` -> `app.agents.services.credit_service`
4. `backend/app/hoc/int/agent/engines/message_engine.py` -> `app.agents.services.message_service`
5. `backend/app/hoc/int/agent/engines/registry_engine.py` -> `app.agents.services.registry_service`
6. `backend/app/hoc/int/agent/engines/governance_engine.py` -> `app.agents.services.governance_service`
7. `backend/app/hoc/int/agent/engines/invoke_audit_engine.py` -> wrapper alias over `app.agents.services.invoke_audit_driver` (`InvokeAuditService` compatibility preserved)

All remediated files now carry `capability_id: CAP-008`.

## Capability Evidence Sync
Updated `docs/capabilities/CAPABILITY_REGISTRY.yaml` (`CAP-008` evidence list) to include the 7 remediated HOC engine files.

## Re-Audit Results
### Layer Segregation (`--scope hoc`)
- Before: `93` violation instances (15 files)
- After: `14` violation instances (8 files)
- Delta: `-79` violations

Residual layer files:
1. `backend/app/hoc/fdr/ops/engines/founder_action_write_engine.py` (2)
2. `backend/app/hoc/fdr/ops/engines/ops_incident_engine.py` (2)
3. `backend/app/hoc/fdr/account/engines/explorer_engine.py` (2)
4. `backend/app/hoc/fdr/logs/engines/timeline_engine.py` (2)
5. `backend/app/hoc/fdr/logs/engines/review_engine.py` (2)
6. `backend/app/hoc/fdr/incidents/engines/ops_incident_engine.py` (2)
7. `backend/app/hoc/int/platform/engines/sandbox_engine.py` (1)
8. `backend/app/hoc/int/platform/drivers/memory_driver.py` (1)

### Full HOC Capability Sweep
- Before: `972` blocking + `13` warnings
- After: `965` blocking + `13` warnings
- Delta: `-7` blockers (the 7 remediated engine files)

### Import Hygiene Guard
- `HOC_REL_FILES=0`
- `CUS_REL_FILES=0`
- No regressions introduced.

## Verification Commands
```bash
python3 -m py_compile \
  backend/app/hoc/int/agent/engines/job_engine.py \
  backend/app/hoc/int/agent/engines/worker_engine.py \
  backend/app/hoc/int/agent/engines/credit_engine.py \
  backend/app/hoc/int/agent/engines/message_engine.py \
  backend/app/hoc/int/agent/engines/registry_engine.py \
  backend/app/hoc/int/agent/engines/governance_engine.py \
  backend/app/hoc/int/agent/engines/invoke_audit_engine.py

python3 scripts/ops/layer_segregation_guard.py --check --scope hoc

FILES=$(git ls-files 'backend/app/hoc/**/*.py')
python3 scripts/ops/capability_registry_enforcer.py check-pr --files $FILES
```

## Next Wave
- Wave 2 should clear the remaining 14 layer violations by extracting DB access from the 7 founder/platform files and removing `severity` policy logic from `memory_driver.py`.
