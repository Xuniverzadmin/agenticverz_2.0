# Overview — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/overview.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/overview/` (1 files)
         ├── overview.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (1 files)
                       ├── overview_facade.py → L6 ✅
                       │
                       └──→ L6 Drivers (1 files)
                              ├── overview_facade_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L3_adapter | No L3 adapters but 1 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/overview/L3_adapters/ with domain adapter(s) |
| L7_models | 1 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
