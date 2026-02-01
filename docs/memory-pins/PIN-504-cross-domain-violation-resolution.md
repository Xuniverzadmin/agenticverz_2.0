# PIN-504 — Cross-Domain Violation Resolution (Loop Model)

**Status:** COMPLETE
**Date:** 2026-01-31
**Category:** Architecture / HOC Migration
**Depends On:** PIN-503 (Cleansing Cycle), PIN-487 (Loop Model), PIN-484 (HOC Topology V2.0.0)
**Blocks:** None (final violation resolution phase)

---

## Purpose

Resolve 14 cross-domain import violations identified during PIN-503 cleansing cycle. Uses the Loop Model (PIN-487) C4 Coordinator pattern to mediate cross-domain operations without violating layer topology constraints.

---

## Violation Categories Addressed

| Category | Description | Count | Resolution |
|----------|-------------|-------|------------|
| Cross-domain L5→L5 (audit) | incidents/policies importing logs audit services | 4 | Dependency injection via L4 handlers + AuditCoordinator |
| Cross-domain L6→L6 (signal) | controls importing activity run_signal_driver | 2 | SignalCoordinator (L4) mediates dual emission |
| Cross-domain L3→L5 (logs) | integrations adapter importing logs engine | 1 | LogsCoordinator (L4) spine passthrough |
| L2→L5 engine imports | aos_accounts.py importing L5 engine types | 7 | Moved types to L5_schemas (legal for L2) |

**Total violations resolved:** 14

---

## Phase 1: Shared Types Extraction

Extracted cross-domain data types to neutral locations so multiple domains can import without violations.

### Files Created

| File | Contents |
|------|----------|
| `hoc/cus/account/L5_schemas/result_types.py` | `AccountsErrorResult` dataclass |
| `hoc/cus/hoc_spine/schemas/threshold_types.py` | `LimitSnapshot` frozen dataclass |

### Files Modified

| File | Change |
|------|--------|
| `account/L5_engines/accounts_facade.py` | Re-exports `AccountsErrorResult` from `L5_schemas.result_types` |
| `account/L5_schemas/__init__.py` | Added `AccountsErrorResult` export |
| `controls/L6_drivers/threshold_driver.py` | Re-exports `LimitSnapshot` from `hoc_spine.schemas.threshold_types` |
| `activity/L6_drivers/__init__.py` | Imports `LimitSnapshot` from spine (removed all controls re-exports) |

---

## Phase 2: Audit Coordinator (4 violations)

Created `AuditCoordinator` (C4) to mediate audit dispatch between incidents/policies and logs domains.

**Pattern:** L4 handler creates audit service → injects into L5 engine constructor → engine calls audit inside transaction block (atomicity preserved).

### Files Created

| File | Purpose |
|------|---------|
| `hoc_spine/orchestrator/coordinators/__init__.py` | Coordinator package init |
| `hoc_spine/orchestrator/coordinators/audit_coordinator.py` | Cross-domain audit dispatch (sync + async) |

### Files Modified

| File | Change |
|------|--------|
| `incidents/L5_engines/incident_write_engine.py` | Removed `AuditLedgerService` import; accepts `audit: Any = None` via injection |
| `policies/L5_engines/policy_limits_engine.py` | Removed `AuditLedgerServiceAsync` import; accepts `audit: Any = None` |
| `policies/L5_engines/policy_rules_engine.py` | Same pattern |
| `policies/L5_engines/policy_proposal_engine.py` | Same pattern |
| `hoc_spine/orchestrator/handlers/incidents_handler.py` | Added `IncidentsWriteHandler` with audit injection |
| `hoc_spine/orchestrator/handlers/policies_handler.py` | Limits/Rules handlers inject audit |

### Violations Resolved

