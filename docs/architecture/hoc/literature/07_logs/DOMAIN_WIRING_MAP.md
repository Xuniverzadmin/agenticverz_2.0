# Logs — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/logs.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/logs/` (4 files)
         ├── cost_intelligence.py
         ├── guard_logs.py
         ├── tenants.py
         ├── traces.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (16 files)
                       ├── audit_evidence.py → L6 ❌ (no matching driver)
                       ├── audit_ledger_engine.py → L6 ✅
                       ├── audit_reconciler.py → L6 ❌ (no matching driver)
                       ├── certificate.py → L6 ❌ (no matching driver)
                       ├── completeness_checker.py → L6 ❌ (no matching driver)
                       ├── cost_intelligence_engine.py → L6 ✅
                       ├── evidence_facade.py → L6 ❌ (no matching driver)
                       ├── evidence_report.py → L6 ❌ (no matching driver)
                       ├── logs_facade.py → L6 ✅
                       ├── logs_read_engine.py → L6 ❌ (no matching driver)
                       └── ... (+6 more)
                     L5 Schemas (2 files)
                       │
                       └──→ L6 Drivers (16 files)
                              ├── audit_ledger_driver.py
                              ├── audit_ledger_read_driver.py
                              ├── audit_ledger_write_driver_sync.py
                              ├── bridges_driver.py
                              ├── capture_driver.py
                              ├── cost_intelligence_driver.py
                              ├── cost_intelligence_sync_driver.py
                              ├── export_bundle_store.py
                              └── ... (+8 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 16 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
