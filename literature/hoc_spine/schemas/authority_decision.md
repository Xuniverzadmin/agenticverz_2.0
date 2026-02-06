# authority_decision.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/authority_decision.py`
**Layer:** L4 — HOC Spine (Schema)
**Component:** Schema
**Created:** 2026-02-03
**Reference:** PIN-520 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            authority_decision.py
Lives in:        schemas/
Role:            Unified authority decision schema for all L4 authority checks
Inbound:         orchestrator, authority/concurrent_runs, authority/degraded_mode_checker, authority/contracts
Outbound:        none (pure data contract)
Transaction:     Forbidden
Cross-domain:    yes (multi-consumer schema per SCHEMA ADMISSION RULE)
Purpose:         Unified AuthorityDecision schema for L4 gates
Violations:      none
```

## Purpose

Unified authority decision schema returned by all L4 authority checks.
Ensures consistent handling of allow/deny/degraded states across:
- concurrent_runs
- degraded_mode_checker
- contract_engine
- runtime_switch

## Key Types

### AuthorityDecision (frozen dataclass)

| Attribute | Type | Description |
|-----------|------|-------------|
| `allowed` | `bool` | Whether operation is permitted |
| `reason` | `str` | Human-readable explanation |
| `degraded` | `bool` | System in degraded mode (allowed but flagged) |
| `code` | `str | None` | Machine-readable status code |
| `conditions` | `tuple[str, ...]` | Conditions affecting the decision |

### Factory Methods

| Method | Returns | Use Case |
|--------|---------|----------|
| `AuthorityDecision.allow(reason, degraded, conditions)` | `allowed=True` | Normal permission grant |
| `AuthorityDecision.deny(reason, code, conditions)` | `allowed=False` | Permission denied |
| `AuthorityDecision.allow_with_degraded_flag(reason, conditions)` | `allowed=True, degraded=True` | Permitted but system degraded |

### Composition

| Method | Purpose |
|--------|---------|
| `decision.with_condition(cond)` | Add condition to existing decision |
| `AuthorityDecision.combine(*decisions)` | Merge multiple decisions (any deny → deny) |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.schemas.authority_decision import AuthorityDecision

# In authority module
def check_concurrent_runs(tenant_id: str, limit: int) -> AuthorityDecision:
    current = get_active_runs(tenant_id)
    if current >= limit:
        return AuthorityDecision.deny(
            reason=f"Concurrent run limit ({limit}) exceeded",
            code="CONCURRENT_LIMIT_EXCEEDED",
        )
    return AuthorityDecision.allow()

# In executor
authority = check_concurrent_runs(tenant_id, limit=5)
if not authority.allowed:
    return OperationResult.fail(authority.reason, authority.code)
if authority.degraded:
    logger.warning("operation.degraded_mode", extra={"reason": authority.reason})
```

## Design Principles

1. **IMMUTABLE** — frozen dataclass, no mutation after creation
2. **EXPLICIT** — allow/deny/degraded are separate states, not inferred
3. **AUDITABLE** — every decision has reason and optional code
4. **COMPOSABLE** — conditions list allows compound decisions

## Consumers

| Domain | Consumer | Usage |
|--------|----------|-------|
| orchestrator | `operation_registry.py` | Authority check before dispatch |
| authority | `concurrent_runs.py` | Concurrency limit enforcement |
| authority | `degraded_mode_checker.py` | Degraded mode detection |
| authority | `contract_engine.py` | Contract state evaluation |

## PIN-520 Phase 1

This schema is part of PIN-520 Phase 1 (Registry Enforcement + AuthorityDecision Schema).
All L4 authority checks will be migrated to return `AuthorityDecision` in Phase 5.

---

*Generated: 2026-02-03*
