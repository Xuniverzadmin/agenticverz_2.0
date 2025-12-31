# PIN-233: File Utilization Analysis - Customer Console UI

**Status:** REFERENCE
**Date:** 2025-12-28
**Category:** Product / UI Architecture
**Related:** PIN-170 (System Contracts), PIN-167 (Visibility Gaps)

---

## Summary

Comprehensive analysis of which codebase files are utilized for the 5-lens customer console UI concept versus internal/ops-only files. This establishes the product boundary and ensures constitutional constraints are respected.

---

## 5-Lens Customer Console UI Concept

### Lens Model (Validated)

| Lens | Original Name | Customer-Friendly | Purpose |
|------|---------------|-------------------|---------|
| 1 | Overview | **Posture** | System stance, freeze status, health |
| 2 | Activity | **Activity** | Worker runs, agent execution |
| 3 | Decisions | **Outcomes** | Effects, not mechanics (PB-S5) |
| 4 | Controls | **Guardrails** | Permissions, boundaries, policies |
| 5 | History | **Evidence** | Immutable audit trails, traces |

### Constitutional Constraints Enforced

- **"Decisions" renamed to "Outcomes"**: `customer_visibility.py` mandates "Show effects, not mechanics"
- **Predictions are advisory only**: PB-S5 contract in `prediction.py`
- **Cross-tenant aggregation is founder-only**: Discovery ledger excluded from customer UI
- **Learning gains clarity, not authority**: Per flywheel validation

---

## File Utilization Summary

| Category | File Count | Percentage | Product Usage |
|----------|------------|------------|---------------|
| **Customer-Facing** | 156 | 22% | Direct UI mapping |
| **Internal Infrastructure** | 171 | 24% | Backend support, not exposed |
| **Testing & CI/CD** | 374 | 54% | Development only |
| **Total** | **701** | 100% | |

---

## Files Utilized by Lens

### Posture Lens (12 files)

```
app/api/guard.py                    -> GuardStatus, TodaySnapshot
app/api/health.py                   -> System health indicators
app/api/customer_visibility.py      -> PreRunDeclaration, OutcomeReconciliation
app/api/v1_killswitch.py            -> Freeze status, system posture
app/auth/tier_gating.py             -> Tier-based visibility
app/models/killswitch.py            -> Killswitch state model
app/workflow/health.py              -> Workflow health status
app/stores/health.py                -> Health persistence
app/costsim/circuit_breaker.py      -> Circuit breaker status
app/integrations/cost_safety_rails.py -> Safety rail status
app/contracts/guard.py              -> Guard contracts
app/utils/guard_cache.py            -> Guard state caching
```

### Activity Lens (41 files)

```
app/api/workers.py                  -> Worker list, status
app/api/agents.py                   -> Agent management
app/api/traces.py                   -> Execution traces
app/api/runtime.py                  -> Runtime status
app/workflow/*.py (12 files)        -> Workflow execution visibility
app/worker/*.py (9 files)           -> Worker run status
app/agents/*.py (18 files)          -> Agent activity
app/skill_http.py                   -> Skill execution status
```

### Outcomes Lens (18 files)

```
app/api/feedback.py                 -> Pattern feedback (read-only)
app/api/predictions.py              -> Advisory predictions (PB-S5)
app/api/cost_intelligence.py        -> Cost outcomes
app/api/cost_ops.py                 -> Cost operation results
app/models/feedback.py              -> Feedback data model
app/models/prediction.py            -> Prediction data model
app/routing/feedback.py             -> Routing outcomes
app/learning/__init__.py            -> Learning outcomes (observe only)
app/learning/suggestions.py         -> Suggestion outcomes
app/services/prediction.py          -> Prediction service (advisory)
app/predictions/*.py (2 files)      -> Prediction API
app/integrations/learning_proof.py  -> Learning proof visibility
app/integrations/graduation_engine.py -> Graduation status
```

### Guardrails Lens (32 files)

```
app/api/policy_proposals.py         -> Policy proposals (read-only, PB-S4)
app/api/policy.py                   -> Policy visibility
app/api/policy_layer.py             -> Policy layer abstraction
app/policy/*.py (15 files)          -> Policy engine visibility
app/auth/rbac.py                    -> Permission structure
app/auth/rbac_engine.py             -> RBAC visibility
app/auth/tier_gating.py             -> Tier constraints
app/optimization/*.py (7 files)     -> Optimization envelope status
app/models/policy.py                -> Policy data model
app/services/policy_proposal.py     -> Proposal status
app/services/policy_violation_service.py -> Violation visibility
```

