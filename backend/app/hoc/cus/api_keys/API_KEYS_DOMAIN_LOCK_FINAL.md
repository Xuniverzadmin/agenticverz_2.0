# API Keys Domain Lock — FINAL
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

> **API Keys is a CREDENTIAL domain — it manages API key lifecycle and authentication.**

API Keys domain:
- **Manages** — API key creation, rotation, revocation
- **Authenticates** — validates API keys for machine-to-machine auth
- **Tracks** — key usage, permissions, scopes

API Keys does NOT:
- Execute business policies (→ Policies domain)
- Manage user accounts (→ Account domain)
- Track run executions (→ Activity domain)

---

## Locked Artifacts

### L5 Engines (L5_engines/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `api_keys_facade.py` | LOCKED | 2026-01-24 | API keys management facade |
| `email_verification.py` | LOCKED | 2026-01-24 | Email verification for keys |
| `keys_engine.py` | LOCKED | 2026-01-24 | Key generation and validation logic |
| `__init__.py` | LOCKED | 2026-01-24 | Engine exports |

### L5 Schemas (L5_schemas/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `__init__.py` | LOCKED | 2026-01-24 | Schema exports |

### L6 Drivers (L6_drivers/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `api_keys_facade_driver.py` | LOCKED | 2026-01-24 | API keys DB operations |
| `keys_driver.py` | LOCKED | 2026-01-24 | Key storage DB operations |
| `__init__.py` | LOCKED | 2026-01-24 | Driver exports |

---

## Phase 3 Directory Restructure

- Adopted layer-prefixed folder naming: `L5_engines/`, `L5_schemas/`, `L6_drivers/`
- Moved facades from old `facades/` folder to `L5_engines/`
- No L5/L6 reclassification needed (all files correctly layered)

---

## Governance Invariants

| ID | Rule | Status | Enforcement |
|----|------|--------|-------------|
| **INV-KEY-001** | L5 cannot import sqlalchemy at runtime | COMPLIANT | BLCA |
| **INV-KEY-002** | L6 drivers pure data access | COMPLIANT | BLCA |
| **INV-KEY-003** | Facades delegate, never query directly | COMPLIANT | Architecture |

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
| 2026-01-24 | 1.0.0 | Initial lock — Phase 3 Directory Restructure complete. Layer-prefixed folder naming adopted. PIN-470. | Claude |

---

**END OF DOMAIN LOCK**