| # | Domain | File | Removed Import |
|---|--------|------|---------------|
| 1 | incidents | `incident_write_engine.py` | `app.hoc.cus.logs.L5_engines.audit_ledger_service` |
| 2 | policies | `policy_limits_engine.py` | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` |
| 3 | policies | `policy_rules_engine.py` | Same |
| 4 | policies | `policy_proposal_engine.py` | Same |

---

## Phase 3: Signal Coordinator (2 violations)

Created `SignalCoordinator` (C4) to mediate threshold signal emission between controls and activity domains.

### Files Created

| File | Purpose |
|------|---------|
| `hoc_spine/orchestrator/coordinators/signal_coordinator.py` | Dual emission: ops_events (controls) + runs.risk_level (activity) |

### Files Modified

| File | Change |
|------|--------|
| `controls/L6_drivers/threshold_driver.py` | `emit_and_persist_threshold_signal` delegates to `SignalCoordinator` |
| `activity/L6_drivers/__init__.py` | Removed `ThresholdDriver`, `ThresholdDriverSync`, signal emission re-exports |

### Violations Resolved

| # | Domain | File | Removed Import |
|---|--------|------|---------------|
| 1 | controls | `threshold_driver.py` | `app.hoc.cus.activity.L6_drivers.run_signal_driver` |
| 2 | activity | `__init__.py` | All `app.hoc.cus.controls` re-exports |

---

## Phase 4: Logs Coordinator (1 violation)

Created `LogsCoordinator` (C4) as thin spine passthrough for logs read service access.

### Files Created

| File | Purpose |
|------|---------|
| `hoc_spine/orchestrator/coordinators/logs_coordinator.py` | `get_logs_read_service_via_spine()` |

### Files Modified

| File | Change |
|------|--------|
| `integrations/adapters/customer_logs_adapter.py` | Routes through `logs_coordinator` instead of direct logs L5 import |

---

## Phase 5: L2 Type-Checking Fix (7 violations)

### Files Modified

| File | Change |
|------|--------|
| `api/cus/policies/aos_accounts.py` | All 7 `AccountsErrorResult` imports changed from `L5_engines.accounts_facade` to `L5_schemas.result_types` |

---

## Architecture Summary

### New Coordinator Pattern (C4 Loop Model)

```
L2 API → L4 Handler → L5 Engine (with injected dependencies)
                   ↘ L4 Coordinator → L5/L6 (cross-domain, lazy import)
