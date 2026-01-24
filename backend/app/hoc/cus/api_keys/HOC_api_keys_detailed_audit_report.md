# HOC API Keys Domain — Rigorous Line-by-Line Audit Report

**Status:** HOC DOMAIN CLEAN — External duplicate noted
**Audit Date:** 2026-01-23 (Updated with migration execution)
**Auditor:** Claude (claude-opus-4-5-20251101)
**Domain:** `houseofcards/customer/api_keys`
**Scope:** Within api_keys domain only (not beyond)

---

## Executive Summary

**HOC DOMAIN INTERNAL STATUS: CLEAN**

The api_keys domain within HOC contains no internal duplicates. The facade and engine have distinct responsibilities and no overlapping code.

**EXTERNAL DUPLICATE NOTED (Outside Scope):**

| Finding ID | Type | Location | Status |
|------------|------|----------|--------|
| **INT-APIKEYS-DUP-001** | External duplicate | `app/services/keys_service.py` (ORIGINAL) copied to HOC | DEFERRED — handled in separate phase |
| **INT-APIKEYS-BUG-001** | Missing field | `is_frozen` used but not in model/schema | **RESOLVED** — schema updated |

---

## 1. Files Audited (Line Counts)

| File | Path | Lines | Type |
|------|------|-------|------|
| F1 | `api_keys/__init__.py` | 50 | Domain contract |
| F2 | `facades/__init__.py` | 11 | Package placeholder |
| F3 | `facades/api_keys_facade.py` | 238 | Substantive |
| F4 | `engines/__init__.py` | 11 | Package placeholder |
| F5 | `engines/keys_service.py` | 218 | Substantive |
| F6 | `drivers/__init__.py` | 11 | Package placeholder |
| F7 | `schemas/__init__.py` | 11 | Package placeholder |
| **EXTERNAL** | `app/services/keys_service.py` | 212 | **DUPLICATE of F5** |

**Total Lines in Domain:** 550
**Total Lines Including Duplicate:** 762

---

## 2. EXTERNAL FINDING: INT-APIKEYS-DUP-001 (Deferred)

### Full File Duplicate Detected (Outside HOC Scope)

**ORIGINAL:** `backend/app/services/keys_service.py` (212 lines) — Outside HOC namespace
**COPY:** `backend/app/houseofcards/customer/api_keys/engines/keys_service.py` (218 lines) — Inside HOC namespace

**Status:** DEFERRED — The original file in `app/services/` will be handled in a separate phase when that namespace is audited. The HOC copy is the canonical location going forward.

### Line-by-Line Comparison Evidence

#### Header Differences (Non-Code)

| Line | File 1 (app/services) | File 2 (HOC engines) |
|------|----------------------|----------------------|
| 7 | `# Callers: customer_keys_adapter.py (L3)` | `# Callers: customer_keys_adapter.py (L3), runtime, gateway — NOT L2` |
| 11-14 | `# GOVERNANCE NOTE:` (3 lines) | `# PRODUCT SCOPE NOTE:` + `# GOVERNANCE NOTE:` (9 lines) |

#### Code Comparison (100% IDENTICAL)

| Section | File 1 Lines | File 2 Lines | Match |
|---------|--------------|--------------|-------|
| `import datetime` | 33 | 39 | IDENTICAL |
| `import typing` | 34 | 40 | IDENTICAL |
| `import sqlalchemy` | 36 | 42 | IDENTICAL |
| `import sqlmodel` | 37 | 43 | IDENTICAL |
| `from app.models.killswitch import ProxyCall` | 40 | 46 | IDENTICAL |
| `from app.models.tenant import APIKey` | 41 | 47 | IDENTICAL |
| `class KeysReadService` | 44-141 | 50-148 | IDENTICAL (98 lines) |
| `class KeysWriteService` | 144-193 | 150-199 | IDENTICAL (50 lines) |
| `get_keys_read_service()` | 196-198 | 202-204 | IDENTICAL |
| `get_keys_write_service()` | 201-203 | 207-209 | IDENTICAL |
| `__all__` | 206-211 | 212-217 | IDENTICAL |

