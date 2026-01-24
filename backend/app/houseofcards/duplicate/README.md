# HOC Duplicate Quarantine Zone

**Status:** ACTIVE
**Effective:** 2026-01-23
**Reference:** HOC_incidents_deep_audit_report.md, ACTIVITY_DTO_RULES.md

---

## Purpose

This directory contains **quarantined duplicate DTOs** that have been superseded by canonical engine types. These files are:

- **Non-authoritative** — do not use for new development
- **Structurally frozen** — do not modify except header fixes
- **Non-importable** — no production code may import from here

This is a **graveyard**, not a library.

---

## Import Ban (ENFORCED)

**No production code may import from `houseofcards.duplicate`**

Enforcement:
```bash
# CI check - must return empty
grep -rn "from app.houseofcards.duplicate" backend/app/ --include="*.py" | grep -v "duplicate/"
grep -rn "import app.houseofcards.duplicate" backend/app/ --include="*.py" | grep -v "duplicate/"
```

Violations are **blocking**.

---

## Header Contract (MANDATORY)

Every quarantined file MUST contain this header block:

```python
# ============================================================
# DUPLICATE — QUARANTINED
#
# This file is a historical duplicate and MUST NOT be used
# for new development.
#
# Original (Authoritative):
#   <path to canonical file>
#   Class: <CanonicalClassName>
#
# Superseding Type:
#   <path to facade file where this was defined>
#   Class: <DuplicateClassName> (QUARANTINED)
#
# Reason for Quarantine:
#   <Issue ID> — <description>
#
# Status:
#   FROZEN — do not modify
#
# Removal Policy:
#   Remove after import cleanup verified
# ============================================================
```

**No header = invalid quarantine.**

---

## Removal Policy

Quarantined files may be deleted when:

1. All imports have been migrated to canonical types
2. No downstream code references the quarantined type
3. CI validation passes
4. Audit trail updated

---

## Directory Structure

```
duplicate/
├── README.md           # This file
├── activity/           # Activity domain duplicates
│   └── __init__.py     # Empty, no exports
└── incidents/          # Incidents domain duplicates
    └── __init__.py     # Empty, no exports
```

Each domain gets its own subdirectory. Do not mix domains.

---

## What NOT to Do

- Leaving duplicates in-place with "TODO" comments
- Keeping them importable "just in case"
- Letting new code depend on them
- Allowing partial edits
- Forgetting to mark the canonical source

---

*Quarantine is for controlled decay, not storage.*
