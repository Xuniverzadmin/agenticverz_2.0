# Layer: L4 — Domain Engine
# Product: AI Console
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Record near-threshold and breach events for alerting and audit
# Callers: policy/prevention_engine.py, services/alert_emitter.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-006

"""
Threshold Signal Model

Records threshold events during run execution:
- NEAR: Approaching threshold (configurable percentage)
- BREACH: Threshold exceeded, enforcement triggered

These signals are immutable evidence for audit and compliance.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class SignalType(str, Enum):
    """Type of threshold signal."""

    NEAR = "near"  # Approaching threshold
    BREACH = "breach"  # Threshold exceeded


class ThresholdMetric(str, Enum):
    """Metrics that can trigger threshold signals."""

    TOKEN_USAGE = "token_usage"
    COST = "cost"
    BURN_RATE = "burn_rate"
    RAG_ACCESS = "rag_access"
    STEP_COUNT = "step_count"
    LATENCY = "latency"


class ThresholdSignal(SQLModel, table=True):
    """
    Immutable record of a threshold event.

    Created when a monitored metric approaches (NEAR) or exceeds (BREACH)
    the configured threshold. These records form the audit trail for
    enforcement actions.
    """

    __tablename__ = "threshold_signals"

    id: Optional[int] = Field(default=None, primary_key=True)
    signal_id: str = Field(
        default_factory=lambda: f"SIG-{uuid.uuid4().hex[:12]}",
        index=True,
        unique=True,
    )

    # References
    run_id: str = Field(index=True)  # FK to runs.run_id
    policy_id: str = Field(index=True)  # FK to policy_rules.policy_id
    tenant_id: str = Field(index=True)  # FK to tenants.id
    step_index: Optional[int] = Field(default=None)  # Step where signal occurred

    # Signal data
    signal_type: str  # SignalType value
    metric: str  # ThresholdMetric value
    current_value: float  # Current value of the metric
    threshold_value: float  # Configured threshold
    percentage: Optional[float] = Field(default=None)  # Percentage of threshold

    # Action taken (for BREACH signals)
    action_taken: Optional[str] = Field(default=None)  # pause, stop, kill

    # Metadata
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Acknowledgement (for NEAR signals)
    acknowledged: bool = Field(default=False)
    acknowledged_by: Optional[str] = Field(default=None)
    acknowledged_at: Optional[datetime] = Field(default=None)

    # Alert status
    alert_sent: bool = Field(default=False)
    alert_sent_at: Optional[datetime] = Field(default=None)
    alert_channels: Optional[str] = Field(default=None)  # JSON array

    @classmethod
    def create_near_signal(
        cls,
        run_id: str,
        policy_id: str,
        tenant_id: str,
        metric: ThresholdMetric,
        current_value: float,
        threshold_value: float,
        step_index: Optional[int] = None,
    ) -> "ThresholdSignal":
        """Factory method for NEAR threshold signals."""
        percentage = (current_value / threshold_value * 100) if threshold_value > 0 else 0
        return cls(
            run_id=run_id,
            policy_id=policy_id,
            tenant_id=tenant_id,
            step_index=step_index,
            signal_type=SignalType.NEAR.value,
            metric=metric.value,
            current_value=current_value,
            threshold_value=threshold_value,
            percentage=percentage,
        )

    @classmethod
    def create_breach_signal(
        cls,
        run_id: str,
        policy_id: str,
        tenant_id: str,
        metric: ThresholdMetric,
        current_value: float,
        threshold_value: float,
        action_taken: str,
        step_index: Optional[int] = None,
    ) -> "ThresholdSignal":
        """Factory method for BREACH threshold signals."""
        percentage = (current_value / threshold_value * 100) if threshold_value > 0 else 100
        return cls(
            run_id=run_id,
            policy_id=policy_id,
            tenant_id=tenant_id,
            step_index=step_index,
            signal_type=SignalType.BREACH.value,
            metric=metric.value,
            current_value=current_value,
            threshold_value=threshold_value,
            percentage=percentage,
            action_taken=action_taken,
        )

    def acknowledge(self, user_id: str) -> None:
        """Acknowledge a NEAR signal."""
        self.acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now(timezone.utc)

    def mark_alert_sent(self, channels: list[str]) -> None:
        """Mark alert as sent via specified channels."""
        import json

        self.alert_sent = True
        self.alert_sent_at = datetime.now(timezone.utc)
        self.alert_channels = json.dumps(channels)

    def to_evidence(self) -> dict:
        """Convert to evidence dict for export bundles."""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "metric": self.metric,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "percentage": self.percentage,
            "step_index": self.step_index,
            "action_taken": self.action_taken,
            "timestamp": self.timestamp.isoformat(),
        }


class ThresholdSignalResponse(BaseModel):
    """Response model for threshold signal."""

    signal_id: str
    run_id: str
    policy_id: str
    tenant_id: str
    step_index: Optional[int]
    signal_type: SignalType
    metric: ThresholdMetric
    current_value: float
    threshold_value: float
    percentage: Optional[float]
    action_taken: Optional[str]
    timestamp: datetime
    acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]


class ThresholdSignalListResponse(BaseModel):
    """Response model for list of threshold signals."""

    signals: list[ThresholdSignalResponse]
    total: int
    page: int
    page_size: int
