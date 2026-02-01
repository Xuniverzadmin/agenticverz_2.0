# Ops Domain — Canonical Software Literature (DRAFT)

**Domain:** ops (fdr/ops)
**Status:** DRAFT — not yet canonical
**Generated:** 2026-02-01
**Reference:** PIN-513 Phase 7

---

## File Registry

### L5 Engines

**`founder_action_write_service.py`** (109 LOC)
- Role: Write engine for founder operational actions (freeze-tenant, throttle-tenant, override-incident)
- Callers: `api/fdr/ops/founder_actions.py` (L2)
- Delegates: `founder_action_write_driver.py` (L6)
- Key methods: `create_founder_action()`, `mark_action_reversed()`, `commit()`, `rollback()`

**`ops_incident_service.py`** (463 LOC)
- Role: Incident aggregation and severity classification from error store data
- Callers: `ops_facade.py` (L2.1 facade)
- Delegates: `error_store.py` (L6) via `ErrorStoreProtocol`
- Key methods: `get_active_incidents()`, `get_incident_by_component()`, `get_incident_summary()`
- Note: Identical copy exists at `fdr/incidents/engines/ops_incident_service.py` — potential dedup target

**`founder_review.py`** (LOC TBD)
- Role: Contract review queue engine for founder oversight
- Callers: `founder_review_adapter.py` (facade)
- Key functions: `get_contract_service()`, `get_eligible_contracts()`, `ReviewDecisionRequest`

### L5 Schemas

**`ops_domain_models.py`**
- Role: Core domain models for ops domain
- Exports: `OpsIncident`, `OpsHealthSignal`, `OpsRiskFinding`, `OpsTrendMetric`, `OpsDecisionOutcome`
- Enums: `OpsSeverity`, `OpsIncidentCategory`, `OpsHealthStatus`, `OpsRiskLevel`
- Consumers: `ops_incident_service.py` (both copies), `ops_facade.py`

**`ops.py`**
- Role: DTO definitions for ops API layer (25+ DTOs)
- Key exports: `SystemPulseDTO`, `CustomerSegmentDTO`, `CustomerAtRiskDTO`, `FounderActionRequestDTO`, `FounderActionResponseDTO`

### L6 Drivers

**`error_store.py`** (131 LOC)
- Role: Error persistence and query against infra error store
- Callers: `ops_facade.py` (via lazy load)
- Key methods: `get_errors_by_component()`, `get_error_counts_by_class()`, `get_error_counts_by_component()`

**`founder_action_write_driver.py`** (148 LOC)
- Role: Pure DB operations for founder actions
- Callers: `founder_action_write_service.py` (L5)
- Key methods: `insert_action()`, `update_action_reversed()`

**`ops_write_service.py`** (LOC TBD)
- Role: Write operations for ops domain data
- Callers: TBD

**`event_emitter.py`** (LOC TBD)
- Role: Domain event emission for ops events
- Exports: `EventType`, `EntityType`, `OpsEvent`, `EventEmitter`, `get_event_emitter()`

### L2.1 Facades

**`ops_facade.py`** (191 LOC)
- Role: Unified access point for ops domain (incidents + errors)
- Callers: `api/fdr/incidents/ops.py` (L2)
- Delegates: `DatabaseErrorStore` (L6), `OpsIncidentService` (L5)
- Key methods: `get_active_incidents()`, `get_incident_summary()`, `get_error_counts_by_component()`, `get_error_counts_by_class()`
- Factory: `get_ops_facade(db_url)`

**`founder_review_adapter.py`** (LOC TBD)
- Role: View adapter translating review engine output to API-friendly format
- Exports: `FounderReviewAdapter`, `FounderContractSummaryView`, `FounderReviewQueueResponse`

---

## Legacy Connections

**None.** All `app.services` imports severed (PIN-513 Phase 7).

## Known Issues

- Duplicate `ops_incident_service.py` exists at both `fdr/ops/engines/` and `fdr/incidents/engines/` — candidate for dedup
- No tally script exists (`scripts/ops/hoc_ops_tally.py`)
- Domain not yet registered in `literature/hoc_domain/INDEX.md`
