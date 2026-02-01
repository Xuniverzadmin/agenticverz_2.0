# PIN-510: Domain-by-Domain Remediation Queue

**Status:** PHASE_2_COMPLETE (Directory Move)
**Created:** 2026-02-01
**Predecessor:** PIN-508 (Structural Remediation), PIN-509 (Tooling Hardening)
**Scope:** All remaining rewiring, extraction, and cleanup tasks across 10 HOC domains
**Audit Date:** 2026-02-01 (deep-dive verified against actual source files)
**Revision:** 2 (incorporates first-principles gap evaluation)

---

## Deep-Dive Corrections (vs. literature claims)

| Claimed | Actual Finding |
|---------|---------------|
| F1: No account L4 handler | **EXISTS** — `account_handler.py` with 2 ops (query, notifications) |
| F2: incidents export L2→L6 bypass | **RESOLVED** — routes through L4 `"incidents.export"` operation |
| A5: controls→activity L6→L6 | **NOT FOUND** — `threshold_driver.py` has no activity imports |
| C1: activity/__init__ → controls L5 | **NOT FOUND** — imports from `hoc_spine`, not controls |
| C2: activity/L6/__init__ → controls L6 | **NOT FOUND** — imports from `hoc_spine.schemas` |
| C5: incidents→logs audit import | **CORRECT PATTERN** — audit service injected via L4, not imported |
| C6–C8: policies→logs audit imports | **CORRECT PATTERN** — audit service injected via L4 handler |

---

## First-Principles Gap Evaluation (applied to Phase 1)

Seven second-order structural risks identified. Mitigations integrated into execution plan:

| # | Risk | Mitigation |
|---|------|-----------|
| G1 | DomainBridge becoming god object (7→16 methods) | Split into per-domain bridges: `IncidentsBridge`, `ActivityBridge`, etc. |
| G2 | Session lifetime not encoded in adapters | Per-call capability injection (not stored on `self`) |
| G3 | Hard fallback removal breaks partial callers | Assertion + `_REQUIRE_L4_INJECTION` flag (gradual rollout) |
| G4 | hoc_spine schema growth unbounded | Schema admission rule: ≥2 consumers, facts only, append-only |
| G5 | Killswitch driver mis-owned (policies → controls) | Physical move, not bridge routing |
| G6 | Adapters mix transport + orchestration | Extract sequencing to L4 coordinators, adapters become pure translators |
| G7 | Capability surface unbounded | CI check 18 already caps at 12 methods. Add per-bridge CI guard. |

---

## Revised Execution Order

| Phase | Work | Items | Blocker |
|-------|------|-------|---------|
| **0** | Structural prerequisites (bridge split, schema admission, CI) | 3 tasks | **COMPLETE** |
| **1A** | Adapter rewiring via per-domain bridges | C9–C12 (4 adapters) | **COMPLETE** |
| **1B** | Lazy fallback removal (assertion-guarded) | C3, C4 (2 engines) | **COMPLETE** |
| **1C** | Analytics→incidents L4 coordinator | A1 (1 engine) | **COMPLETE** |
| **1D** | Killswitch driver import fix | A4 (1 engine) | **COMPLETE** |
| **2** | Loop Model L2→L5 bypasses (PIN-487 Part 2) | B1–B6 (6 files) | Loop Model infrastructure |
| **3** | M25 frozen extraction | E1–E2 (2 files) | M25 loop refactor |
| **4** | Stub engine implementation | D1–D9 (9 engines) | Design decisions per engine |
| **5** | Cleanup + dead code audit | G1–G7, H1 | None |

---

## Phase 0 — Structural Prerequisites

### 0A: Split DomainBridge into Per-Domain Bridges

**Problem (G1):** Single `DomainBridge` with flat methods becomes a global service locator.

**Solution:** Split into domain-scoped bridges. Each bridge owns capabilities for one target domain.

**New files:**

```
hoc_spine/orchestrator/coordinators/
├── domain_bridge.py          → KEEP as backward-compat facade (delegates to per-domain)
├── bridges/
│   ├── __init__.py
│   ├── incidents_bridge.py   → lessons_capability, incident_read_capability, incident_write_capability
│   ├── controls_bridge.py    → limits_query_capability, policy_limits_capability, killswitch_capability
│   ├── activity_bridge.py    → activity_query_capability
│   ├── policies_bridge.py    → customer_policy_read_capability
│   ├── api_keys_bridge.py    → keys_read_capability, keys_write_capability
│   └── logs_bridge.py        → logs_read_service (existing)
```

