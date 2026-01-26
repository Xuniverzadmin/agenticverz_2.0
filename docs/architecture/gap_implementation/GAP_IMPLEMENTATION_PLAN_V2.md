# Gap Implementation Plan v2 — Wiring & Integration

**Status:** IN PROGRESS
**Date:** 2026-01-21
**Last Updated:** 2026-01-21
**Reference:**
- `GAP_IMPLEMENTATION_PLAN_V1.md` (L4 Governance Kernel — GAP-001 to GAP-089)
- `GAP_WIRING_LEDGER_V1.md` (Gap Analysis & Dependencies)
**Author:** Systems Architect

---

## Implementation Status

| Phase | Status | Date | Notes |
|-------|--------|------|-------|
| **W0** | ✅ COMPLETE | 2026-01-21 | All 7 gaps + 4 invariants implemented |
| **W1** | ✅ COMPLETE | 2026-01-21 | All 11 gaps implemented |
| **W2** | ✅ COMPLETE | 2026-01-21 | All 10 gaps implemented |
| **W3** | ✅ COMPLETE | 2026-01-21 | All 10 gaps implemented |
| **W4** | 🔄 IN PROGRESS | 2026-01-21 | L2 APIs & SDK |

### W0 Completion Details

**Invariant Modules (INV-W0):**
| ID | Module | Location | Status |
|----|--------|----------|--------|
| INV-W0-001 | ExecutionContext | `app/core/execution_context.py` | ✅ |
| INV-W0-002 | KillSwitchGuard | `app/core/kill_switch_guard.py` | ✅ |
| INV-W0-003 | IdempotencyKey/Store | `app/core/idempotency.py` | ✅ |
| INV-W0-004 | FailureSemantics | `app/core/failure_semantics.py` | ✅ |

**W0 Gaps:**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-137 | RetrievalHook | `app/worker/hooks/retrieval_hook.py` | ✅ |
| GAP-138 | HallucinationHook | `app/worker/hooks/hallucination_hook.py` | ✅ |
| GAP-139 | LimitHook | `app/worker/hooks/limit_hook.py` | ✅ |
| GAP-140 | StepEnforcementHook | `app/worker/hooks/step_enforcement_hook.py` | ✅ |
| GAP-141 | MCPServerRegistry | `app/services/mcp/server_registry.py` | ✅ |
| GAP-142 | MCPPolicyMapper | `app/services/mcp/policy_mapper.py` | ✅ |
| GAP-143 | MCPAuditEmitter | `app/services/mcp/audit_evidence.py` | ✅ |

### W1 Completion Details

**Job Queue Infrastructure (GAP-154 to GAP-158):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-154 | APSchedulerExecutor | `app/services/scheduler/executor.py` | ✅ |
| GAP-155 | JobQueueWorker | `app/worker/job_queue_worker.py` | ✅ |
| GAP-156 | Job Retry Logic | `app/worker/job_execution.py` (RetryPolicy) | ✅ |
| GAP-157 | Job Progress Reporting | `app/worker/job_execution.py` (JobProgressTracker) | ✅ |
| GAP-158 | Job Audit Evidence | `app/worker/job_execution.py` (JobAuditEmitter) | ✅ |

**Real Execution Handlers (GAP-159 to GAP-161):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-159 | DataIngestionExecutor | `app/services/lifecycle_stages/execution.py` | ✅ |
| GAP-160 | IndexingExecutor | `app/services/lifecycle_stages/execution.py` | ✅ |
| GAP-161 | ClassificationExecutor | `app/services/lifecycle_stages/execution.py` | ✅ |

**Lifecycle Worker Orchestration (GAP-162 to GAP-164):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-162 | LifecycleWorker | `app/worker/lifecycle_worker.py` | ✅ |
| GAP-163 | LifecycleProgressManager | `app/worker/lifecycle_worker.py` | ✅ |
| GAP-164 | LifecycleRecoveryManager | `app/worker/lifecycle_worker.py` | ✅ |

**Key Integration Points:**
- IngestHandler, IndexHandler, ClassifyHandler now use real executors (not simulations)
- DataIngestionExecutor supports HTTP, SQL, File, and Vector connector types
- IndexingExecutor performs text chunking and embedding generation via VectorConnector
- ClassificationExecutor detects PII (email, phone, SSN, credit card, etc.) and determines sensitivity level
- LifecycleWorker orchestrates stage execution via JobQueueWorker with kill switch integration (INV-W0-002)
- LifecycleProgressManager tracks stage-level progress with ETA estimation
- LifecycleRecoveryManager implements exponential backoff retry with jitter

### W2 Completion Details

**Database Migrations (GAP-165 to GAP-170):**
| GAP | Table | Location | Status |
|-----|-------|----------|--------|
| GAP-165 | retrieval_evidence | `alembic/versions/113_t1_retrieval_evidence.py` | ✅ (pre-existing) |
| GAP-166 | audit_events | `alembic/versions/116_w2_audit_events.py` | ✅ |
| GAP-167 | policy_snapshots | `alembic/versions/110_policy_snapshots_v2.py` | ✅ (pre-existing) |
| GAP-168 | budget_envelopes | `alembic/versions/117_w2_budget_envelopes.py` | ✅ |
| GAP-169 | knowledge_planes | `alembic/versions/118_w2_knowledge_planes.py` | ✅ |
| GAP-170 | mcp_servers, mcp_tools | `alembic/versions/119_w2_mcp_servers.py` | ✅ |

**Security & Infrastructure Services (GAP-171 to GAP-174):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-171 | Credential Vault Integration | `app/services/credentials/` | ✅ |
| GAP-172 | Connection Pool Management | `app/services/pools/` | ✅ |
| GAP-173 | IAM Integration | `app/services/iam/` | ✅ |
| GAP-174 | Execution Sandboxing | `app/services/sandbox/` | ✅ |

**Key Features Implemented:**
- **Credential Vault (GAP-171):** Abstract CredentialVault interface with HashiCorp Vault and EnvCredentialVault implementations. Supports API_KEY, OAUTH, DATABASE, BEARER_TOKEN, BASIC_AUTH, SSH_KEY, CERTIFICATE credential types. High-level CredentialService with expiration tracking and rotation support.
- **Connection Pool Manager (GAP-172):** ConnectionPoolManager for database (asyncpg), Redis, and HTTP (httpx) pools. Features health checking, per-tenant connection limits, graceful shutdown, and metrics collection.
- **IAM Integration (GAP-173):** IAMService with multi-provider identity resolution (Clerk, Auth0, OIDC, System, API_KEY). Role-based access control with permission expansion. IdentityChain for resolver chaining.
- **Execution Sandboxing (GAP-174):** ProcessSandboxExecutor (rlimit-based) and ContainerSandboxExecutor (Docker/Podman). Resource limits (CPU, memory, time, processes). Network policies (NONE, LOCAL, RESTRICTED, FULL). Policy-based execution with quota management.

### W3 Completion Details

**Vector Store Adapters (GAP-144 to GAP-146):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-144 | Pinecone Adapter | `app/adapters/vector_stores/pinecone_adapter.py` | ✅ |
| GAP-145 | Weaviate Adapter | `app/adapters/vector_stores/weaviate_adapter.py` | ✅ |
| GAP-146 | PGVector Production Adapter | `app/adapters/vector_stores/pgvector_adapter.py` | ✅ |

**File Storage Adapters (GAP-147 to GAP-148):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-147 | S3 Adapter | `app/adapters/file_storage/s3_adapter.py` | ✅ |
| GAP-148 | GCS Adapter | `app/adapters/file_storage/gcs_adapter.py` | ✅ |

**Serverless Adapters (GAP-149 to GAP-150):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-149 | AWS Lambda Adapter | `app/adapters/serverless/lambda_adapter.py` | ✅ |
| GAP-150 | Cloud Functions Adapter | `app/adapters/serverless/cloud_functions_adapter.py` | ✅ |

**Notification Adapters (GAP-151 to GAP-153):**
| GAP | Module | Location | Status |
|-----|--------|----------|--------|
| GAP-151 | SMTP Adapter | `app/adapters/notifications/smtp_adapter.py` | ✅ |
| GAP-152 | Slack Adapter | `app/adapters/notifications/slack_adapter.py` | ✅ |
| GAP-153 | Webhook Retry Logic | `app/adapters/notifications/webhook_adapter.py` | ✅ |

