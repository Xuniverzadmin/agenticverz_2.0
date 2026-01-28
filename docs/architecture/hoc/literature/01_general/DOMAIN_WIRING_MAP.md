# General — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/general.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/general/` (4 files)
         ├── agents.py
         ├── debug_auth.py
         ├── health.py
         ├── sdk.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                └──→ L4 Runtime (6 files)
                       ├── transaction_coordinator.py
                       ├── constraint_checker.py
                       ├── governance_orchestrator.py
                       ├── phase_status_invariants.py
                       ├── plan_generation_engine.py
                       └── ... (+1 more)
                       │
                │
                └──→ L5 Engines (36 files)
                       ├── alert_log_linker.py → L6 ❌ (no matching driver)
                       ├── alert_worker.py → L6 ❌ (no matching driver)
                       ├── alerts_facade.py → L6 ❌ (no matching driver)
                       ├── audit_durability.py → L6 ❌ (no matching driver)
                       ├── audit_store.py → L6 ❌ (no matching driver)
                       ├── canonical_json.py → L6 ❌ (no matching driver)
                       ├── compliance_facade.py → L6 ❌ (no matching driver)
                       ├── concurrent_runs.py → L6 ❌ (no matching driver)
                       ├── constraint_checker.py → L6 ❌ (no matching driver)
                       ├── control_registry.py → L6 ❌ (no matching driver)
                       └── ... (+26 more)
                     L5 Schemas (8 files)
                     L5 Other (13 files)
                       │
                       └──→ L6 Drivers (13 files)
                              ├── alert_driver.py
                              ├── alert_emitter.py
                              ├── budget_tracker.py
                              ├── cross_domain.py
                              ├── cus_health_driver.py
                              ├── dag_executor.py
                              ├── decisions.py
                              ├── governance_signal_driver.py
                              └── ... (+5 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2.1_facade | No L2.1 facade to group 4 L2 routers | Build hoc/api/facades/cus/general.py grouping: agents.py, debug_auth.py, health.py, sdk.py |
| L3_adapter | No L3 adapters but 36 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/general/L3_adapters/ with domain adapter(s) |
| L6_driver | alert_worker.py has DB imports but no matching L6 driver | Extract DB logic to hoc/cus/general/L6_drivers/alert_worker.py_driver.py |
| L7_models | 13 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `alert_worker.py` | `from app.db_async import AsyncSessionLocal, async_session_co` | L5 MUST NOT access DB directly | Use L6 driver for DB access |
| `knowledge_lifecycle_manager.py` | `from app.models.knowledge_lifecycle import KnowledgePlaneLif` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `knowledge_sdk.py` | `from app.models.knowledge_lifecycle import KnowledgePlaneLif` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `lifecycle_stages_base.py` | `from app.models.knowledge_lifecycle import KnowledgePlaneLif` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `guard_write_driver.py` | `from sqlalchemy import and_, select` | L5 MUST NOT import sqlalchemy | Move DB logic to L6 driver |
| `guard_write_driver.py` | `from sqlmodel import Session` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver |
| `guard_write_driver.py` | `from app.models.killswitch import Incident, IncidentEvent, I` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `offboarding.py` | `from app.models.knowledge_lifecycle import KnowledgePlaneLif` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `onboarding.py` | `from app.models.knowledge_lifecycle import KnowledgePlaneLif` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `job_executor.py` | `from app.models.governance_job import JobStatus, JobStep, St` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `contract_engine.py` | `from app.models.contract import TERMINAL_STATES, VALID_TRANS` | L5 MUST NOT import L7 models directly | Route through L6 driver |
