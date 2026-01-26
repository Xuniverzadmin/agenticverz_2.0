# Runtime Context Model v1.0

**Date:** 2026-01-25
**Status:** DRAFT
**Prerequisite:** AUTHORITY_VIOLATION_SPEC_V1.md
**Reference:** HOC Layer Topology V1, PIN-470

---

## Governing Principle

> **Authorities do not act. Authorities constrain how actions are allowed to occur.**
> **Constraints flow through context.**

This document defines how authority constraints enter the system via **runtime context objects**.

---

## I. Why Context Objects Exist

The Authority Violation Spec defines **what is illegal**.
This document defines **what is the legal way to do it instead**.

| Without Context Objects | With Context Objects |
|------------------------|---------------------|
| Violations point to authorities | Violations point to missing context |
| Engineers import `general.*` everywhere | Engineers receive context as parameter |
| Hidden coupling via static imports | Explicit dependency via function signature |
| Authority becomes service | Authority becomes constraint |

---

## II. Core Rule

> **Contexts are PASSED, never fetched.**

This preserves:
- **Locality** — Dependencies are visible in function signatures
- **Testability** — Contexts can be mocked/stubbed
- **Determinism** — No hidden global state
- **Authority** — Caller controls what capabilities are granted

**Forbidden Pattern:**
```python
# NEVER DO THIS
def process_incident():
    ctx = get_global_context()  # Hidden authority fetch
    timestamp = ctx.time.now()
```

**Required Pattern:**
```python
# ALWAYS DO THIS
def process_incident(ctx: RuntimeContext):
    timestamp = ctx.time.now()  # Explicit authority via parameter
```

---

## III. The Four Context Objects

### Context 1: TimeContext

**Purpose:** Provides deterministic, replay-safe time to the system.

**Interface:**
```python
@dataclass(frozen=True)
class TimeContext:
    """
    Time authority context.

    INVARIANTS:
    - Time is provided at boundary, not acquired locally
    - Same TimeContext produces same time within scope
    - Replay uses captured time, not wall clock
    """

    _current_time: datetime
    _is_replay: bool = False

    def now(self) -> datetime:
        """Returns the authoritative current time for this context."""
        return self._current_time

    def is_replay(self) -> bool:
        """Returns True if this is a replay execution."""
        return self._is_replay

    @classmethod
    def from_wall_clock(cls) -> "TimeContext":
        """
        Creates context from wall clock.
        ONLY ALLOWED at system boundary (API entry, worker start).
        """
        return cls(_current_time=datetime.utcnow(), _is_replay=False)

    @classmethod
    def from_replay(cls, captured_time: datetime) -> "TimeContext":
        """Creates context for replay with captured time."""
        return cls(_current_time=captured_time, _is_replay=True)
```

**Construction Rules:**

| Location | Allowed? | Method |
|----------|----------|--------|
| API endpoint entry | YES | `TimeContext.from_wall_clock()` |
| Worker start | YES | `TimeContext.from_wall_clock()` |
| Scheduler trigger | YES | `TimeContext.from_wall_clock()` |
| Replay execution | YES | `TimeContext.from_replay(captured)` |
| Domain engine | NO | Must receive as parameter |
| Driver | NO | Must receive as parameter |

**Passing Rules:**

```python
# L2 API creates context
@router.post("/runs")
async def create_run(request: Request):
    time_ctx = TimeContext.from_wall_clock()
    return await run_engine.create(request.body, time_ctx=time_ctx)

# L5 Engine receives context
class RunEngine:
    async def create(self, data: RunCreate, *, time_ctx: TimeContext) -> Run:
        run = Run(
            created_at=time_ctx.now(),  # Uses authority
            # ...
        )
        return await self.driver.save(run, time_ctx=time_ctx)

# L6 Driver receives context
class RunDriver:
    async def save(self, run: Run, *, time_ctx: TimeContext) -> Run:
        run.updated_at = time_ctx.now()  # Uses authority
        # ...
```

**Forbidden Patterns:**

| Pattern | Why Forbidden |
|---------|---------------|
| `datetime.now()` | Breaks replay, non-deterministic |
| `datetime.utcnow()` | Breaks replay, non-deterministic |
| `time.time()` | Breaks replay, non-deterministic |
| `TimeContext.from_wall_clock()` in domain code | Authority leak |

---

### Context 2: TransactionContext

**Purpose:** Defines consistency scope and atomic boundaries.

