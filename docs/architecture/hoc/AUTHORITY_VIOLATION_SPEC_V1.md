# Authority Violation Specification v1.0

**Date:** 2026-01-25
**Status:** DRAFT
**Reference:** HOC Layer Topology V1, PIN-470

---

## Governing Principle

> **Authorities are not services. Authorities are constraints on choice.**

This specification defines the architectural authorities that govern backend behavior and the violations that occur when code makes choices outside its jurisdiction.

---

## I. First-Principles Foundation

Any backend that intends to be **long-lived, auditable, and evolvable** must satisfy these invariants:

| Invariant | Meaning |
|-----------|---------|
| **Single Authority per Concern** | Time, Transactions, Orchestration, State transitions each have ONE source of truth |
| **Behavioral Isolation** | Domains may DECIDE, but must not COORDINATE |
| **Explicit Side-Effects** | Writes, transitions, cross-domain calls must be visible and interceptable |
| **Deterministic Replay** | A run, incident, or policy decision must be replayable with identical outcomes |

---

## II. The Four Authorities

### Authority 1: TIME

**Location:** `hoc/cus/general/L5_utils/time.py`

**What It Governs:**
- All timestamps entering the system
- Clock reads for business logic
- Temporal comparisons

**Why It Exists:**
- Time is **global state**, not a utility
- Uncontrolled time breaks replayability
- Uncontrolled time breaks auditability
- Uncontrolled time breaks cross-domain correlation

**Contract:**
```python
from app.hoc.cus.general.L5_utils.time import utc_now

# All timestamps MUST enter via:
timestamp = utc_now()

# Or via runtime context:
timestamp = context.current_time
```

---

### Authority 2: TRANSACTION

**Location:** `hoc/cus/general/L4_runtime/drivers/transaction_coordinator.py`

**What It Governs:**
- **Consistency scope**, not just domain count
- Atomic multi-model writes
- Cross-domain persistence
- Failure recovery

**Why It Exists:**
- A transaction is "a guarantee of system consistency"
- Partial persistence corrupts meaning
- Failure recovery requires central coordination

**Contract:**
```python
from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import (
    RunCompletionTransaction,
    get_transaction_coordinator,
)

# Multi-model writes MUST flow through coordinator
async with get_transaction_coordinator() as coordinator:
    await coordinator.execute(run_id, context)
```

**Critical Distinction:**
- Same-domain writes MAY require transaction authority if they represent a logical invariant
- Cross-domain writes ALWAYS require transaction authority

---

### Authority 3: ORCHESTRATION

**Location:** `hoc/cus/general/L4_runtime/engines/governance_orchestrator.py`

**What It Governs:**
- Execution ordering
- Retry semantics
- Compensation logic
- Cross-service coordination

**Why It Exists:**
- Two orchestrators = split authority = undefined behavior under failure
- There must be exactly ONE place where cross-domain execution order is decided

**Contract:**
```python
from app.hoc.cus.general.L4_runtime.engines.governance_orchestrator import (
    GovernanceOrchestrator,
)
from app.hoc.cus.general.L4_runtime.facades.run_governance_facade import (
    get_run_governance_facade,
)

# Coordination MUST flow through orchestrator
facade = get_run_governance_facade()
await facade.complete_run(run_id, context)
```

**Hard Rule:**
> **If it handles failure, it is orchestration. No exceptions.**

---

### Authority 4: STATE

**Location:** `hoc/cus/general/L5_workflow/contracts/engines/contract_engine.py`

**What It Governs:**
- State machine transitions
- Invariant enforcement
- Terminal state protection

**Why It Exists:**
- State transitions must have single source of truth
- Invariants must be mechanically enforced
- MAY_NOT verdicts must be un-overridable

**Contract:**
```python
from app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine import (
    ContractStateMachine,
    ContractService,
)

# State transitions MUST flow through state machine
state_machine = ContractStateMachine()
if state_machine.can_transition(current, target):
    state_machine.transition(entity, target)
```

**Critical Distinction:**

| Activity | Authority Required? |
|----------|---------------------|
| STATE_DEFINITION (enums, tables, graphs) | NO - Pure description allowed |
| STATE_ENFORCEMENT (validation, execution, side-effects) | YES - Authority-bound |

