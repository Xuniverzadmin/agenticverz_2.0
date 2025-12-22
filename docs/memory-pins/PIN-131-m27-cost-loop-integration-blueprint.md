# PIN-131: M27 Cost Loop Integration Blueprint

**Status:** SPECIFICATION
**Category:** Milestone / Integration / Cost Management
**Created:** 2025-12-22
**Duration:** 1 week
**Dependencies:** M25, M26
**Related PINs:** PIN-128, PIN-129, PIN-130

---

## Objective

Wire Cost Intelligence (M26) into the Pillar Integration Loop (M25), completing the feedback cycle where cost anomalies trigger incidents that generate policies preventing future cost overruns.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     M27: COST → LOOP INTEGRATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐                                                          │
│   │    COST      │                                                          │
│   │  ANOMALY     │  "User spent $89 today (340% above avg)"                │
│   └──────┬───────┘                                                          │
│          │                                                                   │
│          │ (1) Auto-create incident                                          │
│          ▼                                                                   │
│   ┌──────────────┐                                                          │
│   │   INCIDENT   │  Type: cost_anomaly                                      │
│   │   CONSOLE    │  Severity: HIGH                                          │
│   └──────┬───────┘                                                          │
│          │                                                                   │
│          │ (2) Match/create cost pattern                                     │
│          ▼                                                                   │
│   ┌──────────────┐                                                          │
│   │   FAILURE    │  Pattern: "user_cost_spike"                              │
│   │   CATALOG    │  Signature: {entity: user, deviation: >200%}             │
│   └──────┬───────┘                                                          │
│          │                                                                   │
│          │ (3) Generate cost-aware recovery                                  │
│          ▼                                                                   │
│   ┌──────────────┐                                                          │
│   │   RECOVERY   │  Suggestion: "Apply rate limit to user"                  │
│   │   ENGINE     │  OR: "Route to cheaper model"                            │
│   └──────┬───────┘                                                          │
│          │                                                                   │
│          │ (4) Create budget enforcement policy                              │
│          ▼                                                                   │
│   ┌──────────────┐                                                          │
│   │   POLICY     │  Rule: "IF user.daily_spend > $50 THEN rate_limit"      │
│   │   LAYER      │  Category: operational                                   │
│   └──────┬───────┘                                                          │
│          │                                                                   │
│          │ (5) Adjust CARE routing for cost optimization                     │
│          ▼                                                                   │
│   ┌──────────────┐                                                          │
│   │    CARE      │  Action: Route expensive features to cheaper models      │
│   │   ROUTING    │  Action: Add cost-check probe before execution           │
│   └──────────────┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The Invariant:** Every cost anomaly enters the loop. Every loop completion reduces future cost risk.

---

## Prerequisites

### From M25 (Pillar Integration)

| Component | Location | Required |
|-----------|----------|----------|
| IntegrationDispatcher | `backend/app/integrations/dispatcher.py` | ✅ |
| LoopEvent | `backend/app/integrations/events.py` | ✅ |
| loop_traces table | Migration 042 | ✅ |
| Bridge 1-5 infrastructure | `backend/app/integrations/` | ✅ |

### From M26 (Cost Intelligence)

| Component | Location | Required |
|-----------|----------|----------|
| CostAnomalyDetector | `backend/app/cost/anomaly_detector.py` | ✅ |
| CostAnomaly model | `backend/app/cost/anomaly_detector.py` | ✅ |
| cost_anomalies table | Migration 043 | ✅ |
| /cost/anomalies API | `backend/app/api/cost_intelligence.py` | ✅ |

---

## Integration Points (5 Bridges)

### Bridge C1: Cost Anomaly → Incident

**Trigger:** CostAnomalyDetector detects HIGH/CRITICAL anomaly
**Action:** Auto-create incident in Guard Console

