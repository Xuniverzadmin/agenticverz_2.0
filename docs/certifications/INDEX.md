# Certifications Index

**Created:** 2025-12-28
**Purpose:** Track certified system phases and their guarantees

---

## What Is Certification?

Certification means a phase or component has been:

1. **Implemented** — Code complete
2. **Tested** — Regression tests pass on authoritative environment
3. **Verified** — Human semantic verification complete
4. **Locked** — No further changes without re-certification

---

## Current Certifications

| Phase | Document | Date | Status |
|-------|----------|------|--------|
| C1: Telemetry | (implicit) | 2025-12-27 | CERTIFIED |
| C2: Prediction Plane | [C2_CERTIFICATION_STATEMENT.md](C2_CERTIFICATION_STATEMENT.md) | 2025-12-28 | CERTIFIED |

---

## Certification Documents

### C2: Prediction Plane

| Document | Purpose |
|----------|---------|
| [C2_CERTIFICATION_STATEMENT.md](C2_CERTIFICATION_STATEMENT.md) | Full C2 certification |

---

## Related PINs

| PIN | Topic |
|-----|-------|
| PIN-221 | C2 Semantic Contract |
| PIN-222 | C2 Implementation Plan |
| PIN-223 | C2-T3 Completion |

---

## Re-Certification Rules

A certification becomes invalid when:

1. Schema changes occur
2. New scenarios added
3. Guardrails modified
4. Language constraints relaxed
5. Redis integration added
6. UI implementation begins

Re-certification requires full regression testing on authoritative environment.

---

## Pending Certifications

| Phase | Document | Status |
|-------|----------|--------|
| O4: Advisory UI | (pending) | DRAFT |
| C3: Optimization | (pending) | LOCKED |