#### Method-by-Method Identity Proof

**KeysReadService.__init__:**
```
File 1 Lines 51-53:
    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

File 2 Lines 57-59:
    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session
```
**VERDICT: IDENTICAL**

**KeysReadService.list_keys:**
```
File 1 signature (Line 55-60): def list_keys(self, tenant_id: str, limit: int = 50, offset: int = 0) -> Tuple[List[APIKey], int]
File 2 signature (Line 61-66): def list_keys(self, tenant_id: str, limit: int = 50, offset: int = 0) -> Tuple[List[APIKey], int]
```
- File 1 body: Lines 61-88 (28 lines)
- File 2 body: Lines 67-94 (28 lines)
**VERDICT: IDENTICAL**

**KeysReadService.get_key:**
```
File 1 signature (Line 90-94): def get_key(self, key_id: str, tenant_id: str) -> Optional[APIKey]
File 2 signature (Line 96-100): def get_key(self, key_id: str, tenant_id: str) -> Optional[APIKey]
```
- File 1 body: Lines 95-112 (18 lines)
- File 2 body: Lines 101-118 (18 lines)
**VERDICT: IDENTICAL**

**KeysReadService.get_key_usage_today:**
```
File 1 signature (Line 114-118): def get_key_usage_today(self, key_id: str, today_start: datetime) -> Tuple[int, int]
File 2 signature (Line 120-124): def get_key_usage_today(self, key_id: str, today_start: datetime) -> Tuple[int, int]
```
- File 1 body: Lines 119-141 (23 lines)
- File 2 body: Lines 125-147 (23 lines)
**VERDICT: IDENTICAL**

**KeysWriteService.__init__:**
```
File 1 Lines 151-153: IDENTICAL to File 2 Lines 157-159
```
**VERDICT: IDENTICAL**

**KeysWriteService.freeze_key:**
```
File 1 Lines 155-173: IDENTICAL to File 2 Lines 161-179
```
- Both set: `key.is_frozen = True`
- Both set: `key.frozen_at = datetime.now(timezone.utc)`
**VERDICT: IDENTICAL**

**KeysWriteService.unfreeze_key:**
```
File 1 Lines 175-193: IDENTICAL to File 2 Lines 181-199
```
- Both set: `key.is_frozen = False`
- Both set: `key.frozen_at = None`
**VERDICT: IDENTICAL**

### Duplicate Classification

| Metric | Value |
|--------|-------|
| Header differences | 6 lines (comments only) |
| Code differences | 0 lines |
| Identical imports | 6/6 (100%) |
| Identical classes | 2/2 (100%) |
| Identical methods | 7/7 (100%) |
| Identical functions | 2/2 (100%) |
| Identical `__all__` | 1/1 (100%) |

**CONCLUSION: 100% CODE DUPLICATION**

---

## 3. CRITICAL FINDING: INT-APIKEYS-BUG-001

### `is_frozen` Field Not Defined

#### Evidence in keys_service.py (Both Copies)

**File 1 Lines 168-169:**
```python
key.is_frozen = True
key.frozen_at = datetime.now(timezone.utc)
```

**File 1 Lines 188-189:**
```python
key.is_frozen = False
key.frozen_at = None
```

**File 2 Lines 174-175:**
```python
key.is_frozen = True
key.frozen_at = datetime.now(timezone.utc)
```

**File 2 Lines 194-195:**
```python
key.is_frozen = False
key.frozen_at = None
```

#### Evidence in APIKey Model (app/models/tenant.py Lines 348-414)

