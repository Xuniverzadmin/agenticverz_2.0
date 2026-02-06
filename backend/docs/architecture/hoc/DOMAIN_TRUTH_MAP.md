# Domain Truth Map

**Generated:** 2026-02-05
**Purpose:** Per-domain L2 -> L4 -> L5 -> L6 -> L7 chain verification

## Chain Legend

- **COMPLETE**: Full L2->L4->L5->L6->L7 chain exists and all L2 files use REGISTRY wiring
- **PARTIAL**: Some L2 files wired to L4, others not; or chain has gaps
- **BROKEN**: L2 files bypass L4 (DIRECT/NONE) or chain has missing layers
- **GAP**: Layer entirely missing for this domain

## Customer Domains (cus/)

| Domain | L2 Files | L2 Routes | L4 Handler | L4 Bridge | L5 Engines | L6 Drivers | Wiring (R/B/D/N) | DB Violations | Chain Status |
|--------|----------|-----------|------------|-----------|------------|------------|-------------------|---------------|-------------|
| account | 1 | 5 | account_handler.py | account_bridge.py | 7 | 3 | 0/0/0/1 | 3 | BROKEN (no L4 wiring) |
| activity | 1 | 19 | activity_handler.py | activity_bridge.py | 8 | 4 | 1/0/0/0 | 21 | PARTIAL (>50% wired) |
| analytics | 4 | 25 | analytics_sandbox_handler.py, analytics_validation_handler.py, analytics_config_handler.py, analytics_handler.py, analytics_prediction_handler.py, analytics_snapshot_handler.py, analytics_metrics_handler.py | analytics_bridge.py | 20 | 11 | 1/0/0/3 | 17 | PARTIAL (<50% wired) |
| api_keys | 2 | 11 | api_keys_handler.py | api_keys_bridge.py | 2 | 2 | 0/0/0/2 | 0 | BROKEN (no L4 wiring) |
| apis | 0 | 0 | MISSING | MISSING | 0 | 1 | 0/0/0/0 | 0 | GAP (no L5) |
| controls | 0 | 0 | controls_handler.py | controls_bridge.py | 4 | 9 | 0/0/0/0 | 0 | GAP (no L2) |
| incidents | 2 | 22 | incidents_handler.py | incidents_bridge.py | 16 | 12 | 1/0/0/1 | 25 | PARTIAL (>50% wired) |
| integrations | 5 | 20 | integrations_handler.py | integrations_bridge.py | 16 | 5 | 2/0/0/3 | 17 | PARTIAL (<50% wired) |
| logs | 4 | 44 | logs_handler.py | logs_bridge.py | 14 | 13 | 0/1/1/2 | 12 | BROKEN (L5/L6 bypass) |
| overview | 1 | 5 | overview_handler.py | overview_bridge.py | 1 | 1 | 1/0/0/0 | 7 | PARTIAL (>50% wired) |
| policies | 39 | 350 | policies_handler.py | policies_bridge.py | 60 | 19 | 20/1/4/14 | 213 | BROKEN (L5/L6 bypass) |

## Founder Domains (fdr/)

| Domain | L2 Files | L2 Routes | L5 Engines | L6 Drivers | Wiring (R/B/D/N) | DB Violations | Chain Status |
|--------|----------|-----------|------------|------------|-------------------|---------------|-------------|
| agent | 1 | 3 | 0 | 0 | 0/0/0/1 | 0 | BROKEN (no L4 wiring) |
| incidents | 2 | 16 | 0 | 0 | 0/0/0/2 | 6 | BROKEN (no L4 wiring) |
| ops | 1 | 9 | 0 | 0 | 0/0/0/1 | 3 | BROKEN (no L4 wiring) |
| platform | 0 | 0 | 0 | 0 | 0/0/0/0 | 0 | GAP (no L2) |

## L4 Spine (hoc_spine) Summary

**Handler modules:** 24