```python
# backend/app/integrations/cost_to_loop.py

from app.integrations.dispatcher import IntegrationDispatcher
from app.integrations.events import LoopEvent, LoopStage
from app.cost.anomaly_detector import CostAnomaly, AnomalySeverity
from app.models.incidents import Incident, IncidentType

class CostLoopBridge:
    """
    Bridge C1: Cost Anomaly → M25 Integration Loop.

    Automatically creates incidents from cost anomalies,
    feeding them into the standard recovery/policy flow.
    """

    def __init__(self, dispatcher: IntegrationDispatcher):
        self.dispatcher = dispatcher

    async def on_anomaly_detected(self, anomaly: CostAnomaly) -> Optional[str]:
        """
        Create incident from cost anomaly if severity warrants.

        Returns incident_id if created, None otherwise.
        """
        # Only HIGH and CRITICAL anomalies trigger incidents
        if anomaly.severity not in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
            return None

        # Check for duplicate (same entity, same hour)
        existing = await self._find_existing_incident(anomaly)
        if existing:
            # Update existing incident with new data point
            await self._append_to_incident(existing, anomaly)
            return existing.id

        # Create new incident
        incident = await self._create_cost_incident(anomaly)

        # Link anomaly to incident
        await self._link_anomaly(anomaly.id, incident.id)

        # Dispatch to M25 loop
        await self.dispatcher.dispatch(LoopEvent(
            event_id=generate_id("evt"),
            incident_id=incident.id,
            tenant_id=anomaly.tenant_id,
            stage=LoopStage.INCIDENT_CREATED,
            timestamp=datetime.now(timezone.utc),
            details={
                "source": "cost_anomaly",
                "anomaly_id": anomaly.id,
                "anomaly_type": anomaly.anomaly_type.value,
                "severity": anomaly.severity.value,
                "entity_type": anomaly.entity_type,
                "entity_id": anomaly.entity_id,
                "deviation_pct": anomaly.deviation_pct
            }
        ))

        return incident.id

    async def _create_cost_incident(self, anomaly: CostAnomaly) -> Incident:
        """Create incident from cost anomaly."""

        # Map anomaly type to incident title
        titles = {
            AnomalyType.USER_SPIKE: f"Cost Spike: User {anomaly.entity_id}",
            AnomalyType.FEATURE_SPIKE: f"Cost Spike: Feature {anomaly.entity_id}",
            AnomalyType.BUDGET_WARNING: f"Budget Warning: {anomaly.deviation_pct:.0f}% used",
            AnomalyType.BUDGET_EXCEEDED: f"Budget Exceeded: {anomaly.entity_id}",
            AnomalyType.UNUSUAL_MODEL: f"Unusual Model Usage: {anomaly.entity_id}",
        }

        return await create_incident(
            tenant_id=anomaly.tenant_id,
            incident_type=IncidentType.COST_ANOMALY,
            severity=anomaly.severity.value,
            title=titles.get(anomaly.anomaly_type, f"Cost Anomaly: {anomaly.entity_id}"),
            description=anomaly.message,
            metadata={
                "anomaly_id": anomaly.id,
                "anomaly_type": anomaly.anomaly_type.value,
                "entity_type": anomaly.entity_type,
                "entity_id": anomaly.entity_id,
                "current_value_cents": anomaly.current_value_cents,
                "expected_value_cents": anomaly.expected_value_cents,
                "deviation_pct": anomaly.deviation_pct
            }
        )
```

---

### Bridge C2: Cost Pattern → Failure Catalog

**Trigger:** Incident created from cost anomaly
**Action:** Match or create cost-specific failure pattern

