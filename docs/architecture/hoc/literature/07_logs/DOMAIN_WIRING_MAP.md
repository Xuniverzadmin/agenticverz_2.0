# Logs — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/logs.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/logs/` (4 files)
         ├── cost_intelligence.py
         ├── guard_logs.py
         ├── tenants.py
         ├── traces.py
         │
         └──→ L3 Adapters (1 files)
                ├── export_bundle_adapter.py ✅
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (17 files)
                       ├── audit_evidence.py → L6 ❌ (no matching driver)
                       ├── audit_ledger_service.py → L6 ❌ (no matching driver)
                       ├── audit_reconciler.py → L6 ❌ (no matching driver)
                       ├── certificate.py → L6 ❌ (no matching driver)
                       ├── completeness_checker.py → L6 ❌ (no matching driver)
                       ├── evidence_facade.py → L6 ❌ (no matching driver)
                       ├── evidence_report.py → L6 ❌ (no matching driver)
                       ├── logs_facade.py → L6 ✅
                       ├── logs_read_engine.py → L6 ❌ (no matching driver)
                       ├── mapper.py → L6 ❌ (no matching driver)
                       └── ... (+7 more)
                     L5 Other (1 files)
                       │
                       └──→ L6 Drivers (12 files)
                              ├── audit_ledger_service_async.py
                              ├── bridges_driver.py
                              ├── capture.py
                              ├── export_bundle_store.py
                              ├── idempotency.py
                              ├── integrity.py
                              ├── job_execution.py
                              ├── logs_domain_store.py
                              └── ... (+4 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2.1_facade | No L2.1 facade to group 4 L2 routers | Build hoc/api/facades/cus/logs.py grouping: cost_intelligence.py, guard_logs.py, tenants.py, traces.py |
| L7_models | 12 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `export_bundle_adapter.py` | `from app.models.export_bundles import DEFAULT_SOC2_CONTROLS,` | L3 MUST NOT import L7 models | Use L5 schemas for data contracts |
| `audit_ledger_service.py` | `from app.models.audit_ledger import ActorType, AuditEntityTy` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `pdf_renderer.py` | `from app.models.export_bundles import EvidenceBundle, Execut` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `audit_engine.py` | `from app.models.contract import AuditVerdict` | L5 MUST NOT import L7 models directly | Route through L6 driver |
