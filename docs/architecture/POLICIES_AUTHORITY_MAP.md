# POLICIES AUTHORITY MAP — Phase-2.5A Pre-Flight

**Status:** PRE-FLIGHT
**Date:** 2026-01-24
**Reference:** PIN-468, INCIDENTS_DOMAIN_LOCKED.md

---

## Domain Overview

**Location:** `houseofcards/customer/policies/`

| Component | Count |
|-----------|-------|
| Engines | 46 |
| Drivers | 43 |
| Engines with DB signals | 19 |
| Total DB signals in engines | 119 |

**Comparison to Incidents Domain:**
- Incidents: 6 files, ~30 signals → 6 drivers created
- Policies: 19 files, 119 signals → Estimated 8-12 drivers needed

---

## DB Signal Baseline (Sorted by Signal Count)

| Priority | File | Signals | Expected Authority |
|----------|------|---------|-------------------|
| **P0** | engine.py | **50** | POLICY_PERSISTENCE (core policy engine) |
| **P0** | policy_violation_service.py | 13 | POLICY_VIOLATION_FACTS |
| **P0** | lessons_engine.py | 13 | POLICY_LESSONS_PERSISTENCE |
| **P0** | policy_proposal.py | 10 | PROPOSAL_PERSISTENCE |
| **P1** | policy_graph_engine.py | 7 | POLICY_GRAPH_FACTS |
| **P1** | keys_service.py | 6 | KEY_PERSISTENCE |
| **P1** | prevention_engine.py | 4 | PREVENTION_FACTS |
| **P1** | policy_rules_service.py | 4 | RULE_PERSISTENCE |
| **P1** | policy_limits_service.py | 4 | LIMIT_PERSISTENCE |
| **P2** | validator_service.py | 3 | (likely false positives — "text" extraction) |
| **P2** | override_service.py | 3 | OVERRIDE_PERSISTENCE |
| **P2** | prevention_hook.py | 2 | (likely false positives — PreventionContext) |
| **P2** | decorator.py | 2 | (likely false positives — InvocationContext) |
| **P2** | budget_enforcement_engine.py | 2 | BUDGET_ENFORCEMENT_FACTS |
| **P3** | policy_models.py | 1 | (likely false positive — PolicyContext class) |
| **P3** | policy_command.py | 1 | (likely false positive — MinimalContext) |
| **P3** | plan_generation_engine.py | 1 | (likely false positive — PlanGenerationContext) |
| **P3** | job_executor.py | 1 | (likely false positive — ExecutionContext) |
| **P3** | customer_policy_read_service.py | 1 | (TYPE_CHECKING only — already compliant) |

---

## Authority Taxonomy (Expected Drivers)

### Write Authorities

| Authority | Responsible For | Tables |
|-----------|----------------|--------|
| POLICY_PERSISTENCE | Core policy CRUD, versions, activation | policy_rules, policy_versions, policy_snapshots |
| PROPOSAL_PERSISTENCE | Policy proposal lifecycle | policy_proposals, proposal_feedback |
| POLICY_LESSONS_PERSISTENCE | Lesson creation from policy events | lessons_learned (policy-context) |
| RULE_PERSISTENCE | Rule CRUD operations | policy_rules |
| LIMIT_PERSISTENCE | Limit CRUD operations | limits |
| OVERRIDE_PERSISTENCE | Override CRUD operations | policy_overrides |
| KEY_PERSISTENCE | API key management | api_keys |

### Read-Only Authorities

| Authority | Responsible For | Tables |
|-----------|----------------|--------|
| POLICY_GRAPH_FACTS | Dependency graph queries | policy_rules, policy_versions |
| PREVENTION_FACTS | Prevention context queries | prevention_records, policy_rules |
| POLICY_VIOLATION_FACTS | Violation pattern queries | prevention_records, incidents |
| BUDGET_ENFORCEMENT_FACTS | Budget/cost queries | cost_records, limits |

---

## Existing Drivers Audit

**16 files in `policies/drivers/` have DB signals.** These need L4/L6 compliance audit.

### Compliant (Proper L6)

| Driver | Status |
|--------|--------|
| policy_read_driver.py | ✅ Proper L6 — pure data access |

### Requires Audit (Potential L4/L6 Violations)

