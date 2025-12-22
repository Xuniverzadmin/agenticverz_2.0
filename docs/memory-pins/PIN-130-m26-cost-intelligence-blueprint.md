# PIN-130: M26 Cost Intelligence Blueprint

**Status:** SPECIFICATION
**Category:** Milestone / Cost Management / Dashboard
**Created:** 2025-12-22
**Duration:** 1.5 weeks
**Dependencies:** M13, M14, M25
**Related PINs:** PIN-128, PIN-129, PIN-067, PIN-068

---

## Objective

Build a comprehensive Cost Intelligence Dashboard that provides:
1. Real-time cost visibility per tenant, feature, and user
2. Cost anomaly detection (reusing M9 failure pattern infrastructure)
3. Budget alerts and enforcement
4. Cost projection and forecasting
5. Integration with M25 feedback loop (cost anomaly → incident → policy)

**The Invariant:** Every token spent is attributable to a feature, user, and tenant. Every anomaly is actionable.

---

## Current State Inventory

### What Already Exists (60%)

#### M13: Cost Calculator (PIN-067)

| Component | Location | Status |
|-----------|----------|--------|
| CostTracker | `backend/app/observability/cost_tracker.py` | ✅ Live |
| CostQuota | `backend/app/observability/cost_tracker.py` | ✅ Live |
| CostRecord | `backend/app/observability/cost_tracker.py` | ✅ Live |
| CostAlert | `backend/app/observability/cost_tracker.py` | ✅ Live |
| Per-request tracking | CostTracker.record_cost() | ✅ Live |
| Hourly/daily aggregates | CostTracker._hourly_spend | ✅ Live |

**Key Classes:**
```python
class CostQuota:
    daily_limit_cents: int = 10000      # $100/day default
    hourly_limit_cents: int = 1000      # $10/hour default
    per_request_limit_cents: int = 100  # $1/request default
    per_workflow_limit_cents: int = 500 # $5/workflow default
    warn_threshold_percent: float = 0.8 # Warn at 80%

class CostRecord:
    timestamp: datetime
    tenant_id: str
    workflow_id: str
    skill_id: str
    cost_cents: float
    input_tokens: int
    output_tokens: int
    model: str
```

#### M14: BudgetLLM Governance (PIN-070)

| Component | Location | Status |
|-----------|----------|--------|
| LLM cost envelopes | `backend/app/agents/skills/llm_invoke_governed.py` | ✅ Live |
| Citation metering | `backend/app/agents/skills/llm_invoke_governed.py` | ✅ Live |
| Risk scoring | `backend/app/agents/sba/validator.py` | ✅ Live |
| Exhaustion fallback | `backend/app/costsim/config.py` | ✅ Live |

#### M21: Tenant Tracking (PIN-089)

| Component | Location | Status |
|-----------|----------|--------|
| Tenant model | `backend/app/models/tenant.py` | ✅ Live |
| Tenant API | `backend/app/api/tenants.py` | ✅ Live |
| Per-tenant isolation | Multi-tenant middleware | ✅ Live |

#### CostSim V2 (M6)

| Component | Location | Status |
|-----------|----------|--------|
| CostSimMetrics | `backend/app/costsim/metrics.py` | ✅ Live |
| Drift detection | `backend/app/costsim/v2_adapter.py` | ✅ Live |
| Circuit breaker | `backend/app/models/costsim_cb.py` | ✅ Live |
| Divergence reports | `backend/app/costsim/divergence.py` | ✅ Live |

---

### What to Build (40%)

| Component | Effort | Priority |
|-----------|--------|----------|
| Feature tagging API | 2 days | P0 |
| Cost attribution dashboard | 3 days | P0 |
| Cost anomaly detection | 2 days | P0 |
| Budget alerts UI | 1 day | P0 |
| Cost projection engine | 2 days | P1 |
| M25 loop integration | 1 day | P0 |

---

## Architecture