---

## III. Violation Categories

### Violation 1: TIME_LEAK

**Definition:** Code reads time without importing time authority.

**Detection:**
```python
# VIOLATION: Direct datetime calls
datetime.now()
datetime.utcnow()
datetime.today()
time.time()
```

**Severity:** HIGH

**Why Dangerous:**
- Breaks replayability
- Breaks auditability
- Introduces non-determinism

**Required Harness:**
```yaml
type: TIME_AUTHORITY
import: "from app.hoc.cus.general.L5_utils.time import utc_now"
```

---

### Violation 2: STATE_MACHINE_DUPLICATION

**Definition:** Code enforces state transitions without importing state authority.

**Detection Matrix:**

| Activity | Severity |
|----------|----------|
| Defines states only (Enum) | NONE - Allowed |
| Validates transitions (`can_transition`, `is_valid`) | HIGH |
| Executes transitions (`transition_to`, `set_status`) | CRITICAL |

**Why Dangerous:**
- Split authority = undefined behavior under failure
- State corruption on partial execution

**Required Harness:**
```yaml
type: STATE_AUTHORITY
import: "from app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine import ContractStateMachine"
```

---

### Violation 3: TRANSACTION_BYPASS

**Definition:** Code writes to multiple models without transaction authority.

**Detection:**
- Multiple `session.add()` with different model types
- Multiple `session.commit()` in single function
- Cross-domain model writes

**Severity Matrix:**

| Condition | Severity |
|-----------|----------|
| Same-domain, independent models | MEDIUM |
| Same-domain, logical invariant (e.g., "create X with Y") | HIGH |
| Cross-domain writes | CRITICAL |

**Semantic Escalation Triggers:**
- Function name contains: `create_with`, `finalize`, `commit`, `complete`
- Docstring implies atomicity: "creates X and Y together"

**Why Dangerous:**
- Violates atomicity
- Violates observability
- Breaks failure recovery

**Required Harness:**
```yaml
type: TRANSACTION_COORDINATOR
import: "from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import RunCompletionTransaction"
```

---

### Violation 4: ORCHESTRATION_LEAK

**Definition:** Code coordinates execution or handles failures without orchestration authority.

**Detection Rules:**

| Condition | Result |
|-----------|--------|
| Calls 2+ services AND has try/except | ORCHESTRATION |
| Calls 2+ services AND has retry/rollback logic | ORCHESTRATION |
| Calls transaction + time + service (any combination) | ORCHESTRATION |
| Handles partial failures | ORCHESTRATION |

**Severity:** CRITICAL (always)

**Why Dangerous:**
- Execution ordering must have single authority
- Compensation logic must be centralized
- Split orchestration = undefined failure modes

**Required Harness:**
```yaml
type: ORCHESTRATION_AUTHORITY
import: "from app.hoc.cus.general.L4_runtime.engines.governance_orchestrator import GovernanceOrchestrator"
# OR
import: "from app.hoc.cus.general.L4_runtime.facades.run_governance_facade import get_run_governance_facade"
```

---

### Violation 5: AUTHORITY_LEAK

**Definition:** Code makes governance choices that should be made by runtime context.

**Detection - Forbidden Patterns:**

| Pattern | Why Forbidden |
|---------|---------------|
| `uuid.uuid4()` for causal IDs | Breaks determinism |
| Execution order decisions | Orchestration concern |
| Retry with delay (`sleep()` in loop) | Orchestration concern |
| Backoff calculation | Orchestration concern |

**Detection - Allowed Patterns (NOT violations):**

| Pattern | Why Allowed |
|---------|-------------|
| Sorting for presentation | No causal effect |
| UUID parsing (not generation) | Reading, not choosing |
| Deterministic hashing | Reproducible |

**Key Test:**
> Does the code **choose** or **derive**?
> - Choose = VIOLATION
> - Derive = ALLOWED

**Severity:** HIGH

**Required Harness:**
```yaml
type: CONTEXT_AUTHORITY
action: "IDs must be generated by runtime context or transaction scope"
note: "ID authority is contextual, not global"
```

---

### Violation 6: DECISION_VS_EXECUTION

**Definition:** Domain code that executes (coordinates) instead of decides.