```python
# backend/app/integrations/cost_pattern_matcher.py

class CostPatternMatcher:
    """
    Bridge C2: Match cost anomalies to failure patterns.

    Cost patterns are categorized by:
    - Entity type (user, feature, model, tenant)
    - Anomaly type (spike, budget, unusual)
    - Severity threshold
    """

    # Pre-defined cost pattern signatures
    COST_PATTERN_SIGNATURES = {
        "user_daily_spike": {
            "entity_type": "user",
            "anomaly_type": "user_spike",
            "min_deviation_pct": 200,
            "description": "Single user daily spend spike > 200%"
        },
        "user_hourly_spike": {
            "entity_type": "user",
            "anomaly_type": "user_spike",
            "min_deviation_pct": 500,
            "time_window": "hourly",
            "description": "Single user hourly spend spike > 500%"
        },
        "feature_cost_explosion": {
            "entity_type": "feature",
            "anomaly_type": "feature_spike",
            "min_deviation_pct": 300,
            "description": "Feature cost increase > 300%"
        },
        "budget_breach": {
            "entity_type": "tenant",
            "anomaly_type": "budget_exceeded",
            "min_deviation_pct": 100,
            "description": "Tenant budget exceeded"
        },
        "model_cost_anomaly": {
            "entity_type": "model",
            "anomaly_type": "unusual_model",
            "min_deviation_pct": 200,
            "description": "Unusual expensive model usage"
        }
    }

    async def match_cost_pattern(
        self,
        anomaly: CostAnomaly
    ) -> PatternMatchResult:
        """Match anomaly to existing or new cost pattern."""

        # Build signature from anomaly
        signature = self._build_signature(anomaly)

        # Try to match existing pattern
        existing = await self._find_matching_pattern(signature)

        if existing:
            await self._increment_pattern_count(existing.id)
            return PatternMatchResult(
                matched=True,
                pattern_id=existing.id,
                is_new=False,
                confidence=self._calculate_confidence(existing, anomaly)
            )

        # Create new pattern
        pattern = await self._create_cost_pattern(signature, anomaly)

        return PatternMatchResult(
            matched=True,
            pattern_id=pattern.id,
            is_new=True,
            confidence=0.8  # Lower confidence for new patterns
        )

    def _build_signature(self, anomaly: CostAnomaly) -> dict:
        """Build pattern signature from anomaly."""
        return {
            "entity_type": anomaly.entity_type,
            "anomaly_type": anomaly.anomaly_type.value,
            "deviation_range": self._deviation_bucket(anomaly.deviation_pct),
            "severity": anomaly.severity.value
        }

    def _deviation_bucket(self, pct: float) -> str:
        """Bucket deviation percentages for pattern matching."""
        if pct >= 500:
            return "extreme"  # 500%+
        elif pct >= 300:
            return "high"     # 300-500%
        elif pct >= 200:
            return "medium"   # 200-300%
        else:
            return "low"      # <200%
```

**Database Changes:**

```python
# Add cost-specific fields to failure_patterns (Migration 044)

op.add_column('failure_patterns',
    sa.Column('pattern_category', sa.String(32))  # 'error', 'cost', 'performance'
)
op.add_column('failure_patterns',
    sa.Column('cost_signature', JSONB)  # Cost-specific matching criteria
)
```

---

### Bridge C3: Cost Recovery Suggestions

**Trigger:** Cost pattern matched
**Action:** Generate cost-specific recovery suggestion

