# Activity — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/activity.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/activity/` (1 files)
         ├── activity.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (4 files)
                       ├── activity_enums.py → L6 ❌ (no matching driver)
                       ├── activity_facade.py → L6 ✅
                       ├── signal_feedback_engine.py → L6 ❌ (no matching driver)
                       ├── signal_identity.py → L6 ❌ (no matching driver)
                       │
                       └──→ L6 Drivers (1 files)
                              ├── activity_read_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L3_adapter | No L3 adapters but 4 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/activity/L3_adapters/ with domain adapter(s) |
| L7_models | 1 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
