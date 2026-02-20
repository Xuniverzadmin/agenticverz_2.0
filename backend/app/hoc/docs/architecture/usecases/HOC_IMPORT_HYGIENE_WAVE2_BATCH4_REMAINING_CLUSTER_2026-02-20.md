# HOC Import Hygiene Wave 2 — Batch 4 Remaining Cluster (2026-02-20)

## Scope
Wave 2 batch 4 targeted the final HOC residual relative-import cluster after batch 3.

## Backend Changes Applied
Converted relative imports (`from ..`) to canonical absolute imports (`from app...`) in 10 files:

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

## Capability Linkage
Added file-level capability headers for changed files:
- `CAP-012`: workflow execution surfaces (`runner.py`, `pool.py`, `artifact.py`)
- `CAP-007`: auth/rbac surfaces (`shadow_audit.py`, `rbac_middleware.py`)
- `CAP-010`: CARE routing surfaces (`care.py`, `probes.py`)
- `CAP-014`: memory storage surface (`memory_store.py`)
- `CAP-009`: policy enforcement surface (`policies.py`)

## Registry Evidence Sync
Updated `docs/capabilities/CAPABILITY_REGISTRY.yaml` evidence mappings for:
- `CAP-006` (added HOC gateway audit surface evidence)
- `CAP-007`
- `CAP-009`
- `CAP-010`
- `CAP-012`
- `CAP-014`

## Verification
### Command
```bash
( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l
```

### Result
- HOC relative-import backlog files: `0` (down from `10`)

### Command
```bash
( rg -n "from \\.\\." backend/app/hoc/cus --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l
```

### Result
- CUS relative-import backlog files: `0` (stable)

### Command
```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  backend/app/hoc/int/analytics/engines/runner.py \
  backend/app/hoc/int/general/drivers/artifact.py \
  backend/app/hoc/int/logs/drivers/pool.py \
  backend/app/hoc/int/logs/engines/gateway_audit.py \
  backend/app/hoc/int/logs/engines/shadow_audit.py \
  backend/app/hoc/int/platform/drivers/care.py \
  backend/app/hoc/int/platform/drivers/memory_store.py \
  backend/app/hoc/int/platform/drivers/policies.py \
  backend/app/hoc/int/platform/drivers/probes.py \
  backend/app/hoc/int/policies/engines/rbac_middleware.py \
  docs/capabilities/CAPABILITY_REGISTRY.yaml
```

### Result
- Capability-linkage gate for remediated files: `✅ All checks passed`

### Command
```bash
python3 -m py_compile \
  backend/app/hoc/int/analytics/engines/runner.py \
  backend/app/hoc/int/general/drivers/artifact.py \
  backend/app/hoc/int/logs/drivers/pool.py \
  backend/app/hoc/int/logs/engines/gateway_audit.py \
  backend/app/hoc/int/logs/engines/shadow_audit.py \
  backend/app/hoc/int/platform/drivers/care.py \
  backend/app/hoc/int/platform/drivers/memory_store.py \
  backend/app/hoc/int/platform/drivers/policies.py \
  backend/app/hoc/int/platform/drivers/probes.py \
  backend/app/hoc/int/policies/engines/rbac_middleware.py
```

### Result
- Syntax sanity: `PASS`

## Outcome
Wave 2 import-hygiene remediation is complete for HOC scope:
- HOC relative-import backlog: `10 -> 0`
- CUS relative-import backlog: `0 -> 0` (stable)