```python
# backend/app/integrations/cost_recovery_generator.py

class CostRecoveryGenerator:
    """
    Bridge C3: Generate recovery suggestions for cost anomalies.

    Recovery strategies by anomaly type:
    - USER_SPIKE → Rate limit, notify user, review usage
    - FEATURE_SPIKE → Optimize prompts, model downgrade, caching
    - BUDGET_EXCEEDED → Hard block, escalate, increase budget
    - UNUSUAL_MODEL → Route to cheaper model, review routing
    """

    RECOVERY_STRATEGIES = {
        AnomalyType.USER_SPIKE: [
            {
                "action": "rate_limit_user",
                "description": "Apply rate limit to user",
                "confidence": 0.9,
                "auto_apply": False,
                "params": {
                    "requests_per_hour": 50,
                    "duration_hours": 24
                }
            },
            {
                "action": "notify_user",
                "description": "Send cost alert notification to user",
                "confidence": 0.95,
                "auto_apply": True,  # Safe to auto-apply
                "params": {
                    "template": "cost_spike_alert"
                }
            },
            {
                "action": "review_usage",
                "description": "Flag for usage review",
                "confidence": 0.85,
                "auto_apply": True,
                "params": {}
            }
        ],

        AnomalyType.FEATURE_SPIKE: [
            {
                "action": "optimize_prompts",
                "description": "Reduce prompt size for this feature",
                "confidence": 0.7,
                "auto_apply": False,
                "params": {
                    "max_prompt_tokens": 2000,
                    "max_output_tokens": 1000
                }
            },
            {
                "action": "enable_caching",
                "description": "Enable response caching for feature",
                "confidence": 0.8,
                "auto_apply": False,
                "params": {
                    "cache_ttl_seconds": 3600
                }
            },
            {
                "action": "model_downgrade",
                "description": "Route to cheaper model",
                "confidence": 0.75,
                "auto_apply": False,
                "params": {
                    "target_model": "claude-haiku",
                    "fallback_threshold_cents": 50
                }
            }
        ],

        AnomalyType.BUDGET_EXCEEDED: [
            {
                "action": "enforce_hard_limit",
                "description": "Block requests exceeding budget",
                "confidence": 0.95,
                "auto_apply": False,  # Dangerous - needs approval
                "params": {}
            },
            {
                "action": "escalate_to_admin",
                "description": "Escalate to account admin",
                "confidence": 0.99,
                "auto_apply": True,
                "params": {
                    "notification_channels": ["email", "slack"]
                }
            },
            {
                "action": "temporary_throttle",
                "description": "Throttle all requests by 50%",
                "confidence": 0.85,
                "auto_apply": False,
                "params": {
                    "throttle_pct": 50,
                    "duration_hours": 4
                }
            }
        ],

        AnomalyType.UNUSUAL_MODEL: [
            {
                "action": "route_to_cheaper",
                "description": "Route to cost-optimized model",
                "confidence": 0.85,
                "auto_apply": False,
                "params": {
                    "target_model": "claude-haiku",
                    "quality_threshold": 0.9
                }
            },
            {
                "action": "review_routing_rules",
                "description": "Flag routing configuration for review",
                "confidence": 0.9,
                "auto_apply": True,
                "params": {}
            }
        ]
    }

    async def generate_recovery(
        self,
        pattern: FailurePattern,
        incident: Incident
    ) -> List[RecoverySuggestion]:
        """Generate recovery suggestions for cost incident."""

        anomaly_type = AnomalyType(incident.metadata.get("anomaly_type"))
        strategies = self.RECOVERY_STRATEGIES.get(anomaly_type, [])

        suggestions = []
        for strategy in strategies:
            suggestion = RecoverySuggestion(
                id=generate_id("rec"),
                incident_id=incident.id,
                pattern_id=pattern.id,
                action=strategy["action"],
                description=strategy["description"],
                confidence=strategy["confidence"],
                auto_apply=strategy["auto_apply"],
                params=strategy["params"],
                source="cost_recovery_generator",
                status="pending"
            )
            suggestions.append(suggestion)

            # Auto-apply if confidence high enough and safe
            if strategy["auto_apply"] and strategy["confidence"] >= 0.9:
                await self._apply_recovery(suggestion)
                suggestion.status = "applied"

        return suggestions
```

---

### Bridge C4: Cost Policy Generation

**Trigger:** Recovery applied
**Action:** Generate budget enforcement policy

```python
# backend/app/integrations/cost_policy_generator.py

class CostPolicyGenerator:
    """
    Bridge C4: Generate policies from cost recoveries.

    Policy categories:
    - operational: Rate limits, throttling
    - routing: Model selection, cost-aware routing
    - safety: Hard budget blocks
    """

    POLICY_TEMPLATES = {
        "rate_limit_user": {
            "category": "operational",
            "condition_template": "user.id == '{entity_id}' AND user.requests_today > {requests_per_hour}",
            "action": "rate_limit",
            "description_template": "Rate limit user {entity_id} to {requests_per_hour} requests/hour"
        },
        "model_downgrade": {
            "category": "routing",
            "condition_template": "feature_tag == '{feature_tag}' AND request.estimated_cost_cents > {fallback_threshold_cents}",
            "action": "route_to_model",
            "action_params_template": {"model": "{target_model}"},
            "description_template": "Route {feature_tag} to {target_model} when cost > ${threshold}"
        },
        "enforce_hard_limit": {
            "category": "safety",
            "condition_template": "tenant.daily_spend_cents >= tenant.daily_budget_cents",
            "action": "block",
            "description_template": "Block requests when daily budget exceeded"
        },
        "temporary_throttle": {
            "category": "operational",
            "condition_template": "tenant.id == '{tenant_id}' AND NOW() < '{expires_at}'",
            "action": "throttle",
            "action_params_template": {"rate": "{throttle_pct}"},
            "description_template": "Throttle tenant {tenant_id} by {throttle_pct}% until {expires_at}"
        },
        "optimize_prompts": {
            "category": "operational",
            "condition_template": "feature_tag == '{feature_tag}'",
            "action": "limit_tokens",
            "action_params_template": {
                "max_prompt": "{max_prompt_tokens}",
                "max_output": "{max_output_tokens}"
            },
            "description_template": "Limit {feature_tag} to {max_prompt_tokens} prompt / {max_output_tokens} output tokens"
        }
    }

    async def generate_policy(
        self,
        recovery: RecoveryAction,
        pattern: FailurePattern,
        incident: Incident
    ) -> Optional[PolicyRule]:
        """Generate policy from applied recovery."""

        template = self.POLICY_TEMPLATES.get(recovery.action)
        if not template:
            return None

        # Build context for template substitution
        context = {
            **recovery.params,
            "entity_id": incident.metadata.get("entity_id"),
            "feature_tag": incident.metadata.get("feature_tag", "unknown"),
            "tenant_id": incident.tenant_id,
            "threshold": recovery.params.get("fallback_threshold_cents", 0) / 100,
            "expires_at": (datetime.now(timezone.utc) + timedelta(
                hours=recovery.params.get("duration_hours", 24)
            )).isoformat()
        }

        # Generate policy
        policy = PolicyRule(
            id=generate_id("pol"),
            tenant_id=incident.tenant_id,
            name=f"Cost Policy: {recovery.action}",
            description=template["description_template"].format(**context),
            category=template["category"],
            condition=template["condition_template"].format(**context),
            action=template["action"],
            action_params=self._format_params(
                template.get("action_params_template", {}),
                context
            ),
            source_type="cost_recovery",
            source_pattern_id=pattern.id,
            source_recovery_id=recovery.id,
            generation_confidence=recovery.confidence,
            status="active" if recovery.confidence >= 0.9 else "draft",
            created_at=datetime.now(timezone.utc)
        )

        await save_policy_rule(policy)

        return policy
```

