# Analytics Domain — Quarantine Zone

**Status:** FROZEN
**Created:** 2026-01-23
**Reference Audit:** `houseofcards/HOC_analytics_detailed_audit_report.md`

---

## Purpose

This folder contains **quarantined duplicate types** from the analytics domain.

These types were identified during the analytics domain deep audit as facade definitions that duplicate engine definitions with 100% overlap.

---

## Rules

1. **DO NOT import from this package** — All imports are forbidden
2. **DO NOT modify these files** — They are FROZEN
3. **DO NOT add new files** — Quarantine is for existing duplicates only

---

## Quarantined Types

| File | Duplicate | Canonical | Issue |
|------|-----------|-----------|-------|
| `anomaly_severity.py` | AnomalySeverity | `engines/cost_anomaly_detector.py::AnomalySeverity` | ANA-DUP-001 |

---

## Canonical Authority

All canonical types for anomaly severity live in:

```
houseofcards/customer/analytics/engines/cost_anomaly_detector.py
```

**Use the engine enum, not the facade duplicate.**

---

## CI Guard

Add this to CI to prevent imports:

```bash
grep -R "houseofcards\.duplicate\.analytics" app/ && exit 1
```

---

## Removal Policy

These files are eligible for removal after:

1. Phase DTO authority unification is complete
2. All facade imports are updated to use engine types
3. Import cleanup is verified

Until then, retain for historical traceability.

---

## Tolerated Issues (Not Quarantined)

| Issue | Type | Status |
|-------|------|--------|
| ANA-FIND-002 | utc_now() local definition in cost_write_service.py | TOLERATED — Utility drift |
| ANA-FIND-003 | Missing AUDIENCE headers | DEFERRED — Hygiene sweep |

These are not quarantined per architectural guidance (utilities and headers handled separately).