### Cost Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          M26 COST INTELLIGENCE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                          │
│  │   LLM CALL   │  Every API call tagged with:                             │
│  │   (Origin)   │  • tenant_id, user_id, feature_tag                       │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (1) Record cost                                                   │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │    COST      │  Store in cost_records table                             │
│  │   TRACKER    │  Aggregate in Redis for real-time                        │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (2) Check for anomalies                                           │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │   ANOMALY    │  Compare against:                                        │
│  │   DETECTOR   │  • Historical patterns (7-day avg)                       │
│  │              │  • Budget thresholds                                     │
│  │              │  • Per-user limits                                       │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (3) If anomaly detected                                           │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │  M25 LOOP    │  Create incident → pattern → recovery → policy           │
│  │  INTEGRATION │  "Cost anomaly for user_8372"                            │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (4) Update dashboard                                              │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │  DASHBOARD   │  Real-time spend, anomalies, projections                 │
│  │     UI       │  Budget vs actual, feature breakdown                     │
│  └──────────────┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Feature Tagging System

### Concept

Every LLM call must be tagged with a `feature_tag` that identifies what feature initiated the call.

```python
# Feature tags are hierarchical
feature_tags = [
    "customer_support.chat",
    "customer_support.email_draft",
    "content_gen.blog_post",
    "content_gen.social_media",
    "code_assistant.completion",
    "code_assistant.review",
    "search.semantic",
    "search.rag_retrieval",
]
```

### API Changes

```python
# backend/app/api/cost_intelligence.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

router = APIRouter(prefix="/cost", tags=["cost-intelligence"])

# ============ Feature Tags ============

class FeatureTag(BaseModel):
    tag: str                    # e.g., "customer_support.chat"
    display_name: str           # e.g., "Customer Support - Chat"
    description: Optional[str]
    budget_cents: Optional[int] # Per-feature budget limit
    is_active: bool = True

class FeatureTagCreate(BaseModel):
    tag: str
    display_name: str
    description: Optional[str] = None
    budget_cents: Optional[int] = None

@router.post("/features")
async def create_feature_tag(
    tag: FeatureTagCreate,
    tenant_id: str = Depends(get_tenant_id)
) -> FeatureTag:
    """Register a new feature tag for cost tracking."""
    return await create_feature(tag, tenant_id)

@router.get("/features")
async def list_feature_tags(
    tenant_id: str = Depends(get_tenant_id)
) -> List[FeatureTag]:
    """List all registered feature tags."""
    return await get_features(tenant_id)

@router.put("/features/{tag}/budget")
async def set_feature_budget(
    tag: str,
    budget_cents: int,
    tenant_id: str = Depends(get_tenant_id)
) -> FeatureTag:
    """Set budget for a specific feature."""
    return await update_feature_budget(tag, budget_cents, tenant_id)
```

### LLM Call Integration

```python
# Modify existing LLM invoke to require feature_tag

class LLMInvokeRequest(BaseModel):
    prompt: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    feature_tag: str  # NEW: Required for cost attribution
    user_id: Optional[str] = None  # NEW: For per-user tracking

async def invoke_llm(request: LLMInvokeRequest, tenant_id: str):
    # ... existing logic ...

    # Record cost with feature tag
    await cost_tracker.record_cost(
        tenant_id=tenant_id,
        user_id=request.user_id,
        feature_tag=request.feature_tag,
        cost_cents=calculated_cost,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=request.model
    )
```

---

## Cost Attribution Dashboard

### API Endpoints