---

### Bridge C5: Cost-Aware CARE Routing

**Trigger:** Cost policy created
**Action:** Adjust CARE routing for cost optimization

```python
# backend/app/integrations/cost_routing_adjuster.py

class CostRoutingAdjuster:
    """
    Bridge C5: Adjust CARE routing based on cost policies.

    Routing adjustments:
    - Add cost estimation probe before execution
    - Route expensive requests to cheaper models
    - Add budget-check middleware
    - Adjust agent confidence based on cost efficiency
    """

    async def on_cost_policy_created(
        self,
        policy: PolicyRule
    ) -> List[RoutingAdjustment]:
        """Adjust CARE routing based on new cost policy."""

        adjustments = []

        if policy.action == "route_to_model":
            # Add model routing adjustment
            adjustment = await self._add_model_routing(policy)
            adjustments.append(adjustment)

        elif policy.action == "rate_limit":
            # Add rate limit probe
            adjustment = await self._add_rate_limit_probe(policy)
            adjustments.append(adjustment)

        elif policy.action == "block":
            # Add budget check probe (highest priority)
            adjustment = await self._add_budget_check_probe(policy)
            adjustments.append(adjustment)

        elif policy.action == "limit_tokens":
            # Add token limit enforcement
            adjustment = await self._add_token_limit(policy)
            adjustments.append(adjustment)

        # Notify CARE governor
        await self._notify_governor(adjustments)

        return adjustments

    async def _add_model_routing(self, policy: PolicyRule) -> RoutingAdjustment:
        """Add cost-based model routing rule."""
        return RoutingAdjustment(
            id=generate_id("adj"),
            adjustment_type="model_routing",
            scope=policy.condition,
            target_model=policy.action_params.get("model"),
            priority=80,  # High priority but below safety
            source_policy_id=policy.id,
            created_at=datetime.now(timezone.utc)
        )

    async def _add_budget_check_probe(self, policy: PolicyRule) -> RoutingAdjustment:
        """Add pre-execution budget verification probe."""
        return RoutingAdjustment(
            id=generate_id("adj"),
            adjustment_type="probe",
            probe_type="budget_check",
            scope="all",  # Global scope for budget blocks
            priority=100,  # Highest priority
            action_on_fail="block",
            source_policy_id=policy.id,
            created_at=datetime.now(timezone.utc)
        )

    async def _add_rate_limit_probe(self, policy: PolicyRule) -> RoutingAdjustment:
        """Add rate limiting probe."""
        return RoutingAdjustment(
            id=generate_id("adj"),
            adjustment_type="probe",
            probe_type="rate_limit",
            scope=policy.condition,
            priority=90,
            params=policy.action_params,
            source_policy_id=policy.id,
            created_at=datetime.now(timezone.utc)
        )
```

---

## Cost Estimation Probe

