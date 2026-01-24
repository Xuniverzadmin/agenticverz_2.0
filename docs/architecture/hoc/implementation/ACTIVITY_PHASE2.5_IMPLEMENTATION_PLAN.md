# ACTIVITY Domain — Phase 2.5A Implementation Plan

**Document ID:** ACTIVITY-PHASE2.5A-001
**Version:** 1.0.0
**Date:** 2026-01-24
**Status:** PENDING APPROVAL
**Author:** Claude + Founder

---

## Reference Documents

| Document | Location | Relevance |
|----------|----------|-----------|
| **HOC Index** | [`../INDEX.md`](../INDEX.md) | Master documentation index |
| **Layer Topology** | [`../../HOC_LAYER_TOPOLOGY_V1.md`](../../HOC_LAYER_TOPOLOGY_V1.md) | L5/L6 contract rules |
| **Master Migration Plan** | [`../../HOC_MIGRATION_PLAN.md`](../../HOC_MIGRATION_PLAN.md) | Phase 2 scope (Section 1.2 Activity) |
| **Phase 2 Plan** | [`../migration/PHASE2_MIGRATION_PLAN.md`](../migration/PHASE2_MIGRATION_PLAN.md) | Execution context |
| **Extraction Playbook** | [`../migration/PHASE2_EXTRACTION_PLAYBOOK.md`](../migration/PHASE2_EXTRACTION_PLAYBOOK.md) | L4/L6 extraction procedures |
| **Extraction Protocol** | [`../migration/PHASE2_EXTRACTION_PROTOCOL.md`](../migration/PHASE2_EXTRACTION_PROTOCOL.md) | Step-by-step guide |
| **Driver-Engine Contract** | [`../../../../backend/app/houseofcards/DRIVER_ENGINE_CONTRACT.md`](../../../../backend/app/houseofcards/DRIVER_ENGINE_CONTRACT.md) | L5/L6 boundary rules |
| **Analytics Lock** | [`../../../../backend/app/houseofcards/customer/analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md`](../../../../backend/app/houseofcards/customer/analytics/ANALYTICS_DOMAIN_LOCK_FINAL.md) | Lock template |
| **Policies Lock** | [`../../../../backend/app/houseofcards/customer/policies/POLICIES_DOMAIN_LOCK_FINAL.md`](../../../../backend/app/houseofcards/customer/policies/POLICIES_DOMAIN_LOCK_FINAL.md) | Lock template |
| **Activity Audit** | [`../../../../backend/app/houseofcards/customer/activity/HOC_activity_deep_audit_report.md`](../../../../backend/app/houseofcards/customer/activity/HOC_activity_deep_audit_report.md) | Current state |

---

## 1. Executive Summary

### 1.1 Objective

Complete L4/L6 structural layering for the `activity` domain to achieve LOCK-ELIGIBLE status.

### 1.2 Scope

**Domain Path:** `backend/app/houseofcards/customer/activity/`

**Current State:**
- 5 engines (4 with violations, 1 clean)
- 2 drivers (1 with mixed L4/L6)
- NOT lock-eligible

**Target State:**
- All engines free of sqlalchemy imports
- All drivers free of business logic
- LOCK-ELIGIBLE

### 1.3 Strategic Rationale

From HOC_MIGRATION_PLAN.md Section 1.4 (Migration Order):
> 4. **Activity** — well-defined boundaries

Activity domain is optimal for Phase 2.5A because:
1. **Smallest scope** — 5 engines, 2 drivers
2. **Clean dependencies** — Only imports from general domain
3. **Stub nature** — 4 violations are unused imports (easy to remove)
4. **Single complex file** — Only `llm_threshold_service.py` needs real extraction
5. **Pattern establishment** — Proves the extraction workflow for larger domains

---

## 2. Current Violations

### 2.1 File Inventory

