# Ops — Software Bible (DRAFT)

**Domain:** ops (fdr/ops)
**Status:** DRAFT — not yet canonical
**L2 Features:** 1 (founder_actions router)
**Scripts:** 0
**Generated:** 2026-02-01
**Reference:** PIN-513 Phase 7

---

## Layer Inventory

### L5 Engines (`hoc/fdr/ops/engines/`)

| File | Role | Key Exports |
|------|------|-------------|
| `founder_action_write_service.py` | Write engine for founder ops actions | `FounderActionWriteService` |
| `founder_review.py` | Contract review engine | `ReviewDecisionRequest`, `get_contract_service()`, `get_eligible_contracts()` |
| `ops_incident_service.py` | Incident aggregation and classification | `OpsIncidentService`, `ErrorStoreProtocol`, `IncidentAggregationConfig` |

### L5 Schemas (`hoc/fdr/ops/schemas/`)

| File | Role | Key Exports |
|------|------|-------------|
| `ops.py` | DTOs for ops domain | `SystemPulseDTO`, `CustomerSegmentDTO`, `FounderActionRequestDTO`, 25+ DTOs |
| `ops_domain_models.py` | Core domain models | `OpsIncident`, `OpsHealthSignal`, `OpsRiskFinding`, `OpsSeverity`, `OpsIncidentCategory` |

### L6 Drivers (`hoc/fdr/ops/drivers/`)

| File | Role | Key Exports |
|------|------|-------------|
| `error_store.py` | Error persistence and query | `DatabaseErrorStore` |
| `ops_write_service.py` | Ops data write operations | `OpsWriteService` |
| `event_emitter.py` | Domain event emission | `EventType`, `EntityType`, `OpsEvent`, `EventEmitter` |
| `founder_action_write_driver.py` | Founder action DB operations | `FounderActionWriteDriver` |

### L2.1 Facades (`hoc/fdr/ops/facades/`)

| File | Role | Key Exports |
|------|------|-------------|
| `ops_facade.py` | Unified ops access facade | `OpsFacade`, `get_ops_facade()` |
| `founder_review_adapter.py` | Review queue view adapter | `FounderReviewAdapter`, `FounderContractSummaryView` |

### L2 APIs (`hoc/api/fdr/ops/`)

| File | Role | Key Exports |
|------|------|-------------|
| `founder_actions.py` | Founder action endpoints | `POST /ops/actions/*` (freeze, throttle, override) |

---

## PIN-513 Phase 7 — Reverse Boundary Severing (HOC→services) (2026-02-01)

| File | Change | Reference |
|------|--------|-----------|
| `fdr/ops/engines/ops_incident_service.py:40` | Import swapped: `app.services.ops_domain_models` → `app.hoc.fdr.ops.schemas.ops_domain_models` | PIN-513 Phase 7, Step 3b |
| `fdr/ops/facades/ops_facade.py:63` | Import swapped: `app.services.ops.error_store` → `app.hoc.fdr.ops.drivers.error_store` | PIN-513 Phase 7, Step 5a |
| `fdr/ops/facades/ops_facade.py:71` | Import swapped: `app.services.ops_incident_service` → `app.hoc.fdr.ops.engines.ops_incident_service` | PIN-513 Phase 7, Step 5b |
| `api/fdr/ops/founder_actions.py:45` | Import swapped: `app.services.founder_action_write_service` → `app.hoc.fdr.ops.engines.founder_action_write_service` | PIN-513 Phase 7, Step 7 |

**Result:** Zero `app.services` imports remain in ops domain.
