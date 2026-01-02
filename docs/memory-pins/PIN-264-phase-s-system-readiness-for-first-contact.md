# PIN-264: Phase S — System Readiness for First Contact

**Status:** 📋 ACTIVE
**Created:** 2026-01-01
**Category:** Governance / Pre-Launch
**Milestone:** Phase S

---

## Summary

Pre-incident engineering phase. Build diagnostic capability before users arrive. Four tracks: Error Capture, Replay/Reproduction, Synthetic Traffic, Learning Loop.

---

## Details

# Phase-S: System Readiness for First Contact

**Objective:** Create learning signals before users arrive

> **Replace "observe users" with "observe the system observing itself"**

---

## Current State (Re-baselined 2026-01-01)

| Fact | Status |
|------|--------|
| Architecture | ✅ Correct |
| Governance | ✅ Enforced (L5→L4 CI blocking) |
| CI | ✅ Deterministic |
| Production Traffic | ⚠️ **Zero** |

**Implication:** Cannot rely on user behavior to discover failure modes, bottlenecks, or edge cases.

---

## Goal

When the **first bug / complaint / incident** occurs, you already have:
- ✅ Evidence
- ✅ Timeline
- ✅ Root cause
- ✅ Prevention path

---

## Four Parallel Tracks

### TRACK 1 — Error & Incident Capture (P0)

**Goal:** Every failure leaves a forensic trail

#### 1.1 Unified Error Envelope (Non-negotiable)

Every error must emit:
```
error_id
timestamp
layer (L2/L4/L5)
component
correlation_id
decision_id (if any)
input_hash (not raw input)
error_class
severity
```

No stacktrace dumps as primary signal.

#### 1.2 Correlation IDs Everywhere

One request/workflow traceable across:
- API
- Domain engine
- Worker
- Decision emission

#### 1.3 Error Persistence (Not Just Logs)

- Append-only error store (DB or JSONL)
- Indexed by error_class + component
- Retained across deploys
- Becomes **incident memory**

---

### TRACK 2 — Replay & Reproduction (P0)

**Goal:** Any serious incident can be replayed deterministically

#### 2.1 Decision Snapshotting

For L4 engines:
- Store inputs (hashed or redacted)
- Store outputs (decisions)
- Store version hash of engine

Enables: "Given same inputs, would today's code behave the same?"

#### 2.2 Worker Replay Mode (Offline)

```bash
python replay_decision.py --decision-id <id>
```

- No live infra
- No API
- Pure deterministic replay
- Debug without traffic

---

### TRACK 3 — Synthetic Traffic & Chaos (P1)

**Goal:** Simulate users since they aren't here yet

#### 3.1 Synthetic Scenario Runner

Job that:
- Creates fake workflows
- Pushes through L2 → L4 → L5
- Uses real code paths (not mocks)

Run: on demand, nightly, before releases

#### 3.2 Fault Injection (Minimal)

Deliberately inject:
- Timeouts
- Malformed inputs
- Missing decisions
- Retries

Tests resilience, not correctness.

---

### TRACK 4 — Learning Loop & Prevention (P0)

**Goal:** Every incident → permanent system improvement

#### 4.1 Incident → Lesson → Prevention Pipeline

```
Incident Record
      ↓
Root Cause (human-written)
      ↓
Preventive Control
      ↓
Governance Update (rule / check / playbook)
```

If incident does NOT produce a check, rule, or playbook update → it will happen again.

#### 4.2 Session Playbook Evolution

SESSION_PLAYBOOK must:
- Reference known incident classes
- Include "what to check first"
- Include "what never to do again"

Experience → Institutional memory.

---

## What NOT to Focus On Now

| ❌ Skip | Reason |
|---------|--------|
| Feature polish | Downstream of observability |
| UX iteration | Need users first |
| Scaling infra | Premature |
| Performance tuning | No traffic to optimize |
| Multi-tenant complexity | Single-tenant first |

---

## Phase-S Exit Criteria

Phase ends when:
1. First real user issue occurs
2. You can diagnose it in **<15 minutes**
3. You can **replay** it
4. You can **prevent recurrence**

---

## Next Concrete Step

> ~~Design the Unified Error Envelope + Correlation ID standard~~ **DONE**

Next: Implement Error Persistence (Track 1.3)

---

## Implementation Progress

### Track 1.1 — Unified Error Envelope ✅ COMPLETE (2026-01-01)

**Files Created:**
- `backend/app/infra/__init__.py` — Infrastructure namespace
- `backend/app/infra/error_envelope.py` — Error envelope schema
- `backend/app/infra/correlation.py` — Correlation ID utilities