```python
# backend/app/api/cost_intelligence.py (continued)

# ============ Cost Queries ============

class CostSummary(BaseModel):
    total_spend_cents: int
    budget_cents: Optional[int]
    budget_used_pct: float
    period_start: datetime
    period_end: datetime

class CostByFeature(BaseModel):
    feature_tag: str
    display_name: str
    spend_cents: int
    request_count: int
    avg_cost_per_request: float
    budget_cents: Optional[int]
    budget_used_pct: Optional[float]

class CostByUser(BaseModel):
    user_id: str
    spend_cents: int
    request_count: int
    avg_cost_per_request: float
    is_anomalous: bool
    anomaly_reason: Optional[str]

class CostByModel(BaseModel):
    model: str
    spend_cents: int
    request_count: int
    input_tokens: int
    output_tokens: int
    avg_cost_per_1k_tokens: float

class DashboardData(BaseModel):
    summary: CostSummary
    by_feature: List[CostByFeature]
    by_user: List[CostByUser]
    by_model: List[CostByModel]
    anomalies: List[CostAnomaly]
    projection: CostProjection

@router.get("/dashboard")
async def get_cost_dashboard(
    tenant_id: str = Depends(get_tenant_id),
    period: str = Query("day", regex="^(hour|day|week|month)$")
) -> DashboardData:
    """Get complete cost dashboard data."""
    return await build_dashboard(tenant_id, period)

@router.get("/summary")
async def get_cost_summary(
    tenant_id: str = Depends(get_tenant_id),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None
) -> CostSummary:
    """Get cost summary for a period."""
    return await calculate_summary(tenant_id, start, end)

@router.get("/by-feature")
async def get_cost_by_feature(
    tenant_id: str = Depends(get_tenant_id),
    period: str = Query("day", regex="^(hour|day|week|month)$"),
    limit: int = Query(10, ge=1, le=100)
) -> List[CostByFeature]:
    """Get cost breakdown by feature."""
    return await aggregate_by_feature(tenant_id, period, limit)

@router.get("/by-user")
async def get_cost_by_user(
    tenant_id: str = Depends(get_tenant_id),
    period: str = Query("day", regex="^(hour|day|week|month)$"),
    limit: int = Query(20, ge=1, le=100),
    anomalous_only: bool = False
) -> List[CostByUser]:
    """Get cost breakdown by user."""
    return await aggregate_by_user(tenant_id, period, limit, anomalous_only)

@router.get("/by-model")
async def get_cost_by_model(
    tenant_id: str = Depends(get_tenant_id),
    period: str = Query("day", regex="^(hour|day|week|month)$")
) -> List[CostByModel]:
    """Get cost breakdown by model."""
    return await aggregate_by_model(tenant_id, period)
```

---

## Cost Anomaly Detection

### Anomaly Types

```python
# backend/app/cost/anomaly_detector.py

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class AnomalyType(str, Enum):
    USER_SPIKE = "user_spike"           # Single user unusually high
    FEATURE_SPIKE = "feature_spike"     # Feature cost spike
    BUDGET_WARNING = "budget_warning"   # Approaching budget
    BUDGET_EXCEEDED = "budget_exceeded" # Budget exceeded
    UNUSUAL_MODEL = "unusual_model"     # Expensive model usage spike
    OFF_HOURS = "off_hours"             # Usage outside business hours

class AnomalySeverity(str, Enum):
    LOW = "low"           # Informational
    MEDIUM = "medium"     # Worth investigating
    HIGH = "high"         # Immediate attention
    CRITICAL = "critical" # Budget exceeded / action required

@dataclass
class CostAnomaly:
    id: str
    tenant_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    entity_type: str          # "user", "feature", "model"
    entity_id: str            # user_id, feature_tag, or model
    current_value_cents: int
    expected_value_cents: int
    deviation_pct: float
    message: str
    detected_at: datetime
    incident_id: Optional[str] = None  # M25 integration
```

### Detection Engine

