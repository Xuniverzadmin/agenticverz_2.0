# Ops — Software Bible (DRAFT)

**Domain:** ops (fdr/ops + founder validation surface)  
**Status:** DRAFT — canonicalization in progress  
**L2 Features:** 3 backend founder routers + founder UAT route  
**Scripts:** 2 operational gate/hygiene scripts in active use  
**Updated:** 2026-02-15  
**References:** PIN-564, PIN-565, PIN-566

---

## Reality Delta (2026-02-15, UAT Hardening Closure)

- UC/UAT closure artifacts are complete (`PIN-564`, `PIN-565`) and ops founder route now includes UAT console under `/prefops/uat` and `/fops/uat`.
- Playwright determinism hardening landed:
  - host/port normalized to `127.0.0.1:5173`
  - explicit `cwd` in both BIT and UAT Playwright configs
- UAT gate hardening landed:
  - blocking `typecheck:uat`, non-blocking global typecheck debt report
  - explicit preflight for Playwright Chromium browser binary with actionable remediation
- UI hygiene checker now recognizes dynamic imports for orphan-page detection (prevents lazy-route false positives).

## Reality Delta (2026-02-20, CI Scope Split and Tombstone Ledger)

- CI baseline remediation scope was constrained to `backend/app/hoc/**` for active blocker closure.
- Non-`hoc/*` legacy debt is tombstoned and tracked in:
  - `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
- Guard/workflow scope updates:
  - `scripts/ops/layer_segregation_guard.py` supports `--scope hoc`
  - `.github/workflows/layer-segregation.yml` runs HOC-scoped enforcement
  - `.github/workflows/import-hygiene.yml` relative-import and hygiene checks are HOC-scoped
  - `.github/workflows/capability-registry.yml` capability-linkage changed-file selection is HOC-scoped for backend python

## Reality Delta (2026-02-12, Wave-4 Script Coverage Audit)

- Wave-4 UC script coverage audited `hoc/cus/ops` scope as:
  - `4` scripts total (`0 UC_LINKED`, `4 NON_UC_SUPPORT`, `0 UNLINKED` in target scope).
- This file documents `fdr/ops`; the Wave-4 note above remains CUS-scope coverage context.

## Layer Inventory

### L5 Engines (`backend/app/hoc/fdr/ops/engines/`)

| File | Role | Key Exports |
|------|------|-------------|
| `founder_action_write_engine.py` | Write engine for founder ops actions | `FounderActionWriteService` |
| `founder_review.py` | Founder contract review engine | `ReviewDecisionRequest`, `get_contract_service()`, `get_eligible_contracts()` |
| `ops_incident_engine.py` | Incident aggregation and classification | `OpsIncidentService`, `ErrorStoreProtocol`, `IncidentAggregationConfig` |

### L5 Schemas (`backend/app/hoc/fdr/ops/schemas/`)

| File | Role | Key Exports |
|------|------|-------------|
| `ops.py` | DTO surface for founder ops | `SystemPulseDTO`, `FounderActionRequestDTO`, `FounderActionResponseDTO`, `AutoExecuteReview*DTO` |
| `ops_domain_models.py` | Core ops domain models | `OpsIncident`, `OpsHealthSignal`, `OpsRiskFinding`, `OpsSeverity`, `OpsIncidentCategory` |

### L6 Drivers (`backend/app/hoc/fdr/ops/drivers/`)

| File | Role | Key Exports |
|------|------|-------------|
| `error_store.py` | Error persistence and query adapter | `DatabaseErrorStore` |
| `event_emitter.py` | Domain event emission | `EventType`, `EntityType`, `OpsEvent`, `EventEmitter` |
| `founder_action_write_driver.py` | Founder action DB operations | `FounderActionWriteDriver` |
| `ops_write_driver.py` | Ops write operations | `OpsWriteService` |

### L2.1 Facades (`backend/app/hoc/fdr/ops/facades/`)

| File | Role | Key Exports |
|------|------|-------------|
| `ops_facade.py` | Unified ops access facade | `OpsFacade`, `get_ops_facade()` |
| `founder_review_adapter.py` | Review queue view adapter | `FounderReviewAdapter`, `FounderContractSummaryView` |

### L2 APIs (`backend/app/hoc/api/fdr/ops/`)

| File | Role | Key Exports |
|------|------|-------------|
| `cost_ops.py` | Founder cost-intelligence endpoints | `GET /ops/cost/overview`, `/anomalies`, `/tenants`, `/customers/{tenant_id}` |
| `founder_actions.py` | Founder action endpoints | `POST /ops/actions/*`, reversal endpoints, audit endpoints |
| `retrieval_admin.py` | Founder retrieval-plane admin endpoints | `GET/POST /retrieval/planes*`, policy bind/unbind, evidence listing |

## UAT Validation Surface (Founder)

| Artifact | Role |
|----------|------|
| `website/app-shell/src/routes/index.tsx` | Registers founder UAT route (`/prefops/uat`, `/fops/uat`) |
| `website/app-shell/src/features/uat/UcUatConsolePage.tsx` | UAT console page |
| `website/app-shell/tests/uat/playwright.config.ts` | Deterministic UAT Playwright runtime (`127.0.0.1:5173`, explicit `cwd`) |
| `website/app-shell/tests/bit/playwright.config.ts` | Deterministic BIT runtime (`127.0.0.1:5173`, explicit `cwd`) |
| `backend/scripts/ops/hoc_uc_validation_uat_gate.sh` | Unified backend+frontend UAT gate with browser preflight |
| `website/app-shell/scripts/ui-hygiene-check.cjs` | UI hygiene gate; now dynamic-import aware for orphan detection |

## Known Gaps (Architecture Truth)

- `cost_ops.py` is correctly L2->L4 (`ops.cost`).
- `founder_actions.py` currently includes direct SQL and action logic in L2 (not strict thin-boundary shape).
- `retrieval_admin.py` dispatches via L4 operations but imports SQLAlchemy session types directly at L2.
- Ops domain documentation remains draft until all founder L2 routes fully satisfy thin-boundary constraints.
