"""M22 KillSwitch Models

Provides:
- KillSwitchState: Tenant/key freeze state tracking
- ProxyCall: OpenAI proxy call logging for replay
- Incident: Auto-grouped failure incidents
- IncidentEvent: Timeline events within incidents
- DefaultGuardrail: Read-only default policy pack

Incident Grouping v1 Heuristics (LOCKED):
- GROUPING_WINDOW_SECONDS: 300 (5 minutes) - Fixed correlation window
- Single root cause per incident - No merging after close
- One call belongs to exactly one incident
- No splitting or re-grouping after incident is created
- Determinism over cleverness
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any, Dict
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ============== ENUMS ==============

class EntityType(str, Enum):
    TENANT = "tenant"
    KEY = "key"


class TriggerType(str, Enum):
    MANUAL = "manual"
    BUDGET = "budget"
    FAILURE_SPIKE = "failure_spike"
    RATE_LIMIT = "rate_limit"
    POLICY_VIOLATION = "policy_violation"


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class GuardrailAction(str, Enum):
    BLOCK = "block"
    WARN = "warn"
    THROTTLE = "throttle"
    FREEZE = "freeze"


class GuardrailCategory(str, Enum):
    COST = "cost"
    RATE = "rate"
    SAFETY = "safety"
    CONTENT = "content"


# ==============================================================================
# INCIDENT GROUPING v1 HEURISTICS (LOCKED - DO NOT MODIFY)
# ==============================================================================
# These constants define deterministic incident grouping behavior.
# Changing these will break incident correlation and customer expectations.
# If you need different behavior, create a v2 with explicit migration.

GROUPING_WINDOW_SECONDS = 300  # 5 minute correlation window
GROUPING_MIN_ERRORS = 3       # Minimum errors to trigger incident
GROUPING_ERROR_RATE_THRESHOLD = 0.5  # 50% error rate triggers incident
GROUPING_COST_SPIKE_MULTIPLIER = 5   # 5x normal cost triggers incident

# v1 Rules (Immutable):
# 1. Single root cause: Each incident has exactly one trigger_type
# 2. Fixed window: Calls within GROUPING_WINDOW_SECONDS are correlated
# 3. No multi-incident: A call belongs to AT MOST one incident
# 4. No merging: Once an incident closes, it never absorbs new calls
# 5. No splitting: An incident is never split into multiple incidents

# ==============================================================================


# ============== KILLSWITCH STATE ==============

class KillSwitchState(SQLModel, table=True):
    """Track freeze state for tenants and API keys."""
    __tablename__ = "killswitch_state"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    entity_type: str = Field(max_length=20)  # 'tenant' or 'key'
    entity_id: str = Field(max_length=100)
    tenant_id: str = Field(max_length=100, index=True)

    is_frozen: bool = Field(default=False)
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[str] = Field(default=None, max_length=100)
    freeze_reason: Optional[str] = None
    unfrozen_at: Optional[datetime] = None
    unfrozen_by: Optional[str] = Field(default=None, max_length=100)

    auto_triggered: bool = Field(default=False)
    trigger_type: Optional[str] = Field(default=None, max_length=50)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def freeze(self, by: str, reason: str, auto: bool = False, trigger: Optional[str] = None):
        """Freeze this entity."""
        self.is_frozen = True
        self.frozen_at = utc_now()
        self.frozen_by = by
        self.freeze_reason = reason
        self.auto_triggered = auto
        self.trigger_type = trigger
        self.unfrozen_at = None
        self.unfrozen_by = None
        self.updated_at = utc_now()

    def unfreeze(self, by: str):
        """Unfreeze this entity."""
        self.is_frozen = False
        self.unfrozen_at = utc_now()
        self.unfrozen_by = by
        self.updated_at = utc_now()


# ============== PROXY CALLS ==============

class ProxyCall(SQLModel, table=True):
    """Log of OpenAI proxy calls for replay and analysis."""
    __tablename__ = "proxy_calls"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(max_length=100, index=True)
    api_key_id: Optional[str] = Field(default=None, max_length=100, index=True)

    # M23 User Tracking: OpenAI standard `user` field for end-user identification
    user_id: Optional[str] = Field(default=None, max_length=255, index=True)

    # Request
    endpoint: str = Field(max_length=100)  # '/v1/chat/completions', '/v1/embeddings'
    model: str = Field(max_length=100)
    request_hash: str = Field(max_length=64, index=True)
    request_json: str  # Full request body

    # Response
    response_hash: Optional[str] = Field(default=None, max_length=64)
    response_json: Optional[str] = None
    status_code: Optional[int] = None
    error_code: Optional[str] = Field(default=None, max_length=50)

    # Tokens & Cost
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    cost_cents: Decimal = Field(default=Decimal("0"))

    # Policy decisions
    policy_decisions_json: Optional[str] = None
    was_blocked: bool = Field(default=False)
    block_reason: Optional[str] = Field(default=None, max_length=100)

    # Timing
    latency_ms: Optional[int] = None
    upstream_latency_ms: Optional[int] = None

    # Replay
    replay_eligible: bool = Field(default=True)
    replayed_from_id: Optional[str] = Field(default=None, max_length=100)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now, index=True)

    @staticmethod
    def hash_request(request_body: dict) -> str:
        """Generate deterministic hash of request for matching."""
        canonical = json.dumps(request_body, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def hash_response(response_body: dict) -> str:
        """Generate deterministic hash of response."""
        canonical = json.dumps(response_body, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def set_policy_decisions(self, decisions: List[Dict[str, Any]]):
        """Set policy decisions as JSON."""
        self.policy_decisions_json = json.dumps(decisions)

    def get_policy_decisions(self) -> List[Dict[str, Any]]:
        """Get policy decisions from JSON."""
        if self.policy_decisions_json:
            return json.loads(self.policy_decisions_json)
        return []


# ============== INCIDENTS ==============

class Incident(SQLModel, table=True):
    """Auto-grouped failure incidents."""
    __tablename__ = "incidents"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(max_length=100, index=True)

    # Summary
    title: str = Field(max_length=255)
    severity: str = Field(max_length=20)  # 'critical', 'high', 'medium', 'low'
    status: str = Field(default="open", max_length=20)  # 'open', 'acknowledged', 'resolved'

    # Root cause
    trigger_type: str = Field(max_length=50)  # 'failure_spike', 'budget_breach', 'rate_limit'
    trigger_value: Optional[str] = None

    # Impact
    calls_affected: int = Field(default=0)
    cost_delta_cents: Decimal = Field(default=Decimal("0"))
    error_rate: Optional[Decimal] = None

    # Actions taken
    auto_action: Optional[str] = Field(default=None, max_length=50)
    action_details_json: Optional[str] = None

    # Timeline
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    # Related entities
    related_call_ids_json: Optional[str] = None
    killswitch_id: Optional[str] = Field(default=None, max_length=100)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = Field(default=None, max_length=100)

    def add_related_call(self, call_id: str):
        """Add a related call ID."""
        ids = self.get_related_call_ids()
        if call_id not in ids:
            ids.append(call_id)
            self.related_call_ids_json = json.dumps(ids)
            self.calls_affected = len(ids)

    def get_related_call_ids(self) -> List[str]:
        """Get list of related call IDs."""
        if self.related_call_ids_json:
            return json.loads(self.related_call_ids_json)
        return []

    def resolve(self, by: str):
        """Mark incident as resolved."""
        self.status = IncidentStatus.RESOLVED.value
        self.resolved_at = utc_now()
        self.resolved_by = by
        self.ended_at = utc_now()
        if self.started_at:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
        self.updated_at = utc_now()


class IncidentEvent(SQLModel, table=True):
    """Timeline events within an incident."""
    __tablename__ = "incident_events"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    incident_id: str = Field(max_length=100, foreign_key="incidents.id", index=True)

    event_type: str = Field(max_length=50)
    description: str
    data_json: Optional[str] = None

    created_at: datetime = Field(default_factory=utc_now, index=True)

    def set_data(self, data: Dict[str, Any]):
        """Set event data as JSON."""
        self.data_json = json.dumps(data)

    def get_data(self) -> Dict[str, Any]:
        """Get event data from JSON."""
        if self.data_json:
            return json.loads(self.data_json)
        return {}


# ============== DEFAULT GUARDRAILS ==============

class DefaultGuardrail(SQLModel, table=True):
    """Read-only default policy pack."""
    __tablename__ = "default_guardrails"

    id: str = Field(primary_key=True, max_length=100)
    name: str = Field(max_length=100, unique=True)
    description: Optional[str] = None
    category: str = Field(max_length=50)  # 'cost', 'rate', 'safety', 'content'

    # Rule definition
    rule_type: str = Field(max_length=50)  # 'max_value', 'pattern_block', 'rate_limit'
    rule_config_json: str

    # Enforcement
    action: str = Field(max_length=50)  # 'block', 'warn', 'throttle', 'freeze'
    is_enabled: bool = Field(default=True)
    is_default: bool = Field(default=True)
    priority: int = Field(default=100)  # Lower = higher priority

    # Version
    version: str = Field(default="v1", max_length=20)
    created_at: datetime = Field(default_factory=utc_now)

    def get_rule_config(self) -> Dict[str, Any]:
        """Get rule configuration from JSON."""
        return json.loads(self.rule_config_json)

    def evaluate(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Evaluate this guardrail against context.
        Returns (passed, reason) where passed=False means violation.
        """
        if not self.is_enabled:
            return True, None

        config = self.get_rule_config()

        if self.rule_type == "max_value":
            field = config.get("field")
            max_val = config.get("max")
            actual = context.get(field, 0)
            if actual > max_val:
                return False, f"{field} ({actual}) exceeds max ({max_val})"
            return True, None

        elif self.rule_type == "rate_limit":
            # Rate limiting is handled at middleware level
            return True, None

        elif self.rule_type == "threshold":
            metric = config.get("metric")
            threshold = config.get("threshold")
            actual = context.get(metric, 0)
            if actual > threshold:
                return False, f"{metric} ({actual}) exceeds threshold ({threshold})"
            return True, None

        elif self.rule_type == "pattern_block":
            patterns = config.get("patterns", [])
            text = context.get("text", "")
            for pattern in patterns:
                if pattern.lower() in text.lower():
                    return False, f"Blocked pattern detected: {pattern[:20]}..."
            return True, None

        return True, None


