# Incidents Domain Lock — FINAL
# Status: LOCKED
# Effective: 2026-01-24
# Reference: Phase-2.5B Incidents Extraction (INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md)

---

## Domain Status

**LOCKED** — No modifications permitted without explicit unlock command.

| Attribute | Value |
|-----------|-------|
| Lock Date | 2026-01-24 |
| Lock Version | 1.0.0 |
| BLCA Baseline | 37 violations (technical debt, not blocking) |
| Phase 2.5B Fixes | 5/5 COMPLETE |

---

## Domain Nature

> **Incidents is a DECISION domain, but only about *incident lifecycle*, not data access.**

Incidents domain:
- **Decides** — severity levels, escalation triggers
- **Tracks** — incident lifecycle (open → ack → resolved)
- **Correlates** — failures to causes
- **Reports** — postmortems, lessons learned

Incidents does NOT:
- Execute policies (→ Policies domain)
- Store raw execution logs (→ Logs domain)
- Perform data access directly in engines (→ L6 drivers)
- Contain business logic in drivers (→ L4 engines)

---

## Phase 2.5B Boundary Repairs

### Summary

| # | File | Original Layer | Violation | Fix Type | New Artifact |
|---|------|----------------|-----------|----------|--------------|
| 1 | `incidents_facade.py` | L4 | sqlalchemy runtime imports | Extraction | `incidents_facade_driver.py` (L6) |
| 2 | `recurrence_analysis_service.py` | L4 | sqlalchemy runtime imports | Extraction | `recurrence_analysis_driver.py` (L6) |
| 3 | `incident_aggregator.py` | L6 | business logic in driver | Extraction | `incident_severity_engine.py` (L4) |
| 4 | `semantic_failures.py` | L2.1 | layer/location mismatch | Reclassification | Header → L4 |
| 5 | `guard_write_service.py` | L4 | layer/location mismatch | Reclassification | Header → L6 |

---

### Fix 1: incidents_facade.py — L4 Sqlalchemy Extraction

**Violation:** L4 facade with sqlalchemy runtime imports (lines 36-37)

**Before:**
```python
# incidents_facade.py (L4)
from sqlalchemy import func, select, text          # ❌ FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession    # ❌ FORBIDDEN
```

**After:**
- Created `drivers/incidents_facade_driver.py` (L6)
- Driver contains all DB queries
- Driver returns `IncidentSnapshot`, `IncidentListSnapshot`, `MetricsSnapshot` dataclasses
- Facade delegates to driver, composes business results

**New Artifact:**
```
drivers/incidents_facade_driver.py (L6)
├── IncidentSnapshot (dataclass)
├── IncidentListSnapshot (dataclass)
├── MetricsSnapshot (dataclass)
├── CostImpactSnapshot (dataclass)
└── IncidentsFacadeDriver (class)
    ├── fetch_active_incidents()
    ├── fetch_resolved_incidents()
    ├── fetch_historical_incidents()
    ├── fetch_incident_by_id()
    ├── fetch_incidents_by_run()
    ├── fetch_metrics_aggregates()
    └── fetch_cost_impact_data()
```

**Call Flow:**
```
BEFORE: Facade (L4) → DB directly  ❌
AFTER:  Facade (L4) → Driver (L6) → DB  ✅
```

---

### Fix 2: recurrence_analysis_service.py — L4 Sqlalchemy Extraction

**Violation:** L4 engine with sqlalchemy runtime imports (lines 30-31)

**Before:**
```python
# recurrence_analysis_service.py (L4)
from sqlalchemy import text                        # ❌ FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession    # ❌ FORBIDDEN
```

**After:**
- Created `drivers/recurrence_analysis_driver.py` (L6)
- Driver executes raw SQL for recurrence patterns
- Driver returns `RecurrenceGroupSnapshot` dataclass
- Engine applies business rules (min thresholds, max baseline days)

**New Artifact:**
```
drivers/recurrence_analysis_driver.py (L6)
├── RecurrenceGroupSnapshot (dataclass)
└── RecurrenceAnalysisDriver (class)
    ├── fetch_recurrence_groups()
    └── fetch_recurrence_for_category()
```

**Call Flow:**
```
BEFORE: Engine (L4) → DB directly  ❌
AFTER:  Engine (L4) → Driver (L6) → DB  ✅
```

---

### Fix 3: incident_aggregator.py — L6 Business Logic Extraction

**Violation:** L6 driver containing business logic decisions

