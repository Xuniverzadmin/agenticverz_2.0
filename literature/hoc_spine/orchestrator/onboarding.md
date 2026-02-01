# onboarding.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/onboarding.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            onboarding.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         KnowledgeLifecycleManager via StageRegistry
Outbound:        app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution, app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution, app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Onboarding Stage Handlers
Violations:      none
```

## Purpose

Onboarding Stage Handlers

These handlers implement the "dumb plugin" contract for knowledge plane onboarding.

Onboarding Path:
    DRAFT → PENDING_VERIFY → VERIFIED → INGESTING → INDEXED →
    CLASSIFIED → PENDING_ACTIVATE → ACTIVE

Each handler:
- Performs ONLY its specific operation
- Returns success/failure
- Does NOT manage state
- Does NOT emit events
- Does NOT check policies

The KnowledgeLifecycleManager orchestrates everything else.

## Import Analysis

**Spine-internal:**
- `app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution`
- `app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution`
- `app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution`

**L7 Models:**
- `app.models.knowledge_lifecycle`

**External:**
- `base`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `RegisterHandler(BaseStageHandler)`

GAP-071: Register knowledge plane.

Creates the initial knowledge plane record in DRAFT state.
This is a special handler - it doesn't transition FROM a state,
it creates a new entity.

Responsibilities:
- Validate registration request
- Create plane configuration
- Initialize metadata

Does NOT:
- Create database records (orchestrator does that)
- Set state (orchestrator does that)
- Emit events (orchestrator does that)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate registration request.
- `async execute(context: StageContext) -> StageResult` — Execute registration.

### `VerifyHandler(BaseStageHandler)`

GAP-072: Verify knowledge plane connectivity.

Verifies that the knowledge source is accessible and credentials are valid.

Responsibilities:
- Test connection to source
- Validate credentials
- Check source schema/structure

Does NOT:
- Store credentials (already done at registration)
- Update state (orchestrator does that)
- Retry on failure (orchestrator handles retry logic)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate verification request.
- `async execute(context: StageContext) -> StageResult` — Execute verification.
- `async _simulate_verification(source_type: str, connection_string: Optional[str]) -> Dict[str, Any]` — Simulate verification for testing.

### `IngestHandler(BaseStageHandler)`

GAP-073: Ingest data from knowledge source.
GAP-159: Real execution via DataIngestionExecutor.

Reads data from the source and stores it for processing.

Responsibilities:
- Read data from source via ConnectorRegistry
- Transform to internal format
- Store raw data for indexing

Does NOT:
- Create indexes (IndexHandler does that)
- Classify data (ClassifyHandler does that)
- Track progress in state (orchestrator does that)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate ingestion request.
- `async execute(context: StageContext) -> StageResult` — Execute data ingestion.

### `IndexHandler(BaseStageHandler)`

GAP-074: Create indexes and embeddings.
GAP-160: Real execution via IndexingExecutor.

Creates vector embeddings and search indexes for the ingested data.

Responsibilities:
- Generate embeddings via configured provider
- Create vector indexes in VectorConnector
- Build search structures

Does NOT:
- Classify data (ClassifyHandler does that)
- Manage index lifecycle (orchestrator does that)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate indexing request.
- `async execute(context: StageContext) -> StageResult` — Execute indexing.

### `ClassifyHandler(BaseStageHandler)`

GAP-075: Classify data sensitivity and schema.
GAP-161: Real execution via ClassificationExecutor.

Analyzes the data to determine:
- Sensitivity level (public, internal, confidential, restricted)
- Data schema/structure
- Content categories
- PII presence

Responsibilities:
- Detect PII via pattern matching
- Classify sensitivity based on content
- Categorize content

Does NOT:
- Enforce policies (policy gate does that)
- Block activation (orchestrator does that)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate classification request.
- `async execute(context: StageContext) -> StageResult` — Execute classification.

### `ActivateHandler(BaseStageHandler)`

GAP-076: Activate knowledge plane.

Final activation steps before the plane becomes operational.

Responsibilities:
- Validate policies are bound
- Initialize runtime state
- Set up access controls

Does NOT:
- Check policy gate (orchestrator does that via GAP-087)
- Emit activation event (orchestrator does that)

Note: This handler runs AFTER the policy gate check.
The orchestrator calls GAP-087 policy gate first, then this handler.

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate activation request.
- `async execute(context: StageContext) -> StageResult` — Execute activation.
- `async _simulate_activation(plane_id: str) -> Dict[str, Any]` — Simulate activation for testing.

### `GovernHandler(BaseStageHandler)`

GAP-077: Runtime governance hooks.

Called on every access to the knowledge plane to emit governance evidence.

Responsibilities:
- Emit access evidence
- Track usage metrics
- Validate access context

Does NOT:
- Enforce policies (runtime enforcer does that)
- Block access (returns evidence, enforcer decides)

Note: This is not a state transition handler.
It's called at runtime when the plane is ACTIVE.

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate governance request.
- `async execute(context: StageContext) -> StageResult` — Execute governance check.

## Domain Usage

**Callers:** KnowledgeLifecycleManager via StageRegistry

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: RegisterHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: VerifyHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: IngestHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: IndexHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: ClassifyHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: ActivateHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: GovernHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: ['app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution', 'app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution', 'app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution']
    l7_model: ['app.models.knowledge_lifecycle']
    external: ['base']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

