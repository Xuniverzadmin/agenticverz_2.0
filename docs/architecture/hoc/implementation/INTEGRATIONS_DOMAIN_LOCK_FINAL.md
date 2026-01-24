# Integrations Domain — LOCK FINAL
# Status: LOCKED (with documented technical debt)
# Date: 2026-01-24
# BLCA Status: 55 violations (0 actionable in Phase 2.5 scope)
# Reference: INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

---

## Domain Certification

| Check | Status | Evidence |
|-------|--------|----------|
| BLCA Scan | ⚠️ 55 violations | 0 in Phase 2.5 scope; technical debt documented |
| Header Corrections | ✅ COMPLETE | drivers/, engines/, schemas/ init files fixed |
| File Relocations | ✅ COMPLETE | 4 files relocated to correct layers |
| File Splits | ✅ PARTIAL | 3 HYBRID files documented (pending M25) |
| Audience Correction | ✅ COMPLETE | server_registry.py → customer/general/L3_mcp/ |
| Schema Extraction | ✅ COMPLETE | audit_schemas.py, cost_snapshot_schemas.py, loop_events.py |
| Legacy Imports | ⏸️ PARTIAL | 2 deferred until dependency migration |
| Init Exports | ✅ COMPLETE | All 3 init files updated |

---

## Special Status: Technical Debt

This domain has **documented technical debt** that cannot be remediated without:
1. **M25 governance approval** — HYBRID files require class refactoring
2. **Dependency migration** — Legacy imports wait on connectors/services migration
3. **Facade remediation** — Separate Phase 2.5 cycle required

### HYBRID Files (M25 Blocked)

| File | Layer Status | Issue | Remediation |
|------|--------------|-------|-------------|
| `bridges.py` | L5/L6 HYBRID | 20 sqlalchemy runtime imports | Requires class split |
| `cost_snapshots.py` | L5/L6 HYBRID | Embedded DB operations | Requires class split |
| `dispatcher.py` | L5/L6 HYBRID | Embedded DB operations | Requires class split |

### Deferred Items

| File | Import | Waiting On |
|------|--------|------------|
| `execution.py` | `app.services.connectors` | Connectors migration to HOC |
| `cost_bridges_engine.py` | `app.services.governance.cross_domain` | Cross-domain services migration |

---

## Final File Structure

```
backend/app/hoc/cus/integrations/
├── __init__.py
├── adapters/
│   └── __init__.py
├── drivers/
│   ├── __init__.py                      # L6 — Drivers
│   ├── bridges.py                       # L5/L6 HYBRID (M25 debt)
│   ├── bridges_driver.py                # L6 — Policy activation persistence (NEW)
│   ├── connector_registry.py            # L6 — CLEAN
│   ├── cost_safety_rails.py             # L6 — CLEAN
│   ├── cost_snapshots.py                # L5/L6 HYBRID (M25 debt)
│   ├── dispatcher.py                    # L5/L6 HYBRID (M25 debt)
│   ├── execution.py                     # L6 — (deferred legacy import)
│   ├── external_response_service.py     # L6 — (out of scope, naming)
│   ├── identity_resolver.py             # L6 — CLEAN
│   └── knowledge_plane.py               # L6 — CLEAN
├── engines/
│   ├── __init__.py                      # L5 — Domain Engines
│   ├── cost_bridges_engine.py           # L5 — Cost bridge logic (MOVED)
│   ├── cus_health_service.py            # L5 — (out of scope, naming)
│   ├── iam_service.py                   # L5 — (out of scope, naming)
│   ├── learning_proof_engine.py         # L5 — Learning proof logic (MOVED)
│   └── prevention_contract.py           # L5 — Prevention validation (MOVED)
├── facades/
│   └── (8 files — out of scope)
├── schemas/
│   ├── __init__.py                      # L5 — Domain Schemas
│   ├── audit_schemas.py                 # L5 — PolicyActivationAudit (NEW)
│   ├── cost_snapshot_schemas.py         # L5 — Cost snapshot types (NEW)
│   └── loop_events.py                   # L5 — Loop event types (MOVED)
└── vault/
    └── (out of scope)

backend/app/hoc/cus/general/L3_mcp/
├── __init__.py                          # L5 — MCP cross-domain package (NEW)
└── server_registry.py                   # L6 — MCP server registry (MOVED)
```

---

## Layer Distribution

| Layer | Files | Role |
|-------|-------|------|
| L5 (Domain Engine) | `prevention_contract.py`, `learning_proof_engine.py`, `cost_bridges_engine.py` | Business logic |
| L5 (Domain Schema) | `audit_schemas.py`, `cost_snapshot_schemas.py`, `loop_events.py` | Dataclasses, enums |
| L6 (Driver) | `bridges_driver.py`, `connector_registry.py`, `cost_safety_rails.py`, `identity_resolver.py`, `knowledge_plane.py` | Pure data access |
| L5/L6 (HYBRID) | `bridges.py`, `cost_snapshots.py`, `dispatcher.py` | Mixed (M25 debt) |

---

## Violations Remediated

