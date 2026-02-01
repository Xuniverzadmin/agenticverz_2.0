# lifecycle_stages_base.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/lifecycle_stages_base.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            lifecycle_stages_base.py
Lives in:        services/
Role:            Services
Inbound:         KnowledgeLifecycleManager, stage handlers
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Stage Handler Protocol and Base Types
Violations:      none
```

## Purpose

Stage Handler Protocol and Base Types

This module defines the contract for lifecycle stage handlers.

CRITICAL DESIGN INVARIANT:
    Stage handlers are DUMB PLUGINS.
    They do NOT manage state.
    They do NOT emit events.
    They do NOT check policies.
    The orchestrator does ALL of that.

Why Dumb:
- If stages manage state, you get split-brain
- If stages emit events, you get duplicate audit
- If stages check policy, you get enforcement fragmentation

## Import Analysis

**L7 Models:**
- `app.models.knowledge_lifecycle`

**External:**
- `onboarding`
- `offboarding`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `StageStatus(Enum)`

Result status from stage execution.

### `StageContext`

Context passed to stage handlers.

Contains all information a stage needs to execute,
without giving it direct access to state management.

### `StageResult`

Result returned by stage handlers.

Stage handlers return this to indicate success/failure.
The orchestrator uses this to decide what to do next.

#### Methods

- `success() -> bool` — Check if stage succeeded.
- `is_async() -> bool` — Check if stage is async (pending completion).
- `ok(message: Optional[str], **data: Any) -> 'StageResult'` — Create a successful result.
- `fail(message: str, error_code: Optional[str], **details: Any) -> 'StageResult'` — Create a failure result.
- `pending(job_id: str, message: Optional[str]) -> 'StageResult'` — Create a pending (async) result.
- `skipped(reason: str) -> 'StageResult'` — Create a skipped result.

### `StageHandler(Protocol)`

Protocol for stage handlers.

Stage handlers are dumb. The orchestrator is smart.

Implementation Requirements:
- Must be stateless (no instance state that affects execution)
- Must not call KnowledgeLifecycleManager methods
- Must not emit audit events
- Must not check policies
- Must only perform their specific operation

#### Methods

- `stage_name() -> str` — Human-readable name for this stage.
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — States this handler can execute from.
- `async execute(context: StageContext) -> StageResult` — Execute stage-specific operation.
- `async validate(context: StageContext) -> Optional[str]` — Validate that stage can execute with given context.

### `BaseStageHandler(ABC)`

Base class for stage handlers.

Provides common implementation while enforcing the "dumb plugin" contract.

#### Methods

- `stage_name() -> str` — Human-readable name for this stage.
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — States this handler can execute from.
- `async validate(context: StageContext) -> Optional[str]` — Default validation: check that current state is in handles_states.
- `async execute(context: StageContext) -> StageResult` — Execute stage-specific operation.

### `StageRegistry`

Registry of stage handlers.

Maps states to their handlers for the orchestrator to use.

#### Methods

- `__init__() -> None` — _No docstring._
- `register(handler: StageHandler) -> None` — Register a handler for its states.
- `get_handler(state: KnowledgePlaneLifecycleState) -> Optional[StageHandler]` — Get handler for a state, if any.
- `has_handler(state: KnowledgePlaneLifecycleState) -> bool` — Check if a handler is registered for a state.
- `create_default() -> 'StageRegistry'` — Create registry with all default handlers.

## Domain Usage

**Callers:** KnowledgeLifecycleManager, stage handlers

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: StageStatus
      methods: []
      consumers: ["orchestrator"]
    - name: StageContext
      methods: []
      consumers: ["orchestrator"]
    - name: StageResult
      methods:
        - success
        - is_async
        - ok
        - fail
        - pending
        - skipped
      consumers: ["orchestrator"]
    - name: StageHandler
      methods:
        - stage_name
        - handles_states
        - execute
        - validate
      consumers: ["orchestrator"]
    - name: BaseStageHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: StageRegistry
      methods:
        - register
        - get_handler
        - has_handler
        - create_default
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: ['app.models.knowledge_lifecycle']
    external: ['onboarding', 'offboarding']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