**The Key Question:**
> "Is this file deciding WHAT to do, or deciding WHEN/HOW MANY things to do?"

**Decision (OK in domain):**
- `if condition: return X else return Y`
- Validation logic
- Business rules
- Policy evaluation

**Execution (NOT OK in domain):**
- Calling multiple services in sequence
- Handling partial failures
- Coordinating retries
- Ordering side-effects

**Severity:** MEDIUM

**Enforcement:**
- Advisory unless combined with another violation
- Do NOT fail CI on this alone
- Use for code review guidance

---

## IV. Confidence Levels

Every finding MUST include confidence:

| Level | Meaning | Action |
|-------|---------|--------|
| **HIGH** | AST analysis confirms violation pattern | Enforce |
| **MEDIUM** | Pattern detected but context unclear | Review |
| **LOW** | Heuristic match, may be false positive | Investigate |

---

## V. CI Enforcement Phases

### Phase 1 (Immediate)

| Severity | Action |
|----------|--------|
| CRITICAL | FAIL |
| HIGH | WARN |
| MEDIUM | LOG |

### Phase 2 (After Cleanup)

| Severity | Action |
|----------|--------|
| CRITICAL | FAIL |
| HIGH | FAIL |
| MEDIUM | WARN |

### Phase 3 (Mature)

| Severity | Action |
|----------|--------|
| CRITICAL | FAIL |
| HIGH | FAIL |
| MEDIUM | WARN |
| LOW | LOG |

---

## VI. Domain Compliance Status

| Domain | Expected Status | Reason |
|--------|-----------------|--------|
| **general** | PROVIDER | Provides authorities |
| **activity** | CLEAN | Read-only, derived views |
| **logs** | CLEAN | Read-only, archival |
| **overview** | CLEAN | Read-only, aggregation |
| **api_keys** | CLEAN | Simple CRUD |
| **policies** | VIOLATIONS | Duplicates orchestrator, coordinator |
| **incidents** | VIOLATIONS | Time leaks, transaction bypasses |
| **analytics** | VIOLATIONS | Cross-domain writes |
| **account** | VIOLATIONS | Lifecycle patterns |
| **integrations** | VIOLATIONS | Time leaks |

**Note:** Domains being "clean" is a **positive signal** — they are architecturally correct.

---

## VII. Decision Tables

### When Is Transaction Authority Required?

| Writes To | Same Domain | Cross Domain |
|-----------|-------------|--------------|
| 1 model | NO | N/A |
| 2+ models, independent | MEDIUM | CRITICAL |
| 2+ models, logical invariant | HIGH | CRITICAL |

### When Is Orchestration Authority Required?

| Code Pattern | Required? |
|--------------|-----------|
| Calls 1 service | NO |
| Calls 2+ services, no error handling | NO |
| Calls 2+ services, has try/except | YES |
| Calls 2+ services, has retry/rollback | YES |
| Calls transaction + time + service | YES |
| Handles partial failures | YES |

### When Is State Authority Required?

| Activity | Required? |
|----------|-----------|
| Defines Enum with states | NO |
| Defines transition table | NO |
| Validates if transition allowed | YES |
| Executes transition | YES |
| Triggers side-effect on transition | YES |

---

## VIII. Glossary

| Term | Definition |
|------|------------|
| **Authority** | A constraint on choice, not a service |
| **Violation** | Code making choices outside its jurisdiction |
| **Harness** | The correct authority import that resolves a violation |
| **Orchestration** | Deciding WHEN and HOW MANY things to do |
| **Decision** | Deciding WHAT to do |
| **Execution** | Coordinating the doing |
| **Consistency Scope** | The boundary within which atomicity is guaranteed |

---

## IX. References

- **HOC_LAYER_TOPOLOGY_V1.md** — Layer architecture
- **DRIVER_ENGINE_CONTRACT.md** — L5/L6 boundary rules
- **GENERAL_DOMAIN_WIRING_PHASE1.md** — Gap analysis
- **GENERAL_DOMAIN_WIRING_PHASE2.md** — Function catalog
- **PIN-470** — HOC Layer Inventory

---

## X. Change Log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-01-25 | Initial specification |

---

**Specification Author:** Claude (First-Principles Analysis)
**Review Status:** PENDING HUMAN RATIFICATION