| File | Concern |
|------|---------|
| policy_driver.py | Labeled L2, but in drivers/ — orchestration layer |
| llm_threshold_service.py | "_service" in drivers/ — likely L4 code |
| governance_signal_service.py | "_service" in drivers/ — likely L4 code |
| recovery_write_service.py | "_service" in drivers/ — likely L4 code |
| alert_emitter.py | May have notification logic (L4) |
| arbitrator.py | May have decision logic (L4) |
| transaction_coordinator.py | May have orchestration logic (L4) |
| orphan_recovery.py | May have recovery logic (L4) |

---

## Execution Order (Based on Priority)

### Phase 1: Core Policy Engine (P0)

**Target:** `engine.py` (50 signals)

This is the largest extraction. Approach:
1. Classify methods as DECISION vs PERSISTENCE
2. Extract persistence to `policy_core_driver.py`
3. Retain all evaluation logic in engine

**Expected Driver Methods (estimate):**
- 15-20 INSERT/UPDATE methods
- 10-15 SELECT methods
- 5+ aggregate/analytics methods

### Phase 2: Violation & Lessons (P0)

| Engine | Driver | Notes |
|--------|--------|-------|
| policy_violation_service.py | policy_violation_driver.py | May overlap with incidents domain driver |
| lessons_engine.py | policy_lessons_driver.py | May overlap with incidents domain driver |

**Cross-Domain Check Required:**
- `policy_violation_service.py` in policies vs `policy_violation_service.py` in incidents
- `lessons_engine.py` in policies vs `lessons_engine.py` in incidents

### Phase 3: Proposal & Graph (P0/P1)

| Engine | Driver |
|--------|--------|
| policy_proposal.py | proposal_driver.py |
| policy_graph_engine.py | policy_graph_driver.py |

### Phase 4: CRUD Services (P1)

| Engine | Driver |
|--------|--------|
| policy_rules_service.py | policy_rules_driver.py |
| policy_limits_service.py | policy_limits_driver.py |
| keys_service.py | keys_driver.py |

### Phase 5: Secondary Engines (P1/P2)

| Engine | Driver |
|--------|--------|
| prevention_engine.py | prevention_driver.py |
| override_service.py | override_driver.py |
| budget_enforcement_engine.py | budget_enforcement_driver.py |

### Phase 6: False Positives (P3)

Review these files to confirm no extraction needed:
- validator_service.py
- prevention_hook.py
- decorator.py
- policy_models.py
- policy_command.py
- plan_generation_engine.py
- job_executor.py

---

## Cross-Domain Dependency Analysis

### Shared Tables

| Table | Incidents Domain | Policies Domain |
|-------|-----------------|-----------------|
| prevention_records | policy_violation_driver (write) | policy_violation_service (read?) |
| lessons_learned | lessons_driver (write) | lessons_engine (write?) |
| policy_proposals | incident_write_driver (write) | policy_proposal (write) |
| policy_rules | incident_write_driver (read) | policy_rules_service (write) |

### Resolution Strategy

1. **prevention_records:** Single write authority (incidents domain owns)
2. **lessons_learned:** Evaluate if policies lessons_engine is a duplicate
3. **policy_proposals:** Both domains may write (separate contexts)
4. **policy_rules:** Policies domain owns writes, incidents domain reads

---

## Pre-Flight Checklist

Before starting extractions:

- [ ] Confirm `engine.py` method count and classification
- [ ] Audit cross-domain files for duplicates
- [ ] Verify existing drivers are L6 compliant
- [ ] Create driver inventory skeleton with authority names
- [ ] Get approval for extraction order

---

## Estimated Effort

| Phase | Files | Signals | Estimated Drivers |
|-------|-------|---------|-------------------|
| Phase 1 (engine.py) | 1 | 50 | 1 (large) |
| Phase 2 (violations/lessons) | 2 | 26 | 2 |
| Phase 3 (proposal/graph) | 2 | 17 | 2 |
| Phase 4 (CRUD services) | 3 | 14 | 3 |
| Phase 5 (secondary) | 3 | 9 | 2-3 |
| Phase 6 (false positives) | 7 | 3 | 0 |
| **Total** | **18** | **119** | **10-11** |

---

## Next Action

**Recommended:** Start with Phase 2 (violations/lessons) to resolve cross-domain dependencies before tackling the massive `engine.py`.

Alternatively, start with Phase 4 (CRUD services) for quick wins that follow the proven incidents pattern.

**Do NOT start with Phase 1 (engine.py)** until cross-domain analysis is complete.
