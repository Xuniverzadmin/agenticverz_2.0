# TODO — Iteration 3.4

**Date:** 2026-02-06
**Status:** COMPLETE ✅
**Purpose:** Consolidate System Runtime to hoc_spine (first principles — "Question one place")

---

## Goal

"Question one place, find the problem" for runtime/governance.

Today there are two "runtime authorities":
- `app.services.governance/*` — used by workers
- `app.hoc.cus.hoc_spine/*` — used by L2 APIs

This creates split-brain debugging. ITER3.4 consolidates to hoc_spine as the single runtime authority.

---

## 1) Worker Runtime Consolidation ✅

**Current State:** `backend/app/worker/runner.py` imports from `app.services.governance.*`

**Target State:** Worker routes through hoc_spine runtime surfaces (or `app.services.governance.*` becomes thin wrappers that delegate to hoc_spine)

**Result:** Worker continues importing from `app.services.governance.*` which now delegates to hoc_spine. No changes needed to worker code.

**Files modified:**
- `backend/app/services/governance/transaction_coordinator.py` — now a 75-line delegating shim
- `backend/app/services/governance/run_governance_facade.py` — now a 52-line delegating shim

---

## 2) Transaction Coordinator Unification ✅

**Current State:** Two transaction coordinators exist:
- `backend/app/services/governance/transaction_coordinator.py` — used by worker
- `backend/app/hoc/cus/hoc_spine/drivers/transaction_coordinator.py` — hoc_spine version

**Target State:** ONE canonical coordinator in hoc_spine. Old module becomes delegating shim.

**Result:**
- Canonical: `app.hoc.cus.hoc_spine.drivers.transaction_coordinator`
- Shim: `app.services.governance.transaction_coordinator` re-exports all symbols from hoc_spine

**Re-exported symbols:**
```python
RAC_ROLLBACK_AUDIT_ENABLED, TRANSACTION_COORDINATOR_ENABLED,
TransactionPhase, TransactionFailed, RollbackNotSupportedError,
DomainResult, TransactionResult, RollbackAction,
RunCompletionTransaction, get_transaction_coordinator, create_transaction_coordinator
```

---

## 3) Authority Uniformity ✅

**Current State:**
- `backend/app/hoc/cus/hoc_spine/schemas/authority_decision.py` exists (AuthorityDecision class)
- `backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py` uses boolean authority check

**Target State:** `operation_registry.py` uses `AuthorityDecision` type for authority checks, includes in OperationResult metadata, logs decisions.

**Result:**
1. `_check_authority()` now returns `AuthorityDecision` (not `bool`)
2. Authority decision included in audit logs with full metadata:
   - `governance_active`: bool (allowed)
   - `authority_degraded`: bool
   - `authority_reason`: str
   - `authority_code`: str

**Code change:**
```python
def _check_authority(self, operation: str) -> "AuthorityDecision":
    # Returns AuthorityDecision.allow(), allow_with_degraded_flag(), or allow with error
```

---

## 4) Evidence Scans ✅

### Shim verification

```bash
$ wc -l app/services/governance/transaction_coordinator.py app/services/governance/run_governance_facade.py
  75 app/services/governance/transaction_coordinator.py
  52 app/services/governance/run_governance_facade.py
 127 total
```

### Worker imports (unchanged, uses shims)

```bash
$ rg "from.*governance" app/worker/runner.py
from ..services.governance.run_governance_facade import get_run_governance_facade
from ..services.governance.transaction_coordinator import (
```

### _check_authority returns AuthorityDecision

```bash
$ rg "_check_authority.*AuthorityDecision" app/hoc/cus/hoc_spine/orchestrator/operation_registry.py
    def _check_authority(self, operation: str) -> "AuthorityDecision":
```

### Canonical hoc_spine files exist

```bash
$ ls -la app/hoc/cus/hoc_spine/drivers/transaction_coordinator.py app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py
-rw-r--r-- 1 root root 30336 Feb  2 20:38 app/hoc/cus/hoc_spine/drivers/transaction_coordinator.py
-rw-r--r-- 1 root root 11483 Feb  1 13:06 app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py
```

---

## Progress Log

### Phase 1: Exploration ✅
- [x] Scan worker/runner.py imports from app.services.governance
- [x] Read both transaction coordinators to understand differences
- [x] Read authority_decision.py and operation_registry's authority check

### Phase 2: Transaction Coordinator Consolidation ✅
- [x] Make hoc_spine coordinator canonical (already was)
- [x] Create delegating shim in app.services.governance

### Phase 3: Worker Runtime ✅
- [x] Verify worker uses shims correctly (imports unchanged, logic in hoc_spine)
- [x] No direct hoc_spine imports from worker (maintains boundary)

### Phase 4: Authority Uniformity ✅
- [x] Update operation_registry to use AuthorityDecision
- [x] Log/audit authority decisions (governance_active, authority_degraded, authority_reason, authority_code)

### Phase 5: Evidence ✅
- [x] Create evidence scans
- [x] Update this document with results

---

## Files Modified

1. `app/services/governance/transaction_coordinator.py` — replaced with delegating shim (75 lines)
2. `app/services/governance/run_governance_facade.py` — replaced with delegating shim (52 lines)
3. `app/hoc/cus/hoc_spine/orchestrator/operation_registry.py` — `_check_authority()` returns AuthorityDecision, `_audit_dispatch()` logs full decision

---

## Constraints

- No doc edits unless user commands ✅
- No allowlists/workarounds ✅
- Fix dependency direction and single-owner runtime ✅
- app.services.governance becomes shim layer, not deleted ✅

---

## Summary

ITER3.4 establishes **hoc_spine as the single runtime authority**:

1. **Transaction Coordinator**: Canonical in hoc_spine, shim in services.governance
2. **Run Governance Facade**: Canonical in hoc_spine, shim in services.governance
3. **Authority Decisions**: All checks return `AuthorityDecision` with full audit metadata
4. **Worker**: Unchanged imports, but logic now lives in hoc_spine

"Question one place, find the problem" is now achievable — all governance runtime logic is in `app.hoc.cus.hoc_spine`.
