# PIN-508: HOC Structural Remediation Priority Queue

**Status:** ACTIVE
**Created:** 2026-02-01
**Predecessor:** PIN-507 (Laws 0–6, grade A by construction)
**Source:** 10 domain canonical literature files (audited 2026-02-01)
**Scope:** All remaining refactoring, rewiring, and extraction tasks documented in domain literature

---

## Summary

PIN-508 implements the structural remediation queue for the HOC architecture.
It closes all remaining gaps identified after PIN-507's law enforcement:

- **Gap 1:** L5↔L6 boundary enforced by Protocol, not convention
- **Gap 2:** L5 must not receive `session` at all — not just "move DB ops"
- **Gap 3:** DomainBridge returns capability Protocols, not concrete driver types
- **Gap 4:** Tombstones get fail-loud stage with CI enforcement
- **Gap 5:** `app/services/` frozen — no new files or imports permitted
- **Gap 6:** Stub engines raise `NotImplementedError` with `STUB_ENGINE` marker
- **Gap 7:** CI guards codify full negative import space matrix
- **Gap 8:** M25_FROZEN files structurally quarantined in `_frozen/` dirs

---

## Phases Completed

### Phase 6 — CI Guards (6A–6G) ✅

Added checks 8–15 to `scripts/ci/check_init_hygiene.py`:
- Check 8: L5 no `session.execute()` (6A)
- Check 9: L5 no `Session` parameter (6C)
- Check 10: L5 no lazy cross-domain L6 imports (6B)
- Check 11: Negative import space matrix (6D)
- Check 12: No new legacy services (6E)
- Check 13: Tombstone zero dependents (6F)
- Check 14: Stub engines not called without feature flag (6G)
- Check 15: Frozen quarantine validation (Gap 8)

### Phase 1A — Cost Snapshots Extraction ✅

- Created `CostSnapshotsDriverProtocol` in `analytics/L5_schemas/cost_snapshot_schemas.py`
- Created `analytics/L6_drivers/cost_snapshots_driver.py` implementing Protocol
- Rewrote `cost_snapshots_engine.py` — no session, accepts Protocol via constructor

### Phase 1B — Anomaly Bridge Extraction ✅

- Added `insert_incident_from_anomaly()` to `incident_write_driver.py`
- Rewrote `anomaly_bridge.py` — accepts driver, not session
- Factory `get_anomaly_incident_bridge(session)` creates driver internally

### Phase 2A–2C — DomainBridge Capability Wiring ✅

- Created `policies/L5_schemas/domain_bridge_capabilities.py` with:
  - `LessonsQueryCapability(Protocol)`
  - `LimitsQueryCapability(Protocol)`
  - `PolicyLimitsCapability(Protocol)`
- Added capability-returning methods to `domain_bridge.py`
- Updated `policies_handler.py` to inject capabilities via DomainBridge
- Updated engine factories to accept capability injection with legacy fallback

### Phase 4 — Tombstone Removal ✅

- 4A: Removed tombstone re-exports from `threshold_engine.py`
- 4B: Deleted `incident_severity_engine.py` (zero dependents)
- 4C: Deleted `schemas/recovery_decisions.py` (zero dependents)

### Phase 5 — Stub Engine Hardening ✅

Added `# STUB_ENGINE: True` marker and `NotImplementedError` to all public methods:
- `activity/L5_engines/cus_telemetry_engine.py` (already had NotImplementedError)
- `integrations/L5_engines/cus_integration_engine.py` (marker added, no methods)
- `policies/L5_engines/cus_enforcement_engine.py` (3 methods hardened)
- `policies/L5_engines/limits_simulation_engine.py` (1 method hardened)
- `policies/L5_engines/policies_facade.py` (13 methods hardened)

### Phase 7 — M25_FROZEN Quarantine ✅

- Moved `bridges_engine.py` and `dispatcher_engine.py` to `integrations/L5_engines/_frozen/`
- Created `_frozen/__init__.py` with quarantine header
- CI guard validates `_frozen/` directory existence

### Phase 3 — Legacy Services Hard Stop ✅

- CI guard (check 12) blocks new `app/services/` files and imports
- 75+ existing files in frozen allowlist
- HOC equivalent of `incident_write_engine.py` already exists
- Remaining migrations deferred (require design decisions)

---

## Deferred Items

