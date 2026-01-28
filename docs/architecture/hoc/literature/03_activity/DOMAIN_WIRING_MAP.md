# Activity — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/activity.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/activity/` (1 files)
         ├── activity.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (8 files)
                       ├── activity_enums.py → L6 ❌ (no matching driver)
                       ├── activity_facade.py → L6 ✅
                       ├── attention_ranking_engine.py → L6 ❌ (no matching driver)
                       ├── cost_analysis_engine.py → L6 ❌ (no matching driver)
                       ├── cus_telemetry_service.py → L6 ❌ (no matching driver)
                       ├── pattern_detection_engine.py → L6 ❌ (no matching driver)
                       ├── signal_feedback_engine.py → L6 ❌ (no matching driver)
                       ├── signal_identity.py → L6 ❌ (no matching driver)
                       │
                       └──→ L6 Drivers (3 files)
                              ├── activity_read_driver.py
                              ├── orphan_recovery.py
                              ├── run_signal_service.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2.1_facade | No L2.1 facade to group 1 L2 routers | Build hoc/api/facades/cus/activity.py grouping: activity.py |
| L3_adapter | No L3 adapters but 8 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/activity/L3_adapters/ with domain adapter(s) |
| L7_models | 3 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `activity.py` | `from app.hoc.cus.activity.L5_engines.activity_facade import ` | L2 MUST NOT import L5 directly | Route through L3 adapter |
