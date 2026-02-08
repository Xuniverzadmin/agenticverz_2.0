# Agent — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `hoc/api/facades/cus/agent.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/agent/` — **GAP** (0 files)
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines — **GAP** (0 files)
                       │
                       └──→ L6 Drivers (3 files)
                              ├── discovery_stats_driver.py
                              ├── platform_driver.py
                              ├── routing_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2_api | No L2 API routes but 0 engines exist | Build hoc/api/cus/agent/ with route handlers |
| L7_models | 3 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
