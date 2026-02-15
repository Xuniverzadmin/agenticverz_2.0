# L2 Router Inventory

**Generated:** 2026-02-05
**Total L2 files:** 87

## Summary by Audience

| Audience | Files | Routes |
|----------|-------|--------|
| cus | 71 | 618 |
| fdr | 8 | 47 |
| infrastructure | 4 | 2 |
| int | 4 | 1 |
| **TOTAL** | **87** | **668** |

## Summary by Domain

| Domain | Files | Routes |
|--------|-------|--------|
| cus/account | 1 | 5 |
| cus/activity | 1 | 19 |
| cus/agent | 4 | 16 |
| cus/analytics | 4 | 25 |
| cus/api_keys | 2 | 11 |
| cus/general | 5 | 82 |
| cus/incidents | 2 | 22 |
| cus/integrations | 5 | 20 |
| cus/logs | 4 | 44 |
| cus/ops | 1 | 4 |
| cus/overview | 1 | 5 |
| cus/policies | 39 | 350 |
| cus/recovery | 2 | 15 |
| fdr/account | 2 | 12 |
| fdr/agent | 1 | 3 |
| fdr/incidents | 2 | 16 |
| fdr/logs | 2 | 7 |
| fdr/ops | 1 | 9 |
| infrastructure/rate_limit.py | 1 | 1 |
| infrastructure/slow_requests.py | 1 | 0 |
| infrastructure/tenancy.py | 1 | 0 |
| infrastructure/tenant.py | 1 | 1 |
| int/account | 1 | 0 |
| int/general | 2 | 1 |
| int/policies | 1 | 0 |

## Wiring Status Summary

| Wiring Type | Count |
|-------------|-------|
| REGISTRY | 26 |
| BRIDGE | 4 |
| DIRECT | 6 |
| NONE | 51 |

## Full Inventory

