# Orchestrator — Folder Summary

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/`
**Layer:** L4
**Scripts:** 12 + 3 coordinators

---

## 1. Purpose

Sole execution entry point from L2. Owns transaction boundaries, operation resolution, and execution order. No code runs without going through here.

Also provides L4-owned session dependency (`get_session_dep`) so L2 can obtain DB sessions without direct DB/ORM imports.

Bridge updates (PIN-L2-PURITY):
- PoliciesEngineBridge for L2 access to policy engine classes/modules
- AccountBridge exposes RBAC engine capability
- IntegrationsDriverBridge exposes worker registry capabilities

## 2. What Belongs Here

- Operation dispatcher (what runs)
- Cross-domain context assembly
- Start / end / phase transitions
- Job state machines and execution tracking

## 3. What Must NOT Be Here

- Execute domain business logic (that's L5)
- Own persistence (that's L6/L7)
- Import L5 engines directly (use protocols)

## 4. Script Inventory

| Script | Purpose | Transaction | Cross-domain | Verdict |
|--------|---------|-------------|--------------|---------|
| [constraint_checker.py](constraint_checker.md) | Module: constraint_checker | Forbidden | no | OK |
| [execution.py](execution.md) | Module: execution | Forbidden | no | OK |
| [governance_orchestrator.py](governance_orchestrator.md) | Part-2 Governance Orchestrator (L4) | Forbidden | no | OK |
| [job_executor.py](job_executor.md) | Part-2 Job Executor (L5) | Forbidden | no | OK |
| [knowledge_plane.py](knowledge_plane.md) | KnowledgePlane - Knowledge plane models and registry. | Forbidden | no | OK |
| [offboarding.py](offboarding.md) | Offboarding Stage Handlers | Forbidden | no | OK |
| [onboarding.py](onboarding.md) | Onboarding Stage Handlers | Forbidden | no | OK |
| [operation_registry.py](operation_registry.md) | Operation Registry (L4 Orchestrator) | OWNS COMMIT | no | OK |
| [phase_status_invariants.py](phase_status_invariants.md) | Module: phase_status_invariants | Forbidden | no | OK |
| [plan_generation_engine.py](plan_generation_engine.md) | Domain engine for plan generation. | Forbidden | no | OK |
| [pool_manager.py](pool_manager.md) | Connection Pool Manager (GAP-172) | Forbidden | no | OK |
| [run_governance_facade.py](run_governance_facade.md) | Run Governance Facade (L4 Domain Logic) | Forbidden | no | OK |

### Coordinators Subfolder (`coordinators/`)

Cross-domain mediators created by PIN-504 (Loop Model C4 pattern).

| Script | Purpose | Cross-domain | Reference | Wiring Status |
|--------|---------|--------------|-----------|---------------|
| `coordinators/__init__.py` | Package init for C4 coordinator infrastructure | — | PIN-504 | EXPORTED |
| `coordinators/audit_coordinator.py` | Cross-domain audit dispatch (incidents/policies → logs) | yes | PIN-504 | TOMBSTONED |
| `coordinators/signal_coordinator.py` | Dual threshold signal emission (controls + activity) | yes | PIN-504 | EXPORTED |
| `coordinators/logs_coordinator.py` | Spine passthrough for logs read service access | yes | PIN-504 | — |
| `coordinators/run_evidence_coordinator.py` | Cross-domain evidence aggregation for runs (incidents + policies + controls) | yes | PIN-519 | — |
| `coordinators/run_proof_coordinator.py` | Integrity verification via traces (HASH_CHAIN model) | yes | PIN-519 | — |
| `coordinators/signal_feedback_coordinator.py` | Signal feedback queries from audit ledger | yes | PIN-519 | — |
| `coordinators/canary_coordinator.py` | Scheduled canary validation runs | yes | PIN-520 | EXPORTED |
| `coordinators/execution_coordinator.py` | Pre-execution scoping + job lifecycle | yes | PIN-520 | EXPORTED |
| `coordinators/replay_coordinator.py` | Deterministic replay enforcement | yes | PIN-520 | EXPORTED |

## 5. Assessment

**Correct:** 12/12 scripts pass all governance checks.

**Missing (from reconciliation artifact):**

- Explicit OperationRegistry — operation→callable mapping
- Mandatory cross_domain_deps=[] declaration per operation
- Hard assertion: no L5 may call coordinator directly

## 6. L5 Pairing Aggregate

| Script | Serves Domains | Wired L5 Consumers | Gaps |
|--------|----------------|--------------------|------|
| constraint_checker.py | _none_ | 0 | 0 |
| execution.py | _none_ | 0 | 0 |
| governance_orchestrator.py | _none_ | 0 | 0 |
| job_executor.py | _none_ | 0 | 0 |
| knowledge_plane.py | _none_ | 0 | 0 |
| offboarding.py | _none_ | 0 | 0 |
| onboarding.py | _none_ | 0 | 0 |
| operation_registry.py | _none_ | 0 | 0 |
| phase_status_invariants.py | _none_ | 0 | 0 |
| plan_generation_engine.py | _none_ | 0 | 0 |
| pool_manager.py | _none_ | 0 | 0 |
| run_governance_facade.py | _none_ | 0 | 0 |


---

## PIN-507 Law 5 Remediation (2026-02-01)

**Handlers updated:** All 9 handler files (18 handler classes) in `hoc_spine/orchestrator/handlers/` now use explicit dispatch maps instead of `getattr()` reflection. Zero `asyncio.iscoroutinefunction()` calls remain. Mixed sync/async handlers use split `async_dispatch` / `sync_dispatch` dictionaries. Dispatch maps are local per-call (built after lazy facade import inside `execute()`). Error semantics (codes, messages, exception mapping) preserved exactly.

**Files:** `controls_handler.py`, `api_keys_handler.py`, `overview_handler.py`, `account_handler.py`, `analytics_handler.py`, `activity_handler.py`, `incidents_handler.py`, `integrations_handler.py`, `logs_handler.py`, `policies_handler.py`

---

## PIN-519 System Run Introspection (2026-02-03) — COMPLETE

**Problem Solved:** Three TODOs in `activity_facade.py` returned empty/stub data for cross-domain queries.

**Solution:** L4 coordinators mediate cross-domain queries, Activity L5 delegates to them.

**New coordinators:**

| Coordinator | Purpose | Cross-domain Sources | Status |
|-------------|---------|----------------------|--------|
| `run_evidence_coordinator.py` | Composes cross-domain impact for a run | incidents, policies, controls | ✅ |
| `run_proof_coordinator.py` | Verifies run integrity via trace HASH_CHAIN | logs (traces_store) | ✅ |
| `signal_feedback_coordinator.py` | Queries signal feedback from audit ledger | logs (audit_ledger_read_driver) | ✅ |

**Bridge extensions:**

| Bridge | New Capability | Status |
|--------|----------------|--------|
| `incidents_bridge.py` | `incidents_for_run_capability()` | ✅ |
| `policies_bridge.py` | `policy_evaluations_capability()` | ✅ |
| `controls_bridge.py` | `limit_breaches_capability()` | ✅ |
| `logs_bridge.py` | `traces_store_capability()`, `audit_ledger_read_capability()` | ✅ |

**Protocol Types (run_introspection_protocols.py):**
- `RunEvidenceResult`, `RunProofResult`, `SignalFeedbackResult`
- `IntegrityVerificationResult`, `TraceSummary`, `TraceStepSummary`
- `IncidentSummary`, `PolicyEvaluationSummary`, `LimitHitSummary`, `DecisionSummary`

**Consumers:** `ActivityFacade.get_run_evidence()`, `ActivityFacade.get_run_proof()`, `ActivityFacade._get_signal_feedback()`

**Integrity Model:**
```python
INTEGRITY_CONFIG = {"model": "HASH_CHAIN", "trust_boundary": "SYSTEM", "storage": "POSTGRES"}
```

---

## PIN-520 Wiring Audit (2026-02-03)

**Coordinators wired and exported from `coordinators/__init__.py`:**

| Coordinator | Purpose | Import Path | Dependencies |
|-------------|---------|-------------|--------------|
| `CanaryCoordinator` | Scheduled canary validation runs | `from app.hoc.cus.hoc_spine.orchestrator.coordinators import CanaryCoordinator` | `analytics.L5_engines.canary_engine.run_canary()` |
| `ExecutionCoordinator` | Pre-execution scoping + job lifecycle | `from app.hoc.cus.hoc_spine.orchestrator.coordinators import ExecutionCoordinator` | `controls.L6_drivers.scoped_execution_driver`, `logs.L6_drivers.job_execution_driver` |
| `ReplayCoordinator` | Deterministic replay enforcement | `from app.hoc.cus.hoc_spine.orchestrator.coordinators import ReplayCoordinator` | `logs.L6_drivers.replay_driver.get_replay_enforcer()` |

**Usage:**

```python
# Canary validation (scheduler/cron)
coordinator = CanaryCoordinator()
result = await coordinator.run(sample_count=100, drift_threshold=0.2)

