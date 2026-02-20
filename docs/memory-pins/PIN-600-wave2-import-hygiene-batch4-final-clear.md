# PIN-600: Wave 2 Import Hygiene Batch 4 — Final Residual Clear

## Metadata
- Date: 2026-02-20
- Status: COMPLETE
- Scope: HOC-only (`backend/app/hoc/**`)
- Workstream: Legacy debt Wave 2 (import-hygiene final batch)

## Why
After Wave 2 batch 3, a small residual set of HOC `from ..` imports remained. Batch 4 closed this residual set to finish Wave 2 import hygiene for HOC scope.

## What Changed
### Import Hygiene Remediation (10 files)
1. `backend/app/hoc/int/analytics/engines/runner.py`
2. `backend/app/hoc/int/general/drivers/artifact.py`
3. `backend/app/hoc/int/logs/drivers/pool.py`
4. `backend/app/hoc/int/logs/engines/gateway_audit.py`
5. `backend/app/hoc/int/logs/engines/shadow_audit.py`
6. `backend/app/hoc/int/platform/drivers/care.py`
7. `backend/app/hoc/int/platform/drivers/memory_store.py`
8. `backend/app/hoc/int/platform/drivers/policies.py`
9. `backend/app/hoc/int/platform/drivers/probes.py`
10. `backend/app/hoc/int/policies/engines/rbac_middleware.py`

### Capability Linkage
- Added/confirmed `capability_id` linkage on remediated files:
  - `CAP-007`, `CAP-009`, `CAP-010`, `CAP-012`, `CAP-014`
- Synchronized capability evidence in:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml`

### Evidence Artifacts Updated
1. `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_BATCH4_REMAINING_CLUSTER_2026-02-20.md`
2. `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
3. `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
4. `docs/architecture/frontend/CUS_FRONTEND_BACKEND_STABILITY_SYNC_WAVE2_2026-02-20.md`
5. `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`

## Verification
- HOC relative-import backlog:
  - `( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l` -> `0`
- CUS relative-import backlog:
  - `( rg -n "from \\.\\." backend/app/hoc/cus --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l` -> `0`
- Capability linkage gate on changed files:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files ...` -> `✅ All checks passed`
- Syntax sanity:
  - `python3 -m py_compile ...` (10 files) -> `PASS`

## Outcome
- HOC import-hygiene backlog reduced: `10 -> 0`
- CUS import-hygiene remains stable: `0`
- Wave 2 import-hygiene objective is complete for HOC scope.

## Skeptical Audit Note
- Changed-file capability linkage gate is green for this remediation batch.
- A full `check-pr` sweep across all HOC python files reports `972` blocking `MISSING_CAPABILITY_ID` violations (plus `13` warnings) outside the changed-file CI contract; this remains a separate legacy workstream.

## Open Residual
- Layer segregation (`--scope hoc`): `93` violations (separate debt lane).
