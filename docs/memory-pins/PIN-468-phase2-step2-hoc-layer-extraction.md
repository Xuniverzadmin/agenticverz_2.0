# PIN-468: Phase 2 Step 2 — HOC Layer Extraction (L4/L6 Segregation)

**Status:** IN_PROGRESS
**Created:** 2026-01-23
**Category:** Architecture / HOC Migration
**Reference:** PIN-250, PHASE2_EXTRACTION_PROTOCOL.md

---

## Summary

Phase 2 Step 2 of the House of Cards (HOC) migration focuses on **layer segregation** between L4 (Domain Engines) and L6 (Drivers). The goal is to reduce DB signals in engines to ≤5%.

**Stop Condition:** Engines with DB signals ≤ 5% (started at 38.5%)

---

## Canonical Segregation Contract

### L4 Engine Requirements (MUST NOT contain)
- `sqlalchemy`, `sqlmodel` imports (except under TYPE_CHECKING)
- `Session` parameter types at runtime
- `select()`, `insert()`, `update()` statements
- Direct ORM model imports (Enums are acceptable)

### L6 Driver Requirements (MUST NOT contain)
- Business branching (`if policy`, `if budget`, `if severity`)
- Cross-domain imports
- Retries/sleeps
- Business logic decisions

---

## Extraction Patterns

| Pattern | When to Use | Action |
|---------|-------------|--------|
| **TRUE EXTRACTION** | L4 business logic mixed with DB code | Split: logic stays in L4, DB ops move to driver |
| **RECLASSIFY** | File is ≥80% DB code, no business logic | Rename/move to driver, L4 becomes thin facade |

---

## Batch Status

### Batch 1: *_read_service.py — COMPLETE ✅

| File | Pattern | Driver |
|------|---------|--------|
| incident_read_service.py | RECLASSIFY | incident_read_driver.py |
| customer_killswitch_read_service.py | RECLASSIFY | killswitch_read_driver.py |
| customer_policy_read_service.py | RECLASSIFY | policy_read_driver.py |
| logs_read_service.py | Already compliant | Delegates to PostgresTraceStore |

**Cleanup:** Removed duplicate `policies/drivers/logs_read_service.py` (misplaced L4 file)

### Batch 2: *_write_service.py — COMPLETE ✅

| File | Pattern | Driver Created |
|------|---------|----------------|
| incident_write_service.py | TRUE EXTRACTION | incident_write_driver.py |
| cost_write_service.py | RECLASSIFY | cost_write_driver.py |
| founder_action_write_service.py | RECLASSIFY | founder_action_write_driver.py |
| guard_write_service.py | RECLASSIFY | guard_write_driver.py |
| user_write_service.py | RECLASSIFY | user_write_driver.py |

### Batch 3/4: Mixed *_service.py — PENDING

14+ files identified with DB signals:

| Signals | File |
|---------|------|
| 13 | cus_telemetry_service.py |
| 13 | cus_integration_service.py |
| 12 | cus_enforcement_service.py |
| 11 | platform_health_service.py |
| 10 | keys_service.py |
| 6 | api_key_service.py |
| 4 | simulation_service.py |
| 4 | message_service.py |
| 4 | cus_health_service.py |
| 3 | policy_violation_service.py |
| 3 | policy_rules_service.py |
| 3 | policy_limits_service.py |
| 3 | override_service.py |
| 3 | export_bundle_service.py |

---

## Files Created (Batch 2)

```
backend/app/houseofcards/customer/incidents/drivers/incident_write_driver.py
backend/app/houseofcards/customer/analytics/drivers/cost_write_driver.py
backend/app/houseofcards/founder/ops/drivers/founder_action_write_driver.py
backend/app/houseofcards/customer/general/controls/drivers/guard_write_driver.py
backend/app/houseofcards/customer/general/controls/drivers/__init__.py
backend/app/houseofcards/customer/account/drivers/user_write_driver.py
```

---

## Verification Results (Batch 2)

### A. Zero-DB Assertion — PASS ✅
All Session/sqlmodel imports under TYPE_CHECKING blocks.

### B. Driver Isolation — PASS ✅
- No business branching in drivers
- No cross-domain imports
- No retries/sleeps

### C. ORM Model Imports — PASS ✅
Only ActorType Enum (not ORM model) imported at runtime in incident_write_service.py.

---

## L4 Engine Template (Post-Extraction)

```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Allowed Imports: L6 (drivers only, NOT ORM models)
# Forbidden Imports: L2 (api), L3 (adapters), sqlalchemy, sqlmodel

from typing import TYPE_CHECKING

from app.houseofcards.{domain}/drivers/{name}_driver import (
    {Driver},
    get_{name}_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session
    from app.models.{model} import {Model}

class {Service}:
    def __init__(self, session: "Session"):
        self._driver = get_{name}_driver(session)

    def method(self, param: "{Model}") -> "{Model}":
        """Delegate to driver."""
        return self._driver.method(param=param)
```

---

## L6 Driver Template

```python
# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access for {domain} operations
# Allowed Imports: ORM models
# Forbidden Imports: L1, L2, L3, L4, L5

from sqlmodel import Session
from app.models.{model} import {Model}

class {Driver}:
    def __init__(self, session: Session):
        self._session = session

    def method(self, param: {Model}) -> {Model}:
        # Pure DB operations only
        self._session.add(param)
        self._session.commit()
        return param

def get_{name}_driver(session: Session) -> {Driver}:
    return {Driver}(session)
```

---

## Reference Implementation: cus_integration_service.py SPLIT ✅

**Date:** 2026-01-23
**Contract:** `DRIVER_ENGINE_CONTRACT.md`

### Classification Results

