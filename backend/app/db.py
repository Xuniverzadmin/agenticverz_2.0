# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any (import-time lazy, runtime on-demand)
#   Execution: sync (connection pooled)
# Role: Database connection, SQLModel definitions, session management
# Callers: All services, API routes, workers
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Core Infrastructure

import os
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import AsyncGenerator, Optional

import sqlalchemy as sa
from sqlalchemy import JSON, Column
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, Session, SQLModel, create_engine


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime. Use instead of utc_now()."""
    return datetime.now(timezone.utc)


# =============================================================================
# Database Configuration (Lazy Initialization)
# =============================================================================
# IMPORT HYGIENE: No environment reads or engine creation at import time.
# All database resources are created lazily on first use.
# This prevents import failures and allows safe testing/linting.

_engine = None
_async_engine = None
_async_session_local = None


def get_database_url() -> str:
    """Get DATABASE_URL, raising RuntimeError only when actually needed."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return url


def get_engine():
    """Get or create the sync SQLAlchemy engine (lazy initialization)."""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        # Connection pool configuration - can be reduced via env vars for testing
        # PIN-276: Allow smaller pools in test environments to prevent exhaustion
        pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "30"))
        _engine = create_engine(
            database_url,
            echo=False,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,  # Verify connections before use
        )
    return _engine


def get_async_database_url() -> str:
    """
    Get async database URL for asyncpg.

    CANONICAL LOCATION: This is the ONLY place async URL conversion should happen.
    All other code must use this function or get_async_engine().

    asyncpg requires:
    - postgresql+asyncpg:// scheme
    - ssl as connect_args, not URL parameter
    """
    url = get_database_url()

    # Convert scheme
    if url.startswith("postgresql+asyncpg://"):
        async_url = url
    elif url.startswith("postgresql://"):
        async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        raise RuntimeError(f"Unsupported DATABASE_URL scheme: {url}")

    # Remove sslmode from URL (will be added as connect_args)
    # Handle both ?sslmode=require and &sslmode=require
    if "sslmode=require" in async_url:
        async_url = async_url.replace("?sslmode=require", "")
        async_url = async_url.replace("&sslmode=require", "")
        # Clean up trailing ? if no other params
        if async_url.endswith("?"):
            async_url = async_url[:-1]

    return async_url


def get_async_engine():
    """
    Get or create the async SQLAlchemy engine (lazy initialization).

    CANONICAL LOCATION: This is the ONLY place async engines should be created.
    All other code must use this function.
    """
    global _async_engine
    if _async_engine is None:
        async_url = get_async_database_url()
        original_url = get_database_url()

        # Determine if SSL is required
        needs_ssl = "sslmode=require" in original_url

        connect_args = {}
        if needs_ssl:
            connect_args["ssl"] = "require"

        # PIN-276: Allow smaller pools in test environments to prevent exhaustion
        pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        _async_engine = create_async_engine(
            async_url,
            echo=False,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=1800,
            connect_args=connect_args,
        )
    return _async_engine


def get_async_session_factory():
    """Get or create the async session factory (lazy initialization)."""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_local


# For backwards compat with existing code that uses 'engine' at module level,
# create a lazy proxy object
class _LazyEngine:
    """Lazy proxy for SQLAlchemy engine to avoid import-time initialization."""

    def __getattr__(self, name):
        return getattr(get_engine(), name)

    def __call__(self, *args, **kwargs):
        return get_engine()(*args, **kwargs)