**Namespace Separation:**
- `infra.*` namespace for Phase-S infrastructure systems
- Distinct from `product.*` (customer-facing code)
- All files are L6 (Platform Substrate)

**ErrorEnvelope Schema:**
```python
@dataclass(frozen=True)
class ErrorEnvelope:
    error_id: str              # Unique: err_<12-char-hex>
    timestamp: datetime        # UTC
    layer: str                 # L2/L3/L4/L5/L6
    component: str             # Module path
    error_class: ErrorClass    # Classification enum
    severity: ErrorSeverity    # DEBUG/INFO/WARNING/ERROR/CRITICAL
    message: str               # Human-readable

    # Correlation
    correlation_id: Optional[str]
    decision_id: Optional[str]
    run_id: Optional[str]
    agent_id: Optional[str]
    tenant_id: Optional[str]

    # Security
    input_hash: Optional[str]  # SHA256[:16], never raw input

    # Exception (sanitized)
    exception_type: Optional[str]
    exception_chain: Optional[List[str]]

    # Arbitrary context
    context: Dict[str, Any]
```

**ErrorClass Taxonomy:**
- `infra.*` — Infrastructure errors (network, database, timeout)
- `domain.*` — Business logic errors (validation, authorization, budget)
- `system.*` — Internal errors (configuration, recovery, corruption)

**Usage Example:**
```python
from app.infra import ErrorEnvelope, ErrorClass, ErrorSeverity

envelope = ErrorEnvelope.create(
    layer="L4",
    component="app.services.budget_engine",
    error_class=ErrorClass.DOMAIN_BUDGET_EXCEEDED,
    severity=ErrorSeverity.ERROR,
    message="Budget exhausted for run",
    correlation_id=request_id,
    run_id=run.id,
)
```

### Track 1.2 — Correlation IDs ✅ COMPLETE (2026-01-01)

**CorrelationContext:**
```python
@dataclass(frozen=True)
class CorrelationContext:
    correlation_id: str        # Root trace ID (same for entire request)
    span_id: str              # Current operation span
    parent_span_id: Optional[str]
    component: Optional[str]
    started_at: datetime
```

**Context Manager Pattern:**
```python
from app.infra import correlation_scope, child_span

# Establish correlation scope
with correlation_scope(component="api.users") as ctx:
    print(f"Correlation ID: {ctx.correlation_id}")

    # Create child spans for sub-operations
    with child_span("database") as db_span:
        # db_span.parent_span_id == ctx.span_id
        do_database_work()
```

**Thread-Safe:** Uses `contextvars` for async-safe propagation

### Track 1.3 — Error Persistence ✅ COMPLETE (2026-01-01)

**Files Created:**
- `backend/app/infra/error_store.py` — Append-only persistence interface
- `backend/alembic/versions/067_phase_s_error_persistence.py` — Migration

**Table: `infra_error_events`**
```sql
error_id (PK)        -- Unique identifier
timestamp            -- When error occurred
layer                -- L2/L3/L4/L5/L6
component            -- Module path
error_class          -- infra.*/domain.*/system.*
severity             -- Severity level
message              -- Human-readable
correlation_id       -- Request trace (nullable)
decision_id          -- Related decision (nullable)
run_id               -- Related run (nullable)
input_hash           -- SHA256[:16] of input
exception_type       -- Exception class name
exception_chain      -- Cause chain (JSONB)
context              -- Arbitrary context (JSONB)
envelope_version     -- Schema version
created_at           -- For retention cleanup
```

**Indexes:**
- `correlation_id` — Request tracing
- `component + timestamp` — Incident aggregation
- `error_class + timestamp` — Pattern detection
- `created_at` — Retention cleanup
- `run_id` — Run correlation

**Append-Only Enforcement:**
- Database trigger prevents UPDATE operations
- DELETE only allowed via `cleanup_old_errors()` (retention)
- ON CONFLICT DO NOTHING (first write wins)

**Query Functions (for L4 aggregation):**
- `get_errors_by_correlation()` — Trace requests
- `get_errors_by_component()` — Component health
- `get_errors_by_class()` — Pattern detection
- `get_error_counts_by_*()` — Trend metrics
- `get_error_timeline()` — Time-series analysis

**Retention:**
- `cleanup_old_errors(retention_days=90)` — L7 scheduled cleanup

### BLCA Verification

```
Layer Validator (PIN-240)
Files scanned: 608
Violations found: 0
Layer architecture is clean.
```

### Semantic Lockdown ✅ COMPLETE (2026-01-01)

**Risk 1: Error Classification Drift — LOCKED**

