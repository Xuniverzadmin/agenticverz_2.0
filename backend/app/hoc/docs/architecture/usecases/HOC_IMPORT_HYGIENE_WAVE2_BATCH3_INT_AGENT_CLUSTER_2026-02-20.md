# HOC Import Hygiene Wave 2 — Batch 3 INT/Agent Cluster (2026-02-20)

## Scope
Wave 2 batch 3 targeted `backend/app/hoc/int/agent/**` to clear the largest remaining relative-import cluster under HOC scope.

## Backend Changes Applied
Converted relative imports (`from ..`) to canonical absolute imports (`from app...`) in 14 files:

1. `backend/app/hoc/int/agent/drivers/agent_spawn.py`
2. `backend/app/hoc/int/agent/drivers/blackboard_ops.py`
3. `backend/app/hoc/int/agent/drivers/kv_store.py`
4. `backend/app/hoc/int/agent/drivers/sdsr_fail_trigger.py`
5. `backend/app/hoc/int/agent/drivers/worker_registry_driver.py`
6. `backend/app/hoc/int/agent/engines/agent_invoke.py`
7. `backend/app/hoc/int/agent/engines/email_send.py`
8. `backend/app/hoc/int/agent/engines/executor.py`
9. `backend/app/hoc/int/agent/engines/http_call.py`
10. `backend/app/hoc/int/agent/engines/llm_invoke.py`
11. `backend/app/hoc/int/agent/engines/skills_base.py`
12. `backend/app/hoc/int/agent/engines/slack_send.py`
13. `backend/app/hoc/int/agent/engines/voyage_embed.py`
14. `backend/app/hoc/int/agent/engines/webhook_send.py`

## Capability Linkage
Added capability headers for all remediated files:
- `CAP-008` for multi-agent runtime files
- `CAP-016` for skill-system files

## Verification
### Command
```bash
( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l
```

### Result
- HOC relative-import backlog files: `11` (down from `25`)

### Command
```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  backend/app/hoc/int/agent/drivers/agent_spawn.py \
  backend/app/hoc/int/agent/drivers/blackboard_ops.py \
  backend/app/hoc/int/agent/drivers/kv_store.py \
  backend/app/hoc/int/agent/drivers/sdsr_fail_trigger.py \
  backend/app/hoc/int/agent/drivers/worker_registry_driver.py \
  backend/app/hoc/int/agent/engines/agent_invoke.py \
  backend/app/hoc/int/agent/engines/email_send.py \
  backend/app/hoc/int/agent/engines/executor.py \
  backend/app/hoc/int/agent/engines/http_call.py \
  backend/app/hoc/int/agent/engines/llm_invoke.py \
  backend/app/hoc/int/agent/engines/skills_base.py \
  backend/app/hoc/int/agent/engines/slack_send.py \
  backend/app/hoc/int/agent/engines/voyage_embed.py \
  backend/app/hoc/int/agent/engines/webhook_send.py
```

### Result
- Capability-linkage gate for remediated files: `✅ All checks passed`

## Registry Evidence Sync
Updated `docs/capabilities/CAPABILITY_REGISTRY.yaml` evidence for:
- `CAP-008` (multi_agent)
- `CAP-016` (skill_system)

## Outcome
Wave 2 batch 3 is complete with the INT/agent relative-import cluster cleared. Remaining import-hygiene debt is reduced to a smaller residual set outside this cluster.