- `account_handler.py`
- `activity_handler.py`
- `analytics_config_handler.py`
- `analytics_handler.py`
- `analytics_metrics_handler.py`
- `analytics_prediction_handler.py`
- `analytics_sandbox_handler.py`
- `analytics_snapshot_handler.py`
- `analytics_validation_handler.py`
- `api_keys_handler.py`
- `circuit_breaker_handler.py`
- `controls_handler.py`
- `idempotency_handler.py`
- `incidents_handler.py`
- `integration_bootstrap_handler.py`
- `integrations_handler.py`
- `integrity_handler.py`
- `logs_handler.py`
- `mcp_handler.py`
- `orphan_recovery_handler.py`
- `overview_handler.py`
- `policies_handler.py`
- `policy_governance_handler.py`
- `run_governance_handler.py`

**Bridge modules:** 10

- `account_bridge.py`
- `activity_bridge.py`
- `analytics_bridge.py`
- `api_keys_bridge.py`
- `controls_bridge.py`
- `incidents_bridge.py`
- `integrations_bridge.py`
- `logs_bridge.py`
- `overview_bridge.py`
- `policies_bridge.py`

## Gap Analysis

### L2 Files Without L4 Wiring (NONE/DIRECT — Need Handler)

- `app/hoc/api/cus/account/memory_pins.py` — 5 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/cus/agent/authz_status.py` — 5 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/agent/discovery.py` — 3 routes, 2 DB violations, wiring: NONE
- `app/hoc/api/cus/agent/onboarding.py` — 3 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/agent/platform.py` — 5 routes, 7 DB violations, wiring: NONE
- `app/hoc/api/cus/analytics/feedback.py` — 3 routes, 2 DB violations, wiring: NONE
- `app/hoc/api/cus/analytics/predictions.py` — 4 routes, 2 DB violations, wiring: NONE
- `app/hoc/api/cus/analytics/scenarios.py` — 7 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/api_keys/auth_helpers.py` — 1 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/api_keys/embedding.py` — 10 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/general/agents.py` — 49 routes, 6 DB violations, wiring: NONE
- `app/hoc/api/cus/general/debug_auth.py` — 3 routes, 1 DB violations, wiring: NONE
- `app/hoc/api/cus/general/health.py` — 5 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/general/legacy_routes.py` — 23 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/general/sdk.py` — 2 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/incidents/cost_guard.py` — 3 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/cus/integrations/protection_dependencies.py` — 2 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/integrations/session_context.py` — 1 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/integrations/v1_proxy.py` — 3 routes, 6 DB violations, wiring: NONE
- `app/hoc/api/cus/logs/guard_logs.py` — 3 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/logs/tenants.py` — 14 routes, 3 DB violations, wiring: DIRECT
- `app/hoc/api/cus/logs/traces.py` — 13 routes, 6 DB violations, wiring: NONE
- `app/hoc/api/cus/ops/cost_ops.py` — 4 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/M25_integrations.py` — 17 routes, 20 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/alerts.py` — 13 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/compliance.py` — 6 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/customer_visibility.py` — 4 routes, 4 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/guard.py` — 18 routes, 3 DB violations, wiring: DIRECT
- `app/hoc/api/cus/policies/guard_policies.py` — 2 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/lifecycle.py` — 13 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/monitors.py` — 8 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/policy.py` — 15 routes, 34 DB violations, wiring: DIRECT
- `app/hoc/api/cus/policies/policy_proposals.py` — 6 routes, 2 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/rbac_api.py` — 5 routes, 2 DB violations, wiring: DIRECT
- `app/hoc/api/cus/policies/replay.py` — 4 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/retrieval.py` — 6 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/runtime.py` — 9 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/scheduler.py` — 10 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/status_history.py` — 5 routes, 2 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/v1_killswitch.py` — 10 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/cus/policies/workers.py` — 13 routes, 6 DB violations, wiring: DIRECT
- `app/hoc/api/cus/recovery/recovery.py` — 14 routes, 9 DB violations, wiring: DIRECT
- `app/hoc/api/fdr/account/founder_explorer.py` — 6 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/fdr/account/founder_lifecycle.py` — 6 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/fdr/agent/founder_contract_review.py` — 3 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/fdr/incidents/founder_onboarding.py` — 2 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/fdr/incidents/ops.py` — 14 routes, 6 DB violations, wiring: NONE
- `app/hoc/api/fdr/logs/founder_review.py` — 3 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/fdr/logs/founder_timeline.py` — 4 routes, 7 DB violations, wiring: NONE
- `app/hoc/api/fdr/ops/founder_actions.py` — 9 routes, 3 DB violations, wiring: NONE
- `app/hoc/api/infrastructure/rate_limit.py` — 1 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/infrastructure/tenant.py` — 1 routes, 0 DB violations, wiring: NONE
- `app/hoc/api/int/general/founder_auth.py` — 1 routes, 0 DB violations, wiring: NONE