```python
# backend/app/cost/anomaly_detector.py (continued)

class CostAnomalyDetector:
    """
    Detects cost anomalies using historical patterns.

    Detection methods:
    1. Z-score: Flag if > 2 std deviations from 7-day avg
    2. Budget threshold: Flag if > 80% of budget
    3. Rate of change: Flag if > 200% increase in 1 hour
    4. Absolute threshold: Flag any single user > $10/day
    """

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.thresholds = AnomalyThresholds()

    async def detect_anomalies(
        self,
        tenant_id: str,
        window_hours: int = 24
    ) -> List[CostAnomaly]:
        """Run all anomaly detection checks."""
        anomalies = []

        # 1. User-level anomalies
        anomalies.extend(await self._detect_user_spikes(tenant_id, window_hours))

        # 2. Feature-level anomalies
        anomalies.extend(await self._detect_feature_spikes(tenant_id, window_hours))

        # 3. Budget anomalies
        anomalies.extend(await self._detect_budget_anomalies(tenant_id))

        # 4. Model usage anomalies
        anomalies.extend(await self._detect_model_anomalies(tenant_id, window_hours))

        return anomalies

    async def _detect_user_spikes(
        self,
        tenant_id: str,
        window_hours: int
    ) -> List[CostAnomaly]:
        """Detect users with unusual spending."""
        # Get current period spend per user
        current = await self._get_user_spend(tenant_id, hours=window_hours)

        # Get historical average (7-day)
        historical = await self._get_user_spend_avg(tenant_id, days=7)

        anomalies = []
        for user_id, spend in current.items():
            avg = historical.get(user_id, 0)

            # Z-score detection
            if avg > 0:
                std = await self._get_user_spend_std(tenant_id, user_id, days=7)
                z_score = (spend - avg) / max(std, 1)

                if z_score > 2.0:
                    anomalies.append(CostAnomaly(
                        id=generate_id("anom"),
                        tenant_id=tenant_id,
                        anomaly_type=AnomalyType.USER_SPIKE,
                        severity=self._calculate_severity(z_score),
                        entity_type="user",
                        entity_id=user_id,
                        current_value_cents=spend,
                        expected_value_cents=int(avg),
                        deviation_pct=(spend - avg) / avg * 100,
                        message=f"User {user_id} spent ${spend/100:.2f} today, "
                               f"{(spend/avg - 1)*100:.0f}% above average",
                        detected_at=datetime.now(timezone.utc)
                    ))

            # Absolute threshold ($10/day)
            elif spend > 1000:
                anomalies.append(CostAnomaly(
                    id=generate_id("anom"),
                    tenant_id=tenant_id,
                    anomaly_type=AnomalyType.USER_SPIKE,
                    severity=AnomalySeverity.MEDIUM,
                    entity_type="user",
                    entity_id=user_id,
                    current_value_cents=spend,
                    expected_value_cents=0,
                    deviation_pct=100,
                    message=f"New user {user_id} spent ${spend/100:.2f} today",
                    detected_at=datetime.now(timezone.utc)
                ))

        return anomalies
```

### Anomaly API

```python
# backend/app/api/cost_intelligence.py (continued)

@router.get("/anomalies")
async def get_cost_anomalies(
    tenant_id: str = Depends(get_tenant_id),
    hours: int = Query(24, ge=1, le=168),
    severity: Optional[AnomalySeverity] = None
) -> List[CostAnomaly]:
    """Get detected cost anomalies."""
    anomalies = await detector.detect_anomalies(tenant_id, hours)

    if severity:
        anomalies = [a for a in anomalies if a.severity == severity]

    return anomalies

@router.post("/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> dict:
    """Mark anomaly as acknowledged."""
    await mark_acknowledged(anomaly_id, tenant_id)
    return {"status": "acknowledged"}

@router.post("/anomalies/{anomaly_id}/create-incident")
async def create_incident_from_anomaly(
    anomaly_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> dict:
    """Create M25 incident from cost anomaly."""
    anomaly = await get_anomaly(anomaly_id, tenant_id)

    # Create incident via M25 integration
    incident = await create_cost_incident(
        tenant_id=tenant_id,
        anomaly=anomaly
    )

    return {"incident_id": incident.id}
```

---

## M25 Loop Integration

### Cost Anomaly → Incident Flow

```python
# backend/app/integrations/cost_to_incident.py

async def on_cost_anomaly_detected(anomaly: CostAnomaly) -> Optional[Incident]:
    """
    Bridge: Cost anomaly → M25 incident loop.

    Only create incidents for HIGH/CRITICAL severity.
    """
    if anomaly.severity not in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
        return None

    # Create incident
    incident = await create_incident(
        tenant_id=anomaly.tenant_id,
        incident_type="cost_anomaly",
        severity=anomaly.severity.value,
        title=f"Cost Anomaly: {anomaly.anomaly_type.value}",
        description=anomaly.message,
        metadata={
            "anomaly_id": anomaly.id,
            "entity_type": anomaly.entity_type,
            "entity_id": anomaly.entity_id,
            "current_value_cents": anomaly.current_value_cents,
            "expected_value_cents": anomaly.expected_value_cents,
            "deviation_pct": anomaly.deviation_pct
        }
    )

    # Update anomaly with incident reference
    await link_anomaly_to_incident(anomaly.id, incident.id)

    # Dispatch to M25 integration loop
    await dispatch_loop_event(LoopEvent(
        event_id=generate_id("evt"),
        incident_id=incident.id,
        tenant_id=anomaly.tenant_id,
        stage=LoopStage.INCIDENT_CREATED,
        timestamp=datetime.now(timezone.utc),
        details={"source": "cost_anomaly", "anomaly_id": anomaly.id}
    ))

    return incident
```

