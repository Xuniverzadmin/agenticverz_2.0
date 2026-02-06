# operation_registry.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            operation_registry.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         L2 APIs (hoc/api/cus/{domain}/*.py)
Outbound:        app.hoc.cus.hoc_spine.services.time, app.hoc.cus.hoc_spine.authority.runtime_switch
Transaction:     OWNS COMMIT
Cross-domain:    none
Purpose:         Operation Registry (L4 Orchestrator)
Violations:      none
```

## Purpose

Operation Registry (L4 Orchestrator)

Central dispatch layer for domain operations. L2 APIs call this instead of
importing L5 engines directly.

Flow:
    L2 HTTP → OperationRegistry.execute(op_name, ctx) → L5 handler → L6 driver

What the registry adds to every operation:
    1. Authority check (is governance active? degraded mode?)
    2. Audit record (who called what, when, outcome)
    3. Consistent error handling (L5 exceptions → OperationResult)
    4. Single dispatch point (operation name → handler lookup)

What the registry does NOT do:
    - Own transactions (the session comes from L2 via FastAPI DI)
    - Execute business logic (that stays in L5)
    - Make decisions (authority is checked, not created here)

Usage:
    # L2 API file (e.g., hoc/api/cus/overview/overview.py)
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        get_operation_registry,
        get_session_dep,
        OperationContext,
    )

    session = Depends(get_session_dep)
    registry = get_operation_registry()
    result = await registry.execute("overview.query", OperationContext(
        session=session,
        tenant_id=tenant_id,
        params={"endpoint": "highlights"},
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return result.data

Handler registration:
    # In hoc_spine/orchestrator/handlers/{domain}_handler.py
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        OperationHandler,
        OperationContext,
        OperationResult,
    )

    class OverviewQueryHandler(OperationHandler):
        async def execute(self, ctx: OperationContext) -> OperationResult:
            from app.hoc.cus.overview.L5_engines.overview_facade import get_overview_facade
            facade = get_overview_facade()
            data = await facade.get_highlights(session=ctx.session, tenant_id=ctx.tenant_id)
            return OperationResult.ok(data)

    # Registration (called once at startup)
    registry = get_operation_registry()
    registry.register("overview.query", OverviewQueryHandler())

## Import Analysis

**Spine-internal:**
- `app.hoc.cus.hoc_spine.services.time`
- `app.hoc.cus.hoc_spine.authority.runtime_switch`

**External:**
- `sqlalchemy.ext.asyncio`
 - `app.db` (via `get_session_dep` local import)

## Transaction Boundary

- **Commits:** YES
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_operation_registry() -> OperationRegistry`

Get the operation registry singleton.

Returns the same instance for the lifetime of the process.
Handlers register against this instance at import time.

### `get_session_dep() -> AsyncGenerator[AsyncSession, None]`

L4-provided session dependency for L2 endpoints.

L2 files must NOT import sqlalchemy or app.db directly. Use this dependency
to keep L2 free of DB/ORM imports while still providing a session for
OperationContext construction.

### `reset_operation_registry() -> None`

Reset the registry singleton. FOR TESTING ONLY.

Production code must never call this.

## Classes

### `OperationContext`

Immutable context passed to every operation handler.

The session comes from L2 via FastAPI DI. The registry does NOT
create sessions or own transaction boundaries.

### `OperationResult`

Outcome of an operation dispatch.

L2 code inspects .success and either uses .data or raises
based on .error / .error_code.

#### Methods

- `ok(data: Any) -> 'OperationResult'` — Create a successful result.
- `fail(error: str, error_code: str) -> 'OperationResult'` — Create a failed result.

### `OperationHandler(Protocol)`

Protocol for domain operation handlers.

Each handler wraps ONE L5 facade call. The handler:
  - Receives an OperationContext (session, tenant, params)
  - Calls the L5 facade
  - Returns an OperationResult

The handler MUST NOT:
  - Import from L2
  - Create sessions
  - Call session.commit() (transaction ownership stays with caller)
  - Call other domain handlers directly (use registry for cross-domain)

#### Methods

- `async execute(ctx: OperationContext) -> OperationResult` — Execute the domain operation.

### `OperationRegistry`

Central dispatch for domain operations.

Maps operation name strings (e.g., "policies.query") to OperationHandler
instances. L2 APIs call execute() instead of importing L5 directly.

Authority Gate:
    Before dispatching, checks governance runtime state.
    If governance is disabled (kill switch), operations still execute
    but are tagged as unguarded in audit.
    If degraded mode is active, a warning is logged.

Audit:
    Every dispatch logs: operation name, tenant, duration, outcome.
    Structured logging — no external audit store dependency in v1.
    AuditStore integration deferred to Phase A.6.

#### Methods

- `__init__() -> None` — _No docstring._
- `register(operation: str, handler: OperationHandler) -> None` — Register a handler for an operation name.
- `freeze() -> None` — Freeze the registry. No further registrations allowed.
- `async execute(operation: str, ctx: OperationContext) -> OperationResult` — Dispatch an operation to its registered handler.
- `_check_authority(operation: str) -> bool` — Check governance runtime state before dispatch.
- `_audit_dispatch(operation: str, ctx: OperationContext, result: OperationResult, duration_ms: float, governance_active: bool) -> None` — Emit structured audit log for every dispatch.
- `operations() -> list[str]` — Return sorted list of registered operation names.
- `operation_count() -> int` — Return count of registered operations.
- `is_frozen() -> bool` — Return whether the registry is frozen.
- `has_operation(operation: str) -> bool` — Check if an operation is registered.
- `get_handler(operation: str) -> Optional[OperationHandler]` — Get the handler for an operation (for testing/introspection).
- `status() -> dict[str, Any]` — Return registry status for health/diagnostics endpoints.

## Domain Usage

**Callers:** L2 APIs (hoc/api/cus/{domain}/*.py)

## Export Contract

```yaml
exports:
  functions:
    - name: get_operation_registry
      signature: "get_operation_registry() -> OperationRegistry"
      consumers: ["orchestrator"]
    - name: get_session_dep
      signature: "get_session_dep() -> AsyncGenerator[AsyncSession, None]"
      consumers: ["L2 APIs"]
    - name: reset_operation_registry
      signature: "reset_operation_registry() -> None"
      consumers: ["orchestrator"]
  classes:
    - name: OperationContext
      methods: []
      consumers: ["orchestrator"]
    - name: OperationResult
      methods:
        - ok
        - fail
      consumers: ["orchestrator"]
    - name: OperationHandler
      methods:
        - execute
      consumers: ["orchestrator"]
    - name: OperationRegistry
      methods:
        - register
        - freeze
        - execute
        - operations
        - operation_count
        - is_frozen
        - has_operation
        - get_handler
        - status
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
    spine_internal: ['app.hoc.cus.hoc_spine.services.time', 'app.hoc.cus.hoc_spine.authority.runtime_switch']
    l7_model: []
    external: ['sqlalchemy.ext.asyncio']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```