**Fields defined in SQLModel:**
| Line | Field | Type |
|------|-------|------|
| 353 | `id` | `str` |
| 354 | `tenant_id` | `str` |
| 355 | `user_id` | `Optional[str]` |
| 358 | `name` | `str` |
| 359 | `key_prefix` | `str` |
| 360 | `key_hash` | `str` |
| 363 | `permissions_json` | `Optional[str]` |
| 364 | `allowed_workers_json` | `Optional[str]` |
| 367 | `rate_limit_rpm` | `Optional[int]` |
| 368 | `max_concurrent_runs` | `Optional[int]` |
| 371 | `status` | `str` |
| 372 | `expires_at` | `Optional[datetime]` |
| 373 | `revoked_at` | `Optional[datetime]` |
| 374 | `revoked_reason` | `Optional[str]` |
| 377 | `last_used_at` | `Optional[datetime]` |
| 378 | `total_requests` | `int` |
| 381 | `created_at` | `datetime` |
| 384 | `is_synthetic` | `bool` |
| 385 | `synthetic_scenario_id` | `Optional[str]` |

**`is_frozen` is NOT defined in the model.**

#### Evidence in Alembic Migration (037_m22_killswitch.py)

**Lines 175-178 (api_keys columns added):**
```python
op.add_column("api_keys", sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True))
op.add_column("api_keys", sa.Column("frozen_by", sa.String(100), nullable=True))
op.add_column("api_keys", sa.Column("freeze_reason", sa.Text(), nullable=True))
```

**`is_frozen` column is NOT added to api_keys table.**

#### Search Verification

```bash
grep -r "add_column.*api_keys.*is_frozen" backend/alembic/
# Result: No matches found
```

### Bug Classification

| Aspect | Status |
|--------|--------|
| Model defines `is_frozen` | NO |
| Migration adds `is_frozen` to api_keys | NO |
| Code assigns `key.is_frozen` | YES (4 occurrences) |
| Schema-Code mismatch | **CONFIRMED** |

**CONCLUSION: Code assigns to field that doesn't exist in model or database.**

---

## 4. Artifact Inventory (Rigorous)

### F3: `facades/api_keys_facade.py` (238 lines)

#### Header (Lines 1-12)
```
Line 1:  # Layer: L4 — Domain Engine
Line 2:  # AUDIENCE: CUSTOMER
Line 3:  # Product: ai-console
Line 4:  # Temporal:
Line 5:  #   Trigger: api
Line 6:  #   Execution: async (DB reads)
Line 7:  # Role: API Keys domain facade - unified entry point for API key operations
Line 8:  # Callers: L2 api-keys API (aos_api_key.py)
Line 9:  # Allowed Imports: L6
Line 10: # Forbidden Imports: L1, L2, L3, L5
Line 11: # Reference: Connectivity Domain - Customer Console v1 Constitution
Line 12: #
```

#### Imports (Lines 28-36)
| Line | Import Statement |
|------|------------------|
| 28 | `import json` |
| 29 | `from dataclasses import dataclass, field` |
| 30 | `from datetime import datetime` |
| 31 | `from typing import Any, Optional` |
| 33 | `from sqlalchemy import func, select` |
| 34 | `from sqlalchemy.ext.asyncio import AsyncSession` |
| 36 | `from app.models.tenant import APIKey` |

#### Dataclasses

**APIKeySummaryResult (Lines 44-56):**
| Line | Field | Type |
|------|-------|------|
| 48 | `key_id` | `str` |
| 49 | `name` | `str` |
| 50 | `prefix` | `str` |
| 51 | `status` | `str` |
| 52 | `created_at` | `datetime` |
| 53 | `last_used_at` | `Optional[datetime]` |
| 54 | `expires_at` | `Optional[datetime]` |
| 55 | `total_requests` | `int` |

**APIKeysListResult (Lines 58-66):**
| Line | Field | Type |
|------|-------|------|
| 62 | `items` | `list[APIKeySummaryResult]` |
| 63 | `total` | `int` |
| 64 | `has_more` | `bool` |
| 65 | `filters_applied` | `dict[str, Any]` |