**Key Features Implemented:**
- **Vector Store Adapters:** Abstract VectorStoreAdapter interface with Pinecone, Weaviate, and PGVector implementations. Batch upsert, metadata filtering, namespace support, query with score thresholds, and index statistics.
- **File Storage Adapters:** Abstract FileStorageAdapter interface with S3 and GCS implementations. Upload/download with streaming, presigned URLs, batch delete, copy operations, and metadata management.
- **Serverless Adapters:** Abstract ServerlessAdapter interface with Lambda and Cloud Functions implementations. Sync/async invocation, batch execution with semaphore, function info retrieval, and dry-run validation.
- **Notification Adapters:** Abstract NotificationAdapter interface with SMTP, Slack, and Webhook implementations. Rich message formatting, attachment support, thread replies (Slack), exponential backoff retry, circuit breaker pattern, and dead letter queue support.

---

## Executive Summary

This document provides the implementation plan for closing all wiring and integration gaps (GAP-090 to GAP-174) identified in the gap analysis. These gaps transform the governance kernel from "architecturally correct but operationally inert" to "shippable product."

**Prerequisite:** All 85 L4 governance gaps (GAP-001 to GAP-089) are COMPLETE with 2,007 passing tests.

### Key Metrics

| Tier | Gap Range | Count | Purpose | Timeline |
|------|-----------|-------|---------|----------|
| **W0** | GAP-137→143 | 7 | Execution Coupling | Week 1 |
| **W1** | GAP-154→164 | 11 | Job & Lifecycle Execution | Week 2-3 |
| **W2** | GAP-165→174 | 10 | Database & Security | Week 3-4 |
| **W3** | GAP-144→153 | 10 | Real Adapters | Week 4-5 |
| **W4** | GAP-090→136 | 47 | L2 APIs & SDK | Week 5-8 |
| **Total** | GAP-090→174 | **85** | | 8 weeks |

### Implementation Phases

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         IMPLEMENTATION SEQUENCE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PHASE 0: CRITICAL FOUNDATION (Week 1)                                         │
│  ═════════════════════════════════════                                          │
│  W0: Execution Coupling (7 gaps)                                               │
│      → RetrievalMediator runner hook (GAP-137)                                 │
│      → HallucinationDetector runner hook (GAP-138)                             │
│      → Monitor/Limit enforcement (GAP-139)                                     │
│      → MCP control plane (GAP-141→143)                                         │
│                                                                                 │
│  PHASE 1: EXECUTION INFRASTRUCTURE (Week 2-3)                                  │
│  ═════════════════════════════════════════════                                  │
│  W1: Job & Lifecycle Execution (11 gaps)                                       │
│      → APScheduler binding (GAP-154)                                           │
│      → Job queue worker (GAP-155)                                              │
│      → Real lifecycle handlers (GAP-159→161)                                   │
│      → Lifecycle worker orchestration (GAP-162→164)                            │
│                                                                                 │
│  PHASE 2: PERSISTENCE & SECURITY (Week 3-4)                                    │
│  ═══════════════════════════════════════════                                    │
│  W2: Database & Security (10 gaps)                                             │
│      → Alembic migrations T1→T4 (GAP-165→170)                                  │
│      → Credential vault (GAP-171)                                              │
│      → Connection pools (GAP-172)                                              │
│      → IAM & sandboxing (GAP-173→174)                                          │
│                                                                                 │
│  PHASE 3: REAL ADAPTERS (Week 4-5)                                             │
│  ═════════════════════════════════                                              │
│  W3: Real Adapters (10 gaps)                                                   │
│      → Vector stores (GAP-144→146)                                             │
│      → File storage (GAP-147→148)                                              │
│      → Serverless (GAP-149→150)                                                │
│      → Notifications (GAP-151→153)                                             │
│                                                                                 │
│  PHASE 4: API SURFACE & SDK (Week 5-8)                                         │
│  ═════════════════════════════════════                                          │
│  W4: L2 APIs & SDK (47 gaps)                                                   │
│      → T0 APIs (GAP-090→095)                                                   │
│      → T1 APIs (GAP-102→105)                                                   │
│      → T2 APIs (GAP-109→114)                                                   │
│      → T3 APIs (GAP-119→125)                                                   │
│      → T4 APIs (GAP-131→134)                                                   │
│      → SDK namespaces (GAP-096→098, 106→108, 115→118, 126→130, 135→136)       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Gate Invariant (IMPL-GATE-002)

> **No Phase N+1 work may begin until Phase N gate passes.**
>
> Phase gates are enforced by:
> 1. CI workflow blocks later phase PRs if current phase tests fail
> 2. Manual merge requires phase certification
> 3. PR labels must include `phase:wN-certified` before W(N+1) work

---

## Section 1: Implementation Standards

### 1.1 Wiring Script Template

Every wiring script MUST follow this declaration pattern:

```python
# Layer: L{x} — {Layer Name}
# Product: {product | system-wide}
# Wiring Type: {runner-hook | api-route | sdk-method | migration | adapter}
# Parent Gap: GAP-{xxx} (L4 service being wired)
# Reference: GAP-{yyy} (this wiring gap)

"""
Module: {module_name}
Purpose: {detailed purpose}

Wires:
    - Source: {L4 service location}
    - Target: {L2 route / L5 runner / SDK method}

Integration Points:
    - {list of integration points}

Test Coverage:
    - {list of test files}
"""
```

### 1.2 Test Requirements

Each wiring gap requires:

| Test Type | Location | Purpose |
|-----------|----------|---------|
| Unit Tests | `tests/wiring/w{N}/test_{gap}.py` | Isolated component tests |
| Integration Tests | `tests/integration/test_{feature}.py` | Cross-layer tests |
| E2E Tests | `tests/e2e/test_{flow}.py` | Full flow verification |

### 1.3 Acceptance Criteria Template

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| AC-{GAP}-01 | Primary functionality works | Unit test |
| AC-{GAP}-02 | Integration with parent gap | Integration test |
| AC-{GAP}-03 | Error handling | Negative test cases |
| AC-{GAP}-04 | Audit/logging | Log verification |
| AC-{GAP}-05 | No orphan — wired to caller | grep confirms import |

### 1.4 Execution Invariants (MANDATORY — Before W0)

These invariants are **foundational contracts** that ALL wiring gaps must respect. They are not gaps themselves but enforcement rules that govern gap implementation.

#### INV-W0-001: Execution Contract Definition (CRITICAL)

**Problem:** Without a unified ExecutionContext, services cannot coordinate tenant isolation, step tracking, or audit provenance.

**The Contract:**

Every service in the execution path MUST receive and propagate an `ExecutionContext`:

```python
# File: backend/app/core/execution_context.py
# Layer: L4 — Domain Engines
# Reference: INV-W0-001

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable execution context passed through all service calls.

    INVARIANT: All services MUST:
    1. Accept ExecutionContext as first parameter (or via dependency injection)
    2. Propagate context to all downstream calls
    3. Never mutate context (frozen=True)
    4. Include context in all audit emissions
    """
    # Identity
    tenant_id: str
    run_id: str
    step_id: Optional[str] = None

    # Execution metadata
    started_at: datetime = None
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    # Governance
    policy_snapshot_id: Optional[str] = None
    budget_envelope_id: Optional[str] = None

    # Audit provenance
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None  # human | machine | system

    def with_step(self, step_id: str) -> "ExecutionContext":
        """Create child context for a step."""
        return ExecutionContext(
            tenant_id=self.tenant_id,
            run_id=self.run_id,
            step_id=step_id,
            started_at=self.started_at,
            trace_id=self.trace_id,
            parent_span_id=self.step_id,
            policy_snapshot_id=self.policy_snapshot_id,
            budget_envelope_id=self.budget_envelope_id,
            actor_id=self.actor_id,
            actor_type=self.actor_type,
        )

    def to_audit_dict(self) -> dict:
        """Extract audit-relevant fields."""
        return {
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "trace_id": self.trace_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
        }
```

**Enforcement Rules:**

| Rule | Description | Verification |
|------|-------------|--------------|
| EC-001 | All L4 services accept ExecutionContext | grep for `ctx: ExecutionContext` in signatures |
| EC-002 | Context propagated to downstream calls | Code review + integration test |
| EC-003 | Audit emissions include context | Log verification |
| EC-004 | No context = BLOCK (fail-closed) | Unit test for missing context |

---

#### INV-W0-002: Kill-Switch Propagation to Jobs (HIGH)

**Problem:** If RuntimeSwitch disables a capability, running jobs must stop — not continue blindly.

**The Contract:**

Every job execution MUST check RuntimeSwitch:
1. **At start** — before any work begins
2. **On heartbeat** — every N seconds during execution
3. **On completion** — before committing results

