# Incidents Domain — Phase 2.5B Implementation Plan
# Status: COMPLETE → LOCKED
# Date: 2026-01-24
# Lock Date: 2026-01-24
# Lock Document: INCIDENTS_DOMAIN_LOCK_FINAL.md
# Reference: HOC_LAYER_TOPOLOGY_V1.md, INCIDENTS_DOMAIN_ANALYSIS_REPORT.md

---

## Core Axiom (LOCKED)

> **Incidents is a decision domain, but only about *incident lifecycle*, not data access.**

Consequences:
1. L4 may decide **severity, escalation, recurrence meaning**
2. L6 may only **persist, aggregate, or fetch**
3. Facades must never touch persistence directly
4. Call flow: **Facade → Engine → Driver** (only valid path)

---

## Violation Summary

| # | File | Violation | Severity | Phase |
|---|------|-----------|----------|-------|
| 1 | `facades/incidents_facade.py` | L4 with sqlalchemy runtime imports | CRITICAL | I |
| 2 | `engines/recurrence_analysis_service.py` | L4 with sqlalchemy runtime imports | CRITICAL | I |
| 3 | `drivers/incident_aggregator.py` | L6 with business logic | HIGH | I |
| 4 | `engines/semantic_failures.py` | Layer/location mismatch | MEDIUM | II |
| 5 | `drivers/guard_write_service.py` | Layer/location mismatch | MEDIUM | II |

---

## Phase I — Hard Violations (Boundary Repair)

### I.1 — incidents_facade.py Extraction

**Current State:**
- File declares L4
- Contains direct sqlalchemy imports at runtime (lines 36-37)
- 7 methods with direct DB access

**Target State:**
- Facade becomes orchestration-only
- All DB access moves to driver
- Call flow: Facade → Engine → Driver

**Extraction Plan:**

```
BEFORE:
  incidents_facade.py (L4) — contains DB queries

AFTER:
  incidents_facade.py (L4) — orchestration only
      ↓ delegates to
  incidents_list_engine.py (L4) — business logic if any
      ↓ calls
  incidents_facade_driver.py (L6) — pure DB access
```

**Files to Create:**
1. `drivers/incidents_facade_driver.py` — L6 pure data access

**Functions to Extract:**
| Function | Lines | Destination |
|----------|-------|-------------|
| `list_active_incidents()` | 375-471 | Driver: `fetch_active_incidents()` |
| `list_resolved_incidents()` | 473-564 | Driver: `fetch_resolved_incidents()` |
| `list_historical_incidents()` | 566-645 | Driver: `fetch_historical_incidents()` |
| `get_incident_detail()` | 651-689 | Driver: `fetch_incident_by_id()` |
| `get_incidents_for_run()` | 691-714 | Driver: `fetch_incidents_by_run()` |
| `get_metrics()` | 720-812 | Driver: `fetch_metrics_aggregates()` |
| `analyze_cost_impact()` | 818-870 | Driver: `fetch_cost_impact_data()` |

**Facade Transformation:**
- Remove sqlalchemy imports
- Add TYPE_CHECKING block for type hints
- Inject driver as dependency
- Delegate all DB operations to driver

---

### I.2 — recurrence_analysis_service.py Extraction

**Current State:**
- File declares L4 (engines/)
- Contains direct sqlalchemy imports (lines 30-31)
- 2 methods with raw SQL via `text()`

**Target State:**
- Engine receives data snapshots from driver
- Engine reasons over facts, never fetches them

**Extraction Plan:**

```
BEFORE:
  recurrence_analysis_service.py (L4) — contains DB queries

AFTER:
  recurrence_analysis_service.py (L4) — business logic only
      ↓ calls
  recurrence_analysis_driver.py (L6) — pure DB access
```

**Files to Create:**
1. `drivers/recurrence_analysis_driver.py` — L6 pure data access

**Note:** The facade already references `app.services.incidents.recurrence_analysis_driver` (line 960). Need to verify if this exists or create it.

**Functions to Extract:**
| Function | Lines | Destination |
|----------|-------|-------------|
| `analyze_recurrence()` | 80-161 | Driver: `fetch_recurrence_groups()` |
| `get_recurrence_for_category()` | 163-219 | Driver: `fetch_recurrence_for_category()` |

---

### I.3 — incident_aggregator.py Split

**Current State:**
- File declares L6 (drivers/)
- Contains sqlmodel imports (L6-compliant)
- Contains **business logic** (NOT L6-compliant):
  - `_calculate_severity()` — severity threshold decisions
  - `_get_initial_severity()` — trigger-type to severity mapping
  - Auto-escalation logic in `_add_call_to_incident()`

**Target State:**
- L6 driver: Pure persistence, receives pre-computed severity
- L4 engine: Decides severity, escalation rules

**Split Plan:**

```
BEFORE:
  incident_aggregator.py (L6) — mixed: DB + business logic

AFTER:
  incident_severity_engine.py (L4) — severity decisions
      ↓ provides computed severity
  incident_aggregation_store.py (L6) — pure persistence
```

**Files to Create:**
1. `engines/incident_severity_engine.py` — L4 severity/escalation logic