# Scoped execution (job handlers)
coordinator = ExecutionCoordinator()
scope = await coordinator.create_scope(incident_id, action, intent, max_cost_usd)
result = await coordinator.execute_with_scope(scope_id, action, incident_id, parameters)

# Replay enforcement (trace replay)
coordinator = ReplayCoordinator()
result = await coordinator.enforce_step(step, execute_fn, tenant_id)
result = await coordinator.enforce_trace(trace, step_executor, tenant_id)
```

**ExecutionCoordinator → JobExecutor Integration:**

The `CoordinatedJobExecutor` class in `execution/job_executor.py` wires ExecutionCoordinator capabilities:

| JobExecutor Method | Coordinator Method | Purpose |
|-------------------|-------------------|---------|
| `execute_job_with_audit()` | `emit_audit_created/completed/failed()` | Audit trail |
| `execute_scoped_job()` | `create_scope()`, `execute_with_scope()` | P2FC-4 risk gates |
| `get_retry_advice()` | `should_retry()` | Advisory retry (EXEC-006 compliant) |
| `track_job_progress()` | `track_progress()` | Progress tracking |

```python
from app.hoc.cus.hoc_spine.orchestrator.execution.job_executor import create_coordinated_executor

executor = create_coordinated_executor()
result = await executor.execute_job_with_audit(job_id, tenant_id, contract_id, steps, handler)
```

## PIN-521 Shared Services Extraction (2026-02-03)

### New hoc_spine/services Files

**Purpose:** Domain-agnostic shared utilities extracted from domain L5_engines for L6 driver import compliance.

| Service | Purpose | Consumers |
|---------|---------|-----------|
| `costsim_config.py` | CostSim V2 configuration (env vars) | controls L6 drivers, analytics L5 engines |
| `costsim_metrics.py` | CostSim V2 Prometheus metrics | controls L6 drivers, analytics L5 engines |

### hoc_spine/services/__init__.py Exports

```python
# Alert delivery (PIN-520)
from app.hoc.cus.hoc_spine.services import AlertDeliveryAdapter, get_alert_delivery_adapter