| File | Layer | LOC | Violation | Severity |
|------|-------|-----|-----------|----------|
| `engines/signal_feedback_service.py` | L5 | 128 | AsyncSession import (unused) | STRUCTURAL |
| `engines/attention_ranking_service.py` | L5 | 87 | AsyncSession import (unused) | STRUCTURAL |
| `engines/pattern_detection_service.py` | L5 | 80 | AsyncSession import (unused) | STRUCTURAL |
| `engines/cost_analysis_service.py` | L5 | 81 | AsyncSession import (unused) | STRUCTURAL |
| `engines/signal_identity.py` | L5 | 66 | None | CLEAN |
| `drivers/llm_threshold_service.py` | L6 | 813 | Mixed L4/L6 | **CRITICAL** |
| `drivers/activity_enums.py` | L6 | — | None | CLEAN |

### 2.2 Violation Details

#### Engine Violations (Lines 11 in each file)

```python
# All 4 files have this pattern:
from sqlalchemy.ext.asyncio import AsyncSession

class XxxService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session  # NEVER USED - stub implementations
```

**Rule Violated:** HOC_LAYER_TOPOLOGY_V1.md
> L5 Engine MUST NOT import `sqlalchemy`, `sqlmodel`, `Session` at runtime

#### Driver Violation (llm_threshold_service.py)

813 LOC file contains:

| Component | Current Layer | Should Be | LOC |
|-----------|---------------|-----------|-----|
| `ThresholdParams` | L6 (wrong) | L5 | ~50 |
| `ThresholdParamsUpdate` | L6 (wrong) | L5 | ~15 |
| `ThresholdSignal` enum | L6 (wrong) | L5 | ~10 |
| `ThresholdEvaluationResult` | L6 (wrong) | L5 | ~10 |
| `LLMRunThresholdResolver` | L6 (wrong) | L5 | ~75 |
| `LLMRunEvaluator` | L6 (wrong) | L5 | ~140 |
| `LLMRunThresholdResolverSync` | L6 (wrong) | L5 | ~70 |
| `LLMRunEvaluatorSync` | L6 (wrong) | L5 | ~70 |
| DB queries | L6 (correct) | L6 | ~50 |
| Signal helpers | L6 (ambiguous) | L5 | ~100 |

**Rule Violated:** DRIVER_ENGINE_CONTRACT.md
> L6 drivers have NO business logic

Business logic in driver (example from line 250-257):
```python
# This is BUSINESS LOGIC - belongs in L5 engine
if limit.scope == "GLOBAL":
    applies = True
elif limit.scope == "TENANT":
    applies = True
elif limit.scope == "PROJECT" and limit.scope_id == project_id:
    applies = True
elif limit.scope == "AGENT" and limit.scope_id == agent_id:
    applies = True
```

---

## 3. Implementation Plan

### 3.1 Phase 1: Engine Stub Cleanup (LOW RISK)

**Objective:** Remove unused AsyncSession imports from stub engines

**Duration:** ~30 minutes

**Files to modify:**
1. `engines/signal_feedback_service.py`
2. `engines/attention_ranking_service.py`
3. `engines/pattern_detection_service.py`
4. `engines/cost_analysis_service.py`

**Change Pattern:**

```python
# BEFORE
from sqlalchemy.ext.asyncio import AsyncSession

class SignalFeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

# AFTER
class SignalFeedbackService:
    def __init__(self) -> None:
        pass  # Stub - no DB dependency
```

