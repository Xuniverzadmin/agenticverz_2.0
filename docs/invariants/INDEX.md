# Invariant Documentation Index

**Status:** ACTIVE
**Reference:** PIN-267 (Test System Protection Rule), PIN-268 (Guidance System Upgrade)

---

## Purpose

This directory contains human-readable documentation of system invariants.
Each invariant is enforced by tests in `backend/tests/invariants/` or other test files.

**Governing Principle (GU-001):**

> Every invariant test must have a doc entry.
> Engineers can discover invariants BEFORE writing code.

---

## Invariant Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Schema** | Database structure guarantees | Constraint exists, column present |
| **Concurrency** | Thread/connection safety | Race condition documentation |
| **Behavioral** | Semantic truth guarantees | Cost chain, immutability |
| **Structural** | Code/architecture constraints | Trigger exists, view present |

---

## Documented Modules

| Module | Document | Tests | PIN |
|--------|----------|-------|-----|
| M10 Recovery | [M10_RECOVERY_INVARIANTS.md](./M10_RECOVERY_INVARIANTS.md) | `tests/invariants/test_m10_invariants.py` | PIN-267 |
| PB-S1 Immutability | [PB_S1_INVARIANTS.md](./PB_S1_INVARIANTS.md) | `tests/test_pb_s1_invariants.py`, `tests/test_pb_s1_behavioral_invariants.py` | PIN-199 |

---

## Template for New Invariant Docs

```markdown
# {Module} Invariants

**Status:** ACTIVE
**Tests:** `tests/invariants/test_{module}_invariants.py`
**Reference:** PIN-XXX

---

## Schema Invariants

### {Constraint Name}

**What Must Be True:**
- {constraint description}

**Why It Exists:**
- {rationale}

**Where Enforced:**
- {test file}:{test function}

**What Breaks If Violated:**
- {consequence}

---

## Concurrency Invariants

### {Race Condition Name}

**Root Cause:**
- {description}

**Correct Pattern:**
- {how to avoid}

**Forbidden "Fixes":**
- {anti-patterns}

**Reference:**
- PIN-XXX, {test file}

---

## Behavioral Invariants

### {Invariant Name}

**Semantic Meaning:**
- {what this guarantees}

**Enforcement:**
- {how enforced}

**Tests:**
- {test functions}
```

---

## Adding New Invariants

1. Write the invariant test in `tests/invariants/test_{module}_invariants.py`
2. Create doc entry in this directory using the template
3. Update this INDEX.md
4. Reference the appropriate PIN

**Rule:** Invariants without documentation are incomplete. Tests without docs are undiscoverable.

---

## References

- PIN-267 (Test System Protection Rule)
- PIN-268 (Guidance System Upgrade)
- CI_REDISCOVERY_MASTER_ROADMAP.md