# CostSim config (PIN-521)
from app.hoc.cus.hoc_spine.services import CostSimConfig, get_config

# CostSim metrics (PIN-521)
from app.hoc.cus.hoc_spine.services import CostSimMetrics, get_metrics
```

### Usage

```python
# For L6 drivers (compliant with layer rules)
from app.hoc.cus.hoc_spine.services.costsim_config import get_config
from app.hoc.cus.hoc_spine.services.costsim_metrics import get_metrics

config = get_config()
if config.v2_sandbox_enabled:
    metrics = get_metrics()
    metrics.record_drift(drift_score, verdict, tenant_id)
```

### CI Violations Fixed

| Category | Before | After | Change |
|----------|--------|-------|--------|
| L6_L5_ENGINE | 5 | 0 | -5 |
| L6_CROSS_DOMAIN | 4 | 1 | -3 |
| **Total** | 24 | 16 | -8 |

---

## PIN-521 Phase 4-5 Completion (2026-02-03)

### New Protocol: MCPAuditEmitterPort

**File:** `hoc_spine/schemas/protocols.py`

**Purpose:** Protocol for MCP audit event emission, enabling L5→L5 cross-domain dependency injection.

**Methods:**
- `emit_tool_requested(tenant_id, server_id, tool_name, run_id, input_params, trace_id) -> Any`
- `emit_tool_allowed(tenant_id, server_id, tool_name, run_id, policy_id, trace_id) -> Any`
- `emit_tool_denied(tenant_id, server_id, tool_name, run_id, deny_reason, policy_id, message, trace_id) -> Any`
- `emit_tool_started(tenant_id, server_id, tool_name, run_id, span_id, trace_id) -> Any`
- `emit_tool_completed(tenant_id, server_id, tool_name, run_id, output, duration_ms, span_id, trace_id) -> Any`
- `emit_tool_failed(tenant_id, server_id, tool_name, run_id, error_message, duration_ms, span_id, trace_id) -> Any`

**Implemented by:** `MCPAuditEmitter` (logs/L5_engines/audit_evidence.py)
**Consumed by:** `McpToolInvocationEngine` (integrations/L5_engines)

### New Coordinator Method: detect_only()

**File:** `hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py`

**Purpose:** Exposes detection capability via L4 without automatic incident escalation.

```python
async def detect_only(self, session: Any, tenant_id: str) -> list:
    """Run analytics detection only (no incident escalation)."""
    from app.hoc.cus.analytics.L5_engines.cost_anomaly_detector_engine import (
        run_anomaly_detection,
    )
    return await run_anomaly_detection(session, tenant_id)