| Layer | Allowed `error_class` | Forbidden |
|-------|----------------------|-----------|
| L2 (API) | `infra.*`, `system.*` | `domain.*` |
| L3 (Adapter) | `infra.*`, `system.*` | `domain.*` |
| L4 (Domain) | `domain.*`, `system.*` | `infra.*` |
| L5 (Worker) | `infra.*`, `system.*` | `domain.*` |
| L6 (Platform) | `infra.*`, `system.*` | `domain.*` |

**Risk 2: Product API Leak — LOCKED**

ErrorEnvelope is **INFRASTRUCTURE-ONLY**:
- ❌ NEVER return from L2 APIs
- ❌ NEVER render in UI
- ❌ NEVER use as product contract
- ❌ NEVER expose to customers

**Governance Documents Updated:**
- `backend/app/infra/error_envelope.py` — Constraints in docstring
- `docs/governance/SEMANTIC_ARTIFACTS.md` — Emission rules + forbidden patterns
- `docs/playbooks/SESSION_PLAYBOOK.yaml` — Section 16 (Phase-S Infrastructure Rule)

### L4 Ops Domain Models ✅ COMPLETE (2026-01-01)

**File Created:** `backend/app/services/ops_domain_models.py`

**Publication Pipeline (Locked):**
```
L6  Infra Truth (ErrorEnvelope, DecisionSnapshot)
 ↓   (never exposed)
L4  Domain Interpretation (OpsIncident, OpsHealthSignal)
 ↓
L3  View Adapters (FounderOpsAdapter, PreflightOpsAdapter)
 ↓
L2  Ops APIs (read-only, aggregated)
 ↓
L1  Consoles (fops, preflight-fops)
```

**Core Models (6 types):**

| Model | Purpose | Operator Question |
|-------|---------|-------------------|
| `OpsIncident` | Aggregated failure patterns | "Why did this fail?" |
| `OpsHealthSignal` | Current component health | "Is the system OK now?" |
| `OpsRiskFinding` | Preflight risk findings | "What breaks if users arrive?" |
| `OpsTrendMetric` | Time-series trends | "Is this getting better or worse?" |
| `OpsDecisionOutcome` | Decision summaries | "What decisions did the system make?" |
| `OpsCorrelatedEvent` | Cross-component correlation | "What happened together?" |

**Ops-Level Enums (distinct from infra):**
- `OpsSeverity`: INFO → ATTENTION → ACTION → URGENT
- `OpsIncidentCategory`: execution_failure, budget_exhaustion, policy_violation...
- `OpsHealthStatus`: healthy, degraded, unhealthy, unknown
- `OpsRiskLevel`: low, medium, high, critical

**Key Constraint Verified:**
- ✅ No L6 infra imports in L4 models
- ✅ Models are pure dataclasses (no DB dependency)
- ✅ BLCA: CLEAN (606 files, 0 violations)

### L4 Aggregation Services 🔄 IN PROGRESS (2026-01-01)

**File Created:** `backend/app/services/ops_incident_service.py`

**Design Principles:**
- INPUT: Time window, severity threshold, optional component scope
- OUTPUT: `List[OpsIncident]` (domain models only)
- NO: UI shaping, pagination, sorting for display, auth, filtering by role

**Hard Rules:**
1. Never return infra artifacts (ErrorEnvelope, raw DB rows)
2. Never know about consoles (fops, preflight)
3. Never paginate (that's L3's job)
4. Must be unit-testable with fake infra data

**OpsIncidentService (FIRST SERVICE):**

```python
class OpsIncidentService:
    def get_active_incidents(
        self,
        since: datetime,
        until: Optional[datetime] = None,
        component: Optional[str] = None,
        min_severity: Optional[OpsSeverity] = None,
    ) -> List[OpsIncident]:
        # Query infra → aggregate → return domain models
```

**Methods:**
- `get_active_incidents()`: Primary aggregation method
- `get_incident_by_component()`: Single component incidents
- `get_incident_summary()`: Summary counts by severity

**Key Features:**
- Protocol-based dependency injection (`ErrorStoreProtocol`)
- SQL aggregation in `infra_error_events` table
- Infra → Domain translation in `_aggregate_to_incidents()`
- Error class → incident category mapping
- Occurrence count → operator severity computation

**BLCA Verification:**
- ✅ 609 files, 0 violations
- ✅ No L2 API imports in L4 service
- ✅ No FastAPI imports

**Governance Update:**
- `SESSION_PLAYBOOK.yaml` Section 16: Added `l4_aggregation_rules`

