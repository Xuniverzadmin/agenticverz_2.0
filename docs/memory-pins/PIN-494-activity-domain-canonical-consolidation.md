# PIN-494: Activity Domain — Canonical Consolidation

**Created:** 2026-01-31
**Status:** COMPLETE
**Category:** Architecture / Domain Consolidation
**Related PINs:** PIN-470 (HOC Layer Inventory), PIN-484 (HOC Topology V2.0.0), PIN-493 (Incidents Domain)

---

## Summary

Completed full consolidation of the activity domain: two-pass analysis (second skeptical of first), naming violation fixes, canonical registration, literature generation, and deterministic tally verification. Second domain after incidents pilot.

## Scope

- **Physical files:** 16 (8 L5_engines + 3 L6_drivers + 2 __init__.py + 1 L4 handler + 1 deprecated + 1 deprecated excluded)
- **Active scripts:** 14 (excluding __init__.py and .deprecated)
- **Stub engines:** 4 (attention_ranking, cost_analysis, pattern_detection, signal_feedback)
- **L4 Operations:** 4 (activity.query, activity.signal_fingerprint, activity.signal_feedback, activity.telemetry)

## Key Decisions

### 1. Zero Duplicates Confirmed
No duplicate scripts found in activity domain. Each file has a distinct purpose.

### 2. All 14 Active Scripts Declared Canonical
Every active script has a unique purpose. Full registry in `ACTIVITY_CANONICAL_SOFTWARE_LITERATURE.md`.

### 3. Three Naming Violations Fixed
| ID | Old Name | New Name | Status |
|----|----------|----------|--------|
| N1 | run_signal_service.py | run_signal_driver.py | FIXED — class RunSignalDriver, alias preserved |
| N2 | cus_telemetry_service.py | cus_telemetry_engine.py | FIXED — header updated, L4 handler updated |
| N3 | orphan_recovery.py | orphan_recovery_driver.py | FIXED — header updated with rename note |

### 4. Four Stub Engines Identified
All stub engines return empty/mock data. Need ideal contractor analysis post-all-domain:
- `attention_ranking_engine.py` — signal prioritization algorithm needed
- `cost_analysis_engine.py` — cost anomaly detection algorithm needed
- `pattern_detection_engine.py` — pattern recognition algorithm needed
- `signal_feedback_engine.py` — persistence layer needed (audit_ledger integration)

### 5. Deferred Issues
| ID | Issue | Severity |
|----|-------|----------|
| V1 | controls/threshold_driver.py (L6) imports activity/run_signal_driver.py (L6) — cross-domain L6→L6 | HIGH |
| L1 | cus_telemetry_engine.py imports from app.services (HOC→legacy) | MEDIUM |
| W1 | orphan_recovery_driver.py called from int/agent/main.py via legacy path (.services.orphan_recovery) | MEDIUM |
| S1-S4 | 4 stub engines need ideal contractor analysis | DEFERRED |

## Cross-Domain Dependencies

- Activity ↔ Controls: Threshold evaluation (bidirectional via __init__.py re-exports)
- Correct pattern per V2.0.0: L6 control → L5 control → L4 runtime → L5 activity → L6 activity
- Current V1 violation: L6 control (threshold_driver) directly imports L6 activity (run_signal_driver)

## Artifacts Produced

| Artifact | Path |
|----------|------|
| Full Literature | `literature/hoc_domain/activity/ACTIVITY_CANONICAL_SOFTWARE_LITERATURE.md` |
| Tally Script | `scripts/ops/hoc_activity_tally.py` |
| Memory PIN | `docs/memory-pins/PIN-494-activity-domain-canonical-consolidation.md` |

## Lessons Applied from Incidents (PIN-493)

| # | Lesson | Applied |
|---|--------|---------|
| L1 | Overlap detection must consider role | Yes — no overlaps found |
| L3 | L6→L5 imports are common violation pattern | Yes — V1 is L6→L6 cross-domain |
| L6 | Naming violations break automated classification | Yes — fixed 3 naming violations first |

## New Lessons (for subsequent domains)

| # | Lesson | Impact |
|---|--------|--------|
| A1 | Stub engines are common in newer domains — need ideal contractor analysis | Track across all domains |
| A2 | Re-export stubs (HOC→legacy) should not be compared with legacy | Focus only within HOC for cleansing |
| A3 | Cross-domain __init__.py re-exports blur domain boundaries | May need cleanup post-all-domain |
| A4 | Legacy caller paths (.services.*) need migration to HOC paths | Track as wiring issue |

## Verification Commands

```bash
python3 scripts/ops/hoc_activity_tally.py          # 9/9 PASS expected
```