```python
# File: backend/app/worker/kill_switch_guard.py
# Layer: L5 — Execution & Workers
# Reference: INV-W0-002

from typing import Optional
from app.services.config.runtime_switch import RuntimeSwitch, get_runtime_switch

class KillSwitchGuard:
    """
    Guard that enforces RuntimeSwitch checks during job execution.

    INVARIANT: Jobs MUST be killable at any point.
    """

    def __init__(
        self,
        capability: str,
        runtime_switch: Optional[RuntimeSwitch] = None,
        heartbeat_interval_seconds: int = 30,
    ):
        self._capability = capability
        self._switch = runtime_switch or get_runtime_switch()
        self._heartbeat_interval = heartbeat_interval_seconds
        self._last_check = None

    async def check_or_abort(self, job_id: str) -> bool:
        """
        Check if capability is enabled. Returns True if OK, raises if killed.

        Usage:
            guard = KillSwitchGuard("lifecycle.ingest")
            await guard.check_or_abort(job_id)  # At start

            while processing:
                await guard.heartbeat_check(job_id)  # During
                ...

            await guard.check_or_abort(job_id)  # Before commit
        """
        is_enabled = await self._switch.is_enabled(self._capability)

        if not is_enabled:
            from app.services.scheduler import get_job_scheduler
            scheduler = get_job_scheduler()

            await scheduler.abort_job(
                job_id=job_id,
                reason=f"RuntimeSwitch disabled: {self._capability}",
                abort_type="kill_switch",
            )

            raise JobKilledException(
                job_id=job_id,
                capability=self._capability,
                reason="RuntimeSwitch disabled capability during execution",
            )

        return True

    async def heartbeat_check(self, job_id: str) -> bool:
        """Check on heartbeat interval. No-op if interval not elapsed."""
        import time
        now = time.time()

        if self._last_check is None or (now - self._last_check) >= self._heartbeat_interval:
            self._last_check = now
            return await self.check_or_abort(job_id)

        return True

class JobKilledException(Exception):
    """Raised when a job is killed by RuntimeSwitch."""
    def __init__(self, job_id: str, capability: str, reason: str):
        self.job_id = job_id
        self.capability = capability
        self.reason = reason
        super().__init__(f"Job {job_id} killed: {reason}")
```

**Integration Pattern (Required in W1 Gaps):**

```python
# In GAP-155 JobQueueWorker._process_job():
async def _process_job(self, worker_id: int, job_data: bytes) -> None:
    job = json.loads(job_data)
    job_id = job.get("job_id")
    capability = job.get("capability", "job.default")

    guard = KillSwitchGuard(capability)

    try:
        # Check at start
        await guard.check_or_abort(job_id)

        # Process with heartbeat checks
        async for progress in self._execute_with_progress(job):
            await guard.heartbeat_check(job_id)
            yield progress

        # Check before commit
        await guard.check_or_abort(job_id)

        await self._commit_result(job_id)

    except JobKilledException:
        # Already aborted — just log
        logger.warning(f"Job {job_id} killed by RuntimeSwitch")
```

**Enforcement Rules:**

| Rule | Description | Verification |
|------|-------------|--------------|
| KS-001 | All job handlers use KillSwitchGuard | grep for `KillSwitchGuard` in handlers |
| KS-002 | Heartbeat check every 30s | Timer verification in tests |
| KS-003 | Killed jobs do not commit | Integration test with switch toggle |
| KS-004 | Kill events audited | Audit log verification |

---

#### INV-W0-003: Idempotency & Replay Guarantees (HIGH)

**Problem:** Network failures, restarts, and retries can cause duplicate job execution. Without idempotency, side effects multiply.

**The Contract:**

Job execution MUST be idempotent by `(job_id, plane_id)`:

```python
# File: backend/app/worker/idempotency.py
# Layer: L5 — Execution & Workers
# Reference: INV-W0-003

from typing import Optional
from datetime import datetime, timedelta
import hashlib

class IdempotencyKey:
    """
    Idempotency key for job execution.

    INVARIANT: Same (job_id, plane_id) MUST produce same result.
    """

    def __init__(self, job_id: str, plane_id: str):
        self.job_id = job_id
        self.plane_id = plane_id
        self._key = self._compute_key()

    def _compute_key(self) -> str:
        """Compute stable idempotency key."""
        payload = f"{self.job_id}:{self.plane_id}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    @property
    def key(self) -> str:
        return self._key

class IdempotencyStore:
    """
    Store for tracking idempotent job executions.

    Uses Redis with TTL for distributed idempotency.
    """

    def __init__(self, redis_client, ttl_hours: int = 24):
        self._redis = redis_client
        self._ttl = timedelta(hours=ttl_hours)

    async def check_and_acquire(
        self,
        idem_key: IdempotencyKey,
    ) -> tuple[bool, Optional[dict]]:
        """
        Check if job was already executed.

        Returns:
            (is_new, cached_result)
            - (True, None): First execution, lock acquired
            - (False, result): Already executed, return cached result
        """
        key = f"idem:{idem_key.key}"

        # Try to acquire lock
        acquired = await self._redis.set(
            key,
            "processing",
            nx=True,  # Only set if not exists
            ex=int(self._ttl.total_seconds()),
        )

        if acquired:
            return (True, None)

        # Check if completed or still processing
        value = await self._redis.get(key)
        if value == "processing":
            # Still processing — wait or raise
            raise JobAlreadyProcessingException(idem_key)

        # Return cached result
        import json
        return (False, json.loads(value))

    async def mark_complete(
        self,
        idem_key: IdempotencyKey,
        result: dict,
    ) -> None:
        """Mark job as complete with result."""
        import json
        key = f"idem:{idem_key.key}"

        await self._redis.set(
            key,
            json.dumps(result),
            ex=int(self._ttl.total_seconds()),
        )

    async def mark_failed(
        self,
        idem_key: IdempotencyKey,
        allow_retry: bool = True,
    ) -> None:
        """Mark job as failed. Optionally allow retry."""
        key = f"idem:{idem_key.key}"

        if allow_retry:
            # Delete key to allow retry
            await self._redis.delete(key)
        else:
            # Mark as permanently failed
            await self._redis.set(
                key,
                '{"status": "permanently_failed"}',
                ex=int(self._ttl.total_seconds()),
            )

class JobAlreadyProcessingException(Exception):
    """Raised when attempting to process a job already in progress."""
    pass
```

**Integration Pattern (Required in W1 Gaps):**

```python
# In lifecycle handler:
async def execute(self, context: StageContext) -> StageResult:
    idem_key = IdempotencyKey(
        job_id=context.job_id,
        plane_id=context.plane_id,
    )

    idem_store = get_idempotency_store()

    is_new, cached_result = await idem_store.check_and_acquire(idem_key)

    if not is_new:
        logger.info(f"Returning cached result for {idem_key.key}")
        return StageResult.from_dict(cached_result)

    try:
        result = await self._do_work(context)
        await idem_store.mark_complete(idem_key, result.to_dict())
        return result

    except Exception as e:
        await idem_store.mark_failed(idem_key, allow_retry=True)
        raise
```

**Enforcement Rules:**

| Rule | Description | Verification |
|------|-------------|--------------|
| IDEM-001 | All state-mutating jobs use IdempotencyKey | grep for `IdempotencyKey` |
| IDEM-002 | Duplicate calls return cached result | Unit test with same key |
| IDEM-003 | Failed jobs can retry (unless permanent) | Retry test |
| IDEM-004 | TTL prevents unbounded growth | Redis key expiry check |

---

#### INV-W0-004: Customer-Visible Failure Semantics (MEDIUM)

**Problem:** Customers cannot distinguish between "try again later" and "this will never work" without explicit failure categories.

**The Contract:**

All customer-visible failures MUST be categorized:

```python
# File: backend/app/core/failure_semantics.py
# Layer: L4 — Domain Engines
# Reference: INV-W0-004

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class FailureCategory(Enum):
    """
    Customer-visible failure categories.

    TRANSIENT: Retry may succeed (network, rate limit, temporary outage)
    PERMANENT: Retry will not succeed (invalid input, missing resource)
    POLICY: Governance blocked (policy violation, budget exceeded)
    """
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    POLICY = "policy"

@dataclass
class CustomerFailure:
    """
    Structured failure for customer-visible errors.

    SDK and API responses MUST use this structure.
    """
    category: FailureCategory
    code: str  # Machine-readable error code
    message: str  # Human-readable message
    retry_after_seconds: Optional[int] = None  # Only for TRANSIENT
    details: Optional[dict] = None

    def to_sdk_response(self) -> dict:
        """Convert to SDK response format."""
        response = {
            "success": False,
            "error": {
                "category": self.category.value,
                "code": self.code,
                "message": self.message,
            }
        }

        if self.category == FailureCategory.TRANSIENT and self.retry_after_seconds:
            response["error"]["retry_after_seconds"] = self.retry_after_seconds

        if self.details:
            response["error"]["details"] = self.details

        return response

    @classmethod
    def transient(
        cls,
        code: str,
        message: str,
        retry_after: int = 60,
    ) -> "CustomerFailure":
        """Create a transient failure (retry may help)."""
        return cls(
            category=FailureCategory.TRANSIENT,
            code=code,
            message=message,
            retry_after_seconds=retry_after,
        )

    @classmethod
    def permanent(
        cls,
        code: str,
        message: str,
        details: Optional[dict] = None,
    ) -> "CustomerFailure":
        """Create a permanent failure (retry will not help)."""
        return cls(
            category=FailureCategory.PERMANENT,
            code=code,
            message=message,
            details=details,
        )

    @classmethod
    def policy(
        cls,
        code: str,
        message: str,
        policy_id: Optional[str] = None,
    ) -> "CustomerFailure":
        """Create a policy failure (governance blocked)."""
        return cls(
            category=FailureCategory.POLICY,
            code=code,
            message=message,
            details={"policy_id": policy_id} if policy_id else None,
        )

# Standard error codes
class ErrorCodes:
    # Transient
    RATE_LIMITED = "rate_limited"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"

    # Permanent
    INVALID_INPUT = "invalid_input"
    RESOURCE_NOT_FOUND = "resource_not_found"
    INVALID_STATE = "invalid_state"
    UNSUPPORTED_OPERATION = "unsupported_operation"

    # Policy
    POLICY_VIOLATION = "policy_violation"
    BUDGET_EXCEEDED = "budget_exceeded"
    CAPABILITY_DISABLED = "capability_disabled"
    TENANT_SUSPENDED = "tenant_suspended"
```

