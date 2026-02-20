# HOC Import Hygiene Wave 2 — Batch 2 API/Auth Stabilization (2026-02-20)

## Scope
Wave 2 batch 2 targeted HOC API/auth-adjacent files to reduce relative-import debt while preserving runtime behavior.

## Backend Changes Applied
Converted relative imports (`from ..`) to canonical absolute imports (`from app...`) in:

1. `backend/app/hoc/api/cus/api_keys/embedding.py`
2. `backend/app/hoc/api/int/agent/agents.py`
3. `backend/app/hoc/int/agent/engines/onboarding_gate.py`
4. `backend/app/hoc/int/general/engines/role_guard.py`
5. `backend/app/hoc/int/general/engines/tier_gating.py`

Also added capability linkage headers:
- `CAP-014` on embedding API file
- `CAP-008` on internal agents API file
- `CAP-007` on onboarding/role/tier auth files

## Verification
### Command
```bash
( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l
```

### Result
- HOC relative-import backlog files: `25` (down from `30`)

### Command
```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  backend/app/hoc/api/cus/api_keys/embedding.py \
  backend/app/hoc/api/int/agent/agents.py \
  backend/app/hoc/int/agent/engines/onboarding_gate.py \
  backend/app/hoc/int/general/engines/role_guard.py \
  backend/app/hoc/int/general/engines/tier_gating.py
```

### Result
- Capability-linkage gate for remediated files: `✅ All checks passed`

## Capability Evidence Sync
Registry evidence mapping was synchronized in `docs/capabilities/CAPABILITY_REGISTRY.yaml` for:
- `CAP-014` (`memory_system`) -> embedding API evidence path
- `CAP-008` (`multi_agent`) -> internal agents API evidence path
- `CAP-007` (`authorization`) -> onboarding/role/tier evidence paths

## Outcome
Wave 2 batch 2 is closed. HOC import-hygiene debt is reduced while preserving CUS frontend-consumed contract surfaces.