### Priority Order for Gate 1 (DB Removal)

Sorted by DB violation count (highest first):

1. `app/hoc/api/cus/policies/policy_layer.py` — **44 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/policy.py` — **34 DB violations**, wiring: DIRECT
1. `app/hoc/api/cus/incidents/incidents.py` — **22 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/activity/activity.py` — **21 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/M25_integrations.py` — **20 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/aos_accounts.py` — **19 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/logs.py` — **19 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/policies.py` — **16 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/analytics/costsim.py` — **13 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/integrations/mcp_servers.py` — **11 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/analytics.py` — **10 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/policy_limits_crud.py` — **9 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/recovery/recovery.py` — **9 DB violations**, wiring: DIRECT
1. `app/hoc/api/cus/agent/platform.py` — **7 DB violations**, wiring: NONE
1. `app/hoc/api/cus/overview/overview.py` — **7 DB violations**, wiring: REGISTRY
1. `app/hoc/api/fdr/logs/founder_timeline.py` — **7 DB violations**, wiring: NONE
1. `app/hoc/api/cus/general/agents.py` — **6 DB violations**, wiring: NONE
1. `app/hoc/api/cus/integrations/v1_proxy.py` — **6 DB violations**, wiring: NONE
1. `app/hoc/api/cus/logs/traces.py` — **6 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/override.py` — **6 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/workers.py` — **6 DB violations**, wiring: DIRECT
1. `app/hoc/api/fdr/incidents/ops.py` — **6 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/aos_api_key.py` — **4 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/customer_visibility.py` — **4 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/policy_rules_crud.py` — **4 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/recovery/recovery_ingest.py` — **4 DB violations**, wiring: BRIDGE
1. `app/hoc/api/cus/account/memory_pins.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/cus/incidents/cost_guard.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/cus/logs/cost_intelligence.py` — **3 DB violations**, wiring: BRIDGE
1. `app/hoc/api/cus/logs/tenants.py` — **3 DB violations**, wiring: DIRECT
1. `app/hoc/api/cus/ops/cost_ops.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/guard.py` — **3 DB violations**, wiring: DIRECT
1. `app/hoc/api/cus/policies/replay.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/simulate.py` — **3 DB violations**, wiring: REGISTRY
1. `app/hoc/api/cus/policies/v1_killswitch.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/fdr/account/founder_explorer.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/fdr/logs/founder_review.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/fdr/ops/founder_actions.py` — **3 DB violations**, wiring: NONE
1. `app/hoc/api/cus/agent/discovery.py` — **2 DB violations**, wiring: NONE
1. `app/hoc/api/cus/analytics/feedback.py` — **2 DB violations**, wiring: NONE
1. `app/hoc/api/cus/analytics/predictions.py` — **2 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/policy_proposals.py` — **2 DB violations**, wiring: NONE
1. `app/hoc/api/cus/policies/rbac_api.py` — **2 DB violations**, wiring: DIRECT
1. `app/hoc/api/cus/policies/status_history.py` — **2 DB violations**, wiring: NONE
1. `app/hoc/api/cus/general/debug_auth.py` — **1 DB violations**, wiring: NONE
1. `app/hoc/api/int/account/aos_cli.py` — **1 DB violations**, wiring: NONE