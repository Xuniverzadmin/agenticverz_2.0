# HOC General Domain — Detailed Technical Report

**Domain:** `app/hoc/cus/general/`
**Date:** 2026-01-22
**Total Files:** ~38 Python files
**Total LOC:** ~10,500+
**Status:** Analysis Complete

---

## Table of Contents

1. [Facades](#1-facades-5-files-2961-loc)
2. [Runtime Engines](#2-runtime-engines-6-files-2650-loc)
3. [Lifecycle Engines](#3-lifecycle-engines-6-files-3440-loc)
4. [UI Engines](#4-ui-engines-1-file-717-loc)
5. [Workflow/Contracts Engines](#5-workflowcontracts-engines-1-file-708-loc)
6. [Controls Engines](#6-controls-engines-1-file-249-loc--temporary)
7. [Cross-Domain Engines](#7-cross-domain-engines-1-file-497-loc)
8. [Summary Statistics](#8-summary-statistics)
9. [Layer Violations](#9-layer-violations)
10. [Documented Invariants](#10-documented-invariants)

---

## 1. FACADES (5 files, ~2,961 LOC)

### facades/__init__.py (11 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Services |
| **Audience** | CUSTOMER |
| **Purpose** | Facade exports (placeholder) |
| **Imports** | None |
| **Exports** | None declared |

---

### facades/monitors_facade.py (535 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Audience** | CUSTOMER |
| **Role** | Centralized access to monitoring operations |
| **Reference** | GAP-120, GAP-121 |

**Imports:**
```python
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `MonitorType` | Enum | HTTP, TCP, DNS, HEARTBEAT, CUSTOM |
| `MonitorStatus` | Enum | HEALTHY, UNHEALTHY, DEGRADED, UNKNOWN |
| `CheckStatus` | Enum | SUCCESS, FAILURE, TIMEOUT, ERROR |
| `MonitorConfig` | dataclass | Monitor configuration record |
| `HealthCheckResult` | dataclass | Health check result record |
| `MonitorStatusSummary` | dataclass | Overall status summary |
| `MonitorsFacade` | class | Main facade with CRUD + check operations |

**Methods (MonitorsFacade):**

| Method | Description |
|--------|-------------|
| `create_monitor()` | Create a new monitor |
| `list_monitors()` | List monitors with filters |
| `get_monitor()` | Get specific monitor |
| `update_monitor()` | Update monitor configuration |
| `delete_monitor()` | Delete a monitor |
| `run_check()` | Execute health check |
| `get_check_history()` | Get check history |
| `get_status_summary()` | Get overall status |

**Factory:**
```python
def get_monitors_facade() -> MonitorsFacade
```

---

### facades/alerts_facade.py (671 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Centralized access to alert operations |
| **Reference** | GAP-110, GAP-111, GAP-124 |

**Imports:**
```python
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `AlertSeverity` | Enum | INFO, WARNING, ERROR, CRITICAL |
| `AlertStatus` | Enum | ACTIVE, ACKNOWLEDGED, RESOLVED |
| `AlertRule` | dataclass | Alert rule definition |
| `AlertEvent` | dataclass | Alert history entry |
| `AlertRoute` | dataclass | Alert routing rule |
| `AlertsFacade` | class | Main facade |

**Methods (AlertsFacade):**

| Category | Methods |
|----------|---------|
| Rules | `create_rule()`, `list_rules()`, `get_rule()`, `update_rule()`, `delete_rule()` |
| History | `list_history()`, `get_event()`, `acknowledge_event()`, `resolve_event()`, `trigger_alert()` |
| Routes | `create_route()`, `list_routes()`, `get_route()`, `delete_route()` |

**Factory:**
```python
def get_alerts_facade() -> AlertsFacade
```

---

### facades/scheduler_facade.py (544 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Centralized access to job scheduling |
| **Reference** | GAP-112 |

**Imports:**
```python
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `JobStatus` | Enum | ACTIVE, PAUSED, DISABLED |
| `JobRunStatus` | Enum | PENDING, RUNNING, COMPLETED, FAILED, SKIPPED |
| `ScheduledJob` | dataclass | Job definition |
| `JobRun` | dataclass | Job run history entry |
| `SchedulerFacade` | class | Main facade |

**Methods (SchedulerFacade):**

| Category | Methods |
|----------|---------|
| CRUD | `create_job()`, `list_jobs()`, `get_job()`, `update_job()`, `delete_job()` |
| Control | `trigger_job()`, `pause_job()`, `resume_job()` |
| History | `list_runs()`, `get_run()` |
| Private | `_calculate_next_run()` |

**Factory:**
```python
def get_scheduler_facade() -> SchedulerFacade
```

---

### facades/compliance_facade.py (510 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Centralized access to compliance verification |
| **Reference** | GAP-103 |

**Imports:**
```python
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `ComplianceScope` | Enum | ALL, DATA, POLICY, COST, SECURITY |
| `ComplianceStatus` | Enum | COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT, UNKNOWN |
| `ComplianceRule` | dataclass | Rule definition |
| `ComplianceViolation` | dataclass | Violation record |
| `ComplianceReport` | dataclass | Verification report |
| `ComplianceStatusInfo` | dataclass | Overall status |
| `ComplianceFacade` | class | Main facade |

**Methods (ComplianceFacade):**

| Category | Methods |
|----------|---------|
| Verification | `verify_compliance()`, `_check_rule_compliance()` |
| Reports | `list_reports()`, `get_report()` |
| Rules | `list_rules()`, `get_rule()` |
| Status | `get_compliance_status()` |

**Factory:**
```python
def get_compliance_facade() -> ComplianceFacade
```

---

### facades/lifecycle_facade.py (701 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Audience** | CUSTOMER |
| **Phase** | W4 |
| **Role** | Centralized access to lifecycle operations |
| **Reference** | GAP-131 to GAP-136 |

**Imports:**
```python
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `AgentState` | Enum | CREATED, STARTING, RUNNING, STOPPING, STOPPED, TERMINATED, ERROR |
| `RunState` | Enum | PENDING, RUNNING, PAUSED, COMPLETED, CANCELLED, FAILED |
| `AgentLifecycle` | dataclass | Agent lifecycle record |
| `RunLifecycle` | dataclass | Run lifecycle record |
| `LifecycleSummary` | dataclass | Summary stats |
| `LifecycleFacade` | class | Main facade |

**Methods (LifecycleFacade):**

| Category | Methods |
|----------|---------|
| Agent | `create_agent()`, `list_agents()`, `get_agent()`, `start_agent()`, `stop_agent()`, `terminate_agent()` |
| Run | `create_run()`, `list_runs()`, `get_run()`, `pause_run()`, `resume_run()`, `cancel_run()` |
| Summary | `get_summary()` |

**Factory:**
```python
def get_lifecycle_facade() -> LifecycleFacade
```

---

## 2. RUNTIME ENGINES (6 files, ~2,650 LOC)

### runtime/engines/governance_orchestrator.py (~800 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Orchestrates contract execution |
| **Reference** | PIN-292 |

**Key Classes:**
- `GovernanceOrchestrator` — Orchestrates only, does not execute
- `ContractActivationService` — Contract lifecycle
- `ExecutionOrchestrator` — Execution coordination
- `JobStateTracker` — State machine for jobs

---

### runtime/engines/transaction_coordinator.py (829 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Atomic cross-domain transaction coordinator |
| **Reference** | PIN-454, FIX-001 |

**Imports:**
```python
import logging, os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid
from sqlmodel import Session
from app.db.engine import get_engine
from app.events import get_publisher
from app.services.audit.*
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `TransactionPhase` | Enum | NOT_STARTED, INCIDENT_CREATED, POLICY_EVALUATED, TRACE_COMPLETED, COMMITTED, EVENTS_PUBLISHED, ROLLED_BACK, FAILED |
| `TransactionFailed` | Exception | phase, partial_results, cause |
| `DomainResult` | dataclass | domain, action, result_id, success, error, timestamp |
| `TransactionResult` | dataclass | run_id, incident_result, policy_result, trace_result, phase, events_published, duration_ms |
| `RollbackAction` | dataclass | domain, action, rollback_fn, result_id, executed |
| `RunCompletionTransaction` | class | Main coordinator |

**Methods (RunCompletionTransaction):**

| Method | Description |
|--------|-------------|
| `execute()` | Main entry point |
| `_create_incident()` | Create incident in transaction |
| `_create_policy_evaluation()` | Create policy evaluation |
| `_complete_trace()` | Complete trace |
| `_publish_events()` | Publish domain events |
| `_execute_rollback()` | Rollback on failure |

**Factory Functions:**
```python
def get_transaction_coordinator() -> RunCompletionTransaction
def create_transaction_coordinator(...) -> RunCompletionTransaction
```

---

### runtime/engines/phase_status_invariants.py (354 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engines |
| **Role** | Phase-status invariant enforcement from GovernanceConfig |
| **Reference** | GAP-051 |

**Imports:**
```python
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `InvariantCheckResult` | Enum | VALID, INVALID, ENFORCEMENT_DISABLED, UNKNOWN_PHASE |
| `PhaseStatusInvariantEnforcementError` | Exception | phase, status, allowed_statuses, enforcement_enabled |
| `InvariantCheckResponse` | dataclass | result, is_valid, enforcement_enabled, phase, status, allowed_statuses, message |
| `PhaseStatusInvariantChecker` | class | Main checker |

**Methods (PhaseStatusInvariantChecker):**

| Method | Description |
|--------|-------------|
| `from_governance_config()` | Factory from config |
| `get_allowed_statuses()` | Get allowed statuses for phase |
| `is_valid_combination()` | Check phase-status validity |
| `check()` | Check and return response |
| `ensure_valid()` | Check and raise if invalid |
| `should_allow_transition()` | Check transition allowance |

**Functions:**
```python
def check_phase_status_invariant(...) -> InvariantCheckResponse
def ensure_phase_status_invariant(...) -> None
```

**Constants:**
- `PHASE_STATUS_INVARIANTS` — Dict mapping phases to allowed statuses

---

### runtime/engines/plan_generation_engine.py (257 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine (System Truth) |
| **Role** | Plan generation domain logic |
| **Reference** | PIN-257 Phase R-2 |

**Imports:**
```python
import json, logging
from dataclasses import dataclass
from typing import Any
from app.memory import get_retriever
from app.planners import get_planner
from app.skills import get_skill_manifest
from app.utils.budget_tracker import get_budget_tracker
from app.utils.plan_inspector import validate_plan
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `PlanGenerationContext` | dataclass | agent_id, goal, run_id, agent_budget_cents |
| `PlanGenerationResult` | dataclass | plan, plan_json, steps, context_summary, memory_snippet_count, validation_valid, validation_warnings |
| `PlanGenerationEngine` | class | Main engine |

**Methods (PlanGenerationEngine):**

| Method | Description |
|--------|-------------|
| `generate(context)` | Generate plan, returns PlanGenerationResult |

**Factory:**
```python
def generate_plan_for_run(agent_id, goal, run_id) -> PlanGenerationResult
```

**Exports:**
```python
__all__ = ["PlanGenerationContext", "PlanGenerationResult", "PlanGenerationEngine", "generate_plan_for_run"]
```

---

### runtime/engines/constraint_checker.py (303 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engines |
| **Role** | Enforce MonitorConfig inspection constraints before logging |
| **Reference** | GAP-033 |

**Imports:**
```python
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `InspectionOperation` | Enum | LOG_PROMPT, LOG_RESPONSE, CAPTURE_PII, ACCESS_SECRET |
| `InspectionConstraintViolation` | dataclass | operation, constraint_field, constraint_value, message |
| `InspectionConstraintChecker` | class | Main checker |

**Methods (InspectionConstraintChecker):**

| Method | Description |
|--------|-------------|
| `from_monitor_config()` | Factory from MonitorConfig |
| `from_snapshot()` | Factory from snapshot dict |
| `is_allowed()` | Check if operation allowed |
| `check()` | Check and return violation if not allowed |
| `check_all()` | Check multiple operations |
| `get_allowed_operations()` | Get list of allowed operations |
| `get_denied_operations()` | Get list of denied operations |
| `to_dict()` | Convert to dictionary |

**Functions:**
```python
def check_inspection_allowed(operation, ...) -> bool
def get_constraint_violations(operations, ...) -> list[dict]
```

**Constants:**
- `OPERATION_TO_CONSTRAINT` — Maps operations to constraint field names

---

### runtime/engines/run_governance_facade.py (~500 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Run governance interface |

---

## 3. LIFECYCLE ENGINES (6 files, ~3,440 LOC)

### lifecycle/engines/base.py (310 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Stage Handler Protocol and Base Types |
| **Reference** | GAP-071-082 |

**Imports:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Protocol, Type, runtime_checkable
from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `StageStatus` | Enum | SUCCESS, FAILURE, PENDING, SKIPPED |
| `StageContext` | dataclass | Context passed to stage handlers |
| `StageResult` | dataclass | Result from stage execution |
| `StageHandler` | Protocol | Stage handler contract |
| `BaseStageHandler` | ABC | Base class for handlers |
| `StageRegistry` | class | Registry of stage handlers |

**StageResult Factory Methods:**

| Method | Description |
|--------|-------------|
| `StageResult.ok()` | Create successful result |
| `StageResult.fail()` | Create failure result |
| `StageResult.pending()` | Create pending (async) result |
| `StageResult.skipped()` | Create skipped result |

**StageRegistry Methods:**

| Method | Description |
|--------|-------------|
| `register()` | Register a handler |
| `get_handler()` | Get handler for state |
| `has_handler()` | Check if handler exists |
| `create_default()` | Create registry with all handlers |

**Design Invariant:**
```
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
```

---

### lifecycle/engines/onboarding.py (696 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Onboarding Stage Handlers (GAP-071 to GAP-077) |

**Imports:**
```python
import asyncio, hashlib, logging
from datetime import datetime
from typing import Optional
from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState
from .base import BaseStageHandler, StageContext, StageResult, StageStatus
```

**Classes (all extend BaseStageHandler):**

| Class | stage_name | handles_states | Reference |
|-------|------------|----------------|-----------|
| `RegisterHandler` | "register" | () | GAP-071 |
| `VerifyHandler` | "verify" | (DRAFT,) | GAP-072 |
| `IngestHandler` | "ingest" | (VERIFIED,) | GAP-073, GAP-159 |
| `IndexHandler` | "index" | (INGESTING,) | GAP-074, GAP-160 |
| `ClassifyHandler` | "classify" | (INDEXED,) | GAP-075, GAP-161 |
| `ActivateHandler` | "activate" | (PENDING_ACTIVATE,) | GAP-076 |
| `GovernHandler` | "govern" | (ACTIVE,) | GAP-077 |

**Each handler implements:**
- `validate(context) -> Optional[str]`
- `execute(context) -> StageResult`

---

### lifecycle/engines/offboarding.py (525 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Offboarding Stage Handlers (GAP-078 to GAP-082) |
| **Note** | Governance-controlled for GDPR/CCPA compliance |

**Imports:**
```python
import asyncio, hashlib, logging
from datetime import datetime
from typing import Optional
from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState
from .base import BaseStageHandler, StageContext, StageResult, StageStatus
```

**Classes (all extend BaseStageHandler):**

| Class | stage_name | handles_states | Reference |
|-------|------------|----------------|-----------|
| `DeregisterHandler` | "deregister" | (ACTIVE,) | GAP-078 |
| `VerifyDeactivateHandler` | "verify_deactivate" | (PENDING_DEACTIVATE,) | GAP-079 |
| `DeactivateHandler` | "deactivate" | (PENDING_DEACTIVATE,) | GAP-080 |
| `ArchiveHandler` | "archive" | (DEACTIVATED,) | GAP-081 |
| `PurgeHandler` | "purge" | (ARCHIVED,) | GAP-082 |

**Critical:** `PurgeHandler` requires `purge_approved=true` in context.

---

### lifecycle/engines/pool_manager.py (599 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Connection pool management |
| **Reference** | GAP-172 |

---

### lifecycle/engines/knowledge_plane.py (468 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Knowledge graph models |
| **Reference** | GAP-056 |

---

### lifecycle/engines/execution.py (1313 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Data/Index/Classify executors |
| **Reference** | GAP-159-161 |

---

## 4. UI ENGINES (1 file, 717 LOC)

### ui/engines/rollout_projection.py (717 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine (Projection) |
| **Role** | Read-only projection of audited truth |
| **Reference** | PIN-296 |

**Imports:**
```python
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `RolloutStage` | Enum | NOT_VISIBLE, PLANNED, INTERNAL, LIMITED, GENERAL |
| `BlastRadius` | dataclass (frozen) | tenant_count, customer_segment, region, estimated_users |
| `StabilizationWindow` | dataclass (frozen) | started_at, duration_hours, elapsed_hours, is_satisfied, remaining_hours |
| `ContractSummary` | dataclass (frozen) | contract_id, issue_id, title, eligibility_verdict, approved_by, approved_at, affected_capabilities |
| `ExecutionSummary` | dataclass (frozen) | job_id, status, started_at, completed_at, steps_executed, steps_succeeded |
| `AuditSummary` | dataclass (frozen) | audit_id, verdict, checks_passed, checks_failed, audited_at |
| `RolloutPlan` | dataclass (frozen) | current_stage, planned_stages, blast_radius, stabilization |
| `FounderRolloutView` | dataclass (frozen) | Full lineage projection for founders |
| `GovernanceCompletionReport` | dataclass (frozen) | Machine-generated completion artifact |
| `CustomerRolloutView` | dataclass (frozen) | Customer facts only |
| `RolloutProjectionService` | class | Main service |

**RolloutProjectionService Methods:**

| Method | Description |
|--------|-------------|
| `project_founder_view()` | Full lineage for founders |
| `generate_completion_report()` | Only if audit PASS |
| `project_customer_view()` | Facts only for customers |
| `can_advance_stage()` | Read-only check |

**Invariants:**
```
ROLLOUT-001: Projection is read-only
ROLLOUT-002: Stage advancement requires audit PASS
ROLLOUT-003: Stage advancement requires stabilization
ROLLOUT-004: No health degradation during rollout
ROLLOUT-005: Stages are monotonic
ROLLOUT-006: Customer sees only current stage facts
```

**Constants:**
- `PROJECTION_VERSION = "1.0.0"`
- `STAGE_ORDER` — Maps stages to numeric order

**Helper Functions:**
```python
def founder_view_to_dict(view) -> dict
def completion_report_to_dict(report) -> dict
```

---

## 5. WORKFLOW/CONTRACTS ENGINES (1 file, 708 LOC)

### workflow/contracts/engines/contract_service.py (708 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | System Contract state machine |
| **Reference** | PIN-291 |

**Imports:**
```python
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4
from app.models.contract import (
    TERMINAL_STATES, VALID_TRANSITIONS, AuditVerdict, ContractApproval,
    ContractImmutableError, ContractSource, ContractStatus, EligibilityVerdictData,
    InvalidTransitionError, MayNotVerdictError, RiskLevel, TransitionRecord, ValidatorVerdictData
)
from app.services.governance.eligibility_engine import EligibilityDecision, EligibilityVerdict
from app.services.governance.validator_service import ValidatorVerdict
```

**Classes:**

| Class | Type | Description |
|-------|------|-------------|
| `ContractState` | dataclass | In-memory contract state representation |
| `ContractStateMachine` | class | State machine enforcement |
| `ContractService` | class | Main service |

**ContractStateMachine Methods:**

| Method | Description |
|--------|-------------|
| `can_transition()` | Check if transition is valid |
| `validate_transition()` | Validate and raise errors if invalid |
| `transition()` | Execute state transition |

**ContractService Methods:**

| Method | Description |
|--------|-------------|
| `create_contract()` | Create contract (**MAY_NOT enforcement is ABSOLUTE**) |
| `approve()` | Approve contract (Founder Review Gate) |
| `reject()` | Reject contract |
| `activate()` | Activate contract (start execution) |
| `complete()` | Complete contract (audit passed) |
| `fail()` | Fail contract (job or audit failed) |
| `expire()` | Expire contract (TTL exceeded) |
| `is_terminal()` | Check if in terminal state |
| `is_approved()` | Check if approved |
| `can_approve()` | Check if can be approved |
| `get_valid_transitions()` | Get valid transitions from current state |

**Invariants (from SYSTEM_CONTRACT_OBJECT.md):**
```
CONTRACT-001: Status transitions must follow state machine
CONTRACT-002: APPROVED requires approved_by
CONTRACT-003: ACTIVE requires job exists
CONTRACT-004: COMPLETED requires audit_verdict = PASS
CONTRACT-005: Terminal states are immutable
CONTRACT-006: proposed_changes must validate schema
CONTRACT-007: confidence_score range [0,1]
```

**MAY_NOT Enforcement (PIN-291):**
```python
# This is mechanically un-overridable
if eligibility_verdict.decision == EligibilityDecision.MAY_NOT:
    raise MayNotVerdictError(eligibility_verdict.reason)
```

---

## 6. CONTROLS ENGINES (1 file, 249 LOC) — TEMPORARY

### controls/engines/guard_write_service.py (249 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Status** | **TEMPORARY** (Phase 2B) |
| **Role** | DB write delegation for Guard API |
| **Reference** | PIN-250 Phase 2B Batch 1 |

**Imports:**
```python
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import and_, select
from sqlmodel import Session
from app.models.killswitch import (
    Incident, IncidentEvent, IncidentSeverity, IncidentStatus, KillSwitchState, TriggerType
)
```

**Classes:**

| Class | Description |
|-------|-------------|
| `GuardWriteService` | DB write facade for Guard Console |

**Methods (GuardWriteService):**

| Category | Methods |
|----------|---------|
| KillSwitch | `get_or_create_killswitch_state()`, `freeze_killswitch()`, `unfreeze_killswitch()` |
| Incident | `acknowledge_incident()`, `resolve_incident()`, `create_demo_incident()` |

**Phase 2 Note:**
```
PHASE 2 NOTE:
This is a TEMPORARY AGGREGATE service for Phase 2 structural extraction.
It bundles KillSwitch, Incident, and IncidentEvent writes together.
Post-alignment (Phase 3+), this may split into:
  - KillSwitchWriteService
  - IncidentWriteService
Do NOT split during Phase 2.
```

---

## 7. CROSS-DOMAIN ENGINES (1 file, 497 LOC)

### cross-domain/engines/cross_domain.py (497 LOC)

| Property | Value |
|----------|-------|
| **Layer** | L4 — Domain Engine |
| **Role** | Mandatory cross-domain governance functions |
| **Reference** | design/CROSS_DOMAIN_GOVERNANCE.md |

**Imports:**
```python
import logging, uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session
from app.errors.governance import GovernanceError
from app.metrics import governance_incidents_created_total, governance_limit_breaches_recorded_total
from app.models.killswitch import Incident
from app.models.policy_control_plane import LimitBreach
```

**Doctrine:**
```
Rule 1: Governance must throw
Rule 2: No optional dependencies
Rule 3: Learning is downstream only
```

**Constants:**
- `ANOMALY_SEVERITY_MAP` — Maps anomaly severity to incident severity
- `ANOMALY_TRIGGER_TYPE_MAP` — Maps anomaly type to trigger type

**Async Functions:**

| Function | Description |
|----------|-------------|
| `create_incident_from_cost_anomaly()` | **MANDATORY** — Create incident from cost anomaly |
| `record_limit_breach()` | **MANDATORY** — Record limit breach |
| `table_exists()` | Helper — Check if table exists |

**Sync Functions:**

| Function | Description |
|----------|-------------|
| `create_incident_from_cost_anomaly_sync()` | For legacy sync code |
| `record_limit_breach_sync()` | For legacy sync code |

**Helpers:**
```python
def utc_now() -> datetime
def generate_uuid() -> str
```

---

## 8. SUMMARY STATISTICS

| Subdomain | Files | LOC | Key Components |
|-----------|-------|-----|----------------|
| **Facades** | 5 | ~2,961 | 5 facades, 5 factories |
| **Runtime** | 6 | ~2,650 | Transaction coordinator, Phase invariants, Plan generation, Constraint checker |
| **Lifecycle** | 6 | ~3,440 | 12 stage handlers, StageRegistry, base protocol |
| **UI** | 1 | 717 | RolloutProjectionService, 9 data classes |
| **Workflow/Contracts** | 1 | 708 | ContractService, ContractStateMachine |
| **Controls** | 1 | 249 | GuardWriteService (TEMPORARY) |
| **Cross-Domain** | 1 | 497 | 4 governance functions (async + sync) |
| **TOTAL** | ~38 | ~10,500+ | |

---

## 9. LAYER VIOLATIONS

| File | Declared Layer | Issue |
|------|----------------|-------|
| `engines/knowledge_sdk.py` | L2 | **MISPLACED** — L2 file in engines directory (should be in `app/api/` if truly L2) |

---

## 10. DOCUMENTED INVARIANTS

| Category | Count | Source | Examples |
|----------|-------|--------|----------|
| **Contract** | 7 | PIN-291 | CONTRACT-001 through CONTRACT-007 |
| **Rollout** | 6 | PIN-296 | ROLLOUT-001 through ROLLOUT-006 |
| **Stage Handler** | 1 | GAP-071-082 | "Dumb plugins" invariant |
| **Cross-Domain** | 3 | CROSS_DOMAIN_GOVERNANCE.md | "Governance must throw" doctrine |
| **Phase-Status** | Multiple | GAP-051 | Phase→Status mappings |

---

## 11. CROSS-DOMAIN DEPENDENCIES

| File | External Imports |
|------|------------------|
| `governance_orchestrator.py` | `app.models.contract.*` |
| `contract_service.py` | `app.models.contract.*`, `app.services.governance.*` |
| `cross_domain.py` | `app.models.incidents.*`, `app.services.policies.*` |
| `execution.py` | `app.services.connectors.*` |
| `transaction_coordinator.py` | `app.db.engine`, `app.events`, `app.services.audit.*` |

---

## 12. RECOMMENDED ACTIONS

### Immediate (Before Next Phase)

1. **Add governance contract** to `general/__init__.py`
2. **Document known issues** in domain contract
3. **Track** `guard_write_service.py` for Phase 3 split

### Near-Term (Phase 4+)

4. **Resolve** `knowledge_sdk.py` layer classification
5. **Begin extraction** of runtime subdomain
6. **Begin extraction** of lifecycle subdomain
7. **Begin extraction** of contracts subdomain

### Long-Term

8. **Complete domain split** per recommendation
9. **Remove** general domain once empty (or keep for cross-domain only)

---

## 13. REFERENCES

| Reference | Description |
|-----------|-------------|
| PIN-291 | Contract MAY_NOT enforcement |
| PIN-292 | Governance orchestrator design |
| PIN-296 | Rollout projection service |
| PIN-250 | Phase 2B extraction plan |
| PIN-257 | Plan generation design |
| PIN-454 | Transaction coordinator |
| GAP-019 | Alert-log linking |
| GAP-033 | Inspection constraints |
| GAP-051 | Phase-status invariants |
| GAP-056 | Knowledge plane model |
| GAP-071-082 | Lifecycle stages |
| GAP-083-085 | Knowledge SDK |
| GAP-103 | Compliance verification |
| GAP-110-124 | Alert APIs |
| GAP-112 | Scheduler API |
| GAP-120-121 | Monitor APIs |
| GAP-131-136 | Lifecycle APIs |
| GAP-159-161 | Execution engines |
| GAP-172 | Connection pool management |

---

## Changes Log

| Date | Change |
|------|--------|
| 2026-01-22 | Initial detailed report created |
| 2026-01-22 | All 38 files analyzed with imports, exports, classes, functions |
| 2026-01-22 | Documented 20+ invariants across 5 categories |
| 2026-01-22 | Identified 1 layer violation |
| 2026-01-22 | Documented cross-domain dependencies |