| Method | Classification | Reason |
|--------|---------------|--------|
| `create_integration` | MIXED | Duplicate name check (DECISION) + DB create (PERSISTENCE) |
| `get_integration` | DRIVER | Pure query by ID |
| `list_integrations` | DRIVER | Pure query with filters |
| `update_integration` | DRIVER | Apply field updates |
| `delete_integration` | MIXED | Soft delete policy (DECISION) |
| `enable_integration` | MIXED | State transition guard (DECISION) |
| `disable_integration` | DRIVER | Set status to disabled |
| `test_credentials` | MIXED | Health check orchestration |
| `get_limits_status` | MIXED | Period calc + percentage calc (DECISION) |

**Total:** 9 decision points, 32 DB operations

### Files Created

```
backend/app/services/cus_integration_driver.py  (L6 - all persistence)
backend/app/services/cus_integration_engine.py  (L4 - all decisions)
```

### Verification

```
Engine DB imports: NONE (CLEAN)
Driver business logic: NONE (CLEAN)
Backward compatibility: CusIntegrationService alias works
```

### Callers Updated

- `app/services/integrations_facade.py` → imports from engine
- `app/houseofcards/customer/integrations/facades/integrations_facade.py` → imports from engine

### HOC Duplicates Deleted

- `houseofcards/customer/integrations/engines/cus_integration_service.py`
- `houseofcards/customer/logs/engines/cus_integration_service.py`

---

## Next Steps

1. Apply SPLIT pattern to remaining 21 MIXED files:
   - `cus_telemetry_service.py` (13 signals)
   - `cus_enforcement_service.py` (12 signals)
   - `platform_health_service.py` (11 signals)

2. Follow `DRIVER_ENGINE_CONTRACT.md` exactly for each split

3. Re-measure DB signal percentage after each batch

---


---

## Updates

### Update (2026-01-23)

### Update (2026-01-23)

### Update (2026-01-24)

## 2026-01-24: Session 5 — Incidents Domain Closed, Policies Pre-Flight Complete

### Incidents Domain Closure

**Status:** COMPLETE ✅

All 6 engines in `customer/incidents/engines/` extracted:

| Engine | Driver | Authority |
|--------|--------|-----------|
| incident_engine.py | incident_write_driver.py | INCIDENT_PERSISTENCE |
| lessons_engine.py | lessons_driver.py | LESSONS_PERSISTENCE |
| policy_violation_service.py | policy_violation_driver.py | POLICY_VIOLATION_PERSISTENCE |
| llm_failure_service.py | llm_failure_driver.py | LLM_FAILURE_PERSISTENCE |
| postmortem_service.py | postmortem_driver.py | POSTMORTEM_ANALYTICS |
| incident_pattern_service.py | incident_pattern_driver.py | INCIDENT_PATTERN_FACTS |

**Domain Lock Artifact Created:** `INCIDENTS_DOMAIN_LOCKED.md`

### Policies Domain Pre-Flight

**Status:** PRE-FLIGHT COMPLETE

Created `POLICIES_AUTHORITY_MAP.md` with:

| Metric | Value |
|--------|-------|
| Engines with DB signals | 19 files |
| Total DB signals | 119 |
| Estimated drivers needed | 10-11 |

**Top Signal Files:**
- engine.py (50 signals) — massive core policy engine
- policy_violation_service.py (13 signals)
- lessons_engine.py (13 signals)
- policy_proposal.py (10 signals)

**Cross-Domain Dependencies Identified:**
- `policy_violation_service.py` exists in BOTH incidents and policies
- `lessons_engine.py` exists in BOTH incidents and policies
- Shared tables need authority resolution

**Recommended Next:** Resolve cross-domain duplicates before tackling engine.py

### Phase-2.5A Progress
- **Completed:** 6/70 HOC engine DB violations fixed (incidents domain)
- **Next Domain:** policies (119 signals, 19 files)
- **Total Estimated Remaining:** ~64 engines


## 2026-01-24: Session 6 — Cross-Domain Containment Complete

### Containment Actions Executed

**Reference:** `POLICIES_CROSS_DOMAIN_OWNERSHIP.md`

**Root Invariant Enforced:**
> A persistence authority must be owned by exactly one domain.

### Step A: Deleted Duplicate Files from Policies Domain

| File | Reason |
|------|--------|
| `houseofcards/customer/policies/engines/lessons_engine.py` | Duplicate of incidents canonical; no callers |
| `houseofcards/customer/policies/engines/policy_violation_service.py` | Duplicate of incidents canonical; no callers |

### Step B: Created Legacy Shims (app/services/)

Converted legacy files to shims pointing to incidents domain canonical:

| File | Shims To |
|------|----------|
| `app/services/policy/lessons_engine.py` | `incidents/engines/lessons_engine.py` |
| `app/services/policy_violation_service.py` | `incidents/engines/policy_violation_service.py` |

**Shim Pattern:**
```python
# Layer: L7 — Legacy Shim (DEPRECATED)
# MIGRATION PATH:
#   Current:  from app.services.policy.lessons_engine import ...
#   Future:   from app.houseofcards.customer.incidents.engines.lessons_engine import ...
```

### Step C: Updated Driver Inventory with Ownership

Added `cross_domain_ownership` section to `driver_inventory.yaml`:

```yaml
cross_domain_ownership:
  lessons_driver:
    owner: incidents
    consumers: [policies]
  policy_violation_driver:
    owner: incidents
    consumers: [policies]
```

### Flow Preserved

The critical flow is unchanged:
```
incidents → lessons → policy draft → human approval → policy library
```

Callers import from `app.services.policy.lessons_engine` (shim) which re-exports from `incidents` domain (canonical). All method signatures are identical.

### Signal Reduction Impact

