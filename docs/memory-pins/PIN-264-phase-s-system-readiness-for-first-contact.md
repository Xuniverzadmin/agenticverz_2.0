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

### Track 1.3 — Error Persistence 📋 PENDING

Next implementation:
- Append-only error store (DB table or JSONL)
- Indexed by error_class + component
- Retained across deploys

### BLCA Verification

```
Layer Validator (PIN-240)
Files scanned: 605
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

---

## Progress Tracker

| Track | Item | Status |
|-------|------|--------|
| 1.1 | Error Envelope Schema | ✅ COMPLETE |
| 1.2 | Correlation IDs | ✅ COMPLETE |
| 1.3 | Error Persistence | 📋 PENDING |
| — | Semantic Lockdown | ✅ COMPLETE |
| — | L4 Ops Domain Models | ✅ COMPLETE |
| — | L3 View Adapters | 📋 PENDING |
| — | L2 Ops APIs | 📋 PENDING |
| — | L1 Console Wiring | 📋 PENDING |
| 2.1 | Decision Snapshotting | 📋 PENDING |
| 2.2 | Replay Mode | 📋 PENDING |
| 3.1 | Synthetic Scenario Runner | 📋 PENDING |
| 4.1 | Incident → Lesson Pipeline | 📋 PENDING |

---

## Reference

- PIN-263: Phase R (L5→L4 Structural Repair)
- PIN-240: Seven-Layer Model
- Session: Phase G → Phase S transition

---

## Related PINs

- [PIN-263](PIN-263-.md)