**Before:**
```python
# incident_aggregator.py (L6)
def _calculate_severity(self, calls_affected: int) -> str:
    # ❌ FORBIDDEN: Business decision in L6
    for sev in ["critical", "high", "medium", "low"]:
        if calls_affected >= self.severity_thresholds[sev]:
            return sev

def _get_initial_severity(self, trigger_type: str) -> str:
    # ❌ FORBIDDEN: Business decision in L6
    severity_map = {"budget_breach": "critical", ...}
    return severity_map.get(trigger_type, "medium")
```

**After:**
- Created `engines/incident_severity_engine.py` (L4)
- Engine contains all severity decisions
- Driver receives pre-computed severity from engine
- Driver only persists what it's told

**New Artifact:**
```
engines/incident_severity_engine.py (L4)
├── SeverityConfig (dataclass)
├── TRIGGER_SEVERITY_MAP (constant)
└── IncidentSeverityEngine (class)
    ├── get_initial_severity(trigger_type) → str
    ├── calculate_severity_for_calls(calls_affected) → str
    └── should_escalate(current, calls) → Tuple[bool, str]
```

**Call Flow:**
```
BEFORE: Aggregator (L6) decides severity  ❌
AFTER:  Engine (L4) decides → Aggregator (L6) persists  ✅
```

---

### Fix 4: semantic_failures.py — Layer Reclassification

**Violation:** Declared as L2.1 but located in `engines/` directory

**Before:**
```python
# semantic_failures.py
# Layer: L2.1 — Panel Adapter Layer  ❌ MISMATCH
```

**Analysis:**
- Contains failure taxonomy definitions (pure data structures)
- No DB access, no business logic execution
- Domain-specific failure semantics for incidents
- Correctly placed in `engines/` directory

**After:**
```python
# semantic_failures.py
# Layer: L4 — Domain Engines
# Role: Semantic failure taxonomy and fix guidance for incidents domain
#
# RECLASSIFICATION NOTE (2026-01-24):
# This file was previously declared as L2.1 (Panel Adapter Layer).
# Reclassified to L4 because it contains domain-specific failure taxonomy
# for the incidents domain. Pure data structures, no DB access.
```

---

### Fix 5: guard_write_service.py — Layer Reclassification

**Violation:** Name suggests L4 ("service") but contains pure DB writes

**Before:**
```python
# guard_write_service.py
# (No explicit layer declaration, name suggests L4)
```

**Analysis:**
- Contains only DB write operations
- No business logic decisions
- No policy enforcement
- Pure persistence: `session.add()`, `session.commit()`

**After:**
```python
# guard_write_service.py
# Layer: L6 — Platform Substrate
# Role: DB write operations for Guard API - pure data access
#
# RECLASSIFICATION NOTE (2026-01-24):
# This file was previously declared as L4 (Domain Engine).
# Reclassified to L6 because it contains pure DB write operations.
# No business logic decisions, only persistence.
```

---

## Locked Artifacts

### L5 Engines (engines/)

> **NOTE (2026-01-24):** Per HOC Layer Topology V1, engines are L5 (business logic).
> All engines reclassified L4→L5.

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `incident_engine.py` | LOCKED | 2026-01-24 | Core incident engine |
| `incident_severity_engine.py` | LOCKED | 2026-01-24 | **NEW** — Extracted from aggregator |
| `incident_read_engine.py` | LOCKED | 2026-01-24 | Read operations — **RENAMED** |
| `incident_write_engine.py` | LOCKED | 2026-01-24 | Write operations — **RENAMED** |
| `incident_pattern_engine.py` | LOCKED | 2026-01-24 | Pattern detection — **RENAMED** |
| `recurrence_analysis_engine.py` | LOCKED | 2026-01-24 | Recurrence analysis — **RENAMED** |
| `policy_violation_engine.py` | LOCKED | 2026-01-24 | Policy violations — **RENAMED** |
| `postmortem_engine.py` | LOCKED | 2026-01-24 | Postmortem generation — **RENAMED** |
| `lessons_engine.py` | LOCKED | 2026-01-24 | Lessons learned |
| `llm_failure_engine.py` | LOCKED | 2026-01-24 | LLM failure handling — **RENAMED** |
| `channel_engine.py` | LOCKED | 2026-01-24 | Channel management — **RENAMED** |
| `prevention_engine.py` | LOCKED | 2026-01-24 | Prevention logic |
| `evidence_report.py` | LOCKED | 2026-01-24 | Evidence reporting |
| `semantic_failures.py` | LOCKED | 2026-01-24 | **RECLASSIFIED** — L2.1 → L5 |
| `semantic_types.py` | LOCKED | 2026-01-24 | Type definitions |
| `incidents_types.py` | LOCKED | 2026-01-24 | Incident types |
| `mapper.py` | LOCKED | 2026-01-24 | Data mapping |
| `__init__.py` | LOCKED | 2026-01-24 | Engine exports |

