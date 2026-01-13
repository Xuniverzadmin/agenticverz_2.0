# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Policy control-plane models (PIN-412)
# Callers: policy/*, api/policies/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-412 Domain Design

"""
Policy Control-Plane Models (PIN-412)

Establishes the foundational persistence for the Policies domain:
- PolicyRule: Governance rules (active, retired)
- PolicyEnforcement: Rule trigger history
- Limit: Budget, rate, threshold constraints
- LimitBreach: Breach history

After this schema:
- Policies › Governance is eligible for O2 API design
- Policies › Limits is eligible for O2 API design
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    """Return current UTC time (PIN-412)."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a UUID string (PIN-412)."""
    return str(uuid.uuid4())


# =============================================================================
# Enums (Canonical Values - PIN-412)
# =============================================================================


class EnforcementMode(str, Enum):
    """Policy rule enforcement modes."""

    BLOCK = "BLOCK"
    WARN = "WARN"
    AUDIT = "AUDIT"
    DISABLED = "DISABLED"


class PolicyScope(str, Enum):
    """Policy rule scope levels."""

    GLOBAL = "GLOBAL"
    TENANT = "TENANT"
    PROJECT = "PROJECT"
    AGENT = "AGENT"


class LimitScope(str, Enum):
    """Limit scope levels (extends PolicyScope with PROVIDER)."""

    GLOBAL = "GLOBAL"
    TENANT = "TENANT"
    PROJECT = "PROJECT"
    AGENT = "AGENT"
    PROVIDER = "PROVIDER"


class PolicyRuleStatus(str, Enum):
    """Policy rule lifecycle status."""

    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class PolicySource(str, Enum):
    """Policy rule creation source."""

    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"
    LEARNED = "LEARNED"


class EnforcementAction(str, Enum):
    """Actions taken when a rule triggers."""

    BLOCKED = "BLOCKED"
    WARNED = "WARNED"
    AUDITED = "AUDITED"


class LimitCategory(str, Enum):
    """Limit categories."""

    BUDGET = "BUDGET"
    RATE = "RATE"
    THRESHOLD = "THRESHOLD"


class LimitEnforcement(str, Enum):
    """Limit enforcement behaviors."""

    BLOCK = "BLOCK"
    WARN = "WARN"
    REJECT = "REJECT"
    QUEUE = "QUEUE"
    DEGRADE = "DEGRADE"
    ALERT = "ALERT"


class LimitConsequence(str, Enum):
    """Threshold limit consequences."""

    ALERT = "ALERT"
    INCIDENT = "INCIDENT"
    ABORT = "ABORT"


