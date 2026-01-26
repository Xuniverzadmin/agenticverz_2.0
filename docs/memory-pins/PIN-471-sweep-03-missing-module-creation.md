# PIN-471: SWEEP-03 Missing Module Creation

**Status:** 📋 ACTIVE
**Created:** 2026-01-25
**Category:** HOC Migration / Module Creation

---

## Summary

Created HOC modules for missing symbols imported by HOC files. Batch 1: LimitEnforcer, UsageMonitor, RunSignalService. Batch 2: LimitsSimulationService, CusEnforcementService, CusTelemetryService. Reduced MISSING_HOC_MODULE from 10 to 4.

---

## Details

## SWEEP-03: Missing Module Creation

### Invariant
Every non-deprecated symbol imported by ≥1 HOC file must have a HOC module with an explicit contract.

### Batches Completed

#### Batch 1 (CLOSED 2026-01-25)
| Module | Layer | Location | Callers |
|--------|-------|----------|---------|
| LimitEnforcer | L5 | policies/L5_engines/limit_enforcer*.py | limit_hook.py (×2) |
| UsageMonitor | L5 | policies/L5_engines/usage_monitor*.py | limit_hook.py (×2) |
| RunSignalService | L6 | activity/L6_drivers/run_signal_service.py | threshold_driver.py, llm_threshold_driver.py |

#### Batch 2 (CLOSED 2026-01-25)
| Module | Layer | Location | Callers |
|--------|-------|----------|---------|
| LimitsSimulationService | L5 | policies/L5_engines/limits_simulation_service.py | simulate.py |
| CusEnforcementService | L5 | policies/L5_engines/cus_enforcement_service.py | cus_enforcement.py |
| CusTelemetryService | L5 | integrations/L5_engines/cus_telemetry_service.py | cus_telemetry.py |

### Metrics
- MISSING_HOC_MODULE: 10 → 7 (Batch 1) → 4 (Batch 2)

### Remaining (Future Batches)
- PlatformHealthService (L4 runtime semantics)
- CusIntegrationService (cross-domain coupling)
- PoliciesFacade (needs decision sweep)
- AuditLedgerService (sync)

### Documentation
- docs/architecture/hoc/SWEEP_03_MISSING_MODULE_CREATION.md
- docs/architecture/hoc/SWEEP_03_BATCH_2_LOCK.md
---

## Updates

### Update (2026-01-25)

## 2026-01-25: Batch 3 Complete

### Modules Migrated

| Module | HOC Location | Type | Caller Wired |
|--------|--------------|------|--------------|
| CusIntegrationService | `integrations/L5_engines/cus_integration_service.py` | Re-export wrapper | `integrations_facade.py` |
| PoliciesFacade | `policies/L5_engines/policies_facade.py` | Re-export wrapper | `policies.py` |
| AuditLedgerService | `logs/L5_engines/audit_ledger_service.py` | New implementation | `incident_write_engine.py` |

### Key Decisions

- **AuditLedgerService**: Required creating new sync implementation (source at `app.services.logs.audit_ledger_service` didn't exist). Provides `incident_acknowledged`, `incident_resolved`, `incident_manually_closed` methods.
- **PoliciesFacade**: Re-exports all 20+ result types plus facade class from legacy location.
- **CusIntegrationService**: Re-exports from existing `cus_integration_engine.py`.

### Metrics

| Metric | Batch 1 | Batch 2 | Batch 3 | Remaining |
|--------|---------|---------|---------|-----------|
| MISSING_HOC_MODULE | 10→7 | 7→4 | 4→1 | 1 |

### Remaining Work

- **Batch 4**: PlatformHealthService (L4 runtime semantics, requires separate design)

### Lock Document

`docs/architecture/hoc/SWEEP_03_BATCH_3_LOCK.md` - Status: CLOSED
