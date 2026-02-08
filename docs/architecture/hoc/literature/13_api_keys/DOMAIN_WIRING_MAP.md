# Api_Keys — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/api_keys.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/api_keys/` (2 files)
         ├── auth_helpers.py
         ├── embedding.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (2 files)
                       ├── api_keys_facade.py → L6 ✅
                       ├── keys_engine.py → L6 ✅
                       │
                       └──→ L6 Drivers (2 files)
                              ├── api_keys_facade_driver.py
                              ├── keys_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 2 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