**SDK Response Pattern:**

```python
# In SDK facade (GAP-083 to GAP-085):
class SDKResult:
    def __init__(
        self,
        success: bool,
        data: Optional[dict] = None,
        failure: Optional[CustomerFailure] = None,
    ):
        self.success = success
        self.data = data
        self.failure = failure

    def to_dict(self) -> dict:
        if self.success:
            return {"success": True, "data": self.data}
        else:
            return self.failure.to_sdk_response()

# Usage in SDK:
async def register(self, ...) -> SDKResult:
    try:
        result = await self._manager.register(...)
        return SDKResult(success=True, data=result)
    except PolicyViolationError as e:
        return SDKResult(
            success=False,
            failure=CustomerFailure.policy(
                code=ErrorCodes.POLICY_VIOLATION,
                message=str(e),
                policy_id=e.policy_id,
            )
        )
    except RateLimitError as e:
        return SDKResult(
            success=False,
            failure=CustomerFailure.transient(
                code=ErrorCodes.RATE_LIMITED,
                message="Rate limit exceeded",
                retry_after=e.retry_after,
            )
        )
```

**Enforcement Rules:**

| Rule | Description | Verification |
|------|-------------|--------------|
| FS-001 | All SDK methods return SDKResult | Type check |
| FS-002 | All failures have category | No raw exceptions in responses |
| FS-003 | TRANSIENT includes retry_after | Schema validation |
| FS-004 | POLICY includes policy context | Log verification |

---

### 1.5 Invariant Enforcement Summary

| Invariant | Phase | Integration Points |
|-----------|-------|-------------------|
| INV-W0-001 (ExecutionContext) | W0 | All hooks (GAP-137→143) |
| INV-W0-002 (KillSwitch) | W1 | Job worker (GAP-154, 155), Lifecycle (GAP-159→164) |
| INV-W0-003 (Idempotency) | W1 | Job worker (GAP-155), Lifecycle (GAP-159→164) |
| INV-W0-004 (FailureSemantics) | W4 | SDK facade (GAP-083→085), APIs (GAP-090→136) |

**Gate Invariant (IMPL-GATE-003):**

> **No gap implementation may proceed without demonstrating compliance with applicable invariants.**

Verification: Each gap's acceptance criteria MUST include invariant compliance tests.

---

## Section 2: Phase W0 — Execution Coupling (7 gaps)

**Gate:** No execution, lifecycle, or adapter work until W0 complete.
**Timeline:** Week 1
**Reference:** GAP_WIRING_LEDGER_V1.md Section 2

### W0-001: GAP-137 — RetrievalMediator Runner Hook

**Priority:** CRITICAL | **Parent Gap:** GAP-065

#### Problem Statement

The RetrievalMediator exists (GAP-065) but is not in the LLM execution path. LLM calls can bypass governance.

#### Script Declaration

```python
# File: backend/app/worker/hooks/retrieval_hook.py
# Layer: L5 — Execution & Workers
# Product: system-wide
# Wiring Type: runner-hook
# Parent Gap: GAP-065 (RetrievalMediator)
# Reference: GAP-137

"""
Module: retrieval_hook
Purpose: Wire RetrievalMediator as MANDATORY in LLM path.

Wires:
    - Source: app/services/mediation/retrieval_mediator.py
    - Target: app/worker/runner.py (step execution)

Invariant: NO BYPASS ALLOWED
    - All external data retrieval MUST go through mediator
    - Direct connector access from runner is FORBIDDEN
    - Audit trail for every retrieval operation
"""

from typing import Optional
from app.services.mediation.retrieval_mediator import (
    RetrievalMediator,
    RetrievalRequest,
    RetrievalResponse,
    get_retrieval_mediator,
)
from app.models.retrieval_evidence import RetrievalEvidence

class RetrievalHook:
    """
    Runner hook that enforces retrieval mediation.

    This hook intercepts all data retrieval requests in the runner
    and routes them through the RetrievalMediator.
    """

    def __init__(self, mediator: Optional[RetrievalMediator] = None):
        self._mediator = mediator or get_retrieval_mediator()

    async def before_retrieval(
        self,
        run_id: str,
        step_index: int,
        request: RetrievalRequest,
    ) -> RetrievalResponse:
        """
        Intercept retrieval request and route through mediator.

        INVARIANT: This method MUST be called for ALL retrievals.
        Direct connector access is a governance violation.
        """
        # Add execution context
        request.metadata["run_id"] = run_id
        request.metadata["step_index"] = step_index

        # Route through mediator (policy checks, audit, etc.)
        response = await self._mediator.execute(request)

        return response

# Singleton for runner access
_retrieval_hook: Optional[RetrievalHook] = None

def get_retrieval_hook() -> RetrievalHook:
    global _retrieval_hook
    if _retrieval_hook is None:
        _retrieval_hook = RetrievalHook()
    return _retrieval_hook
```

#### Runner Integration

```python
# File: backend/app/worker/runner.py (MODIFICATION)
# Location: Step execution loop

from app.worker.hooks.retrieval_hook import get_retrieval_hook

# In execute_step():
async def execute_step(self, step: PlanStep, cursor: ExecutionCursor) -> StepResult:
    # ... existing code ...

    # GAP-137: Route all retrievals through mediator
    if step.requires_retrieval:
        retrieval_hook = get_retrieval_hook()
        retrieval_response = await retrieval_hook.before_retrieval(
            run_id=str(cursor.run_id),
            step_index=cursor.step_index,
            request=step.retrieval_request,
        )

        if not retrieval_response.success:
            return StepResult.blocked(
                reason="retrieval_blocked",
                details=retrieval_response.blocked_reason,
            )

        step.retrieval_data = retrieval_response.data

    # ... continue with step execution ...
```

#### Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-137-01 | All retrievals go through mediator | Unit test with mock mediator |
| AC-137-02 | Direct connector access blocked | Negative test case |
| AC-137-03 | Audit evidence emitted | Log verification |
| AC-137-04 | Policy blocks propagate to step | Integration test |
| AC-137-05 | Hook is imported in runner.py | grep confirms import |

#### Unit Tests

```python
# File: backend/tests/wiring/w0/test_retrieval_hook.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.worker.hooks.retrieval_hook import RetrievalHook, get_retrieval_hook

class TestRetrievalHook:

    @pytest.fixture
    def mock_mediator(self):
        mediator = AsyncMock()
        mediator.execute.return_value = MagicMock(
            success=True,
            data={"result": "test"},
        )
        return mediator

    async def test_before_retrieval_routes_through_mediator(self, mock_mediator):
        """AC-137-01: All retrievals go through mediator"""
        hook = RetrievalHook(mediator=mock_mediator)

        request = MagicMock()
        request.metadata = {}

        response = await hook.before_retrieval(
            run_id="run-123",
            step_index=0,
            request=request,
        )

        mock_mediator.execute.assert_called_once_with(request)
        assert response.success is True

    async def test_context_added_to_request(self, mock_mediator):
        """Verify run context is added to request metadata"""
        hook = RetrievalHook(mediator=mock_mediator)

        request = MagicMock()
        request.metadata = {}

        await hook.before_retrieval(
            run_id="run-456",
            step_index=3,
            request=request,
        )

        assert request.metadata["run_id"] == "run-456"
        assert request.metadata["step_index"] == 3

    async def test_blocked_response_propagates(self, mock_mediator):
        """AC-137-04: Policy blocks propagate"""
        mock_mediator.execute.return_value = MagicMock(
            success=False,
            blocked_reason="policy_violation",
        )

        hook = RetrievalHook(mediator=mock_mediator)
        request = MagicMock()
        request.metadata = {}

        response = await hook.before_retrieval(
            run_id="run-789",
            step_index=0,
            request=request,
        )

        assert response.success is False
```

