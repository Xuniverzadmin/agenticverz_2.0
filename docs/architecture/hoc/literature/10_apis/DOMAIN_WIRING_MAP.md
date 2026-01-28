# Apis — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/apis.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/apis/` — **GAP** (0 files)
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines — **GAP** (0 files)
                       │
                       └──→ L6 Drivers (1 files)
                              ├── keys_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2_api | No L2 API routes but 0 engines exist | Build hoc/api/cus/apis/ with route handlers |
| L7_models | 1 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