**Verification:**
- [ ] BLCA check after each file
- [ ] No functional change (stubs don't use session)

### 3.2 Phase 2: Split llm_threshold_service.py (MEDIUM COMPLEXITY)

**Objective:** Extract L5 business logic from L6 driver

**Duration:** ~2 hours

#### 3.2.1 Create New Engine

**New File:** `engines/threshold_engine.py`

**Contents to extract (all L4 — decision engine):**
- `DEFAULT_LLM_RUN_PARAMS` (constants)
- `ThresholdParams` (Pydantic model — **L4 decision contract**)
- `ThresholdParamsUpdate` (Pydantic model — **L4 decision contract**)
- `ThresholdSignal` (enum — **L4 decision contract**)
- `ThresholdEvaluationResult` (dataclass — **L4 decision contract**)
- `LLMRunThresholdResolver` (business logic — **L4 decision engine**)
- `LLMRunEvaluator` (business logic — **L4 decision engine**)
- `LLMRunThresholdResolverSync` (business logic — **L4 decision engine**)
- `LLMRunEvaluatorSync` (business logic — **L4 decision engine**)
- `ThresholdSignalRecord` (dataclass — **L4 decision contract**)
- Signal helper functions

**L4 Engine Header:**
```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Threshold resolution and evaluation logic (decision engine)
# Callers: L3 Adapters, API routes
# Reference: docs/architecture/hoc/INDEX.md → Activity Phase 2.5A
#
# L4 ENGINE CONTRACT:
# - Pure business decisions (precedence resolution, threshold evaluation)
# - No sqlalchemy imports
# - Uses ThresholdDriver interface for DB access
# - Decision contracts (ThresholdParams, etc.) owned by this engine
```

#### 3.2.2 Refactor Driver

**Rename:** `drivers/llm_threshold_service.py` → `drivers/threshold_driver.py`

**Contents to keep (L6 only):**
- `LimitSnapshot` (dataclass for returning data)
- `get_active_threshold_limits()` (DB query)
- `get_threshold_limit_by_scope()` (DB query)

**L6 Driver Header:**
```python
# Layer: L6 — Database Driver
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Database operations for threshold limits
# Callers: L5 threshold_engine
# Reference: docs/architecture/hoc/INDEX.md → Activity Phase 2.5A
#
# DRIVER CONTRACT:
# - Returns domain objects, not ORM models
# - No business logic (no precedence rules, no evaluation)
```

#### 3.2.3 Interface Contract

```python
# L6 Driver (threshold_driver.py)
@dataclass
class LimitSnapshot:
    """Immutable snapshot returned to engines."""
    id: str
    tenant_id: str
    scope: str
    scope_id: Optional[str]
    params: dict
    status: str
    created_at: datetime

class ThresholdDriver:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_threshold_limits(
        self, tenant_id: str
    ) -> list[LimitSnapshot]:
        """Query Limit table, return snapshots (not ORM)."""
        ...

    async def get_threshold_limit_by_scope(
        self, tenant_id: str, scope: str, scope_id: Optional[str]
    ) -> Optional[LimitSnapshot]:
        """Query single limit by scope."""
        ...

# L5 Engine (threshold_engine.py)
class LLMRunThresholdResolver:
    def __init__(self, driver: ThresholdDriver):
        self._driver = driver

    async def resolve(
        self, tenant_id: str, agent_id: Optional[str], project_id: Optional[str]
    ) -> ThresholdParams:
        """Apply precedence logic (AGENT > PROJECT > TENANT > GLOBAL)."""
        limits = await self._driver.get_active_threshold_limits(tenant_id)
        # Business logic here...
```

### 3.3 Phase 3: Verification & Lock

**Objective:** Produce ACTIVITY_DOMAIN_LOCK_FINAL.md

**Duration:** ~30 minutes

**Verification Checklist:**
- [ ] BLCA passes with 0 violations for activity domain
- [ ] No sqlalchemy imports in `engines/` files
- [ ] No business logic in `drivers/` files (grep for `if.*scope`, etc.)
- [ ] All callers updated to new import paths
- [ ] Tests pass (if applicable)

**Lock Document Creation:**
- [ ] Create `ACTIVITY_DOMAIN_LOCK_FINAL.md` following analytics/policies template
- [ ] Document locked artifacts
- [ ] Document any transitional debt

---

## 4. Task Breakdown

| Task ID | Description | Phase | Dependency | Risk | Est. Time |
|---------|-------------|-------|------------|------|-----------|
| ACT-001 | Remove AsyncSession from signal_feedback_service.py | 1 | None | LOW | 5 min |
| ACT-002 | Remove AsyncSession from attention_ranking_service.py | 1 | None | LOW | 5 min |
| ACT-003 | Remove AsyncSession from pattern_detection_service.py | 1 | None | LOW | 5 min |
| ACT-004 | Remove AsyncSession from cost_analysis_service.py | 1 | None | LOW | 5 min |
| ACT-005 | BLCA verification (Phase 1) | 1 | ACT-001-004 | LOW | 5 min |
| ACT-006 | Create engines/threshold_engine.py | 2 | ACT-005 | MEDIUM | 45 min |
| ACT-007 | Refactor drivers/threshold_driver.py | 2 | ACT-006 | MEDIUM | 30 min |
| ACT-008 | Update imports in callers | 2 | ACT-007 | LOW | 20 min |
| ACT-009 | BLCA verification (Phase 2) | 2 | ACT-008 | LOW | 10 min |
| ACT-010 | Create ACTIVITY_DOMAIN_LOCK_FINAL.md | 3 | ACT-009 | LOW | 20 min |

**Total Estimated Time:** ~2.5 hours

---

## 5. AUDIT Protocol

When executing this plan, Claude will operate in AUDIT mode:

### 5.1 Trigger Conditions

AUDIT is triggered when:
- Modifying any file in `engines/` or `drivers/`
- Adding imports to any file
- Moving code between files

### 5.2 AUDIT Output Format

```
⚠️ LAYER TOPOLOGY AUDIT

File: <path>:<line>
Violation: <description>
Rule: <reference to HOC_LAYER_TOPOLOGY_V1.md or DRIVER_ENGINE_CONTRACT.md>

Options:
A) <fix option 1>
B) <fix option 2>
C) Defer decision

Awaiting decision before proceeding.
```

### 5.3 Decision Authority

| Decision Type | Authority |
|---------------|-----------|
| Remove unused import | Claude may proceed |
| Extract to new file | Requires approval |
| Change interface contract | Requires approval |
| Mark as transitional debt | Requires approval |

---

## 6. Success Criteria

### 6.1 Phase 1 Success

- [ ] 0 sqlalchemy imports in activity `engines/` directory
- [ ] BLCA passes with 0 violations for activity engines
- [ ] No functional change (stubs remain stubs)

### 6.2 Phase 2 Success

- [ ] `threshold_engine.py` exists with all business logic
- [ ] `threshold_driver.py` contains only DB operations
- [ ] Interface contract matches specification in Section 3.2.3
- [ ] All callers use new import paths
- [ ] BLCA passes with 0 violations

### 6.3 Phase 3 Success

- [ ] `ACTIVITY_DOMAIN_LOCK_FINAL.md` created
- [ ] All artifacts listed in lock document
- [ ] Domain comparable to locked analytics/policies domains

---

## 7. Rollback Plan

If issues arise during implementation:

1. **Phase 1 rollback:** Restore AsyncSession imports (trivial)
2. **Phase 2 rollback:** Delete new engine, restore original driver from git
3. **Phase 3 rollback:** Delete lock document

All changes are tracked in git. No database migrations involved.

---

## 8. Post-Implementation

### 8.1 Update Documentation

- [ ] Update HOC INDEX.md with activity lock status
- [ ] Update activity audit report
- [ ] Update INVENTORY.md if applicable

### 8.2 Next Domain

Per dependency analysis, recommended next domain: **logs**

---

## 9. Approval

**Decision Required:**

- [ ] Proceed with implementation as outlined
- [ ] Modifications requested: _______________
- [ ] Pre-approved transitional debt items: _______________

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial plan | Claude |

---

**END OF IMPLEMENTATION PLAN**
