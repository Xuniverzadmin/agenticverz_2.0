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
| C3: Optimization Safety | [C3_CERTIFICATION_STATEMENT.md](C3_CERTIFICATION_STATEMENT.md) | 2025-12-28 | CERTIFIED |
| C4: Multi-Envelope Coordination | [C4_CERTIFICATION_STATEMENT.md](C4_CERTIFICATION_STATEMENT.md) | 2025-12-28 | CERTIFIED |
| C5-S1: Learning from Rollback | [C5_S1_CERTIFICATION_STATEMENT.md](C5_S1_CERTIFICATION_STATEMENT.md) | 2025-12-28 | CERTIFIED |

---

## Certification Documents

### C2: Prediction Plane

| Document | Purpose |
|----------|---------|
| [C2_CERTIFICATION_STATEMENT.md](C2_CERTIFICATION_STATEMENT.md) | Full C2 certification |

### C3: Optimization Safety

| Document | Purpose |
|----------|---------|
| [C3_CERTIFICATION_STATEMENT.md](C3_CERTIFICATION_STATEMENT.md) | Full C3 certification (69 tests, S1/S2/S3) |

### C4: Multi-Envelope Coordination

| Document | Purpose |
|----------|---------|
| [C4_CERTIFICATION_STATEMENT.md](C4_CERTIFICATION_STATEMENT.md) | Full C4 certification (14 coordination tests, 83 total optimization tests) |

### C5-S1: Learning from Rollback Frequency

| Document | Purpose |
|----------|---------|
| [C5_S1_CERTIFICATION_STATEMENT.md](C5_S1_CERTIFICATION_STATEMENT.md) | Full C5-S1 certification (27 tests, 6/6 guardrails, 46/46 acceptance criteria) |

---

## Related PINs

| PIN | Topic |
|-----|-------|
| PIN-221 | C2 Semantic Contract |
| PIN-222 | C2 Implementation Plan |
| PIN-223 | C2-T3 Completion |
| PIN-225 | C3 Entry Conditions (CERTIFIED) |
| PIN-226 | C3 Closure and C4 Bridge |
| PIN-230 | C4 Entry Conditions (FROZEN) |
| PIN-231 | C4 Certification Complete |
| PIN-232 | C5 Entry Conditions (FROZEN) |

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
| C5-S2+: Additional Learning Scenarios | (pending) | LOCKED |
