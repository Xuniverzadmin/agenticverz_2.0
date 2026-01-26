# L4 / L5 Contracts — v1.0

**Date:** 2026-01-25
**Status:** DRAFT
**Prerequisites:**
- AUTHORITY_VIOLATION_SPEC_V1.md
- RUNTIME_CONTEXT_MODEL.md
**Reference:** HOC Layer Topology V1, PIN-470

---

## Governing Principle

> **Contracts do not provide power. Contracts LIMIT power already provided via context.**

Each layer's contract **removes capabilities**, never adds them.

---

## I. Contract Taxonomy

| Layer | Contract Type | Purpose |
|-------|--------------|---------|
| **L4** | Coordinator / Orchestrator Contracts | Create & own contexts |
| **L5** | Domain Engine Contracts | Decide business logic |
| **L6** | Driver Contracts | Perform persistence / IO |

---

## II. Enforcement Model

**Primary:** Type system (Protocols)
**Secondary:** Analyzer (for edge cases)

**Why Type System:**
- IDE catches violations immediately
- mypy/pyright enforce at CI
- Self-documenting code
- Impossible to accidentally violate if types are correct
- Zero heuristics, zero debates

---

## III. L4 Contracts (Authority Owners)

### Contract 1: RuntimeCoordinatorContract

**Purpose:** Owns creation and finalization of runtime contexts.

**Location:** `hoc/cus/general/L4_runtime/contracts/coordinator.py`

```python
from typing import Protocol, Callable, TypeVar, Awaitable
from app.hoc.cus.general.L5_utils.time import TimeContext
from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import TransactionContext
from app.hoc.cus.general.L4_runtime.engines.governance_orchestrator import OrchestrationContext

T = TypeVar('T')


class RuntimeCoordinatorContract(Protocol):
    """
    L4 Coordinator Contract.

    OWNS:
    - Creation of TransactionContext
    - Creation of OrchestrationContext
    - Commit / Rollback authority

    MUST NOT:
    - Contain domain logic
    - Perform persistence directly
    - Make business decisions
    """

    async def run(
        self,
        *,
        time_ctx: TimeContext,
        fn: Callable[[TransactionContext, OrchestrationContext], Awaitable[T]]
    ) -> T:
        """
        Execute a coordinated operation.

        Creates transaction and orchestration contexts,
        executes fn, handles commit/rollback.
        """
        ...

    async def commit(self, ctx: TransactionContext) -> None:
        """
        Commit the transaction.
        ONLY L4 may call this.
        """
        ...

    async def rollback(self, ctx: TransactionContext) -> None:
        """
        Rollback the transaction.
        ONLY L4 may call this.
        """
        ...
```

**Rules:**

| Operation | Permitted | Forbidden |
|-----------|-----------|-----------|
| Create `TransactionContext` | YES | — |
| Create `OrchestrationContext` | YES | — |
| Call `commit()` / `rollback()` | YES | — |
| Contain domain logic | — | YES |
| Perform persistence directly | — | YES |
| Call L6 drivers directly | — | YES |

**Enforcement Signal:**
- Any `commit()` / `rollback()` outside L4 = TRANSACTION_BYPASS

---

### Contract 2: OrchestratorContract

**Purpose:** Define execution ordering and failure semantics.

**Location:** `hoc/cus/general/L4_runtime/contracts/orchestrator.py`

```python
from typing import Protocol, List, Callable, Awaitable, Optional
from dataclasses import dataclass


@dataclass
class StepResult:
    """Result of an orchestration step."""
    success: bool
    data: Optional[any] = None
    error: Optional[Exception] = None


class OrchestratorContract(Protocol):
    """
    L4 Orchestrator Contract.

    OWNS:
    - Execution ordering
    - Retry semantics
    - Compensation logic
    - Partial failure handling

    MUST NOT:
    - Write to DB
    - Inspect domain state directly
    - Contain business rules
    """

    async def execute(
        self,
        *,
        ctx: OrchestrationContext,
        steps: List[Callable[[], Awaitable[StepResult]]]
    ) -> OrchestrationResult:
        """
        Execute steps in order with failure handling.
        """
        ...

    async def retry(
        self,
        *,
        ctx: OrchestrationContext,
        step: Callable[[], Awaitable[StepResult]],
        policy: RetryPolicy
    ) -> StepResult:
        """
        Retry a step according to policy.
        ONLY L4 may implement retry logic.
        """
        ...

    async def compensate(
        self,
        *,
        ctx: OrchestrationContext
    ) -> None:
        """
        Execute compensation in reverse order.
        ONLY L4 may trigger compensation.
        """
        ...
```

**Rules:**