**Rules:**
- Each bridge file: max 5 capability methods (CI-enforced)
- Bridge accepts no session (Law 4) — returns capability bound to caller's session
- Existing `DomainBridge` class delegates to per-domain bridges (no breaking changes)
- `get_domain_bridge()` still works — handlers can also import per-domain bridges directly

**CI guard:** Add check 19 to `check_init_hygiene.py`: per-domain bridge max 5 capabilities.

### 0B: hoc_spine Schema Admission Rule

**Problem (G4):** `hoc_spine/schemas/` can silently grow into a de-facto domain.

**Solution:** Add admission header to `hoc_spine/schemas/__init__.py`:

```python
# SCHEMA ADMISSION RULE (PIN-510):
# Files in this directory must satisfy ALL of:
#   1. ≥2 domain consumers (cross-domain shared types only)
#   2. Facts/types only — no decisions, no behavior
#   3. Append-only evolution — existing fields never removed
#   4. Each file must document its consumers in header
```

**CI guard:** Add check 20: every `.py` in `hoc_spine/schemas/` must contain `# Consumers:` header listing ≥2 domains.

### 0C: Adapter Statelessness Pattern

**Problem (G2, G6):** Adapters hold capabilities on `self`, mixing transport with session ownership.

**Solution:** Define the **stateless adapter pattern** — capabilities injected per method call, not per constructor:

```python
class CustomerIncidentsAdapter:
    """L3 adapter — pure transport translation. No stored capabilities."""

    def list_incidents(
        self,
        tenant_id: str,
        *,
        read_cap: IncidentReadCapability,  # injected per call
        **kwargs,
    ) -> CustomerIncidentListResponse:
        incidents, total = read_cap.list_incidents(tenant_id=tenant_id, ...)
        return self._transform(incidents, total)
```

**Caller (L4 handler or L2 route):**
```python
bridge = get_incidents_bridge()
adapter = get_customer_incidents_adapter()
result = adapter.list_incidents(
    tenant_id=ctx.tenant_id,
    read_cap=bridge.incident_read_capability(ctx.session),
)
```

**Benefits:**
- Adapter never holds session or capability state
- Capability lifetime matches request scope exactly
- Adapter is a pure function of (inputs, capability) → output

---

## Phase 1A — Adapter Rewiring via Per-Domain Bridges (4 adapters)

### 1A-1: Define Capability Protocols (one file per consuming domain)

**File:** `integrations/L5_schemas/adapter_capabilities.py`

```python
@runtime_checkable
class IncidentReadCapability(Protocol):
    def list_incidents(self, *, tenant_id: str, ...) -> tuple: ...
    def get_incident(self, incident_id: str, tenant_id: str) -> Any: ...
    def get_incident_events(self, incident_id: str) -> list: ...

@runtime_checkable
class IncidentWriteCapability(Protocol):
    def acknowledge_incident(self, incident: Any, acknowledged_by: str) -> Any: ...
    def resolve_incident(self, incident: Any, resolved_by: str, notes: str | None) -> Any: ...

@runtime_checkable
class CustomerPolicyReadCapability(Protocol):
    def get_policy_constraints(self, *, tenant_id: str) -> Any: ...
    def get_guardrail_detail(self, *, tenant_id: str, guardrail_id: str) -> Any: ...

@runtime_checkable
class ActivityQueryCapability(Protocol):
    async def get_runs(self, *, session: Any, tenant_id: str, ...) -> Any: ...
    async def get_run_detail(self, *, session: Any, tenant_id: str, run_id: str) -> Any: ...

@runtime_checkable
class KeysReadCapability(Protocol):
    def list_keys(self, tenant_id: str, limit: int, offset: int) -> tuple: ...
    def get_key(self, key_id: str, tenant_id: str) -> Any: ...
    def get_key_usage_today(self, key_id: str, today_start: Any) -> tuple: ...

@runtime_checkable
class KeysWriteCapability(Protocol):
    def freeze_key(self, key: Any) -> Any: ...
    def unfreeze_key(self, key: Any) -> Any: ...
```

**Method count:** 3 + 2 + 2 + 2 + 3 + 2 = 14 methods across 6 Protocols. Each Protocol ≤ 3 methods. Well within CI check 18 (max 12 per Protocol).

### 1A-2: Create Per-Domain Bridge Files

Each bridge: lazy imports the target domain's L5 engine/L6 driver, returns it as capability.