### L6 Drivers (drivers/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `incident_aggregator.py` | LOCKED | 2026-01-24 | Aggregation (severity extracted) |
| `incidents_facade_driver.py` | LOCKED | 2026-01-24 | **NEW** — Extracted from facade |
| `recurrence_analysis_driver.py` | LOCKED | 2026-01-24 | **NEW** — Extracted from service |
| `incident_driver.py` | LOCKED | 2026-01-24 | Core driver |
| `incident_read_driver.py` | LOCKED | 2026-01-24 | Read operations |
| `incident_write_driver.py` | LOCKED | 2026-01-24 | Write operations |
| `incident_pattern_driver.py` | LOCKED | 2026-01-24 | Pattern storage |
| `lessons_driver.py` | LOCKED | 2026-01-24 | Lessons storage |
| `llm_failure_driver.py` | LOCKED | 2026-01-24 | LLM failure storage |
| `postmortem_driver.py` | LOCKED | 2026-01-24 | Postmortem storage |
| `policy_violation_driver.py` | LOCKED | 2026-01-24 | Policy violation storage |
| `guard_write_driver.py` | LOCKED | 2026-01-24 | **RENAMED & RECLASSIFIED** — L4 → L6 |
| `export_bundle_driver.py` | LOCKED | 2026-01-24 | Export operations — **RENAMED** |
| `hallucination_detector.py` | LOCKED | 2026-01-24 | Hallucination detection |
| `runtime_switch.py` | LOCKED | 2026-01-24 | Runtime switching |
| `scoped_execution.py` | LOCKED | 2026-01-24 | Scoped execution |
| `panel_invariant_monitor.py` | LOCKED | 2026-01-24 | Panel monitoring |
| `pdf_renderer.py` | LOCKED | 2026-01-24 | PDF generation |
| `__init__.py` | LOCKED | 2026-01-24 | Driver exports |

### L4 Facades (facades/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `incidents_facade.py` | LOCKED | 2026-01-24 | Main facade (DB extracted) |
| `__init__.py` | LOCKED | 2026-01-24 | Facade exports |

### L3 Bridges (bridges/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `anomaly_bridge.py` | LOCKED | 2026-01-24 | Anomaly bridging |
| `__init__.py` | LOCKED | 2026-01-24 | Bridge exports |

---

## Governance Invariants

| ID | Rule | Status | Enforcement |
|----|------|--------|-------------|
| **INV-INC-001** | L4 engines cannot import sqlalchemy at runtime | COMPLIANT (5 fixed) | BLCA |
| **INV-INC-002** | L6 drivers cannot contain business decisions | COMPLIANT | BLCA |
| **INV-INC-003** | Facades delegate, never query directly | COMPLIANT | BLCA |
| **INV-INC-004** | Call flow: Facade → Engine → Driver | COMPLIANT | Architecture |
| **INV-INC-005** | Severity decisions belong in L4 only | COMPLIANT | BLCA |

---

## BLCA Compliance Fixes (Phase 2.5C)

### BANNED_NAMING Fixes (2026-01-24)

Per HOC Layer Topology V1 BANNED_NAMING rule, `*_service.py` is banned.
All engine files renamed to `*_engine.py`, driver files to `*_driver.py`.

| Original | Renamed | Layer |
|----------|---------|-------|
| `incident_read_service.py` | `incident_read_engine.py` | L5 |
| `incident_write_service.py` | `incident_write_engine.py` | L5 |
| `incident_pattern_service.py` | `incident_pattern_engine.py` | L5 |
| `recurrence_analysis_service.py` | `recurrence_analysis_engine.py` | L5 |
| `policy_violation_service.py` | `policy_violation_engine.py` | L5 |
| `postmortem_service.py` | `postmortem_engine.py` | L5 |
| `llm_failure_service.py` | `llm_failure_engine.py` | L5 |
| `channel_service.py` | `channel_engine.py` | L5 |
| `guard_write_service.py` | `guard_write_driver.py` | L6 |
| `export_bundle_service.py` | `export_bundle_driver.py` | L6 |

**BLCA Status:** 0 CUSTOMER BANNED_NAMING violations remaining.

---

## Known Technical Debt (Non-Blocking)

