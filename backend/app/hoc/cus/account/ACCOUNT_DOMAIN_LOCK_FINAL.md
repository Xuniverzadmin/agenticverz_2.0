# Account Domain Lock — FINAL
# Status: LOCKED
# Effective: 2026-01-24
# Reference: Phase 3 Directory Restructure (PIN-470)

---

## Domain Status

**LOCKED** — No modifications permitted without explicit unlock command.

| Attribute | Value |
|-----------|-------|
| Lock Date | 2026-01-24 |
| Lock Version | 1.0.0 |
| BLCA Baseline | 0 violations |
| Phase 3 Fixes | COMPLETE |

---

## Domain Nature

> **Account is an IDENTITY & TENANT domain — it manages users, tenants, and authentication contexts.**

Account domain:
- **Manages** — user accounts, tenant configurations, profiles
- **Verifies** — email verification, identity resolution
- **Notifies** — user notifications, channels
- **Supports** — CRM integration, audit logging

Account does NOT:
- Execute business policies (→ Policies domain)
- Track run executions (→ Activity domain)
- Manage incidents (→ Incidents domain)

---

## Locked Artifacts

### L5 Engines (L5_engines/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `accounts_facade.py` | LOCKED | 2026-01-24 | Account management facade |
| `email_verification.py` | LOCKED | 2026-01-24 | Email verification logic |
| `identity_resolver.py` | LOCKED | 2026-01-24 | Identity resolution (L6→L5 reclassified) |
| `notifications_facade.py` | LOCKED | 2026-01-24 | Notifications facade |
| `profile.py` | LOCKED | 2026-01-24 | Profile management (L6→L5 reclassified) |
| `tenant_engine.py` | LOCKED | 2026-01-24 | Tenant business logic |
| `user_write_engine.py` | LOCKED | 2026-01-24 | User write operations |
| `__init__.py` | LOCKED | 2026-01-24 | Engine exports |

### L5 Notifications (L5_notifications/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `engines/channel_engine.py` | LOCKED | 2026-01-24 | Notification channel logic |

### L5 Support (L5_support/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `CRM/engines/audit_engine.py` | LOCKED | 2026-01-24 | CRM audit logic |
| `CRM/engines/job_executor.py` | LOCKED | 2026-01-24 | CRM job execution |
| `CRM/engines/validator_engine.py` | LOCKED | 2026-01-24 | CRM validation logic |

### L5 Schemas (L5_schemas/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `__init__.py` | LOCKED | 2026-01-24 | Schema exports |

### L6 Drivers (L6_drivers/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `accounts_facade_driver.py` | LOCKED | 2026-01-24 | Account DB operations |
| `tenant_driver.py` | LOCKED | 2026-01-24 | Tenant DB operations |
| `user_write_driver.py` | LOCKED | 2026-01-24 | User write DB operations |
| `worker_registry_driver.py` | LOCKED | 2026-01-24 | Worker registry DB operations |
| `__init__.py` | LOCKED | 2026-01-24 | Driver exports |

---

## Phase 3 L5/L6 Reclassification

Files reclassified from L6→L5 based on content analysis (no DB ops):

| File | Old Layer | New Layer | Reason |
|------|-----------|-----------|--------|
| `identity_resolver.py` | L6 | L5 | Pure identity logic, no Session imports |
| `profile.py` | L6 | L5 | Pure profile logic, no Session imports |

---

## Governance Invariants

| ID | Rule | Status | Enforcement |
|----|------|--------|-------------|
| **INV-ACC-001** | L5 cannot import sqlalchemy at runtime | COMPLIANT | BLCA |
| **INV-ACC-002** | L6 drivers pure data access | COMPLIANT | BLCA |
| **INV-ACC-003** | Facades delegate, never query directly | COMPLIANT | Architecture |

---

## Lock Rules

### What Is Locked

1. **Layer assignments** — No file may change its declared layer
2. **File locations** — No file may move between directories
3. **Import boundaries** — L5 engines cannot add sqlalchemy imports

### What Is Allowed (Without Unlock)

1. **Bug fixes** — Within existing file boundaries
2. **Documentation** — Comments, docstrings
3. **Type hints** — Adding TYPE_CHECKING imports
4. **Test coverage** — New tests for existing code

### Unlock Procedure

To modify locked artifacts:
1. Create unlock request with justification
2. Run BLCA after changes
3. Update this lock document
4. Re-lock domain

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock — Phase 3 Directory Restructure complete. 2 L5 engine files (identity_resolver.py, profile.py) reclassified L6→L5. PIN-470. | Claude |

---

**END OF DOMAIN LOCK**
