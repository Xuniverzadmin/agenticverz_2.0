# SWEEP-03: Batch 3 Lock

**Status:** CLOSED
**Effective:** 2026-01-25
**Predecessor:** SWEEP-03 Batch 2 (CLOSED)

---

## Batch 3 Closure

> **Status: CLOSED**
> CusIntegrationService, PoliciesFacade, and AuditLedgerService created with HOC modules.
> All declared callers wired.
> Remaining 1 missing module (PlatformHealthService) deferred to subsequent batch.

### Batch 3 Deliverables

| Module | HOC Location | Callers Wired |
|--------|--------------|---------------|
| CusIntegrationService | `integrations/L5_engines/cus_integration_service.py` | `integrations_facade.py` |
| PoliciesFacade | `policies/L5_engines/policies_facade.py` | `policies.py` |
| AuditLedgerService | `logs/L5_engines/audit_ledger_service.py` | `incident_write_engine.py` |

### Batch 3 Metrics

| Metric | Before | After |
|--------|--------|-------|
| MISSING_HOC_MODULE | 4 | 1 |

### Implementation Notes

- **CusIntegrationService**: Re-export wrapper from `app.services.cus_integration_engine`
- **PoliciesFacade**: Re-export wrapper from `app.services.policies_facade`
- **AuditLedgerService**: New sync implementation (source didn't exist)

---

**Continuation:** See future `SWEEP_03_BATCH_4_LOCK.md` for PlatformHealthService

---

## Invariant (UNCHANGED — LOCKED)

> **Every non-deprecated symbol imported by ≥1 HOC file must have a HOC module with an explicit contract.**

---

## Metric

`MISSING_HOC_MODULE` count

**Target:** Reduced from 4 to 1 (this batch of 3 modules)

---

## Scope: Batch 3 (3 Modules)

| Order | Module | Layer | Location | Callers |
|-------|--------|-------|----------|---------|
| 1 | **CusIntegrationService** | L5 | `app.hoc.cus.integrations.L5_engines.cus_integration_service` | `integrations_facade.py` |
| 2 | **PoliciesFacade** | L5 | `app.hoc.cus.policies.L5_engines.policies_facade` | `policies.py` |
| 3 | **AuditLedgerService** | L5 | `app.hoc.cus.logs.L5_engines.audit_ledger_service` | `incident_write_engine.py` |

### Import Details

| Module | Current Import | Target Import |
|--------|----------------|---------------|
| CusIntegrationService | `from app.services.cus_integration_engine import CusIntegrationService` | `from app.hoc.cus.integrations.L5_engines.cus_integration_service import ...` |
| PoliciesFacade | `from app.services.policies_facade import get_policies_facade` | `from app.hoc.cus.policies.L5_engines.policies_facade import ...` |
| AuditLedgerService | `from app.services.logs.audit_ledger_service import AuditLedgerService` | `from app.hoc.cus.logs.L5_engines.audit_ledger_service import ...` |

---

## Explicitly NOT in Batch 3

| Module | Reason |
|--------|--------|
| PlatformHealthService | L4 runtime semantics (separate sweep) |

---

## Execution Protocol (Per Module)

```
1. DEFINE contract first (or re-export wrapper)
2. CREATE minimal implementation
3. WIRE existing callers
4. STOP
```

---

## Out of Scope (LOCKED)

| Item | Reason |
|------|--------|
| Refactoring callers | Separate sweep |
| Performance optimization | Premature |
| Authority rules (TIME/TX/orchestration) | Different invariant |
| Behavior expansion | Contract creep |

---

## Stop Conditions

This batch is COMPLETE when:

1. All 3 modules have HOC implementations
2. All callers are wired to HOC paths
3. `MISSING_HOC_MODULE` count = 1 (reduced by 3)

---

## Approval Gate

> **Do not execute until human validation received.**
>
> Validation phrase: "Sweep-03 Batch-3 lock validated. Begin execution."
