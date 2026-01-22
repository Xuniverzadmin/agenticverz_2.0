# HOC API Keys Domain Analysis v1

**Date:** 2026-01-22
**Domain:** `app/houseofcards/customer/api_keys/`
**Status:** Analysis Complete — Governance Applied

---

## Executive Summary

| Aspect | Assessment |
|--------|------------|
| Architectural quality | Functional |
| Role clarity | Clarified (was ambiguous) |
| Current risk | Low |
| Security sensitivity | High (keys = access) |
| Changes applied | Domain contract + invariants |

**Verdict:** API Keys is a small, security-sensitive domain. Clarity matters more than code volume here. Governance contract now declares entry point hierarchy and invariants.

---

## Directory Structure

```
app/houseofcards/customer/api_keys/
├── __init__.py                           (50 LOC) ← governance added
├── facades/
│   ├── __init__.py                       (11 LOC)
│   └── api_keys_facade.py                (238 LOC)
├── engines/
│   ├── __init__.py                       (11 LOC)
│   └── keys_service.py                   (220 LOC) ← clarification added
├── drivers/
│   └── __init__.py                       (11 LOC)
└── schemas/
    └── __init__.py                       (11 LOC)
                                          ──────────
                              Total:      552 LOC
```

---

## Domain Contract (Added)

### Entry Point Hierarchy

| Priority | Entry Point | Pattern | Operations | Callers |
|----------|-------------|---------|------------|---------|
| 1 | `APIKeysFacade` | Async | READ-ONLY | L2 API routes only |
| 2 | `KeysReadService` / `KeysWriteService` | Sync | Read + Write | L3 adapters, runtime, gateway |

### Caller Rule

```
L2 APIs MUST use APIKeysFacade.
L2 APIs MUST NOT call engines directly.
```

### Invariants

| ID | Rule |
|----|------|
| INV-KEY-001 | API key state changes must be explicit, auditable, and reversible |
| INV-KEY-002 | No implicit mutation during read paths |
| INV-KEY-003 | Synthetic keys never exposed to customer facade |

### Async/Sync Split (Intentional)

| Layer | Pattern | Reason |
|-------|---------|--------|
| Facade | Async | Modern API handlers |
| Engine | Sync | Runtime/gateway compatibility |

**This is intentional, not technical debt.**

---

## What Was Validated (No Changes Needed)

### 1. Facade = Read-Only, Engine = Mutations — Correct

- Facade: customer-visible, async, read-only
- Engine: operational, sync, allowed to mutate

**Do not merge these.**

### 2. Synthetic Key Filtering in Facade — Correct

`is_synthetic == False` enforced only in customer facade. This prevents internal keys leaking to customers.

### 3. Tenant Isolation — Correct

All queries enforce tenant_id filtering.

---

## File Analysis

### `api_keys/facades/api_keys_facade.py` (238 LOC)

```
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Callers: L2 api-keys API (aos_api_key.py)
```

**DTOs:**

| Class | Purpose |
|-------|---------|
| `APIKeySummaryResult` | List view summary |
| `APIKeysListResult` | Paginated list response |
| `APIKeyDetailResult` | Full key details |

**Class: `APIKeysFacade`**

| Method | Order | Description |
|--------|-------|-------------|
| `list_api_keys()` | O2 | List keys, excludes synthetic |
| `get_api_key_detail()` | O3 | Get key detail |

**Exports:**
```python
__all__ = [
    "APIKeysFacade", "get_api_keys_facade",
    "APIKeySummaryResult", "APIKeysListResult", "APIKeyDetailResult",
]
```

---

### `api_keys/engines/keys_service.py` (220 LOC)

```
# Layer: L4 — Domain Engine
# Product: system-wide
# Callers: customer_keys_adapter.py (L3), runtime, gateway — NOT L2
```

**Classes:**

| Class | Methods | Description |
|-------|---------|-------------|
| `KeysReadService` | `list_keys()`, `get_key()`, `get_key_usage_today()` | Read operations |
| `KeysWriteService` | `freeze_key()`, `unfreeze_key()` | Write operations |

**Exports:**
```python
__all__ = [
    "KeysReadService", "KeysWriteService",
    "get_keys_read_service", "get_keys_write_service",
]
```

---

## Cross-Domain Dependencies

| File | External Imports |
|------|------------------|
| `api_keys_facade.py` | `app.models.tenant.APIKey` |
| `keys_service.py` | `app.models.tenant.APIKey`, `app.models.killswitch.ProxyCall` |

---

## Key Architectural Properties

| Property | Status |
|----------|--------|
| Owns tables | **NO** (uses APIKey, ProxyCall) |
| Tenant isolation | **YES** |
| Synthetic filtering | **YES** (facade only) |
| Entry point hierarchy | **YES** (documented) |
| Governance contract | **YES** (added 2026-01-22) |

---

## Issues Resolved

### 1. Dual Entry Points — RESOLVED

**Was:** Two valid ways in, no declared hierarchy.
**Now:** Explicit hierarchy documented. Facade for L2, engines for L3/runtime.

### 2. Product Declaration Mismatch — CLARIFIED

**Was:** Facade `ai-console`, engine `system-wide` — looked inconsistent.
**Now:** Clarifying comment added explaining why engine is system-wide.

### 3. Async/Sync Split — DOCUMENTED

**Was:** Looked like technical debt.
**Now:** Documented as intentional design decision.

---

## What Must NEVER Happen

| Action | Why Forbidden |
|--------|---------------|
| Add writes to facade | Violates read-only principle |
| L2 calling engines directly | Bypasses facade controls |
| Implicit mutations on read | Violates INV-KEY-002 |
| Exposing synthetic keys to customers | Violates INV-KEY-003 |
| Merging facade and engine | Destroys separation of concerns |

---

## Changes Applied

| Date | Change |
|------|--------|
| 2026-01-22 | Added domain contract to `api_keys/__init__.py` |
| 2026-01-22 | Documented 3 invariants (INV-KEY-001 through INV-KEY-003) |
| 2026-01-22 | Added entry point hierarchy and caller rule |
| 2026-01-22 | Added product scope clarification to `keys_service.py` |
| 2026-01-22 | Documented async/sync split as intentional |

---

## Conclusion

API Keys domain is **small, sharp, and security-sensitive**.

The governance contract now provides:
- Clear entry point hierarchy (facade vs engine)
- Explicit caller restrictions (L2 → facade, L3 → engine)
- Mutation invariants for security
- Documentation of intentional async/sync split

**The domain is now stable and boring — which is exactly right for security-sensitive code.**