---

### W0-002: GAP-138 — HallucinationDetector Runner Hook

**Priority:** HIGH | **Parent Gap:** GAP-023

#### Problem Statement

HallucinationDetector exists (GAP-023) but is not wired to runner output. Hallucinations are detected but not consumed.

#### Script Declaration

```python
# File: backend/app/worker/hooks/hallucination_hook.py
# Layer: L5 — Execution & Workers
# Product: system-wide
# Wiring Type: runner-hook
# Parent Gap: GAP-023 (HallucinationDetector)
# Reference: GAP-138

"""
Module: hallucination_hook
Purpose: Wire HallucinationDetector to runner output annotation.

Wires:
    - Source: app/services/detection/hallucination_detector.py
    - Target: app/worker/runner.py (after LLM response)

Design: Non-blocking per INV-002 (HALLU-INV-001)
    - Detection runs async
    - Results annotate response
    - High confidence triggers alert (does not block)
"""

import asyncio
from typing import Optional
from dataclasses import dataclass
from app.services.detection.hallucination_detector import (
    HallucinationDetector,
    DetectionResult,
    get_hallucination_detector,
)

@dataclass
class HallucinationAnnotation:
    """Annotation added to LLM responses."""
    checked: bool = False
    confidence: float = 0.0
    flagged: bool = False
    details: Optional[dict] = None

class HallucinationHook:
    """
    Runner hook for hallucination detection on LLM outputs.

    INV-002: Non-blocking — detection does not halt execution.
    """

    def __init__(self, detector: Optional[HallucinationDetector] = None):
        self._detector = detector or get_hallucination_detector()

    async def after_llm_response(
        self,
        run_id: str,
        step_index: int,
        prompt: str,
        response: str,
        context: Optional[dict] = None,
    ) -> HallucinationAnnotation:
        """
        Check LLM response for hallucinations.

        Non-blocking: Returns annotation, does not raise.
        """
        try:
            result = await self._detector.check(
                prompt=prompt,
                response=response,
                context=context or {},
            )

            annotation = HallucinationAnnotation(
                checked=True,
                confidence=result.confidence,
                flagged=result.is_hallucination,
                details=result.to_dict(),
            )

            # Emit alert if high confidence hallucination
            if result.is_hallucination and result.confidence > 0.8:
                await self._emit_hallucination_alert(
                    run_id=run_id,
                    step_index=step_index,
                    result=result,
                )

            return annotation

        except Exception as e:
            # Non-blocking: log and return unchecked annotation
            import logging
            logging.getLogger(__name__).warning(
                f"Hallucination check failed: {e}"
            )
            return HallucinationAnnotation(checked=False)

    async def _emit_hallucination_alert(
        self,
        run_id: str,
        step_index: int,
        result: DetectionResult,
    ) -> None:
        """Emit alert for high-confidence hallucination."""
        from app.events import get_publisher

        await get_publisher().publish(
            "hallucination.detected",
            {
                "run_id": run_id,
                "step_index": step_index,
                "confidence": result.confidence,
                "evidence": result.evidence,
            },
        )

# Singleton
_hallucination_hook: Optional[HallucinationHook] = None

def get_hallucination_hook() -> HallucinationHook:
    global _hallucination_hook
    if _hallucination_hook is None:
        _hallucination_hook = HallucinationHook()
    return _hallucination_hook
```

#### Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-138-01 | LLM responses are checked | Unit test |
| AC-138-02 | Non-blocking per INV-002 | Error handling test |
| AC-138-03 | Annotations added to response | Integration test |
| AC-138-04 | High confidence triggers alert | Event emission test |
| AC-138-05 | Hook is imported in runner.py | grep confirms import |

---

### W0-003: GAP-139 — Monitor/Limit Runner Enforcement

**Priority:** HIGH | **Parent Gap:** GAP-053, GAP-054, GAP-055
**Type:** BUNDLE

#### Problem Statement

UsageMonitor and LimitEnforcer exist but are not enforced in runner step loop.

#### Script Declaration

```python
# File: backend/app/worker/hooks/limit_hook.py
# Layer: L5 — Execution & Workers
# Product: system-wide
# Wiring Type: runner-hook
# Parent Gap: GAP-053 (UsageMonitor), GAP-054 (HealthMonitor), GAP-055 (LimitEnforcer)
# Reference: GAP-139

"""
Module: limit_hook
Purpose: Enforce usage limits and monitor health in runner.

Wires:
    - Source: app/services/monitors/usage_monitor.py
    - Source: app/services/monitors/health_monitor.py
    - Source: app/services/limits/limit_enforcer.py
    - Target: app/worker/runner.py (step loop)

Enforcement Points:
    - Before step: Check limits, may block
    - After step: Record usage, update monitors
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

class LimitDecision(Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"

@dataclass
class LimitCheckResult:
    decision: LimitDecision
    limit_type: Optional[str] = None
    current_usage: Optional[float] = None
    max_allowed: Optional[float] = None
    message: Optional[str] = None

class LimitHook:
    """
    Runner hook for limit enforcement.
    """

    async def before_step(
        self,
        run_id: str,
        step_index: int,
        tenant_id: str,
        estimated_cost: float,
    ) -> LimitCheckResult:
        """
        Check limits before step execution.

        Returns:
            LimitCheckResult with ALLOW, WARN, or BLOCK decision.
        """
        # Import here to avoid circular dependency
        from app.services.limits import get_limit_enforcer

        enforcer = get_limit_enforcer()

        result = await enforcer.check_limits(
            tenant_id=tenant_id,
            operation="step_execution",
            estimated_cost=estimated_cost,
        )

        if result.exceeded:
            return LimitCheckResult(
                decision=LimitDecision.BLOCK,
                limit_type=result.limit_type,
                current_usage=result.current_usage,
                max_allowed=result.max_allowed,
                message=f"Limit exceeded: {result.limit_type}",
            )
        elif result.warning:
            return LimitCheckResult(
                decision=LimitDecision.WARN,
                limit_type=result.limit_type,
                current_usage=result.current_usage,
                max_allowed=result.max_allowed,
                message=f"Approaching limit: {result.limit_type}",
            )
        else:
            return LimitCheckResult(decision=LimitDecision.ALLOW)

    async def after_step(
        self,
        run_id: str,
        step_index: int,
        tenant_id: str,
        actual_cost: float,
        tokens_used: int,
        latency_ms: float,
    ) -> None:
        """
        Record usage after step execution.
        """
        from app.services.monitors import get_usage_monitor

        monitor = get_usage_monitor()

        await monitor.record_usage(
            tenant_id=tenant_id,
            run_id=run_id,
            step_index=step_index,
            cost=actual_cost,
            tokens=tokens_used,
            latency_ms=latency_ms,
        )

# Singleton
_limit_hook: Optional[LimitHook] = None

def get_limit_hook() -> LimitHook:
    global _limit_hook
    if _limit_hook is None:
        _limit_hook = LimitHook()
    return _limit_hook
```

---

### W0-004: GAP-140 — StepEnforcement Event Bus

**Priority:** MEDIUM | **Parent Gap:** GAP-016

*(Implementation details similar to above pattern)*

---

### W0-005: GAP-141 — MCP Server Registration

**Priority:** HIGH | **Parent Gap:** GAP-063

#### Script Declaration