engine = _LazyEngine()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session context manager for async endpoints.

    Usage:
        async with get_async_session() as session:
            result = await session.execute(...)

    NOTE: This is wrapped with @asynccontextmanager for use with `async with`.
    For FastAPI Depends(), use `get_async_session_dep()` instead.
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_session_dep() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async sessions.

    This is an async generator function (no @asynccontextmanager decorator)
    that works correctly with FastAPI's Depends() system.

    Usage in FastAPI:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session_dep)):
            result = await session.execute(...)
    """
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = Field(default=None)
    status: str = Field(default="active")  # active, paused, disabled, maintenance

    # Capabilities and configuration (JSON strings)
    capabilities_json: Optional[str] = Field(default=None, description="JSON: AgentCapabilities schema")
    planner_config_json: Optional[str] = Field(default=None, description="JSON: PlannerConfig schema")

    # Rate limits
    rate_limit_rpm: int = Field(default=60, description="Requests per minute limit")
    concurrent_runs_limit: int = Field(default=5, description="Max concurrent runs")

    # Budget tracking
    budget_cents: Optional[int] = Field(default=None, description="Total budget in cents")
    spent_cents: int = Field(default=0, description="Amount spent so far")
    budget_alert_threshold: int = Field(default=80, description="Alert at this % spent")

    # Ownership and multi-tenancy
    owner_id: Optional[str] = Field(default=None, index=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    tags_json: Optional[str] = Field(default=None, description="JSON array of tags")

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # SDSR: Synthetic data marking (PIN-370)
    is_synthetic: bool = Field(default=False, description="True if created by synthetic scenario injection")
    synthetic_scenario_id: Optional[str] = Field(default=None, description="Scenario ID for traceability")

    @property
    def remaining_budget_cents(self) -> Optional[int]:
        """Calculate remaining budget."""
        if self.budget_cents is None:
            return None
        return max(0, self.budget_cents - self.spent_cents)

    @property
    def budget_usage_percent(self) -> Optional[float]:
        """Calculate budget usage percentage."""
        if self.budget_cents is None or self.budget_cents == 0:
            return None
        return (self.spent_cents / self.budget_cents) * 100

    def is_budget_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        if self.budget_cents is None:
            return False
        return self.spent_cents >= self.budget_cents

    def should_alert_budget(self) -> bool:
        """Check if budget alert threshold is reached."""
        usage = self.budget_usage_percent
        if usage is None:
            return False
        return usage >= self.budget_alert_threshold


class Memory(SQLModel, table=True):
    __tablename__ = "memories"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    agent_id: str = Field(index=True)
    memory_type: str = Field(default="skill_result")  # skill_result, user_input, system, context
    text: str
    meta: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    agent_id: str = Field(index=True)

    # =========================================================================
    # Attribution Fields (Attribution as Run Invariant)
    # Per AOS_SDK_ATTRIBUTION_CONTRACT, RUN_VALIDATION_RULES, SDSR_ATTRIBUTION_INVARIANT
    # =========================================================================

    # actor_type: HUMAN | SYSTEM | SERVICE
    # Per RUN_VALIDATION_RULES R3: actor_type MUST be from closed set
    actor_type: str = Field(
        default="SYSTEM",
        description="Actor classification: HUMAN, SYSTEM, or SERVICE"
    )

    # actor_id: Human identity (only required for HUMAN actors)
    # Per RUN_VALIDATION_RULES R4: actor_id REQUIRED if actor_type=HUMAN
    # Per RUN_VALIDATION_RULES R5: actor_id MUST be NULL if actor_type=SYSTEM
    actor_id: Optional[str] = Field(
        default=None,
        description="Human actor identity (required for HUMAN, null for SYSTEM)"
    )

    # origin_system_id: Where the run originated
    # Per AOS_SDK_ATTRIBUTION_CONTRACT: origin_system_id is REQUIRED
    origin_system_id: str = Field(
        description="Originating system identifier for accountability (REQUIRED — no default)"
    )

    goal: str
    status: str = Field(default="queued")  # queued, running, succeeded, failed, retry
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)
    error_message: Optional[str] = None
    plan_json: Optional[str] = None
    tool_calls_json: Optional[str] = None

    # Idempotency support
    idempotency_key: Optional[str] = Field(
        default=None, index=True, description="Client-provided key for idempotent submissions"
    )

    # Parent run for reruns
    parent_run_id: Optional[str] = Field(default=None, index=True, description="Original run ID if this is a rerun")

    # Priority for queue ordering
    priority: int = Field(default=0, description="Higher = more urgent")

    # Tenant scoping
    tenant_id: Optional[str] = Field(default=None, index=True)

    # SDSR: Synthetic data marking (PIN-370)
    is_synthetic: bool = Field(default=False, description="True if created by synthetic scenario injection")
    synthetic_scenario_id: Optional[str] = Field(default=None, description="Scenario ID for traceability")

    # Timestamps
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=True))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=True))
    next_attempt_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=True))
    duration_ms: Optional[float] = None

    # Phase E FIX-02: Pre-computed authorization fields
    # Authorization is computed at submission (L2 → L4) and read at execution (L5 → L6)
    # This eliminates L5 → L4 import violation (VIOLATION-002, VIOLATION-003)
    authorization_decision: Optional[str] = Field(
        default="GRANTED",
        description="Auth decision: GRANTED, DENIED, PENDING_APPROVAL",
    )
    authorization_engine: Optional[str] = Field(
        default=None,
        description="L4 engine that evaluated: rbac_engine, approvals_engine, etc.",
    )
    authorization_context: Optional[str] = Field(
        default=None,
        description="JSON: {roles, permissions, resource, action, decision_reason}",
    )
    authorized_at: Optional[datetime] = Field(
        default=None,
        description="When authorization decision was computed (submission time)",
        sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=True),
    )
    authorized_by: Optional[str] = Field(
        default=None,
        description="Principal that authorized: user_id, api_key_id, system",
    )

    # =========================================================================
    # Governance Fields (BACKEND_REMEDIATION_PLAN: GAP-001, GAP-002, GAP-006)
    # Runtime governance for policy enforcement and violation tracking
    # =========================================================================

    # Policy snapshot reference (GAP-006)
    policy_snapshot_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Reference to PolicySnapshot captured at run start"
    )

    # Termination tracking (GAP-002, GAP-007)
    termination_reason: Optional[str] = Field(
        default=None,
        description="RunTerminationReason value: policy_block, budget_exceeded, etc."
    )
    stopped_at_step: Optional[int] = Field(
        default=None,
        description="Step index where run was stopped (if terminated early)"
    )
    violation_policy_id: Optional[str] = Field(
        default=None,
        description="ID of policy that caused violation (if terminated by policy)"
    )

    # =========================================================================
    # Observability Status (PIN-454 FIX-004: Observability Guard)
    # Tracks whether full tracing was available during run execution
    # =========================================================================

    observability_status: str = Field(
        default="FULL",
        description="Observability status: FULL, DEGRADED, NONE"
    )
    observability_error: Optional[str] = Field(
        default=None,
        description="Error message if observability was degraded"
    )

    # =========================================================================
    # O2 Schema Columns (PIN-411: Aurora Runtime Projections)
    # These columns are computed UPSTREAM and stored for read-only access.
    # /runs endpoint is READ-ONLY - no computation at query time.
    # =========================================================================

    # Lifecycle state (different from status - this is LIVE vs COMPLETED)
    state: str = Field(
        default="LIVE",
        description="Run lifecycle state: LIVE or COMPLETED"
    )

    # Project scope
    project_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Project scope (UUID)"
    )

    # Heartbeat for LIVE runs
    last_seen_at: Optional[datetime] = Field(
        default=None,
        description="Last heartbeat timestamp for LIVE runs"
        ,
        sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Source and provider
    source: str = Field(
        default="agent",
        description="Run initiator: agent, human, sdk"
    )
    provider_type: str = Field(
        default="anthropic",
        description="LLM provider: openai, anthropic, internal"
    )

    # Risk and health (computed upstream, stored here)
    risk_level: str = Field(
        default="NORMAL",
        description="Risk classification: NORMAL, NEAR_THRESHOLD, AT_RISK, VIOLATED"
    )
    latency_bucket: str = Field(
        default="OK",
        description="Latency classification: OK, SLOW, STALLED"
    )
    evidence_health: str = Field(
        default="FLOWING",
        description="Evidence capture health: FLOWING, DEGRADED, MISSING"
    )
    integrity_status: str = Field(
        default="UNKNOWN",
        description="Integrity verification: UNKNOWN, VERIFIED, DEGRADED, FAILED"
    )

    # Impact signals
    incident_count: int = Field(
        default=0,
        description="Count of incidents caused by this run"
    )
    policy_draft_count: int = Field(
        default=0,
        description="Count of policy drafts generated"
    )
    policy_violation: bool = Field(
        default=False,
        description="Whether run violated any policy"
    )

    # Cost tracking
    input_tokens: Optional[int] = Field(
        default=None,
        description="Input token count"
    )
    output_tokens: Optional[int] = Field(
        default=None,
        description="Output token count"
    )
    estimated_cost_usd: Optional[float] = Field(
        default=None,
        description="Estimated cost in USD"
    )

    # Expected latency for latency_bucket computation
    expected_latency_ms: Optional[int] = Field(
        default=None,
        description="Expected latency in ms (from policy/intent)"
    )


class Provenance(SQLModel, table=True):
    __tablename__ = "provenance"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    run_id: Optional[str] = Field(default=None, index=True)
    agent_id: str = Field(index=True)
    goal: str
    status: str = Field(default="completed")  # pending, running, completed, failed, partial
    plan_json: str
    tool_calls_json: str
    error_message: Optional[str] = None
    attempts: int = Field(default=1)
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None


# ============== Feature Flags (M5 Prep - DB-backed for multi-node) ==============


class FeatureFlag(SQLModel, table=True):
    """
    DB-backed feature flags for multi-node deployments.

    Replaces file-based feature_flags.json for production scale.
    Uses SELECT FOR UPDATE for safe concurrent access.
    """

    __tablename__ = "feature_flags"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True, description="Flag identifier")
    enabled: bool = Field(default=False, description="Whether flag is active")
    environment: str = Field(default="staging", index=True, description="staging/production")

    # Flag metadata
    description: Optional[str] = Field(default=None)
    owner: str = Field(default="platform", description="Team owning this flag")
    requires_signoff: bool = Field(default=False, description="Requires .m4_signoff artifact")

    # Rollout configuration
    rollout_percentage: int = Field(default=100, ge=0, le=100, description="Percentage rollout")
    rollout_tenant_ids_json: Optional[str] = Field(
        default=None, description="JSON array of tenant IDs for targeted rollout"
    )

    # Audit trail
    changed_by: Optional[str] = Field(default=None, description="User who last changed")
    git_sha: Optional[str] = Field(default=None, description="Git SHA when changed")
    config_hash: Optional[str] = Field(default=None, description="Config hash for provenance")
    rollback_to: Optional[str] = Field(default=None, description="Previous state for rollback")

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    enabled_at: Optional[datetime] = Field(default=None, description="When flag was enabled")
    disabled_at: Optional[datetime] = Field(default=None, description="When flag was disabled")

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "environment": self.environment,
            "description": self.description,
            "owner": self.owner,
            "requires_signoff": self.requires_signoff,
            "rollout_percentage": self.rollout_percentage,
            "changed_by": self.changed_by,
            "git_sha": self.git_sha,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============== Policy Approval Hierarchy (M5 Prep) ==============


class PolicyApprovalLevel(SQLModel, table=True):
    """
    Defines approval hierarchy for policy decisions.

    Levels (in escalation order):
    1. auto_approve - System auto-approves (rate limits, caching)
    2. pre_approved - Operator pre-configured approval
    3. agent_approve - Agent-level capability (within budget)
    4. manual_approve - Runtime human approval required
    5. owner_override - Owner/admin emergency override
    """

    __tablename__ = "policy_approval_levels"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    policy_type: str = Field(index=True, description="budget, rate_limit, capability, permission")
    approval_level: str = Field(
        default="auto_approve", description="auto_approve, pre_approved, agent_approve, manual_approve, owner_override"
    )

    # Scope
    tenant_id: Optional[str] = Field(default=None, index=True, description="Tenant scope (null=global)")
    agent_id: Optional[str] = Field(default=None, index=True, description="Agent scope (null=all)")
    skill_id: Optional[str] = Field(default=None, description="Skill scope (null=all)")

    # Thresholds for auto-approval
    auto_approve_max_cost_cents: Optional[int] = Field(default=None, description="Max cost for auto-approval (cents)")
    auto_approve_max_tokens: Optional[int] = Field(default=None, description="Max tokens for auto-approval")

    # Escalation config
    escalate_to: Optional[str] = Field(default=None, description="Next approval level if denied")
    escalation_timeout_seconds: int = Field(default=300, description="Timeout before auto-escalating")

    # Audit
    created_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "policy_type": self.policy_type,
            "approval_level": self.approval_level,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "auto_approve_max_cost_cents": self.auto_approve_max_cost_cents,
            "escalate_to": self.escalate_to,
        }


# ============== Approval Request (M5) ==============


class ApprovalRequest(SQLModel, table=True):
    """
    Persistent storage for policy approval requests.

    Implements a state machine:
    - pending -> approved (via approve action)
    - pending -> rejected (via reject action)
    - pending -> escalated (via timeout)
    - pending -> expired (via expiration)
    """

    __tablename__ = "approval_requests"

    id: str = Field(default_factory=lambda: f"apr_{uuid.uuid4().hex[:16]}", primary_key=True)

    # Correlation ID for idempotency
    correlation_id: Optional[str] = Field(
        default_factory=lambda: uuid.uuid4().hex, description="Unique ID for webhook idempotency"
    )

    # Request metadata
    policy_type: str = Field(index=True, description="cost, capability, resource, rate_limit")
    skill_id: Optional[str] = Field(default=None, index=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    agent_id: Optional[str] = Field(default=None)

    # Request details
    requested_by: str = Field(description="User/system that created the request")
    justification: Optional[str] = Field(default=None)
    payload_json: Optional[str] = Field(default=None, description="JSON of execution payload")

    # Status state machine
    status: str = Field(default="pending", index=True)
    status_history_json: Optional[str] = Field(default=None, description="JSON array of status transitions for audit")

    # Approval tracking
    required_level: int = Field(default=3, description="Minimum approval level needed")
    current_level: int = Field(default=0, description="Highest approval level received")
    approvals_json: Optional[str] = Field(default=None, description="JSON array of approval actions")

    # Escalation config
    escalate_to: Optional[str] = Field(default=None)
    escalation_timeout_seconds: int = Field(default=300)

    # Webhook tracking
    webhook_url: Optional[str] = Field(default=None)
    webhook_secret_hash: Optional[str] = Field(default=None, description="Hash of webhook secret")
    webhook_attempts: int = Field(default=0)
    last_webhook_status: Optional[str] = Field(default=None)
    last_webhook_at: Optional[datetime] = Field(default=None)

    # Timestamps
    expires_at: datetime = Field(description="When request expires")
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)
    resolved_at: Optional[datetime] = Field(default=None)

    def get_payload(self) -> dict:
        """Parse payload JSON."""
        import json

        if self.payload_json:
            return json.loads(self.payload_json)
        return {}

    def set_payload(self, payload: dict) -> None:
        """Set payload as JSON."""
        import json

        self.payload_json = json.dumps(payload)

    def get_approvals(self) -> list:
        """Parse approvals JSON."""
        import json

        if self.approvals_json:
            return json.loads(self.approvals_json)
        return []

    def add_approval(self, approver_id: str, level: int, action: str, notes: Optional[str] = None) -> None:
        """Add an approval action."""
        import json

        approvals = self.get_approvals()
        approvals.append(
            {
                "approver_id": approver_id,
                "level": level,
                "action": action,
                "notes": notes,
                "timestamp": utc_now().isoformat(),
            }
        )
        self.approvals_json = json.dumps(approvals)
        self.current_level = max(a["level"] for a in approvals)
        self.updated_at = utc_now()

    def get_status_history(self) -> list:
        """Parse status history JSON."""
        import json

        if self.status_history_json:
            return json.loads(self.status_history_json)
        return []

    def transition_status(self, new_status: str, actor: Optional[str] = None, reason: Optional[str] = None) -> None:
        """
        Transition to a new status with audit trail.

        Args:
            new_status: Target status
            actor: Who/what triggered the transition
            reason: Why the transition happened
        """
        import json

        old_status = self.status
        history = self.get_status_history()
        history.append(
            {
                "from_status": old_status,
                "to_status": new_status,
                "actor": actor,
                "reason": reason,
                "timestamp": utc_now().isoformat(),
            }
        )
        self.status_history_json = json.dumps(history)
        self.status = new_status
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "request_id": self.id,
            "correlation_id": self.correlation_id,
            "status": self.status,
            "status_history": self.get_status_history(),
            "policy_type": self.policy_type,
            "skill_id": self.skill_id,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "payload": self.get_payload(),
            "requested_by": self.requested_by,
            "justification": self.justification,
            "required_level": self.required_level,
            "current_level": self.current_level,
            "approvers": self.get_approvals(),
            "escalate_to": self.escalate_to,
            "webhook_attempts": self.webhook_attempts,
            "last_webhook_status": self.last_webhook_status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============== CostSim Circuit Breaker State (M6 - DB-backed) ==============


class CostSimCBState(SQLModel, table=True):
    """
    DB-backed circuit breaker state for CostSim V2.

    Replaces file-based state for multi-replica consistency.
    Uses SELECT FOR UPDATE for atomic state transitions.

    Supports:
    - Centralized state across all replicas
    - TTL-based auto-recovery (disabled_until)
    - Audit trail (who/why/when)
    - Alertmanager integration
    """

    __tablename__ = "costsim_cb_state"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, description="Circuit breaker identifier (e.g. 'costsim_v2')")
    disabled: bool = Field(default=False, description="Whether circuit breaker is open (V2 disabled)")
    disabled_by: Optional[str] = Field(default=None, description="Who disabled (user_id, system, circuit_breaker)")
    disabled_reason: Optional[str] = Field(default=None, description="Reason for disabling")
    disabled_until: Optional[datetime] = Field(
        default=None, description="Auto-recovery time (null = manual reset required)"
    )
    incident_id: Optional[str] = Field(default=None, description="Associated incident ID")
    consecutive_failures: int = Field(default=0, description="Number of consecutive drift threshold violations")
    last_failure_at: Optional[datetime] = Field(default=None, description="Timestamp of last failure")
    updated_at: datetime = Field(default_factory=utc_now, description="Last state update timestamp")
    created_at: datetime = Field(default_factory=utc_now, description="Record creation timestamp")

    def is_expired(self) -> bool:
        """Check if disabled_until has passed."""
        if self.disabled_until is None:
            return False
        return utc_now() > self.disabled_until

    def should_auto_recover(self) -> bool:
        """Check if circuit breaker should auto-recover based on TTL."""
        return self.disabled and self.is_expired()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "disabled": self.disabled,
            "disabled_by": self.disabled_by,
            "disabled_reason": self.disabled_reason,
            "disabled_until": self.disabled_until.isoformat() if self.disabled_until else None,
            "incident_id": self.incident_id,
            "consecutive_failures": self.consecutive_failures,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CostSimCBIncident(SQLModel, table=True):
    """
    Incident records for circuit breaker trips.

    Provides audit trail for all circuit breaker events.
    Stores alert sending status for retry/debugging.
    """

    __tablename__ = "costsim_cb_incidents"

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12], primary_key=True)
    circuit_breaker_name: str = Field(index=True, description="Name of circuit breaker")
    timestamp: datetime = Field(default_factory=utc_now, index=True)
    reason: str = Field(description="Reason for trip")
    severity: str = Field(description="P1, P2, P3")
    drift_score: Optional[float] = Field(default=None)
    sample_count: Optional[int] = Field(default=None)
    details_json: Optional[str] = Field(default=None)

    # Resolution
    resolved: bool = Field(default=False, index=True)
    resolved_at: Optional[datetime] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)

    # Alert tracking
    alert_sent: bool = Field(default=False)
    alert_sent_at: Optional[datetime] = Field(default=None)
    alert_response: Optional[str] = Field(default=None)

    def get_details(self) -> dict:
        """Parse details JSON."""
        import json

        if self.details_json:
            return json.loads(self.details_json)
        return {}

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "circuit_breaker_name": self.circuit_breaker_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "reason": self.reason,
            "severity": self.severity,
            "drift_score": self.drift_score,
            "sample_count": self.sample_count,
            "details": self.get_details(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "alert_sent": self.alert_sent,
            "alert_sent_at": self.alert_sent_at.isoformat() if self.alert_sent_at else None,
        }


# ============== Status History (M6 - Immutable Audit Trail) ==============


class StatusHistory(SQLModel, table=True):
    """
    Immutable append-only status history for audit trail.

    This table captures ALL status transitions for runs, agents, and approvals.
    Records are NEVER updated or deleted - only appended.

    Supports:
    - CSV/JSONL export via signed URLs
    - Audit compliance (SOC2, HIPAA)
    - Regulatory evidence retention
    - Historical analysis and debugging
    """

    __tablename__ = "status_history"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    # Entity reference
    entity_type: str = Field(index=True, description="Type: run, agent, approval, workflow, costsim")
    entity_id: str = Field(index=True, description="ID of the entity (run_id, agent_id, etc.)")

    # Status transition
    old_status: Optional[str] = Field(default=None, description="Previous status (null for creation)")
    new_status: str = Field(description="New status after transition")

    # Actor and reason
    actor_type: str = Field(default="system", description="Type: system, user, agent, scheduler, circuit_breaker")
    actor_id: Optional[str] = Field(default=None, description="ID of actor (user_id, agent_id, etc.)")
    reason: Optional[str] = Field(default=None, description="Human-readable reason for transition")

    # Context
    tenant_id: Optional[str] = Field(default=None, index=True, description="Tenant scope for multi-tenancy")
    correlation_id: Optional[str] = Field(default=None, index=True, description="Correlation ID for tracing")

    # Metadata (JSON)
    metadata_json: Optional[str] = Field(default=None, description="Additional context as JSON")

    # Immutable timestamp (set once, never updated)
    created_at: datetime = Field(
        default_factory=utc_now, index=True, description="Timestamp of status change (immutable)"
    )

    # Sequence number for ordering
    sequence: Optional[int] = Field(
        default=None, index=True, description="Auto-incrementing sequence for total ordering"
    )

    def get_metadata(self) -> dict:
        """Parse metadata JSON."""
        import json

        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "tenant_id": self.tenant_id,
            "correlation_id": self.correlation_id,
            "metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sequence": self.sequence,
        }

    def to_csv_row(self) -> list:
        """Convert to CSV row."""
        return [
            self.id,
            self.entity_type,
            self.entity_id,
            self.old_status or "",
            self.new_status,
            self.actor_type,
            self.actor_id or "",
            self.reason or "",
            self.tenant_id or "",
            self.correlation_id or "",
            self.metadata_json or "",
            self.created_at.isoformat() if self.created_at else "",
            str(self.sequence) if self.sequence else "",
        ]

    @staticmethod
    def csv_headers() -> list:
        """Get CSV headers."""
        return [
            "id",
            "entity_type",
            "entity_id",
            "old_status",
            "new_status",
            "actor_type",
            "actor_id",
            "reason",
            "tenant_id",
            "correlation_id",
            "metadata_json",
            "created_at",
            "sequence",
        ]


# ============== Failure Match (M9 - Failure Persistence) ==============


class FailureMatch(SQLModel, table=True):
    """
    Persistent storage for failure catalog matches.

    Tracks all failure events for:
    - Learning from runtime errors
    - Recovery suggestion engine (M10)
    - Failure analytics dashboards
    - Pattern aggregation for unknown errors

    Every time failure_catalog.match() runs, a record is persisted here.
    """

    __tablename__ = "failure_matches"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    run_id: str = Field(index=True, description="Run that produced this failure")
    tenant_id: Optional[str] = Field(default=None, index=True, description="Tenant scope")

    # Error identification
    error_code: str = Field(index=True, description="Error code (e.g., TIMEOUT, BUDGET_EXCEEDED)")
    error_message: Optional[str] = Field(default=None, description="Full error message")

    # Catalog match info
    catalog_entry_id: Optional[str] = Field(
        default=None, index=True, description="Matched catalog entry code (null if miss)"
    )
    match_type: str = Field(default="unknown", description="How match was found: exact, prefix, regex, code, unknown")
    confidence_score: float = Field(default=0.0, description="Match confidence (1.0 = exact, 0.7 = prefix, 0 = miss)")

    # Catalog entry details (denormalized for analytics)
    category: Optional[str] = Field(default=None, description="TRANSIENT, PERMANENT, RESOURCE, etc.")
    severity: Optional[str] = Field(default=None, description="LOW, MEDIUM, HIGH, CRITICAL")
    is_retryable: bool = Field(default=False, description="Whether error is retryable")
    recovery_mode: Optional[str] = Field(default=None, description="Recommended recovery strategy")
    recovery_suggestion: Optional[str] = Field(default=None, description="Human-readable suggestion")

    # Recovery tracking
    recovery_attempted: bool = Field(default=False, description="Whether recovery was tried")
    recovery_succeeded: bool = Field(default=False, description="Whether recovery worked")
    recovered_at: Optional[datetime] = Field(default=None, description="When recovery completed")
    recovered_by: Optional[str] = Field(default=None, description="User/system that marked recovery")
    recovery_notes: Optional[str] = Field(default=None, description="Operator notes on recovery")

    # Execution context
    skill_id: Optional[str] = Field(default=None, description="Skill that failed")
    step_index: Optional[int] = Field(default=None, description="Step in plan")
    context_json: Optional[str] = Field(default=None, description="Additional context as JSON")

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)

    def get_context(self) -> dict:
        """Parse context JSON."""
        import json

        if self.context_json:
            return json.loads(self.context_json)
        return {}

    def set_context(self, context: dict) -> None:
        """Set context as JSON."""
        import json

        self.context_json = json.dumps(context)

    def mark_recovery_attempted(self) -> None:
        """Mark that recovery was attempted."""
        self.recovery_attempted = True
        self.updated_at = utc_now()

    def mark_recovery_succeeded(self, by: Optional[str] = None, notes: Optional[str] = None) -> None:
        """Mark that recovery succeeded."""
        self.recovery_attempted = True
        self.recovery_succeeded = True
        self.recovered_at = utc_now()
        if by:
            self.recovered_by = by
        if notes:
            self.recovery_notes = notes
        self.updated_at = utc_now()

    def mark_recovery_failed(self, by: Optional[str] = None, notes: Optional[str] = None) -> None:
        """Mark that recovery was attempted but failed."""
        self.recovery_attempted = True
        self.recovery_succeeded = False
        self.recovered_at = utc_now()
        if by:
            self.recovered_by = by
        if notes:
            self.recovery_notes = notes
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "catalog_entry_id": self.catalog_entry_id,
            "match_type": self.match_type,
            "confidence_score": self.confidence_score,
            "category": self.category,
            "severity": self.severity,
            "is_retryable": self.is_retryable,
            "recovery_mode": self.recovery_mode,
            "recovery_suggestion": self.recovery_suggestion,
            "recovery_attempted": self.recovery_attempted,
            "recovery_succeeded": self.recovery_succeeded,
            "recovered_at": self.recovered_at.isoformat() if self.recovered_at else None,
            "recovered_by": self.recovered_by,
            "recovery_notes": self.recovery_notes,
            "skill_id": self.skill_id,
            "step_index": self.step_index,
            "context": self.get_context(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# Helper function for status history logging
def log_status_change(
    session: Session,
    entity_type: str,
    entity_id: str,
    new_status: str,
    old_status: Optional[str] = None,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
    reason: Optional[str] = None,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> StatusHistory:
    """
    Log a status change to the immutable history.

    This is the canonical way to record status transitions.
    Always use this function instead of directly creating StatusHistory records.

    Args:
        session: Database session
        entity_type: Type of entity (run, agent, approval, etc.)
        entity_id: ID of the entity
        new_status: New status after transition
        old_status: Previous status (None for creation)
        actor_type: Type of actor making the change
        actor_id: ID of the actor
        reason: Human-readable reason
        tenant_id: Tenant scope
        correlation_id: Correlation ID for tracing
        metadata: Additional context

    Returns:
        Created StatusHistory record
    """
    import json

    record = StatusHistory(
        entity_type=entity_type,
        entity_id=entity_id,
        old_status=old_status,
        new_status=new_status,
        actor_type=actor_type,
        actor_id=actor_id,
        reason=reason,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )

    session.add(record)
    session.commit()
    session.refresh(record)

    # Safe: session is DI-managed and stays open for caller
    return record


# =============================================================================
# M26 Cost Intelligence Models
# =============================================================================
# Every token spent is attributable to tenant → user → feature → request.
# Every anomaly must trigger an action, not a chart.
# =============================================================================


class FeatureTag(SQLModel, table=True):
    """
    Registered feature namespaces for cost attribution.

    This is the KEY UNLOCK for:
    - Feature ROI analysis
    - Kill-switch precision
    - Product pricing

    No tag → request defaulted to 'unclassified' (and flagged).
    """

    __tablename__ = "feature_tags"

    id: str = Field(default_factory=lambda: f"ft_{uuid.uuid4().hex[:16]}", primary_key=True)
    tenant_id: str = Field(index=True)
    tag: str = Field(index=True)  # e.g., "customer_support.chat"
    display_name: str
    description: Optional[str] = None
    budget_cents: Optional[int] = None  # Per-feature budget
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CostRecord(SQLModel, table=True):
    """
    High-volume raw cost metering (append-only).

    Design rule: Raw writes fast, reads aggregated.
    Never dashboard off raw rows.
    """

    __tablename__ = "cost_records"

    id: str = Field(default_factory=lambda: f"cr_{uuid.uuid4().hex[:16]}", primary_key=True)
    tenant_id: str = Field(index=True)
    user_id: Optional[str] = Field(default=None, index=True)  # Who made the request
    feature_tag: Optional[str] = Field(default=None, index=True)  # Which feature
    request_id: Optional[str] = None  # Trace linkage
    workflow_id: Optional[str] = None
    skill_id: Optional[str] = None
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_cents: float
    created_at: datetime = Field(default_factory=utc_now)


class CostAnomaly(SQLModel, table=True):
    """
    Detected cost anomalies.

    Four signals initially (keep it small):
    - USER_SPIKE: One user behaving abnormally
    - FEATURE_SPIKE: Feature cost exploding
    - BUDGET_WARNING: Projected overrun
    - BUDGET_EXCEEDED: Hard stop

    Anything more early = noise.
    """

    __tablename__ = "cost_anomalies"

    id: str = Field(default_factory=lambda: f"ca_{uuid.uuid4().hex[:16]}", primary_key=True)
    tenant_id: str = Field(index=True)
    anomaly_type: str  # USER_SPIKE, FEATURE_SPIKE, BUDGET_WARNING, BUDGET_EXCEEDED
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    entity_type: str  # user, feature, model, tenant
    entity_id: Optional[str] = None  # user_id, feature_tag, model name
    current_value_cents: float
    expected_value_cents: float
    deviation_pct: float
    threshold_pct: float = 200.0  # What deviation % triggered this
    message: str
    incident_id: Optional[str] = None  # Link to M25 incident if escalated
    action_taken: Optional[str] = None  # What action was taken
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata_json: Optional[dict] = Field(default=None, sa_column=Column("metadata", JSON, nullable=True))
    detected_at: datetime = Field(default_factory=utc_now)
    # M29: Added for anomaly rules alignment
    derived_cause: Optional[str] = None  # RETRY_LOOP, PROMPT_GROWTH, FEATURE_SURGE, TRAFFIC_GROWTH, UNKNOWN
    breach_count: int = 1  # How many consecutive intervals breached


class CostBreachHistory(SQLModel, table=True):
    """
    M29: Track breach history for consecutive interval logic.

    Absolute spike rule: 1.4x threshold + 2 consecutive daily intervals
    One record per entity per day per breach_type.
    """

    __tablename__ = "cost_breach_history"

    id: str = Field(default_factory=lambda: f"bh_{uuid.uuid4().hex[:16]}", primary_key=True)
    tenant_id: str = Field(index=True)
    entity_type: str  # user, feature, tenant, model
    entity_id: Optional[str] = None
    breach_type: str  # ABSOLUTE_SPIKE, SUSTAINED_DRIFT
    breach_date: date
    deviation_pct: float
    current_value_cents: float
    baseline_value_cents: float
    created_at: datetime = Field(default_factory=utc_now)


class CostDriftTracking(SQLModel, table=True):
    """
    M29: Track sustained drift for early-warning detection.

    Sustained drift rule: 7d rolling avg > baseline_7d * 1.25 for >= 3 days.
    """

    __tablename__ = "cost_drift_tracking"

    id: str = Field(default_factory=lambda: f"dt_{uuid.uuid4().hex[:16]}", primary_key=True)
    tenant_id: str = Field(index=True)
    entity_type: str  # user, feature, tenant
    entity_id: Optional[str] = None
    rolling_7d_avg_cents: float
    baseline_7d_avg_cents: float
    drift_pct: float
    drift_days_count: int = 1
    first_drift_date: date
    last_check_date: date
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CostBudget(SQLModel, table=True):
    """
    Per-tenant and per-feature budget limits.
    """

    __tablename__ = "cost_budgets"

    id: str = Field(default_factory=lambda: f"cb_{uuid.uuid4().hex[:16]}", primary_key=True)
    tenant_id: str = Field(index=True)
    budget_type: str  # tenant, feature, user
    entity_id: Optional[str] = None  # null for tenant-level
    daily_limit_cents: Optional[int] = None
    monthly_limit_cents: Optional[int] = None
    warn_threshold_pct: int = 80
    hard_limit_enabled: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CostDailyAggregate(SQLModel, table=True):
    """
    Pre-aggregated daily costs for fast dashboard reads.

    Never dashboard off raw rows.
    """

    __tablename__ = "cost_daily_aggregates"

    id: str = Field(default_factory=lambda: f"cda_{uuid.uuid4().hex[:16]}", primary_key=True)
    tenant_id: str = Field(index=True)
    date: datetime  # Date only (no time)
    feature_tag: Optional[str] = None  # null for tenant-level
    user_id: Optional[str] = None  # null for tenant/feature-level
    model: Optional[str] = None  # null for higher-level aggregates
    total_cost_cents: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    request_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# SDSR: Incidents Domain (PIN-370)
# =============================================================================
# Incidents are REACTIVE - created by the Incident Engine when runs fail.
# Scenarios inject causes (failed runs), backend creates incidents.
# UI observes incidents via PanelContentRegistry, never writes them.
# =============================================================================


class SDSRIncident(SQLModel, table=True):
    """
    SDSR Incident records created by the Incident Engine.

    This table is separate from `incidents` (killswitch incidents).
    - `incidents` table: KillSwitch proxy layer incidents (calls, rate limits)
    - `sdsr_incidents` table: Run execution incidents (SDSR Activity → Incidents propagation)

    SDSR Contract (PIN-370):
    - Incidents are NEVER directly written by scenarios
    - Incident Engine creates incidents when runs fail
    - Source run must exist before incident is created
    - UI observes via /api/v1/incidents endpoint

    Category Types:
    - EXECUTION_FAILURE: Run execution failed (timeout, error, etc.)
    - POLICY_VIOLATION: Run violated a policy constraint
    - BUDGET_EXCEEDED: Run exceeded budget limits
    - RATE_LIMIT: Run hit rate limits
    - RESOURCE_EXHAUSTION: System resource limits hit
    - MANUAL: Manually created incident
    """

    __tablename__ = "sdsr_incidents"

    id: str = Field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:16]}", primary_key=True)

    # Source linkage - what triggered this incident
    source_run_id: Optional[str] = Field(default=None, index=True, description="Run that triggered this incident")
    source_type: str = Field(default="run", description="Source type: run, policy, budget, manual")

    # Incident classification
    category: str = Field(index=True, description="EXECUTION_FAILURE, POLICY_VIOLATION, BUDGET_EXCEEDED, etc.")
    severity: str = Field(default="MEDIUM", index=True, description="LOW, MEDIUM, HIGH, CRITICAL")
    status: str = Field(default="OPEN", index=True, description="OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, CLOSED")

    # Incident details
    title: str = Field(description="Human-readable incident title")
    description: Optional[str] = Field(default=None, description="Detailed description of the incident")
    error_code: Optional[str] = Field(default=None, index=True, description="Error code (e.g., EXECUTION_TIMEOUT)")
    error_message: Optional[str] = Field(default=None, description="Full error message from source")

    # Impact assessment
    impact_scope: Optional[str] = Field(default=None, description="Impact: single_run, agent, tenant, system")
    affected_agent_id: Optional[str] = Field(default=None, index=True)
    affected_count: int = Field(default=1, description="Number of affected runs/entities")

    # Multi-tenancy
    tenant_id: str = Field(index=True, description="Tenant scope")

    # Resolution tracking
    resolved_at: Optional[datetime] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None, description="User/system that resolved")
    resolution_notes: Optional[str] = Field(default=None)

    # Escalation
    escalated: bool = Field(default=False)
    escalated_at: Optional[datetime] = Field(default=None)
    escalated_to: Optional[str] = Field(default=None, description="Who was escalated to")

    # Metadata (JSON for flexible context)
    metadata_json: Optional[str] = Field(default=None, description="Additional context as JSON")

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)

    # SDSR: Synthetic data marking (PIN-370)
    is_synthetic: bool = Field(default=False, description="True if created during synthetic scenario")
    synthetic_scenario_id: Optional[str] = Field(default=None, description="Scenario ID for traceability")

    # GAP-024: Inflection point metadata
    # Captures the exact moment when an incident was triggered
    inflection_step_index: Optional[int] = Field(
        default=None,
        description="Step index where incident was triggered (GAP-024)"
    )
    inflection_timestamp: Optional[datetime] = Field(
        default=None,
        description="Exact timestamp when inflection was detected (GAP-024)"
    )
    inflection_context_json: Optional[str] = Field(
        default=None,
        description="JSON context about what was happening at inflection (GAP-024)"
    )

    def get_inflection_context(self) -> dict:
        """Get inflection context from JSON (GAP-024)."""
        import json
        if self.inflection_context_json:
            return json.loads(self.inflection_context_json)
        return {}

    def set_inflection_context(self, context: dict) -> None:
        """Set inflection context as JSON (GAP-024)."""
        import json
        self.inflection_context_json = json.dumps(context)

    def set_inflection_point(
        self,
        step_index: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        context: Optional[dict] = None,
    ) -> None:
        """
        Set inflection point metadata (GAP-024).

        Args:
            step_index: Which step triggered the incident
            timestamp: When the inflection was detected
            context: Additional context about the inflection point
        """
        if step_index is not None:
            self.inflection_step_index = step_index
        if timestamp is not None:
            self.inflection_timestamp = timestamp
        elif self.inflection_timestamp is None:
            # Default to now if not provided
            self.inflection_timestamp = utc_now()
        if context is not None:
            self.set_inflection_context(context)

    def get_metadata(self) -> dict:
        """Parse metadata JSON."""
        import json
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}

    def set_metadata(self, metadata: dict) -> None:
        """Set metadata as JSON."""
        import json
        self.metadata_json = json.dumps(metadata)

    def acknowledge(self, by: str) -> None:
        """Acknowledge the incident."""
        self.status = "ACKNOWLEDGED"
        self.updated_at = utc_now()

    def resolve(self, by: str, notes: Optional[str] = None) -> None:
        """Resolve the incident."""
        self.status = "RESOLVED"
        self.resolved_at = utc_now()
        self.resolved_by = by
        if notes:
            self.resolution_notes = notes
        self.updated_at = utc_now()

    def escalate(self, to: str) -> None:
        """Escalate the incident."""
        self.escalated = True
        self.escalated_at = utc_now()
        self.escalated_to = to
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "source_run_id": self.source_run_id,
            "source_type": self.source_type,
            "category": self.category,
            "severity": self.severity,
            "status": self.status,
            "title": self.title,
            "description": self.description,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "impact_scope": self.impact_scope,
            "affected_agent_id": self.affected_agent_id,
            "affected_count": self.affected_count,
            "tenant_id": self.tenant_id,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "escalated": self.escalated,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "escalated_to": self.escalated_to,
            "metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_synthetic": self.is_synthetic,
            "synthetic_scenario_id": self.synthetic_scenario_id,
            # GAP-024: Inflection point metadata
            "inflection_step_index": self.inflection_step_index,
            "inflection_timestamp": self.inflection_timestamp.isoformat() if self.inflection_timestamp else None,
            "inflection_context": self.get_inflection_context(),
        }
