# CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20

## Purpose
Record non-`hoc/*` CI violations moved to legacy tombstone status so active remediation can focus on `backend/app/hoc/**`.

## Policy
- Blocking remediation scope: `backend/app/hoc/**`
- Tombstoned legacy scope: any non-`hoc/*` violations listed here
- Tombstone review date: 2026-03-15
- Tombstone expiry target: 2026-04-30

## Tombstoned Violations (Non-HOC)

### Layer Segregation Guard (6 violation instances across 4 files)
| File | Signals |
|---|---|
| `backend/app/services/incident_write_engine.py` | ORM model import in engine |
| `backend/app/services/budget_enforcement_engine.py` | sqlalchemy import in engine |
| `backend/app/services/policy_graph_engine.py` | sqlalchemy import + session.execute() in engine |
| `backend/app/services/cus_enforcement_driver.py` | business logic in driver (`budget` check) |

### Import Hygiene Relative Imports (29 files)
| File |
|---|
| `backend/app/agents/skills/agent_invoke.py` |
| `backend/app/agents/skills/agent_spawn.py` |
| `backend/app/agents/skills/blackboard_ops.py` |
| `backend/app/auth/gateway_audit.py` |
| `backend/app/auth/onboarding_gate.py` |
| `backend/app/auth/rbac_middleware.py` |
| `backend/app/auth/role_guard.py` |
| `backend/app/auth/shadow_audit.py` |
| `backend/app/auth/tenant_auth.py` |
| `backend/app/auth/tier_gating.py` |
| `backend/app/memory/store.py` |
| `backend/app/models/tenant.py` |
| `backend/app/routing/care.py` |
| `backend/app/routing/probes.py` |
| `backend/app/services/tenant_service.py` |
| `backend/app/skills/base.py` |
| `backend/app/skills/email_send.py` |
| `backend/app/skills/executor.py` |
| `backend/app/skills/http_call.py` |
| `backend/app/skills/kv_store.py` |
| `backend/app/skills/llm_invoke.py` |
| `backend/app/skills/sdsr_fail_trigger.py` |
| `backend/app/skills/slack_send.py` |
| `backend/app/skills/voyage_embed.py` |
| `backend/app/skills/webhook_send.py` |
| `backend/app/storage/artifact.py` |
| `backend/app/utils/budget_tracker.py` |
| `backend/app/utils/idempotency.py` |
| `backend/app/workflow/policies.py` |

### Capability Linkage (`MISSING_CAPABILITY_ID`) (4 files)
| File | Signal |
|---|---|
| `backend/alembic/versions/128_monitoring_activity_feedback_contracts.py` | missing capability ID header |
| `backend/app/skills/registry_v2.py` | missing capability ID header |
| `backend/scripts/ci/check_priority5_intent.py` | missing capability ID header |
| `scripts/ops/lint_sqlmodel_patterns.py` | missing capability ID header |

## Active HOC Backlog (Still Blocking)
- Layer segregation (`--scope hoc`): **14** violations (after Wave 1 hotspot remediation)
- Import hygiene (`backend/app/hoc/**`): **0** files with relative imports (Wave 2 complete)
- Capability linkage (`MISSING_CAPABILITY_ID` in hoc files, full sweep): **965** files (after Wave 1 hotspot remediation)

### HOC Layer-Segregation File Set (8 files)
| File |
|---|
| `backend/app/hoc/fdr/account/engines/explorer_engine.py` |
| `backend/app/hoc/fdr/incidents/engines/ops_incident_engine.py` |
| `backend/app/hoc/fdr/logs/engines/review_engine.py` |
| `backend/app/hoc/fdr/logs/engines/timeline_engine.py` |
| `backend/app/hoc/fdr/ops/engines/founder_action_write_engine.py` |
| `backend/app/hoc/fdr/ops/engines/ops_incident_engine.py` |
| `backend/app/hoc/int/platform/drivers/memory_driver.py` |
| `backend/app/hoc/int/platform/engines/sandbox_engine.py` |

### HOC Relative-Import File Set (0 files)
| File |
|---|
| _None (Wave 2 batch 4 remediation completed on 2026-02-20)_ |

### HOC Capability-Linkage Missing ID Hot Clusters (965 files total)
| Cluster Prefix | Missing `capability_id` Files |
|---|---:|
| `backend/app/hoc/cus/hoc_spine/orchestrator/**` | 83 |
| `backend/app/hoc/cus/policies/L5_engines/**` | 59 |
| `backend/app/hoc/int/platform/drivers/**` | 39 |
| `backend/app/hoc/api/cus/policies/**` | 35 |
| `backend/app/hoc/int/agent/engines/**` | 28 |
| `backend/app/hoc/cus/hoc_spine/services/**` | 32 |

## Reproduction Commands
```bash
python3 scripts/ops/layer_segregation_guard.py --check
python3 scripts/ops/layer_segregation_guard.py --check --scope hoc

grep -r "from \\.\\." backend/app --include='*.py' | cut -d: -f1 | sort -u
grep -r "from \\.\\." backend/app/hoc --include='*.py' | cut -d: -f1 | sort -u

python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  backend/alembic/versions/128_monitoring_activity_feedback_contracts.py \
  backend/app/hoc/cus/integrations/cus_cli.py \
  backend/app/hoc/int/agent/drivers/json_transform_stub.py \
  backend/app/hoc/int/agent/drivers/registry_v2.py \
  backend/app/hoc/int/agent/engines/http_call_stub.py \
  backend/app/hoc/int/agent/engines/llm_invoke_stub.py \
  backend/app/skills/registry_v2.py \
  backend/scripts/ci/check_priority5_intent.py \
  scripts/ops/lint_sqlmodel_patterns.py
```
