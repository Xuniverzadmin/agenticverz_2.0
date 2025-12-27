# PIN-212: C1 Telemetry Plane — CI Enforcement

**Status:** 🏗️ ACTIVE
**Phase:** C1
**Date:** 2025-12-27
**Related:** PIN-210 (C1 Specification)

---

## Summary

C1 Telemetry Plane invariants are now enforced by CI. Any violation blocks merge.

---

### Update (2025-12-27)

C1 Telemetry Plane invariants are now enforced by CI. Any violation blocks merge.


## What Was Done

### 1. CI Workflow Created

`.github/workflows/c1-telemetry-guard.yml` — 3 blocking jobs:

| Job | Purpose | Blocks Merge |
|-----|---------|--------------|
| `c1-sql-probes` | Runs 10+ SQL probes against Docker Postgres | **YES** |
| `c1-schema-guard` | Detects forbidden FK/import changes | **YES** |
| `c1-delete-safety` | Drops telemetry table, verifies I1/I3/I6 | **YES** |

### 2. Triggers

- Push to `main`, `develop`, `feature/*`
- PR targeting `main` or `develop`
- Changes to:
  - `backend/alembic/versions/**`
  - `backend/app/telemetry/**`
  - `scripts/verification/c1_telemetry_probes.py`

### 3. What Gets Verified

Every CI run proves:

| Invariant | Description | Probe |
|-----------|-------------|-------|
| I1 | Truth tables independent of telemetry | `truth-independence` |
| I2 | Replay hash-stable | `replay-isolation` |
| I3 | No telemetry-caused incidents | `telemetry-write-failure-safe` |
| I4 | No execution blocking | `no-fk-constraints` |
| I5 | O1 endpoints unaffected | `truth-tables-independent` |
| I6 | Telemetry deletable | `c1-delete-safety` job |

---

## Certification Statement Updated

`docs/certification/C1_CERTIFICATION_STATEMENT.md` now includes:

1. **Evidence Files** — Explicit file listing with Neon as authoritative
2. **Change Policy** — Re-certification trigger table + blocked actions
3. **CI Enforcement** — Reference to workflow and job descriptions

---

## What's Blocked by CI

### Schema Changes

| Change | Action |
|--------|--------|
| Adding FK from truth tables → telemetry | **BLOCKED** |
| Adding FK from telemetry → truth tables | **BLOCKED** |
| Telemetry imports in truth paths | **WARNING** (review required) |

### Probe Failures

Any failed probe = merge blocked. No exceptions.

---

## Files in This Commit

```
.github/workflows/c1-telemetry-guard.yml      # CI workflow
docs/certification/C1_CERTIFICATION_STATEMENT.md  # Updated
docs/certification/C1_HUMAN_UI_VERIFICATION.md    # Template
docs/memory-pins/PIN-210-c1-telemetry-plane.md    # Specification
scripts/verification/c1_telemetry_probes.py       # 10+ probes
scripts/verification/c1_claude_test_pack.md       # Test instructions
scripts/verification/c1_failure_injection_matrix.md  # Failure matrix
scripts/verification/evidence/c1_neon_*.json      # Neon evidence (authoritative)
backend/alembic/versions/060_c1_telemetry_plane.py  # Migration
```

---

## Next Steps

1. **Human UI Verification** — Complete `C1_HUMAN_UI_VERIFICATION.md` checklist
2. **Sign Certification** — Add name and date to certification statement
3. **C2 Design** — Begin prediction layer (C1 unlocks this)

---

## Commit Reference

```
84f2d8c C1 Telemetry Plane: CI enforcement + certification
```

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-27 | Initial CI enforcement wired |
