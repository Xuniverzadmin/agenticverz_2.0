# PIN-427: HISAR Backend Gaps Tracker

**Status:** ACTIVE
**Created:** 2026-01-15
**Category:** UI Pipeline / Backend Gaps
**Milestone:** AURORA L2
**Related PINs:** PIN-422, PIN-426

---

## Summary

This PIN documents the creation of the HISAR Backend Gaps Tracker for
consolidating all backend gaps discovered by HISAR/SDSR verification.

---

## Tracker Location

**Canonical Tracker:** `docs/tracking/HISAR_BACKEND_GAPS_TRACKER.md`

The tracker is maintained in `docs/tracking/` as a working document that
is actively updated as HISAR runs reveal backend gaps.

---

## Purpose

When HISAR/SDSR runs verify backend capabilities against human intent:
- Gaps are discovered (missing provenance, auth failures, schema mismatches)
- Gaps are recorded in the tracker for backend team resolution
- Once fixed, SDSR is re-run to verify the fix
- Resolved gaps move from Active to Resolved section

---

## Current Gap Summary (Full Sweep 2026-01-15)

| Domain | Total Panels | BOUND | BLOCKED | Completion |
|--------|--------------|-------|---------|------------|
| OVERVIEW | 12 | 4 | 8 | 33% |
| ACTIVITY | 15 | 6 | 9 | 40% |
| INCIDENTS | 15 | 6 | 9 | 40% |
| POLICIES | 30 | 4 | 26 | 13% |
| LOGS | 15 | 3 | 12 | 20% |
| **TOTAL** | **87** | **23** | **64** | **26%** |

### Gap Breakdown

| Gap Type | Count | Priority |
|----------|-------|----------|
| AUTH_FAILURE | 24 | P0 - Add public paths |
| ENDPOINT_MISSING | 23 | P1 - Create endpoints |
| SDSR_FAILED | 13 | P2 - Fix responses |
| PROVENANCE_MISSING | 2 | P3 - Add provenance |
| COHERENCY_FAILED | 2 | P4 - Fix route format |

---

## Governance

This tracker follows the **Invariant Immutability Law** (PIN-422):
- SDSR reveals gaps, does not hide them
- Backend is fixed to satisfy intent
- Invariants are never changed to match backend

---

## References

- **Tracker:** `docs/tracking/HISAR_BACKEND_GAPS_TRACKER.md`
- **Doctrine:** PIN-422 (HISAR Execution Doctrine)
- **Blocked Panel:** PIN-426 (OVR-SUM-CI-O1)
- **Script:** `backend/aurora_l2/tools/aurora_sdsr_runner.py`
