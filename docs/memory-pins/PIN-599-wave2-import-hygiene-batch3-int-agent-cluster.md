# PIN-599: Wave 2 Import Hygiene Batch 3 — INT/Agent Cluster

## Metadata
- Date: 2026-02-20
- Status: COMPLETE
- Scope: HOC-only (`backend/app/hoc/**`)
- Workstream: Legacy debt Wave 2 (import-hygiene batch 3)

## Why
After Wave 2 batch 2, HOC relative-import debt remained concentrated in `int/agent` runtime files. Batch 3 targeted this cluster to remove the largest remaining pocket in one pass.

## What Changed
### Import Hygiene Remediation (14 files)
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

### Capability Linkage
- Added file-level `capability_id` headers:
  - `CAP-008` for multi-agent runtime files
  - `CAP-016` for skill-system files
- Synchronized evidence mapping in:
  - `docs/capabilities/CAPABILITY_REGISTRY.yaml`

### Evidence Artifacts Updated
1. `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_BATCH3_INT_AGENT_CLUSTER_2026-02-20.md`
2. `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
3. `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
4. `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`

## Verification
- HOC relative-import backlog:
  - `( rg -n "from \\.\\." backend/app/hoc --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l` -> `11`
- CUS relative-import backlog (stability hold):
  - `( rg -n "from \\.\\." backend/app/hoc/cus --glob '*.py' || true ) | cut -d: -f1 | sort -u | wc -l` -> `0`
- Capability linkage gate on remediated files:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files ...` -> `✅ All checks passed`
- Syntax sanity:
  - `python3 -m py_compile` on all 14 remediated files -> pass

## Outcome
- HOC import-hygiene backlog reduced: `25 -> 11`
- CUS import-hygiene remains stable: `0`

## Open Residual
- Relative-import backlog still open: `11` files (`int/analytics`, `int/logs`, `int/platform`, `int/policies`, `int/worker`, `int/general/drivers/artifact.py`)
- Layer segregation (`--scope hoc`): `93` violations (separate debt lane)