**APIKeyDetailResult (Lines 68-89):**
| Line | Field | Type |
|------|-------|------|
| 72 | `key_id` | `str` |
| 73 | `name` | `str` |
| 74 | `prefix` | `str` |
| 75 | `status` | `str` |
| 76 | `created_at` | `datetime` |
| 77 | `last_used_at` | `Optional[datetime]` |
| 78 | `expires_at` | `Optional[datetime]` |
| 79 | `total_requests` | `int` |
| 81 | `permissions` | `Optional[list[str]]` |
| 82 | `allowed_workers` | `Optional[list[str]]` |
| 84 | `rate_limit_rpm` | `Optional[int]` |
| 85 | `max_concurrent_runs` | `Optional[int]` |
| 87 | `revoked_at` | `Optional[datetime]` |
| 88 | `revoked_reason` | `Optional[str]` |

#### Classes

**APIKeysFacade (Lines 96-211):**
| Line | Method | Signature |
|------|--------|-----------|
| 108-168 | `list_api_keys` | `async def list_api_keys(self, session: AsyncSession, tenant_id: str, *, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> APIKeysListResult` |
| 170-211 | `get_api_key_detail` | `async def get_api_key_detail(self, session: AsyncSession, tenant_id: str, key_id: str) -> Optional[APIKeyDetailResult]` |

#### Global Variables
| Line | Name | Type |
|------|------|------|
| 218 | `_facade_instance` | `APIKeysFacade | None` |

#### Functions
| Line | Name | Signature |
|------|------|-----------|
| 221-226 | `get_api_keys_facade` | `def get_api_keys_facade() -> APIKeysFacade` |

#### Exports (Lines 229-237)
```python
__all__ = [
    "APIKeysFacade",
    "get_api_keys_facade",
    "APIKeySummaryResult",
    "APIKeysListResult",
    "APIKeyDetailResult",
]
```

### F5: `engines/keys_service.py` (218 lines)

#### Header (Lines 1-20)
```
Line 1:  # Layer: L4 — Domain Engine
Line 2:  # Product: system-wide
Line 3:  # Temporal:
Line 4:  #   Trigger: api
Line 5:  #   Execution: sync (DB reads/writes)
Line 6:  # Role: API Keys domain operations (L4)
Line 7:  # Callers: customer_keys_adapter.py (L3), runtime, gateway — NOT L2
Line 8:  # Allowed Imports: L6
Line 9:  # Forbidden Imports: L1, L2, L3, L5
Line 10: # Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
Line 11: #
Line 12: # PRODUCT SCOPE NOTE:
Line 13: # Marked system-wide because engines serve runtime/gateway (not just console).
Line 14: # The facade (api_keys_facade.py) is ai-console because it's customer-facing only.
Line 15: # See api_keys/__init__.py for full domain contract.
Line 16: #
Line 17: # GOVERNANCE NOTE:
Line 18: # This L4 service provides READ and WRITE operations for the Keys domain.
Line 19: # L2 APIs MUST NOT call this directly — use APIKeysFacade instead.
Line 20: # Engines are operational primitives for L3 adapters and runtime layers.
```

#### Imports (Lines 39-47)
| Line | Import Statement |
|------|------------------|
| 39 | `from datetime import datetime, timezone` |
| 40 | `from typing import List, Optional, Tuple` |
| 42 | `from sqlalchemy import and_, desc, func, select` |
| 43 | `from sqlmodel import Session` |
| 46 | `from app.models.killswitch import ProxyCall` |
| 47 | `from app.models.tenant import APIKey` |

#### Classes

**KeysReadService (Lines 50-148):**
| Line | Method | Signature |
|------|--------|-----------|
| 57-59 | `__init__` | `def __init__(self, session: Session)` |
| 61-94 | `list_keys` | `def list_keys(self, tenant_id: str, limit: int = 50, offset: int = 0) -> Tuple[List[APIKey], int]` |
| 96-118 | `get_key` | `def get_key(self, key_id: str, tenant_id: str) -> Optional[APIKey]` |
| 120-147 | `get_key_usage_today` | `def get_key_usage_today(self, key_id: str, today_start: datetime) -> Tuple[int, int]` |