| Operation | Permitted | Forbidden |
|-----------|-----------|-----------|
| Retry | YES | — |
| Compensate | YES | — |
| Reorder execution | YES | — |
| Handle partial failure | YES | — |
| Write to DB | — | YES |
| Inspect domain state | — | YES |
| Contain business rules | — | YES |

**Enforcement Signal:**
- Any retry/compensation logic outside L4 = ORCHESTRATION_LEAK

---

## IV. L5 Contracts (Domain Engines)

### Contract 3: DomainEngineContract

**Purpose:** Encapsulate pure business decisions.

**Location:** `hoc/cus/general/L5_engines/contracts/engine.py`

```python
from typing import Protocol, TypeVar, Generic
from app.hoc.cus.general.L5_utils.time import TimeContext

Input = TypeVar('Input')
Decision = TypeVar('Decision')


class DomainEngineContract(Protocol, Generic[Input, Decision]):
    """
    L5 Domain Engine Contract.

    OWNS:
    - Business decisions
    - Validation logic
    - Domain rules

    MAY:
    - Read time via ctx.time.now()
    - Perform validation
    - Return decisions

    MUST NOT:
    - Call multiple services
    - Handle retries / exceptions for coordination
    - Perform persistence
    - Create contexts
    """

    def decide(
        self,
        *,
        ctx: TimeContext,
        input: Input
    ) -> Decision:
        """
        Make a business decision.

        This is PURE COMPUTATION.
        No side effects. No persistence. No coordination.
        """
        ...
```

**Rules:**

| Operation | Permitted | Forbidden |
|-----------|-----------|-----------|
| Read `ctx.time.now()` | YES | — |
| Perform validation | YES | — |
| Return decisions | YES | — |
| Call multiple services | — | YES |
| Handle retries | — | YES |
| Perform persistence | — | YES |
| Create contexts | — | YES |
| Call `session.add()` | — | YES |

**Enforcement Signal:**
- `try/except` + service calls = ORCHESTRATION_LEAK
- `session.add()` in L5 = LAYER_VIOLATION

---

### Contract 4: TransactionalEngineContract

