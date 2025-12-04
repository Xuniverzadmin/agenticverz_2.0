import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, Session, create_engine


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime. Use instead of utc_now()."""
    return datetime.now(timezone.utc)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

# Connection pool configuration for concurrent load
# pool_size: number of persistent connections
# max_overflow: additional connections allowed above pool_size
# pool_timeout: seconds to wait for a connection from pool
# pool_recycle: seconds before recycling connections (helps with stale connections)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,  # Verify connections before use
)


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = Field(default=None)
    status: str = Field(default="active")  # active, paused, disabled, maintenance

    # Capabilities and configuration (JSON strings)
    capabilities_json: Optional[str] = Field(
        default=None,
        description="JSON: AgentCapabilities schema"
    )
    planner_config_json: Optional[str] = Field(
        default=None,
        description="JSON: PlannerConfig schema"
    )

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
    goal: str
    status: str = Field(default="queued")  # queued, running, succeeded, failed, retry
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)
    error_message: Optional[str] = None
    plan_json: Optional[str] = None
    tool_calls_json: Optional[str] = None

    # Idempotency support
    idempotency_key: Optional[str] = Field(
        default=None,
        index=True,
        description="Client-provided key for idempotent submissions"
    )

    # Parent run for reruns
    parent_run_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Original run ID if this is a rerun"
    )

    # Priority for queue ordering
    priority: int = Field(default=0, description="Higher = more urgent")

    # Tenant scoping
    tenant_id: Optional[str] = Field(default=None, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None
    duration_ms: Optional[float] = None


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
        default=None,
        description="JSON array of tenant IDs for targeted rollout"
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
        default="auto_approve",
        description="auto_approve, pre_approved, agent_approve, manual_approve, owner_override"
    )

    # Scope
    tenant_id: Optional[str] = Field(default=None, index=True, description="Tenant scope (null=global)")
    agent_id: Optional[str] = Field(default=None, index=True, description="Agent scope (null=all)")
    skill_id: Optional[str] = Field(default=None, description="Skill scope (null=all)")

    # Thresholds for auto-approval
    auto_approve_max_cost_cents: Optional[int] = Field(
        default=None,
        description="Max cost for auto-approval (cents)"
    )
    auto_approve_max_tokens: Optional[int] = Field(
        default=None,
        description="Max tokens for auto-approval"
    )

    # Escalation config
    escalate_to: Optional[str] = Field(
        default=None,
        description="Next approval level if denied"
    )
    escalation_timeout_seconds: int = Field(
        default=300,
        description="Timeout before auto-escalating"
    )

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
        default_factory=lambda: uuid.uuid4().hex,
        description="Unique ID for webhook idempotency"
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
    status_history_json: Optional[str] = Field(
        default=None,
        description="JSON array of status transitions for audit"
    )

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
        approvals.append({
            "approver_id": approver_id,
            "level": level,
            "action": action,
            "notes": notes,
            "timestamp": utc_now().isoformat()
        })
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
        history.append({
            "from_status": old_status,
            "to_status": new_status,
            "actor": actor,
            "reason": reason,
            "timestamp": utc_now().isoformat()
        })
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
    name: str = Field(
        unique=True,
        index=True,
        description="Circuit breaker identifier (e.g. 'costsim_v2')"
    )
    disabled: bool = Field(
        default=False,
        description="Whether circuit breaker is open (V2 disabled)"
    )
    disabled_by: Optional[str] = Field(
        default=None,
        description="Who disabled (user_id, system, circuit_breaker)"
    )
    disabled_reason: Optional[str] = Field(
        default=None,
        description="Reason for disabling"
    )
    disabled_until: Optional[datetime] = Field(
        default=None,
        description="Auto-recovery time (null = manual reset required)"
    )
    incident_id: Optional[str] = Field(
        default=None,
        description="Associated incident ID"
    )
    consecutive_failures: int = Field(
        default=0,
        description="Number of consecutive drift threshold violations"
    )
    last_failure_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last failure"
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        description="Last state update timestamp"
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Record creation timestamp"
    )

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

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:12],
        primary_key=True
    )
    circuit_breaker_name: str = Field(
        index=True,
        description="Name of circuit breaker"
    )
    timestamp: datetime = Field(
        default_factory=utc_now,
        index=True
    )
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
    entity_type: str = Field(
        index=True,
        description="Type: run, agent, approval, workflow, costsim"
    )
    entity_id: str = Field(
        index=True,
        description="ID of the entity (run_id, agent_id, etc.)"
    )

    # Status transition
    old_status: Optional[str] = Field(
        default=None,
        description="Previous status (null for creation)"
    )
    new_status: str = Field(
        description="New status after transition"
    )

    # Actor and reason
    actor_type: str = Field(
        default="system",
        description="Type: system, user, agent, scheduler, circuit_breaker"
    )
    actor_id: Optional[str] = Field(
        default=None,
        description="ID of actor (user_id, agent_id, etc.)"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Human-readable reason for transition"
    )

    # Context
    tenant_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Tenant scope for multi-tenancy"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Correlation ID for tracing"
    )

    # Metadata (JSON)
    metadata_json: Optional[str] = Field(
        default=None,
        description="Additional context as JSON"
    )

    # Immutable timestamp (set once, never updated)
    created_at: datetime = Field(
        default_factory=utc_now,
        index=True,
        description="Timestamp of status change (immutable)"
    )

    # Sequence number for ordering
    sequence: Optional[int] = Field(
        default=None,
        index=True,
        description="Auto-incrementing sequence for total ordering"
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

    return record
