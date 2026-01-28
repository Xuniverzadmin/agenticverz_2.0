# Policies — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/policies.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/policies/` (38 files)
         ├── M25_integrations.py
         ├── alerts.py
         ├── analytics.py
         ├── aos_accounts.py
         ├── aos_api_key.py
         └── ... (+33 more)
         │
         └──→ L3 Adapters (2 files)
                ├── founder_contract_review_adapter.py ✅
                ├── policy_adapter.py ✅
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (61 files)
                       ├── ast.py → L6 ❌ (no matching driver)
                       ├── authority_checker.py → L6 ❌ (no matching driver)
                       ├── binding_moment_enforcer.py → L6 ❌ (no matching driver)
                       ├── claim_decision_engine.py → L6 ❌ (no matching driver)
                       ├── compiler_parser.py → L6 ❌ (no matching driver)
                       ├── content_accuracy.py → L6 ❌ (no matching driver)
                       ├── cus_enforcement_service.py → L6 ❌ (no matching driver)
                       ├── customer_policy_read_engine.py → L6 ❌ (no matching driver)
                       ├── decorator.py → L6 ❌ (no matching driver)
                       ├── degraded_mode.py → L6 ❌ (no matching driver)
                       └── ... (+51 more)
                     L5 Schemas (1 files)
                       │
                       └──→ L6 Drivers (14 files)
                              ├── arbitrator.py
                              ├── optimizer_conflict_resolver.py
                              ├── policy_engine_driver.py
                              ├── policy_graph_driver.py
                              ├── policy_proposal_read_driver.py
                              ├── policy_proposal_write_driver.py
                              ├── policy_read_driver.py
                              ├── policy_rules_driver.py
                              └── ... (+6 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2.1_facade | No L2.1 facade to group 38 L2 routers | Build hoc/api/facades/cus/policies.py grouping: M25_integrations.py, alerts.py, analytics.py, aos_accounts.py, aos_api_key.py, aos_cus_integrations.py, billing_dependencies.py, compliance.py, connectors.py, controls.py, cus_enforcement.py, customer_visibility.py, datasources.py, detection.py, evidence.py, governance.py, guard.py, guard_policies.py, lifecycle.py, logs.py, monitors.py, notifications.py, override.py, policies.py, policy.py, policy_layer.py, policy_limits_crud.py, policy_proposals.py, policy_rules_crud.py, rate_limits.py, rbac_api.py, replay.py, retrieval.py, runtime.py, scheduler.py, simulate.py, status_history.py, workers.py |
| L6_driver | engine.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/policies/L6_drivers/engine.py_driver.py |
| L7_models | 14 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `alerts.py` | `from app.hoc.cus.general.L5_engines.alerts_facade import Ale` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `analytics.py` | `from app.hoc.cus.analytics.L5_engines.analytics_facade impor` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `aos_accounts.py` | `from app.hoc.cus.account.L5_engines.accounts_facade import g` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `aos_accounts.py` | `from app.models.tenant import Invitation, Subscription, Supp` | L2 MUST NOT import L7 models | Use L5 schemas or response models |
| `aos_api_key.py` | `from app.hoc.cus.api_keys.L5_engines.api_keys_facade import ` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `aos_cus_integrations.py` | `from app.hoc.cus.integrations.L5_engines.integrations_facade` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `compliance.py` | `from app.hoc.cus.general.L5_engines.compliance_facade import` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `connectors.py` | `from app.hoc.cus.integrations.L5_engines.connectors_facade i` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `controls.py` | `from app.hoc.cus.controls.L5_engines.controls_facade import ` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `cus_enforcement.py` | `from app.hoc.cus.policies.L5_engines.cus_enforcement_service` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `datasources.py` | `from app.hoc.cus.integrations.L5_engines.datasources_facade ` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `detection.py` | `from app.hoc.cus.analytics.L5_engines.detection_facade impor` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `evidence.py` | `from app.hoc.cus.logs.L5_engines.evidence_facade import Evid` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `governance.py` | `from app.hoc.cus.policies.L5_engines.governance_facade impor` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `guard.py` | `from app.models.killswitch import DefaultGuardrail, Incident` | L2 MUST NOT import L7 models | Use L5 schemas or response models |
| `guard.py` | `from app.models.tenant import Tenant` | L2 MUST NOT import L7 models | Use L5 schemas or response models |
| `guard.py` | `from app.hoc.cus.logs.L5_engines.certificate import Certific` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `guard.py` | `from app.hoc.cus.logs.L5_engines.replay_determinism import D` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `guard.py` | `from app.hoc.cus.logs.L5_engines.replay_determinism import R` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `lifecycle.py` | `from app.hoc.cus.general.L5_engines.lifecycle_facade import ` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| ... | +22 more | | |
