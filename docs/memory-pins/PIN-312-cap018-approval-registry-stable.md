# PIN-312: CAP-018 Approval & Registry Stabilization

**Status:** COMPLETE
**Created:** 2026-01-05
**Category:** Governance / Registry

---

## Summary

Approved CAP-018 (M25 Integration Platform) as a first-class capability with founder approval, completed all registry validation, and achieved a stable 18-capability registry state.

---

## Tasks Completed

| Task | Description | Result |
|------|-------------|--------|
| T1.1 | Finalize CAP-018 registry entry | Full entry with planes, lifecycle, governance, evidence |
| T1.2 | Verify plane completeness | engine, l2_api, authority, audit_replay all present |
| T1.3 | Evidence link verification | All 6 file paths verified to exist |
| T2.1 | Full registry validation | Passed (after fixing SECTION 2.5 structure) |
| T2.2 | Lifecycle sanity check | cost_simulation=PARTIAL, CLOSED=14 |
| T3.1 | Regenerate gap heatmap | GAP_HEATMAP.md regenerated |
| T3.2 | Verify final gap set | 4 blocking capabilities confirmed |
| T4.1 | Update PIN-306 | CAP-018 approval documented |
| T4.2 | Close PIN-311 | Final closure with registry state |
| Final | check-pr verification | All CAP-018 files annotated and pass |

---

## Registry State Achieved

| Metric | Value |
|--------|-------|
| Total Capabilities | 18 |
| CLOSED | 14 |
| PARTIAL | 1 (cost_simulation) |
| READ_ONLY | 2 (policy_proposals, prediction_plane) |
| PLANNED | 1 (cross_project) |
| Unmapped API Files | 0 |

---

## Files Modified

| File | Change |
|------|--------|
| `docs/capabilities/CAPABILITY_REGISTRY.yaml` | CAP-018 entry added, gap_summary updated, SECTION 2.5 created |
| `docs/capabilities/GAP_HEATMAP.md` | Regenerated |
| `docs/memory-pins/PIN-306-capability-registry-governance.md` | CAP-018 approval section |
| `docs/memory-pins/PIN-311-system-resurvey-registry-aligned.md` | Final closure section |
| `backend/app/api/integration.py` | capability_id: CAP-018 annotation |
| `backend/app/api/recovery.py` | capability_id: CAP-018 annotation |
| `backend/app/api/recovery_ingest.py` | capability_id: CAP-018 annotation |

---

## Key Fix: Registry Validation Error

**Problem:** `legacy_routes` and `platform_infrastructure` were inside the `capabilities:` block, causing validation to fail with "Missing capability_id".

**Solution:** Moved them to new `SECTION 2.5: NON-CAPABILITY METADATA` outside the capabilities section.

---

## Blocking Gaps Remaining (4)

1. **CAP-002 (cost_simulation):** PARTIAL — PLANE_ASYMMETRY, MISSING_AUDIT
2. **CAP-003 (policy_proposals):** READ_ONLY — LIFECYCLE_INCOMPLETE, PLANE_ASYMMETRY
3. **CAP-004 (prediction_plane):** READ_ONLY — no gaps tagged
4. **CAP-017 (cross_project):** PLANNED — INTENTIONALLY_ABSENT

---

## Related PINs

- [PIN-306](PIN-306-capability-registry-governance.md) — Registry governance
- [PIN-311](PIN-311-system-resurvey-registry-aligned.md) — System resurvey

---

## Next Steps

PIN-313 will address governance hardening and gap closure for the remaining 4 capabilities.