### L3 FounderOpsAdapter ✅ COMPLETE (2026-01-01)

**File Created:** `backend/app/adapters/founder_ops_adapter.py`

**Purpose:** Translate OpsIncident domain models to Founder-facing views.

**View DTOs:**
- `FounderIncidentSummaryView`: Single incident for display
- `FounderIncidentsSummaryResponse`: Summary response for L2

**Hard Rules Verified:**
- ✅ NO infra queries (L4's job)
- ✅ NO aggregation (L4's job)
- ✅ NO permissions logic (L2's job)
- ✅ NO pagination (L2's job)
- ✅ ONLY field selection, redaction, light renaming

### L2 GET /ops/incidents/infra-summary ✅ COMPLETE (2026-01-01)

**Endpoint Added:** `backend/app/api/ops.py`

```
GET /ops/incidents/infra-summary?hours=24
```

**Returns:**
```json
{
  "total_incidents": 5,
  "by_severity": {"urgent": 1, "action": 2, "attention": 1, "info": 1},
  "recent_incidents": [...],
  "window_start": "2026-01-01T00:00:00Z",
  "window_end": "2026-01-01T12:00:00Z"
}
```

**Auth:** Founder-only (verify_fops_token)

**BLCA Verification:** ✅ 612 files, 0 violations

---

## 🛑 PHASE-S FROZEN (2026-01-01)

**Status:** One vertical slice complete. Phase-S work STOPPED.

**Completed Vertical Slice:**
```
L6 infra_error_events     ✅
 → L4 OpsIncidentService  ✅
 → L3 FounderOpsAdapter   ✅
 → L2 GET /incidents/infra-summary ✅
```

**NOT Implemented (Intentionally Deferred):**
- ❌ OpsHealthService, OpsRiskService, OpsTrendService
- ❌ PreflightOpsAdapter
- ❌ L1 Console Wiring
- ❌ Track 2 (Decision Snapshotting, Replay)
- ❌ Track 3 (Synthetic Traffic)
- ❌ Track 4 (Learning Loop)

**Reason:** Return to CI hygiene work (integration hanging tests, 131 unit failures).

---

## Next Work (Pending)

### Phase-2.1: Integration Test Hanging ✅ COMPLETE (2026-01-01)

**Status:** ✅ COMPLETE + SELF-DEFENDING UPGRADE

**Root Cause Identified:**
The circuit breaker tests (`test_circuit_breaker.py`) were hanging due to
`SELECT ... FOR UPDATE` locks being held across multiple database connections.
The issue was that `session.commit()` released connections to the pool, and
subsequent operations acquired different connections. When `_get_or_create_state()`
was called twice (in `disable_v2()` and `_trip()`), the second call blocked on
the first connection's `FOR UPDATE` lock.

**Initial Fix Applied (Symptom):**
Added `use_single_connection_pool` fixture in `test_circuit_breaker.py` that
replaces the engine with a `StaticPool` (single connection).

**Self-Defending Upgrade (Prevention):**
Upgraded from "memory-assisted" to "self-defending" architecture:

| Component | Purpose | Location |
|-----------|---------|----------|
| `single_connection_transaction()` | Blessed path for row locks | `app/infra/transaction.py` |
| `SingleConnectionTxn` | Type-safe transaction context | `app/infra/transaction.py` |
| `check_forbidden_patterns.py` | CI ban on raw `FOR UPDATE` | `scripts/ci/check_forbidden_patterns.py` |
| SESSION_PLAYBOOK Section 17 | Code-first governance | `docs/playbooks/SESSION_PLAYBOOK.yaml` |

**Self-Defense Guarantees:**

1. **Path-of-least-resistance is correct**
   - `single_connection_transaction()` is easier than raw sessions
   - `txn.lock_row()` is easier than `with_for_update()`

2. **Illegal states are unrepresentable**
   - `SingleConnectionTxn` type makes requirements visible
   - Functions requiring locks MUST accept this type

3. **Violations fail early and locally**
   - CI fails immediately if forbidden patterns detected
   - 4 current violations flagged (to be refactored)

4. **New feature design is constrained**
   - Primitives answer "how should I do this?"
   - Documentation points to code, not rules

**CI Check Output (Current Violations):**
```
FORBIDDEN PATTERNS DETECTED: 4
- app/costsim/alert_worker.py:122
- app/costsim/circuit_breaker_async.py:147
- app/costsim/circuit_breaker_async.py:248
- app/costsim/circuit_breaker.py:213
```

**Results:**
- ✅ 21 circuit breaker tests pass (previously hung)
- ✅ 112 total integration tests complete in ~26s (87 passed, 9 failed, 16 skipped)
- ✅ No more hanging tests
- ✅ Self-defending primitives created
- ✅ CI enforcement active
- ⚠️ 4 files need refactoring to use new primitives (deferred)
- ⚠️ 9 RBAC-related failures (403 Forbidden) — functional issues for Phase-3

**Rules Followed:**
- ✅ No domain logic edits (primitives added, not refactored)
- ✅ Test harness fixed
- ✅ Infrastructure primitives added (L6)
- ✅ CI enforcement added
- ✅ SESSION_PLAYBOOK updated

### Phase-3: 131 Unit Test Failures (NEXT)

**Status:** 📋 PENDING

**Focus:**
- Classify failures by domain slice
- Fix one slice per commit
- No mass greenwashing

---

## Progress Tracker

| Track | Item | Status |
|-------|------|--------|
| 1.1 | Error Envelope Schema | ✅ COMPLETE |
| 1.2 | Correlation IDs | ✅ COMPLETE |
| 1.3 | Error Persistence | ✅ COMPLETE |
| — | Semantic Lockdown | ✅ COMPLETE |
| — | L4 Ops Domain Models | ✅ COMPLETE |
| — | L4 Aggregation Services | ✅ COMPLETE (OpsIncidentService only) |
| — | L3 View Adapters | ✅ COMPLETE (FounderOpsAdapter only) |
| — | L2 Ops APIs | ✅ COMPLETE (infra-summary only) |
| — | L1 Console Wiring | 🛑 FROZEN |
| 2.1 | Decision Snapshotting | 📋 PENDING |
| 2.2 | Replay Mode | 📋 PENDING |
| 3.1 | Synthetic Scenario Runner | 📋 PENDING |
| 4.1 | Incident → Lesson Pipeline | 📋 PENDING |
| — | Phase-2.1: Integration Test Hanging | ✅ COMPLETE |
| — | Phase-3: Unit Test Failures | 📋 PENDING |

---

## Reference

- PIN-263: Phase R (L5→L4 Structural Repair)
- PIN-240: Seven-Layer Model
- Session: Phase G → Phase S transition

---


---

## Phase-2.2 Update

### Update (2026-01-01)

## 2026-01-01: Phase-2.2 Self-Defending Transactions with Intent

### Philosophy Upgrade
Upgraded from "blocked" to "guided by construction". The key insight:
- **Before (Phase-2.1)**: Block mistakes with CI after they happen
- **After (Phase-2.2)**: Guide engineers BEFORE code is written via intent declaration

The real root cause is NOT "FOR UPDATE". It is:
> "Transactional intent is not explicit in feature design."

### TransactionIntent System
Added to `app/infra/transaction.py`:

| Intent | Description | Required Parameter |
|--------|-------------|-------------------|
| READ_ONLY | Plain session, no locks | Session |
| ATOMIC_WRITE | Transaction context, no FOR UPDATE | Session |
| LOCKED_MUTATION | single_connection_transaction() REQUIRED | SingleConnectionTxn |

### Key Components
1. **TransactionIntent enum** — Declares intent before implementation
2. **@transactional decorator** — Validates signature at decoration time (fail-fast)
3. **IntentViolationError** — Design-time exception (don't catch, fix design)
4. **_INTENT_REGISTRY** — Global registry for CI validation

### CI Enforcement
- `scripts/ci/check_forbidden_patterns.py` — Blocks raw FOR UPDATE syntax
- `scripts/ci/check_intent_consistency.py` — Validates intent/primitive alignment

### Golden Examples
Created `app/infra/transaction_examples.py` with reference implementations for:
- READ_ONLY queries
- ATOMIC_WRITE operations
- LOCKED_MUTATION with proper txn.lock_row() usage
- Caller patterns demonstrating correct transaction context creation

### SESSION_PLAYBOOK v2.27
Section 17 updated with:
- "MIRROR, NOT AUTHORITY" directive (playbook explains, code enforces)
- Intent declaration documentation
- Evolution rule: every incident → new primitive, stricter intent, or new CI invariant

### Files Changed
- `app/infra/transaction.py` — Core intent system
- `app/infra/__init__.py` — Exports
- `scripts/ci/check_intent_consistency.py` — New CI script
- `app/infra/transaction_examples.py` — Golden examples
- `docs/playbooks/SESSION_PLAYBOOK.yaml` — v2.27

### Deferred Work
- 3 circuit breaker files still have forbidden patterns (flagged, not yet migrated)
- 116 test failures remaining (Phase-3)

## Related PINs

- [PIN-263](PIN-263-.md)
