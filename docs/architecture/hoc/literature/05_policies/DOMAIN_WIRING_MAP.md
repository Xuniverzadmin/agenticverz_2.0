# Policies — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/policies.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/policies/` (38 files)
         ├── M25_integrations.py
         ├── alerts.py
         ├── analytics.py
         ├── aos_accounts.py
         ├── aos_api_key.py
         └── ... (+33 more)
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (58 files)
                       ├── ast.py → L6 ❌ (no matching driver)
                       ├── authority_checker.py → L6 ❌ (no matching driver)
                       ├── binding_moment_enforcer.py → L6 ❌ (no matching driver)
                       ├── compiler_parser.py → L6 ❌ (no matching driver)
                       ├── content_accuracy.py → L6 ❌ (no matching driver)
                       ├── cus_enforcement_engine.py → L6 ✅
                       ├── customer_policy_read_engine.py → L6 ❌ (no matching driver)
                       ├── dag_executor.py → L6 ❌ (no matching driver)
                       ├── decorator.py → L6 ❌ (no matching driver)
                       ├── degraded_mode.py → L6 ❌ (no matching driver)
                       └── ... (+48 more)
                     L5 Schemas (4 files)
                       │
                       └──→ L6 Drivers (27 files)
                              ├── arbitrator.py
                              ├── cus_enforcement_driver.py
                              ├── guard_read_driver.py
                              ├── limits_simulation_driver.py
                              ├── m25_integration_read_driver.py
                              ├── m25_integration_write_driver.py
                              ├── optimizer_conflict_resolver.py
                              ├── policies_facade_driver.py
                              └── ... (+19 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 27 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
