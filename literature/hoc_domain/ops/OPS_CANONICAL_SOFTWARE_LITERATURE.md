# Ops Domain — Canonical Software Literature (DRAFT)

**Domain:** ops (fdr/ops)  
**Status:** DRAFT — audit-aligned, not yet fully canonical  
**Updated:** 2026-02-15  
**References:** PIN-564, PIN-565, PIN-566

---

## Reality Delta (2026-02-15)

- Founder UAT console is wired via app-shell routing for both founder surfaces:
  - `/prefops/uat`
  - `/fops/uat`
- UAT execution gate is unified in:
  - `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`
- Determinism hardening applied:
  - Playwright configs pinned to `127.0.0.1:5173` + explicit app-shell `cwd`
  - Browser binary preflight check added to gate script
  - UI orphan-page check now recognizes lazy dynamic imports

## Reality Delta (2026-02-12, Wave-4 Script Coverage Audit)

- Wave-4 UC script coverage audited `hoc/cus/ops` scope as:
  - `4` scripts total (`0 UC_LINKED`, `4 NON_UC_SUPPORT`, `0 UNLINKED` in target scope).
- This document remains focused on `fdr/ops`; Wave-4 note is retained as cross-domain coverage context.

## File Registry

### L2 APIs (`backend/app/hoc/api/fdr/ops/`)

**`cost_ops.py`**
- Role: founder cost intelligence API surface
- Delegation: L4 `OperationRegistry` operation `ops.cost`
- Methods used: `get_overview`, `get_anomalies`, `get_tenants`, `get_customer_drilldown`
- Boundary shape: thin L2 route pattern (expected topology-compliant path)

**`founder_actions.py`**
- Role: founder freeze/throttle/override + reversal + audit endpoints
- Delegation: uses `FounderActionWriteService` plus in-file SQL helper logic
- Boundary shape: currently mixed (L2 contains direct SQL/business logic)

**`retrieval_admin.py`**
- Role: founder retrieval-plane and evidence administration
- Delegation: L4 operations (`knowledge.planes.*`)
- Boundary shape: L2->L4 dispatch present, with L2 session type imports

### L5 Engines (`backend/app/hoc/fdr/ops/engines/`)

**`founder_action_write_engine.py`**
- Role: write engine for founder operational actions
- Delegates to: `founder_action_write_driver.py`
- Key methods: `create_founder_action()`, `mark_action_reversed()`, `commit()`, `rollback()`

**`ops_incident_engine.py`**
- Role: incident aggregation and severity classification from error-store facts
- Delegates to: `error_store.py` via `ErrorStoreProtocol`
- Key methods: `get_active_incidents()`, `get_incident_by_component()`, `get_incident_summary()`

**`founder_review.py`**
- Role: contract review queue + review decision flow
- Key exports: `ReviewDecisionRequest`, `get_contract_service()`, `get_eligible_contracts()`

### L5 Schemas (`backend/app/hoc/fdr/ops/schemas/`)

**`ops_domain_models.py`**
- Core domain models and enums:
  - `OpsIncident`, `OpsHealthSignal`, `OpsRiskFinding`, `OpsTrendMetric`, `OpsDecisionOutcome`
  - `OpsSeverity`, `OpsIncidentCategory`, `OpsHealthStatus`, `OpsRiskLevel`

**`ops.py`**
- Founder ops DTO catalog including:
  - incident/cost/founder action DTOs
  - auto-execute review DTOs

### L6 Drivers (`backend/app/hoc/fdr/ops/drivers/`)

**`error_store.py`**
- Error persistence/query adapter over infra store APIs.

**`founder_action_write_driver.py`**
- Pure DB writes for founder actions.

**`ops_write_driver.py`**
- Ops write operations (`OpsWriteService`).

**`event_emitter.py`**
- Structured founder ops event emission (`EventEmitter`).

### L2.1 Facades (`backend/app/hoc/fdr/ops/facades/`)

**`ops_facade.py`**
- Unified incident/error view facade for ops.

**`founder_review_adapter.py`**
- Converts review/contracts to founder-facing response views.

## Route and Operation Maps

### Founder Cost Ops (Topology-Compliant)

- `GET /ops/cost/overview` -> L4 `ops.cost` (`method=get_overview`)
- `GET /ops/cost/anomalies` -> L4 `ops.cost` (`method=get_anomalies`)
- `GET /ops/cost/tenants` -> L4 `ops.cost` (`method=get_tenants`)
- `GET /ops/cost/customers/{tenant_id}` -> L4 `ops.cost` (`method=get_customer_drilldown`)

### Founder UAT Console Route Map (Frontend)

- `website/app-shell/src/routes/index.tsx`:
  - `/${prefix}/uat` inside founder route set
  - rendered for both prefixes: `/prefops` and `/fops`

## Known Issues (Active)

- `founder_actions.py` contains direct SQL and business-condition logic in L2.
- `retrieval_admin.py` is partially compliant (dispatches to L4, but L2 boundary remains broader than ideal).
- Full canonical status remains pending until founder L2 surfaces are fully thin and topology-clean.