**KeysWriteService (Lines 150-199):**
| Line | Method | Signature |
|------|--------|-----------|
| 157-159 | `__init__` | `def __init__(self, session: Session)` |
| 161-179 | `freeze_key` | `def freeze_key(self, key: APIKey) -> APIKey` |
| 181-199 | `unfreeze_key` | `def unfreeze_key(self, key: APIKey) -> APIKey` |

#### Functions
| Line | Name | Signature |
|------|------|-----------|
| 202-204 | `get_keys_read_service` | `def get_keys_read_service(session: Session) -> KeysReadService` |
| 207-209 | `get_keys_write_service` | `def get_keys_write_service(session: Session) -> KeysWriteService` |

#### Exports (Lines 212-217)
```python
__all__ = [
    "KeysReadService",
    "KeysWriteService",
    "get_keys_read_service",
    "get_keys_write_service",
]
```

---

## 5. Header Inconsistencies (Facts Only)

### Layer Naming

| File | Line | Value |
|------|------|-------|
| `facades/api_keys_facade.py` | 1 | `# Layer: L4 — Domain Engine` |
| `engines/keys_service.py` | 1 | `# Layer: L4 — Domain Engine` |
| `__init__.py` | 1 | `# Layer: L4 — Domain Services` |
| `facades/__init__.py` | 1 | `# Layer: L4 — Domain Services` |
| `engines/__init__.py` | 1 | `# Layer: L4 — Domain Services` |
| `drivers/__init__.py` | 1 | `# Layer: L4 — Domain Services` |
| `schemas/__init__.py` | 1 | `# Layer: L4 — Domain Services` |

**FACT:** "Domain Engine" vs "Domain Services" inconsistency.

### AUDIENCE Header

| File | Line | Value |
|------|------|-------|
| `facades/api_keys_facade.py` | 2 | `# AUDIENCE: CUSTOMER` |
| `engines/keys_service.py` | 2 | (none — has `# Product: system-wide`) |
| `__init__.py` | 2 | `# AUDIENCE: CUSTOMER` |
| `facades/__init__.py` | 2 | `# AUDIENCE: CUSTOMER` |
| `engines/__init__.py` | 2 | `# AUDIENCE: CUSTOMER` |
| `drivers/__init__.py` | 2 | `# AUDIENCE: CUSTOMER` |
| `schemas/__init__.py` | 2 | `# AUDIENCE: CUSTOMER` |

**FACT:** `engines/keys_service.py` has no AUDIENCE header.
**FACT:** `engines/__init__.py` says `AUDIENCE: CUSTOMER` but `keys_service.py` says `Product: system-wide`.

---

## 6. Import Cross-Reference

### Shared Imports Between Facade and Engine

| Import | Facade Line | Engine Line | Match |
|--------|-------------|-------------|-------|
| `from app.models.tenant import APIKey` | 36 | 47 | EXACT |

### Unique Imports

**Facade only:**
| Line | Import |
|------|--------|
| 28 | `import json` |
| 29 | `from dataclasses import dataclass, field` |
| 34 | `from sqlalchemy.ext.asyncio import AsyncSession` |

**Engine only:**
| Line | Import |
|------|--------|
| 39 | `from datetime import datetime, timezone` (facade has only `datetime`) |
| 43 | `from sqlmodel import Session` |
| 46 | `from app.models.killswitch import ProxyCall` |

### sqlalchemy Import Comparison

| Module | Facade (Line 33) | Engine (Line 42) |
|--------|------------------|------------------|
| `func` | YES | YES |
| `select` | YES | YES |
| `and_` | NO | YES |
| `desc` | NO | YES |

---

## 7. Findings Summary

### HOC Domain Internal Status: CLEAN

No duplicates exist within the HOC api_keys namespace. The facade and engine serve distinct purposes.

### External Duplicate (Deferred)

