# offboarding.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/offboarding.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            offboarding.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         KnowledgeLifecycleManager via StageRegistry
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Offboarding Stage Handlers
Violations:      none
```

## Purpose

Offboarding Stage Handlers

These handlers implement the "dumb plugin" contract for knowledge plane offboarding.

Offboarding Path:
    ACTIVE → PENDING_DEACTIVATE → DEACTIVATED → ARCHIVED → PURGED

Each handler:
- Performs ONLY its specific operation
- Returns success/failure
- Does NOT manage state
- Does NOT emit events
- Does NOT check policies

The KnowledgeLifecycleManager orchestrates everything else.

CRITICAL: Offboarding is governance-controlled for GDPR/CCPA compliance.
- PENDING_DEACTIVATE has a grace period (cancel window)
- DEACTIVATED preserves data (soft delete)
- ARCHIVED exports to cold storage
- PURGED deletes data but preserves audit trail

## Import Analysis

**L7 Models:**
- `app.models.knowledge_lifecycle`

**External:**
- `base`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `DeregisterHandler(BaseStageHandler)`

GAP-078: Start offboarding process.

Initiates deregistration by moving to PENDING_DEACTIVATE state.
This starts a grace period where the offboarding can be cancelled.

Responsibilities:
- Validate no active runs are using this plane
- Check for dependent resources
- Calculate grace period end time

Does NOT:
- Actually deactivate the plane
- Delete any data
- Change state (orchestrator does that)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate deregistration request.
- `async execute(context: StageContext) -> StageResult` — Execute deregistration.
- `async _check_active_references(plane_id: str) -> List[Dict[str, Any]]` — Check for active references to this knowledge plane.
- `async _check_dependents(plane_id: str) -> List[Dict[str, Any]]` — Check for resources that depend on this knowledge plane.

### `VerifyDeactivateHandler(BaseStageHandler)`

GAP-079: Verify deactivation is safe.

Verifies that the knowledge plane can be safely deactivated:
- No active runs
- No pending queries
- Grace period has passed (or forced)

Responsibilities:
- Verify grace period status
- Check for any remaining active usage
- Validate deactivation is safe

Does NOT:
- Actually deactivate
- Make policy decisions (orchestrator's policy gate does that)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate verify deactivate request.
- `async execute(context: StageContext) -> StageResult` — Verify deactivation is safe.
- `async _check_active_usage(plane_id: str) -> List[Dict[str, Any]]` — Check for active usage of this knowledge plane.

### `DeactivateHandler(BaseStageHandler)`

GAP-080: Deactivate knowledge plane (soft delete).

Performs soft deletion - the plane is no longer queryable but data is preserved.

Responsibilities:
- Disable query endpoint
- Revoke active access tokens
- Mark as deactivated

Does NOT:
- Delete any data (preserved for archival)
- Remove from storage
- Delete audit trail

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate deactivation request.
- `async execute(context: StageContext) -> StageResult` — Execute deactivation (soft delete).
- `async _perform_deactivation(plane_id: str) -> Dict[str, Any]` — Perform deactivation operations.

### `ArchiveHandler(BaseStageHandler)`

GAP-081: Archive knowledge plane to cold storage.

Exports data to cold storage for long-term retention.

Responsibilities:
- Export data to archive storage
- Generate archive manifest
- Verify archive integrity
- Remove from hot storage (after verification)

Does NOT:
- Delete audit trail
- Remove from system entirely
- Make purge decision (requires separate approval)

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate archive request.
- `async execute(context: StageContext) -> StageResult` — Execute archival to cold storage.
- `async _perform_archive(plane_id: str, archive_bucket: str) -> Dict[str, Any]` — Perform archive to cold storage.

### `PurgeHandler(BaseStageHandler)`

GAP-082: Purge knowledge plane (permanent deletion).

Permanently deletes all data except the audit trail.

Responsibilities:
- Delete data from archive storage
- Delete indexes and embeddings
- Delete metadata
- Preserve audit trail (REQUIRED for compliance)

Does NOT:
- Delete audit trail (audit is immutable)
- Make this reversible (PURGED is terminal)

CRITICAL: This operation requires approval via GAP-087 policy gate.
The orchestrator calls the policy gate BEFORE this handler.

#### Methods

- `stage_name() -> str` — _No docstring._
- `handles_states() -> tuple[KnowledgePlaneLifecycleState, ...]` — _No docstring._
- `async validate(context: StageContext) -> Optional[str]` — Validate purge request.
- `async execute(context: StageContext) -> StageResult` — Execute permanent deletion.
- `async _perform_purge(plane_id: str) -> Dict[str, Any]` — Perform permanent deletion.

## Domain Usage

**Callers:** KnowledgeLifecycleManager via StageRegistry

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: DeregisterHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: VerifyDeactivateHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: DeactivateHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: ArchiveHandler
      methods:
        - stage_name
        - handles_states
        - validate
        - execute
      consumers: ["orchestrator"]
    - name: PurgeHandler
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
    spine_internal: []
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

