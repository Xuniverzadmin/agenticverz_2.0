# PIN-509: HOC Tooling Hardening

**Status:** ACTIVE
**Created:** 2026-02-01
**Predecessor:** PIN-508 (HOC Structural Remediation)
**Scope:** Close 7 meta-gaps identified in PIN-508's final state

---

## Summary

PIN-509 hardens PIN-508's structural remediation with tooling-level enforcement.
PIN-508 established CI detection guards; PIN-509 upgrades them to impossibility-by-construction where feasible.

---

## Gap Analysis (from first-principles audit of PIN-508)

| Gap | Issue | PIN-509 Closure |
|-----|-------|----------------|
| 1 | Session absence enforced by CI, not type erasure | Check 17: L5 Session symbol import ban |
| 2 | DomainBridge enforces routing, not authority | Check 18: Protocol surface baseline (method count cap) |
| 3 | Tombstones enforced but deletion manual | `scripts/ops/collapse_tombstones.py` auto-collapse |
| 4 | Legacy frozen, not isolated | `app/services/__init__.py` deprecation warning |
| 5 | Stub engines claim interface authority | Already addressed by PIN-508 Phase 5 (NotImplementedError) |
| 6 | Frozen code quarantined, not decoupled | Check 16: No imports from `_frozen/` paths |
| 7 | CI guards complete but not generative | `scripts/ops/new_l5_engine.py` + `new_l6_driver.py` scaffolding |

---

## Changes Made

### CI Checks Added (checks 16–18 in `check_init_hygiene.py`)

| Check | Name | Category | Enforces |
|-------|------|----------|----------|
| 16 | `check_frozen_no_imports` | FROZEN_IMPORT_BAN | No imports from `_frozen/` paths outside `_frozen/` |
| 17 | `check_l5_no_session_symbol_import` | L5_SESSION_SYMBOL | L5 engines must not import Session/AsyncSession symbols |
| 18 | `check_protocol_surface_baseline` | PROTOCOL_SURFACE_CREEP | Capability Protocols max 12 methods |

### Scripts Created

| Script | Purpose |
|--------|---------|
| `scripts/ops/collapse_tombstones.py` | Detect + auto-remove zero-dependent tombstones |
| `scripts/ops/new_l5_engine.py` | Scaffold L5 engine with correct headers + Protocol injection |
| `scripts/ops/new_l6_driver.py` | Scaffold L6 driver with correct headers + session pattern |

### Files Modified

| File | Change |
|------|--------|
| `scripts/ci/check_init_hygiene.py` | Added checks 16–18, header updated |
| `app/services/__init__.py` | Added FROZEN + DEPRECATED header, DeprecationWarning |

---

## Allowlists (ratchet pattern — block new violations, tolerate existing)

### L5 Session Symbol Import Allowlist

Pre-existing L5 engines that import Session symbols (tracked for remediation):
- `prevention_engine.py`
- `lessons_engine.py`
- `coordinator_engine.py`
- `cus_health_engine.py`
- `incident_engine.py`
- `customer_killswitch_read_engine.py`

Plus all files in `L5_SESSION_PARAM_ALLOWLIST` from PIN-508.

### Protocol Surface Baseline

Max 12 methods per capability Protocol. Current Protocols at 11 methods:
- `LessonsQueryCapability` (11 methods)
- `CostSnapshotsDriverProtocol` (11 methods)

---

## Verification

```bash
# All CI checks pass (18 checks total)
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
# → 0 blocking violations

# Tombstone auto-collapse dry run
PYTHONPATH=. python3 scripts/ops/collapse_tombstones.py

# Scaffolding test
python3 scripts/ops/new_l5_engine.py --help
python3 scripts/ops/new_l6_driver.py --help
```
