# Cross-Domain Governance Design

**PIN**: N/A (Pre-PIN Design Consolidation)
**Status**: DRAFT
**Created**: 2026-01-17
**Author**: Architecture Review

---

## Executive Summary

This document establishes the governance architecture for cross-domain data flow in customer-facing paths. The core principle: **boring, mandatory function calls that succeed or raise**.

No new abstractions. No optional dispatchers. No silent failures.

---

## 1. Objective

### 1.1 Problem Statement

The codebase has accumulated three distinct event/signal patterns:

| Pattern | Location | Purpose | Audience |
|---------|----------|---------|----------|
| **OpsEvent** | `event_emitter.py` | Operational telemetry | Founder Console (human analytics) |
| **LoopEvent** | `integrations/events.py` | M25 integration loop | Dogfooding (internal learning) |
| **Implicit Sync** | Various services | Cross-domain updates | Customer Console |

The problem: **customer-facing governance is optional**. Code patterns like `dispatcher=None` allow governance to be silently skipped, creating data inconsistency and audit gaps.

### 1.2 Goal

Establish mandatory governance for customer-facing paths:

1. **Activity → Incidents**: Run failures MUST create incidents
2. **Analytics → Incidents**: Cost anomalies MUST create incidents
3. **Policies ↔ Analytics**: Limit breaches MUST be recorded
4. **Overview → All**: Aggregation MUST degrade gracefully on missing data

### 1.3 Non-Goals

- Modifying M25 (FROZEN)
- Creating new abstraction layers (DomainSignal, GovernanceEvent)
- Replacing OpsEvent (serves different purpose)
- Unifying all event systems (they serve different audiences)

---

## 2. Doctrine

### Rule 1: Governance Must Throw

```python
# WRONG - Silent failure
if dispatcher:
    dispatcher.emit(event)

# RIGHT - Mandatory failure
def record_incident(session: Session, incident: Incident) -> str:
    """Record incident. Raises GovernanceError on failure."""
    try:
        session.add(incident)
        session.flush()
        return incident.id
    except Exception as e:
        raise GovernanceError(f"Failed to record incident: {e}") from e
```

### Rule 2: No Optional Dependencies in Governance Paths

```python
# WRONG - Optional dispatcher
async def process_anomaly(
    anomaly: CostAnomaly,
    dispatcher: Optional[IntegrationDispatcher] = None  # VIOLATION
):
    ...

# RIGHT - Mandatory function
async def process_anomaly(
    session: AsyncSession,
    anomaly: CostAnomaly,
) -> str:
    """Process anomaly. Returns incident_id. Raises GovernanceError on failure."""
    incident = create_incident_from_anomaly(anomaly)
    return record_incident(session, incident)
```

### Rule 3: Learning is Downstream Only

```
Customer Path (MANDATORY)         Dogfood Path (OPTIONAL)
─────────────────────────         ──────────────────────
Run fails
    │
    ▼
create_incident()  ──────────────► M25 LoopEvent (if enabled)
    │                                    │
    ▼                                    ▼
Database commit                   Pattern learning
    │                             Policy proposals
    ▼
Customer sees incident
```

M25 lives downstream. If M25 fails, the customer still sees their incident.

### Corollary: Governance Errors Must Surface

Any `GovernanceError` **must**:

* Fail the request **or**
* Mark the operation as failed in a customer-visible way

It must **never** be:

* Logged and ignored
* Converted into a warning
* Retried-hidden
* Deferred to async repair

**Rationale:** Engineers will be tempted to "handle" GovernanceError. This corollary removes ambiguity and closes the last escape hatch. Silent handling of governance errors is a governance violation.

---

## 3. Findings

### 3.1 Missing Database Tables

**Status**: Migration exists, may not be applied

| Table | Migration | Status |
|-------|-----------|--------|
| `limits` | 088_policy_control_plane | EXISTS (check if applied) |
| `limit_breaches` | 088_policy_control_plane | EXISTS (check if applied) |
| `policy_rules` | 088_policy_control_plane | EXISTS (check if applied) |
| `policy_enforcements` | 088_policy_control_plane | EXISTS (check if applied) |

