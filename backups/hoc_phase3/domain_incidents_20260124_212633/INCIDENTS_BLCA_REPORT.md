# Incidents Domain — BLCA Scan Report
# Status: BASELINE ESTABLISHED
# Date: 2026-01-24
# Scanner: layer_validator.py (HOC Layer Topology V1)
# Reference: HOC_LAYER_TOPOLOGY_V1.md, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md

---

## Executive Summary

**Files Scanned:** 48
**Total Violations:** 37
**Errors:** 37
**Warnings:** 0

| Category | Count | Severity |
|----------|-------|----------|
| BANNED_NAMING | 10 | ERROR |
| LAYER_BOUNDARY | 5 | ERROR |
| LEGACY_IMPORT | 16 | ERROR |
| SQLALCHEMY_RUNTIME | 6 | ERROR |

---

## Phase 2.5B Violations — RESOLVED

The following 5 violations from the original analysis report have been fixed:

| # | File | Original Violation | Resolution | Status |
|---|------|-------------------|------------|--------|
| 1 | `facades/incidents_facade.py` | L4 with sqlalchemy runtime | Extracted to `incidents_facade_driver.py` | ✅ FIXED |
| 2 | `engines/recurrence_analysis_service.py` | L4 with sqlalchemy runtime | Extracted to `recurrence_analysis_driver.py` | ✅ FIXED |
| 3 | `drivers/incident_aggregator.py` | L6 with business logic | Extracted to `incident_severity_engine.py` | ✅ FIXED |
| 4 | `engines/semantic_failures.py` | Layer/location mismatch | Reclassified header to L4 | ✅ FIXED |
| 5 | `drivers/guard_write_service.py` | Layer/location mismatch | Reclassified header to L6 | ✅ FIXED |

---

## Remaining Violations — Technical Debt

### BANNED_NAMING (10 errors)

Files using `*_service.py` pattern must be renamed to `*_engine.py` or `*_driver.py`.

| File | Current Name | Suggested Rename |
|------|--------------|------------------|
| `drivers/export_bundle_service.py` | export_bundle_service | export_bundle_driver |
| `drivers/guard_write_service.py` | guard_write_service | guard_write_driver |
| `engines/policy_violation_service.py` | policy_violation_service | policy_violation_engine |
| `engines/postmortem_service.py` | postmortem_service | postmortem_engine |
| `engines/incident_write_service.py` | incident_write_service | incident_write_engine |
| `engines/incident_read_service.py` | incident_read_service | incident_read_engine |
| `engines/channel_service.py` | channel_service | channel_engine |
| `engines/llm_failure_service.py` | llm_failure_service | llm_failure_engine |
| `engines/recurrence_analysis_service.py` | recurrence_analysis_service | recurrence_analysis_engine |
| `engines/incident_pattern_service.py` | incident_pattern_service | incident_pattern_engine |

**Note:** Renaming requires updating all callers. Deferred to Phase 3.

---

### LAYER_BOUNDARY (5 errors)

L4 engines importing directly from L7 models violates HOC topology.

| File | Line | Violation | Import |
|------|------|-----------|--------|
| `drivers/incident_aggregator.py` | 50 | L6→L5 | `incident_severity_engine` |
| `engines/incident_severity_engine.py` | 33 | L4→L7 | `app.models.killswitch.IncidentSeverity` |
| `engines/incident_write_service.py` | 48 | L4→L7 | `app.models.audit_ledger.ActorType` |
| `engines/incident_write_service.py` | 53 | L4→L7 | `app.models.killswitch.Incident` |
| `engines/incident_read_service.py` | 47 | L4→L7 | `app.models.killswitch.Incident, IncidentEvent` |

**Resolution Pattern:**
- L4 engines should receive snapshots/dicts from L6 drivers
- Use TYPE_CHECKING for type hints only
- Import enums/constants from shared types module, not models

---

### LEGACY_IMPORT (16 errors)

HOC files importing from legacy `app.services` namespace.