**Logic to Extract to L4 Engine:**
| Function | Lines | New Location |
|----------|-------|--------------|
| `_calculate_severity()` | 412-423 | Engine: `calculate_severity_for_calls()` |
| `_get_initial_severity()` | 425-434 | Engine: `get_initial_severity_for_trigger()` |
| Escalation decision | 388-407 | Engine: `should_escalate_severity()` |
| Severity thresholds config | 64-66 | Engine: class constant |
| Severity mapping | 427-434 | Engine: class constant |

**Driver Transformation:**
- Remove severity calculation logic
- Accept `severity: str` as parameter from caller
- Only persist what it's told

---

## Phase II — Intent Resolution

### II.1 — semantic_failures.py Classification

**Current State:**
- Declares L2.1 (Panel Adapter Layer)
- Located in `engines/`
- Contains failure taxonomy definitions (pure data structures)

**Decision Required:**
> Does this file *decide meaning*, or *translate representation*?

**Options:**
| Option | Classification | Location |
|--------|---------------|----------|
| A | L2.1 Panel Adapter | Move to `api/facades/cus/` or panel area |
| B | L4 Engine | Update header, keep in `engines/` |

**Recommendation:** Option B — This is domain-specific failure semantics for incidents, classify as L4 and add proper header.

---

### II.2 — guard_write_service.py Resolution

**Current State:**
- Located in `drivers/`
- Name suggests L4 ("service")
- Need to verify file contents

**Decision Required:**
> Does it enforce *conditions* (L4), or only persist *guarded writes* (L6)?

**Options:**
| Option | Classification | Action |
|--------|---------------|--------|
| A | L4 Engine | Move to `engines/guard_write_engine.py` |
| B | L6 Driver | Rename to `drivers/guard_write_store.py` |

---

## Execution Checklist

### Phase I Execution

- [x] **I.1.1** Create `drivers/incidents_facade_driver.py` ✅ 2026-01-24
- [x] **I.1.2** Extract DB queries from facade to driver ✅ 2026-01-24
- [x] **I.1.3** Update facade to use TYPE_CHECKING + delegate to driver ✅ 2026-01-24
- [x] **I.1.4** Run BLCA verification ✅ 2026-01-24 — 0 violations
- [x] **I.2.1** Create `drivers/recurrence_analysis_driver.py` ✅ 2026-01-24
- [x] **I.2.2** Extract DB queries from engine to driver ✅ 2026-01-24
- [x] **I.2.3** Update engine to delegate to driver ✅ 2026-01-24
- [x] **I.2.4** Run BLCA verification ✅ 2026-01-24 — 0 violations
- [x] **I.3.1** Create `engines/incident_severity_engine.py` ✅ 2026-01-24
- [x] **I.3.2** Extract severity logic from aggregator to engine ✅ 2026-01-24
- [x] **I.3.3** Update aggregator to accept pre-computed severity ✅ 2026-01-24
- [~] **I.3.4** Rename aggregator to `incident_aggregation_store.py` — SKIPPED (callers depend on current name)
- [x] **I.3.5** Run BLCA verification ✅ 2026-01-24 — 0 violations

### Phase II Execution

- [x] **II.1.1** Classify semantic_failures.py intent ✅ 2026-01-24 → L4 (domain-specific taxonomy)
- [x] **II.1.2** Update header or relocate ✅ 2026-01-24 → Updated header to L4, kept in engines/
- [x] **II.2.1** Read guard_write_service.py contents ✅ 2026-01-24
- [x] **II.2.2** Classify intent ✅ 2026-01-24 → L6 (pure DB writes)
- [x] **II.2.3** Rename or relocate ✅ 2026-01-24 → Updated header to L6, kept name (callers depend on it)

### Post-Remediation

- [x] Run full BLCA scan ✅ 2026-01-24 — 0 violations (2066 files scanned)
- [x] Add AUDIENCE headers to new files ✅ 2026-01-24 — All new files have AUDIENCE: CUSTOMER
- [ ] Create INCIDENTS_DOMAIN_LOCK_FINAL.md
- [ ] Update HOC INDEX.md

---

## Transitional Debt Policy

**Decision:** ❌ NO transitional debt approved

Rationale:
- Incidents is a locked-class domain
- Prior domains (analytics, policies, activity, logs) achieved zero debt
- Allowing debt here would invalidate architecture integrity

If something cannot be cleanly classified → **Quarantine it**

---

## Governance Invariants

| ID | Rule | Enforcement |
|----|------|-------------|
| **INV-INC-001** | L4 cannot import sqlalchemy at runtime | BLOCKING |
| **INV-INC-002** | L6 cannot contain business decisions | BLOCKING |
| **INV-INC-003** | Facades delegate, never query directly | BLOCKING |
| **INV-INC-004** | Call flow: Facade → Engine → Driver | BLOCKING |
| **INV-INC-005** | Severity decisions belong in L4 only | BLOCKING |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-24 | 1.0.0 | Initial plan created |
| 2026-01-24 | 1.1.0 | Phase I complete: Created incidents_facade_driver.py, recurrence_analysis_driver.py, incident_severity_engine.py |
| 2026-01-24 | 1.2.0 | Phase II complete: Reclassified semantic_failures.py (L4), guard_write_service.py (L6) |
| 2026-01-24 | 2.0.0 | **DOMAIN LOCKED** — See INCIDENTS_DOMAIN_LOCK_FINAL.md |

---

**STATUS: COMPLETE → LOCKED**

**Lock Signature:** `INCIDENTS-LOCK-2026-01-24-V1.0.0`

**END OF IMPLEMENTATION PLAN**