**Action**: Run `alembic upgrade head` and verify tables exist.

### 3.2 Governance Violations (dispatcher=None Pattern)

Seven locations allow governance to be silently skipped:

| File | Line | Pattern | Severity |
|------|------|---------|----------|
| `cost_anomaly_detector.py` | 1128 | `dispatcher=None` | CRITICAL |
| `cost_anomaly_detector.py` | 1149 | `if ... and dispatcher:` | CRITICAL |
| `cost_bridges.py` | 180 | `dispatcher=None` | HIGH |
| `cost_bridges.py` | 201 | `dispatcher=None` | HIGH |
| `cost_bridges.py` | 1064 | `dispatcher=None` | HIGH |
| `cost_safety_rails.py` | TBD | `dispatcher=None` | HIGH |
| `cost_intelligence.py` | TBD | `dispatcher=None` | HIGH |

### 3.3 Missing GovernanceError Class

**Status**: Does not exist

The codebase has no dedicated exception for governance failures. Currently, governance failures either:
- Raise generic exceptions (losing semantic meaning)
- Log and continue (silent failure)
- Return None (caller doesn't know about failure)

### 3.4 OpsEvent Clarification

**OpsEvent is NOT for cross-domain sync.** It serves:

| Aspect | OpsEvent | Cross-Domain Governance |
|--------|----------|------------------------|
| Audience | Founder Console (humans) | Customer Console (data integrity) |
| Purpose | Analytics, friction detection | Mandatory data relationships |
| Failure Mode | Degraded dashboards | Data inconsistency |
| Timing | Retrospective | Real-time |
| Cardinality | One per user action | One per domain entity |

### 3.5 M25 Status

**Status**: FROZEN

```python
# M25_FROZEN - DO NOT MODIFY
# Any changes here require explicit M25 reopen approval.
# Changes invalidate all prior graduation evidence.
```

M25 (`integrations/events.py`, `integrations/dispatcher.py`) cannot be modified. Use wrapper pattern for dogfooding integration.

---

## 4. Macro Plan

### Phase 0: Database Foundation (Prerequisite)

Ensure all migrations are applied and tables exist.

### Phase 1: Mandatory Governance (Core Work)

1. Create `GovernanceError` exception class
2. Remove all `dispatcher=None` patterns
3. Replace with mandatory function calls
4. Add defensive queries for Overview

### Phase 2: Dogfood Integration (Optional Enhancement)

1. Create M25 wrapper that calls existing functions
2. Wire wrapper to emit LoopEvents downstream
3. M25 failure does NOT affect customer path

---

## 5. Granular Topics

### 5.1 GovernanceError Class Design

```python
# app/errors/governance.py

class GovernanceError(Exception):
    """
    Raised when a governance operation fails.

    Governance operations are MANDATORY - they must succeed or the
    entire operation must fail. This includes:
    - Incident creation from run failures
    - Incident creation from cost anomalies
    - Limit breach recording
    - Policy enforcement recording
    """

    def __init__(
        self,
        message: str,
        domain: str,
        operation: str,
        entity_id: Optional[str] = None,
    ):
        self.domain = domain
        self.operation = operation
        self.entity_id = entity_id
        super().__init__(f"[{domain}] {operation}: {message}")
```

### 5.2 Mandatory Incident Creation

```python
# app/services/governance/incidents.py

from app.errors.governance import GovernanceError

async def create_incident_from_run_failure(
    session: AsyncSession,
    run_id: str,
    failure_reason: str,
    tenant_id: str,
) -> str:
    """
    Create incident from run failure. MANDATORY.

    Returns: incident_id
    Raises: GovernanceError if incident cannot be created
    """
    try:
        incident = Incident(
            id=generate_uuid(),
            tenant_id=tenant_id,
            run_id=run_id,
            source="RUN_FAILURE",
            status="OPEN",
            severity="HIGH",
            title=f"Run {run_id[:8]} failed",
            description=failure_reason,
            created_at=utc_now(),
        )
        session.add(incident)
        await session.flush()
        return incident.id
    except Exception as e:
        raise GovernanceError(
            message=str(e),
            domain="Activity",
            operation="create_incident_from_run_failure",
            entity_id=run_id,
        ) from e


async def create_incident_from_cost_anomaly(
    session: AsyncSession,
    anomaly: CostAnomaly,
    tenant_id: str,
) -> str:
    """
    Create incident from cost anomaly. MANDATORY.

    Returns: incident_id
    Raises: GovernanceError if incident cannot be created
    """
    try:
        incident = Incident(
            id=generate_uuid(),
            tenant_id=tenant_id,
            source="COST_ANOMALY",
            status="OPEN",
            severity=anomaly_to_severity(anomaly),
            title=f"Cost anomaly detected: {anomaly.anomaly_type}",
            description=anomaly.description,
            metadata={"anomaly_id": anomaly.id},
            created_at=utc_now(),
        )
        session.add(incident)
        await session.flush()
        return incident.id
    except Exception as e:
        raise GovernanceError(
            message=str(e),
            domain="Analytics",
            operation="create_incident_from_cost_anomaly",
            entity_id=anomaly.id,
        ) from e
```

### 5.3 Defensive Overview Queries

```python
# app/api/overview.py - Defensive pattern

async def get_limit_breach_count(
    session: AsyncSession,
    tenant_id: str,
    since: datetime,
) -> int:
    """
    Get limit breach count. Returns 0 if table doesn't exist.

    This is a read-only aggregation - failure is acceptable.
    """
    try:
        result = await session.execute(
            select(func.count(LimitBreach.id))
            .where(LimitBreach.tenant_id == tenant_id)
            .where(LimitBreach.breached_at >= since)
        )
        return result.scalar() or 0
    except Exception as e:
        # Table may not exist yet - degrade gracefully
        logger.warning(f"limit_breaches query failed: {e}")
        return 0
```

### 5.4 Removing dispatcher=None Pattern

**Before** (cost_anomaly_detector.py:1128):
```python
async def process_high_severity_anomalies(
    anomalies: List[CostAnomaly],
    dispatcher: Optional[IntegrationDispatcher] = None,
):
    for anomaly in anomalies:
        # ... processing ...
        if dispatcher:
            await dispatcher.emit(LoopEvent(...))
```

**After**:
```python
async def process_high_severity_anomalies(
    session: AsyncSession,
    anomalies: List[CostAnomaly],
    tenant_id: str,
) -> List[str]:
    """
    Process high severity anomalies. Creates incidents.

    Returns: List of incident_ids
    Raises: GovernanceError if any incident creation fails
    """
    incident_ids = []
    for anomaly in anomalies:
        # ... processing ...
        incident_id = await create_incident_from_cost_anomaly(
            session, anomaly, tenant_id
        )
        incident_ids.append(incident_id)
    return incident_ids
```

---

## 6. Domain Use Cases

### 6.1 Activity → Incidents

**Trigger**: Run completes with `status=FAILED`

**Flow**:
```
RunService.complete_run(status=FAILED)
    │
    ▼
create_incident_from_run_failure(session, run_id, reason, tenant_id)
    │
    ├── SUCCESS: incident_id returned, run linked
    │
    └── FAILURE: GovernanceError raised, transaction rolled back
                 Run status NOT updated (atomic)
```

**Invariant**: Every FAILED run has exactly one incident.

### 6.2 Analytics → Incidents

**Trigger**: Cost anomaly detector finds HIGH/CRITICAL anomaly

**Flow**:
```
CostAnomalyDetector.detect()
    │
    ▼ (anomaly.severity >= HIGH)
    │
create_incident_from_cost_anomaly(session, anomaly, tenant_id)
    │
    ├── SUCCESS: incident_id returned, anomaly linked
    │
    └── FAILURE: GovernanceError raised, detection rolled back
                 Anomaly not persisted (atomic)
```

**Invariant**: Every HIGH+ anomaly has exactly one incident.

### 6.3 Policies ↔ Analytics

**Trigger**: Cost exceeds budget limit

**Flow**:
```
CostTracker.record_cost(run_id, cost_usd)
    │
    ▼ (check limits)
    │
check_budget_limits(session, tenant_id, cost_usd)
    │
    ├── UNDER LIMIT: return None
    │
    └── OVER LIMIT:
        │
        ▼
        record_limit_breach(session, limit_id, run_id, value, limit)
            │
            ├── SUCCESS: breach_id returned
            │
            └── FAILURE: GovernanceError raised
```

**Invariant**: Every limit breach is recorded in `limit_breaches`.

### 6.4 Overview Aggregation

**Trigger**: Dashboard load

**Flow**:
```
GET /api/overview/summary
    │
    ▼
get_overview_summary(session, tenant_id)
    │
    ├── get_active_run_count() ─────── [runs table - required]
    │
    ├── get_open_incident_count() ──── [incidents table - required]
    │
    ├── get_limit_breach_count() ───── [limit_breaches - DEFENSIVE]
    │                                   Returns 0 if table missing
    │
    └── get_cost_this_period() ──────── [cost_records - required]
```

**Invariant**: Overview NEVER fails. Missing tables return zero/empty.

---

## 7. Molecular Todo List

### Phase 0: Database Foundation

- [ ] **P0-1**: Verify migration 088 is applied
  ```bash
  alembic current
  alembic upgrade head  # if needed
  ```

- [ ] **P0-2**: Verify tables exist
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public'
  AND table_name IN ('limits', 'limit_breaches', 'policy_rules', 'policy_enforcements');
  ```

- [ ] **P0-3**: Run model validation
  ```bash
  python -c "from app.models.policy_control_plane import *; print('OK')"
  ```

### Phase 1: Mandatory Governance

#### 1A: Create GovernanceError

- [ ] **P1A-1**: Create `app/errors/governance.py` with GovernanceError class
- [ ] **P1A-2**: Add to `app/errors/__init__.py` exports
- [ ] **P1A-3**: Write unit tests for GovernanceError

#### 1B: Create Governance Functions

- [ ] **P1B-1**: Create `app/services/governance/__init__.py`
- [ ] **P1B-2**: Create `app/services/governance/incidents.py`
  - `create_incident_from_run_failure()`
  - `create_incident_from_cost_anomaly()`
- [ ] **P1B-3**: Create `app/services/governance/limits.py`
  - `record_limit_breach()`
  - `check_budget_limits()`
- [ ] **P1B-4**: Write unit tests for governance functions

#### 1C: Fix cost_anomaly_detector.py

- [ ] **P1C-1**: Line 1128 - Remove `dispatcher=None` parameter
- [ ] **P1C-2**: Line 1149 - Replace `if ... and dispatcher:` with mandatory call
- [ ] **P1C-3**: Update all callers to pass session instead of dispatcher
- [ ] **P1C-4**: Run existing tests, fix failures

#### 1D: Fix cost_bridges.py

- [ ] **P1D-1**: Line 180 - Remove `dispatcher=None` parameter
- [ ] **P1D-2**: Line 201 - Remove `dispatcher=None` parameter
- [ ] **P1D-3**: Line 1064 - Remove `dispatcher=None` parameter
- [ ] **P1D-4**: Update all callers
- [ ] **P1D-5**: Run existing tests, fix failures

#### 1E: Fix cost_safety_rails.py

- [ ] **P1E-1**: Locate and remove `dispatcher=None` patterns
- [ ] **P1E-2**: Replace with mandatory governance calls
- [ ] **P1E-3**: Update all callers
- [ ] **P1E-4**: Run existing tests, fix failures

#### 1F: Fix cost_intelligence.py

- [ ] **P1F-1**: Locate and remove `dispatcher=None` patterns
- [ ] **P1F-2**: Replace with mandatory governance calls
- [ ] **P1F-3**: Update all callers
- [ ] **P1F-4**: Run existing tests, fix failures

#### 1G: Defensive Overview Queries

- [ ] **P1G-1**: `app/api/overview.py` - Wrap `limit_breaches` query in try/except
- [ ] **P1G-2**: Add logging for graceful degradation
- [ ] **P1G-3**: Write integration test for missing table scenario

### Phase 2: Dogfood Integration (Optional)

- [ ] **P2-1**: Create `app/integrations/governance_wrapper.py`
  - Wraps governance functions
  - Emits LoopEvents downstream (fire-and-forget)
  - Never blocks customer path on M25 failure

- [ ] **P2-2**: Wire wrapper via feature flag
  ```python
  if settings.M25_DOGFOOD_ENABLED:
      await emit_loop_event_async(...)  # Non-blocking
  ```

- [ ] **P2-3**: Add metrics for M25 emission success/failure

---

## 8. Verification Checklist

After implementation, verify:

- [ ] `dispatcher=None` pattern returns 0 results:
  ```bash
  grep -r "dispatcher.*=.*None" app/services/ app/integrations/
  ```

- [ ] All governance functions raise GovernanceError on failure (unit tests)

- [ ] Overview API returns valid response even with missing tables (integration test)

- [ ] Run failure creates incident (integration test)

- [ ] Cost anomaly creates incident (integration test)

- [ ] Budget breach creates limit_breach record (integration test)

---

## 9. References

- **Migration 088**: `alembic/versions/088_policy_control_plane.py`
- **Policy Models**: `app/models/policy_control_plane.py`
- **M25 Events** (FROZEN): `app/integrations/events.py`
- **M25 Dispatcher** (FROZEN): `app/integrations/dispatcher.py`
- **OpsEvent**: `app/services/event_emitter.py`
- **Cost Anomaly Detector**: `app/services/cost_anomaly_detector.py`
- **Cost Bridges**: `app/integrations/cost_bridges.py`

---

## Appendix A: File Locations for Violations

```
app/services/cost_anomaly_detector.py:1128  dispatcher=None
app/services/cost_anomaly_detector.py:1149  if ... and dispatcher
app/integrations/cost_bridges.py:180        dispatcher=None
app/integrations/cost_bridges.py:201        dispatcher=None
app/integrations/cost_bridges.py:1064       dispatcher=None
app/services/cost_safety_rails.py           dispatcher=None (TBD line)
app/services/cost_intelligence.py           dispatcher=None (TBD line)
```

## Appendix B: Migration 088 Tables

```sql
-- Created by 088_policy_control_plane.py

CREATE TABLE policy_rules (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
    name VARCHAR(256) NOT NULL,
    description TEXT,
    enforcement_mode VARCHAR(16) NOT NULL,  -- BLOCK, WARN, AUDIT, DISABLED
    scope VARCHAR(16) NOT NULL,             -- GLOBAL, TENANT, PROJECT, AGENT
    scope_id VARCHAR,
    conditions JSONB,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    created_by VARCHAR,
    source VARCHAR(16) NOT NULL DEFAULT 'MANUAL',
    source_proposal_id VARCHAR,
    parent_rule_id VARCHAR REFERENCES policy_rules(id),
    legacy_rule_id VARCHAR REFERENCES policy_rules_legacy(id),
    retired_at TIMESTAMP WITH TIME ZONE,
    retired_by VARCHAR,
    retirement_reason TEXT,
    superseded_by VARCHAR REFERENCES policy_rules(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE limits (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
    name VARCHAR(256) NOT NULL,
    description TEXT,
    limit_category VARCHAR(16) NOT NULL,    -- BUDGET, RATE, THRESHOLD
    limit_type VARCHAR(32) NOT NULL,
    scope VARCHAR(16) NOT NULL,             -- GLOBAL, TENANT, PROJECT, AGENT, PROVIDER
    scope_id VARCHAR,
    max_value NUMERIC(18,4) NOT NULL,
    reset_period VARCHAR(16),               -- DAILY, WEEKLY, MONTHLY, NONE
    next_reset_at TIMESTAMP WITH TIME ZONE,
    window_seconds INTEGER,
    measurement_window_seconds INTEGER,
    enforcement VARCHAR(16) NOT NULL DEFAULT 'BLOCK',
    consequence VARCHAR(16),                -- ALERT, INCIDENT, ABORT
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE limit_breaches (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
    limit_id VARCHAR NOT NULL REFERENCES limits(id),
    run_id VARCHAR REFERENCES runs(id),
    incident_id VARCHAR REFERENCES incidents(id),
    breach_type VARCHAR(16) NOT NULL,       -- BREACHED, EXHAUSTED, THROTTLED, VIOLATED
    value_at_breach NUMERIC(18,4),
    limit_value NUMERIC(18,4) NOT NULL,
    details JSONB,
    breached_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    recovered_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE policy_enforcements (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
    rule_id VARCHAR NOT NULL REFERENCES policy_rules(id),
    run_id VARCHAR REFERENCES runs(id),
    incident_id VARCHAR REFERENCES incidents(id),
    action_taken VARCHAR(16) NOT NULL,      -- BLOCKED, WARNED, AUDITED
    details JSONB,
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

---

## Appendix C: 10-Minute Governance Invariant Walkthrough

**Audience:** Any engineer touching cost, incidents, policies, overview, or integrations
**Goal:** Prevent silent correctness failures

---

### Minute 0-1: The One-Sentence Truth

> **If the system shows something to a customer, the invariant enforcing it must either succeed or crash loudly.**

If you remember nothing else, remember this.

---

### Minute 1-3: The Three Rules (Non-Negotiable)

#### Rule 1 - Governance Must Throw

If a customer-visible invariant is violated:

* You **must** raise `GovernanceError`
* You **must not** log-and-continue
* You **must not** return `None`

**Why:** Silent failure = lying system.

```python
# CORRECT
incident_id = await incident_engine.create_from_anomaly(...)
if not incident_id:
    raise GovernanceError("HIGH anomaly must create incident")
```

#### Rule 2 - No Optional Dependencies

Governance code **cannot** depend on optional services.

**Forbidden patterns:**

```python
dispatcher=None
if dispatcher:
    ...
```

**Why:** Optional dependency = optional correctness.

#### Rule 3 - Learning Is Downstream Only

Learning systems (M25):

* May fail
* May be disabled
* Must never block customers

```python
# AFTER correctness is guaranteed
try:
    await m25_dispatcher.dispatch(...)
except Exception:
    pass  # Allowed - learning failure
```

---

### Minute 3-5: What Is *Not* Governance

#### OpsEvent (NOT Governance)

* Telemetry
* Dashboards
* Cost analysis
* Human observability

**Not a correctness mechanism.**

#### M25 / LoopEvent (NOT Governance)

* Pattern learning
* Recovery experimentation
* Policy discovery

**Not customer-critical.**

#### Governance = Function Calls That Must Succeed

Governance lives in:

* `incident_engine.create_*`
* Policy enforcement functions
* Budget / limit checks
* Overview invariants

No events. No abstraction layers. Just truth or failure.

---

### Minute 5-7: Concrete Examples

#### Example 1 - Analytics -> Incidents (Cost Anomaly)

```python
# WRONG
if high_anomalies and dispatcher:
    await orchestrator.process_anomaly(...)
```

```python
# CORRECT
for anomaly in high_anomalies:
    incident_id = await incident_engine.create_from_anomaly(...)
    if not incident_id:
        raise GovernanceError("Failed to create incident")
```

#### Example 2 - Overview Queries

```python
# WRONG
SELECT count(*) FROM limit_breaches
```

```python
# CORRECT
if not await table_exists("limit_breaches"):
    breach_count = 0
else:
    breach_count = await query()
```

**Why:** UI must degrade, not crash.

---

### Minute 7-9: How Violations Sneak Back In

Watch for these red flags during reviews:

* `dispatcher=None`
* `if service:`
* `try/except Exception: log()`
* Returning `None` from governance functions
* "Temporary" bypasses
* Comments like "best effort" or "optional"

If you see one:
- Stop the review
- Ask: *"What invariant does this break?"*

---

### Minute 9-10: Final Checklist (Before You Merge)

Ask yourself:

* Does this code enforce a customer-visible invariant?
* If it fails, does it throw `GovernanceError`?
* Is any dependency optional?
* Is learning strictly downstream?
* Would a customer ever see a lie instead of an error?

If all answers are correct -> ship.
If not -> fix before merge.

---

### Closing Statement

> **Correctness first. Learning later. Silence is a bug.**

That's the entire governance model.
