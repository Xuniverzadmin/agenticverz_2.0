# Policies — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/policies.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/policies/` (37 files)
         ├── M25_integrations.py
         ├── alerts.py
         ├── analytics.py
         ├── aos_accounts.py
         ├── aos_api_key.py
         └── ... (+32 more)
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (51 files)
                       ├── ast.py → L6 ❌ (no matching driver)
                       ├── authority_checker.py → L6 ❌ (no matching driver)
                       ├── binding_moment_enforcer.py → L6 ❌ (no matching driver)
                       ├── compiler_parser.py → L6 ❌ (no matching driver)
                       ├── content_accuracy.py → L6 ❌ (no matching driver)
                       ├── customer_policy_read_engine.py → L6 ❌ (no matching driver)
                       ├── decorator.py → L6 ❌ (no matching driver)
                       ├── degraded_mode.py → L6 ❌ (no matching driver)
                       ├── deterministic_engine.py → L6 ❌ (no matching driver)
                       ├── dsl_parser.py → L6 ❌ (no matching driver)
                       └── ... (+41 more)
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
| L3_adapter | No L3 adapters but 51 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/policies/L3_adapters/ with domain adapter(s) |
| L7_models | 14 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