### Evidence Lens (23 files)

```
app/api/status_history.py           -> Historical status
app/traces/*.py (8 files)           -> Immutable trace evidence
app/optimization/audit_persistence.py -> Audit trails
app/auth/shadow_audit.py            -> Shadow audit logs
app/costsim/provenance.py           -> Cost provenance
app/costsim/provenance_async.py     -> Async provenance
app/runtime/replay.py               -> Replay evidence
app/runtime/failure_catalog.py      -> Failure catalog (descriptive)
app/integrations/cost_snapshots.py  -> Historical cost snapshots
app/utils/deterministic.py          -> Determinism proofs
```

### Cross-Cutting (30 files)

```
app/auth/*.py (13 files)            -> Authentication for all lenses
app/schemas/*.py (5 files)          -> Data schemas
app/models/*.py (8 files)           -> Database models
app/main.py                         -> Entry point
app/auth.py                         -> Auth handler
```

**Total Customer-Facing: 156 files**

---

## Files NOT Utilized for Customer UI

### Internal Infrastructure (51 files)

```
NEVER EXPOSED TO CUSTOMERS:

app/db.py, db_async.py, db_helpers.py   -> Database internals
app/middleware/*.py (4 files)            -> Request handling internals
app/config/*.py (3 files)                -> Configuration internals
app/secrets/*.py (2 files)               -> Secret management
app/events/*.py (3 files)                -> Event bus internals
app/storage/*.py (2 files)               -> Storage layer
app/stores/checkpoint_offload.py         -> Checkpoint internals
app/observability/cost_tracker.py        -> Internal cost tracking
app/utils/*.py (13 files)                -> Internal utilities
app/logging_config.py                    -> Logging setup
app/metrics.py                           -> Internal metrics
app/cli.py                               -> CLI tools (dev only)
```

### Founder/Ops Only (20 files)

```
FOUNDER/OPS ONLY (per constitutional constraints):

app/discovery/ledger.py             -> Cross-tenant signal ledger
app/services/pattern_detection.py   -> Pattern detection engine
app/jobs/failure_aggregation.py     -> Chaos corpus aggregation
app/jobs/graduation_evaluator.py    -> Graduation evaluation
app/services/incident_aggregator.py -> Cross-tenant incidents
app/api/founder_actions.py          -> Founder action endpoints
app/api/founder_timeline.py         -> Founder timeline data
app/api/ops.py                      -> Ops console endpoints
app/api/discovery.py                -> Discovery endpoints (internal)
app/api/recovery.py                 -> Recovery endpoints (ops)
app/api/recovery_ingest.py          -> Recovery ingestion (ops)
app/services/recovery_*.py (3 files) -> Recovery internals
app/services/orphan_recovery.py     -> Orphan recovery
app/tasks/recovery_*.py (2 files)   -> Recovery tasks
```

### Background Services (30 files)

```
INTERNAL PROCESSING (no customer visibility):

app/services/*.py (20 files)        -> Business logic services
app/jobs/*.py (4 files)             -> Background jobs
app/tasks/*.py (4 files)            -> Async tasks
app/worker/outbox_processor.py      -> Outbox processing
app/costsim/alert_worker.py         -> Alert generation
```

### Testing & CI/CD (374 files)

```
DEVELOPMENT ONLY:

tests/*.py (146 files)              -> Unit/integration tests
alembic/*.py (65 files)             -> Database migrations
scripts/ops/*.py (48 files)         -> Operations scripts
scripts/*.sh (112 files)            -> Shell scripts
ops/*.py (1 file)                   -> Ops utilities
ops/*.sh (2 files)                  -> Ops shell scripts
```

### Legacy/Stubs (10 files)

```
DEPRECATED/TESTING:

app/api/legacy_routes.py            -> Legacy routes
app/skills/stubs/*.py (4 files)     -> Test stubs
app/planners/stub_adapter.py        -> Stub planner
app/planner/stub_planner.py         -> Stub implementation
```

---

## Utilization Matrix by Lens