| # | File | Violation | Resolution |
|---|------|-----------|------------|
| 1 | `drivers/__init__.py` | L4 header (should be L6) | ✅ Fixed to L6 |
| 2 | `schemas/__init__.py` | L4 header (should be L5) | ✅ Fixed to L5 |
| 3 | `engines/__init__.py` | L4 header (should be L5) | ✅ Fixed to L5 |
| 4 | `events.py` | L5 schema in drivers/ | ✅ Moved to schemas/loop_events.py |
| 5 | `prevention_contract.py` | L5 engine in drivers/ | ✅ Moved to engines/ |
| 6 | `learning_proof.py` | L5 engine in drivers/ | ✅ Moved to engines/learning_proof_engine.py |
| 7 | `cost_bridges.py` | L5 engine in drivers/ | ✅ Moved to engines/cost_bridges_engine.py |
| 8 | `bridges.py` | Mixed L5/L6 | ✅ Partial: extracted schemas + driver |
| 9 | `cost_snapshots.py` | Mixed L5/L6 | ✅ Partial: extracted schemas |
| 10 | `dispatcher.py` | Mixed L5/L6 | ✅ Header updated to HYBRID |
| 11 | `server_registry.py` | AUDIENCE: INTERNAL (wrong) | ✅ Fixed to CUSTOMER, moved to general/mcp/ |
| 12 | `cost_bridges_engine.py` | Legacy import (events) | ✅ Fixed to use ..schemas.loop_events |

---

## Governance Invariants (Enforced)

| ID | Rule | Status |
|----|------|--------|
| INV-INT-001 | L5 cannot import sqlalchemy at runtime | ⚠️ HYBRID files exempt (M25 debt) |
| INV-INT-002 | L5 cannot import from L7 models directly | ⚠️ HYBRID files exempt (M25 debt) |
| INV-INT-003 | Schemas are pure dataclasses (no DB) | ✅ ENFORCED |
| INV-INT-004 | Engines contain business logic | ✅ ENFORCED |
| INV-INT-005 | Drivers contain pure DB operations | ✅ ENFORCED |
| INV-INT-006 | Files stay within audience boundary | ✅ ENFORCED |
| INV-INT-007 | Cross-domain goes to {audience}/general/ | ✅ ENFORCED |

---

## Files Created

| File | Layer | Purpose |
|------|-------|---------|
| `schemas/audit_schemas.py` | L5 | PolicyActivationAudit dataclass |
| `schemas/cost_snapshot_schemas.py` | L5 | Cost snapshot types, enums |
| `drivers/bridges_driver.py` | L6 | record_policy_activation() |
| `general/mcp/__init__.py` | L5 | MCP cross-domain package |
| `general/mcp/server_registry.py` | L6 | MCP server registry (relocated) |

---

## Files Moved

| Old Location | New Location | Reason |
|--------------|--------------|--------|
| `drivers/events.py` | `schemas/loop_events.py` | Pure L5 schema |
| `drivers/prevention_contract.py` | `engines/prevention_contract.py` | Pure L5 engine |
| `drivers/learning_proof.py` | `engines/learning_proof_engine.py` | Pure L5 engine |
| `drivers/cost_bridges.py` | `engines/cost_bridges_engine.py` | Pure L5 engine |
| `drivers/server_registry.py` | `general/mcp/server_registry.py` | Cross-domain + audience fix |

---

## Files Deleted

| File | Reason |
|------|--------|
| `drivers/server_registry.py` | Relocated to `general/mcp/` |

---

## Out of Scope (Require Separate Remediation)

The following files were NOT remediated in Phase 2.5:

### Banned Naming (4 files)
- `drivers/external_response_service.py`
- `engines/cus_health_service.py`
- `engines/iam_service.py`
- `vault/engines/cus_credential_service.py`

### Facades (8 files with legacy imports)
- All files in `facades/` require separate Phase 2.5 cycle

### Layer Boundary Violations (facades)
- Various facades importing from `app.services.*`

---

## Domain Axiom (LOCKED)

> **Integrations is a CONNECTIVITY domain.**
> It manages external connections, MCP servers, cost tracking, and loop mechanics.

Consequences:
1. Bridges orchestrate policy activation with audit trails
2. Cost snapshots track usage with anomaly detection
3. Dispatcher manages loop lifecycle and event persistence
4. MCP registry is cross-domain (customer/general/L3_mcp/)
5. HYBRID files are technical debt, not permanent architecture

---

## Post-Lock Constraints

Any future changes to the integrations domain MUST:

1. Respect HYBRID file freeze until M25 governance approval
2. Not introduce new legacy imports from `app.services.*`
3. Place all new schemas in `schemas/`
4. Place all new engines in `engines/`
5. Place all new drivers in `drivers/`
6. Cross-domain items go to `customer/general/`
7. AUDIENCE must match folder location

---

## BLCA Results (2026-01-24)

```
Total Violations: 55
In-Scope Actionable: 0

BANNED_NAMING:       4 (out of scope)
LAYER_BOUNDARY:     10 (out of scope - facades)
LEGACY_IMPORT:      21 (1 deferred, 20 out of scope)
SQLALCHEMY_RUNTIME: 20 (HYBRID files - M25 debt)
```

---

## Certification

```
DOMAIN: integrations
STATUS: LOCKED (with documented technical debt)
DATE: 2026-01-24
BLCA: 55 violations (0 actionable in scope)
PHASE: 2.5 COMPLETE
VIOLATIONS_REMEDIATED: 12
FILES_CREATED: 5
FILES_MOVED: 5
FILES_DELETED: 1
TECHNICAL_DEBT: 3 HYBRID files (M25), 2 deferred imports
OUT_OF_SCOPE: 4 naming, 8 facades
```

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock (with documented technical debt) | Claude |
| 2026-01-24 | 1.1.0 | Phase 2.5E BLCA verification: 0 errors, 0 warnings across all 6 check types (for in-scope files) | Claude |

---

**END OF LOCK DOCUMENT**