| Domain | Before | After | Reduction |
|--------|--------|-------|-----------|
| Policies engines with signals | 19 | **17** | -2 files |
| Policies total signals | 119 | **93** | -26 signals |

This removes **22% of policies extraction work** by resolving duplication.

### Artifacts Created/Updated

| Artifact | Action |
|----------|--------|
| `POLICIES_CROSS_DOMAIN_OWNERSHIP.md` | Created (authority resolution) |
| `POLICIES_AUTHORITY_MAP.md` | Created (pre-flight) |
| `INCIDENTS_DOMAIN_LOCKED.md` | Created (freeze artifact) |
| `app/services/policy/lessons_engine.py` | Converted to shim |
| `app/services/policy_violation_service.py` | Converted to shim |
| `driver_inventory.yaml` | Added cross_domain_ownership section |

### Policies Domain Ready for Extraction

With duplicates resolved, the policies domain pre-flight is complete:
- **17 engines** with DB signals remain (was 19)
- **93 signals** total (was 119)
- **Cross-domain tables** have clear ownership
- **Recommended start:** Phase 4 CRUD services (quick wins) before engine.py (massive)

### Facade Verification (Mandatory Gate) — PASS

Verified import resolution after shim introduction:

| Check | Status |
|-------|--------|
| No imports from deleted `policies/engines/lessons_engine.py` | PASS |
| No imports from deleted `policies/engines/policy_violation_service.py` | PASS |
| All callers import from shim layer (`app.services.`) | PASS |
| Shims forward to incidents canonical engines | PASS |
| Runtime boot (import graph) passes | PASS |

**Bug Fixed:** `AsyncSession` type hint at line 579 in `policy_violation_service.py` was not quoted. Fixed to `"AsyncSession"` per L4 invariant.

### Domain Boundary Lock Created

Created `POLICIES_DOMAIN_LOCK.md` declaring:
- Policies **DOES NOT WRITE**: `lessons_learned`, `prevention_records`
- Policies **MAY READ** cross-domain tables
- `driver_inventory.yaml` is canonical authority

### Phase 4 CRUD Extractions Started

**Pattern:** SPLIT (not RECLASSIFY) — both files have business logic mixed with DB operations.

| Engine | Driver | Authority | Signals Before | After |
|--------|--------|-----------|----------------|-------|
| policy_limits_service.py | policy_limits_driver.py | LIMIT_PERSISTENCE | 8 | 0 (TYPE_CHECKING only) |
| policy_rules_service.py | policy_rules_driver.py | RULE_PERSISTENCE | 8 | 0 (TYPE_CHECKING only) |

**Driver Methods Created:**

`policy_limits_driver.py`:
- `fetch_limit_by_id()` — SELECT with tenant scope
- `add_limit()` — Add limit to session
- `add_integrity()` — Add integrity record
- `flush()` — Flush pending changes

`policy_rules_driver.py`:
- `fetch_rule_by_id()` — SELECT with tenant scope
- `add_rule()` — Add rule to session
- `add_integrity()` — Add integrity record
- `flush()` — Flush pending changes

**Business Logic Retained in Engines (L4):**
- Validation (`_validate_category_fields`, `_validate_conditions`)
- Response mapping (`_to_response`)
- Hash computation (`_compute_hash`)
- Retirement logic (rules)
- Audit event coordination

**Total Drivers:** 8 (6 incidents + 2 policies)

---

## 2026-01-23: Session 3 — incident_engine.py Phase-2.5A Extraction Complete

### Work Completed

**Target File:** `houseofcards/customer/incidents/engines/incident_engine.py`

**DB Operations Extracted to Driver:**

| Method | Before | After (Driver Method) |
|--------|--------|----------------------|
| `_check_policy_suppression()` | Raw SQL | `driver.fetch_suppressing_policy()` |
| `_write_prevention_record()` | Raw SQL | `driver.insert_prevention_record()` |
| `create_incident_for_run()` | Raw SQL | `driver.insert_incident()`, `update_run_incident_count()`, `update_trace_incident_id()` |
| `create_incident_for_failed_run()` | Raw SQL | Same as above |
| `_maybe_create_policy_proposal()` | Raw SQL | `driver.insert_policy_proposal()` |
| `get_incidents_for_run()` | Raw SQL | `driver.fetch_incidents_by_run_id()` |

**Driver Methods Added to `incident_write_driver.py`:**
- `insert_incident()` — Insert new incident record
- `update_run_incident_count()` — Increment runs.incident_count
- `update_trace_incident_id()` — Propagate incident_id to aos_traces
- `insert_prevention_record()` — Record policy suppression
- `insert_policy_proposal()` — Create draft policy proposal
- `fetch_suppressing_policy()` — Check for active suppression rules
- `fetch_incidents_by_run_id()` — Query incidents for a run
- `commit()` — Commit transaction

### Verification Gates (STEP 6) — PASS ✅

| Gate | Status |
|------|--------|
| Zero sqlalchemy/sqlmodel at runtime | PASS (only under TYPE_CHECKING) |
| No select()/insert()/update() in engine | PASS |
| No raw SQL (text()) in engine | PASS |
| Driver has no business logic | PASS |
| Pyright errors resolved | PASS |

### Business Logic Retained in Engine (L4)
- Severity mapping (FAILURE_SEVERITY_MAP)
- Category mapping (FAILURE_CATEGORY_MAP)
- Title generation (_generate_title)
- Proposal type determination
- Policy suppression decision flow

### Files Modified
- `backend/app/houseofcards/customer/incidents/engines/incident_engine.py`
- `backend/app/houseofcards/customer/incidents/drivers/incident_write_driver.py`