| File | Domain | Prefix | Routes | Wiring | DB Violations | Notes |
|------|--------|--------|--------|--------|---------------|-------|
| `app/hoc/api/cus/account/memory_pins.py` | cus/account | `/api/v1/memory` | 5 | NONE | 3 | db_violations=3 |
| `app/hoc/api/cus/activity/activity.py` | cus/activity | `/api/v1/activity` | 19 | REGISTRY | 21 | db_violations=21 |
| `app/hoc/api/cus/agent/authz_status.py` | cus/agent | `/int/authz` | 5 | NONE | 0 |  |
| `app/hoc/api/cus/agent/discovery.py` | cus/agent | `/api/v1/discovery` | 3 | NONE | 2 | db_violations=2 |
| `app/hoc/api/cus/agent/onboarding.py` | cus/agent | `/api/v1/onboarding` | 3 | NONE | 0 |  |
| `app/hoc/api/cus/agent/platform.py` | cus/agent | `/platform` | 5 | NONE | 7 | db_violations=7 |
| `app/hoc/api/cus/analytics/costsim.py` | cus/analytics | `/costsim` | 11 | REGISTRY | 13 | db_violations=13 |
| `app/hoc/api/cus/analytics/feedback.py` | cus/analytics | `/api/v1/feedback` | 3 | NONE | 2 | db_violations=2 |
| `app/hoc/api/cus/analytics/predictions.py` | cus/analytics | `/api/v1/predictions` | 4 | NONE | 2 | db_violations=2 |
| `app/hoc/api/cus/analytics/scenarios.py` | cus/analytics | `/scenarios` | 7 | NONE | 0 |  |
| `app/hoc/api/cus/api_keys/auth_helpers.py` | cus/api_keys | `UNKNOWN` | 1 | NONE | 0 |  |
| `app/hoc/api/cus/api_keys/embedding.py` | cus/api_keys | `/embedding` | 10 | NONE | 0 |  |
| `app/hoc/api/cus/general/agents.py` | cus/general | `/api/v1` | 49 | NONE | 6 | db_violations=6 |
| `app/hoc/api/cus/general/debug_auth.py` | cus/general | `/debug/auth` | 3 | NONE | 1 | db_violations=1 |
| `app/hoc/api/cus/general/health.py` | cus/general | `UNKNOWN` | 5 | NONE | 0 |  |
| `app/hoc/api/cus/general/legacy_routes.py` | cus/general | `UNKNOWN` | 23 | NONE | 0 |  |
| `app/hoc/api/cus/general/sdk.py` | cus/general | `/sdk` | 2 | NONE | 0 |  |
| `app/hoc/api/cus/incidents/cost_guard.py` | cus/incidents | `/guard/costs` | 3 | NONE | 3 | db_violations=3 |
| `app/hoc/api/cus/incidents/incidents.py` | cus/incidents | `/api/v1/incidents` | 19 | REGISTRY | 22 | db_violations=22 |
| `app/hoc/api/cus/integrations/cus_telemetry.py` | cus/integrations | `/telemetry` | 5 | REGISTRY | 0 |  |
| `app/hoc/api/cus/integrations/mcp_servers.py` | cus/integrations | `/api/v1/integrations/mcp-servers` | 9 | REGISTRY | 11 | db_violations=11 |
| `app/hoc/api/cus/integrations/protection_dependencies.py` | cus/integrations | `UNKNOWN` | 2 | NONE | 0 |  |
| `app/hoc/api/cus/integrations/session_context.py` | cus/integrations | `/api/v1/session` | 1 | NONE | 0 |  |
| `app/hoc/api/cus/integrations/v1_proxy.py` | cus/integrations | `/v1` | 3 | NONE | 6 | db_violations=6 |
| `app/hoc/api/cus/logs/cost_intelligence.py` | cus/logs | `/cost` | 14 | BRIDGE | 3 | db_violations=3 |
| `app/hoc/api/cus/logs/guard_logs.py` | cus/logs | `/guard/logs` | 3 | NONE | 0 |  |
| `app/hoc/api/cus/logs/tenants.py` | cus/logs | `/api/v1` | 14 | DIRECT | 3 | L6_import; db_violations=3 |
| `app/hoc/api/cus/logs/traces.py` | cus/logs | `/traces` | 13 | NONE | 6 | db_violations=6 |
| `app/hoc/api/cus/ops/cost_ops.py` | cus/ops | `/ops/cost` | 4 | NONE | 3 | db_violations=3 |
| `app/hoc/api/cus/overview/overview.py` | cus/overview | `/api/v1/overview` | 5 | REGISTRY | 7 | db_violations=7 |
| `app/hoc/api/cus/policies/M25_integrations.py` | cus/policies | `/integration` | 17 | NONE | 20 | db_violations=20 |
| `app/hoc/api/cus/policies/alerts.py` | cus/policies | `/alerts` | 13 | NONE | 0 |  |
| `app/hoc/api/cus/policies/analytics.py` | cus/policies | `/analytics` | 8 | REGISTRY | 10 | db_violations=10 |
| `app/hoc/api/cus/account/aos_accounts.py` | cus/account | `/api/v1/accounts` | 17 | REGISTRY | 19 | db_violations=19 |
| `app/hoc/api/cus/api_keys/aos_api_key.py` | cus/api_keys | `/api/v1/api-keys` | 2 | REGISTRY | 4 | db_violations=4 |
| `app/hoc/api/cus/integrations/aos_cus_integrations.py` | cus/integrations | `/api/v1/integrations` | 10 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/billing_dependencies.py` | cus/policies | `UNKNOWN` | 2 | BRIDGE | 0 |  |
| `app/hoc/api/cus/policies/compliance.py` | cus/policies | `/compliance` | 6 | NONE | 0 |  |
| `app/hoc/api/cus/policies/connectors.py` | cus/policies | `/connectors` | 6 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/controls.py` | cus/policies | `/controls` | 6 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/cus_enforcement.py` | cus/policies | `/enforcement` | 3 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/customer_visibility.py` | cus/policies | `/customer` | 4 | NONE | 4 | db_violations=4 |
| `app/hoc/api/cus/policies/datasources.py` | cus/policies | `/datasources` | 9 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/detection.py` | cus/policies | `/detection` | 6 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/evidence.py` | cus/policies | `/evidence` | 8 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/governance.py` | cus/policies | `/governance` | 6 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/guard.py` | cus/policies | `/guard` | 18 | DIRECT | 3 | L5_import; db_violations=3 |
| `app/hoc/api/cus/policies/guard_policies.py` | cus/policies | `/guard/policies` | 2 | NONE | 0 |  |
| `app/hoc/api/cus/policies/lifecycle.py` | cus/policies | `/lifecycle` | 13 | NONE | 0 |  |
| `app/hoc/api/cus/policies/logs.py` | cus/policies | `/api/v1/logs` | 19 | REGISTRY | 19 | db_violations=19 |
| `app/hoc/api/cus/policies/monitors.py` | cus/policies | `/monitors` | 8 | NONE | 0 |  |
| `app/hoc/api/cus/policies/notifications.py` | cus/policies | `/notifications` | 7 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/override.py` | cus/policies | `/limits` | 4 | REGISTRY | 6 | db_violations=6 |
| `app/hoc/api/cus/policies/policies.py` | cus/policies | `/api/v1/policies` | 16 | REGISTRY | 16 | db_violations=16 |
| `app/hoc/api/cus/policies/policy.py` | cus/policies | `/api/v1/policy` | 15 | DIRECT | 34 | L5_import; db_violations=34 |
| `app/hoc/api/cus/policies/policy_layer.py` | cus/policies | `/policy-layer` | 43 | REGISTRY | 44 | db_violations=44 |
| `app/hoc/api/cus/policies/policy_limits_crud.py` | cus/policies | `/policies` | 5 | REGISTRY | 9 | db_violations=9 |
| `app/hoc/api/cus/policies/policy_proposals.py` | cus/policies | `/api/v1/policy-proposals` | 6 | NONE | 2 | db_violations=2 |
| `app/hoc/api/cus/policies/policy_rules_crud.py` | cus/policies | `/policies` | 2 | REGISTRY | 4 | db_violations=4 |
| `app/hoc/api/cus/policies/rate_limits.py` | cus/policies | `/rate-limits` | 6 | REGISTRY | 0 |  |
| `app/hoc/api/cus/policies/rbac_api.py` | cus/policies | `/api/v1/rbac` | 5 | DIRECT | 2 | L5_import; db_violations=2 |
| `app/hoc/api/cus/policies/replay.py` | cus/policies | `/replay` | 4 | NONE | 3 | db_violations=3 |
| `app/hoc/api/cus/policies/retrieval.py` | cus/policies | `/retrieval` | 6 | NONE | 0 |  |
| `app/hoc/api/cus/policies/runtime.py` | cus/policies | `/api/v1/runtime` | 9 | NONE | 0 |  |
| `app/hoc/api/cus/policies/scheduler.py` | cus/policies | `/scheduler` | 10 | NONE | 0 |  |
| `app/hoc/api/cus/policies/simulate.py` | cus/policies | `/limits` | 1 | REGISTRY | 3 | db_violations=3 |
| `app/hoc/api/cus/policies/status_history.py` | cus/policies | `/status_history` | 5 | NONE | 2 | db_violations=2 |
| `app/hoc/api/cus/policies/v1_killswitch.py` | cus/policies | `/v1` | 10 | NONE | 3 | db_violations=3 |
| `app/hoc/api/cus/policies/workers.py` | cus/policies | `/api/v1/workers/business-builder` | 13 | DIRECT | 6 | L5_import; db_violations=6 |
| `app/hoc/api/cus/recovery/recovery.py` | cus/recovery | `/api/v1/recovery` | 14 | DIRECT | 9 | L5_import; L6_import; db_violations=9 |
| `app/hoc/api/cus/recovery/recovery_ingest.py` | cus/recovery | `/api/v1/recovery` | 1 | BRIDGE | 4 | db_violations=4 |
| `app/hoc/api/fdr/account/founder_explorer.py` | fdr/account | `/explorer` | 6 | NONE | 3 | db_violations=3 |
| `app/hoc/api/fdr/account/founder_lifecycle.py` | fdr/account | `/fdr/lifecycle` | 6 | NONE | 0 |  |
| `app/hoc/api/fdr/agent/founder_contract_review.py` | fdr/agent | `/fdr/contracts` | 3 | NONE | 0 |  |
| `app/hoc/api/fdr/incidents/founder_onboarding.py` | fdr/incidents | `/fdr/onboarding` | 2 | NONE | 0 |  |
| `app/hoc/api/fdr/incidents/ops.py` | fdr/incidents | `/ops` | 14 | NONE | 6 | db_violations=6 |
| `app/hoc/api/fdr/logs/founder_review.py` | fdr/logs | `/fdr/review` | 3 | NONE | 3 | db_violations=3 |
| `app/hoc/api/fdr/logs/founder_timeline.py` | fdr/logs | `/fdr/timeline` | 4 | NONE | 7 | db_violations=7 |
| `app/hoc/api/fdr/ops/founder_actions.py` | fdr/ops | `/ops/actions` | 9 | NONE | 3 | db_violations=3 |
| `app/hoc/api/infrastructure/rate_limit.py` | infrastructure/rate_limit.py | `UNKNOWN` | 1 | NONE | 0 |  |
| `app/hoc/api/infrastructure/slow_requests.py` | infrastructure/slow_requests.py | `UNKNOWN` | 0 | NONE | 0 |  |
| `app/hoc/api/infrastructure/tenancy.py` | infrastructure/tenancy.py | `UNKNOWN` | 0 | NONE | 0 |  |
| `app/hoc/api/infrastructure/tenant.py` | infrastructure/tenant.py | `UNKNOWN` | 1 | NONE | 0 |  |
| `app/hoc/int/integrations/int_cli.py` | int/integrations | `UNKNOWN` | 0 | NONE | 1 | db_violations=1 |
| `app/hoc/api/int/general/founder_auth.py` | int/general | `UNKNOWN` | 1 | NONE | 0 |  |
| `app/hoc/api/int/general/protection_gate.py` | int/general | `UNKNOWN` | 0 | NONE | 0 |  |
| `app/hoc/api/int/policies/billing_gate.py` | int/policies | `UNKNOWN` | 0 | BRIDGE | 0 |  |

## Files Needing L4 Wiring

### NONE (No L4 wiring — inline DB or no routes)

- `app/hoc/api/cus/account/memory_pins.py` (cus/account, 5 routes, 3 DB violations)
- `app/hoc/api/cus/agent/authz_status.py` (cus/agent, 5 routes, 0 DB violations)
- `app/hoc/api/cus/agent/discovery.py` (cus/agent, 3 routes, 2 DB violations)
- `app/hoc/api/cus/agent/onboarding.py` (cus/agent, 3 routes, 0 DB violations)
- `app/hoc/api/cus/agent/platform.py` (cus/agent, 5 routes, 7 DB violations)
- `app/hoc/api/cus/analytics/feedback.py` (cus/analytics, 3 routes, 2 DB violations)
- `app/hoc/api/cus/analytics/predictions.py` (cus/analytics, 4 routes, 2 DB violations)
- `app/hoc/api/cus/analytics/scenarios.py` (cus/analytics, 7 routes, 0 DB violations)
- `app/hoc/api/cus/api_keys/auth_helpers.py` (cus/api_keys, 1 routes, 0 DB violations)
- `app/hoc/api/cus/api_keys/embedding.py` (cus/api_keys, 10 routes, 0 DB violations)
- `app/hoc/api/cus/general/agents.py` (cus/general, 49 routes, 6 DB violations)
- `app/hoc/api/cus/general/debug_auth.py` (cus/general, 3 routes, 1 DB violations)
- `app/hoc/api/cus/general/health.py` (cus/general, 5 routes, 0 DB violations)
- `app/hoc/api/cus/general/legacy_routes.py` (cus/general, 23 routes, 0 DB violations)
- `app/hoc/api/cus/general/sdk.py` (cus/general, 2 routes, 0 DB violations)
- `app/hoc/api/cus/incidents/cost_guard.py` (cus/incidents, 3 routes, 3 DB violations)
- `app/hoc/api/cus/integrations/protection_dependencies.py` (cus/integrations, 2 routes, 0 DB violations)
- `app/hoc/api/cus/integrations/session_context.py` (cus/integrations, 1 routes, 0 DB violations)
- `app/hoc/api/cus/integrations/v1_proxy.py` (cus/integrations, 3 routes, 6 DB violations)
- `app/hoc/api/cus/logs/guard_logs.py` (cus/logs, 3 routes, 0 DB violations)
- `app/hoc/api/cus/logs/traces.py` (cus/logs, 13 routes, 6 DB violations)
- `app/hoc/api/cus/ops/cost_ops.py` (cus/ops, 4 routes, 3 DB violations)
- `app/hoc/api/cus/policies/M25_integrations.py` (cus/policies, 17 routes, 20 DB violations)
- `app/hoc/api/cus/policies/alerts.py` (cus/policies, 13 routes, 0 DB violations)
- `app/hoc/api/cus/policies/compliance.py` (cus/policies, 6 routes, 0 DB violations)
- `app/hoc/api/cus/policies/customer_visibility.py` (cus/policies, 4 routes, 4 DB violations)
- `app/hoc/api/cus/policies/guard_policies.py` (cus/policies, 2 routes, 0 DB violations)
- `app/hoc/api/cus/policies/lifecycle.py` (cus/policies, 13 routes, 0 DB violations)
- `app/hoc/api/cus/policies/monitors.py` (cus/policies, 8 routes, 0 DB violations)
- `app/hoc/api/cus/policies/policy_proposals.py` (cus/policies, 6 routes, 2 DB violations)
- `app/hoc/api/cus/policies/replay.py` (cus/policies, 4 routes, 3 DB violations)
- `app/hoc/api/cus/policies/retrieval.py` (cus/policies, 6 routes, 0 DB violations)
- `app/hoc/api/cus/policies/runtime.py` (cus/policies, 9 routes, 0 DB violations)
- `app/hoc/api/cus/policies/scheduler.py` (cus/policies, 10 routes, 0 DB violations)
- `app/hoc/api/cus/policies/status_history.py` (cus/policies, 5 routes, 2 DB violations)
- `app/hoc/api/cus/policies/v1_killswitch.py` (cus/policies, 10 routes, 3 DB violations)
- `app/hoc/api/fdr/account/founder_explorer.py` (fdr/account, 6 routes, 3 DB violations)
- `app/hoc/api/fdr/account/founder_lifecycle.py` (fdr/account, 6 routes, 0 DB violations)
- `app/hoc/api/fdr/agent/founder_contract_review.py` (fdr/agent, 3 routes, 0 DB violations)
- `app/hoc/api/fdr/incidents/founder_onboarding.py` (fdr/incidents, 2 routes, 0 DB violations)
- `app/hoc/api/fdr/incidents/ops.py` (fdr/incidents, 14 routes, 6 DB violations)
- `app/hoc/api/fdr/logs/founder_review.py` (fdr/logs, 3 routes, 3 DB violations)
- `app/hoc/api/fdr/logs/founder_timeline.py` (fdr/logs, 4 routes, 7 DB violations)
- `app/hoc/api/fdr/ops/founder_actions.py` (fdr/ops, 9 routes, 3 DB violations)
- `app/hoc/int/integrations/int_cli.py` (int/integrations, 0 routes, 1 DB violations)
- `app/hoc/api/int/general/founder_auth.py` (int/general, 1 routes, 0 DB violations)
- `app/hoc/api/int/general/protection_gate.py` (int/general, 0 routes, 0 DB violations)
- `app/hoc/api/infrastructure/rate_limit.py` (infrastructure/rate_limit.py, 1 routes, 0 DB violations)
- `app/hoc/api/infrastructure/slow_requests.py` (infrastructure/slow_requests.py, 0 routes, 0 DB violations)
- `app/hoc/api/infrastructure/tenancy.py` (infrastructure/tenancy.py, 0 routes, 0 DB violations)
- `app/hoc/api/infrastructure/tenant.py` (infrastructure/tenant.py, 1 routes, 0 DB violations)

### DIRECT (L5/L6 bypass — needs L4 routing)

- `app/hoc/api/cus/logs/tenants.py` (cus/logs, 14 routes, notes: L6_import; db_violations=3)
- `app/hoc/api/cus/policies/guard.py` (cus/policies, 18 routes, notes: L5_import; db_violations=3)
- `app/hoc/api/cus/policies/policy.py` (cus/policies, 15 routes, notes: L5_import; db_violations=34)
- `app/hoc/api/cus/policies/rbac_api.py` (cus/policies, 5 routes, notes: L5_import; db_violations=2)
- `app/hoc/api/cus/policies/workers.py` (cus/policies, 13 routes, notes: L5_import; db_violations=6)
- `app/hoc/api/cus/recovery/recovery.py` (cus/recovery, 14 routes, notes: L5_import; L6_import; db_violations=9)

### DB Violations in REGISTRY-wired files

- `app/hoc/api/cus/activity/activity.py` (cus/activity, 21 DB lines)
- `app/hoc/api/cus/analytics/costsim.py` (cus/analytics, 13 DB lines)
- `app/hoc/api/cus/incidents/incidents.py` (cus/incidents, 22 DB lines)
- `app/hoc/api/cus/integrations/mcp_servers.py` (cus/integrations, 11 DB lines)
- `app/hoc/api/cus/overview/overview.py` (cus/overview, 7 DB lines)
- `app/hoc/api/cus/policies/analytics.py` (cus/policies, 10 DB lines)
- `app/hoc/api/cus/account/aos_accounts.py` (cus/account, 19 DB lines)
- `app/hoc/api/cus/api_keys/aos_api_key.py` (cus/api_keys, 4 DB lines)
- `app/hoc/api/cus/policies/logs.py` (cus/policies, 19 DB lines)
- `app/hoc/api/cus/policies/override.py` (cus/policies, 6 DB lines)
- `app/hoc/api/cus/policies/policies.py` (cus/policies, 16 DB lines)
- `app/hoc/api/cus/policies/policy_layer.py` (cus/policies, 44 DB lines)
- `app/hoc/api/cus/policies/policy_limits_crud.py` (cus/policies, 9 DB lines)
- `app/hoc/api/cus/policies/policy_rules_crud.py` (cus/policies, 4 DB lines)
- `app/hoc/api/cus/policies/simulate.py` (cus/policies, 3 DB lines)
