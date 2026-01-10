# Database Authority Contract

**Status:** LOCKED
**Effective:** 2026-01-10
**Reference:** DB-AUTH-001

---

## Authority Declaration (Non-Negotiable)

```
AUTHORITATIVE_DB = neon
LOCAL_DB_ROLE = ephemeral, test-only
```

---

## Rules

### Neon is the ONLY source of truth for:

- Capability registry
- Run history
- Production-like validation
- Governance checks
- SDSR scenario verification
- Trace and incident records
- Policy proposal state

### Local DB is ONLY for:

- Migration dry-runs
- Unit/integration tests
- Synthetic or disposable data
- Schema experiments

---

## Enforcement

**Violation = protocol breach.**

This is not documentation. This is **law**.

---

## Environment Variables (Required)

Every execution context MUST define:

```env
DB_AUTHORITY=<neon|local>
DB_ENV=<prod-like|dev|test>
```

Absence = **hard failure**.

---

## Connection Mapping

| Authority | DATABASE_URL Pattern |
|-----------|---------------------|
| neon | `*neon.tech*` |
| local | `localhost:*` or `127.0.0.1:*` or Docker service |

---

## Decision Table

| Task Type | DB to Use | Reason |
|-----------|-----------|--------|
| Historical truth | Neon | Authoritative |
| Capability state | Neon | Source of truth |
| Run verification | Neon | Non-ephemeral |
| SDSR execution | Neon | Canonical validation |
| Migration testing | Local | Disposable |
| Schema experiments | Local | Safe |
| Unit tests | Local | Isolated |

If the task spans both:
- **Neon = read**
- **Local = write/test**

No exceptions.

---

## The Core Rule

> **Claude must never infer database authority from evidence. Authority is declared, not discovered.**

Discovery is forbidden.
Inference is a violation.
Guessing is not intelligence.

---

## Related

- `docs/governance/DB_AUTH_001_INVARIANT.md` - Formal invariant
- `backend/scripts/_db_guard.py` - Enforcement script