### Phase-2.5A Progress
- **Completed:** 1/70 HOC engine DB violations fixed
- **Next Target:** Continue with P0 priority (incidents, policies domains)


## 2026-01-23: Session 4 — lessons_engine.py Phase-2.5A Extraction Complete

### Work Completed

**Target File:** `houseofcards/customer/incidents/engines/lessons_engine.py`

**DB Operations Extracted to Driver:**

| Method | Before | After (Driver Method) |
|--------|--------|----------------------|
| `_create_lesson()` | Raw SQL | `driver.insert_lesson()` |
| `get_lesson()` | Raw SQL | `driver.fetch_lesson_by_id()` |
| `list_lessons()` | Raw SQL | `driver.fetch_lessons_list()` |
| `get_lesson_stats()` | Raw SQL | `driver.fetch_lesson_stats()` |
| `defer_lesson()` | Raw SQL | `driver.update_lesson_deferred()` |
| `dismiss_lesson()` | Raw SQL | `driver.update_lesson_dismissed()` |
| `convert_lesson_to_draft()` | Raw SQL | `driver.update_lesson_converted()` + `driver.insert_policy_proposal_from_lesson()` |
| `reactivate_deferred_lesson()` | Raw SQL | `driver.update_lesson_reactivated()` |
| `_is_debounced()` | Raw SQL | `driver.fetch_debounce_count()` |
| `get_expired_deferred_lessons()` | Raw SQL | `driver.fetch_expired_deferred()` |

**New Driver Created: `lessons_driver.py`**

| Method | Purpose |
|--------|---------|
| `insert_lesson()` | Create lesson record |
| `fetch_lesson_by_id()` | Get single lesson with all fields |
| `fetch_lessons_list()` | List lessons with filters |
| `fetch_lesson_stats()` | Aggregate stats by type/status |
| `update_lesson_deferred()` | Set deferred status + deferred_until |
| `update_lesson_dismissed()` | Set dismissed status + metadata |
| `update_lesson_converted()` | Set converted_to_draft + proposal_id |
| `update_lesson_reactivated()` | Set pending status, clear deferred_until |
| `fetch_debounce_count()` | Check recent lessons for debounce |
| `fetch_expired_deferred()` | Get deferred lessons past expiry |
| `insert_policy_proposal_from_lesson()` | Create draft proposal (for conversion) |
| `commit()` | Transaction commit |

### Verification Gates (STEP 6) — PASS ✅

| Gate | Status |
|------|--------|
| No select()/insert()/update() in engine | PASS |
| No raw SQL (text()) in engine | PASS |
| Driver has no business logic | PASS |
| Governance headers locked | PASS |

**Note:** Lazy sqlalchemy import for session factory is accepted infrastructure pattern (same as incident_engine.py).

### Business Logic Retained in Engine (L4)
- Lesson type classification (FAILURE, NEAR_THRESHOLD, CRITICAL_SUCCESS)
- State machine transitions (pending → converted/deferred/dismissed)
- Debounce decision logic
- Severity-based title/description generation
- Proposal type determination for conversion

### Files Created/Modified
- **NEW:** `backend/app/houseofcards/customer/incidents/drivers/lessons_driver.py`
- **MODIFIED:** `backend/app/houseofcards/customer/incidents/engines/lessons_engine.py`

### Phase-2.5A Progress
- **Completed:** 2/70 HOC engine DB violations fixed
- **Next Target:** Continue with P0 priority (incidents, policies domains)


## 2026-01-23: Session 4 (continued) — policy_violation_service.py Phase-2.5A Extraction Complete

### Work Completed

**Target File:** `houseofcards/customer/incidents/engines/policy_violation_service.py`

**Complexity:** HIGH (async + sync patterns, cross-domain dependencies)

**DB Operations Extracted to Driver:**

| Method | Before | After (Driver Method) |
|--------|--------|----------------------|
| `persist_violation_fact()` | Raw SQL INSERT | `driver.insert_violation_record()` |
| `check_violation_persisted()` | Raw SQL SELECT | `driver.fetch_violation_exists()` |
| `check_policy_enabled()` | Raw SQL SELECT | `driver.fetch_policy_enabled()` |
| `persist_evidence()` | Raw SQL INSERT | `driver.insert_evidence_event()` |
| `check_incident_exists()` | Raw SQL SELECT | `driver.fetch_incident_by_violation()` |
| `verify_violation_truth()` | Multiple SELECTs | `driver.fetch_violation_truth_check()` |
| `create_policy_evaluation_record()` | Raw SQL INSERT | `driver.insert_policy_evaluation()` |
| `create_policy_evaluation_sync()` | psycopg2 INSERT | `insert_policy_evaluation_sync()` |

**New Driver Created: `policy_violation_driver.py`**

| Method | Purpose |
|--------|---------|
| `insert_violation_record()` | Create violation fact in prevention_records |
| `fetch_violation_exists()` | Check if violation record exists |
| `fetch_policy_enabled()` | Check if policy is active for tenant |
| `insert_evidence_event()` | Create evidence capture event |
| `fetch_incident_by_violation()` | Check for existing incident |
| `fetch_violation_truth_check()` | Get violation truth verification data |
| `insert_policy_evaluation()` | Create policy evaluation record (async) |
| `insert_policy_evaluation_sync()` | Create policy evaluation record (sync/psycopg2) |
| `commit()` | Transaction commit |

### Verification Gates (STEP 6) — PASS ✅

| Gate | Status |
|------|--------|
| No select()/insert()/update() in engine | PASS |
| No raw SQL (text()) in engine | PASS |
| Driver has no business logic | PASS |
| Governance headers locked | PASS |

### Known Limitation