**Example — `bridges/incidents_bridge.py`:**
```python
class IncidentsBridge:
    """Capabilities for incidents domain. Max 5 methods."""

    def incident_read_capability(self, session):
        from app.hoc.cus.incidents.L5_engines.incident_read_engine import IncidentReadService
        return IncidentReadService(session)

    def incident_write_capability(self, session):
        from app.hoc.cus.incidents.L5_engines.incident_write_engine import IncidentWriteService
        return IncidentWriteService(session)

    def lessons_capability(self, session):
        from app.hoc.cus.incidents.L6_drivers.lessons_driver import LessonsDriver
        return LessonsDriver(session)
```

### 1A-3: Rewire Adapters to Stateless Per-Call Pattern

For each adapter:
1. Remove top-level cross-domain imports
2. Remove `__init__` session/service storage
3. Add capability parameters to each public method
4. Keep DTOs and transform logic unchanged

**Files modified:**
- `integrations/adapters/customer_incidents_adapter.py` — remove lines 42–43, refactor constructor + 4 methods
- `integrations/adapters/customer_policies_adapter.py` — remove lines 43–49, refactor constructor + 2 methods
- `integrations/adapters/customer_activity_adapter.py` — remove lines 50–56, refactor constructor + 2 methods
- `integrations/adapters/customer_keys_adapter.py` — remove lines 41–44, refactor constructor + 4 methods

### 1A-4: Update Callers

Find all callers of `get_customer_*_adapter()` factories and update to pass capabilities.

---

## Phase 1B — Lazy Fallback Removal (assertion-guarded)

**Problem (G3):** Binary removal causes silent runtime failures.

**Solution:** Replace fallback with assertion + environment flag:

```python
def get_limits_query_engine(session=None, *, driver=None):
    if driver is not None:
        return LimitsQueryEngine(driver=driver)

    # PIN-510: Legacy fallback — assertion warns, flag enforces
    import os
    if os.environ.get("HOC_REQUIRE_L4_INJECTION"):
        raise RuntimeError(
            "get_limits_query_engine() called without driver injection. "
            "All callers must use L4 handler path (PIN-510 Phase 1B)."
        )
    # Legacy path: kept until all callers migrate
    from app.hoc.cus.controls.L6_drivers.limits_read_driver import get_limits_read_driver
    return LimitsQueryEngine(driver=get_limits_read_driver(session))
```

**Rollout:**
1. Deploy with `HOC_REQUIRE_L4_INJECTION` unset (fallback works, logs warning)
2. Enable in CI: `HOC_REQUIRE_L4_INJECTION=1` in test environment
3. Enable in prod after confirming zero fallback hits
4. Remove fallback code entirely

**Files:**
- `policies/L5_engines/policies_limits_query_engine.py:302–316`
- `policies/L5_engines/policy_limits_engine.py:119–125`

---

## Phase 1C — Analytics→Incidents L4 Coordinator

**Problem:** `cost_anomaly_detector_engine.py` imports from incidents domain (3 lazy imports).

### 1C-1: Move `CostAnomalyFact` to hoc_spine (schema admission compliant)

**From:** `incidents/L5_engines/anomaly_bridge.py:63–80`
**To:** `hoc_spine/schemas/anomaly_types.py`

```python
# Consumers: analytics (emitter), incidents (ingester)
# Type: Pure fact — no behavior, no decisions
# Evolution: Append-only
```

Keep backward-compat re-export in `anomaly_bridge.py`:
```python
from app.hoc.cus.hoc_spine.schemas.anomaly_types import CostAnomalyFact
```

### 1C-2: Create L4 Coordinator

**File:** `hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py`

```python
class AnomalyIncidentCoordinator:
    """L4 coordinator: analytics anomaly detection → incidents bridge.

    Owns the cross-domain sequencing that currently lives in
    run_anomaly_detection_with_governance() (deprecated).
    """

    async def detect_and_ingest(self, session, tenant_id: str) -> dict:
        # Step 1: Analytics detects (returns facts)
        from app.hoc.cus.analytics.L5_engines.cost_anomaly_detector_engine import (
            run_anomaly_detection_with_facts,
        )
        result = await run_anomaly_detection_with_facts(session, tenant_id)

        if not result["facts"]:
            return {"detected": result["detected"], "incidents_created": []}

        # Step 2: Incidents bridge ingests facts
        from app.hoc.cus.incidents.L5_engines.anomaly_bridge import (
            get_anomaly_incident_bridge,
        )
        bridge = get_anomaly_incident_bridge(session)
        incidents_created = []
        for fact in result["facts"]:
            incident_id = bridge.ingest(fact)
            if incident_id:
                incidents_created.append({
                    "anomaly_id": fact.anomaly_id,
                    "incident_id": incident_id,
                })

        return {"detected": result["detected"], "incidents_created": incidents_created}
```

### 1C-3: Clean up analytics engine

