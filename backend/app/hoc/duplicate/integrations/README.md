# Integrations Domain — Quarantine Zone

**Status:** FROZEN
**Created:** 2026-01-23
**Reference Audit:** `houseofcards/HOC_integrations_detailed_audit_report.md`

---

## Purpose

This folder contains **quarantined duplicate types** from the integrations domain.

These types were identified during the integrations domain deep audit as connector definitions that were duplicated across 3 files with 100% overlap.

---

## Rules

1. **DO NOT import from this package** — All imports are forbidden
2. **DO NOT modify these files** — They are FROZEN
3. **DO NOT add new files** — Quarantine is for existing duplicates only

---

## Quarantined Types

| File | Duplicate | Canonical | Issue |
|------|-----------|-----------|-------|
| `credential.py` | Credential dataclass | `engines/credentials/types.py::Credential` | INT-DUP-001 |
| `credential_service.py` | CredentialService protocol | `engines/credentials/protocol.py::CredentialService` | INT-DUP-002 |

---

## Canonical Authority

All canonical types for connector credentials live in:

```
houseofcards/customer/integrations/engines/credentials/
├── __init__.py      # Package exports
├── types.py         # Credential dataclass (canonical)
└── protocol.py      # CredentialService protocol (canonical)
```

**Use the canonical types, not the quarantined duplicates.**

---

## Original Duplicate Locations

The duplicates were found in these connector files:

| File | Credential Lines | CredentialService Lines |
|------|------------------|-------------------------|
| `http_connector.py` | 99-103 | 106-112 |
| `mcp_connector.py` | 90-94 | 97-103 |
| `sql_gateway.py` | 114-118 | 121-127 |

All three definitions were 100% identical.

---

## CI Guard

Add this to CI to prevent imports:

```bash
grep -R "houseofcards\\.duplicate\\.integrations" app/ && exit 1
```

---

## Removal Policy

These files are eligible for removal after:

1. Phase DTO authority unification is complete
2. All connector imports are updated to use canonical types
3. Import cleanup is verified

Until then, retain for historical traceability.

---

## Tolerated Issues (Not Quarantined)

| Issue | Type | Status |
|-------|------|--------|
| INT-FIND-001 | No canonical source | RESOLVED — Canonical source created |
| INT-FIND-002 | Missing AUDIENCE headers | DEFERRED — Hygiene sweep |

These are not quarantined per architectural guidance.