### Cost-Aware Recovery Suggestions

```python
# backend/app/integrations/cost_recovery.py

COST_RECOVERY_TEMPLATES = {
    AnomalyType.USER_SPIKE: [
        {
            "action": "rate_limit_user",
            "description": "Apply per-user rate limit",
            "confidence": 0.9,
            "params": {"requests_per_hour": 100}
        },
        {
            "action": "notify_user",
            "description": "Send cost alert email to user",
            "confidence": 0.95,
            "params": {}
        }
    ],
    AnomalyType.FEATURE_SPIKE: [
        {
            "action": "chunk_optimization",
            "description": "Reduce context size for this feature",
            "confidence": 0.7,
            "params": {"max_tokens": 2000}
        },
        {
            "action": "model_downgrade",
            "description": "Use cheaper model for this feature",
            "confidence": 0.8,
            "params": {"fallback_model": "claude-haiku"}
        }
    ],
    AnomalyType.BUDGET_EXCEEDED: [
        {
            "action": "enforce_hard_limit",
            "description": "Block requests exceeding budget",
            "confidence": 0.95,
            "params": {}
        },
        {
            "action": "escalate_to_billing",
            "description": "Create billing alert for review",
            "confidence": 0.99,
            "params": {}
        }
    ]
}

async def generate_cost_recovery(
    pattern: FailurePattern,
    incident: Incident
) -> RecoverySuggestion:
    """Generate recovery suggestion for cost anomaly."""
    anomaly_type = AnomalyType(incident.metadata.get("anomaly_type"))

    templates = COST_RECOVERY_TEMPLATES.get(anomaly_type, [])

    if not templates:
        return await generate_generic_recovery(pattern, incident)

    # Select best template based on context
    template = select_best_template(templates, incident)

    return RecoverySuggestion(
        incident_id=incident.id,
        pattern_id=pattern.id,
        action=template["action"],
        description=template["description"],
        confidence=template["confidence"],
        params=template["params"],
        source="cost_recovery_template"
    )
```

### Cost-Aware Policies

```python
# backend/app/integrations/cost_policy.py

async def generate_cost_prevention_policy(
    recovery: RecoveryAction,
    pattern: FailurePattern
) -> PolicyRule:
    """Generate policy to prevent future cost anomalies."""

    if recovery.action == "rate_limit_user":
        return PolicyRule(
            name=f"Rate limit for pattern {pattern.id[:8]}",
            category="operational",
            condition=f"user.requests_per_hour > {recovery.params['requests_per_hour']}",
            action="rate_limit",
            scope=PolicyScope.TENANT,
            source_type="cost_recovery",
            source_pattern_id=pattern.id
        )

    elif recovery.action == "model_downgrade":
        return PolicyRule(
            name=f"Model fallback for {pattern.feature_tag}",
            category="routing",
            condition=f"feature_tag == '{pattern.feature_tag}' AND cost_estimate > 50",
            action="route_to_cheaper_model",
            params={"fallback_model": recovery.params["fallback_model"]},
            scope=PolicyScope.TENANT,
            source_type="cost_recovery",
            source_pattern_id=pattern.id
        )

    elif recovery.action == "enforce_hard_limit":
        return PolicyRule(
            name="Budget enforcement",
            category="safety",
            condition="tenant.daily_spend >= tenant.daily_budget",
            action="block",
            scope=PolicyScope.TENANT,
            source_type="cost_recovery",
            source_pattern_id=pattern.id
        )
```

---

## Cost Projection Engine