# ============== PYDANTIC SCHEMAS (API) ==============

class KillSwitchStatus(BaseModel):
    """Response schema for kill switch status."""
    entity_type: str
    entity_id: str
    is_frozen: bool
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[str] = None
    freeze_reason: Optional[str] = None
    auto_triggered: bool = False
    trigger_type: Optional[str] = None


class KillSwitchAction(BaseModel):
    """Request schema for kill switch actions."""
    reason: str
    actor: Optional[str] = "system"


class IncidentSummary(BaseModel):
    """Summary view of an incident."""
    id: str
    title: str
    severity: str
    status: str
    trigger_type: str
    calls_affected: int
    cost_delta_cents: float
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class IncidentDetail(BaseModel):
    """Detailed view of an incident with timeline."""
    id: str
    title: str
    severity: str
    status: str
    trigger_type: str
    trigger_value: Optional[str] = None
    calls_affected: int
    cost_delta_cents: float
    error_rate: Optional[float] = None
    auto_action: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    timeline: List[Dict[str, Any]] = []


class GuardrailSummary(BaseModel):
    """Summary of active guardrails."""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    action: str
    is_enabled: bool
    priority: int


class ProxyCallSummary(BaseModel):
    """Summary of a proxy call."""
    id: str
    endpoint: str
    model: str
    status_code: Optional[int] = None
    was_blocked: bool
    cost_cents: float
    input_tokens: int
    output_tokens: int
    latency_ms: Optional[int] = None
    created_at: datetime
    replay_eligible: bool