```

**Usage:**
```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.anomaly_incident_coordinator import (
    get_anomaly_incident_coordinator,
)

coordinator = get_anomaly_incident_coordinator()

# Detection only (no escalation)
anomalies = await coordinator.detect_only(session, tenant_id)

# Detection with escalation
result = await coordinator.detect_and_ingest(session, tenant_id)
```

### Final CI Status (PIN-521 Complete)

| Phase | Violations Fixed | Method |
|-------|------------------|--------|
| 1 | 8 | L5_schemas extraction, hoc_spine/services |
| 2 | 1 | TraceStorePort Protocol |
| 3 | 4 | CI allowlist (Protocol injection pending) |
| 4 | 1 | MCPAuditEmitterPort Protocol |
| 5 | 1 | Route via L4 coordinator (detect_only) |
| 6 | 9 | Delete orphaned legacy services |
| **Total** | **24** | |

**CI Status:** ✅ All checks passed. 0 blocking violations.

### Phase 6: Legacy Services Deletion

9 orphaned files in `app/services/` deleted (zero callers, zero imports):
- governance_signal_service.py
- cus_credential_service.py
- external_response_service.py
- founder_action_write_service.py
- worker_write_service_async.py
- recovery_write_service.py
- ops_write_service.py
- worker_registry_service.py
- ops_incident_service.py

---

## PIN-520 Phase 1 Handler & Bridge Extensions (2026-02-03)

**Problem Solved:** workers.py directly imported L5 engines for moat availability checks and L6 drivers for evidence capture, violating L2->L4->L5/L6 layer rules.

**Solution:** New handlers and bridge capabilities absorb these operations, routing them through L4.

### New Handlers

| Handler | Operation | Purpose | Documentation |
|---------|-----------|---------|---------------|
| `LogsCaptureHandler` | `logs.capture` | Evidence capture at run creation | [logs_handler.md](logs_handler.md) |
| `PoliciesHealthHandler` | `policies.health` | Moat availability checks | [policies_handler.md](policies_handler.md) |

### Bridge Extensions

| Bridge | New Capability | Purpose | Documentation |
|--------|----------------|---------|---------------|
| `logs_bridge.py` | `capture_driver_capability()` | Evidence capture via L6 driver | [logs_bridge.md](logs_bridge.md) |

### Usage

```python
# Evidence capture (via logs.capture handler)
result = await registry.execute(
    "logs.capture",
    tenant_id="t-123",
    session=session,
    params={
        "method": "capture_environment",
        "run_id": "run-456",
        "trace_id": "trace-789",
    }
)

# Moat availability check (via policies.health handler)
result = await registry.execute(
    "policies.health",
    tenant_id="t-123",
    session=session,
    params={}
)
# result.data = {"m20_policy": "available", "m9_failure_catalog": "available", ...}
```

### Evidence Architecture v1.0 Integration

The LogsCaptureHandler enables Evidence Architecture v1.0 compliance:
1. Environment evidence captured at run creation via L4->L6 path
2. No direct L2->L6 imports in workers.py
3. Proper layer compliance for evidence workflows