```python
# backend/app/cost/projection.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

@dataclass
class CostProjection:
    current_spend_cents: int
    projected_daily_cents: int
    projected_weekly_cents: int
    projected_monthly_cents: int
    budget_cents: Optional[int]
    days_until_budget_exceeded: Optional[int]
    trend: str  # "increasing", "stable", "decreasing"
    confidence: float

class CostProjectionEngine:
    """
    Projects future costs based on historical patterns.

    Methods:
    1. Linear regression on 7-day trend
    2. Weighted moving average (recent days weighted higher)
    3. Seasonality adjustment (day-of-week patterns)
    """

    async def project(
        self,
        tenant_id: str,
        lookback_days: int = 7
    ) -> CostProjection:
        """Generate cost projection."""
        # Get historical data
        daily_costs = await self._get_daily_costs(tenant_id, lookback_days)

        if len(daily_costs) < 3:
            return self._simple_projection(daily_costs)

        # Calculate trend
        trend_slope = self._calculate_trend(daily_costs)
        trend = "increasing" if trend_slope > 0.05 else \
                "decreasing" if trend_slope < -0.05 else "stable"

        # Project forward
        current = daily_costs[-1] if daily_costs else 0
        projected_daily = int(current * (1 + trend_slope))
        projected_weekly = projected_daily * 7
        projected_monthly = projected_daily * 30

        # Budget analysis
        budget = await self._get_budget(tenant_id)
        days_until_exceeded = None
        if budget and projected_daily > 0:
            remaining = budget - sum(daily_costs)
            days_until_exceeded = max(0, int(remaining / projected_daily))

        return CostProjection(
            current_spend_cents=sum(daily_costs),
            projected_daily_cents=projected_daily,
            projected_weekly_cents=projected_weekly,
            projected_monthly_cents=projected_monthly,
            budget_cents=budget,
            days_until_budget_exceeded=days_until_exceeded,
            trend=trend,
            confidence=min(0.95, 0.5 + len(daily_costs) * 0.05)
        )
```

---

## Database Schema

```python
# backend/alembic/versions/043_m26_cost_intelligence.py

"""M26: Cost Intelligence Dashboard

Revision ID: 043_m26_cost_intel
Revises: 042_m25_integration
Create Date: 2025-12-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '043_m26_cost_intel'
down_revision = '042_m25_integration'

def upgrade():
    # Feature tags table
    op.create_table(
        'feature_tags',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('tag', sa.String(128), nullable=False),
        sa.Column('display_name', sa.String(256), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('budget_cents', sa.Integer),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        'uq_feature_tag_tenant',
        'feature_tags',
        ['tenant_id', 'tag']
    )
    op.create_index('idx_feature_tags_tenant', 'feature_tags', ['tenant_id'])

    # Cost records table (high-volume, partitioned by date)
    op.create_table(
        'cost_records',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('user_id', sa.String(64)),
        sa.Column('feature_tag', sa.String(128)),
        sa.Column('workflow_id', sa.String(64)),
        sa.Column('skill_id', sa.String(64)),
        sa.Column('model', sa.String(64), nullable=False),
        sa.Column('cost_cents', sa.Float, nullable=False),
        sa.Column('input_tokens', sa.Integer, nullable=False),
        sa.Column('output_tokens', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cost_records_tenant_date', 'cost_records',
                    ['tenant_id', 'created_at'])
    op.create_index('idx_cost_records_feature', 'cost_records',
                    ['tenant_id', 'feature_tag', 'created_at'])
    op.create_index('idx_cost_records_user', 'cost_records',
                    ['tenant_id', 'user_id', 'created_at'])

    # Cost anomalies table
    op.create_table(
        'cost_anomalies',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('anomaly_type', sa.String(32), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False),
        sa.Column('entity_type', sa.String(32), nullable=False),
        sa.Column('entity_id', sa.String(128), nullable=False),
        sa.Column('current_value_cents', sa.Integer, nullable=False),
        sa.Column('expected_value_cents', sa.Integer, nullable=False),
        sa.Column('deviation_pct', sa.Float, nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('incident_id', sa.String(64)),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True)),
        sa.Column('acknowledged_by', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cost_anomalies_tenant', 'cost_anomalies',
                    ['tenant_id', 'created_at'])
    op.create_index('idx_cost_anomalies_severity', 'cost_anomalies',
                    ['tenant_id', 'severity', 'created_at'])

    # Cost budgets table
    op.create_table(
        'cost_budgets',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('budget_type', sa.String(32), nullable=False),  # 'daily', 'weekly', 'monthly'
        sa.Column('budget_cents', sa.Integer, nullable=False),
        sa.Column('alert_threshold_pct', sa.Float, server_default='0.8'),
        sa.Column('enforce_hard_limit', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        'uq_cost_budget_tenant_type',
        'cost_budgets',
        ['tenant_id', 'budget_type']
    )

    # Daily cost aggregates (materialized for performance)
    op.create_table(
        'cost_daily_aggregates',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('feature_tag', sa.String(128)),
        sa.Column('user_id', sa.String(64)),
        sa.Column('model', sa.String(64)),
        sa.Column('total_cents', sa.Integer, nullable=False),
        sa.Column('request_count', sa.Integer, nullable=False),
        sa.Column('input_tokens', sa.Integer, nullable=False),
        sa.Column('output_tokens', sa.Integer, nullable=False),
    )
    op.create_unique_constraint(
        'uq_cost_daily_agg',
        'cost_daily_aggregates',
        ['tenant_id', 'date', 'feature_tag', 'user_id', 'model']
    )
    op.create_index('idx_cost_daily_tenant_date', 'cost_daily_aggregates',
                    ['tenant_id', 'date'])

def downgrade():
    op.drop_table('cost_daily_aggregates')
    op.drop_table('cost_budgets')
    op.drop_table('cost_anomalies')
    op.drop_table('cost_records')
    op.drop_table('feature_tags')
```