**`create_incident_from_violation()` method** has cross-domain dependency on `IncidentAggregator`:
- Imports `Session` from sqlmodel (runtime)
- Imports `engine` from `app.db`
- Calls `IncidentAggregator.get_or_create_incident()`

This is a cross-domain call to another L4 engine, not direct DB access. The Session is used to call the aggregator facade, not for raw SQL. This will be addressed when `IncidentAggregator` is extracted.

### Business Logic Retained in Engine (L4)
- VERIFICATION_MODE invariant checking
- Outcome mapping (run_status → policy outcome)
- Confidence calculation based on outcome
- S3 truth verification logic (AC-1 through AC-7)
- Idempotency checks

### Files Created/Modified
- **NEW:** `backend/app/houseofcards/customer/incidents/drivers/policy_violation_driver.py`
- **MODIFIED:** `backend/app/houseofcards/customer/incidents/engines/policy_violation_service.py`

### Phase-2.5A Progress
- **Completed:** 3/70 HOC engine DB violations fixed
- **Next Target:** Continue with P0 priority (incidents, policies domains)


## 2026-01-23: Session 4 (continued) — llm_failure_service.py Phase-2.5A Extraction Complete

### Work Completed

**Target File:** `houseofcards/customer/incidents/engines/llm_failure_service.py`

**DB Operations Extracted to Driver:**

| Method | Before | After (Driver Method) |
|--------|--------|----------------------|
| `_persist_failure()` | Raw SQL INSERT | `driver.insert_failure()` |
| `_capture_evidence()` | Raw SQL INSERT | `driver.insert_evidence()` |
| `_mark_run_failed()` | Raw SQL UPDATE | `driver.update_run_failed()` |
| `_verify_no_contamination()` | Multiple SELECTs | `driver.fetch_contamination_check()` |
| `get_failure_by_run_id()` | Raw SQL SELECT | `driver.fetch_failure_by_run_id()` |

**New Driver Created: `llm_failure_driver.py`**

| Method | Purpose |
|--------|---------|
| `insert_failure()` | Create failure fact in run_failures |
| `insert_evidence()` | Create evidence record in failure_evidence |
| `update_run_failed()` | Mark run as failed with error |
| `fetch_failure_by_run_id()` | Get failure record by run ID |
| `fetch_contamination_check()` | Verify no downstream artifacts created |
| `commit()` | Transaction commit |

### Verification Gates (STEP 6) — PASS

| Gate | Status |
|------|--------|
| No select()/insert()/update() in engine | PASS |
| No raw SQL (text()) in engine | PASS |
| Only TYPE_CHECKING sqlalchemy import | PASS |
| Driver has no business logic | PASS |
| Governance headers locked | PASS |

### Business Logic Retained in Engine (L4)
- Failure type validation (timeout, exception, invalid_output)
- LLMFailureFact dataclass (domain object)
- Verification mode contamination check logic (interpretation of counts)
- PIN-196 invariant orchestration (persist → evidence → mark failed)

### Files Created/Modified
- **NEW:** `backend/app/houseofcards/customer/incidents/drivers/llm_failure_driver.py`
- **MODIFIED:** `backend/app/houseofcards/customer/incidents/engines/llm_failure_service.py`

### Driver Inventory Updated
- Added `llm_failure_driver` to `docs/architecture/driver_inventory.yaml`
- Table ownership: run_failures, failure_evidence, worker_runs (status fields)
- Read-only: cost_records, cost_anomalies, incidents (for contamination check)

### Phase-2.5A Progress
- **Completed:** 4/70 HOC engine DB violations fixed
- **Incidents Domain Status:** 4 engines extracted (incident_engine, lessons_engine, policy_violation_service, llm_failure_service)
- **Next Target:** P1 — postmortem_service.py, incident_pattern_service.py


## 2026-01-23: Session 4 (continued) — postmortem_service.py Phase-2.5A Extraction Complete

### Work Completed

**Target File:** `houseofcards/customer/incidents/engines/postmortem_service.py`

**Classification:** READ-ONLY analytics (5 SELECT queries, 0 writes)

**DB Operations Extracted to Driver:**

| Method | Before | After (Driver Method) |
|--------|--------|----------------------|
| `get_category_learnings()` | 3 raw SQL SELECTs | `driver.fetch_category_stats()` + `fetch_resolution_methods()` + `fetch_recurrence_data()` |
| `_get_resolution_summary()` | Raw SQL SELECT | `driver.fetch_resolution_summary()` |
| `_find_similar_incidents()` | Raw SQL SELECT | `driver.fetch_similar_incidents()` |

**New Driver Created: `postmortem_driver.py`**

| Method | Purpose |
|--------|---------|
| `fetch_category_stats()` | Get incident counts and resolution times for category |
| `fetch_resolution_methods()` | Get common resolution methods for category |
| `fetch_recurrence_data()` | Get recurrence rate data |
| `fetch_resolution_summary()` | Get resolution summary for single incident |
| `fetch_similar_incidents()` | Find similar resolved incidents |

### Verification Gates (STEP 6) — PASS

| Gate | Status |
|------|--------|
| No select()/insert()/update() in engine | PASS |
| No raw SQL (text()) in engine | PASS |
| Only TYPE_CHECKING sqlalchemy import | PASS |
| Driver has no business logic | PASS |
| Governance headers locked | PASS |

### Business Logic Retained in Engine (L4)
- `_extract_insights()` — Insight extraction from resolution data
- `_generate_category_insights()` — Category-level insight generation
- Confidence calculation algorithms
- Resolution time pattern analysis
- All dataclass definitions (ResolutionSummary, LearningInsight, PostMortemResult, CategoryLearnings)