| File | Line | Legacy Import |
|------|------|---------------|
| `drivers/incident_driver.py` | 33 | `app.services.incidents.incident_driver` |
| `drivers/incident_driver.py` | 75 | `app.services.incidents.incident_engine` |
| `drivers/incident_driver.py` | 201 | `app.services.audit.models` |
| `drivers/incident_driver.py` | 202 | `app.services.audit.store` |
| `facades/incidents_facade.py` | 785 | `app.services.incidents.incident_pattern_service` |
| `facades/incidents_facade.py` | 830 | `app.services.incidents.recurrence_analysis_driver` |
| `facades/incidents_facade.py` | 875 | `app.services.incidents.postmortem_service` |
| `engines/policy_violation_service.py` | 263 | `app.services.incident_aggregator` |
| `engines/incident_engine.py` | 82 | `app.services.policy.lessons_engine` |
| `engines/prevention_engine.py` | 812 | `app.services.policy_violation_service` |
| ... | ... | (6 more) |

**Resolution Pattern:**
- Migrate legacy services to HOC namespace
- Update imports to use `app.houseofcards.customer.incidents.*`

---

### SQLALCHEMY_RUNTIME (6 errors)

L4 engines with sqlalchemy runtime imports (not in TYPE_CHECKING block).

| File | Line | Import |
|------|------|--------|
| `bridges/anomaly_bridge.py` | 316 | `from sqlalchemy import text` |
| `engines/policy_violation_service.py` | 260 | `from sqlmodel import Session` |
| `engines/incident_engine.py` | 207 | `from sqlalchemy import create_engine` |
| `engines/incident_engine.py` | 208 | `from sqlalchemy.orm import sessionmaker` |
| `engines/lessons_engine.py` | 203 | `from sqlalchemy import create_engine` |
| `engines/lessons_engine.py` | 204 | `from sqlalchemy.orm import sessionmaker` |

**Resolution Pattern:**
- Extract DB operations to L6 drivers
- Use TYPE_CHECKING pattern for type hints
- Engines receive session as injected dependency

---

## Remediation Roadmap

### Phase 3.0 — Naming Normalization (PLANNED)

**Scope:** Rename all `*_service.py` files to `*_engine.py` or `*_driver.py`
**Risk:** HIGH (breaks all caller imports)
**Prerequisite:** Full caller graph analysis

### Phase 3.1 — Layer Boundary Repair (PLANNED)

**Scope:** Remove L4→L7 direct model imports
**Pattern:**
1. Create shared types module for enums/constants
2. Move model imports to L6 drivers
3. Pass snapshots to L4 engines

### Phase 3.2 — Legacy Import Migration (PLANNED)

**Scope:** Replace all `app.services.*` imports in HOC
**Dependency:** Legacy services must be migrated to HOC first

### Phase 3.3 — Sqlalchemy Extraction (PLANNED)

**Scope:** Extract remaining sqlalchemy imports from L4 engines
**Pattern:** Same as Phase 2.5B extraction pattern

---

## Governance Invariants

| ID | Rule | Current Status |
|----|------|----------------|
| INV-INC-001 | L4 cannot import sqlalchemy at runtime | 6 violations |
| INV-INC-002 | L6 cannot contain business decisions | ✅ COMPLIANT |
| INV-INC-003 | Facades delegate, never query directly | ✅ COMPLIANT |
| INV-INC-004 | `*_service.py` naming banned | 10 violations |
| INV-INC-005 | HOC cannot import legacy app.services | 16 violations |

---

## Iteration History

| Date | Phase | Violations | Delta | Notes |
|------|-------|------------|-------|-------|
| 2026-01-24 | Analysis | 5 | - | Original report |
| 2026-01-24 | Phase 2.5B | 0 | -5 | Critical violations fixed |
| 2026-01-24 | BLCA v2 | 37 | +37 | Enhanced scanner, new rules |

**Note:** Violation count increased because BLCA v2 enforces additional rules (naming, legacy imports, L4→L7 boundaries) not covered in original analysis.

---

## Related Documents

| Document | Location |
|----------|----------|
| HOC Layer Topology | `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md` |
| Phase 2.5 Plan | `docs/architecture/hoc/implementation/INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md` |
| Domain Analysis | `INCIDENTS_DOMAIN_ANALYSIS_REPORT.md` |
| BLCA Script | `scripts/ops/layer_validator.py` |

---

**END OF BLCA REPORT**