---

## Console UI

### Dashboard Component

```typescript
// website/aos-console/console/src/pages/cost/CostDashboard.tsx

import React from 'react';
import { useCostDashboard } from '../../hooks/useCostDashboard';
import { formatCurrency, formatPercent } from '../../utils/format';

interface CostDashboardProps {
  period: 'hour' | 'day' | 'week' | 'month';
}

export function CostDashboard({ period }: CostDashboardProps) {
  const { data, isLoading } = useCostDashboard(period);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="cost-dashboard">
      {/* Summary Header */}
      <div className="dashboard-header">
        <div className="summary-card">
          <h2>Total Spend</h2>
          <div className="amount">
            {formatCurrency(data.summary.total_spend_cents)}
          </div>
          {data.summary.budget_cents && (
            <div className="budget-bar">
              <div
                className="budget-fill"
                style={{ width: `${data.summary.budget_used_pct}%` }}
              />
              <span className="budget-label">
                {formatPercent(data.summary.budget_used_pct)} of{' '}
                {formatCurrency(data.summary.budget_cents)} budget
              </span>
            </div>
          )}
        </div>

        <div className="projection-card">
          <h2>Projection</h2>
          <div className="projection-grid">
            <div>
              <span className="label">Daily</span>
              <span className="value">
                {formatCurrency(data.projection.projected_daily_cents)}
              </span>
            </div>
            <div>
              <span className="label">Monthly</span>
              <span className="value">
                {formatCurrency(data.projection.projected_monthly_cents)}
              </span>
            </div>
            <div>
              <span className="label">Trend</span>
              <TrendIndicator trend={data.projection.trend} />
            </div>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="dashboard-grid">
        {/* Cost by Feature */}
        <div className="panel">
          <h3>Cost by Feature</h3>
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Spend</th>
                <th>Requests</th>
                <th>Avg</th>
              </tr>
            </thead>
            <tbody>
              {data.by_feature.map(f => (
                <tr key={f.feature_tag}>
                  <td>{f.display_name}</td>
                  <td>{formatCurrency(f.spend_cents)}</td>
                  <td>{f.request_count.toLocaleString()}</td>
                  <td>{formatCurrency(f.avg_cost_per_request)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Anomalies */}
        <div className="panel">
          <h3>Cost Anomalies</h3>
          {data.anomalies.length === 0 ? (
            <div className="empty-state">
              ✓ No anomalies detected
            </div>
          ) : (
            <div className="anomaly-list">
              {data.anomalies.map(a => (
                <AnomalyCard key={a.id} anomaly={a} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Cost by User */}
      <div className="panel full-width">
        <h3>Top Users by Spend</h3>
        <UserCostTable users={data.by_user} />
      </div>

      {/* Cost by Model */}
      <div className="panel full-width">
        <h3>Cost by Model</h3>
        <ModelCostChart models={data.by_model} />
      </div>
    </div>
  );
}
```

### Anomaly Card Component

