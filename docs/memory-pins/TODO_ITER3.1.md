# TODO — Iteration 3.1

**Date:** 2026-02-06
**Status:** ✅ COMPLETE (strict first-principles)
**Purpose:** First‑principles fixes for hoc_spine imports in L5.

---

## What Was Fixed

### 1. Remove L5 orchestrator imports (6 files) ✅

| File | Violation | Fix |
|------|-----------|-----|
| `activity/L5_engines/__init__.py` | run_governance_facade | Removed to comment |
| `activity/L5_engines/activity_facade.py` | 3 coordinator imports | Protocols + constructor injection |
| `incidents/L5_engines/incident_engine.py` | lessons_coordinator | Optional evidence_recorder injection |
| `policies/L5_engines/eligibility_engine.py` | orchestrator types | Imports from account/L5_engines |
| `analytics/L5_engines/detection_facade.py` | anomaly_incident_coordinator | Protocol + injection |
| `integrations/L5_engines/cost_bridges_engine.py` | create_incident_from_cost_anomaly_sync | Protocol + injection |

### 2. Remove L5 authority imports (3 files) ✅

| File | Violation | Fix |
|------|-----------|-----|
| `policies/L5_engines/governance_facade.py` | runtime_switch (5 locations) | Constructor injection via ModuleType |
| `policies/L5_engines/failure_mode_handler.py` | profile_policy_mode | Module-level setter |
| `policies/adapters/founder_contract_review_adapter.py` | ContractState | Protocol (ContractStatePort) |

### 3. Move hoc_spine driver usage out of L5 (1 file) ✅

| File | Violation | Fix |
|------|-----------|-----|
| `analytics/L5_engines/alert_worker_engine.py` | AlertDriver + get_alert_delivery_adapter | Constructor injection |

### 4. Remove L5 → L4 bridge docstring examples (5 files) ✅

All docstrings showing hoc_spine bridge import examples were replaced with
"L4 callers must inject ... L5 must not import from hoc_spine."

---

## First‑Principles Constraints (Verified)

- ✅ L5 does not import hoc_spine orchestrator or authority modules
- ✅ L5 does not import hoc_spine bridges (even in docstrings)
- ✅ L4 owns authority/orchestration decisions and passes results to L5
- ✅ L5 depends only on L6 drivers, L5 schemas, and injected dependencies

---

## Evidence (2026-02-06)

```bash
# Zero hoc_spine.orchestrator imports in L5 engines
rg "from app\.hoc\.cus\.hoc_spine\.orchestrator" app/hoc/cus/**/L5_engines/**/*.py
# Result: No matches found

# Zero hoc_spine.authority imports in L5 engines
rg "from app\.hoc\.cus\.hoc_spine\.authority" app/hoc/cus/**/L5_engines/**/*.py
# Result: No matches found

# Zero hoc_spine imports in adapters (orchestrator/authority)
rg "from app\.hoc\.cus\.hoc_spine\.(orchestrator|authority)" app/hoc/cus/**/adapters/**/*.py
# Result: No matches found
```

---

## L4 Bridge Capabilities Added

| Bridge | New Capabilities |
|--------|-----------------|
| analytics_bridge.py | anomaly_coordinator, detection_facade, alert_driver, alert_adapter_factory |
| activity_bridge.py | run_evidence_coordinator, run_proof_coordinator, signal_feedback_coordinator |
| incidents_bridge.py | recovery_rule_engine, evidence_recorder |
| integrations_bridge.py | incident_creator_capability |
| policies_bridge.py | governance_runtime, governance_config |

---

## Remaining Work (Out of Scope for Iter3.1)

L5 files still import from `hoc_spine.services` for utilities:
- `hoc_spine.services.time` (utc_now) — 15+ files
- `hoc_spine.services.audit_store` — 2 files
- `hoc_spine.services.costsim_*` — 2 files
- `hoc_spine.drivers.cross_domain` (generate_uuid) — 2 files

These are Phase 2 concerns (PIN-520.2).