**Interface:**
```python
@dataclass
class TransactionContext:
    """
    Transaction authority context.

    INVARIANTS:
    - All writes within scope are atomic
    - Commit/rollback is owned by context, not caller
    - Cross-domain writes require explicit scope declaration
    """

    _session: AsyncSession
    _scope: TransactionScope
    _domains_touched: Set[str] = field(default_factory=set)
    _committed: bool = False

    @property
    def scope(self) -> TransactionScope:
        """Returns the declared consistency scope."""
        return self._scope

    def touch_domain(self, domain: str) -> None:
        """Records that this transaction touches a domain."""
        if self._committed:
            raise TransactionClosed("Cannot touch domain after commit")
        self._domains_touched.add(domain)

    def add(self, model: Any, domain: str) -> None:
        """
        Adds model to transaction.
        Domain must be declared for cross-domain tracking.
        """
        self.touch_domain(domain)
        self._session.add(model)

    async def commit(self) -> None:
        """
        Commits the transaction.
        ONLY the transaction owner may call this.
        """
        if len(self._domains_touched) > 1 and self._scope != TransactionScope.CROSS_DOMAIN:
            raise TransactionScopeViolation(
                f"Cross-domain write ({self._domains_touched}) requires CROSS_DOMAIN scope"
            )
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        """Rolls back the transaction."""
        await self._session.rollback()


class TransactionScope(Enum):
    """Declared consistency scope."""
    SINGLE_MODEL = "single_model"      # One model type
    SINGLE_DOMAIN = "single_domain"    # Multiple models, same domain
    CROSS_DOMAIN = "cross_domain"      # Multiple domains (requires coordinator)


@asynccontextmanager
async def transaction_context(
    scope: TransactionScope,
    session_factory: Callable[[], AsyncSession]
) -> AsyncIterator[TransactionContext]:
    """
    Creates a transaction context.
    ONLY ALLOWED at L4 runtime or coordinator level.
    """
    async with session_factory() as session:
        ctx = TransactionContext(_session=session, _scope=scope)
        try:
            yield ctx
            if not ctx._committed:
                await ctx.commit()
        except Exception:
            await ctx.rollback()
            raise
```

**Construction Rules:**

| Location | Allowed? | Scope |
|----------|----------|-------|
| L4 RunCompletionTransaction | YES | CROSS_DOMAIN |
| L4 GovernanceOrchestrator | YES | CROSS_DOMAIN |
| L6 Driver (single domain) | YES | SINGLE_DOMAIN |
| L5 Engine | NO | Must receive as parameter |

**Passing Rules:**

```python
# L4 Coordinator creates CROSS_DOMAIN context
class RunCompletionTransaction:
    async def execute(self, run_id: str) -> TransactionResult:
        async with transaction_context(
            scope=TransactionScope.CROSS_DOMAIN,
            session_factory=self.session_factory
        ) as tx_ctx:
            await self._create_incident(tx_ctx)
            await self._evaluate_policy(tx_ctx)
            await self._complete_trace(tx_ctx)
            # commit happens automatically

# L5 Engine receives context
class IncidentEngine:
    async def create_from_run(
        self,
        run: Run,
        *,
        tx_ctx: TransactionContext
    ) -> Incident:
        incident = Incident(...)
        tx_ctx.add(incident, domain="incidents")
        return incident

# L6 Driver receives context
class IncidentDriver:
    async def save(
        self,
        incident: Incident,
        *,
        tx_ctx: TransactionContext
    ) -> Incident:
        tx_ctx.add(incident, domain="incidents")
        # NO commit here - context owner commits
        return incident
```

**Forbidden Patterns:**

| Pattern | Why Forbidden |
|---------|---------------|
| `session.add()` without context | No scope tracking |
| `session.commit()` in L5/L6 | Authority leak |
| Creating CROSS_DOMAIN in domain code | Authority leak |
| Multiple `session.commit()` in one function | Split atomicity |

---

### Context 3: OrchestrationContext

**Purpose:** Controls execution ordering, retry policy, and compensation.