```typescript
// website/aos-console/console/src/components/AnomalyCard.tsx

interface AnomalyCardProps {
  anomaly: CostAnomaly;
}

export function AnomalyCard({ anomaly }: AnomalyCardProps) {
  const severityColors = {
    low: 'blue',
    medium: 'yellow',
    high: 'orange',
    critical: 'red'
  };

  return (
    <div className={`anomaly-card severity-${anomaly.severity}`}>
      <div className="anomaly-header">
        <span className={`severity-badge ${severityColors[anomaly.severity]}`}>
          {anomaly.severity.toUpperCase()}
        </span>
        <span className="anomaly-type">
          {formatAnomalyType(anomaly.anomaly_type)}
        </span>
      </div>

      <div className="anomaly-body">
        <p>{anomaly.message}</p>
        <div className="anomaly-stats">
          <span>
            Current: {formatCurrency(anomaly.current_value_cents)}
          </span>
          <span>
            Expected: {formatCurrency(anomaly.expected_value_cents)}
          </span>
          <span className="deviation">
            +{anomaly.deviation_pct.toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="anomaly-actions">
        {!anomaly.acknowledged_at && (
          <button onClick={() => acknowledgeAnomaly(anomaly.id)}>
            Acknowledge
          </button>
        )}
        {!anomaly.incident_id && anomaly.severity !== 'low' && (
          <button
            className="create-incident"
            onClick={() => createIncident(anomaly.id)}
          >
            Create Incident
          </button>
        )}
        {anomaly.incident_id && (
          <a href={`/guard/incidents/${anomaly.incident_id}`}>
            View Incident
          </a>
        )}
      </div>
    </div>
  );
}
```

---

## Implementation Phases

### Phase 1: Data Layer (Days 1-2)

| Task | Owner | Status |
|------|-------|--------|
| Create migration 043_m26_cost_intelligence | Backend | ⬜ |
| Implement CostRecord model | Backend | ⬜ |
| Implement FeatureTag model | Backend | ⬜ |
| Add feature_tag to LLM invoke | Backend | ⬜ |
| Create /cost API router | Backend | ⬜ |

### Phase 2: Aggregation & Queries (Days 3-4)

| Task | Owner | Status |
|------|-------|--------|
| Implement cost aggregation queries | Backend | ⬜ |
| Build daily aggregate job | Backend | ⬜ |
| Add Redis caching for real-time | Backend | ⬜ |
| Implement /cost/dashboard endpoint | Backend | ⬜ |
| Unit tests for aggregation | Backend | ⬜ |

### Phase 3: Anomaly Detection (Days 5-6)

| Task | Owner | Status |
|------|-------|--------|
| Implement CostAnomalyDetector | Backend | ⬜ |
| Add anomaly detection job (hourly) | Backend | ⬜ |
| Implement /cost/anomalies endpoint | Backend | ⬜ |
| M25 integration (anomaly → incident) | Backend | ⬜ |
| Cost recovery templates | Backend | ⬜ |

### Phase 4: Console UI (Days 7-9)

| Task | Owner | Status |
|------|-------|--------|
| CostDashboard page | Frontend | ⬜ |
| AnomalyCard component | Frontend | ⬜ |
| Cost charts (by feature, model) | Frontend | ⬜ |
| Budget configuration UI | Frontend | ⬜ |
| Feature tag management UI | Frontend | ⬜ |

### Phase 5: Projection & Polish (Days 10-11)

| Task | Owner | Status |
|------|-------|--------|
| CostProjectionEngine | Backend | ⬜ |
| Add projection to dashboard | Frontend | ⬜ |
| Integration tests | Backend | ⬜ |
| Performance optimization | Backend | ⬜ |
| Documentation | All | ⬜ |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Feature tag coverage | > 95% | % of LLM calls with feature_tag |
| Anomaly detection latency | < 5 minutes | Time from spike to detection |
| Dashboard load time | < 2 seconds | P95 for /cost/dashboard |
| False positive rate | < 10% | % of anomalies that are false alarms |
| Budget alert accuracy | 100% | All budget thresholds trigger alerts |
| M25 integration rate | > 80% | % of HIGH/CRITICAL anomalies creating incidents |

---

## Rollback Plan

If cost intelligence causes issues:

1. **Feature flag:** `COST_INTELLIGENCE_ENABLED=false` disables all new endpoints
2. **Anomaly flag:** `COST_ANOMALY_DETECTION_ENABLED=false` disables detection job
3. **Rollback migration:** `alembic downgrade -1`
4. **Clear data:** `TRUNCATE cost_records, cost_anomalies`

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Created PIN-130 M26 Cost Intelligence Blueprint |