New CARE probe for pre-execution cost estimation:

```python
# backend/app/routing/probes/cost_probe.py

class CostEstimationProbe:
    """
    CARE probe that estimates request cost before execution.

    Used to:
    1. Route to cheaper models if estimate exceeds threshold
    2. Block requests that would exceed budget
    3. Warn users about expensive operations
    """

    # Cost per 1K tokens by model (in cents)
    MODEL_COSTS = {
        "claude-opus-4-5-20251101": {"input": 1.5, "output": 7.5},
        "claude-sonnet-4-20250514": {"input": 0.3, "output": 1.5},
        "claude-haiku": {"input": 0.025, "output": 0.125},
        "gpt-4o": {"input": 0.5, "output": 1.5},
        "gpt-4o-mini": {"input": 0.015, "output": 0.06},
    }

    async def probe(
        self,
        request: RoutingRequest,
        context: RoutingContext
    ) -> ProbeResult:
        """Estimate cost and return routing decision."""

        # Estimate tokens
        prompt_tokens = self._estimate_prompt_tokens(request)
        output_tokens = self._estimate_output_tokens(request)

        # Calculate cost for requested model
        model = request.model or context.default_model
        cost_cents = self._calculate_cost(model, prompt_tokens, output_tokens)

        # Check against thresholds
        if await self._exceeds_budget(context.tenant_id, cost_cents):
            return ProbeResult(
                status="blocked",
                reason="budget_exceeded",
                message=f"Request would exceed budget (${cost_cents/100:.2f})",
                metadata={"estimated_cost_cents": cost_cents}
            )

        if cost_cents > context.cost_threshold_cents:
            # Suggest cheaper model
            cheaper = self._find_cheaper_model(model, prompt_tokens, output_tokens)
            if cheaper:
                return ProbeResult(
                    status="reroute",
                    reason="cost_optimization",
                    suggested_model=cheaper["model"],
                    message=f"Routing to {cheaper['model']} to save ${(cost_cents - cheaper['cost'])/100:.2f}",
                    metadata={
                        "original_cost_cents": cost_cents,
                        "optimized_cost_cents": cheaper["cost"]
                    }
                )

        return ProbeResult(
            status="allowed",
            metadata={"estimated_cost_cents": cost_cents}
        )

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        output_tokens: int
    ) -> int:
        """Calculate cost in cents."""
        costs = self.MODEL_COSTS.get(model, {"input": 1.0, "output": 5.0})
        return int(
            (prompt_tokens / 1000 * costs["input"]) +
            (output_tokens / 1000 * costs["output"])
        )
```

---

## Database Migration

```python
# backend/alembic/versions/044_m27_cost_loop_integration.py

"""M27: Cost Loop Integration

Revision ID: 044_m27_cost_loop
Revises: 043_m26_cost_intel
Create Date: 2025-12-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '044_m27_cost_loop'
down_revision = '043_m26_cost_intel'

def upgrade():
    # Add cost category to failure patterns
    op.add_column('failure_patterns',
        sa.Column('pattern_category', sa.String(32), server_default='error')
    )
    op.add_column('failure_patterns',
        sa.Column('cost_signature', JSONB)
    )
    op.create_index('idx_failure_patterns_category',
        'failure_patterns', ['pattern_category']
    )

    # Add cost fields to incidents
    op.add_column('incidents',
        sa.Column('incident_category', sa.String(32), server_default='error')
    )
    op.add_column('incidents',
        sa.Column('cost_impact_cents', sa.Integer)
    )

    # Cost routing adjustments
    op.create_table(
        'cost_routing_adjustments',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('adjustment_type', sa.String(32), nullable=False),
        sa.Column('scope', sa.Text),
        sa.Column('target_model', sa.String(64)),
        sa.Column('probe_type', sa.String(32)),
        sa.Column('priority', sa.Integer, server_default='50'),
        sa.Column('params', JSONB),
        sa.Column('source_policy_id', sa.String(64)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_cost_routing_tenant',
        'cost_routing_adjustments', ['tenant_id', 'is_active']
    )

    # Add IncidentType.COST_ANOMALY
    # (handled by enum extension or new column)

def downgrade():
    op.drop_table('cost_routing_adjustments')
    op.drop_column('incidents', 'cost_impact_cents')
    op.drop_column('incidents', 'incident_category')
    op.drop_index('idx_failure_patterns_category')
    op.drop_column('failure_patterns', 'cost_signature')
    op.drop_column('failure_patterns', 'pattern_category')
```

