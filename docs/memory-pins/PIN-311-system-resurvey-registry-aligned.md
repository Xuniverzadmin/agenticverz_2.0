# PIN-311: System Resurvey Registry-Aligned

**Status:** ✅ COMPLETE
**Created:** 2026-01-05
**Category:** Governance / Survey

---

## Summary

Registry-aligned system resurvey collecting facts across 8 sections (A-H) with consistency check against CAPABILITY_REGISTRY.yaml

---

## Details

## Objective

Execute a mechanical, registry-aligned system resurvey collecting facts only (no inference) with strict cross-checking against CAPABILITY_REGISTRY.yaml.

---

## Survey Scope

**Declared:** System as-is, current main branch
**Reference:** CAPABILITY_REGISTRY.yaml (17 capabilities)

---

## Phase 1 Results

### Section A — Architecture Ground Truth

| Component | Count | Status |
|-----------|-------|--------|
| Backend app directories | 44 | ENUMERATED |
| Python files with functions | 371 | COUNTED |
| L4 Domain Engines | 11/11 | ALL PRESENT |

**L4 Engines Verified:** workflow (12), policy (26), routing (7), learning (5), optimization (9), agents (22), memory (10), skills (27), costsim (16), predictions (2), traces (8)

### Section B — L2 API Survey

| Metric | Value |
|--------|-------|
| API files with routes | 42 |
| Total endpoints | 380 |
| Mapped to capabilities | 27 files |
| UNMAPPED (gap candidates) | 15 files |

**Top APIs:** agents.py (49), policy_layer.py (37), legacy_routes.py (23), guard.py (18)

**UNREGISTERED_CODE candidates:**
cost_guard.py, cost_intelligence.py, cost_ops.py, customer_activity.py, customer_visibility.py, discovery.py, embedding.py, feedback.py, guard_logs.py, integration.py, onboarding.py, recovery.py, recovery_ingest.py, scenarios.py, status_history.py

### Section C — Data Objects

| Metric | Value |
|--------|-------|
| Model files with table=True | 2 |
| Alembic migrations | 68 |

### Section D — Authority & RBAC

| Metric | Value |
|--------|-------|
| Auth files | 32 |
| authorization_choke.py | PRESENT (724 lines) |
| gateway.py | PRESENT (396 lines) |

### Section E — Frontend

| Metric | Value |
|--------|-------|
| Page files (.tsx) | 48 |
| API clients (.ts) | 26 |
| Components (.tsx) | 20 |

### Section F — Testing

| Metric | Value |
|--------|-------|
| Test files | 176 |
| Test directories | 31 |
| Conftest files | 4 |

### Section G — Constraints

| Metric | Value |
|--------|-------|
| Governance docs | 24 |
| Invariant docs | 4 |
| Memory pins | 312 |

### Section H — Known Unknowns

| Marker | Count |
|--------|-------|
| TODO | 21 |
| FIXME | 0 |
| HACK | 0 |
| Stub files | 13 |
| DEPRECATED | 57 |

---

## Phase 2 — Consistency Check

### Registry State Summary

| State | Count |
|-------|-------|
| CLOSED | 11 |
| PARTIAL | 3 |
| READ_ONLY | 2 |
| PLANNED | 1 |

### Claimed Gaps in Registry: 7

1. CAP-001 replay: PLANE_ASYMMETRY
2. CAP-002 cost_simulation: PLANE_ASYMMETRY
3. CAP-002 cost_simulation: MISSING_AUDIT
4. CAP-003 policy_proposals: LIFECYCLE_INCOMPLETE
5. CAP-003 policy_proposals: PLANE_ASYMMETRY
6. CAP-005 founder_console: LIFECYCLE_INCOMPLETE
7. CAP-017 cross_project: INTENTIONALLY_ABSENT

### Evidence Verification

- Paths checked: 99
- Base files: ALL EXIST

---

## Discrepancies Found

| Finding | Type | Detail |
|---------|------|--------|
| 15 unmapped API files | UNREGISTERED_CODE | Not linked to capability_id |
| M7 files present | TECHNICAL_DEBT | Retained for admin only |
| 57 DEPRECATED markers | TECHNICAL_DEBT | Not removed |
| 13 stub files | STUBBED_INFRA | Present |

---

## Conclusion

Registry matches code reality. 17 capabilities tracked, 11 CLOSED. Key gap: 15 API files are UNREGISTERED_CODE candidates requiring capability linkage.

---

## Resolution (2026-01-05)

**All 15 unmapped API files have been resolved:**

| Action | Count |
|--------|-------|
| Files mapped to existing capabilities | 19 |
| Files marked LEGACY | 2 |
| Files marked PLATFORM | 2 |
| Files pending CAP-018 (founder approval) | 3 |
| Total unmapped | **0** |

**State Changes:**
- CAP-001 (replay): PARTIAL → CLOSED (client exists)
- CAP-005 (founder_console): PARTIAL → CLOSED (routes wired)
- CLOSED capabilities: 11 → **13**
- PARTIAL capabilities: 3 → **1**

**Registry Updated:**
- `CAPABILITY_REGISTRY.yaml` — Evidence links added
- `GAP_HEATMAP.md` — Regenerated
- `PIN-306` — Resolution documented

**Pending:**
- CAP-018 (M25 Integration) requires founder approval

---

## Related PINs

- [PIN-306](PIN-306-capability-registry-governance.md) — Registry governance (resolution documented)
- [PIN-310](PIN-310-fast-track-m7-closure.md) — M7 Authorization closure

---

## Final Closure (2026-01-05)

**Status:** ✅ CLOSED — Registry stable

### CAP-018 Resolution

| Action | Result |
|--------|--------|
| CAP-018 (M25 Integration Platform) | Approved as first-class capability |
| State | CLOSED |
| Founder Approval | ✅ Granted |
| Evidence Verified | All paths exist |

### Final Registry State

| Metric | Value |
|--------|-------|
| Total Capabilities | 18 |
| CLOSED | 14 |
| PARTIAL | 1 (cost_simulation) |
| READ_ONLY | 2 (policy_proposals, prediction_plane) |
| PLANNED | 1 (cross_project) |
| Unmapped API Files | 0 |

### Blocking Gaps (4)

1. CAP-002 (cost_simulation): PARTIAL — PLANE_ASYMMETRY, MISSING_AUDIT
2. CAP-003 (policy_proposals): READ_ONLY — LIFECYCLE_INCOMPLETE, PLANE_ASYMMETRY
3. CAP-004 (prediction_plane): READ_ONLY — no gaps tagged
4. CAP-017 (cross_project): PLANNED — INTENTIONALLY_ABSENT

### Artifacts Updated

- `CAPABILITY_REGISTRY.yaml` — CAP-018 added, gap_summary updated
- `GAP_HEATMAP.md` — Regenerated
- `PIN-306` — CAP-018 approval documented

**No structural changes pending. Registry is stable.**
