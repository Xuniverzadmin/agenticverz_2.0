# PIN-598: Wave 2 Import Hygiene Batch 2 — API/Auth Stabilization

## Metadata
- Date: 2026-02-20
- Status: COMPLETE
- Scope: HOC-only (`backend/app/hoc/**`)
- Workstream: Legacy debt Wave 2 (import-hygiene batch 2)

## Why
After Wave 2 CUS stabilization (`PIN-597`), HOC import-hygiene debt remained at 30 files. Batch 2 targeted API/auth-adjacent files that affect frontend-consumed surfaces and auth boundary behavior.

## What Changed
### Import Hygiene Remediation (5 files)
1. `backend/app/hoc/api/cus/api_keys/embedding.py`
2. `backend/app/hoc/api/int/agent/agents.py`
3. `backend/app/hoc/int/agent/engines/onboarding_gate.py`
4. `backend/app/hoc/int/general/engines/role_guard.py`
5. `backend/app/hoc/int/general/engines/tier_gating.py`

### Capability Linkage
- Added file-level `capability_id` headers:
  - `CAP-014` (`embedding.py`)
  - `CAP-008` (`agents.py`)
  - `CAP-007` (`onboarding_gate.py`, `role_guard.py`, `tier_gating.py`)
- Synchronized evidence mapping in:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml`

### Evidence Artifacts Updated
1. `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_BATCH2_API_AUTH_STABILIZATION_2026-02-20.md`
2. `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
3. `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
4. `docs/architecture/frontend/CUS_FRONTEND_BACKEND_STABILITY_SYNC_WAVE2_2026-02-20.md`
5. `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`

## Verification
- HOC relative-import backlog:
  - `( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l` -> `25`
- Capability linkage gate on remediated files:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files ...` -> `✅ All checks passed`
- Syntax sanity:
  - `python3 -m py_compile` on all 5 remediated files -> pass

## Outcome
- HOC import-hygiene backlog reduced: `30 -> 25`
- CUS import-hygiene remains stable at `0` residual files
- Frontend-facing contracts remain stable (no route/payload contract changes in this batch)

## Open Residual
- Relative-import backlog still open: `25` files (primarily legacy `int/agent`, `int/logs`, `int/platform` clusters)
- Layer segregation (`--scope hoc`): `93` violations (separate debt lane)