---

## Console UI Updates

### Cost Incident View

```typescript
// website/aos-console/console/src/pages/guard/incidents/CostIncidentDetail.tsx

interface CostIncidentDetailProps {
  incident: Incident;
}

export function CostIncidentDetail({ incident }: CostIncidentDetailProps) {
  const costData = incident.metadata;

  return (
    <div className="cost-incident-detail">
      <div className="cost-summary">
        <div className="metric">
          <span className="label">Current Spend</span>
          <span className="value critical">
            {formatCurrency(costData.current_value_cents)}
          </span>
        </div>
        <div className="metric">
          <span className="label">Expected</span>
          <span className="value">
            {formatCurrency(costData.expected_value_cents)}
          </span>
        </div>
        <div className="metric">
          <span className="label">Deviation</span>
          <span className="value warning">
            +{costData.deviation_pct.toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="entity-info">
        <span className="label">{costData.entity_type}</span>
        <span className="value">{costData.entity_id}</span>
      </div>

      {/* Show loop progress */}
      <LoopProgress incidentId={incident.id} />

      {/* Cost-specific recovery actions */}
      <CostRecoveryPanel incidentId={incident.id} />
    </div>
  );
}
```

### Cost Recovery Panel

```typescript
// website/aos-console/console/src/components/CostRecoveryPanel.tsx

export function CostRecoveryPanel({ incidentId }: { incidentId: string }) {
  const { data: suggestions } = useCostRecoveries(incidentId);

  return (
    <div className="cost-recovery-panel">
      <h3>Recovery Suggestions</h3>

      {suggestions?.map(suggestion => (
        <div key={suggestion.id} className="recovery-card">
          <div className="recovery-header">
            <span className="action">{formatAction(suggestion.action)}</span>
            <ConfidenceBadge value={suggestion.confidence} />
          </div>

          <p className="description">{suggestion.description}</p>

          {suggestion.status === 'pending' && (
            <div className="recovery-actions">
              <button
                className="apply-btn"
                onClick={() => applyRecovery(suggestion.id)}
              >
                Apply
              </button>
              <button
                className="dismiss-btn"
                onClick={() => dismissRecovery(suggestion.id)}
              >
                Dismiss
              </button>
            </div>
          )}

          {suggestion.status === 'applied' && (
            <div className="applied-badge">
              ✓ Applied {formatTime(suggestion.applied_at)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

---

## Testing Strategy

```python
# backend/tests/test_m27_cost_loop.py

class TestCostLoopIntegration:
    """Test cost anomaly → M25 loop integration."""

    async def test_high_severity_anomaly_creates_incident(self, db, redis):
        """HIGH severity anomaly should create incident."""
        anomaly = CostAnomaly(
            id="anom_test",
            tenant_id="tenant_1",
            anomaly_type=AnomalyType.USER_SPIKE,
            severity=AnomalySeverity.HIGH,
            entity_type="user",
            entity_id="user_123",
            current_value_cents=8900,
            expected_value_cents=2000,
            deviation_pct=345,
            message="User spent $89 today",
            detected_at=datetime.now(timezone.utc)
        )

        bridge = CostLoopBridge(dispatcher)
        incident_id = await bridge.on_anomaly_detected(anomaly)

        assert incident_id is not None

        incident = await get_incident(incident_id)
        assert incident.incident_type == IncidentType.COST_ANOMALY
        assert incident.metadata["anomaly_id"] == anomaly.id

    async def test_low_severity_anomaly_no_incident(self, db, redis):
        """LOW severity anomaly should NOT create incident."""
        anomaly = CostAnomaly(
            severity=AnomalySeverity.LOW,
            # ...
        )

        bridge = CostLoopBridge(dispatcher)
        incident_id = await bridge.on_anomaly_detected(anomaly)

        assert incident_id is None

    async def test_cost_incident_triggers_full_loop(self, db, redis):
        """Cost incident should complete all 5 loop stages."""
        anomaly = create_test_cost_anomaly(severity=AnomalySeverity.CRITICAL)

        bridge = CostLoopBridge(dispatcher)
        incident_id = await bridge.on_anomaly_detected(anomaly)

        # Wait for loop completion
        status = await wait_for_loop_completion(incident_id, timeout=30)

        assert status.is_complete
        assert "pattern_matched" in status.stages_completed
        assert "recovery_suggested" in status.stages_completed
        assert "policy_generated" in status.stages_completed
        assert "routing_adjusted" in status.stages_completed

    async def test_cost_recovery_generates_rate_limit_policy(self, db, redis):
        """Rate limit recovery should generate operational policy."""
        incident = await create_cost_incident(
            anomaly_type=AnomalyType.USER_SPIKE,
            entity_id="user_456"
        )

        # Apply rate limit recovery
        recovery = await apply_recovery(
            incident_id=incident.id,
            action="rate_limit_user",
            params={"requests_per_hour": 50}
        )

        # Check policy generated
        policies = await get_policies_for_incident(incident.id)
        assert len(policies) >= 1

        policy = policies[0]
        assert policy.category == "operational"
        assert policy.action == "rate_limit"
        assert "user_456" in policy.condition

    async def test_budget_exceeded_adds_block_probe(self, db, redis):
        """Budget exceeded policy should add blocking probe."""
        policy = await create_cost_policy(
            action="block",
            category="safety"
        )

        adjuster = CostRoutingAdjuster()
        adjustments = await adjuster.on_cost_policy_created(policy)

        assert len(adjustments) >= 1

        probe_adj = next(a for a in adjustments if a.adjustment_type == "probe")
        assert probe_adj.probe_type == "budget_check"
        assert probe_adj.priority == 100  # Highest priority
