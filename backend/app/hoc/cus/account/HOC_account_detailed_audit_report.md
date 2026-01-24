# HOC Account Domain Audit Report

**Date:** 2026-01-23
**Updated:** 2026-01-23
**Domain:** `app/houseofcards/customer/account/`
**Scope:** Internal domain audit (duplicates, imports, semantics)
**Reference:** INT-ACCOUNT-AUDIT-001

---

## Executive Summary

| Metric | Count | Severity | Status |
|--------|-------|----------|--------|
| Files Audited | 16 | - | - |
| **CRITICAL Duplicates** | 5 | CRITICAL | INTENTIONAL (acknowledged) |
| **BROKEN Import** | 1 | CRITICAL | **FIXED** |
| Helper Function Duplicates | 2 | MEDIUM | **FIXED** |
| Structural Issues | 2 | LOW | - |
| Triple Duplicate | 1 | HIGH | **RESOLVED** (removed from policies) |

**Overall Health:** HEALTHY - All critical issues remediated

---

## 1. File Inventory

### 1.1 Account Domain Structure

```
app/houseofcards/customer/account/
├── __init__.py (empty)
├── facades/
│   ├── __init__.py
│   ├── accounts_facade.py (minimal/empty)
│   └── notifications_facade.py (minimal/empty)
├── drivers/
│   └── __init__.py
├── schemas/
│   └── __init__.py
├── engines/
│   ├── __init__.py
│   ├── email_verification.py
│   ├── tenant_service.py (630 lines)
│   ├── user_write_service.py (105 lines)
│   ├── profile.py (452 lines)
│   └── identity_resolver.py (199 lines)
├── support/CRM/engines/
│   ├── audit_service.py (886 lines)
│   ├── job_executor.py (521 lines)
│   └── validator_service.py (731 lines)
└── notifications/engines/
    └── channel_service.py (1098 lines)
```

### 1.2 New Shared Utility Created

```
app/houseofcards/customer/general/
├── __init__.py
└── utils/
    ├── __init__.py
    └── time.py (utc_now helper)
```

---

## 2. Remediation Completed

### 2.1 identity_resolver.py - Import Fixed

| Item | Before | After |
|------|--------|-------|
| Line 26 | `from .iam_service import ...` (BROKEN) | `from app.houseofcards.internal.platform.iam.engines.iam_service import ...` |
| Status | BROKEN | **FIXED** |

**IAM Service Canonical Location:**
```
app/houseofcards/internal/platform/iam/engines/iam_service.py
```

---

### 2.2 Legacy Duplicates - Acknowledged as Intentional

The following duplicates in `app/services/` are **intentional** and will be ignored:

| HOC File | Legacy Location | Status |
|----------|-----------------|--------|
| identity_resolver.py | app/services/iam/ | INTENTIONAL |
| tenant_service.py | app/services/ | INTENTIONAL |
| user_write_service.py | app/services/ | INTENTIONAL |
| email_verification.py | app/services/ | INTENTIONAL |
| profile.py | app/services/governance/ | INTENTIONAL |
| audit_service.py | app/services/governance/ | INTENTIONAL |
| job_executor.py | app/services/governance/ | INTENTIONAL |
| channel_service.py | app/services/notifications/ | INTENTIONAL |

---

### 2.3 validator_service.py - Triple Duplicate Resolved

| Location | Status |
|----------|--------|
| `app/services/governance/validator_service.py` | INTENTIONAL (legacy) |
| `app/houseofcards/customer/account/support/CRM/engines/validator_service.py` | CANONICAL |
| `app/houseofcards/customer/policies/engines/validator_service.py` | **REMOVED** |

**Action Taken:** Removed duplicate from policies domain.

---

### 2.4 utc_now() Helper - Extracted to Shared Utility

| Item | Status |
|------|--------|
| Created | `app/houseofcards/customer/general/utils/time.py` |
| Removed from | `tenant_service.py:39-40` |
| Removed from | `user_write_service.py:32-34` |
| Import updated | Both files now import from `general.utils.time` |

**New Canonical Location:**
```python
from app.houseofcards.customer.general.utils.time import utc_now
```

---

## 3. Current Import Analysis

### 3.1 identity_resolver.py (FIXED)

```python
# Line 26-28
from app.houseofcards.internal.platform.iam.engines.iam_service import (
    ActorType, Identity, IdentityProvider,
)
```
**Status:** CORRECT - Uses absolute import to canonical HOC location

### 3.2 tenant_service.py (UPDATED)

```python
# Line 25
from app.houseofcards.customer.general.utils.time import utc_now
# Lines 26-35
from ..models.tenant import (...)
```
**Status:** utc_now import CORRECT, relative model import unchanged

### 3.3 user_write_service.py (UPDATED)

```python
# Line 28
from app.houseofcards.customer.general.utils.time import utc_now
# Line 29
from app.models.tenant import User
```
**Status:** utc_now import CORRECT

---

## 4. Semantic Analysis

### 4.1 Layer Compliance

| File | Declared Layer | Status |
|------|----------------|--------|
| tenant_service.py | L6 Platform | Note: Contains business logic |
| user_write_service.py | L4 Engine | Correct |
| profile.py | L4 Engine | Correct |
| identity_resolver.py | L4 Engine | Correct |
| audit_service.py | L8 Catalyst | Correct |
| job_executor.py | L5 Execution | Correct |
| validator_service.py | L4 Engine | Correct |
| channel_service.py | L4 Engine | Correct |
| general/utils/time.py | L6 Platform | Correct |

### 4.2 Temporal Compliance

All files declare appropriate temporal triggers (api, worker, sync/async).

---

## 5. Remaining Items (Low Priority)

### 5.1 Relative Import in tenant_service.py

```python
from ..models.tenant import (...)
```
**Risk:** LOW - Assumes models exist at account/models/tenant.py
**Status:** Not blocking, monitor for issues

### 5.2 Layer Declaration Review

`tenant_service.py` declares L6 but contains business logic typical of L4.
**Status:** Cosmetic issue, no action required

---

## 6. Audit Summary

| Category | Issues Found | Issues Fixed | Remaining |
|----------|--------------|--------------|-----------|
| Broken Imports | 1 | 1 | 0 |
| Helper Duplicates | 2 | 2 | 0 |
| Triple Duplicates | 1 | 1 | 0 |
| Legacy Duplicates | 8 | N/A | INTENTIONAL |

**All critical and medium issues have been remediated.**

---

## 7. Files Modified During Remediation

| File | Change |
|------|--------|
| `account/engines/identity_resolver.py` | Fixed import path (line 26) |
| `account/engines/tenant_service.py` | Added utc_now import, removed local def, removed unused timezone import |
| `account/engines/user_write_service.py` | Added utc_now import, removed local def and datetime imports |
| `general/__init__.py` | Pre-existing |
| `general/utils/__init__.py` | Created |
| `general/utils/time.py` | Created with utc_now() |
| `policies/engines/validator_service.py` | **DELETED** |

---

**Report Generated:** 2026-01-23
**Report Updated:** 2026-01-23
**Auditor:** Claude (Automated HOC Audit)
**Status:** COMPLETE - All remediations applied