```python
# File: backend/app/services/mcp/server_registry.py
# Layer: L4 — Domain Engines
# Product: system-wide
# Wiring Type: registry
# Parent Gap: GAP-063 (MCPConnector)
# Reference: GAP-141

"""
Module: server_registry
Purpose: Registry for external MCP servers.

Provides:
    - MCP server registration
    - Server capability discovery
    - Health monitoring
    - Tenant-scoped access control

Database Table: mcp_servers (requires GAP-170 migration)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

class MCPServerStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"

@dataclass
class MCPServer:
    """Registered MCP server."""
    server_id: str
    tenant_id: str
    name: str
    url: str
    status: MCPServerStatus
    capabilities: List[str]
    registered_at: datetime
    last_health_check: Optional[datetime] = None
    metadata: Optional[Dict] = None

@dataclass
class MCPTool:
    """Tool exposed by MCP server."""
    tool_id: str
    server_id: str
    name: str
    description: str
    input_schema: Dict
    requires_policy: bool = True

class MCPServerRegistry:
    """
    Registry for MCP servers and their tools.

    GAP-141: Provides registration API for external MCP servers.
    GAP-142: Tool→Policy mapping (separate gap).
    GAP-143: Audit evidence emission (separate gap).
    """

    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        self._tools: Dict[str, List[MCPTool]] = {}

    async def register_server(
        self,
        tenant_id: str,
        name: str,
        url: str,
        capabilities: Optional[List[str]] = None,
    ) -> MCPServer:
        """
        Register a new MCP server.

        Discovers tools via MCP protocol and registers them.
        """
        import uuid

        server_id = str(uuid.uuid4())

        # Discover capabilities via MCP handshake
        discovered_capabilities = await self._discover_capabilities(url)

        server = MCPServer(
            server_id=server_id,
            tenant_id=tenant_id,
            name=name,
            url=url,
            status=MCPServerStatus.PENDING,
            capabilities=capabilities or discovered_capabilities,
            registered_at=datetime.utcnow(),
        )

        # Discover and register tools
        tools = await self._discover_tools(server_id, url)

        self._servers[server_id] = server
        self._tools[server_id] = tools

        # Health check to activate
        await self._health_check(server_id)

        return server

    async def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID."""
        return self._servers.get(server_id)

    async def list_servers(self, tenant_id: str) -> List[MCPServer]:
        """List servers for tenant."""
        return [
            s for s in self._servers.values()
            if s.tenant_id == tenant_id
        ]

    async def get_tools(self, server_id: str) -> List[MCPTool]:
        """Get tools for server."""
        return self._tools.get(server_id, [])

    async def _discover_capabilities(self, url: str) -> List[str]:
        """Discover server capabilities via MCP protocol."""
        # TODO: Implement MCP handshake
        return ["tools", "resources"]

    async def _discover_tools(self, server_id: str, url: str) -> List[MCPTool]:
        """Discover tools exposed by server."""
        # TODO: Implement MCP tools/list call
        return []

    async def _health_check(self, server_id: str) -> bool:
        """Check server health and update status."""
        server = self._servers.get(server_id)
        if not server:
            return False

        # TODO: Implement health check
        server.status = MCPServerStatus.ACTIVE
        server.last_health_check = datetime.utcnow()

        return True

# Singleton
_mcp_registry: Optional[MCPServerRegistry] = None

def get_mcp_registry() -> MCPServerRegistry:
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPServerRegistry()
    return _mcp_registry
```

---

### W0-006: GAP-142 — MCP Tool→Policy Mapping

**Priority:** HIGH | **Parent Gap:** GAP-063, GAP-087
**Depends On:** GAP-141

*(Maps MCP tool invocations to policy gates)*

---

### W0-007: GAP-143 — MCP Audit Evidence

**Priority:** HIGH | **Parent Gap:** GAP-063, GAP-088
**Depends On:** GAP-141

*(Emits compliance-grade audit for MCP tool calls)*

---

### W0 Gate Criteria

| Criterion | Verification |
|-----------|--------------|
| All 7 W0 tests passing | `pytest tests/wiring/w0/ -v` |
| Runner imports all hooks | grep confirms imports |
| No direct connector access in runner | Code review |
| MCP registry functional | Integration test |

---

## Section 3: Phase W1 — Job & Lifecycle Execution (11 gaps)

**Gate:** No database migrations until W1 complete.
**Timeline:** Week 2-3
**Reference:** GAP_WIRING_LEDGER_V1.md Sections 4-5

### W1-001: GAP-154 — APScheduler Binding

**Priority:** CRITICAL | **Parent Gap:** GAP-039

#### Script Declaration

```python
# File: backend/app/services/scheduler/executor.py
# Layer: L4 — Domain Engines
# Product: system-wide
# Wiring Type: executor
# Parent Gap: GAP-039 (JobScheduler)
# Reference: GAP-154

"""
Module: executor
Purpose: Bind JobScheduler to APScheduler for actual execution.

Wires:
    - Source: app/services/scheduler/job_scheduler.py
    - Target: APScheduler library

Execution Modes:
    - Cron: Periodic execution via APScheduler cron trigger
    - One-time: Delayed execution via APScheduler date trigger
    - Immediate: Direct execution (no scheduling)
"""

import logging
from typing import Callable, Optional
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from app.services.scheduler.job_scheduler import (
    JobScheduler,
    ScheduledJob,
    JobScheduleType,
    JobStatus,
)

logger = logging.getLogger(__name__)

class APSchedulerExecutor:
    """
    Binds JobScheduler to APScheduler for real execution.
    """

    def __init__(self, job_scheduler: Optional[JobScheduler] = None):
        self._job_scheduler = job_scheduler
        self._ap_scheduler = AsyncIOScheduler()
        self._job_handlers: dict[str, Callable] = {}

    def register_handler(self, job_type: str, handler: Callable) -> None:
        """Register a handler for a job type."""
        self._job_handlers[job_type] = handler

    async def start(self) -> None:
        """Start the scheduler."""
        self._ap_scheduler.start()
        logger.info("APScheduler started")

        # Load existing jobs from job_scheduler
        if self._job_scheduler:
            jobs = await self._job_scheduler.list_pending_jobs()
            for job in jobs:
                await self._schedule_job(job)

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._ap_scheduler.shutdown()
        logger.info("APScheduler stopped")

    async def schedule(self, job: ScheduledJob) -> str:
        """Schedule a job for execution."""
        ap_job_id = await self._schedule_job(job)
        return ap_job_id

    async def _schedule_job(self, job: ScheduledJob) -> str:
        """Internal: Add job to APScheduler."""
        handler = self._job_handlers.get(job.job_type)
        if not handler:
            raise ValueError(f"No handler for job type: {job.job_type}")

        if job.schedule.schedule_type == JobScheduleType.CRON:
            trigger = CronTrigger.from_crontab(job.schedule.cron_expression)
        elif job.schedule.schedule_type == JobScheduleType.ONE_TIME:
            trigger = DateTrigger(run_date=job.schedule.run_at)
        else:
            # Immediate — run now
            trigger = DateTrigger(run_date=datetime.utcnow())

        ap_job = self._ap_scheduler.add_job(
            self._execute_job,
            trigger=trigger,
            args=[job.job_id, handler],
            id=job.job_id,
            name=job.name,
        )

        logger.info(f"Scheduled job {job.job_id} with trigger {trigger}")
        return ap_job.id

    async def _execute_job(self, job_id: str, handler: Callable) -> None:
        """Execute a scheduled job."""
        logger.info(f"Executing job {job_id}")

        try:
            # Update status to running
            if self._job_scheduler:
                await self._job_scheduler.update_status(job_id, JobStatus.RUNNING)

            # Execute handler
            await handler(job_id)

            # Update status to completed
            if self._job_scheduler:
                await self._job_scheduler.update_status(job_id, JobStatus.COMPLETED)

            logger.info(f"Job {job_id} completed")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            if self._job_scheduler:
                await self._job_scheduler.update_status(
                    job_id,
                    JobStatus.FAILED,
                    error=str(e),
                )

# Singleton
_executor: Optional[APSchedulerExecutor] = None

def get_scheduler_executor() -> APSchedulerExecutor:
    global _executor
    if _executor is None:
        from app.services.scheduler import JobScheduler
        _executor = APSchedulerExecutor(JobScheduler())
    return _executor
```

---

### W1-002: GAP-155 — Job Queue Worker

**Priority:** CRITICAL | **Parent Gap:** GAP-039

```python
# File: backend/app/worker/job_queue_worker.py
# Layer: L5 — Execution & Workers
# Product: system-wide
# Wiring Type: worker
# Parent Gap: GAP-039 (JobScheduler)
# Reference: GAP-155

"""
Module: job_queue_worker
Purpose: Background worker that processes job queue.

Uses Redis for job queue persistence.
Supports:
    - Job pickup from queue
    - Concurrent execution (configurable workers)
    - Dead letter queue for failed jobs
    - Graceful shutdown
"""

import asyncio
import logging
from typing import Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class JobQueueWorker:
    """
    Background worker for processing scheduled jobs.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        queue_name: str = "aos:job_queue",
        max_workers: int = 4,
    ):
        self._redis_url = redis_url
        self._queue_name = queue_name
        self._max_workers = max_workers
        self._redis: Optional[redis.Redis] = None
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the worker."""
        self._redis = await redis.from_url(self._redis_url)
        self._running = True

        # Start worker tasks
        for i in range(self._max_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._tasks.append(task)

        logger.info(f"JobQueueWorker started with {self._max_workers} workers")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        self._running = False

        # Wait for tasks to complete
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        if self._redis:
            await self._redis.close()

        logger.info("JobQueueWorker stopped")

    async def enqueue(self, job_id: str, job_data: dict) -> None:
        """Add job to queue."""
        import json
        await self._redis.rpush(
            self._queue_name,
            json.dumps({"job_id": job_id, **job_data}),
        )

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop — pick and process jobs."""
        while self._running:
            try:
                # Blocking pop with timeout
                result = await self._redis.blpop(
                    self._queue_name,
                    timeout=1,
                )

                if result:
                    _, job_data = result
                    await self._process_job(worker_id, job_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

    async def _process_job(self, worker_id: int, job_data: bytes) -> None:
        """Process a single job."""
        import json

        try:
            job = json.loads(job_data)
            job_id = job.get("job_id")

            logger.info(f"Worker {worker_id} processing job {job_id}")

            # Execute job via scheduler executor
            from app.services.scheduler.executor import get_scheduler_executor
            executor = get_scheduler_executor()

            handler = executor._job_handlers.get(job.get("job_type"))
            if handler:
                await handler(job_id)
            else:
                logger.warning(f"No handler for job {job_id}")

        except Exception as e:
            logger.error(f"Job processing failed: {e}")
            # Move to dead letter queue
            await self._redis.rpush(
                f"{self._queue_name}:dead_letter",
                job_data,
            )
```

