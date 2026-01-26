# SWEEP-03: Missing Module Creation

**Status:** CLOSED (Batch 1)
**Effective:** 2026-01-25
**Predecessor:** SWEEP-02A (CLOSED)

---

## Batch 1 Closure

> **Status: CLOSED (Batch 1)**
> LimitEnforcer, UsageMonitor, and RunSignalService created with minimal contracts and implementations.
> All declared callers wired.
> Remaining missing modules deferred to subsequent batches.

### Batch 1 Deliverables

| Module | Files Created | Callers Wired |
|--------|---------------|---------------|
| LimitEnforcer | `limit_enforcer_contract.py`, `limit_enforcer.py` | `limit_hook.py` (×2) |
| UsageMonitor | `usage_monitor_contract.py`, `usage_monitor.py` | `limit_hook.py` (×2) |
| RunSignalService | `run_signal_service.py` | `threshold_driver.py`, `llm_threshold_driver.py` |

### Batch 1 Metrics

| Metric | Before | After |
|--------|--------|-------|
| MISSING_HOC_MODULE | 10 | 7 |

---

**Continuation:** See `SWEEP_03_BATCH_2_LOCK.md` for remaining modules

---

## Invariant

> **Every non-deprecated symbol imported by ≥1 HOC file must have a HOC module with an explicit contract.**

---

## Metric

`MISSING_HOC_MODULE` count

**Target:** Reduce from 10 to 7 (first batch of 3 modules)

---

## Scope: First Batch (3 Modules)

| Module | Gap ID | Location | Callers |
|--------|--------|----------|---------|
| **LimitEnforcer** | GAP-055 | `app.hoc.int.policies.L5_engines.limit_enforcer` | `limit_hook.py` |
| **UsageMonitor** | GAP-053 | `app.hoc.int.policies.L5_engines.usage_monitor` | `limit_hook.py` |
| **RunSignalService** | - | `app.hoc.cus.activity.L6_drivers.run_signal_service` | `threshold_driver.py`, `llm_threshold_driver.py` |

### Selection Rationale

1. **LimitEnforcer + UsageMonitor**: Both documented as formal gaps (GAP-053, GAP-055), both called from same file, logical pair
2. **RunSignalService**: Simple L6 driver, 2 callers, clear boundary (activity domain)

---

## Execution Protocol (Per Module)

```
1. DEFINE contract first
   - Interface (class/function signatures)
   - Inputs (types, validation)
   - Outputs (return types)
   - Dependencies (what it imports)

2. CREATE minimal implementation
   - Stub if behavior unclear
   - Real if behavior documented
   - NO expansion beyond contract

3. WIRE existing callers
   - Update import path
   - Add migration comment
   - Verify no runtime errors

4. STOP
   - Do not refactor caller
   - Do not add features
   - Do not consolidate with other modules
```

---

## In Scope

- Creating NEW HOC modules (3 specified above)
- Defining minimal contracts
- Wiring existing callers to new modules
- Adding standard HOC headers

---

## Out of Scope (LOCKED)

| Item | Reason |
|------|--------|
| Refactoring callers | Separate sweep |
| Performance optimization | Premature |
| Authority rules (TIME/TX/orchestration) | Different invariant |
| Raw SQL changes | Different invariant |
| Founder (fdr/) tooling | Different audience |
| Cross-domain consolidation | Requires architecture review |
| Behavior expansion | Contract creep |
| Remaining 7 modules | Future batches |

---

## Remaining Backlog (Future Batches)

| Module | Priority | Notes |
|--------|----------|-------|
| CusTelemetryService | HIGH | Customer telemetry ingestion |
| CusEnforcementService | HIGH | LLM enforcement checks |
| CusIntegrationService | MEDIUM | Integration management |
| LimitsSimulationService | MEDIUM | Pre-execution simulation |
| PoliciesFacade | MEDIUM | Policy CRUD operations |
| AuditLedgerService (sync) | LOW | May use async version |
| PlatformHealthService | LOW | Founder-facing adapter |

---

## Validation Checklist

Before starting execution:

- [ ] Invariant is clear and testable
- [ ] Metric is measurable
- [ ] Module list is final (no additions mid-sweep)
- [ ] Out-of-scope list acknowledged
- [ ] Execution protocol understood

---

## Stop Conditions

This sweep is COMPLETE when:

1. All 3 modules have HOC implementations
2. All callers are wired to HOC paths
3. `MISSING_HOC_MODULE` count = 7 (reduced by 3)
4. No new imports of legacy paths for these modules

---

## Approval Gate

> **Do not execute until human validation received.**
>
> Validation phrase: "Sweep-03 lock validated. Begin execution."