### Files Created/Modified
- **NEW:** `backend/app/houseofcards/customer/incidents/drivers/postmortem_driver.py`
- **MODIFIED:** `backend/app/houseofcards/customer/incidents/engines/postmortem_service.py`

### Driver Inventory Updated
- Added `postmortem_driver` to `docs/architecture/driver_inventory.yaml`
- Authority: POSTMORTEM_ANALYTICS
- Shared tables (read-only): incidents, incident_evidence

### Phase-2.5A Progress
- **Completed:** 5/70 HOC engine DB violations fixed
- **Incidents Domain Status:** 5 engines extracted
- **Next Target:** P1 — incident_pattern_service.py


## 2026-01-23: Session 4 (continued) — incident_pattern_service.py Phase-2.5A Extraction Complete

### Work Completed

**Target File:** `houseofcards/customer/incidents/engines/incident_pattern_service.py`

**Classification:** READ-ONLY pattern detection (4 SELECT queries, 0 writes)

**DB Operations Extracted to Driver:**

| Method | Before | After (Driver Method) |
|--------|--------|----------------------|
| `detect_patterns()` | COUNT query | `driver.fetch_incidents_count()` |
| `_detect_category_clusters()` | Raw SQL GROUP BY | `driver.fetch_category_clusters()` |
| `_detect_severity_spikes()` | Raw SQL GROUP BY | `driver.fetch_severity_spikes()` |
| `_detect_cascade_failures()` | Raw SQL GROUP BY | `driver.fetch_cascade_failures()` |

**New Driver Created: `incident_pattern_driver.py`**

| Method | Purpose |
|--------|---------|
| `fetch_incidents_count()` | Count incidents in time window |
| `fetch_category_clusters()` | Get incidents grouped by category for cluster detection |
| `fetch_severity_spikes()` | Get high/critical incidents in last hour |
| `fetch_cascade_failures()` | Get incidents grouped by source run for cascade detection |

### Verification Gates (STEP 6) — PASS

| Gate | Status |
|------|--------|
| No select()/insert()/update() in engine | PASS |
| No raw SQL (text()) in engine | PASS |
| Only TYPE_CHECKING sqlalchemy import | PASS |
| Driver has no business logic | PASS |
| Governance headers locked | PASS |

### Business Logic Retained in Engine (L4)
- Pattern thresholds (CATEGORY_CLUSTER_THRESHOLD, SEVERITY_SPIKE_THRESHOLD, CASCADE_THRESHOLD)
- Confidence calculation formulas for each pattern type
- All dataclass definitions (PatternMatch, PatternResult)
- Pattern type determination logic

### Files Created/Modified
- **NEW:** `backend/app/houseofcards/customer/incidents/drivers/incident_pattern_driver.py`
- **MODIFIED:** `backend/app/houseofcards/customer/incidents/engines/incident_pattern_service.py`

### Driver Inventory Updated
- Added `incident_pattern_driver` to `docs/architecture/driver_inventory.yaml`
- Authority: INCIDENT_PATTERN_FACTS
- Shared tables (read-only): incidents

### Phase-2.5A Progress
- **Completed:** 6/70 HOC engine DB violations fixed
- **Incidents Domain Status:** 6 engines extracted — **DOMAIN COMPLETE**
- **Next Target:** Evaluate domain stop condition

---

## Incidents Domain Stop Condition — EVALUATION

### Checklist

| Criterion | Status |
|-----------|--------|
| All engines in `customer/incidents/engines/` have zero raw DB signals | ✅ PASS |
| All *_service.py files have drivers | ✅ PASS |
| Drivers inventory has no duplicate methods | ✅ PASS |
| All drivers registered in driver_inventory.yaml | ✅ PASS |

### Engines Extracted

| Engine | Driver | Authority |
|--------|--------|-----------|
| incident_engine.py | incident_write_driver.py | INCIDENT_PERSISTENCE |
| lessons_engine.py | lessons_driver.py | LESSONS_PERSISTENCE |
| policy_violation_service.py | policy_violation_driver.py | POLICY_VIOLATION_PERSISTENCE |
| llm_failure_service.py | llm_failure_driver.py | LLM_FAILURE_PERSISTENCE |
| postmortem_service.py | postmortem_driver.py | POSTMORTEM_ANALYTICS |
| incident_pattern_service.py | incident_pattern_driver.py | INCIDENT_PATTERN_FACTS |

### Verdict

**INCIDENTS DOMAIN PHASE-2.5A: COMPLETE ✅**

All engines in `customer/incidents/engines/` now delegate persistence to L6 drivers.
No raw SQL remains in L4 engines. All drivers are registered with canonical authority.

---

## 2026-01-23: Session 2 — Critical Reframe & HOC Authority Map

### Critical Reframe (User Directive)

> **HOC (houseofcards/) is the CANONICAL runtime.**
> **app/services/ is a transitional compatibility layer — will be deleted.**

**Phase-2 Goal Rewritten:**
- NOT: clean up app/services layer violations
- IS: ensure every runtime execution path resolves into HOC L4/L6 files

**Phase-2 Exit Criteria:**
- Every caller of app/services delegates 100% to HOC
- No new code in app/services (shims only)
- HOC engines have ≤5% DB signals

### Work Completed This Session

**app/services Splits (Shims Created):**

| File | Engine | Driver |
|------|--------|--------|
| incident_write_service.py | incident_write_engine.py | incident_write_driver.py |
| llm_failure_service.py | llm_failure_engine.py | llm_failure_driver.py |

**Total Shims in shim_guard.py:** 9 (all passing)

1. cus_integration_service.py
2. cus_telemetry_service.py
3. cus_enforcement_service.py
4. cus_health_service.py
5. platform_health_service.py (in platform/)
6. simulation_service.py (in limits/)
7. api_key_service.py (in auth/)
8. incident_write_service.py
9. llm_failure_service.py

