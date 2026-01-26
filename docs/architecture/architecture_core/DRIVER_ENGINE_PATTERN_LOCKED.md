# Driver/Engine Pattern — LOCKED

**Status:** LOCKED
**Effective:** 2026-01-23
**Reference:** PIN-468, DRIVER_ENGINE_CONTRACT.md

---

## Pattern Definition (Immutable)

| Layer | Role | Single Sentence |
|-------|------|-----------------|
| **L4 Engine** | Decides *what* should happen | Engines think |
| **L6 Driver** | Performs *effects* only | Drivers touch |

**Invariant:** Decisions ≠ Effects. A file doing both is structurally invalid.

---

## Naming Rules (Enforced)

| Pattern | Status | Enforcement |
|---------|--------|-------------|
| `*_service.py` | **BANNED** | CI blocks creation |
| `*_engine.py` | Required for L4 | CI validates layer header |
| `*_driver.py` | Required for L6 | CI validates layer header |

---

## Engine Contract (L4)

### MUST

- Accept domain inputs (ids, enums, intent objects)
- Call drivers via injected dependency
- Return domain results (schemas, dataclasses)
- Be testable with mocked driver
- Contain all business logic

### MUST NOT

- Import `sqlalchemy`, `sqlmodel`, `Session` (except TYPE_CHECKING)
- Import `app.models.*` ORM classes at runtime
- Construct SQL queries
- Contain transaction management
- Reference table/column names

---

## Driver Contract (L6)

### MUST

- Accept primitives (str, int, UUID, dataclass)
- Perform DB I/O only
- Return raw facts (rows, counts, DTOs)
- Be stateless

### MUST NOT

- Contain business conditionals (`if severity`, `if policy`, `if threshold`)
- Know "why" data is accessed
- Import engines
- Make decisions about data validity

---

## Deviation Process

Any deviation from this pattern requires:

1. **RFC document** with justification
2. **Founder approval** (not engineer approval)
3. **PIN documenting exception** with expiry date

No implicit exceptions. No "temporary" violations.

---

## CI Enforcement (Mandatory)

| Guard | Trigger | Action |
|-------|---------|--------|
| Engine DB imports | `engines/*.py` imports sqlalchemy/sqlmodel | **FAIL BUILD** |
| New service files | `*_service.py` created in hoc | **FAIL BUILD** |
| Driver engine imports | `drivers/*.py` imports from engines | **FAIL BUILD** |
| Missing layer header | Any `.py` without `# Layer:` | **FAIL BUILD** |

---

## Mental Model

> **Engines think. Drivers touch. Adapters combine. Runtime triggers. APIs expose.**

If a file violates this sentence, it is wrong.

---

## Reference Implementation

```
backend/app/services/cus_integration_engine.py  (L4)
backend/app/services/cus_integration_driver.py  (L6)
```

All future splits must match this structure exactly.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-23 | Pattern LOCKED after cus_integration_service.py reference split |