| Item | Reason | Tracked By |
|------|--------|-----------|
| 1C: `bridges_engine.py` extraction | M25_FROZEN (quarantined) | Phase 7 |
| 1D: `dispatcher_engine.py` extraction | M25_FROZEN (quarantined) | Phase 7 |
| 2D: `policies/guard.py` L2→L5 bypass | Requires Loop Model (PIN-487 Part 2) | — |
| 2E: `integrations/adapters/*` cross-domain | Requires L4 orchestration | — |
| 3B–3D: Legacy policy services migration | Design decisions needed | — |
| 3E: Orphan recovery routing | Design decision: L4 or infra? | — |
| Phase 5 implementations | Separate PINs per stub engine | — |

---

## Files Created

| File | Domain | Purpose |
|------|--------|---------|
| `analytics/L6_drivers/cost_snapshots_driver.py` | analytics | L6 driver for cost snapshot DB ops |
| `policies/L5_schemas/domain_bridge_capabilities.py` | policies | Capability Protocols for DomainBridge |
| `integrations/L5_engines/_frozen/__init__.py` | integrations | Quarantine marker |

## Files Deleted

| File | Domain | Reason |
|------|--------|--------|
| `incidents/L5_engines/incident_severity_engine.py` | incidents | Tombstone with zero dependents |
| `hoc_spine/schemas/recovery_decisions.py` | hoc_spine | Tombstone with zero dependents |

## Files Modified

| File | Domain | Change |
|------|--------|--------|
| `scripts/ci/check_init_hygiene.py` | CI | Added checks 8–15 |
| `analytics/L5_schemas/cost_snapshot_schemas.py` | analytics | Added CostSnapshotsDriverProtocol |
| `analytics/L5_engines/cost_snapshots_engine.py` | analytics | Removed session, accepts Protocol |
| `incidents/L6_drivers/incident_write_driver.py` | incidents | Added insert_incident_from_anomaly |
| `incidents/L5_engines/anomaly_bridge.py` | incidents | Removed session, accepts driver |
| `controls/L5_engines/threshold_engine.py` | controls | Removed tombstone re-exports |
| `hoc_spine/orchestrator/coordinators/domain_bridge.py` | hoc_spine | Added capability methods |
| `hoc_spine/orchestrator/handlers/policies_handler.py` | hoc_spine | Injects capabilities via DomainBridge |
| `policies/L5_engines/lessons_engine.py` | policies | Factory accepts driver param |
| `policies/L5_engines/policies_limits_query_engine.py` | policies | Factory accepts driver param |
| `policies/L5_engines/policy_limits_engine.py` | policies | Constructor accepts driver param |
| `policies/L5_engines/cus_enforcement_engine.py` | policies | STUB_ENGINE + NotImplementedError |
| `policies/L5_engines/limits_simulation_engine.py` | policies | STUB_ENGINE + NotImplementedError |
| `policies/L5_engines/policies_facade.py` | policies | STUB_ENGINE + NotImplementedError |
| `activity/L5_engines/cus_telemetry_engine.py` | activity | STUB_ENGINE marker added |
| `integrations/L5_engines/cus_integration_engine.py` | integrations | STUB_ENGINE marker added |

## Files Moved

| From | To | Reason |
|------|-----|--------|
| `integrations/L5_engines/bridges_engine.py` | `integrations/L5_engines/_frozen/bridges_engine.py` | M25_FROZEN quarantine |
| `integrations/L5_engines/dispatcher_engine.py` | `integrations/L5_engines/_frozen/dispatcher_engine.py` | M25_FROZEN quarantine |

---

## Verification

```bash
# All CI checks pass
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
# → 0 blocking violations

# No session.execute in L5 engines (Phase 1)
grep -rn "session.execute" app/hoc/cus/*/L5_engines/*.py
# → 0 hits (allowlisted frozen files excluded)

# No lazy cross-domain L6 imports remaining as primary path (Phase 2)
# Legacy fallback paths retained with DomainBridge as preferred

# All tombstones with zero dependents removed (Phase 4)
# CI check 13 enforces this going forward

# All stub engines have STUB_ENGINE marker (Phase 5)
grep -rn "STUB_ENGINE: True" app/hoc/cus/*/L5_engines/*.py
# → 5 hits

# Frozen quarantine exists (Phase 7)
ls app/hoc/cus/integrations/L5_engines/_frozen/
# → bridges_engine.py, dispatcher_engine.py, __init__.py
```