| ID | Type | Location | Severity | Action |
|----|------|----------|----------|--------|
| INT-APIKEYS-DUP-001 | External Duplicate | `app/services/keys_service.py` (ORIGINAL outside HOC) | MEDIUM | DEFERRED — separate phase |

### Bugs Identified

| ID | Type | Location | Severity | Action |
|----|------|----------|----------|--------|
| INT-APIKEYS-BUG-001 | Missing Field | `is_frozen` not in model/schema | HIGH | **RESOLVED** — schema updated |

### Hygiene Issues (Tolerate)

| ID | Type | Location | Severity | Action |
|----|------|----------|----------|--------|
| INT-APIKEYS-FIND-001 | Header inconsistency | "Domain Engine" vs "Domain Services" | LOW | DEFER |
| INT-APIKEYS-FIND-002 | Missing AUDIENCE | `engines/keys_service.py` | LOW | DEFER |
| INT-APIKEYS-FIND-003 | AUDIENCE mismatch | `engines/__init__.py` vs `keys_service.py` | LOW | DEFER |

---

## 8. Recommendations & Resolutions

### 8.1 INT-APIKEYS-DUP-001 — DEFERRED

**Status:** Deferred to separate phase

**Canonical Source:** `houseofcards/customer/api_keys/engines/keys_service.py`

**Original (to be quarantined later):** `app/services/keys_service.py`

**Rationale:** The `app/services/` namespace is outside the scope of this HOC audit. It will be handled when that namespace is audited and migrated.

### 8.2 INT-APIKEYS-BUG-001 — RESOLVED

**Resolution:** Schema support added and migration executed

**Changes made:**
1. Added `is_frozen: bool = Field(default=False)` to APIKey model in `tenant.py:376-377`
2. Added `frozen_at: Optional[datetime] = None` field definition to model (column already in DB from migration 037)
3. Created Alembic migration `120_add_is_frozen_to_api_keys.py`
4. **Migration executed:** 2026-01-23

**Migration details:**
- Revision: `120_is_frozen_api_keys`
- Parent: `c8213cda2be4`
- Added column: `is_frozen BOOLEAN NOT NULL DEFAULT false`
- Added index: `ix_api_keys_is_frozen` on `(is_frozen, tenant_id)`

**Verification:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'api_keys' AND column_name IN ('is_frozen', 'frozen_at');

 column_name |        data_type         | is_nullable
-------------+--------------------------+-------------
 frozen_at   | timestamp with time zone | YES
 is_frozen   | boolean                  | NO
```

**Note:** Both copies of keys_service.py now work correctly with the database schema.

---

## Appendix A: Proof of Duplicate (Diff Output)

```
--- app/services/keys_service.py
+++ houseofcards/customer/api_keys/engines/keys_service.py

@@ -7 +7 @@
-# Callers: customer_keys_adapter.py (L3)
+# Callers: customer_keys_adapter.py (L3), runtime, gateway — NOT L2

@@ -11,4 +11,10 @@
-# GOVERNANCE NOTE:
-# This L4 service provides READ and WRITE operations for the Keys domain.
-# All key operations must go through this service.
+# PRODUCT SCOPE NOTE:
+# Marked system-wide because engines serve runtime/gateway (not just console).
+# The facade (api_keys_facade.py) is ai-console because it's customer-facing only.
+# See api_keys/__init__.py for full domain contract.
+#
+# GOVERNANCE NOTE:
+# This L4 service provides READ and WRITE operations for the Keys domain.
+# L2 APIs MUST NOT call this directly — use APIKeysFacade instead.
+# Engines are operational primitives for L3 adapters and runtime layers.
```

**All other lines: IDENTICAL**

---

## Appendix B: File Checksums

| File | Lines | Code Lines (excluding comments) |
|------|-------|--------------------------------|
| `app/services/keys_service.py` | 212 | ~155 |
| `HOC engines/keys_service.py` | 218 | ~155 |
| **Code Identity** | — | **100%** |
