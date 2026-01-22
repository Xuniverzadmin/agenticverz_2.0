# HOC Incidents Domain Analysis v1

**Domain:** `app/houseofcards/customer/incidents/`
**Audience:** CUSTOMER
**Date:** 2026-01-22
**Status:** CLEANUP COMPLETE
**Last Updated:** 2026-01-22

---

## 1. Final Structure (Post-Cleanup)

```
app/houseofcards/customer/incidents/
├── __init__.py
├── drivers/
│   └── __init__.py               (EMPTY - reserved for L3 adapters)
├── engines/
│   ├── __init__.py
│   ├── incident_aggregator.py        # Incident grouping/escalation
│   ├── incident_engine.py            # Incident creation logic (SDSR)
│   ├── incident_pattern_service.py   # Pattern detection
│   ├── incident_read_service.py      # Read operations
│   ├── incident_write_service.py     # Write operations (MOVED from drivers/)
│   ├── llm_failure_service.py        # S4 failure truth model
│   ├── postmortem_service.py         # Post-mortem insights
│   ├── recovery_evaluation_engine.py # Recovery decisions
│   ├── recovery_rule_engine.py       # Recovery rules
│   └── recurrence_analysis_service.py # Recurrence patterns
├── facades/
│   ├── __init__.py
│   └── incidents_facade.py           # Domain entry point
└── schemas/
    └── __init__.py                   (EMPTY - reserved for DTOs)
```

**File Count:** 10 files (excluding __init__.py)

---

## 2. Completed Actions (2026-01-22)

### 2.1 Files Moved Within Domain

| File | From | To | Reason |
|------|------|-----|--------|
| `incident_write_service.py` | incidents/drivers/ | incidents/engines/ | Role violation: L4 Engine was in drivers/ folder |

### 2.2 Files Moved Out of Domain

| File | From | To | Reason |
|------|------|-----|--------|
| `incident_driver.py` | incidents/drivers/ | `internal/recovery/engines/` | Audience violation: INTERNAL in customer/ path |
| `guard_write_service.py` | incidents/engines/ | `general/controls/engines/` | Domain violation: Guard/KillSwitch, not incidents |

### 2.3 Decision Rationale

**incident_write_service.py:**
- Header declared: `L4 — Domain Engine`
- Performs domain writes (acknowledge, resolve, add_comment, update_severity)
- No external boundary adaptation (not a driver role)

**incident_driver.py:**
- Header explicitly declared: `AUDIENCE: INTERNAL`
- Header stated: *"For CUSTOMER-facing operations use incidents_facade.py instead"*
- Callers: Workers, governance services, transaction coordinators

**guard_write_service.py:**
- Header declared: `Product: AI Console (Guard)`
- Header admitted: *"TEMPORARY AGGREGATE service for Phase 2 structural extraction"*
- Primary operations: KillSwitch state management (freeze/unfreeze)
- Incident writes were incidental, not primary
- **Note:** Placed in `general/controls/` as temporary location until policy domain refactor

### 2.4 Files Kept (No Action - Rationale)

| File | Reason |
|------|--------|
| `llm_failure_service.py` | Owns failure truth (incident-grade). PIN-196 compliant. |
| `recovery_rule_engine.py` | Incident-triggered. Defer extraction until recovery is multi-source. |
| `recovery_evaluation_engine.py` | Incident-triggered. Defer extraction until recovery is multi-source. |

---

## 3. Engine Inventory

### 3.1 `incident_engine.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Product** | system-wide (NOT console-owned) |
| **Role** | Incident creation decision-making (domain logic) |
| **Contract** | SDSR (PIN-370), PIN-407 |

**Exports:**
- `IncidentEngine` - Main engine class
- `get_incident_engine()` - Singleton factory

**Key Methods:**
- `create_incident_for_run()` - Create incident for ANY run (PIN-407)
- `create_incident_for_failed_run()` - Create incident for failed run
- `get_incidents_for_run()` - Get incidents linked to a run

---

### 3.2 `incident_aggregator.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Product** | system-wide |
| **Role** | Incident grouping rules, escalation logic |
| **Reference** | PIN-242 |

**Exports:**
- `IncidentAggregator` - Main aggregator class
- `IncidentAggregatorConfig` - Configuration dataclass
- `create_incident_aggregator()` - Factory function

**Key Methods:**
- `get_or_create_incident()` - Get existing or create new incident
- `resolve_stale_incidents()` - Auto-resolve inactive incidents
- `get_incident_stats()` - Get incident statistics