**Purpose:** Domain engine that participates in transactions (but doesn't own them).

**Location:** `hoc/cus/general/L5_engines/contracts/transactional.py`

```python
from typing import Protocol, TypeVar, Generic
from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import TransactionContext
from app.hoc.cus.general.L5_utils.time import TimeContext

Input = TypeVar('Input')
Output = TypeVar('Output')


class TransactionalEngineContract(Protocol, Generic[Input, Output]):
    """
    L5 Transactional Engine Contract.

    Participates in transactions but does NOT own them.

    MAY:
    - Read time via ctx.time.now()
    - Call ctx.transaction.add() to queue writes
    - Register compensation

    MUST NOT:
    - Call ctx.transaction.commit()
    - Call ctx.transaction.rollback()
    - Create TransactionContext
    """

    async def process(
        self,
        *,
        time_ctx: TimeContext,
        tx_ctx: TransactionContext,
        input: Input
    ) -> Output:
        """
        Process input within transaction context.

        May add to transaction, but MUST NOT commit.
        """
        ...
```

**Rules:**

| Operation | Permitted | Forbidden |
|-----------|-----------|-----------|
| `ctx.time.now()` | YES | — |
| `ctx.transaction.add()` | YES | — |
| Register compensation | YES | — |
| `ctx.transaction.commit()` | — | YES |
| `ctx.transaction.rollback()` | — | YES |
| Create `TransactionContext` | — | YES |

**Enforcement Signal:**
- `commit()` in L5 = TRANSACTION_BYPASS
- `TransactionContext()` in L5 = AUTHORITY_LEAK

---

### Contract 5: StatefulEngineContract (L5_workflow ONLY)

**Purpose:** Guard state transitions.

**Location:** `hoc/cus/general/L5_workflow/contracts/stateful.py`

```python
from typing import Protocol, TypeVar
from app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine import StateContext

State = TypeVar('State')
Event = TypeVar('Event')


class StatefulEngineContract(Protocol):
    """
    L5 Stateful Engine Contract.

    RESTRICTED TO: L5_workflow only

    OWNS:
    - State transition validation
    - State transition execution

    MUST NOT:
    - Persist state (L6 does that)
    - Trigger side effects
    - Create StateContext (L4 does that)
    """

    def can_transition(
        self,
        *,
        ctx: StateContext,
        target: State
    ) -> bool:
        """
        Validate if transition is allowed.
        """
        ...

    def transition(
        self,
        *,
        ctx: StateContext,
        target: State,
        reason: str
    ) -> StateTransition:
        """
        Execute state transition.

        Updates ctx.current_state but does NOT persist.
        """
        ...
```

**Rules:**

| Operation | Permitted | Forbidden |
|-----------|-----------|-----------|
| Validate transitions | YES | — |
| Execute transitions | YES | — |
| Persist state | — | YES |
| Trigger side effects | — | YES |
| Create `StateContext` | — | YES |

**Enforcement Signal:**
- Transition logic outside L5_workflow = STATE_MACHINE_DUPLICATION
- `session.add()` after transition = LAYER_VIOLATION

---

## V. L6 Contracts (Drivers)

### Contract 6: PersistenceDriverContract

**Purpose:** Perform mechanical IO only.

**Location:** `hoc/cus/general/L6_drivers/contracts/persistence.py`

```python
from typing import Protocol, TypeVar, Optional, List
from app.hoc.cus.general.L4_runtime.drivers.transaction_coordinator import TransactionContext
from app.hoc.cus.general.L5_utils.time import TimeContext

Model = TypeVar('Model')


class PersistenceDriverContract(Protocol, Generic[Model]):
    """
    L6 Persistence Driver Contract.

    PERFORMS:
    - Mechanical IO only
    - Adding to transaction
    - Reading from DB

    MUST NOT:
    - Commit / rollback
    - Generate IDs
    - Generate timestamps
    - Call other drivers
    - Contain business logic
    """

    async def save(
        self,
        *,
        time_ctx: TimeContext,
        tx_ctx: TransactionContext,
        entity: Model
    ) -> Model:
        """
        Save entity to transaction.

        Adds to transaction but does NOT commit.
        """
        ...

    async def get(
        self,
        *,
        tx_ctx: TransactionContext,
        id: str
    ) -> Optional[Model]:
        """
        Read entity by ID.
        """
        ...

    async def list(
        self,
        *,
        tx_ctx: TransactionContext,
        filters: dict
    ) -> List[Model]:
        """
        List entities matching filters.
        """
        ...
```

**Rules:**

| Operation | Permitted | Forbidden |
|-----------|-----------|-----------|
| `ctx.transaction.add()` | YES | — |
| Read from DB | YES | — |
| Use `ctx.time.now()` for updated_at | YES | — |
| Commit / rollback | — | YES |
| Generate IDs (`uuid.uuid4()`) | — | YES |
| Generate timestamps (`datetime.now()`) | — | YES |
| Call other drivers | — | YES |
| Contain business logic | — | YES |

**Enforcement Signal:**
- `session.commit()` in L6 = TRANSACTION_BYPASS
- `uuid.uuid4()` in L6 = AUTHORITY_LEAK
- `datetime.now()` in L6 = TIME_LEAK
- `if condition:` business logic = LAYER_VIOLATION

---

## VI. Forbidden Dependency Matrix (Hard Law)

### Context Access by Layer

| Context ↓ / Layer → | L2 | L4 | L5 | L6 |
|---------------------|:--:|:--:|:--:|:--:|
| Create `TimeContext` | YES | NO | NO | NO |
| Create `TransactionContext` | NO | YES | NO | NO |
| Create `OrchestrationContext` | NO | YES | NO | NO |
| Create `StateContext` | NO | YES | L5_workflow | NO |
| Use `time_ctx.now()` | YES | YES | YES | YES |
| Use `tx_ctx.add()` | NO | YES | YES | YES |
| Use `tx_ctx.commit()` | NO | YES | NO | NO |
| Use `orch_ctx.compensate()` | NO | YES | NO | NO |
| Use `state_ctx.transition()` | NO | YES | L5_workflow | NO |

### Operations by Layer

| Operation ↓ / Layer → | L4 | L5 | L6 |
|-----------------------|:--:|:--:|:--:|
| Business decisions | NO | YES | NO |
| Execution ordering | YES | NO | NO |
| Retry logic | YES | NO | NO |
| Compensation | YES | NO | NO |
| State transitions | YES | L5_workflow | NO |
| Persistence (add) | NO | YES | YES |
| Persistence (commit) | YES | NO | NO |
| Generate IDs | YES | NO | NO |
| Generate timestamps | Boundary | NO | NO |

**Violation of this matrix = CI failure.**

---

## VII. Protocol Inheritance Diagram

```
                    ┌─────────────────────────┐
                    │  RuntimeCoordinatorContract  │ L4
                    │  - Creates all contexts      │
                    │  - Owns commit/rollback      │
                    └─────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ OrchestratorContract │ │ StatefulEngineContract │ │ DomainEngineContract │
│ L4                   │ │ L5_workflow only       │ │ L5                   │
│ - Retry              │ │ - State transitions    │ │ - Business decisions │
│ - Compensation       │ │ - Validation           │ │ - Validation         │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │ TransactionalEngineContract │ L5
                    │ - Participates in tx       │
                    │ - Cannot commit            │
                    └─────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │ PersistenceDriverContract │ L6
                    │ - Mechanical IO only      │
                    │ - Cannot commit           │
                    │ - Cannot generate IDs     │
                    └─────────────────────────┘
```

---

## VIII. Type Enforcement Examples

### Example 1: Correct L5 Engine

```python
from app.hoc.cus.general.L5_engines.contracts.transactional import TransactionalEngineContract


class IncidentEngine(TransactionalEngineContract[IncidentCreate, Incident]):
    """Implements TransactionalEngineContract correctly."""

    async def process(
        self,
        *,
        time_ctx: TimeContext,
        tx_ctx: TransactionContext,
        input: IncidentCreate
    ) -> Incident:
        # LEGAL: Use time from context
        incident = Incident(
            id=input.id,  # ID provided by caller (L4)
            created_at=time_ctx.now(),
            severity=input.severity
        )

        # LEGAL: Add to transaction (but don't commit)
        tx_ctx.add(incident, domain="incidents")

        return incident
```

### Example 2: Violation Detection

```python
class BadIncidentEngine:
    """This would fail type checking and analyzer."""

    async def process(self, input: IncidentCreate) -> Incident:
        # TYPE ERROR: Missing required context parameters
        # ANALYZER: TIME_LEAK

        incident = Incident(
            id=str(uuid.uuid4()),  # ANALYZER: AUTHORITY_LEAK
            created_at=datetime.utcnow(),  # ANALYZER: TIME_LEAK
            severity=input.severity
        )

        session.add(incident)
        session.commit()  # ANALYZER: TRANSACTION_BYPASS

        return incident
```

**mypy output:**
```
error: Missing named argument "time_ctx" for "process" of "TransactionalEngineContract"
error: Missing named argument "tx_ctx" for "process" of "TransactionalEngineContract"
```

**Analyzer output:**
```yaml
violations:
  - type: TIME_LEAK
    line: 8
    call: datetime.utcnow()
  - type: AUTHORITY_LEAK
    line: 7
    call: uuid.uuid4()
  - type: TRANSACTION_BYPASS
    line: 13
    call: session.commit()
```

---

## IX. Contract File Locations

| Contract | Location |
|----------|----------|
| `RuntimeCoordinatorContract` | `hoc/cus/general/L4_runtime/contracts/coordinator.py` |
| `OrchestratorContract` | `hoc/cus/general/L4_runtime/contracts/orchestrator.py` |
| `DomainEngineContract` | `hoc/cus/general/L5_engines/contracts/engine.py` |
| `TransactionalEngineContract` | `hoc/cus/general/L5_engines/contracts/transactional.py` |
| `StatefulEngineContract` | `hoc/cus/general/L5_workflow/contracts/stateful.py` |
| `PersistenceDriverContract` | `hoc/cus/general/L6_drivers/contracts/persistence.py` |

---

## X. Migration Strategy

### Phase 1: Add Contracts (Non-Breaking)
1. Create contract Protocol files
2. Document expected usage
3. Run analyzer in WARN mode

### Phase 2: Annotate Existing Code
1. Add Protocol inheritance to existing classes
2. Add context parameters to signatures
3. Fix type errors

### Phase 3: Enforce
1. Enable mypy strict mode for contracts
2. Run analyzer in FAIL mode for CRITICAL
3. CI blocks on violations

---

## XI. Analyzer Integration

With these contracts, the analyzer becomes trivial:

```python
def analyze_file(file_path: str) -> List[Violation]:
    """
    Analyzer rule = contract × context × call-site
    """
    layer = detect_layer(file_path)  # L4, L5, L6

    violations = []

    for call in extract_calls(file_path):
        # Check: Is this call permitted for this layer?
        if call.name == "commit" and layer != "L4":
            violations.append(Violation("TRANSACTION_BYPASS", call.line))

        if call.name == "uuid4" and layer in ("L5", "L6"):
            violations.append(Violation("AUTHORITY_LEAK", call.line))

        if call.name in ("datetime.now", "datetime.utcnow"):
            violations.append(Violation("TIME_LEAK", call.line))

        # etc.

    return violations
```

**No heuristics. No debates. Contract × Layer = Rule.**

---

## XII. References

- **AUTHORITY_VIOLATION_SPEC_V1.md** — What is illegal
- **RUNTIME_CONTEXT_MODEL.md** — How authority enters the system
- **HOC_LAYER_TOPOLOGY_V1.md** — Layer architecture
- **DRIVER_ENGINE_CONTRACT.md** — L5/L6 boundary rules

---

## XIII. Change Log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-01-25 | Initial specification |

---

**Specification Author:** Claude (First-Principles Analysis)
**Enforcement Model:** Type System (Protocols) + Analyzer
**Review Status:** PENDING HUMAN RATIFICATION
