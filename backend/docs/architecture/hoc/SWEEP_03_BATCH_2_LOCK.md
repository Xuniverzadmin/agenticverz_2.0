# SWEEP-03: Batch 2 Lock

**Status:** CLOSED
**Effective:** 2026-01-25
**Predecessor:** SWEEP-03 Batch 1 (CLOSED)

---

## Batch 2 Closure

> **Status: CLOSED**
> LimitsSimulationService, CusEnforcementService, and CusTelemetryService created with HOC modules.
> All declared callers wired.
> Remaining 4 missing modules deferred to subsequent batches.

### Batch 2 Deliverables

| Module | HOC Location | Callers Wired |
|--------|--------------|---------------|
| LimitsSimulationService | `policies/L5_engines/limits_simulation_service.py` | `simulate.py` |
| CusEnforcementService | `policies/L5_engines/cus_enforcement_service.py` | `cus_enforcement.py` |
| CusTelemetryService | `integrations/L5_engines/cus_telemetry_service.py` | `cus_telemetry.py` |

### Batch 2 Metrics

| Metric | Before | After |
|--------|--------|-------|
| MISSING_HOC_MODULE | 7 | 4 |

---

**Continuation:** See future `SWEEP_03_BATCH_3_LOCK.md` for remaining modules

---

## Invariant (UNCHANGED — LOCKED)

> **Every non-deprecated symbol imported by ≥1 HOC file must have a HOC module with an explicit contract.**

This invariant is **unchanged** from Batch 1. No reinterpretation allowed.

---

## Metric

`MISSING_HOC_MODULE` count

**Target:** Reduce from 7 to 4 (this batch of 3 modules)

---

## Scope: Batch 2 (3 Modules)

| Order | Module | Layer | Location | Callers |
|-------|--------|-------|----------|---------|
| 1 | **LimitsSimulationService** | L5 | `app.hoc.cus.policies.L5_engines.limits_simulation` | `simulate.py` |
| 2 | **CusEnforcementService** | L5 | `app.hoc.cus.policies.L5_engines.cus_enforcement` | `cus_enforcement.py` |
| 3 | **CusTelemetryService** | L5 | `app.hoc.cus.integrations.L5_engines.cus_telemetry` | `cus_telemetry.py` |

### Import Details

| Module | Current Import | Target Import |
|--------|----------------|---------------|
| LimitsSimulationService | `from app.services.limits.simulation_service import LimitsSimulationService` | `from app.hoc.cus.policies.L5_engines.limits_simulation_service import ...` |
| CusEnforcementService | `from app.services.cus_enforcement_service import CusEnforcementService` | `from app.hoc.cus.policies.L5_engines.cus_enforcement_service import ...` |
| CusTelemetryService | `from app.services.cus_telemetry_service import CusTelemetryService` | `from app.hoc.cus.integrations.L5_engines.cus_telemetry_service import ...` |

### Selection Rationale

1. **LimitsSimulationService**: Pure policy-local logic, isolated, no cross-domain coupling
2. **CusEnforcementService**: Directly blocks API paths, clear enforcement boundary
3. **CusTelemetryService**: Small surface, well-bounded, customer telemetry ingestion

---

## Explicitly NOT in Batch 2

| Module | Reason |
|--------|--------|
| PlatformHealthService | L4 runtime semantics (requires different sweep) |
| CusIntegrationService | Cross-domain coupling (requires architecture review) |
| PoliciesFacade | Potentially redundant after driver pattern (needs decision sweep) |
| AuditLedgerService (sync) | Low priority, may use async version |

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

## Out of Scope (LOCKED — RE-CONFIRMED)

| Item | Reason |
|------|--------|
| Refactoring callers | Separate sweep |
| Performance optimization | Premature |
| Authority rules (TIME/TX/orchestration) | Different invariant |
| Raw SQL changes | Different invariant |
| Founder (fdr/) tooling | Different audience |
| Cross-domain consolidation | Requires architecture review |
| Behavior expansion | Contract creep |
| Remaining 4 modules | Future batches |
| Creating facades "for convenience" | Not in invariant |
| Improving reliability/performance | Not in invariant |
| Touching Platform/L4 runtime | Different invariant |

---

## Stop Signal

If, during contract definition, you discover:

- Ambiguous ownership
- Conflicting semantics
- Need for orchestration
- Cross-domain coupling

→ **STOP**
→ That module is *not eligible* for this sweep
→ Defer it to a future design sweep

Do **not** improvise.

---

## Stop Conditions

This batch is COMPLETE when:

1. All 3 modules have HOC implementations
2. All callers are wired to HOC paths
3. `MISSING_HOC_MODULE` count = 4 (reduced by 3)
4. No new imports of legacy paths for these modules

---

## Approval Gate

> **Do not execute until human validation received.**
>
> Validation phrase: "Sweep-03 Batch-2 lock validated. Begin execution."
