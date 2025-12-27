# Operating Rules — AOS Phase A.5

**Status:** ACTIVE
**Enforced By:** CI + Claude Instructions
**Last Updated:** 2025-12-26

---

## Rule 1: Truth Preflight Gate

> **No Truth Preflight → No Scenario → No Acceptance → No Merge**

Anything else is process theater.

---

## Enforcement Mechanism

| Layer | Enforcement |
|-------|-------------|
| CI | `.github/workflows/truth-preflight.yml` blocks merge |
| Claude | `CLAUDE.md` instruction blocks reasoning |
| Human | PIN-193/PIN-194 define acceptance criteria |

---

## What This Means

1. **Before ANY scenario (S2-S6) can execute:**
   - CI job `Truth Preflight Gate` must pass
   - Exit code 0 from `scripts/verification/truth_preflight.sh`

2. **If preflight fails:**
   - No scenario execution
   - No acceptance possible
   - No merge to main
   - Fix the failure first

3. **No exceptions:**
   - Cannot bypass "temporarily"
   - Cannot simulate results
   - Cannot assume success
   - Cannot merge with failed preflight

---

## Why This Exists

Historical failures that this prevents:

| P0 ID | Failure | Prevention |
|-------|---------|------------|
| P0-001 | Database mismatch (local vs cloud) | CHECK 1: Runtime DB target |
| P0-005 | In-memory only storage | CHECK 2: No `_runs_store` |
| P0-??? | Silent persistence failure | CHECK 3: Persistence guard |
| P0-??? | API/DB desync | CHECK 5: Count verification |
| P0-??? | Tenant data leak | CHECK 6: Tenant isolation |

---

## Preflight Checks

| Check | What It Verifies |
|-------|------------------|
| CHECK 1 | Backend is healthy and connected to Neon |
| CHECK 2 | No in-memory `_runs_store` in workers.py |
| CHECK 3 | Persistence failure guard exists |
| CHECK 4 | Direct database connectivity |
| CHECK 5 | API count matches DB count |
| CHECK 6 | Invalid tenant returns 0 results |
| CHECK 7 | S1 acceptance run exists |
| CHECK 8 | No incident table pollution |

---

## Related Documents

- **PIN-193:** S1 Truth Propagation (ACCEPTED)
- **PIN-194:** S2 Cost Advisory Truth (FROZEN)
- **PIN-191:** Claude System Test Script
- **CLAUDE.md:** Claude operating instructions

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Created OPERATING_RULES.md |