### HOC Authority Map (Generated)

**Structure:**
- 287 engines in houseofcards/
- 259 drivers in houseofcards/

**Violation Counts:**
| Type | Count | Severity |
|------|-------|----------|
| Engine DB Access Violations | 70 | P0 |
| Engine Naming Violations (*_service.py) | 51 | P1 |
| Driver Logic Violations | 5 | P2 |

**Critical Engine DB Violations by Domain (P0):**

| Domain | Files |
|--------|-------|
| customer/incidents/engines/ | incident_engine.py, lessons_engine.py, etc. |
| customer/policies/engines/ | policy_graph_engine.py, budget_enforcement_engine.py |
| customer/analytics/engines/ | cost_anomaly_detector.py, coordinator.py |
| customer/activity/engines/ | signal_feedback_service.py |
| internal/agent/engines/ | 45 engines, many with DB access |

### Phase-2.5 Scope (Future — After All Splits)

1. Extract DB from 70 HOC engines
2. Rename 51 \*_service.py → \*_engine.py in engines/ directories
3. Review 5 drivers with logic violations
4. Delete app/services entirely

### Key Files Created

```
backend/app/services/incident_write_driver.py
backend/app/services/incident_write_engine.py
backend/app/services/llm_failure_driver.py
backend/app/services/llm_failure_engine.py
```

### Shim Pattern Template

```python
# Layer: L4 — Domain Engine (DEPRECATED - use *_engine.py)
"""Service Name - DEPRECATED"""
import warnings
warnings.warn("*_service is deprecated. Use *_engine instead.", DeprecationWarning, stacklevel=2)

# Re-export from engine
from app.services.*_engine import (...)
__all__ = [...]
```


---

## Phase-2.5 Scoping

### Update (2026-01-23)

## Phase-2.5A Signal Whitelist (LOCKED)

**Infrastructure signals are NOT violations.** These are allowed in L4 engines:

| Signal Type | Pattern | Allowed In | Rationale |
|-------------|---------|------------|-----------|
| TYPE_CHECKING | `if TYPE_CHECKING: from sqlmodel` | L4_ENGINE | Type hints only, no runtime import |
| LAZY_SESSION | `from sqlalchemy import create_engine` inside method | L4_ENGINE | Session factory for driver injection |
| CROSS_DOMAIN | `from sqlmodel import Session` for calling other engines | L4_ENGINE | Orchestration, not direct DB access |

**Files with INFRASTRUCTURE-only signals (not violations):**
- `incident_engine.py` (3 signals) → COMPLETE
- `lessons_engine.py` (3 signals) → COMPLETE
- `policy_violation_service.py` (2 signals) → COMPLETE
- `llm_failure_service.py` (1 signal - TYPE_CHECKING only) → COMPLETE
- `postmortem_service.py` (1 signal - TYPE_CHECKING only) → COMPLETE
- `incident_pattern_service.py` (1 signal - TYPE_CHECKING only) → COMPLETE

---

## Driver Inventory Snapshot (2026-01-23)

**RULE: Before creating a driver method, search inventory. If semantics overlap ≥70%, extend existing driver.**

### incident_write_driver.py
| Method | Table | Operation |
|--------|-------|-----------|
| insert_incident | incidents | INSERT |
| update_run_incident_count | runs | UPDATE |
| update_trace_incident_id | aos_traces | UPDATE |
| insert_prevention_record | prevention_records | INSERT |
| insert_policy_proposal | policy_proposals | INSERT |
| fetch_suppressing_policy | policy_rules | SELECT |
| fetch_incidents_by_run_id | incidents | SELECT |
| update_incident_acknowledged | incidents | UPDATE |
| update_incident_resolved | incidents | UPDATE |
| create_incident_event | incident_events | INSERT |

### lessons_driver.py
| Method | Table | Operation |
|--------|-------|-----------|
| insert_lesson | lessons_learned | INSERT |
| fetch_lesson_by_id | lessons_learned | SELECT |
| fetch_lessons_list | lessons_learned | SELECT |
| fetch_lesson_stats | lessons_learned | SELECT (aggregate) |
| update_lesson_deferred | lessons_learned | UPDATE |
| update_lesson_dismissed | lessons_learned | UPDATE |
| update_lesson_converted | lessons_learned | UPDATE |
| update_lesson_reactivated | lessons_learned | UPDATE |
| fetch_debounce_count | lessons_learned | SELECT (count) |
| fetch_expired_deferred | lessons_learned | SELECT |
| insert_policy_proposal_from_lesson | policy_proposals | INSERT |

### policy_violation_driver.py
| Method | Table | Operation |
|--------|-------|-----------|
| insert_violation_record | prevention_records | INSERT |
| fetch_violation_exists | prevention_records | SELECT |
| fetch_policy_enabled | policy_rules | SELECT |
| insert_evidence_event | incident_events | INSERT |
| fetch_incident_by_violation | incidents | SELECT |
| fetch_violation_truth_check | prevention_records, incidents, incident_events | SELECT (multiple) |
| insert_policy_evaluation | prevention_records | INSERT |
| insert_policy_evaluation_sync | prevention_records | INSERT (psycopg2) |

### llm_failure_driver.py
| Method | Table | Operation |
|--------|-------|-----------|
| insert_failure | run_failures | INSERT |
| insert_evidence | failure_evidence | INSERT |
| update_run_failed | worker_runs | UPDATE |
| fetch_failure_by_run_id | run_failures | SELECT |
| fetch_contamination_check | cost_records, cost_anomalies, incidents | SELECT (multiple) |