---

### 3.3 `incident_read_service.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine |
| **Product** | system-wide |
| **Role** | Incident domain read operations |
| **Reference** | PIN-281 |

**Exports:**
- `IncidentReadService` - Main service class
- `get_incident_read_service()` - Factory function

**Key Methods:**
- `list_incidents()` - List incidents with filters
- `get_incident()` - Get single incident by ID
- `get_incident_events()` - Get timeline events

---

### 3.4 `incident_write_service.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine |
| **Product** | system-wide |
| **Role** | Incident domain write operations |

**Exports:**
- `IncidentWriteService` - Main service class

**Key Methods:**
- `acknowledge_incident()` - Acknowledge an incident
- `resolve_incident()` - Resolve an incident
- `add_comment()` - Add comment to incident
- `update_severity()` - Update incident severity

---

### 3.5 `llm_failure_service.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Product** | system-wide |
| **Role** | S4 failure truth model, fact persistence |
| **Reference** | PIN-196 |

**Exports:**
- `LLMFailureService` - Main service class
- `LLMFailureFact` - Failure fact dataclass
- `LLMFailureResult` - Result dataclass

**Key Methods:**
- `persist_failure_and_mark_run()` - Persist failure and mark run as FAILED
- `get_failure_by_run_id()` - Get failure fact by run ID

---

### 3.6 `recovery_rule_engine.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Product** | system-wide |
| **Role** | Rule-based evaluation for recovery suggestions |
| **Reference** | PIN-240, M10 |
| **Scope Note** | Recovery logic scoped to incident-triggered flows |

**Exports:**
- `RecoveryRuleEngine` - Main engine class
- `Rule`, `ErrorCodeRule`, `HistoricalRule`, `SkillRule` - Rule classes
- `RuleContext`, `RuleResult`, `EvaluationResult` - Dataclasses

---

### 3.7 `recovery_evaluation_engine.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Product** | system-wide |
| **Role** | Recovery evaluation decision-making |
| **Reference** | PIN-257 |
| **Scope Note** | Recovery logic scoped to incident-triggered flows |

**Exports:**
- `RecoveryEvaluationEngine` - Main engine class
- `FailureContext`, `RecoveryDecision` - Dataclasses

---

### 3.8 `incident_pattern_service.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engines |
| **Product** | ai-console |
| **Role** | Detect structural patterns across incidents |
| **Reference** | INCIDENTS_DOMAIN_SQL.md#5-act-o4 |

**Exports:**
- `IncidentPatternService` - Main service class
- `PatternMatch`, `PatternResult` - Dataclasses

**Key Methods:**
- `detect_patterns()` - Detect all patterns in time window
- `_detect_category_clusters()` - Detect category clusters
- `_detect_severity_spikes()` - Detect severity spikes
- `_detect_cascade_failures()` - Detect cascade failures

---

### 3.9 `postmortem_service.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engines |
| **Product** | ai-console |
| **Role** | Extract learnings and post-mortem insights |
| **Reference** | INCIDENTS_DOMAIN_SQL.md#8-res-o4 |

**Exports:**
- `PostMortemService` - Main service class
- `ResolutionSummary`, `LearningInsight`, `PostMortemResult`, `CategoryLearnings` - Dataclasses

**Key Methods:**
- `get_incident_learnings()` - Get post-mortem for incident
- `get_category_learnings()` - Get learnings for category

---

### 3.10 `recurrence_analysis_service.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Engines |
| **Product** | ai-console |
| **Role** | Analyze recurring incident patterns |
| **Reference** | INCIDENTS_DOMAIN_SQL.md#9-hist-o3 |

**Exports:**
- `RecurrenceAnalysisService` - Main service class
- `RecurrenceGroup`, `RecurrenceResult` - Dataclasses

**Key Methods:**
- `analyze_recurrence()` - Analyze incident recurrence patterns

---

## 4. Facade Inventory

### 4.1 `incidents_facade.py`

| Attribute | Value |
|-----------|-------|
| **Layer** | L4 — Domain Facade |
| **Product** | ai-console |
| **Role** | Incidents domain entry point |
| **Callers** | app.api.incidents (L2) |