| Lens | Files Used | Files NOT Used (in scope) | Notes |
|------|------------|---------------------------|-------|
| Posture | 12 | 0 | All relevant files utilized |
| Activity | 41 | 4 | Internal workers, outbox excluded |
| Outcomes | 18 | 8 | Pattern detection, aggregation excluded |
| Guardrails | 32 | 3 | Policy internals excluded |
| Evidence | 23 | 2 | Internal replay mechanics excluded |
| Cross-Cutting | 30 | 51 | Infrastructure layer excluded |

---

## Constitutional Boundaries

### Correctly Excluded from Customer UI

| File | Reason | Constitutional Basis |
|------|--------|---------------------|
| `discovery/ledger.py` | Cross-tenant signals | Founder-only aggregation |
| `pattern_detection.py` | Chaos corpus | Observational, not exposed |
| `founder_actions.py` | Founder actions | Tier-gated to founder |
| `founder_timeline.py` | Founder timeline | Tier-gated to founder |
| `failure_aggregation.py` | Pattern accumulation | Internal learning |
| `incident_aggregator.py` | Cross-tenant incidents | Founder-only |

### PB Contract Compliance

| Contract | Enforcement | Files Affected |
|----------|-------------|----------------|
| PB-S3 | Feedback is observational | `pattern_detection.py` internal |
| PB-S4 | Policies proposed, never auto-enforced | `policy_proposals.py` read-only |
| PB-S5 | Predictions advisory only | `predictions.py`, `prediction.py` |

---

## Recommendations

### High Priority

1. **Map all 156 customer files to API endpoints** - Verify API parity exists
2. **Audit 171 internal files** - Ensure no accidental customer exposure
3. **Consolidate versioned files** - `v1`/`v2` sprawl creates confusion

### Consolidation Candidates

| Files | Recommendation |
|-------|----------------|
| `db.py` + `db_async.py` + `db_helpers.py` | Merge into single module |
| `circuit_breaker.py` + `circuit_breaker_async.py` | Merge |
| `provenance.py` + `provenance_async.py` | Merge |
| `registry.py` + `registry_v2.py` | Version consolidation |
| `llm_invoke.py` + `llm_invoke_v2.py` | Version consolidation |

### Legacy Removal Candidates

| File | Status |
|------|--------|
| `api/legacy_routes.py` | Review for removal |
| `skills/stubs/*.py` | Keep for testing only |
| `planners/stub_adapter.py` | Keep for testing only |

---

## Directory Structure Reference

```
/root/agenticverz2.0/backend/app/     [327 .py files]
├── agents/             [18 files - Agent framework]
├── api/                [28 files - REST API endpoints]
├── auth/               [13 files - Authentication & RBAC]
├── config/             [3 files - Configuration]
├── contracts/          [4 files - Data contracts]
├── costsim/            [16 files - Cost simulation]
├── discovery/          [2 files - Service discovery]
├── events/             [3 files - Event system]
├── integrations/       [11 files - Third-party]
├── jobs/               [4 files - Background jobs]
├── learning/           [4 files - ML learning]
├── memory/             [8 files - Memory management]
├── middleware/         [4 files - Request middleware]
├── models/             [8 files - Database models]
├── observability/      [1 file - Observability]
├── optimization/       [7 files - Optimization]
├── planner/            [3 files - Planning interface]
├── planners/           [3 files - LLM planners]
├── policy/             [15 files - Policy engine]
├── predictions/        [2 files - Prediction API]
├── routing/            [6 files - Routing engine]
├── runtime/            [2 files - Runtime utilities]
├── schemas/            [5 files - Data schemas]
├── secrets/            [2 files - Secret management]
├── services/           [20 files - Business logic]
├── skills/             [24 files - Skill implementations]
├── storage/            [2 files - Storage layer]
├── stores/             [3 files - Persistence stores]
├── tasks/              [4 files - Background tasks]
├── traces/             [8 files - Tracing]
├── utils/              [13 files - Utilities]
├── worker/             [9 files - Worker system]
├── workers/            [11 files - Worker implementations]
└── workflow/           [12 files - Workflow engine]
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-28 | Initial creation - File utilization analysis for 5-lens customer console |

---

## References

- UI Concept Review (conversation)
- `app/api/customer_visibility.py` - "Show effects, not mechanics"
- `app/services/prediction.py` - PB-S5 contract
- `app/api/policy_proposals.py` - PB-S4 contract
- `app/discovery/ledger.py` - Discovery ledger (founder-only)