---

### W1-003 to W1-005: GAP-156, GAP-157, GAP-158

*(Job retry logic, progress reporting, audit evidence — following same pattern)*

---

### W1-006: GAP-159 — IngestHandler Real Execution

**Priority:** CRITICAL | **Parent Gap:** GAP-073

```python
# File: backend/app/services/lifecycle_stages/onboarding.py (MODIFICATION)
# Location: IngestHandler.execute method

"""
GAP-159: Replace _simulate_ingestion with real data source reads.

Wires:
    - Source: Customer data source (via ConnectorRegistry)
    - Target: Internal storage for indexing

Requires:
    - GAP-171 (Credential Vault) for source credentials
    - GAP-147/148 (Storage Adapters) for file sources
"""

async def execute(self, context: StageContext) -> StageResult:
    """
    Execute REAL data ingestion.
    """
    try:
        config = context.config or {}
        source_type = config.get("source_type")
        source_config = config.get("source_config", {})

        # Get connector for source type
        from app.services.connectors import get_connector_registry
        registry = get_connector_registry()

        connector = await registry.get_connector(
            connector_type=source_type,
            tenant_id=context.tenant_id,
        )

        if not connector:
            return StageResult.fail(
                message=f"No connector for source type: {source_type}",
                error_code="CONNECTOR_NOT_FOUND",
            )

        # Get credentials from vault
        from app.services.credentials import get_credential_vault
        vault = get_credential_vault()

        credentials = await vault.get_credentials(
            tenant_id=context.tenant_id,
            credential_id=source_config.get("credential_id"),
        )

        # Execute ingestion
        ingestion_result = await connector.ingest(
            config=source_config,
            credentials=credentials,
            progress_callback=self._progress_callback,
        )

        if ingestion_result.success:
            return StageResult.ok(
                message="Ingestion complete",
                records_ingested=ingestion_result.records,
                bytes_processed=ingestion_result.bytes,
                ingested_at=datetime.now(timezone.utc).isoformat(),
            )
        else:
            return StageResult.fail(
                message=f"Ingestion failed: {ingestion_result.error}",
                error_code="INGESTION_FAILED",
            )

    except Exception as e:
        logger.error(f"IngestHandler failed: {e}")
        return StageResult.fail(
            message=f"Ingestion error: {str(e)}",
            error_code="INGEST_ERROR",
        )

async def _progress_callback(self, progress: float, message: str) -> None:
    """Report ingestion progress."""
    # GAP-163: Progress tracking
    pass
```

---

### W1-007 to W1-011: GAP-160 to GAP-164

*(IndexHandler real execution, ClassifyHandler real execution, lifecycle worker orchestration, progress tracking, failure recovery — following same pattern)*

---

### W1 Gate Criteria

| Criterion | Verification |
|-----------|--------------|
| All 11 W1 tests passing | `pytest tests/wiring/w1/ -v` |
| APScheduler starts with app | Startup log verification |
| Job queue worker processes jobs | Integration test |
| Lifecycle handlers execute real operations | E2E test with mock sources |

---

## Section 4: Phase W2 — Database & Security (10 gaps)

**Gate:** No real adapters until W2 complete.
**Timeline:** Week 3-4
**Reference:** GAP_WIRING_LEDGER_V1.md Sections 6-7

### W2-001: GAP-165 — T1 Evidence Migration

**Priority:** HIGH | **Parent Gap:** GAP-058

```python
# File: backend/alembic/versions/xxxx_add_retrieval_evidence.py
# Layer: L6 — Platform Substrate
# Reference: GAP-165

"""
Add retrieval_evidence table for T1 Evidence.

Revision ID: xxxx
Revises: previous_revision
Create Date: 2026-01-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = 'xxxx_retrieval_evidence'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'retrieval_evidence',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', UUID(as_uuid=True), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('connector_type', sa.String(64), nullable=False),
        sa.Column('source_id', sa.String(256), nullable=True),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('response_hash', sa.String(64), nullable=False),
        sa.Column('bytes_retrieved', sa.BigInteger(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('policy_applied', sa.String(64), nullable=True),
        sa.Column('redaction_applied', sa.Boolean(), default=False),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.Index('ix_retrieval_evidence_run_id', 'run_id'),
        sa.Index('ix_retrieval_evidence_tenant_id', 'tenant_id'),
        sa.Index('ix_retrieval_evidence_created_at', 'created_at'),
    )

def downgrade() -> None:
    op.drop_table('retrieval_evidence')
```

---

### W2-002 to W2-006: GAP-166 to GAP-170

*(Similar Alembic migrations for T2-T4 tables)*

---

### W2-007: GAP-171 — Credential Vault Integration

**Priority:** CRITICAL | **Parent Gap:** GAP-040, GAP-059-063

```python
# File: backend/app/services/credentials/vault.py
# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-171

"""
Module: vault
Purpose: Credential vault integration for secure credential storage.

Supports:
    - HashiCorp Vault
    - AWS Secrets Manager
    - Environment variables (dev only)

Provides:
    - Secure credential storage
    - Credential rotation
    - Tenant isolation
    - Audit logging
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class VaultProvider(Enum):
    HASHICORP = "hashicorp"
    AWS_SECRETS = "aws_secrets"
    ENV = "env"  # Development only

@dataclass
class Credential:
    """Stored credential."""
    credential_id: str
    tenant_id: str
    name: str
    credential_type: str  # api_key, oauth, database, etc.
    # Actual secret values are NOT stored in this object
    # They are fetched on-demand from vault

class CredentialVault(ABC):
    """Abstract credential vault."""

    @abstractmethod
    async def store_credential(
        self,
        tenant_id: str,
        name: str,
        credential_type: str,
        secret_data: Dict[str, str],
    ) -> str:
        """Store credential, return credential_id."""
        pass

    @abstractmethod
    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[Dict[str, str]]:
        """Get credential secret data."""
        pass

    @abstractmethod
    async def delete_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> bool:
        """Delete credential."""
        pass

class HashiCorpVault(CredentialVault):
    """HashiCorp Vault implementation."""

    def __init__(self, vault_url: str, token: str):
        self._vault_url = vault_url
        self._token = token

    async def store_credential(
        self,
        tenant_id: str,
        name: str,
        credential_type: str,
        secret_data: Dict[str, str],
    ) -> str:
        """Store credential in Vault."""
        import uuid
        import httpx

        credential_id = str(uuid.uuid4())
        path = f"secret/data/aos/{tenant_id}/{credential_id}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._vault_url}/v1/{path}",
                headers={"X-Vault-Token": self._token},
                json={
                    "data": {
                        "name": name,
                        "type": credential_type,
                        **secret_data,
                    }
                },
            )
            response.raise_for_status()

        logger.info(f"Stored credential {credential_id} for tenant {tenant_id}")
        return credential_id

    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[Dict[str, str]]:
        """Get credential from Vault."""
        import httpx

        path = f"secret/data/aos/{tenant_id}/{credential_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._vault_url}/v1/{path}",
                    headers={"X-Vault-Token": self._token},
                )
                response.raise_for_status()

                data = response.json()
                return data.get("data", {}).get("data", {})

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def delete_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> bool:
        """Delete credential from Vault."""
        import httpx

        path = f"secret/metadata/aos/{tenant_id}/{credential_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self._vault_url}/v1/{path}",
                headers={"X-Vault-Token": self._token},
            )
            return response.status_code == 204

# Factory
def get_credential_vault() -> CredentialVault:
    """Get credential vault based on configuration."""
    import os

    provider = os.getenv("CREDENTIAL_VAULT_PROVIDER", "env")

    if provider == "hashicorp":
        return HashiCorpVault(
            vault_url=os.getenv("VAULT_URL", "http://localhost:8200"),
            token=os.getenv("VAULT_TOKEN", ""),
        )
    elif provider == "aws_secrets":
        # TODO: Implement AWS Secrets Manager
        raise NotImplementedError("AWS Secrets Manager not yet implemented")
    else:
        # Development: Use environment variables
        return EnvCredentialVault()

class EnvCredentialVault(CredentialVault):
    """Development-only: Credentials from environment."""

    async def store_credential(self, *args, **kwargs) -> str:
        raise NotImplementedError("Cannot store credentials in env vault")

    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[Dict[str, str]]:
        import os
        # Look for AOS_CRED_{CREDENTIAL_ID} in environment
        env_key = f"AOS_CRED_{credential_id.upper().replace('-', '_')}"
        value = os.getenv(env_key)
        if value:
            return {"api_key": value}
        return None

    async def delete_credential(self, *args, **kwargs) -> bool:
        return False
```