```

### Files Created (6 total)

1. `backend/app/hoc/cus/account/L5_schemas/result_types.py`
2. `backend/app/hoc/cus/hoc_spine/schemas/threshold_types.py`
3. `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/__init__.py`
4. `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/audit_coordinator.py`
5. `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/signal_coordinator.py`
6. `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/logs_coordinator.py`

### Files Modified (12 total)

1. `account/L5_engines/accounts_facade.py`
2. `account/L5_schemas/__init__.py`
3. `controls/L6_drivers/threshold_driver.py`
4. `activity/L6_drivers/__init__.py`
5. `incidents/L5_engines/incident_write_engine.py`
6. `policies/L5_engines/policy_limits_engine.py`
7. `policies/L5_engines/policy_rules_engine.py`
8. `policies/L5_engines/policy_proposal_engine.py`
9. `hoc_spine/orchestrator/handlers/incidents_handler.py`
10. `hoc_spine/orchestrator/handlers/policies_handler.py`
11. `integrations/adapters/customer_logs_adapter.py`
12. `api/cus/policies/aos_accounts.py`

---

## Phase 6: Categories D+E — L2 Bypass + Cross-Domain Violations (24 violations)

Resolved 14 remaining violations across 4 domains. 10 recovery-domain violations deferred to PIN-505.

### Phase 6a: Re-export Cleanup (2 violations)

| # | Domain | File | Violation | Fix |
|---|--------|------|-----------|-----|
| 1 | account | `L6_drivers/__init__.py` | Re-exports `WorkerRegistryService` from integrations L6 | Deleted import block |
| 2 | activity | `L5_engines/__init__.py` | Re-exports 12 symbols from controls L5 | Deleted import block |

### Phase 6b: Type Extractions to L5_schemas (3 violations)

| # | L2 File | Old Import (L5/L6) | New Import (L5_schemas) | Types Moved |
|---|---------|--------------------|-----------------------|-------------|
| 1 | `policies/analytics.py` | `analytics/L5_engines/analytics_facade` | `analytics/L5_schemas/query_types` | `ResolutionType`, `ScopeType` |
| 2 | `policies/guard.py` | `logs/L5_engines/replay_determinism` | `logs/L5_schemas/determinism_types` | `DeterminismLevel` |
| 3 | `policies/override.py` | `controls/L6_drivers/override_driver` | `controls/L5_schemas/override_types` | 5 error classes |

### Phase 6c: L2→L6 Bypass Resolution (3 violations)

| # | L2 File | Old Pattern | New Pattern |
|---|---------|------------|-------------|
| 1 | `incidents/incidents.py` (3 endpoints) | Direct `export_bundle_driver` L6 import | L4 `incidents.export` handler |
| 2 | `policies/override.py` (4 endpoints) | Direct `LimitOverrideService` L6 import | L4 `controls.overrides` handler |
| 3 | `policies/workers.py` (2 probes) | Direct `RecoveryMatcher` L6 import | L5 `RecoveryEvaluationEngine` |

### Phase 6d: Cross-Domain L5→L5/L6 Resolution (6 violations)

| # | Source File | Old Import | Resolution |
|---|------------|-----------|------------|
| 1 | `incidents/incident_engine.py` | `policies.L5_engines.lessons_engine` | LessonsCoordinator (L4) injected as `evidence_recorder` |
| 2 | `policies/lessons_engine.py` | `incidents.L6_drivers.lessons_driver` | Lazy import inside `_get_driver()` |
| 3 | `policies/policies_limits_query_engine.py` | `controls.L6_drivers.limits_read_driver` | Lazy import inside factory |
| 4 | `policies/policy_limits_engine.py` | `controls.L6_drivers.policy_limits_driver` | Lazy import inside constructor |
| 5 | `policies/recovery_evaluation_engine.py` | `incidents.L5_engines.recovery_rule_engine` | Moved pure functions to `hoc_spine/schemas/recovery_decisions.py` |
| 6 | `policies/L6_drivers/__init__.py` | `controls.L6_drivers.limits_read_driver` | Deleted re-export block |

### Phase 6e: Cleanup

| # | Action | File |
|---|--------|------|
| 1 | Deleted deprecated shim | `policies/L5_engines/keys_shim.py` |
| 2 | Absorbed into DomainBridge | `hoc_spine/orchestrator/coordinators/logs_coordinator.py` |

### Files Created (Phase 6)

| # | Path | Purpose |
|---|------|---------|
| 1 | `scripts/ops/hoc_cross_domain_validator.py` | Progressive enforcement (5 rules, --ci mode) |
| 2 | `hoc_spine/orchestrator/coordinators/lessons_coordinator.py` | incidents→policies evidence recording |
| 3 | `hoc_spine/orchestrator/coordinators/domain_bridge.py` | Cross-domain service accessor |
| 4 | `analytics/L5_schemas/query_types.py` | `ResolutionType`, `ScopeType` enums |
| 5 | `logs/L5_schemas/determinism_types.py` | `DeterminismLevel` enum |
| 6 | `controls/L5_schemas/override_types.py` | Override error classes |
| 7 | `hoc_spine/schemas/recovery_decisions.py` | Pure recovery decision functions |

### Files Deleted (Phase 6)

| # | Path | Reason |
|---|------|--------|
| 1 | `policies/L5_engines/keys_shim.py` | Deprecated, zero callers |
| 2 | `hoc_spine/orchestrator/coordinators/logs_coordinator.py` | Absorbed into DomainBridge |

### Validator Baseline

Cross-domain validator (`hoc_cross_domain_validator.py --ci`) reports **0 violations** (excluding recovery domain, deferred to PIN-505).

---

## What This PIN Does NOT Address

- L5→L4 reaching-up violations (3 files) — requires event/callback pattern, separate PIN
- TODO stubs from PIN-503 — requires HOC-native implementations
- Recovery domain L2→L6 bypass (8 violations) — deferred to PIN-505, INTERNAL/Founder API only