**Interface:**
```python
@dataclass
class OrchestrationContext:
    """
    Orchestration authority context.

    INVARIANTS:
    - Execution order is defined by orchestrator, not domain
    - Retry/backoff policy is owned by context
    - Compensation hooks are registered, not ad-hoc
    """

    _execution_id: str
    _retry_policy: RetryPolicy
    _compensation_stack: List[Callable[[], Awaitable[None]]] = field(default_factory=list)
    _step_results: Dict[str, StepResult] = field(default_factory=dict)

    @property
    def execution_id(self) -> str:
        """Unique identifier for this orchestration execution."""
        return self._execution_id

    def register_compensation(self, compensate: Callable[[], Awaitable[None]]) -> None:
        """
        Registers a compensation action.
        Called in reverse order if orchestration fails.
        """
        self._compensation_stack.append(compensate)

    def record_step(self, step_name: str, result: StepResult) -> None:
        """Records the result of an orchestration step."""
        self._step_results[step_name] = result

    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        """Gets the result of a previous step."""
        return self._step_results.get(step_name)

    async def compensate(self) -> None:
        """
        Executes compensation in reverse order.
        ONLY called by orchestrator on failure.
        """
        for compensate in reversed(self._compensation_stack):
            try:
                await compensate()
            except Exception as e:
                # Log but continue compensation
                logger.error(f"Compensation failed: {e}")

    @property
    def retry_policy(self) -> RetryPolicy:
        """Returns the retry policy for this orchestration."""
        return self._retry_policy


@dataclass
class RetryPolicy:
    """Retry policy owned by orchestration context."""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0

    def get_delay(self, attempt: int) -> float:
        """Calculates delay for given attempt number."""
        delay = self.base_delay_seconds * (self.exponential_base ** attempt)
        return min(delay, self.max_delay_seconds)


@dataclass
class StepResult:
    """Result of an orchestration step."""
    success: bool
    data: Any = None
    error: Optional[Exception] = None
```

**Construction Rules:**

| Location | Allowed? | Reason |
|----------|----------|--------|
| L4 GovernanceOrchestrator | YES | Owns orchestration |
| L4 RunCompletionTransaction | YES | Coordinates execution |
| L5 Engine | NO | Must receive as parameter |
| L6 Driver | NO | Must receive as parameter |

**Passing Rules:**

```python
# L4 Orchestrator creates context
class GovernanceOrchestrator:
    async def execute_workflow(self, contract_id: str) -> WorkflowResult:
        orch_ctx = OrchestrationContext(
            _execution_id=str(uuid.uuid4()),
            _retry_policy=RetryPolicy(max_attempts=3)
        )

        # Step 1: Activate contract
        result = await self._activate_contract(contract_id, orch_ctx=orch_ctx)
        orch_ctx.record_step("activate", result)

        if not result.success:
            await orch_ctx.compensate()
            return WorkflowResult.failed(result.error)

        # Step 2: Create job
        result = await self._create_job(contract_id, orch_ctx=orch_ctx)
        orch_ctx.record_step("create_job", result)

        # ... etc

# Domain code receives context but CANNOT orchestrate
class ContractEngine:
    async def activate(
        self,
        contract_id: str,
        *,
        orch_ctx: OrchestrationContext
    ) -> Contract:
        # Register compensation BEFORE action
        orch_ctx.register_compensation(
            lambda: self._deactivate(contract_id)
        )

        # Perform action
        contract = await self.driver.activate(contract_id)
        return contract
```

**Forbidden Patterns:**

| Pattern | Why Forbidden |
|---------|---------------|
| `try/except` with retry in domain code | Orchestration leak |
| `while` loop with `sleep()` | Orchestration leak |
| `asyncio.sleep()` for backoff | Orchestration leak |
| Calling 2+ services with error handling | Orchestration leak |
| Creating OrchestrationContext in L5/L6 | Authority leak |

---

### Context 4: StateContext

**Purpose:** Owns state transition validation and execution.

