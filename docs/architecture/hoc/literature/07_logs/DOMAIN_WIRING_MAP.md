# Logs — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/logs.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/logs/` (4 files)
         ├── cost_intelligence.py
         ├── guard_logs.py
         ├── tenants.py
         ├── traces.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (13 files)
                       ├── audit_evidence.py → L6 ❌ (no matching driver)
                       ├── audit_reconciler.py → L6 ❌ (no matching driver)
                       ├── certificate.py → L6 ❌ (no matching driver)
                       ├── completeness_checker.py → L6 ❌ (no matching driver)
                       ├── evidence_facade.py → L6 ❌ (no matching driver)
                       ├── evidence_report.py → L6 ❌ (no matching driver)
                       ├── logs_facade.py → L6 ✅
                       ├── logs_read_engine.py → L6 ❌ (no matching driver)
                       ├── mapper.py → L6 ❌ (no matching driver)
                       ├── pdf_renderer.py → L6 ❌ (no matching driver)
                       └── ... (+3 more)
                       │
                       └──→ L6 Drivers (4 files)
                              ├── bridges_driver.py
                              ├── export_bundle_store.py
                              ├── logs_domain_store.py
                              ├── pg_store.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L3_adapter | No L3 adapters but 13 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/logs/L3_adapters/ with domain adapter(s) |
| L7_models | 4 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