```

---

## Implementation Phases

### Phase 1: Bridge Infrastructure (Days 1-2)

| Task | Owner | Status |
|------|-------|--------|
| Create CostLoopBridge class | Backend | ⬜ |
| Wire anomaly detector to bridge | Backend | ⬜ |
| Create migration 044 | Backend | ⬜ |
| Add IncidentType.COST_ANOMALY | Backend | ⬜ |
| Unit tests for Bridge C1 | Backend | ⬜ |

### Phase 2: Pattern & Recovery (Days 3-4)

| Task | Owner | Status |
|------|-------|--------|
| Implement CostPatternMatcher | Backend | ⬜ |
| Implement CostRecoveryGenerator | Backend | ⬜ |
| Define recovery strategy templates | Backend | ⬜ |
| Integration tests for C2, C3 | Backend | ⬜ |

### Phase 3: Policy & Routing (Days 5-6)

| Task | Owner | Status |
|------|-------|--------|
| Implement CostPolicyGenerator | Backend | ⬜ |
| Implement CostRoutingAdjuster | Backend | ⬜ |
| Create CostEstimationProbe | Backend | ⬜ |
| Integration tests for C4, C5 | Backend | ⬜ |

### Phase 4: Console & E2E (Day 7)

| Task | Owner | Status |
|------|-------|--------|
| CostIncidentDetail component | Frontend | ⬜ |
| CostRecoveryPanel component | Frontend | ⬜ |
| Full loop E2E tests | Backend | ⬜ |
| Documentation | All | ⬜ |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Anomaly → Incident rate | 100% | All HIGH/CRITICAL anomalies create incidents |
| Pattern match accuracy | > 85% | Similar cost anomalies match same pattern |
| Recovery suggestion rate | > 90% | Cost incidents receive at least 1 suggestion |
| Policy generation rate | > 80% | Applied recoveries generate policies |
| Routing adjustment rate | 100% | Cost policies trigger routing changes |
| Loop completion time | < 10 seconds | P95 from anomaly to routing adjustment |

---

## Rollback Plan

If integration causes issues:

1. **Feature flag:** `COST_LOOP_INTEGRATION_ENABLED=false`
2. **Disable bridges individually:**
   - `COST_BRIDGE_C1_ENABLED=false` (anomaly → incident)
   - `COST_BRIDGE_C2_ENABLED=false` (pattern matching)
   - `COST_BRIDGE_C3_ENABLED=false` (recovery generation)
   - `COST_BRIDGE_C4_ENABLED=false` (policy generation)
   - `COST_BRIDGE_C5_ENABLED=false` (routing adjustment)
3. **Rollback migration:** `alembic downgrade -1`

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Created PIN-131 M27 Cost Loop Integration Blueprint |
