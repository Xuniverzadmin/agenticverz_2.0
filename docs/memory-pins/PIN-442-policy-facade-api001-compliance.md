# PIN-442: Policy Facade Layer - API-001 Compliance Fix

**Status:** COMPLETE
**Created:** 2026-01-18
**Author:** Claude Opus 4.5
**Category:** Architecture / Governance / API-001
**Related PINs:** PIN-441, PIN-370, PIN-410
**Working Directory:** `/root/agenticverz2.0/backend`

---

## Executive Summary

Created PolicyFacade layer to fix API-001 governance violation in the POLICIES domain. The `policy_layer.py` API routes were directly importing and calling `get_policy_engine()` (33 locations), bypassing the facade pattern that other domains (Incidents, Ops) correctly implement.

**Impact:** 33 direct engine calls replaced with facade calls. Architecture now compliant with API-001.

---

## Problem Statement

### API-001 Governance Requirement

From `docs/architecture/GOVERNANCE_GUARDRAILS.md`:

> **API-001:** All domain data MUST be accessed through unified facade. Forbidden: Direct table queries in other routers.

### Violation Detected

**File:** `backend/app/api/policy_layer.py` (L2 API Routes)

```python
# VIOLATION - Direct L2 → L4 engine access (33 locations)
from app.policy import get_policy_engine

engine = get_policy_engine()  # Bypasses facade
result = await engine.evaluate(eval_request, db)
```

### Comparison: Correct Pattern (Incidents Domain)

```python
# CORRECT - L2 → L4 via Facade
from app.services.incidents.facade import get_incident_facade

facade = get_incident_facade()
incident_id = facade.create_incident_for_run(...)
```

---

## Solution Implemented

### 1. Created PolicyFacade

**File:** `backend/app/services/policy/facade.py`

```python
# Layer: L4 — Domain Engine
# Role: Policy Domain Facade - Centralized access to policy operations
# Reference: API-001 Guardrail (Domain Facade Required)

class PolicyFacade:
    """
    Facade for Policy domain operations.

    This is the ONLY entry point for external code to interact with
    policy services. Direct imports of PolicyEngine from outside
    this domain are forbidden (API-001).
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url
        self._policy_engine = None

    @property
    def _engine(self):
        """Lazy-load policy engine."""
        if self._policy_engine is None:
            from app.policy.engine import PolicyEngine
            self._policy_engine = PolicyEngine(database_url=self._db_url)
        return self._policy_engine

    async def evaluate(self, request, db=None, dry_run: bool = False):
        """Evaluate a request against all applicable policies."""
        return await self._engine.evaluate(request, db, dry_run=dry_run)

    # ... 30+ facade methods wrapping PolicyEngine
```

### 2. Updated policy_layer.py

**Before:**
```python
from app.policy import get_policy_engine

engine = get_policy_engine()
result = await engine.evaluate(eval_request, db)
```

**After:**
```python
from app.services.policy.facade import get_policy_facade

facade = get_policy_facade()
result = await facade.evaluate(eval_request, db)
```

### 3. Updated Package Exports

**File:** `backend/app/services/policy/__init__.py`

Added exports:
- `PolicyFacade`
- `get_policy_facade`
- `reset_policy_facade`

---

## Files Changed

### Created (1 file)

| File | Lines | Purpose |
|------|-------|---------|
| `app/services/policy/facade.py` | ~350 | PolicyFacade implementation |

### Modified (2 files)

| File | Changes | Purpose |
|------|---------|---------|
| `app/api/policy_layer.py` | 33 replacements + header | Use facade instead of direct engine |
| `app/services/policy/__init__.py` | Added exports | Package-level facade access |

---

## Architecture Compliance

### Before (VIOLATION)

```
┌─────────────────────────────────────────────────────────────┐
│  policy_layer.py (L2 API Routes)                            │
│                                                             │
│  from app.policy import get_policy_engine  ← DIRECT IMPORT  │
│                           ↓                                 │
│  engine = get_policy_engine()              ← NO FACADE      │
│  result = await engine.evaluate(...)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PolicyEngine (L4)                                          │
│  - No authorization checkpoint                              │
│  - No centralized audit logging                             │
│  - Exposed to multiple callers                              │
└─────────────────────────────────────────────────────────────┘
```

### After (COMPLIANT)

```
┌─────────────────────────────────────────────────────────────┐
│  policy_layer.py (L2 API Routes)                            │
│                                                             │
│  from app.services.policy.facade import get_policy_facade   │
│                           ↓                                 │
│  facade = get_policy_facade()              ← FACADE LAYER   │
│  result = await facade.evaluate(...)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PolicyFacade (L4)                 ← CENTRALIZED ACCESS     │
│  - Authorization checkpoint possible                        │
│  - Centralized audit logging                                │
│  - Single entry point for external code                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PolicyEngine (L4)                 ← ENCAPSULATED           │
│  - Internal implementation detail                           │
│  - Only accessed via facade                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Facade Methods Implemented

| Category | Methods |
|----------|---------|
| **Core Evaluation** | `evaluate`, `pre_check`, `get_state`, `reload_policies` |
| **Violations** | `get_violations`, `get_violation`, `acknowledge_violation` |
| **Risk Ceilings** | `get_risk_ceilings`, `get_risk_ceiling`, `update_risk_ceiling`, `reset_risk_ceiling` |
| **Safety Rules** | `get_safety_rules`, `update_safety_rule` |
| **Ethical Constraints** | `get_ethical_constraints` |
| **Cooldowns** | `get_active_cooldowns`, `clear_cooldowns` |
| **Metrics** | `get_metrics` |
| **Versioning (GAP 1)** | `get_policy_versions`, `get_current_version`, `create_policy_version`, `rollback_to_version`, `get_version_provenance`, `activate_policy_version` |
| **Dependencies (GAP 2)** | `get_dependency_graph`, `get_policy_conflicts`, `resolve_conflict`, `validate_dependency_dag`, `add_dependency_with_dag_check`, `get_topological_evaluation_order` |
| **Temporal (GAP 3)** | `get_temporal_policies`, `create_temporal_policy`, `get_temporal_utilization`, `prune_temporal_metrics`, `get_temporal_storage_stats` |
| **Context-Aware (GAP 4)** | `evaluate_with_context` |

---

## Verification Results

### SDSR Coherency Check

```
POLICIES Domain: 100% PASS (0 failures)
Overall: 85/86 PASS (1 unrelated ACTIVITY failure)
```

### YAML Files

No changes needed - facade is internal implementation. API endpoints unchanged.

---

## Benefits of Facade Pattern

| Benefit | Description |
|---------|-------------|
| **Authorization** | Single point for auth checks before engine calls |
| **Audit Logging** | Centralized logging of all policy operations |
| **Encapsulation** | PolicyEngine internals hidden from API routes |
| **Testability** | Easy to mock facade for unit tests |
| **Interface Stability** | External callers isolated from engine changes |
| **API-001 Compliance** | Follows established governance pattern |

---

## Lessons Learned

1. **Facade pattern is mandatory** - All domains must use facades per API-001
2. **Direct engine imports are violations** - Even if code works, it bypasses governance
3. **Consistency matters** - Incidents/Ops had facades, Policies was the outlier
4. **Internal changes need no YAML updates** - Facade is implementation detail

---

## References

- `docs/architecture/GOVERNANCE_GUARDRAILS.md` - API-001 definition
- `backend/app/services/incidents/facade.py` - Reference implementation
- `backend/app/services/ops/facade.py` - Reference implementation
- PIN-410 - Architecture Guardrails & Prevention Contract