---

### W2-008 to W2-010: GAP-172 to GAP-174

*(Connection pool management, IAM integration, execution sandboxing)*

---

### W2 Gate Criteria

| Criterion | Verification |
|-----------|--------------|
| All 10 W2 tests passing | `pytest tests/wiring/w2/ -v` |
| Migrations run successfully | `alembic upgrade head` |
| Credential vault stores/retrieves | Integration test |
| Connection pools are healthy | Health check |

---

## Section 5: Phase W3 — Real Adapters (10 gaps)

**Timeline:** Week 4-5
**Reference:** GAP_WIRING_LEDGER_V1.md Section 3

*(GAP-144 to GAP-153: Vector store adapters, file storage, serverless, notification delivery)*

---

## Section 6: Phase W4 — L2 APIs & SDK (47 gaps)

**Timeline:** Week 5-8
**Reference:** GAP_WIRING_LEDGER_V1.md Sections T0-T4

*(GAP-090 to GAP-136: All L2 API routes and SDK integrations)*

---

## Appendix A: Test Structure

```
backend/tests/
├── wiring/
│   ├── w0/                           # Execution Coupling (Week 1)
│   │   ├── test_retrieval_hook.py    # GAP-137
│   │   ├── test_hallucination_hook.py # GAP-138
│   │   ├── test_limit_hook.py        # GAP-139
│   │   ├── test_enforcement_bus.py   # GAP-140
│   │   ├── test_mcp_registry.py      # GAP-141
│   │   ├── test_mcp_policy.py        # GAP-142
│   │   └── test_mcp_audit.py         # GAP-143
│   ├── w1/                           # Job & Lifecycle (Week 2-3)
│   │   ├── test_apscheduler.py       # GAP-154
│   │   ├── test_job_queue.py         # GAP-155
│   │   ├── test_job_retry.py         # GAP-156
│   │   ├── test_job_progress.py      # GAP-157
│   │   ├── test_job_audit.py         # GAP-158
│   │   ├── test_real_ingest.py       # GAP-159
│   │   ├── test_real_index.py        # GAP-160
│   │   ├── test_real_classify.py     # GAP-161
│   │   ├── test_lifecycle_worker.py  # GAP-162
│   │   ├── test_lifecycle_progress.py # GAP-163
│   │   └── test_lifecycle_recovery.py # GAP-164
│   ├── w2/                           # Database & Security (Week 3-4)
│   │   ├── test_migrations/          # GAP-165 to GAP-170
│   │   ├── test_credential_vault.py  # GAP-171
│   │   ├── test_connection_pool.py   # GAP-172
│   │   ├── test_iam.py               # GAP-173
│   │   └── test_sandbox.py           # GAP-174
│   ├── w3/                           # Real Adapters (Week 4-5)
│   │   ├── test_pinecone.py          # GAP-144
│   │   ├── test_weaviate.py          # GAP-145
│   │   ├── test_pgvector_prod.py     # GAP-146
│   │   ├── test_s3.py                # GAP-147
│   │   ├── test_gcs.py               # GAP-148
│   │   ├── test_lambda.py            # GAP-149
│   │   ├── test_cloud_functions.py   # GAP-150
│   │   ├── test_smtp.py              # GAP-151
│   │   ├── test_slack.py             # GAP-152
│   │   └── test_webhook_retry.py     # GAP-153
│   └── w4/                           # L2 APIs & SDK (Week 5-8)
│       ├── api/                      # L2 route tests
│       └── sdk/                      # SDK integration tests
└── integration/
    └── wiring/                       # Cross-phase integration tests
```

---

## Appendix B: Reference Documents

| Document | Purpose | Location |
|----------|---------|----------|
| GAP_IMPLEMENTATION_PLAN_V1.md | L4 Governance Kernel (GAP-001 to GAP-089) | `docs/architecture/` |
| GAP_WIRING_LEDGER_V1.md | Gap Analysis & Dependencies | `docs/architecture/` |
| DOMAINS_E2E_SCAFFOLD_V3.md | E2E Architecture | `docs/architecture/` |
| AOS_Domain_Architecture_Mental_Map.md | Domain Model | `docs/architecture/` |

---

## Appendix C: Minimum Shippable Product (MSP)

To reach 80% client integration coverage, complete these 19 CRITICAL gaps:

| Phase | Gaps | What It Enables |
|-------|------|-----------------|
| W0 | GAP-137 | RAG mediation works |
| W1 | GAP-154, 155, 159, 160, 162 | Jobs run, lifecycle works |
| W2 | GAP-170, 171 | Data persists, secrets secure |
| W3 | GAP-144/146, 147, 149 | Real connectors work |
| W4 | GAP-090, 091, 096, 131, 132, 135, 136 | API & SDK functional |

**Total MSP Gaps:** 19 of 85

---

## Appendix D: Execution Invariant Sources

The Section 1.4 invariants were identified from GPT analysis feedback on missing architectural elements:

| Invariant | GPT Finding | Priority | Resolution |
|-----------|-------------|----------|------------|
| INV-W0-001 | "Execution Contract Definition" — No unified context for tenant/run/step tracking | CRITICAL | Added ExecutionContext dataclass with propagation rules |
| INV-W0-002 | "Kill-Switch Propagation to Jobs" — Running jobs ignore RuntimeSwitch toggles | HIGH | Added KillSwitchGuard with start/heartbeat/commit checks |
| INV-W0-003 | "Idempotency & Replay Guarantees" — Duplicate execution causes duplicate side effects | HIGH | Added IdempotencyKey + IdempotencyStore with Redis backing |
| INV-W0-004 | "Customer-Visible Failure Semantics" — Customers cannot distinguish transient vs permanent failures | MEDIUM | Added FailureCategory enum + CustomerFailure dataclass |

**Integration Pattern:**

These invariants are NOT standalone gaps — they are contracts that govern how gaps are implemented:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INVARIANT → GAP RELATIONSHIP                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  INV-W0-001 (ExecutionContext)                                                 │
│  └── Must be passed through: GAP-137, 138, 139, 141-143 (W0 hooks)             │
│                                                                                 │
│  INV-W0-002 (KillSwitch)                                                       │
│  └── Must be checked in: GAP-154, 155 (APScheduler, JobQueue)                  │
│  └── Must be checked in: GAP-159-164 (Lifecycle handlers)                      │
│                                                                                 │
│  INV-W0-003 (Idempotency)                                                      │
│  └── Must be enforced in: GAP-155 (JobQueueWorker)                             │
│  └── Must be enforced in: GAP-159-164 (Lifecycle handlers)                     │
│                                                                                 │
│  INV-W0-004 (FailureSemantics)                                                 │
│  └── Must be used in: GAP-083-085 (SDK facade)                                 │
│  └── Must be used in: GAP-090-136 (L2 API responses)                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Validation Sequence:**

1. Implement invariant primitives (Section 1.4) as shared modules
2. For each gap implementation, verify invariant compliance in acceptance criteria
3. CI workflow validates invariant usage via grep patterns

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-21 | v2.0 | Systems Architect | Initial wiring implementation plan |
| 2026-01-21 | v2.1 | Systems Architect | Added Section 1.4 Execution Invariants (INV-W0-001 to INV-W0-004) from GPT analysis feedback |
| 2026-01-21 | v2.2 | Systems Architect | W1 COMPLETE: All 11 gaps implemented (GAP-154 to GAP-164) |
| 2026-01-21 | v2.3 | Systems Architect | W2 COMPLETE: All 10 gaps implemented (GAP-165 to GAP-174) - Database migrations, Credential Vault, Connection Pools, IAM, Sandboxing |
| 2026-01-21 | v2.4 | Systems Architect | W3 COMPLETE: All 10 gaps implemented (GAP-144 to GAP-153) - Vector Stores (Pinecone, Weaviate, PGVector), File Storage (S3, GCS), Serverless (Lambda, Cloud Functions), Notifications (SMTP, Slack, Webhook with retry) |

---

**End of Gap Implementation Plan v2.4**