**Exports (Result Types):**
- `IncidentSummaryResult`, `PaginationResult`, `IncidentListResult`
- `IncidentDetailResult`, `IncidentsByRunResult`
- `PatternMatchResult`, `PatternDetectionResult`
- `RecurrenceGroupResult`, `RecurrenceAnalysisResult`
- `CostImpactSummaryResult`, `CostImpactResult`
- `IncidentMetricsResult`, `HistoricalTrendResult`
- `LearningInsightResult`, `ResolutionSummaryResult`, `LearningsResult`

**Methods:**
| Method | Description | Order |
|--------|-------------|-------|
| `list_active_incidents()` | List active incidents | O2 |
| `list_resolved_incidents()` | List resolved incidents | O2 |
| `list_historical_incidents()` | List historical incidents | O2 |
| `get_incident_detail()` | Get incident detail | O3 |
| `get_incidents_for_run()` | Get incidents by run | O3 |
| `get_metrics()` | Get incident metrics | O1 |
| `analyze_cost_impact()` | Analyze cost impact | RES-O3 |
| `detect_patterns()` | Pattern detection | ACT-O5 |
| `analyze_recurrence()` | Recurrence analysis | HIST-O3 |
| `get_incident_learnings()` | Post-mortem learnings | RES-O4 |

---

## 5. Import Inventory

### 5.1 External Imports (to be updated in Phase 5)

| File | Old Import | New Import |
|------|------------|------------|
| All engines | `app.services.incidents.*` | `app.houseofcards.customer.incidents.engines.*` |
| `recovery_evaluation_engine.py` | `app.services.recovery_*` | TBD |

### 5.2 L6 Imports (Correct)

| File | Import |
|------|--------|
| Most engines | `app.models.killswitch` |
| `incident_write_service.py` | `app.models.audit_ledger` |
| Database | `sqlalchemy`, `sqlmodel` |

---

## 6. Dependency Graph

```
incidents_facade.py
├── incident_pattern_service.py
├── postmortem_service.py
├── recurrence_analysis_service.py
└── app.models.killswitch (direct DB)

incident_engine.py
├── app.services.policy.lessons_engine (cross-domain)
└── Direct DB via sqlalchemy.text

incident_aggregator.py
├── app.models.killswitch
└── app.utils.runtime

recovery_evaluation_engine.py
├── recovery_rule_engine.py (same domain)
├── app.services.recovery_matcher (OLD PATH)
└── app.contracts.decisions

llm_failure_service.py
└── app.utils.runtime
```

---

## 7. Remaining Action Items

### 7.1 Import Path Updates (Phase 5)

| File | Action |
|------|--------|
| All engines | Update `app.services.incidents.*` → `app.houseofcards.customer.incidents.engines.*` |
| `recovery_evaluation_engine.py` | Update `app.services.recovery_*` paths |

### 7.2 Documentation (Low Priority)

- Add `__init__.py` exports for each subpackage
- Extract stable DTOs into `schemas/`

### 7.3 Monitor for Future Extraction

| File | Condition for Extraction |
|------|-------------------------|
| `recovery_rule_engine.py` | When recovery inputs broaden beyond incidents |
| `recovery_evaluation_engine.py` | When recovery inputs broaden beyond incidents |
| `llm_failure_service.py` | When non-incident failures emerge |

---

## 8. Domain Summary

| Metric | Value |
|--------|-------|
| **Purpose** | Incidents, failures, recovery, post-mortem |
| **Files** | 10 |
| **Facade** | 1 (incidents_facade.py) |
| **Engines** | 10 |
| **Drivers** | 0 (reserved) |
| **Schemas** | 0 (reserved) |
| **External Dependencies** | sqlalchemy, sqlmodel, app.models.killswitch |
| **Callers** | app.api.incidents (L2) |

---

## 9. Change Log

| Date | Action | Details |
|------|--------|---------|
| 2026-01-22 | Initial analysis | Structure, imports, exports documented |
| 2026-01-22 | File moved | `incident_write_service.py` → incidents/engines/ |
| 2026-01-22 | File moved | `incident_driver.py` → internal/recovery/engines/ |
| 2026-01-22 | File moved | `guard_write_service.py` → general/controls/engines/ |
| 2026-01-22 | Status updated | CLEANUP COMPLETE |

---

## 10. Related Domains Affected

Files moved out of incidents now reside in:

| File | New Location | Domain |
|------|--------------|--------|
| `incident_driver.py` | `internal/recovery/engines/` | internal/recovery |
| `guard_write_service.py` | `customer/general/controls/engines/` | general/controls (temporary) |

---

*Generated: 2026-01-22*
*Version: v1.1*