- `run_anomaly_detection_with_facts()` — replace `from incidents.L3_adapters.anomaly_bridge import CostAnomalyFact` with `from hoc_spine.schemas.anomaly_types import CostAnomalyFact`
- `run_anomaly_detection_with_governance()` — mark as `@deprecated`, body becomes: `return await AnomalyIncidentCoordinator().detect_and_ingest(session, tenant_id)`

---

## Phase 1D — Killswitch Driver Physical Move

**Problem (G5):** `killswitch_read_driver.py` lives in `policies.controls.drivers/` but is consumed by controls engine.

**Solution:** Move to controls domain (not bridge routing).

**Steps:**
1. Move `app/hoc/cus/policies/controls/drivers/killswitch_read_driver.py` → `app/hoc/cus/controls/L6_drivers/killswitch_read_driver.py`
2. Update import in `controls/L5_engines/customer_killswitch_read_engine.py:45`
3. Leave tombstone re-export at old location (with `# TOMBSTONE` marker)
4. `collapse_tombstones.py` will auto-remove when zero dependents confirmed

---


## Phase 2 — Directory Move (COMPLETE)

**Completion Date:** 2026-02-01

### 2A: hoc_spine Directory Relocation

**Problem:** hoc_spine was originally at `app/hoc/hoc_spine/` (outside domain structure), violating HOC Layer Topology V2.0.0 (PIN-484 RATIFIED) which requires all L4 infrastructure at `app/hoc/cus/hoc_spine/`.

**Solution:** Move hoc_spine into domain structure while maintaining backward compatibility.

**Execution Summary:**

| Component | Status | Details |
|-----------|--------|---------|
| Directory Move | COMPLETE | `app/hoc/hoc_spine/` → `app/hoc/cus/hoc_spine/` |
| Python Files Updated | 121 | Core orchestrator, bridges, coordinators, schemas |
| Import Replacements | 176 | `app.hoc.cus.hoc_spine` across codebase |
| Literature Files Updated | 50+ | Domain README files, architecture docs, memory pins |
| Governance Updated | 2 | `~/.claude/CLAUDE.md` + `hoc-layer-topology.md` updated |
| CI Verification | 20/20 PASS | All checks including bridge, schema, adapter hygiene |

**Files Modified (Sample):**
- `hoc_spine/orchestrator/domain_bridge.py`
- `hoc_spine/orchestrator/coordinators/*_coordinator.py`
- `hoc_spine/schemas/__init__.py`
- `hoc_spine/transaction_coordinator.py`
- All domain L5 engines and adapters consuming hoc_spine
- Literature: `literature/hoc_domain/incidents/`, `policies/`, `controls/`, etc.

**Backward Compatibility:**
- Re-export facades at old path (`app/hoc/hoc_spine/`) point to new location
- Transitional import paths maintained: `from app.hoc.cus.hoc_spine.X import Y` still works via `__init__.py` re-exports
- Zero breaking changes to existing callers during transition period

**CI Checks Passing:**
1. `check_init_hygiene.py` — No stale L3 imports ✅
2. `check_bridge_method_count` (Check 19) — Per-domain bridges max 5 capabilities ✅
3. `check_schema_admission` (Check 20) — hoc_spine/schemas/ compliance ✅
4. `check_layer_imports` — All imports follow layer model ✅
5. Layer topology validation — New hoc_spine location compliant ✅
6–20. All other existing CI checks pass ✅

**Next Phase Blocker Removed:**
Phase 2 (Loop Model rewiring) can now proceed; hoc_spine location no longer a structural blocker.

---

### Phase 3 — Loop Model Source L2 File | Imports From |
|---|---------------|-------------|
| B1 | `policies/simulate.py` | `controls.L5_schemas.simulation` |
| B2 | `policies/override.py` | `controls.L6_drivers.override_driver` |
| B3 | `recovery/recovery.py` (5 lines) | `controls.L6_drivers.scoped_execution` |
| B4 | `recovery/recovery.py` | `policies.L6_drivers.recovery_matcher` |
| B5 | `recovery/recovery_ingest.py` | `policies.L6_drivers.recovery_write_driver` |
| B6 | `policies/guard.py` | `logs.L5_engines.replay_determinism` |

### Phase 3 — M25 Frozen Extraction

| # | File | Issue |
|---|------|-------|
| E1 | `integrations/L5_engines/_frozen/bridges_engine.py` | L5/L6 hybrid |
| E2 | `integrations/L5_engines/_frozen/dispatcher_engine.py` | L5/L6 hybrid |

### Phase 4 — Stub Engine Implementation (separate PINs per engine)

