# Ops — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `hoc/api/facades/cus/ops.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/ops/` — **GAP** (0 files)
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (1 files)
                       ├── cost_ops_engine.py → L6 ❌ (no matching driver)
                       │
                       └──→ L6 Drivers (1 files)
                              ├── cost_read_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2_api | No L2 API routes but 1 engines exist | Build hoc/api/cus/ops/ with route handlers |
| L7_models | 1 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
