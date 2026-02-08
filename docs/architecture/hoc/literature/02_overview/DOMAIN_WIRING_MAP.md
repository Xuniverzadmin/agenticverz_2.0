# Overview — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/overview.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/overview/` (1 files)
         ├── overview.py
         │
         ├──→ L4 Spine (via hoc_spine/)
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
| L7_models | 1 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