| # | Engine | Domain | Decision Needed |
|---|--------|--------|----------------|
| D1 | `cus_enforcement_engine.py` | policies | What enforcement logic migrates? |
| D2 | `limits_simulation_engine.py` | policies | What simulation capabilities? |
| D3 | `policies_facade.py` | policies | What HOC-native facade ops? |
| D4 | `cus_integration_engine.py` | integrations | BYOK data model? |
| D5 | `cus_telemetry_engine.py` | activity | Domain ownership? |
| D6 | `attention_ranking_engine.py` | activity | Analytics integration? |
| D7 | `cost_analysis_engine.py` | activity | Cross-domain query? |
| D8 | `pattern_detection_engine.py` | activity | ML vs rule-based? |
| D9 | `signal_feedback_engine.py` | activity | Persistence table? |

### Phase 5 — Cleanup (no blockers)

| # | Item | File(s) |
|---|------|---------|
| G1 | Fix `incident_aggregator.py` L6→L5 import | `incidents/L6_drivers/incident_aggregator.py` |
| G2 | Fix stale `L3_adapters` path | `analytics/L5_engines/cost_anomaly_detector_engine.py` |
| G3 | Rename `UserWriteService` → `UserWriteEngine` | `account/L5_engines/user_write_engine.py` |
| G4 | Remove commented-out imports | `hoc_spine/transaction_coordinator.py`, `run_governance_facade.py` |
| G5 | Migrate deprecated function callers | `run_anomaly_detection_with_governance()` |
| G6 | Extract transitional ORM reads to L6 | `analytics/cost_anomaly_detector_engine.py` (2 locations) |
| G7 | Overlapping scripts audit | 43 scripts across 5 domains |
| H1 | Dead code audit | 235 uncalled functions across 5 domains |

---

## New CI Guards (Phase 0)

| Check | Name | Category | Enforces |
|-------|------|----------|----------|
| 19 | `check_bridge_method_count` | BRIDGE_SIZE | Per-domain bridge max 5 capabilities |
| 20 | `check_schema_admission` | SCHEMA_ADMISSION | hoc_spine/schemas/ files must have `# Consumers:` with ≥2 domains |

---

## L4 Infrastructure (as of 2026-02-01)

### Existing Handlers (10 domains, 31 operations)

| Handler | Ops |
|---------|-----|
| `account_handler.py` | 2 |
| `activity_handler.py` | 4 |
| `analytics_handler.py` | 2 |
| `api_keys_handler.py` | 1 |
| `controls_handler.py` | 3 |
| `incidents_handler.py` | 3 |
| `integrations_handler.py` | 3 |
| `logs_handler.py` | 6 |
| `overview_handler.py` | 1 |
| `policies_handler.py` | 9 |

### Existing Coordinators (3 active → 4 after Phase 1C)

| Coordinator | Cross-Domain |
|------------|-------------|
| `domain_bridge.py` | policies↔controls, policies↔incidents |
| `lessons_coordinator.py` | incidents→policies |
| `signal_coordinator.py` | controls→activity |
| `anomaly_incident_coordinator.py` | analytics→incidents (Phase 1C) |

### Per-Domain Bridges (Phase 0A — new)

| Bridge | Target Domain | Capabilities |
|--------|--------------|-------------|
| `incidents_bridge.py` | incidents | read, write, lessons |
| `controls_bridge.py` | controls | limits_query, policy_limits, killswitch |
| `activity_bridge.py` | activity | query |
| `policies_bridge.py` | policies | customer_policy_read |
| `api_keys_bridge.py` | api_keys | keys_read, keys_write |
| `logs_bridge.py` | logs | read_service |

---

## Domain Health Summary

| Domain | Clean? | Remaining |
|--------|--------|-----------|
| overview | ✅ | 0 |
| api_keys | ✅ | 0 |
| account | ✅ | 1 (G3: class rename) + 9 uncalled billing functions |
| analytics | ❌ | 5 (A1, G2, G5, G6, + 8 uncalled) |
| activity | ❌ | 6 (5 stubs, legacy orphan recovery) |
| logs | ❌ | 2 (1 L2 bypass B6, 18 uncalled) |
| controls | ❌ | 8 (7 L2 bypass B1–B3, A4 killswitch) |
| incidents | ❌ | 4 (G1 L6→L5, G4 commented imports, 5 uncalled) |
| policies | ❌ | 7 (3 stubs, C3 C4 fallbacks, 2 L2 bypass, 152 uncalled) |
| integrations | ❌ | 7 (1 stub, 2 frozen, 4 adapter violations C9–C12) |
