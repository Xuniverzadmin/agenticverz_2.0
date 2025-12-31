# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Agent API request/response schemas
# Callers: API routes
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: API Schemas

# Agent Schemas
# Pydantic models for Agent capabilities and configuration

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


from .retry import RetryPolicy


class AgentStatus(str, Enum):
    """Agent operational status."""

    ACTIVE = "active"  # Normal operation
    PAUSED = "paused"  # Temporarily disabled
    DISABLED = "disabled"  # Permanently disabled
    MAINTENANCE = "maintenance"  # Under maintenance


class PlannerType(str, Enum):
    """Supported planner backends."""

    STUB = "stub"  # Returns static test plans
    ANTHROPIC = "anthropic"  # Claude-based planner
    OPENAI = "openai"  # GPT-based planner
    LOCAL = "local"  # Local/Ollama models
    CUSTOM = "custom"  # Custom planner implementation


class PlannerConfig(BaseModel):
    """Configuration for the agent's planner.

    Controls how goals are translated into execution plans.
    """

    planner_type: PlannerType = Field(default=PlannerType.STUB, description="Which planner backend to use")
    model: Optional[str] = Field(default=None, description="Model to use (provider-specific)")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature for planning")
    max_tokens: int = Field(default=2048, ge=256, le=8192, description="Max tokens for plan generation")
    max_steps: int = Field(default=10, ge=1, le=50, description="Maximum steps in a plan")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt for planner")
    few_shot_examples: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Few-shot examples for planning"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "planner_type": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.5,
                "max_steps": 10,
            }
        }
    )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration for an agent."""

    requests_per_minute: int = Field(default=60, ge=1, le=10000, description="Maximum requests per minute")
    tokens_per_minute: Optional[int] = Field(
        default=None, ge=1000, le=1_000_000, description="Maximum LLM tokens per minute"
    )
    concurrent_runs: int = Field(default=5, ge=1, le=100, description="Maximum concurrent run executions")


class BudgetConfig(BaseModel):
    """Budget tracking configuration for an agent."""

    budget_cents: Optional[int] = Field(default=None, ge=0, description="Total budget in cents (None = unlimited)")
    spent_cents: int = Field(default=0, ge=0, description="Amount spent so far")
    alert_threshold_percent: int = Field(
        default=80, ge=0, le=100, description="Alert when spending exceeds this percentage"
    )
    hard_limit: bool = Field(default=True, description="Stop execution when budget exhausted")

    @property
    def remaining_cents(self) -> Optional[int]:
        """Calculate remaining budget."""
        if self.budget_cents is None:
            return None
        return max(0, self.budget_cents - self.spent_cents)

    @property
    def usage_percent(self) -> Optional[float]:
        """Calculate usage percentage."""
        if self.budget_cents is None or self.budget_cents == 0:
            return None
        return (self.spent_cents / self.budget_cents) * 100


class AgentCapabilities(BaseModel):
    """Defines what an agent can and cannot do.

    Controls access to skills, external resources,
    and establishes security boundaries.
    """

    # Skill access control
    allowed_skills: Optional[List[str]] = Field(
        default=None, description="Whitelist of allowed skills (None = all allowed)"
    )
    blocked_skills: List[str] = Field(default_factory=list, description="Blacklist of blocked skills")

    # Network/external access
    allow_external_http: bool = Field(default=True, description="Allow HTTP calls to external URLs")
    allowed_domains: Optional[List[str]] = Field(
        default=None, description="Whitelist of allowed domains for HTTP (None = all)"
    )
    blocked_domains: List[str] = Field(default_factory=list, description="Blacklist of blocked domains")

    # File system access
    allow_file_read: bool = Field(default=False, description="Allow reading files")
    allow_file_write: bool = Field(default=False, description="Allow writing files")
    allowed_paths: Optional[List[str]] = Field(
        default=None, description="Whitelist of allowed file paths (glob patterns)"
    )

    # Database access
    allow_database: bool = Field(default=False, description="Allow database queries")
    database_readonly: bool = Field(default=True, description="Restrict to read-only queries")

    # LLM access
    allow_llm: bool = Field(default=True, description="Allow LLM invocations")
    llm_max_tokens_per_call: int = Field(default=4096, ge=100, le=100000, description="Max tokens per LLM call")

    def can_use_skill(self, skill_name: str) -> bool:
        """Check if agent can use a specific skill."""
        # Check blacklist first
        if skill_name in self.blocked_skills:
            return False
        # If whitelist exists, check it
        if self.allowed_skills is not None:
            return skill_name in self.allowed_skills
        return True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "allowed_skills": ["http_call", "llm_invoke", "json_transform"],
                "allow_external_http": True,
                "allowed_domains": ["api.github.com", "api.openai.com"],
                "allow_file_read": False,
                "allow_file_write": False,
                "allow_database": False,
            }
        }
    )

    def can_access_domain(self, domain: str) -> bool:
        """Check if agent can access a domain."""
        if not self.allow_external_http:
            return False
        if domain in self.blocked_domains:
            return False
        if self.allowed_domains is not None:
            return domain in self.allowed_domains
        return True


class AgentConfig(BaseModel):
    """Complete configuration for an agent.

    Combines capabilities, planner settings, rate limits,
    and budget tracking.
    """

    agent_id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Human-readable name")
    description: Optional[str] = Field(default=None, description="Agent description/purpose")

    # Core configuration
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="Current operational status")
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities, description="What the agent can do")
    planner: PlannerConfig = Field(default_factory=PlannerConfig, description="Planner configuration")

    # Resource limits
    rate_limits: RateLimitConfig = Field(default_factory=RateLimitConfig, description="Rate limiting configuration")
    budget: BudgetConfig = Field(default_factory=BudgetConfig, description="Budget tracking")
    default_retry_policy: RetryPolicy = Field(default_factory=RetryPolicy, description="Default retry policy for runs")

    # Ownership and access
    owner_id: Optional[str] = Field(default=None, description="Owner user/tenant ID")
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID for multi-tenancy")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")

    # Metadata
    created_at: datetime = Field(default_factory=_utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=_utc_now, description="Last update timestamp")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "agent-abc123",
                "name": "Data Fetcher",
                "description": "Fetches and processes data from APIs",
                "status": "active",
                "capabilities": {"allowed_skills": ["http_call", "json_transform"], "allow_external_http": True},
                "planner": {"planner_type": "anthropic", "model": "claude-sonnet-4-20250514"},
                "rate_limits": {"requests_per_minute": 30},
            }
        }
    )