class ProxyCallDetail(BaseModel):
    """Detailed view of a proxy call for replay."""
    id: str
    endpoint: str
    model: str
    request_hash: str
    request_body: Dict[str, Any]
    response_body: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    error_code: Optional[str] = None
    was_blocked: bool
    block_reason: Optional[str] = None
    policy_decisions: List[Dict[str, Any]] = []
    cost_cents: float
    input_tokens: int
    output_tokens: int
    latency_ms: Optional[int] = None
    replay_eligible: bool
    created_at: datetime


class ReplayRequest(BaseModel):
    """Request to replay a call."""
    dry_run: bool = False


class ReplayResult(BaseModel):
    """Result of a replay operation.

    Language layer: "Replay proves enforcement" not "request re-executed"
    This shows PROOF that your guardrails work consistently.
    """
    original_call_id: str
    replay_call_id: Optional[str] = None
    dry_run: bool
    same_result: bool
    diff: Optional[Dict[str, Any]] = None

    # Language layer: Trust-building messages
    enforcement_message: str = "✅ ENFORCEMENT VERIFIED: Replay proves your guardrails are working correctly."


class DemoSimulationRequest(BaseModel):
    """Request to simulate an incident."""
    scenario: str = "budget_breach"  # 'budget_breach', 'failure_spike', 'rate_limit'


class DemoSimulationResult(BaseModel):
    """Result of a demo simulation.

    ⚠️ DEMO SAFETY:
    - is_demo is always True for demo simulations
    - demo_warning explains this is not real data
    - before/after show clear value deltas
    - without_killswitch shows what would have happened
    """
    incident_id: str
    scenario: str
    timeline: List[Dict[str, Any]]
    cost_saved_cents: float
    action_taken: str
    message: str

    # NEW: Demo safety and value demonstration fields
    is_demo: bool = True
    demo_warning: str = "⚠️ This is a DEMO simulation. No real billing or tenant state was affected."
    before: Optional[Dict[str, Any]] = None  # State before incident
    after: Optional[Dict[str, Any]] = None   # State after KillSwitch intervention
    without_killswitch: Optional[Dict[str, Any]] = None  # What would have happened
