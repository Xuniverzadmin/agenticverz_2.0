import os
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, echo=False)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