**Interface:**
```python
@dataclass
class StateContext:
    """
    State authority context.

    INVARIANTS:
    - Only StateContext may validate transitions
    - Only StateContext may execute transitions
    - Domain code may read state, not change it
    """

    _state_machine: StateMachine
    _current_state: str
    _entity_id: str
    _transition_log: List[StateTransition] = field(default_factory=list)

    @property
    def current_state(self) -> str:
        """Returns the current state (read-only)."""
        return self._current_state

    def can_transition(self, target_state: str) -> bool:
        """
        Checks if transition is allowed.
        This is validation, not execution.
        """
        return self._state_machine.is_valid_transition(
            self._current_state,
            target_state
        )

    def transition(self, target_state: str, *, reason: str) -> StateTransition:
        """
        Executes state transition.
        ONLY called via orchestration context.
        """
        if not self.can_transition(target_state):
            raise InvalidStateTransition(
                f"Cannot transition from {self._current_state} to {target_state}"
            )

        transition = StateTransition(
            entity_id=self._entity_id,
            from_state=self._current_state,
            to_state=target_state,
            reason=reason,
            timestamp=datetime.utcnow()  # Should use TimeContext
        )

        self._current_state = target_state
        self._transition_log.append(transition)
        return transition

    @property
    def transition_history(self) -> List[StateTransition]:
        """Returns the transition history (read-only)."""
        return self._transition_log.copy()


@dataclass
class StateTransition:
    """Record of a state transition."""
    entity_id: str
    from_state: str
    to_state: str
    reason: str
    timestamp: datetime


class StateMachine:
    """
    Defines valid state transitions.
    This is the DEFINITION, not ENFORCEMENT.
    """

    def __init__(self, transitions: Dict[str, Set[str]]):
        self._transitions = transitions

    def is_valid_transition(self, from_state: str, to_state: str) -> bool:
        """Checks if transition is valid per definition."""
        allowed = self._transitions.get(from_state, set())
        return to_state in allowed
```

**Construction Rules:**

| Location | Allowed? | Reason |
|----------|----------|--------|
| L5_workflow ContractService | YES | Owns state authority |
| L4 GovernanceOrchestrator | YES | Coordinates transitions |
| L5 Domain Engine | NO | Must receive as parameter |
| L6 Driver | NO | Must receive as parameter |

**The Definition vs Enforcement Split:**

| Activity | Where | Authority Required? |
|----------|-------|---------------------|
| Define states (Enum) | Anywhere | NO |
| Define transitions (StateMachine) | L5_workflow | NO |
| Read current state | Anywhere | NO |
| Validate transition allowed | StateContext | YES |
| Execute transition | StateContext | YES |

**Passing Rules:**

```python
# L5_workflow creates state context
class ContractService:
    def get_state_context(self, contract: Contract) -> StateContext:
        return StateContext(
            _state_machine=CONTRACT_STATE_MACHINE,
            _current_state=contract.status,
            _entity_id=contract.id
        )

    async def approve(
        self,
        contract_id: str,
        *,
        orch_ctx: OrchestrationContext
    ) -> Contract:
        contract = await self.driver.get(contract_id)
        state_ctx = self.get_state_context(contract)

        # Validate and execute via context
        if not state_ctx.can_transition("APPROVED"):
            raise InvalidStateTransition(...)

        transition = state_ctx.transition("APPROVED", reason="Manual approval")

        # Persist
        contract.status = state_ctx.current_state
        await self.driver.save(contract)

        return contract
```

**Forbidden Patterns:**

| Pattern | Why Forbidden |
|---------|---------------|
| `entity.status = "APPROVED"` directly | Bypasses validation |
| `if status == X: status = Y` | Bypasses state machine |
| Transition without StateContext | Authority leak |
| Creating StateContext in L6 driver | Authority leak |

---

## IV. Composite Runtime Context

For convenience, contexts can be bundled:

```python
@dataclass
class RuntimeContext:
    """
    Composite runtime context.
    Bundles all authority contexts for passing.
    """

    time: TimeContext
    transaction: Optional[TransactionContext] = None
    orchestration: Optional[OrchestrationContext] = None
    state: Optional[StateContext] = None

    @classmethod
    def minimal(cls, time: TimeContext) -> "RuntimeContext":
        """Creates minimal context with only time."""
        return cls(time=time)

    @classmethod
    def for_transaction(
        cls,
        time: TimeContext,
        transaction: TransactionContext
    ) -> "RuntimeContext":
        """Creates context for transactional operations."""
        return cls(time=time, transaction=transaction)

    @classmethod
    def for_orchestration(
        cls,
        time: TimeContext,
        transaction: TransactionContext,
        orchestration: OrchestrationContext
    ) -> "RuntimeContext":
        """Creates full context for orchestrated operations."""
        return cls(
            time=time,
            transaction=transaction,
            orchestration=orchestration
        )
```

**Usage:**

```python
# L4 Coordinator creates full context
async def complete_run(self, run_id: str) -> Result:
    ctx = RuntimeContext.for_orchestration(
        time=TimeContext.from_wall_clock(),
        transaction=await self._create_transaction_context(),
        orchestration=OrchestrationContext(...)
    )

    # Pass to engines
    await self.incident_engine.create_from_run(run, ctx=ctx)
    await self.policy_engine.evaluate(run, ctx=ctx)
    await self.trace_store.complete(run, ctx=ctx)
```