class ResetPeriod(str, Enum):
    """Budget limit reset periods."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    NONE = "NONE"


class LimitStatus(str, Enum):
    """Limit status."""

    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class BreachType(str, Enum):
    """Types of limit breaches."""

    BREACHED = "BREACHED"
    EXHAUSTED = "EXHAUSTED"
    THROTTLED = "THROTTLED"
    VIOLATED = "VIOLATED"


# =============================================================================
# Policy Rules (Governance)
# =============================================================================


class PolicyRule(SQLModel, table=True):
    """
    Policy rule record - governance rule definition.

    PIN-412: Rules define constraints that govern LLM Run behavior.
    Rules are never deleted, only retired.
    """

    __tablename__ = "policy_rules"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)

    # Core rule definition
    name: str = Field(max_length=256)
    description: Optional[str] = None
    enforcement_mode: str = Field(
        max_length=16, default=EnforcementMode.WARN.value
    )  # BLOCK, WARN, AUDIT, DISABLED
    scope: str = Field(
        max_length=16, default=PolicyScope.TENANT.value
    )  # GLOBAL, TENANT, PROJECT, AGENT
    scope_id: Optional[str] = None  # Specific ID for non-GLOBAL
    conditions: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Status lifecycle
    status: str = Field(
        max_length=16, default=PolicyRuleStatus.ACTIVE.value
    )  # ACTIVE, RETIRED

    # Provenance
    created_by: Optional[str] = None
    source: str = Field(
        max_length=16, default=PolicySource.MANUAL.value
    )  # MANUAL, SYSTEM, LEARNED
    source_proposal_id: Optional[str] = None
    parent_rule_id: Optional[str] = Field(
        default=None, foreign_key="policy_rules.id"
    )
    # Explicit lineage bridge (INV-GOV-003)
    legacy_rule_id: Optional[str] = Field(
        default=None, foreign_key="policy_rules_legacy.id"
    )

    # Retirement (for retired rules)
    retired_at: Optional[datetime] = None
    retired_by: Optional[str] = None
    retirement_reason: Optional[str] = None
    superseded_by: Optional[str] = Field(
        default=None, foreign_key="policy_rules.id"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    enforcements: list["PolicyEnforcement"] = Relationship(
        back_populates="rule",
        sa_relationship_kwargs={"foreign_keys": "[PolicyEnforcement.rule_id]"},
    )

    def retire(self, by: str, reason: str, superseded_by_id: Optional[str] = None) -> None:
        """Retire this rule (PIN-412)."""
        self.status = PolicyRuleStatus.RETIRED.value
        self.retired_at = utc_now()
        self.retired_by = by
        self.retirement_reason = reason
        self.superseded_by = superseded_by_id
        self.updated_at = utc_now()


class PolicyEnforcement(SQLModel, table=True):
    """
    Policy enforcement record - when a rule triggered.

    PIN-412: Enforcements are append-only history.
    Used for trigger_count_30d and last_triggered_at derivations.
    """

    __tablename__ = "policy_enforcements"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    rule_id: str = Field(foreign_key="policy_rules.id", index=True)
    run_id: Optional[str] = Field(default=None, foreign_key="runs.id", index=True)
    incident_id: Optional[str] = Field(default=None, foreign_key="incidents.id")

    # Enforcement details
    action_taken: str = Field(max_length=16)  # BLOCKED, WARNED, AUDITED
    details: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Timestamps
    triggered_at: datetime = Field(default_factory=utc_now)

    # Relationships
    rule: Optional[PolicyRule] = Relationship(
        back_populates="enforcements",
        sa_relationship_kwargs={"foreign_keys": "[PolicyEnforcement.rule_id]"},
    )


# =============================================================================
# Limits (Budget, Rate, Threshold)
# =============================================================================


class Limit(SQLModel, table=True):
    """
    Limit record - quantitative constraint definition.

    PIN-412: Limits enforce what Governance declares.
    Violations create Incidents, not warnings.
    """

    __tablename__ = "limits"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)

    # Core limit definition
    name: str = Field(max_length=256)
    description: Optional[str] = None
    limit_category: str = Field(max_length=16)  # BUDGET, RATE, THRESHOLD
    limit_type: str = Field(max_length=32)  # COST_USD, TOKENS_*, REQUESTS_*, etc.
    scope: str = Field(
        max_length=16, default=LimitScope.TENANT.value
    )  # GLOBAL, TENANT, PROJECT, AGENT, PROVIDER
    scope_id: Optional[str] = None

    # Limit values
    max_value: Decimal = Field(sa_column=Column(Numeric(18, 4), nullable=False))

    # Budget-specific
    reset_period: Optional[str] = Field(
        default=None, max_length=16
    )  # DAILY, WEEKLY, MONTHLY, NONE
    next_reset_at: Optional[datetime] = None

    # Rate-specific
    window_seconds: Optional[int] = None

    # Threshold-specific
    measurement_window_seconds: Optional[int] = None

    # Enforcement behavior
    enforcement: str = Field(
        max_length=16, default=LimitEnforcement.BLOCK.value
    )  # BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT
    consequence: Optional[str] = Field(
        default=None, max_length=16
    )  # ALERT, INCIDENT, ABORT

    # Status
    status: str = Field(
        max_length=16, default=LimitStatus.ACTIVE.value
    )  # ACTIVE, DISABLED

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    breaches: list["LimitBreach"] = Relationship(back_populates="limit")


class LimitBreach(SQLModel, table=True):
    """
    Limit breach record - when a limit was exceeded.

    PIN-412: Breaches are append-only history.
    Used for breach_count_30d and last_breach_at derivations.
    """

    __tablename__ = "limit_breaches"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    limit_id: str = Field(foreign_key="limits.id", index=True)
    run_id: Optional[str] = Field(default=None, foreign_key="runs.id")
    incident_id: Optional[str] = Field(default=None, foreign_key="incidents.id")

    # Breach details
    breach_type: str = Field(max_length=16)  # BREACHED, EXHAUSTED, THROTTLED, VIOLATED
    value_at_breach: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 4), nullable=True))
    limit_value: Decimal = Field(sa_column=Column(Numeric(18, 4), nullable=False))
    details: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Timestamps
    breached_at: datetime = Field(default_factory=utc_now)
    recovered_at: Optional[datetime] = None

    # Relationships
    limit: Optional[Limit] = Relationship(back_populates="breaches")


# =============================================================================
# Policy Rule Integrity (PIN-412)
# =============================================================================


class IntegrityStatus(str, Enum):
    """Policy rule integrity status values."""

    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class PolicyRuleIntegrity(SQLModel, table=True):
    """
    Policy rule integrity record - current integrity state per rule.

    PIN-412: One row per rule (latest state only).
    Updated when rule is created, modified, retired, or enforcement changes.
    Historical integrity lives in proof / O5.

    INVARIANT: Every ACTIVE policy_rule MUST have exactly one integrity row.
    Enforced by database trigger.
    """

    __tablename__ = "policy_rule_integrity"

    id: str = Field(primary_key=True)
    rule_id: str = Field(foreign_key="policy_rules.id", unique=True)

    # Integrity assessment
    integrity_status: str = Field(max_length=16)  # VERIFIED, DEGRADED, FAILED
    integrity_score: Decimal = Field(sa_column=Column(Numeric(4, 3), nullable=False))
    hash_root: str  # Integrity hash

    # Details (optional JSONB for diagnostics)
    details: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Timestamps
    computed_at: datetime = Field(default_factory=utc_now)


class LimitIntegrity(SQLModel, table=True):
    """
    Limit integrity record - current integrity state per limit.

    PIN-412: One row per limit (latest state only).
    Updated when limit is created, modified, or enforcement changes.
    Historical integrity lives in proof / O5.

    INVARIANT: Every ACTIVE limit MUST have exactly one integrity row.
    Enforced by database trigger.

    Note: Separate from PolicyRuleIntegrity (Option C - explicit, not polymorphic).
    Rules and limits have different lifecycle semantics.
    """

    __tablename__ = "limit_integrity"

    id: str = Field(primary_key=True)
    limit_id: str = Field(foreign_key="limits.id", unique=True)

    # Integrity assessment
    integrity_status: str = Field(max_length=16)  # VERIFIED, DEGRADED, FAILED
    integrity_score: Decimal = Field(sa_column=Column(Numeric(5, 4), nullable=False))

    # Timestamps
    computed_at: datetime = Field(default_factory=utc_now)
