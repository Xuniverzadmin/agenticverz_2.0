# HOC Import Hygiene Wave 2 — CUS Stabilization (2026-02-20)

## Scope
Wave 2 remediation targeted `backend/app/hoc/cus/**` to stabilize CUS backend modules used by frontend slices while reducing import-hygiene debt under HOC-only governance scope.

## Backend Changes Applied
Converted relative imports (`from ..`) to canonical absolute imports (`from app.hoc...`) in:

1. `backend/app/hoc/cus/analytics/L5_engines/cost_snapshots_engine.py`
2. `backend/app/hoc/cus/analytics/L6_drivers/cost_snapshots_driver.py`
3. `backend/app/hoc/cus/integrations/L5_vault/engines/service.py`
4. `backend/app/hoc/cus/logs/L6_drivers/bridges_driver.py`

## Verification
### Command
```bash
rg -n "from \\.\\." backend/app/hoc/cus --glob '*.py' || true
```

### Result
- `backend/app/hoc/cus/**` relative import instances: `0`

### Command
```bash
( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l
```

### Result
- HOC relative-import backlog files: `30` (down from `34`)

### Command
```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  backend/app/hoc/cus/analytics/L5_engines/cost_snapshots_engine.py \
  backend/app/hoc/cus/analytics/L6_drivers/cost_snapshots_driver.py \
  backend/app/hoc/cus/integrations/L5_vault/engines/service.py \
  backend/app/hoc/cus/logs/L6_drivers/bridges_driver.py
```

### Result
- Capability-linkage gate for remediated files: `✅ All checks passed`

## Frontend Stability Impact
- No API route contract change introduced by this wave.
- PR-1 frontend slices (`runs-live`, `runs-completed`) remain aligned to current auth behavior (`401` unauthenticated, `200` authenticated context).
- Cross-reference frontend sync artifact:
  - `docs/architecture/frontend/CUS_FRONTEND_BACKEND_STABILITY_SYNC_WAVE2_2026-02-20.md`

## Outcome
Wave 2 CUS batch is closed for backend import hygiene. Remaining import-hygiene debt is now outside this CUS batch and tracked as residual HOC backlog.

Capability evidence mapping was synchronized in `docs/capabilities/CAPABILITY_REGISTRY.yaml` for:
- `CAP-002` (cost snapshot files)
- `CAP-018` (vault/bridges files)
