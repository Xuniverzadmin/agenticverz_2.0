# INCIDENTS DOMAIN — PHASE-2.5A LOCKED

**Status:** LOCKED
**Date:** 2026-01-23
**Reference:** PIN-468 (Phase-2.5A HOC Layer Extraction)

---

## Lock Declaration

The **Incidents Domain** (`houseofcards/customer/incidents/`) has completed Phase-2.5A extraction.

All engines now delegate persistence to L6 drivers. No raw SQL remains in L4 engines.

---

## Locked Engines (L4)

| Engine | Location |
|--------|----------|
| incident_engine.py | `customer/incidents/engines/` |
| lessons_engine.py | `customer/incidents/engines/` |
| policy_violation_service.py | `customer/incidents/engines/` |
| llm_failure_service.py | `customer/incidents/engines/` |
| postmortem_service.py | `customer/incidents/engines/` |
| incident_pattern_service.py | `customer/incidents/engines/` |

---

## Locked Drivers (L6)

| Driver | Authority | Tables Owned |
|--------|-----------|--------------|
| incident_write_driver.py | INCIDENT_PERSISTENCE | incidents, incident_events, prevention_records, policy_proposals |
| lessons_driver.py | LESSONS_PERSISTENCE | lessons_learned |
| policy_violation_driver.py | POLICY_VIOLATION_PERSISTENCE | prevention_records (violations), incident_events (evidence) |
| llm_failure_driver.py | LLM_FAILURE_PERSISTENCE | run_failures, failure_evidence, worker_runs |
| postmortem_driver.py | POSTMORTEM_ANALYTICS | (read-only) |
| incident_pattern_driver.py | INCIDENT_PATTERN_FACTS | (read-only) |

---

## Invariants (FROZEN)

### L4 Engine Requirements
- NO `sqlalchemy`, `sqlmodel` imports at runtime (TYPE_CHECKING only)
- NO `select()`, `insert()`, `update()` statements
- NO raw SQL (`text()`)
- Business logic decisions ONLY

### L6 Driver Requirements
- NO business branching (`if policy`, `if budget`, `if severity`)
- NO cross-domain imports
- NO retries/sleeps
- Pure persistence ONLY

---

## Forbidden Actions (Until Phase-2.5A Complete on ALL Domains)

- ❌ Adding DB imports to locked engines
- ❌ Moving business logic to drivers
- ❌ Creating new drivers without inventory registration
- ❌ Renaming files (Phase-2.5B scope)

---

## Allowed Actions

- ✅ Bug fixes that preserve L4/L6 separation
- ✅ Adding new driver methods (with inventory registration)
- ✅ Extending engine business logic
- ✅ Unit tests for engines and drivers

---

## Verification Command

```bash
# Verify no raw SQL in incidents engines
grep -rE "(select\(|insert\(|update\(|text\()" \
  backend/app/houseofcards/customer/incidents/engines/

# Expected: No matches (or TYPE_CHECKING only)
```

---

## Next Domain

**P0 Priority:** `customer/policies/engines/`

Begin extraction when this document is acknowledged.

---

## Sign-Off

- **Extracted By:** Claude (PIN-468 Session 4)
- **Registered Drivers:** 6
- **Total Methods:** 31
- **Zero Runtime DB Imports:** ✅ VERIFIED
