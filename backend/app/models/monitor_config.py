# Layer: L4 — Domain Engine
# Product: AI Console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Define what signals to monitor during run execution
# Callers: policy/prevention_engine.py, api/policy_monitors.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-005

"""
Monitor Configuration Model

Defines WHAT signals to collect during run execution:
- Token usage (total, per step)
- Cost tracking (total, burn rate)
- RAG access monitoring
- Inspection constraints (negative capabilities)

Key Rule:
> If something is not monitored, it cannot trigger a limit or action.
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel


class MonitorMetric(str, Enum):
    """Metrics that can be monitored."""

    TOKEN_USAGE = "token_usage"
    TOKEN_PER_STEP = "token_per_step"
    COST = "cost"
    BURN_RATE = "burn_rate"
    RAG_ACCESS = "rag_access"
    LATENCY = "latency"
    STEP_COUNT = "step_count"


class MonitorConfig(SQLModel, table=True):
    """
    Monitor configuration that defines what signals to collect.

    Monitors define signals, not limits. If a metric is not monitored,
    it cannot trigger alerts or enforcement actions.
    """

    __tablename__ = "policy_monitor_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    config_id: str = Field(index=True, unique=True)
    policy_id: str = Field(index=True)  # FK to policy_rules.policy_id
    tenant_id: str = Field(index=True)  # FK to tenants.id

    # Token monitoring
    monitor_token_usage: bool = Field(default=True)
    monitor_token_per_step: bool = Field(default=False)

    # Cost monitoring
    monitor_cost: bool = Field(default=True)
    monitor_burn_rate: bool = Field(default=False)
    burn_rate_window_seconds: int = Field(default=60)  # Rolling window

    # RAG monitoring
    monitor_rag_access: bool = Field(default=False)
    allowed_rag_sources_json: Optional[str] = Field(
        default=None
    )  # JSON array of allowed source IDs

    # Latency and step monitoring
    monitor_latency: bool = Field(default=False)
    monitor_step_count: bool = Field(default=False)

    # Inspection constraints (negative capabilities)
    # These define what the policy is NOT allowed to inspect
    allow_prompt_logging: bool = Field(default=False)
    allow_response_logging: bool = Field(default=False)
    allow_pii_capture: bool = Field(default=False)
    allow_secret_access: bool = Field(default=False)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def allowed_rag_sources(self) -> list[str]:
        """Get allowed RAG sources as list."""
        if self.allowed_rag_sources_json:
            return json.loads(self.allowed_rag_sources_json)
        return []

    @allowed_rag_sources.setter
    def allowed_rag_sources(self, value: list[str]) -> None:
        """Set allowed RAG sources from list."""
        self.allowed_rag_sources_json = json.dumps(value) if value else None

    @property
    def enabled_metrics(self) -> list[MonitorMetric]:
        """Get list of enabled monitor metrics."""
        metrics = []
        if self.monitor_token_usage:
            metrics.append(MonitorMetric.TOKEN_USAGE)
        if self.monitor_token_per_step:
            metrics.append(MonitorMetric.TOKEN_PER_STEP)
        if self.monitor_cost:
            metrics.append(MonitorMetric.COST)
        if self.monitor_burn_rate:
            metrics.append(MonitorMetric.BURN_RATE)
        if self.monitor_rag_access:
            metrics.append(MonitorMetric.RAG_ACCESS)
        if self.monitor_latency:
            metrics.append(MonitorMetric.LATENCY)
        if self.monitor_step_count:
            metrics.append(MonitorMetric.STEP_COUNT)
        return metrics

    def is_metric_monitored(self, metric: MonitorMetric) -> bool:
        """Check if a specific metric is being monitored."""
        return metric in self.enabled_metrics

    def to_snapshot(self) -> dict:
        """Convert to snapshot dict for immutable storage."""
        return {
            "config_id": self.config_id,
            "enabled_metrics": [m.value for m in self.enabled_metrics],
            "burn_rate_window_seconds": self.burn_rate_window_seconds,
            "allowed_rag_sources": self.allowed_rag_sources,
            "inspection_constraints": {
                "allow_prompt_logging": self.allow_prompt_logging,
                "allow_response_logging": self.allow_response_logging,
                "allow_pii_capture": self.allow_pii_capture,
                "allow_secret_access": self.allow_secret_access,
            },
        }


class MonitorConfigCreate(BaseModel):
    """Request model for creating monitor config."""

    policy_id: str
    monitor_token_usage: bool = True
    monitor_token_per_step: bool = False
    monitor_cost: bool = True
    monitor_burn_rate: bool = False
    burn_rate_window_seconds: int = 60
    monitor_rag_access: bool = False
    allowed_rag_sources: Optional[list[str]] = None
    monitor_latency: bool = False
    monitor_step_count: bool = False
    allow_prompt_logging: bool = False
    allow_response_logging: bool = False
    allow_pii_capture: bool = False
    allow_secret_access: bool = False


class MonitorConfigUpdate(BaseModel):
    """Request model for updating monitor config."""

    monitor_token_usage: Optional[bool] = None
    monitor_token_per_step: Optional[bool] = None
    monitor_cost: Optional[bool] = None
    monitor_burn_rate: Optional[bool] = None
    burn_rate_window_seconds: Optional[int] = None
    monitor_rag_access: Optional[bool] = None
    allowed_rag_sources: Optional[list[str]] = None
    monitor_latency: Optional[bool] = None
    monitor_step_count: Optional[bool] = None
    allow_prompt_logging: Optional[bool] = None
    allow_response_logging: Optional[bool] = None
    allow_pii_capture: Optional[bool] = None
    allow_secret_access: Optional[bool] = None


class MonitorConfigResponse(BaseModel):
    """Response model for monitor config."""

    config_id: str
    policy_id: str
    tenant_id: str
    enabled_metrics: list[str]
    burn_rate_window_seconds: int
    allowed_rag_sources: list[str] = PydanticField(default_factory=list)
    inspection_constraints: dict
    created_at: datetime
    updated_at: datetime