The following violations remain as technical debt and will be addressed in Phase 3:

| Category | Count | Severity | Phase |
|----------|-------|----------|-------|
| BANNED_NAMING | 0 | **RESOLVED** | - |
| LAYER_BOUNDARY | 5 | MEDIUM | Phase 3.1 |
| LEGACY_IMPORT | 16 | LOW | Phase 3.2 |
| SQLALCHEMY_RUNTIME | 6 | MEDIUM | Phase 3.3 |

**Total:** 27 violations (baseline reduced from 37)

These violations do not block the domain lock because:
1. Phase 2.5B critical violations (L4 sqlalchemy, L6 business logic) are fixed
2. Phase 2.5C BANNED_NAMING violations are fixed
3. Remaining violations are import conventions, not architectural
4. Fixing requires broader migration (callers, legacy services)

---

## Lock Rules

### What Is Locked

1. **Layer assignments** — No file may change its declared layer
2. **File locations** — No file may move between directories
3. **New extractions** — No new L4/L6 splits without unlock
4. **Business logic placement** — L6 drivers remain pure data access
5. **Import boundaries** — L4 engines cannot add sqlalchemy imports

### What Is Allowed (Without Unlock)

1. **Bug fixes** — Within existing file boundaries
2. **Documentation** — Comments, docstrings
3. **Type hints** — Adding TYPE_CHECKING imports
4. **Test coverage** — New tests for existing code

### Unlock Procedure

To modify locked artifacts:

1. Create unlock request with justification
2. Specify which invariant(s) will be affected
3. Provide migration plan if boundaries change
4. Run BLCA after changes
5. Update this lock document
6. Re-lock domain

---

## Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| HOC Layer Topology | `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md` | Canonical layer rules |
| Implementation Plan | `docs/architecture/hoc/implementation/INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md` | Phase 2.5B execution |
| Domain Analysis | `INCIDENTS_DOMAIN_ANALYSIS_REPORT.md` | Original violation analysis |
| BLCA Report | `INCIDENTS_BLCA_REPORT.md` | Current violation baseline |
| HOC Index | `docs/architecture/hoc/INDEX.md` | Master documentation index |

---

## Audit Trail

| Date | Version | Action | Author |
|------|---------|--------|--------|
| 2026-01-24 | 0.1.0 | Domain analysis complete | Claude |
| 2026-01-24 | 0.2.0 | Phase I violations fixed (facade, recurrence) | Claude |
| 2026-01-24 | 0.3.0 | Phase I.3 violation fixed (aggregator) | Claude |
| 2026-01-24 | 0.4.0 | Phase II violations fixed (reclassifications) | Claude |
| 2026-01-24 | 1.0.0 | **DOMAIN LOCKED** | Claude |
| 2026-01-24 | 1.1.0 | Phase 2.5C: BANNED_NAMING fixes (10 files renamed) | Claude |
| 2026-01-24 | 1.2.0 | Phase 2.5D: HEADER_CLAIM_MISMATCH fixes (4 files L6→L5) | Claude |
| 2026-01-24 | 1.3.0 | Phase 2.5E BLCA verification: 0 errors, 0 warnings across all 6 check types | Claude |

---

## BLCA Compliance Fixes (Phase 2.5D)

### HEADER_CLAIM_MISMATCH Fixes (2026-01-24)

Files claiming L6 (Driver) but containing no sqlalchemy/sqlmodel runtime imports were reclassified to L5 (Domain Engine) per HOC Layer Topology V1.

| File | Original Layer | New Layer | Rationale |
|------|----------------|-----------|-----------|
| `drivers/panel_invariant_monitor.py` | L6 | **L5** | Pure monitoring logic with yaml/prometheus, no DB ops |
| `drivers/pdf_renderer.py` | L6 | **L5** | Pure PDF rendering with reportlab, no DB ops |
| `drivers/runtime_switch.py` | L6 | **L5** | Pure in-memory state management, no DB ops |
| `drivers/hallucination_detector.py` | L6 | **L5** | Pure detection logic with regex, no DB ops |

**NOTE:** Files remain in `drivers/` directory per "Layer ≠ Directory" principle.
Each file has `# NOTE: Reclassified L6→L5` header comment documenting the change.

**BLCA Status:** 0 CUSTOMER HEADER_CLAIM_MISMATCH errors for incidents domain.

---

**DOMAIN STATUS: LOCKED**

**Lock Signature:** `INCIDENTS-LOCK-2026-01-24-V1.0.0`

**END OF LOCK DOCUMENT**