---

## V. Context Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYSTEM BOUNDARY                          │
│   (API Entry, Worker Start, Scheduler Trigger)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  TimeContext    │  ← Created here ONLY
                    │  from_wall_clock│
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     L4 RUNTIME / COORDINATOR                    │
│                                                                 │
│   ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│   │ TransactionCtx  │  │ OrchestrationCtx│  │  StateContext │  │
│   │ (CROSS_DOMAIN)  │  │ (retry, comp)   │  │ (transitions) │  │
│   └─────────────────┘  └─────────────────┘  └───────────────┘  │
│                                                                 │
│   RuntimeContext = bundle(time, tx, orch, state)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ ctx passed as parameter
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        L5 ENGINES                               │
│                                                                 │
│   async def process(self, data, *, ctx: RuntimeContext):        │
│       timestamp = ctx.time.now()           # USE time           │
│       ctx.transaction.add(model, domain)   # USE transaction    │
│       ctx.orchestration.register_compensation(...)  # USE orch  │
│       # CANNOT create contexts                                  │
│       # CANNOT call ctx.transaction.commit()                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ ctx passed as parameter
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        L6 DRIVERS                               │
│                                                                 │
│   async def save(self, model, *, ctx: RuntimeContext):          │
│       model.updated_at = ctx.time.now()    # USE time           │
│       ctx.transaction.add(model, domain)   # USE transaction    │
│       # CANNOT create contexts                                  │
│       # CANNOT call ctx.transaction.commit()                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## VI. Enforcement Summary

### Who Creates What

| Context | Created By | Received By |
|---------|------------|-------------|
| TimeContext | L2 API, Worker, Scheduler | L4, L5, L6 |
| TransactionContext | L4 Coordinator | L5, L6 |
| OrchestrationContext | L4 Orchestrator | L5, L6 |
| StateContext | L5_workflow (state owner) | L5 engines |

### Who May Call What

| Operation | L2 | L4 | L5 | L6 |
|-----------|----|----|----|----|
| `TimeContext.from_wall_clock()` | YES | NO | NO | NO |
| `transaction_context()` | NO | YES | NO | NO |
| `OrchestrationContext()` | NO | YES | NO | NO |
| `StateContext()` | NO | YES | L5_workflow only | NO |
| `ctx.time.now()` | YES | YES | YES | YES |
| `ctx.transaction.add()` | NO | YES | YES | YES |
| `ctx.transaction.commit()` | NO | YES | NO | NO |
| `ctx.orchestration.compensate()` | NO | YES | NO | NO |
| `state_ctx.transition()` | NO | YES | L5_workflow only | NO |

---

## VII. Migration Path

For existing code that violates authority:

### Step 1: Add Context Parameters

```python
# Before
def create_incident(data: IncidentCreate) -> Incident:
    incident = Incident(
        created_at=datetime.utcnow(),  # VIOLATION
        ...
    )

# After
def create_incident(
    data: IncidentCreate,
    *,
    ctx: RuntimeContext
) -> Incident:
    incident = Incident(
        created_at=ctx.time.now(),  # LEGAL
        ...
    )
```

### Step 2: Thread Context Through Call Chain

```python
# L2 creates context
@router.post("/incidents")
async def create_incident_endpoint(request: Request):
    ctx = RuntimeContext.minimal(TimeContext.from_wall_clock())
    return await incident_engine.create(request.body, ctx=ctx)

# L5 passes context
class IncidentEngine:
    async def create(self, data, *, ctx: RuntimeContext):
        incident = Incident(created_at=ctx.time.now(), ...)
        return await self.driver.save(incident, ctx=ctx)

# L6 uses context
class IncidentDriver:
    async def save(self, incident, *, ctx: RuntimeContext):
        incident.updated_at = ctx.time.now()
        ctx.transaction.add(incident, domain="incidents")
```

---

## VIII. References

- **AUTHORITY_VIOLATION_SPEC_V1.md** — What is illegal
- **HOC_LAYER_TOPOLOGY_V1.md** — Layer architecture
- **DRIVER_ENGINE_CONTRACT.md** — L5/L6 boundary rules

---

## IX. Change Log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-01-25 | Initial specification |

---

**Specification Author:** Claude (First-Principles Analysis)
**Review Status:** PENDING HUMAN RATIFICATION
