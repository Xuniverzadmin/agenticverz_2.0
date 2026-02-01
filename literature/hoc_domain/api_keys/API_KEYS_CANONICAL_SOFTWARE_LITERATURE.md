# API Keys Domain — Canonical Software Literature

**Domain:** api_keys
**Generated:** 2026-01-31
**Reference:** PIN-501
**Total Files:** 10 (3 L5_engines, 1 L5_schemas, 3 L6_drivers, 2 adapters, 1 __init__.py)

---

## Consolidation Actions (2026-01-31)

### Naming Violations — None

All files compliant. L5 uses `*_engine.py`/`*_facade.py`, L6 uses `*_driver.py`.

### Header Corrections (2)

| File | Old Header | New Header |
|------|-----------|------------|
| api_keys/__init__.py | `# Layer: L4 — Domain Services` | `# Layer: L5 — Domain (API Keys)` |
| L5_schemas/__init__.py | `# Layer: L4 — Domain Services` | `# Layer: L5 — Domain Schemas` |

### Legacy Connections — None

Zero active `app.services` imports. Clean.

### Cross-Domain Imports — None

Complete domain isolation. Clean.

---

## Domain Contract (from __init__.py)

**Entry Point Hierarchy:**
1. **APIKeysFacade** (`api_keys_facade.py`) — CUSTOMER-FACING, async, READ-ONLY, synthetic keys filtered
2. **KeysEngine** (`keys_engine.py`) — OPERATIONAL PRIMITIVES, sync, Read + Write

**Caller Rule:** L2 APIs MUST use APIKeysFacade. L2 APIs MUST NOT call engines directly.

**Async/Sync Split:** Intentional — facade is async (modern API handlers), engine is sync (runtime/gateway compatibility).

**Invariants:**
- INV-KEY-001: API key state changes must be explicit, auditable, and reversible
- INV-KEY-002: No implicit mutation during read paths
- INV-KEY-003: Synthetic keys never exposed to customer facade

---

## L5_engines (3 files)

### __init__.py
- **Role:** Package init, exports ApiKeysFacade and result types

### api_keys_facade.py
- **Role:** Unified entry point for API key operations (async, read-only)
- **Classes:** ApiKeysFacade
- **Factory:** `get_api_keys_facade()`
- **Callers:** L4 api_keys_handler (api_keys.query)

### keys_engine.py
- **Role:** Business logic for key operations (sync, read+write)
- **Callers:** adapters, runtime, gateway

---

## L5_schemas (1 file)

### __init__.py
- **Role:** Schemas package init (placeholder, awaiting schema files)

---

## L6_drivers (3 files)

### __init__.py
- **Role:** Package init

### api_keys_facade_driver.py
- **Role:** Pure data access for API key queries (async)
- **Classes:** ApiKeysFacadeDriver

### keys_driver.py
- **Role:** Read/write data access for API key engine operations (sync)
- **Classes:** KeysDriver

---

## adapters (2 files)

### __init__.py
- **Role:** Package init (empty)

### customer_keys_adapter.py
- **Role:** L2 boundary adapter for customer API key operations

---

## L4 Handler

**File:** `hoc/hoc_spine/orchestrator/handlers/api_keys_handler.py`
**Operations:** 1

| Operation | Handler Class | Target |
|-----------|--------------|--------|
| api_keys.query | ApiKeysQueryHandler | ApiKeysFacade |

No import updates required.

---

## Cleansing Cycle (2026-01-31) — PIN-503

### No Actions Required

Domain has zero `app.services` imports, zero `cus.general` imports, zero cross-domain violations.

### Tally

12/12 checks PASS (10 consolidation + 2 cleansing).

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.