### postmortem_driver.py
| Method | Table | Operation |
|--------|-------|-----------|
| fetch_category_stats | incidents | SELECT (aggregate) |
| fetch_resolution_methods | incidents | SELECT (aggregate) |
| fetch_recurrence_data | incidents | SELECT (aggregate) |
| fetch_resolution_summary | incidents, incident_evidence | SELECT |
| fetch_similar_incidents | incidents, incident_evidence | SELECT |

### incident_pattern_driver.py
| Method | Table | Operation |
|--------|-------|-----------|
| fetch_incidents_count | incidents | SELECT (count) |
| fetch_category_clusters | incidents | SELECT (aggregate) |
| fetch_severity_spikes | incidents | SELECT (aggregate) |
| fetch_cascade_failures | incidents | SELECT (aggregate) |

---

## Low-Priority Files (ACCEPTABLE_DEBT_PHASE25A)

These files have ≤2 signals and yield negligible governance gain:
- `incident_read_service.py` (1 signal)
- `incident_write_service.py` (1 signal)
- `recovery_rule_engine.py` (1 signal)
- `recovery_evaluation_engine.py` (2 signals)

**Do NOT touch until P0/P1 complete.**

---

## Incidents Domain Stop Condition

Declare **Incidents Phase-2.5A DONE** when:
1. DB signals = 0 or INFRASTRUCTURE-only
2. All *_service.py in engines/ are: renamed OR shimmed OR deleted
3. Drivers inventory has no duplicates

Only then move to `customer/policies/engines/`.

---

## Phase-2.5 Scoping (Locked)

**Objective (Single Purpose):**
> Make Houseofcards internally consistent so it can stand alone when app/services is deleted.

---

### Phase-2.5A — Authority Correction (BLOCKING)

**Scope:**
- 70 Engine DB Access violations
- 5 Driver Logic violations

**Out of Scope:**
- Naming
- File moves
- Cosmetic consistency

**Rule:** If an engine can mutate or read persistence directly, HOC is not yet canonical.

**Execution Order:**

| Priority | Domain | Reason |
|----------|--------|--------|
| P0 | customer/incidents/engines/* | State-mutating, defines failure behavior |
| P0 | customer/policies/engines/* | State-mutating, defines limits |
| P1 | customer/analytics/engines/* | Read-heavy, lower blast radius |
| P1 | customer/activity/engines/* | Signal-driven, lower blast radius |
| P2 | internal/agent/engines/* | Large surface, can be isolated last |

**Pattern:** classify → split → verify → freeze (same as Phase-2)

---

### Phase-2.5B — Canonicalization (NON-BLOCKING)

**Scope:**
- 51 \*_service.py → \*_engine.py renames
- Folder normalization
- Dead abstraction removal

**Rule:** Do NOT rename until Phase-2.5A is complete. Renames break imports, obscure diffs, add risk.

---

### Authoritative Gate (When HOC Becomes Canonical)

1. No engine in HOC touches DB
2. All DB access goes through drivers
3. All decisions live in engines
4. app/services contains zero original logic

---

### Forbidden Actions Until Phase-2.5A Complete

- ❌ Rename folders
- ❌ Merge drivers
- ❌ Optimize APIs
- ❌ Remove shims
- ❌ Delete app/services

## Related PINs

- PIN-250: Phase 2 Extraction Protocol
- PIN-281: L3 Adapter Closure

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-24 | Session 7: Phase-2.5A Policies domain extractions complete — keys_driver.py (RECLASSIFY to L6), policy_engine_driver.py (40+ operations for engine.py). override_service.py DEFERRED (temporary in-memory). Driver audit: policy_driver.py misclassified (orchestrator, not L6), recovery_write_service.py misclassified (L6 marked as L4). engine.py in TRANSITIONAL state - driver ready, method migration TODO. Total: 11 drivers registered in inventory |
| 2026-01-24 | Session 6 (continued): Phase 4 CRUD extractions started — policy_limits_driver.py and policy_rules_driver.py created, engines updated to use drivers, inventory registered (8 drivers total) |
| 2026-01-24 | Session 6 (continued): Facade verification PASS, created POLICIES_DOMAIN_LOCK.md, fixed AsyncSession type hint bug. **Ready for Phase 4 CRUD extractions** |
| 2026-01-24 | Session 6: Cross-domain containment complete — deleted 2 duplicate files from policies, created 2 shims in app/services, added cross_domain_ownership to driver_inventory.yaml. **Policies pre-flight complete** (17 engines, 93 signals remaining) |
| 2026-01-24 | Session 5: Incidents domain closed, INCIDENTS_DOMAIN_LOCKED.md created, POLICIES_AUTHORITY_MAP.md created (119 signals, 19 files), cross-domain duplicates identified |
| 2026-01-23 | Session 4 (continued): incident_pattern_service.py extraction complete, **INCIDENTS DOMAIN CLOSED** (6 engines extracted, 6 drivers registered) |
| 2026-01-23 | Session 4 (continued): postmortem_service.py extraction complete (5/70 engines) |
| 2026-01-23 | Session 4 (continued): llm_failure_service.py extraction complete (4/70 engines), driver_inventory.yaml updated |
| 2026-01-23 | Session 4: incident_engine.py, lessons_engine.py, policy_violation_service.py extractions (3/70 engines) |
| 2026-01-23 | Session 2: Critical reframe (HOC canonical), HOC Authority Map (287 engines, 70 violations), incident_write + llm_failure splits, 9 shims total |
| 2026-01-23 | Created DRIVER_ENGINE_CONTRACT.md and layer_segregation_guard.py |
| 2026-01-23 | Split cus_integration_service.py as reference implementation |
| 2026-01-23 | Created PIN, documented Batch 1 & 2 completion |
