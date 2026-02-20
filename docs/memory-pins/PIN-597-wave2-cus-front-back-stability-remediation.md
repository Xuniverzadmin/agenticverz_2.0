# PIN-597: Wave 2 CUS Front+Back Stability Remediation

## Metadata
- Date: 2026-02-20
- Status: COMPLETE
- Scope: HOC-only remediation (`backend/app/hoc/**`)
- Workstream: Legacy debt Wave 2 (import-hygiene, CUS batch)

## Why
Wave 3 layer-segregation was intentionally deferred. Priority was shifted to stabilizing CUS runtime surfaces consumed by frontend slices and reducing immediate import-hygiene blockers under HOC scope.

## What Changed
### Backend (CUS)
Relative imports were replaced with canonical absolute imports in:
1. `backend/app/hoc/cus/analytics/L5_engines/cost_snapshots_engine.py`
2. `backend/app/hoc/cus/analytics/L6_drivers/cost_snapshots_driver.py`
3. `backend/app/hoc/cus/integrations/L5_vault/engines/service.py`
4. `backend/app/hoc/cus/logs/L6_drivers/bridges_driver.py`

### Governance/Evidence Docs
1. `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_CUS_STABILIZATION_2026-02-20.md` (new)
2. `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md` (Wave 2 progress)
3. `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md` (34 -> 30; CUS files removed from residual set)
4. `docs/capabilities/CAPABILITY_REGISTRY.yaml` (CAP-002/CAP-018 evidence linkage for remediated files)

### Frontend Sync
1. `docs/architecture/frontend/CUS_FRONTEND_BACKEND_STABILITY_SYNC_WAVE2_2026-02-20.md` (new)
2. `docs/architecture/frontend/slices/INDEX.md` (cross-link to Wave 2 sync record)

### Literature
1. `literature/hoc_domain/ops/SOFTWARE_BIBLE.md` (Wave 2 reality delta)

## Verification
- `rg -n "from \\.\\." backend/app/hoc/cus --glob '*.py' || true` -> no matches
- `( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l` -> `30`
- `python3 -m py_compile` on the 4 remediated files -> pass
- `python3 scripts/ops/capability_registry_enforcer.py check-pr --files ...` on the 4 remediated files -> `✅ All checks passed`

## Outcome
- CUS import-hygiene violations: `4 -> 0`
- HOC residual import-hygiene files: `34 -> 30`
- Frontend CUS slice contracts remained stable (no route/payload contract change in this wave)

## Remaining Open Debt
- Layer segregation (`backend/app/hoc/**`): still open (separate wave)
- Remaining HOC relative-import backlog: 30 files
