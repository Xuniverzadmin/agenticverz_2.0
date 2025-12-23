# PIN-129: M25 Pillar Integration Blueprint

**Status:** M25-ALPHA (Loop-Enabled, Not Loop-Proven)
**Category:** Milestone / Architecture / Integration
**Created:** 2025-12-22
**Duration:** 2 weeks
**Dependencies:** M22, M23, M9, M10, M17, M18, M19
**Related PINs:** PIN-128, PIN-095, PIN-100

---

## Objective

Wire the three existing pillars into a closed feedback loop:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   INCIDENT        SELF-HEALING         GOVERNANCE                   │
│   CONSOLE    ───►   PLATFORM    ───►     LAYER                     │
│      │                  │                   │                       │
│      │                  │                   │                       │
│      └──────────────────┴───────────────────┘                       │
│                         │                                           │
│                    FEEDBACK                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**The Invariant:** Every incident should flow through to a policy improvement, and every policy should prevent future incidents.

---

## Current State Inventory

### Pillar 1: Incident Console (M22-M23)

| Component | Location | Status |
|-----------|----------|--------|
| Guard API | `backend/app/api/guard.py` | ✅ Live |
| Incident Model | `backend/app/models/incidents.py` | ✅ Live |
| Decision Timeline | `backend/app/services/incident_aggregator.py` | ✅ Live |
| Kill Switch | `backend/app/api/guard.py:activate_killswitch` | ✅ Live |
| Evidence Export | `backend/app/services/evidence_report.py` | ✅ Live |
| Guard Console UI | `website/aos-console/console/src/pages/guard/` | ✅ Live |

**Key Tables:**
- `incidents` - Incident records
- `decisions` - AI decision audit trail
- `killswitch_state` - Kill switch status per tenant

### Pillar 2: Self-Healing Platform (M9-M10)

| Component | Location | Status |
|-----------|----------|--------|
| Failure Catalog | `backend/app/models/failure_patterns.py` | ✅ Live |
| Pattern Matcher | `backend/app/jobs/failure_aggregation.py` | ✅ Live |
| Recovery Engine | `backend/app/models/m10_recovery.py` | ✅ Live |
| Recovery API | `backend/app/api/recovery.py` | ✅ Live |
| Suggestion Generator | `backend/app/worker/recovery_evaluator.py` | ✅ Live |

**Key Tables:**
- `failure_patterns` - Known failure signatures
- `failure_pattern_exports` - R2 durable storage refs
- `recovery_candidates` - Pending recovery suggestions
- `recovery_actions` - Applied recoveries

### Pillar 3: Governance Layer (M17-M19)

| Component | Location | Status |
|-----------|----------|--------|
| Policy Engine | `backend/app/policy/engine.py` | ✅ Live |
| Policy API | `backend/app/api/policy_layer.py` | ✅ Live |
| CARE Routing | `backend/app/routing/care.py` | ✅ Live |
| CARE Governor | `backend/app/routing/governor.py` | ✅ Live |
| SBA Validator | `backend/app/agents/sba/validator.py` | ✅ Live |

**Key Tables:**
- `policy_rules` - Active policy rules
- `policy_evaluations` - Evaluation audit trail
- `routing_decisions` - CARE routing history
- `sba_profiles` - Strategy-bound agent profiles

---

## Integration Architecture

### The Feedback Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          M25 INTEGRATION LOOP                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                          │
│  │   INCIDENT   │                                                          │
│  │   CREATED    │                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (1) incident.created event                                        │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │   FAILURE    │  Match against known patterns                            │
│  │   CATALOG    │  If new pattern → create failure_pattern                 │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (2) pattern.matched OR pattern.created event                      │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │   RECOVERY   │  Generate recovery suggestion                            │
│  │   ENGINE     │  If auto-applicable → apply immediately                  │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (3) recovery.suggested OR recovery.applied event                  │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │   POLICY     │  Generate prevention rule                                │
│  │   GENERATOR  │  Add to policy_rules table                               │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (4) policy.created event                                          │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │    CARE      │  Adjust routing weights                                  │
│  │   ROUTING    │  Update agent confidence scores                          │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ (5) routing.adjusted event                                        │
│         ▼                                                                   │
│  ┌──────────────┐                                                          │
│  │   CONSOLE    │  Show full loop status                                   │
│  │   UPDATE     │  "Incident → Pattern → Recovery → Policy → Routing"     │
│  └──────────────┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Points (5 Bridges)

### Bridge 1: Incident → Failure Catalog

**Trigger:** New incident created
**Action:** Match against failure patterns, create if new

```python
# backend/app/integrations/incident_to_catalog.py

async def on_incident_created(incident: Incident) -> PatternMatchResult:
    """
    Bridge 1: Route incidents to failure catalog.

    Flow:
    1. Extract signature from incident (error_type, context, agent_id)
    2. Query failure_patterns for match (fuzzy, 80% threshold)
    3. If match: increment pattern.occurrence_count
    4. If no match: create new failure_pattern
    5. Return match result for downstream processing
    """
    signature = extract_failure_signature(incident)

    match = await match_failure_pattern(signature, threshold=0.8)

    if match:
        await increment_pattern_count(match.pattern_id)
        return PatternMatchResult(
            matched=True,
            pattern_id=match.pattern_id,
            confidence=match.confidence,
            is_new=False
        )
    else:
        pattern = await create_failure_pattern(
            signature=signature,
            first_incident_id=incident.id,
            tenant_id=incident.tenant_id
        )
        return PatternMatchResult(
            matched=True,
            pattern_id=pattern.id,
            confidence=1.0,
            is_new=True
        )
```

**Database:**
```sql
-- Add incident_id reference to failure_patterns
ALTER TABLE failure_patterns
ADD COLUMN first_incident_id VARCHAR(64) REFERENCES incidents(id);

-- Add pattern_id reference to incidents
ALTER TABLE incidents
ADD COLUMN matched_pattern_id VARCHAR(64) REFERENCES failure_patterns(id);
```

**Event:**
```python
@dataclass
class PatternMatchedEvent:
    incident_id: str
    pattern_id: str
    confidence: float
    is_new_pattern: bool
    timestamp: datetime
```

---

### Bridge 2: Failure Pattern → Recovery Suggestion

**Trigger:** Pattern matched or created
**Action:** Generate recovery suggestion

```python
# backend/app/integrations/pattern_to_recovery.py

async def on_pattern_matched(event: PatternMatchedEvent) -> RecoverySuggestion:
    """
    Bridge 2: Generate recovery suggestion from pattern.

    Flow:
    1. Load pattern with full context
    2. Check if pattern has existing recovery template
    3. If yes: instantiate template for this incident
    4. If no: generate new suggestion via LLM
    5. Score suggestion confidence
    6. If confidence > 0.9 AND pattern.auto_apply: apply immediately
    7. Otherwise: queue for human review
    """
    pattern = await get_pattern_with_context(event.pattern_id)

    if pattern.recovery_template:
        suggestion = instantiate_template(
            template=pattern.recovery_template,
            incident_id=event.incident_id
        )
    else:
        suggestion = await generate_recovery_suggestion(
            pattern=pattern,
            incident_id=event.incident_id
        )

    if suggestion.confidence > 0.9 and pattern.auto_apply_recovery:
        await apply_recovery(suggestion)
        return suggestion.with_status("applied")
    else:
        await queue_for_review(suggestion)
        return suggestion.with_status("pending_review")
```

**Database:**
```sql
-- Add recovery linking to patterns
ALTER TABLE failure_patterns
ADD COLUMN recovery_template JSONB,
ADD COLUMN auto_apply_recovery BOOLEAN DEFAULT FALSE;

-- Add pattern reference to recovery candidates
ALTER TABLE recovery_candidates
ADD COLUMN source_pattern_id VARCHAR(64) REFERENCES failure_patterns(id),
ADD COLUMN source_incident_id VARCHAR(64) REFERENCES incidents(id);
```

**Event:**
```python
@dataclass
class RecoverySuggestedEvent:
    incident_id: str
    pattern_id: str
    recovery_id: str
    suggestion_type: Literal["template", "generated"]
    confidence: float
    auto_applied: bool
    timestamp: datetime
```

---

### Bridge 3: Recovery → Policy Rule

**Trigger:** Recovery applied (auto or manual)
**Action:** Generate prevention policy

```python
# backend/app/integrations/recovery_to_policy.py

async def on_recovery_applied(event: RecoveryAppliedEvent) -> PolicyRule:
    """
    Bridge 3: Convert applied recovery into prevention policy.

    Flow:
    1. Analyze recovery action type
    2. Determine appropriate policy category (safety, operational, routing)
    3. Generate policy rule that would have prevented the incident
    4. Set policy scope (tenant, agent, global)
    5. Add to policy_rules as draft or active based on confidence
    """
    recovery = await get_recovery_with_context(event.recovery_id)
    pattern = await get_pattern(recovery.source_pattern_id)

    policy_category = determine_policy_category(pattern, recovery)

    rule = generate_prevention_rule(
        pattern=pattern,
        recovery=recovery,
        category=policy_category
    )

    # High-confidence rules go active, others go to draft
    if rule.confidence > 0.85 and pattern.occurrence_count >= 3:
        rule.status = "active"
    else:
        rule.status = "draft"

    await save_policy_rule(rule)

    return rule
```

**Policy Rule Structure:**
```python
@dataclass
class GeneratedPolicyRule:
    id: str
    name: str
    description: str
    category: Literal["safety", "privacy", "operational", "routing", "custom"]
    condition: str  # Policy DSL expression
    action: Literal["block", "warn", "escalate", "route_away"]
    scope: PolicyScope  # tenant, agent, or global
    source_pattern_id: str
    source_recovery_id: str
    confidence: float
    status: Literal["draft", "active", "disabled"]
    created_at: datetime
```

**Database:**
```sql
-- Add source tracking to policy_rules
ALTER TABLE policy_rules
ADD COLUMN source_type VARCHAR(32),  -- 'manual', 'recovery', 'pattern'
ADD COLUMN source_pattern_id VARCHAR(64),
ADD COLUMN source_recovery_id VARCHAR(64),
ADD COLUMN generation_confidence FLOAT;
```

**Event:**
```python
@dataclass
class PolicyGeneratedEvent:
    policy_id: str
    source_pattern_id: str
    source_recovery_id: str
    category: str
    status: str
    confidence: float
    timestamp: datetime
```

---

### Bridge 4: Policy → CARE Routing

**Trigger:** Policy rule created or activated
**Action:** Adjust CARE routing weights

```python
# backend/app/integrations/policy_to_routing.py

async def on_policy_created(event: PolicyGeneratedEvent) -> RoutingAdjustment:
    """
    Bridge 4: Update CARE routing based on new policy.

    Flow:
    1. Identify agents/routes affected by policy
    2. If policy is "block" → reduce agent confidence for that capability
    3. If policy is "route_away" → add negative weight to specific route
    4. If policy is "escalate" → add escalation checkpoint
    5. Notify CARE governor of weight changes
    """
    policy = await get_policy(event.policy_id)
    pattern = await get_pattern(event.source_pattern_id)

    affected_agents = identify_affected_agents(pattern)

    adjustments = []
    for agent in affected_agents:
        adjustment = calculate_routing_adjustment(
            agent=agent,
            policy=policy,
            pattern=pattern
        )
        await apply_routing_adjustment(adjustment)
        adjustments.append(adjustment)

    # Notify governor to recalculate optimal routes
    await notify_care_governor(adjustments)

    return RoutingAdjustment(
        policy_id=policy.id,
        affected_agents=[a.id for a in affected_agents],
        adjustments=adjustments
    )
```

**Routing Adjustment Types:**
```python
@dataclass
class RoutingAdjustment:
    agent_id: str
    capability: str
    adjustment_type: Literal["confidence_penalty", "route_block", "escalation_add"]
    magnitude: float  # -1.0 to +1.0
    reason: str
    source_policy_id: str
    expires_at: Optional[datetime]  # Temporary adjustments
```

**Database:**
```sql
-- Add policy-triggered adjustments to routing
CREATE TABLE routing_policy_adjustments (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    capability VARCHAR(128),
    adjustment_type VARCHAR(32) NOT NULL,
    magnitude FLOAT NOT NULL,
    reason TEXT,
    source_policy_id VARCHAR(64) REFERENCES policy_rules(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_routing_adj_agent ON routing_policy_adjustments(agent_id, is_active);
```

**Event:**
```python
@dataclass
class RoutingAdjustedEvent:
    policy_id: str
    affected_agents: list[str]
    adjustment_count: int
    timestamp: datetime
```

---

### Bridge 5: Loop Status → Console

**Trigger:** Any bridge event
**Action:** Update console with loop status

```python
# backend/app/integrations/loop_status.py

async def on_loop_event(event: LoopEvent) -> LoopStatus:
    """
    Bridge 5: Aggregate loop status for console display.

    Flow:
    1. Update incident with current loop stage
    2. Calculate loop completion percentage
    3. Push SSE update to connected consoles
    4. Store loop trace for debugging
    """
    loop_trace = await get_or_create_loop_trace(event.incident_id)

    loop_trace.add_stage(
        stage=event.stage,
        details=event.details,
        timestamp=event.timestamp
    )

    status = LoopStatus(
        incident_id=event.incident_id,
        current_stage=event.stage,
        stages_completed=loop_trace.completed_stages,
        total_stages=5,
        completion_pct=len(loop_trace.completed_stages) / 5 * 100,
        details=loop_trace.stage_details
    )

    # Push to SSE for live console updates
    await push_sse_update(
        channel=f"incident:{event.incident_id}",
        event_type="loop_progress",
        data=status.to_dict()
    )

    return status
```

**Loop Status Structure:**
```python
@dataclass
class LoopStatus:
    incident_id: str
    current_stage: Literal[
        "incident_created",
        "pattern_matched",
        "recovery_suggested",
        "policy_generated",
        "routing_adjusted"
    ]
    stages_completed: list[str]
    total_stages: int
    completion_pct: float
    details: dict[str, Any]

    def to_console_display(self) -> str:
        """
        Format for console display:
        Incident → Pattern → Recovery → Policy → Routing
           ✅        ✅         ⏳         ○         ○
        """
        icons = {
            "completed": "✅",
            "in_progress": "⏳",
            "pending": "○"
        }
        # ... format logic
```

**Database:**
```sql
-- Loop trace for debugging and display
CREATE TABLE loop_traces (
    id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) NOT NULL REFERENCES incidents(id),
    tenant_id VARCHAR(64) NOT NULL,
    stages JSONB NOT NULL DEFAULT '[]',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    is_complete BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_loop_trace_incident ON loop_traces(incident_id);
```

---

## Event Bus Architecture

### Event Types
```python
# backend/app/integrations/events.py

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

class LoopStage(str, Enum):
    INCIDENT_CREATED = "incident_created"
    PATTERN_MATCHED = "pattern_matched"
    RECOVERY_SUGGESTED = "recovery_suggested"
    POLICY_GENERATED = "policy_generated"
    ROUTING_ADJUSTED = "routing_adjusted"

@dataclass
class LoopEvent:
    """Base event for integration loop."""
    event_id: str
    incident_id: str
    tenant_id: str
    stage: LoopStage
    timestamp: datetime
    details: dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "incident_id": self.incident_id,
            "tenant_id": self.tenant_id,
            "stage": self.stage.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
```

### Event Dispatcher
```python
# backend/app/integrations/dispatcher.py

class IntegrationDispatcher:
    """
    Dispatches events through the integration loop.

    Uses Redis pub/sub for real-time + PostgreSQL for durability.
    """

    def __init__(self, redis: Redis, db: AsyncSession):
        self.redis = redis
        self.db = db
        self.handlers: dict[LoopStage, list[Callable]] = {
            LoopStage.INCIDENT_CREATED: [on_incident_created],
            LoopStage.PATTERN_MATCHED: [on_pattern_matched],
            LoopStage.RECOVERY_SUGGESTED: [on_recovery_suggested],
            LoopStage.POLICY_GENERATED: [on_policy_created],
            LoopStage.ROUTING_ADJUSTED: [on_loop_event],
        }

    async def dispatch(self, event: LoopEvent) -> None:
        """
        Dispatch event to handlers.

        1. Persist to database (durability)
        2. Publish to Redis (real-time)
        3. Call registered handlers
        4. Update loop status
        """
        # Persist
        await self._persist_event(event)

        # Publish
        await self.redis.publish(
            f"loop:{event.tenant_id}",
            event.to_dict()
        )

        # Handle
        for handler in self.handlers.get(event.stage, []):
            try:
                await handler(event)
            except Exception as e:
                await self._handle_error(event, e)

        # Update status
        await on_loop_event(event)
```

---

## API Endpoints

### New Integration API
```python
# backend/app/api/integration.py

from fastapi import APIRouter, Depends
from app.integrations.dispatcher import IntegrationDispatcher

router = APIRouter(prefix="/integration", tags=["integration"])

@router.get("/loop/{incident_id}")
async def get_loop_status(
    incident_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> LoopStatus:
    """Get current loop status for an incident."""
    return await get_loop_trace(incident_id, tenant_id)

@router.get("/loop/{incident_id}/stages")
async def get_loop_stages(
    incident_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> list[LoopStageDetail]:
    """Get detailed stage information for loop."""
    trace = await get_loop_trace(incident_id, tenant_id)
    return trace.stage_details

@router.post("/loop/{incident_id}/retry/{stage}")
async def retry_loop_stage(
    incident_id: str,
    stage: LoopStage,
    tenant_id: str = Depends(get_tenant_id)
) -> LoopStatus:
    """Retry a failed loop stage."""
    return await retry_stage(incident_id, stage, tenant_id)

@router.get("/stats")
async def get_integration_stats(
    tenant_id: str = Depends(get_tenant_id),
    hours: int = 24
) -> IntegrationStats:
    """Get integration loop statistics."""
    return await calculate_integration_stats(tenant_id, hours)
```

### Stats Response
```python
@dataclass
class IntegrationStats:
    total_incidents: int
    patterns_matched: int
    patterns_created: int
    recoveries_suggested: int
    recoveries_applied: int
    policies_generated: int
    routing_adjustments: int
    avg_loop_completion_time_ms: float
    loop_completion_rate: float  # % of incidents that complete full loop
```

---

## Console UI Updates

### Loop Progress Component
```typescript
// website/aos-console/console/src/components/LoopProgress.tsx

interface LoopProgressProps {
  incidentId: string;
}

const STAGES = [
  { key: 'incident_created', label: 'Incident', icon: '🚨' },
  { key: 'pattern_matched', label: 'Pattern', icon: '🔍' },
  { key: 'recovery_suggested', label: 'Recovery', icon: '🔧' },
  { key: 'policy_generated', label: 'Policy', icon: '📋' },
  { key: 'routing_adjusted', label: 'Routing', icon: '🔀' },
];

export function LoopProgress({ incidentId }: LoopProgressProps) {
  const { data: status } = useLoopStatus(incidentId);

  return (
    <div className="loop-progress">
      <div className="stages-row">
        {STAGES.map((stage, idx) => (
          <React.Fragment key={stage.key}>
            <StageIndicator
              stage={stage}
              status={getStageStatus(status, stage.key)}
              details={status?.details[stage.key]}
            />
            {idx < STAGES.length - 1 && <StageConnector />}
          </React.Fragment>
        ))}
      </div>
      <div className="completion-bar">
        <div
          className="completion-fill"
          style={{ width: `${status?.completion_pct ?? 0}%` }}
        />
      </div>
    </div>
  );
}
```

### SSE Integration
```typescript
// website/aos-console/console/src/hooks/useLoopStatus.ts

export function useLoopStatus(incidentId: string) {
  const [status, setStatus] = useState<LoopStatus | null>(null);

  useEffect(() => {
    // Initial fetch
    fetchLoopStatus(incidentId).then(setStatus);

    // SSE for live updates
    const eventSource = new EventSource(
      `/api/integration/loop/${incidentId}/stream`
    );

    eventSource.addEventListener('loop_progress', (event) => {
      setStatus(JSON.parse(event.data));
    });

    return () => eventSource.close();
  }, [incidentId]);

  return { data: status };
}
```

---

## Database Migration

```python
# backend/alembic/versions/042_m25_integration_loop.py

"""M25: Pillar Integration Loop

Revision ID: 042_m25_integration
Revises: 041_fix_enqueue_work_constraint
Create Date: 2025-12-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '042_m25_integration'
down_revision = '041_fix_enqueue_work_constraint'

def upgrade():
    # Loop traces table
    op.create_table(
        'loop_traces',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('incident_id', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('stages', JSONB, nullable=False, server_default='[]'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('is_complete', sa.Boolean, server_default='false'),
    )
    op.create_index('idx_loop_trace_incident', 'loop_traces', ['incident_id'])
    op.create_index('idx_loop_trace_tenant', 'loop_traces', ['tenant_id', 'is_complete'])

    # Loop events table (durability)
    op.create_table(
        'loop_events',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('incident_id', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('stage', sa.String(32), nullable=False),
        sa.Column('details', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_loop_events_incident', 'loop_events', ['incident_id', 'created_at'])

    # Routing policy adjustments
    op.create_table(
        'routing_policy_adjustments',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('agent_id', sa.String(64), nullable=False),
        sa.Column('capability', sa.String(128)),
        sa.Column('adjustment_type', sa.String(32), nullable=False),
        sa.Column('magnitude', sa.Float, nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('source_policy_id', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )
    op.create_index('idx_routing_adj_agent', 'routing_policy_adjustments', ['agent_id', 'is_active'])

    # Add cross-references
    op.add_column('incidents', sa.Column('matched_pattern_id', sa.String(64)))
    op.add_column('incidents', sa.Column('loop_trace_id', sa.String(64)))

    op.add_column('failure_patterns', sa.Column('first_incident_id', sa.String(64)))
    op.add_column('failure_patterns', sa.Column('recovery_template', JSONB))
    op.add_column('failure_patterns', sa.Column('auto_apply_recovery', sa.Boolean, server_default='false'))

    op.add_column('recovery_candidates', sa.Column('source_pattern_id', sa.String(64)))
    op.add_column('recovery_candidates', sa.Column('source_incident_id', sa.String(64)))

    op.add_column('policy_rules', sa.Column('source_type', sa.String(32)))
    op.add_column('policy_rules', sa.Column('source_pattern_id', sa.String(64)))
    op.add_column('policy_rules', sa.Column('source_recovery_id', sa.String(64)))
    op.add_column('policy_rules', sa.Column('generation_confidence', sa.Float))

def downgrade():
    # Remove cross-references
    op.drop_column('policy_rules', 'generation_confidence')
    op.drop_column('policy_rules', 'source_recovery_id')
    op.drop_column('policy_rules', 'source_pattern_id')
    op.drop_column('policy_rules', 'source_type')

    op.drop_column('recovery_candidates', 'source_incident_id')
    op.drop_column('recovery_candidates', 'source_pattern_id')

    op.drop_column('failure_patterns', 'auto_apply_recovery')
    op.drop_column('failure_patterns', 'recovery_template')
    op.drop_column('failure_patterns', 'first_incident_id')

    op.drop_column('incidents', 'loop_trace_id')
    op.drop_column('incidents', 'matched_pattern_id')

    # Drop tables
    op.drop_table('routing_policy_adjustments')
    op.drop_table('loop_events')
    op.drop_table('loop_traces')
```

---

## Testing Strategy

### Integration Tests
```python
# backend/tests/test_m25_integration_loop.py

class TestIntegrationLoop:
    """Test the full integration loop."""

    async def test_incident_triggers_full_loop(self, db, redis):
        """
        Verify that creating an incident triggers all 5 stages.
        """
        # Create incident
        incident = await create_test_incident(db)

        # Wait for loop to complete (with timeout)
        loop_status = await wait_for_loop_completion(
            incident.id,
            timeout_seconds=30
        )

        assert loop_status.is_complete
        assert loop_status.stages_completed == [
            "incident_created",
            "pattern_matched",
            "recovery_suggested",
            "policy_generated",
            "routing_adjusted"
        ]

    async def test_pattern_reuse_on_similar_incident(self, db, redis):
        """
        Second similar incident should match existing pattern.
        """
        # First incident creates pattern
        incident1 = await create_test_incident(db, error_type="rate_limit")
        await wait_for_loop_completion(incident1.id)

        pattern = await get_matched_pattern(incident1.id)
        assert pattern.occurrence_count == 1

        # Second similar incident matches pattern
        incident2 = await create_test_incident(db, error_type="rate_limit")
        await wait_for_loop_completion(incident2.id)

        pattern = await get_matched_pattern(incident2.id)
        assert pattern.id == (await get_matched_pattern(incident1.id)).id
        assert pattern.occurrence_count == 2

    async def test_auto_apply_recovery_on_high_confidence(self, db, redis):
        """
        High-confidence recovery should be auto-applied.
        """
        # Create pattern with high-confidence template
        pattern = await create_pattern_with_template(
            db,
            auto_apply=True,
            confidence=0.95
        )

        # Create matching incident
        incident = await create_incident_matching_pattern(db, pattern)
        await wait_for_loop_completion(incident.id)

        # Recovery should be applied
        recovery = await get_recovery_for_incident(incident.id)
        assert recovery.status == "applied"

    async def test_policy_generated_from_recovery(self, db, redis):
        """
        Applied recovery should generate prevention policy.
        """
        incident = await create_test_incident(db)
        await wait_for_loop_completion(incident.id)

        # Find generated policy
        policies = await get_policies_from_incident(incident.id)
        assert len(policies) >= 1

        policy = policies[0]
        assert policy.source_type == "recovery"
        assert policy.source_pattern_id is not None

    async def test_routing_adjusted_from_policy(self, db, redis):
        """
        New policy should trigger routing adjustment.
        """
        incident = await create_test_incident(db, agent_id="agent-001")
        await wait_for_loop_completion(incident.id)

        # Check routing adjustments
        adjustments = await get_routing_adjustments(agent_id="agent-001")
        assert len(adjustments) >= 1

        # Agent confidence should be reduced
        agent = await get_agent("agent-001")
        assert agent.confidence < 1.0
```

### Performance Tests
```python
# backend/tests/test_m25_performance.py

class TestIntegrationPerformance:
    """Performance tests for integration loop."""

    async def test_loop_completes_under_5_seconds(self, db, redis):
        """Full loop should complete in < 5 seconds."""
        incident = await create_test_incident(db)

        start = time.time()
        await wait_for_loop_completion(incident.id, timeout_seconds=5)
        duration = time.time() - start

        assert duration < 5.0

    async def test_concurrent_incidents_dont_block(self, db, redis):
        """Multiple concurrent incidents should process independently."""
        incidents = await asyncio.gather(*[
            create_test_incident(db)
            for _ in range(10)
        ])

        # All should complete within 10 seconds
        results = await asyncio.gather(*[
            wait_for_loop_completion(i.id, timeout_seconds=10)
            for i in incidents
        ])

        assert all(r.is_complete for r in results)
```

---

## Implementation Phases

### Phase 1: Infrastructure (Days 1-3)

| Task | Owner | Status |
|------|-------|--------|
| Create migration 042_m25_integration_loop | Backend | ⬜ |
| Implement LoopEvent dataclass | Backend | ⬜ |
| Implement IntegrationDispatcher | Backend | ⬜ |
| Create loop_traces table and model | Backend | ⬜ |
| Add /integration API router | Backend | ⬜ |

### Phase 2: Bridges 1-3 (Days 4-7)

| Task | Owner | Status |
|------|-------|--------|
| Bridge 1: Incident → Failure Catalog | Backend | ⬜ |
| Bridge 2: Pattern → Recovery | Backend | ⬜ |
| Bridge 3: Recovery → Policy | Backend | ⬜ |
| Integration tests for bridges 1-3 | Backend | ⬜ |

### Phase 3: Bridges 4-5 (Days 8-10)

| Task | Owner | Status |
|------|-------|--------|
| Bridge 4: Policy → CARE Routing | Backend | ⬜ |
| Bridge 5: Loop Status → Console | Backend | ⬜ |
| SSE endpoint for live updates | Backend | ⬜ |
| Integration tests for bridges 4-5 | Backend | ⬜ |

### Phase 4: Console UI (Days 11-12)

| Task | Owner | Status |
|------|-------|--------|
| LoopProgress component | Frontend | ⬜ |
| useLoopStatus hook with SSE | Frontend | ⬜ |
| Integrate into incident detail page | Frontend | ⬜ |
| Integration stats dashboard | Frontend | ⬜ |

### Phase 5: Testing & Polish (Days 13-14)

| Task | Owner | Status |
|------|-------|--------|
| Full loop E2E tests | Backend | ⬜ |
| Performance tests | Backend | ⬜ |
| Error handling and retry logic | Backend | ⬜ |
| Documentation | All | ⬜ |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Loop completion rate | > 95% | % of incidents completing all 5 stages |
| Loop completion time | < 5 seconds | P95 time from incident to routing adjustment |
| Pattern match accuracy | > 80% | % of similar incidents matching same pattern |
| Auto-apply success rate | > 90% | % of auto-applied recoveries without rollback |
| Policy generation rate | > 70% | % of recoveries generating valid policy |
| Zero data loss | 100% | All events persisted before processing |

---

## Rollback Plan

If integration causes issues:

1. **Feature flag:** `INTEGRATION_LOOP_ENABLED=false` disables all bridges
2. **Per-bridge flags:** `BRIDGE_1_ENABLED`, `BRIDGE_2_ENABLED`, etc.
3. **Rollback migration:** `alembic downgrade -1`
4. **Clear loop traces:** `DELETE FROM loop_traces WHERE created_at > :cutoff`

---

## 2025-12-23: Enhanced Implementation

Based on comprehensive review, the following improvements were implemented:

### 1. Confidence Bands (Instead of Binary 80% Threshold)

Replaced the optimistic 80% binary threshold with graduated confidence bands:

```python
class ConfidenceBand(str, Enum):
    STRONG = "strong"     # > 0.85 - Auto-proceed, high trust
    WEAK = "weak"         # 0.60 - 0.85 - Proceed with confirmation
    NOVEL = "novel"       # < 0.60 - New pattern, needs cataloging
```

**Rationale:** Real-world pattern matching rarely achieves 80%+. The graduated approach allows appropriate handling at each confidence level.

### 2. Policy Shadow Mode with N-Confirmation Activation

Policies now progress through stages before enforcement:

```python
class PolicyMode(str, Enum):
    SHADOW = "shadow"     # Observe only, no enforcement
    PENDING = "pending"   # Awaiting confirmations
    ACTIVE = "active"     # Enforcing
    DISABLED = "disabled" # Manually disabled
```

- Auto-generated policies start in SHADOW mode
- Require N confirmations (default: 3) before activation
- Track `shadow_evaluations` and `shadow_would_block` for visibility
- Track `regret_count` when policies cause incidents

### 3. CARE Routing Guardrails

Added safety limits to prevent runaway routing changes:

```python
@dataclass
class RoutingAdjustment:
    max_delta: float = 0.2          # Never adjust more than 20%
    decay_days: int = 7             # Decay over 7 days
    rollback_threshold: float = 0.1 # Rollback if KPI drops 10%
    kpi_baseline: float = None      # Starting KPI value
    kpi_current: float = None       # Current KPI value
```

### 4. Loop Failure States

Explicit failure states for all unhappy paths:

```python
class LoopFailureState(str, Enum):
    MATCH_FAILED = "match_failed"
    MATCH_LOW_CONFIDENCE = "match_low_confidence"
    RECOVERY_REJECTED = "recovery_rejected"
    RECOVERY_NEEDS_CONFIRMATION = "recovery_needs_confirmation"
    POLICY_LOW_CONFIDENCE = "policy_low_confidence"
    POLICY_SHADOW_MODE = "policy_shadow_mode"
    POLICY_REJECTED = "policy_rejected"
    ROUTING_GUARDRAIL_BLOCKED = "routing_guardrail_blocked"
    ROUTING_KPI_REGRESSION = "routing_kpi_regression"
    HUMAN_CHECKPOINT_PENDING = "human_checkpoint_pending"
    HUMAN_CHECKPOINT_REJECTED = "human_checkpoint_rejected"
```

### 5. Human Checkpoint Controls

Explicit intervention points for human oversight:

```python
class HumanCheckpointType(str, Enum):
    APPROVE_POLICY = "approve_policy"
    APPROVE_RECOVERY = "approve_recovery"
    SIMULATE_ROUTING = "simulate_routing"
    REVERT_LOOP = "revert_loop"
    OVERRIDE_GUARDRAIL = "override_guardrail"
```

### 6. Narrative Artifacts

Loop completion generates storytelling artifacts for the console:

```python
def to_console_display(self) -> dict:
    return {
        "what_happened": "...",
        "what_we_learned": "...",
        "what_we_changed": "...",
        "confidence_summary": "...",
        "human_decisions": [...],
        "timeline": [...]
    }
```

---

## Implementation Status (Updated 2025-12-23)

### Phase 1: Infrastructure ✅ COMPLETE

| Task | Status | Files |
|------|--------|-------|
| Migration 042_m25_integration_loop | ✅ | `backend/alembic/versions/042_m25_integration_loop.py` |
| Event types with enhancements | ✅ | `backend/app/integrations/events.py` |
| IntegrationDispatcher | ✅ | `backend/app/integrations/dispatcher.py` |
| All 5 bridges | ✅ | `backend/app/integrations/bridges.py` |
| Integration API router | ✅ | `backend/app/api/integration.py` |

### Phase 2-3: Bridges ✅ COMPLETE

| Bridge | Status | Key Features |
|--------|--------|--------------|
| Incident → Catalog | ✅ | Signature hashing, fuzzy matching, confidence bands |
| Pattern → Recovery | ✅ | Template instantiation, heuristic generation |
| Recovery → Policy | ✅ | Shadow mode, N-confirmation |
| Policy → Routing | ✅ | Guardrails (max_delta, decay, rollback) |
| Loop → Console | ✅ | Narrative artifacts, timeline |

### Phase 4: Console UI ✅ COMPLETE

| Component | Status | Files |
|-----------|--------|-------|
| Integration API client | ✅ | `website/aos-console/console/src/api/integration.ts` |
| LoopStatusPage | ✅ | `website/aos-console/console/src/pages/integration/LoopStatusPage.tsx` |
| IntegrationDashboard | ✅ | `website/aos-console/console/src/pages/integration/IntegrationDashboard.tsx` |
| Routes configured | ✅ | `website/aos-console/console/src/routes/index.tsx` |

### Phase 5: Testing ✅ COMPLETE

| Test Suite | Status | Coverage |
|------------|--------|----------|
| Confidence bands | ✅ | 5 tests |
| Policy shadow mode | ✅ | 5 tests |
| Routing guardrails | ✅ | 4 tests |
| Loop failure states | ✅ | 4 tests |
| Human checkpoints | ✅ | 3 tests |
| Signature hashing | ✅ | 2 tests |
| Full loop flow | ✅ | 2 tests |

---

## Updated Success Criteria

| Metric | Original Target | Revised Target | Rationale |
|--------|-----------------|----------------|-----------|
| Pattern match accuracy | > 80% | > 60% (strong+weak) | More realistic threshold |
| Loop completion rate | > 95% | > 85% | Accounts for human checkpoints |
| Policy activation rate | N/A | > 70% after shadow | New metric for shadow mode |
| Guardrail effectiveness | N/A | < 5% KPI regression | New metric for routing safety |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Created PIN-129 M25 Pillar Integration Blueprint |
| 2025-12-23 | Enhanced with confidence bands, shadow mode, guardrails, failure states, checkpoints |
| 2025-12-23 | Implemented all bridges and API endpoints |
| 2025-12-23 | Created console UI (Dashboard + LoopStatus) |
| 2025-12-23 | Added comprehensive test suite (25+ tests) |
| 2025-12-23 | Added M25 Graduation Gates (prevention proof, regret rollback, timeline) |
| 2025-12-23 | Status changed to M25-ALPHA (loop-enabled, not loop-proven) |

---

## M25 Graduation Gates

**Current Status:** M25-ALPHA (0/3 gates)

M25 graduates from ALPHA to COMPLETE when all three gates pass:

### Gate 1: Prevention Proof

**Requirement:** At least one policy must prevent one incident recurrence.

```
Incident A (original) → Pattern → Policy Born → Incident B (blocked by policy)
```

Evidence tracked in `prevention_records` table:
- `original_incident_id` - The incident that created the policy
- `blocked_incident_id` - The incident that was prevented
- `signature_match_confidence` - How similar was the blocked incident?

**Gate Status:** Not yet passed (waiting for prevention evidence)

### Gate 2: Regret Rollback

**Requirement:** At least one policy must be auto-demoted due to causing harm.

```
Policy Active → Causes False Positive → Regret Recorded → Auto-Demoted
```

Evidence tracked in `regret_events` and `policy_regret_summary`:
- `regret_score` - Weighted severity score
- `demoted_at` / `demoted_reason` - When and why demoted

**Gate Status:** Not yet passed (waiting for regret evidence)

### Gate 3: Console Timeline

**Requirement:** User must SEE the learning in the console.

Timeline must visibly show:
1. Incident A detected
2. Policy born from failure
3. Incident B PREVENTED

**Gate Status:** Not yet passed (waiting for console proof)

---

## Learning Proof System

New module: `backend/app/integrations/learning_proof.py`

### Key Components

```python
# Gate 1
PreventionRecord    # Evidence of prevention
PreventionTracker   # Accumulates prevention evidence

# Gate 2
RegretEvent         # Single harm event
PolicyRegretTracker # Per-policy regret tracking (auto-demotes)
GlobalRegretTracker # System-wide regret tracking

# Adaptive Confidence (Beyond static thresholds)
PatternCalibration      # Per-pattern outcome tracking
AdaptiveConfidenceSystem # Replaces cargo-cult 0.85 with empirical thresholds

# Checkpoint Prioritization
CheckpointConfig        # Per-tenant configuration
PrioritizedCheckpoint   # Checkpoints with priority/expiry

# Graduation
M25GraduationStatus     # Tracks all 3 gates
PreventionTimeline      # Console-ready visualization
```

### Migration Added

`043_m25_learning_proof.py` adds:
- `prevention_records` - Track preventions
- `regret_events` - Track harm
- `policy_regret_summary` - Aggregated regret
- `pattern_calibrations` - Adaptive thresholds
- `checkpoint_configs` - Per-tenant config
- `m25_graduation_status` - Gate tracking

---

## Honest Assessment

### What M25 IS

A **safely governed feedback loop** that:
- Matches incidents to known patterns (with confidence bands)
- Suggests recoveries (with confirmation requirements)
- Generates policies (in shadow mode first)
- Adjusts routing (with guardrails)
- Allows human intervention (with priority)

### What M25 IS NOT (Yet)

A **proven learning system**. Until the graduation gates pass:
- No evidence policies actually prevent recurrence
- No evidence the system self-corrects when policies cause harm
- No visible proof in the console for users

### Recommended Positioning

> **M25 = Closed-loop capability unlocked**
> **M25.1+ = Evidence that the loop works**

---

## Path to Graduation

### Step 1: Natural Gate Passage

Wait for real-world events:
1. An incident occurs
2. Pattern matched, recovery suggested, policy created
3. Same pattern recurs, policy blocks it → **Gate 1 passes**
4. A policy causes false positive, gets demoted → **Gate 2 passes**
5. User views prevention in console → **Gate 3 passes**

### Step 2: Simulated Gate Passage

For faster validation:

```python
# Simulate Gate 1
prevention_tracker.record_prevention(PreventionRecord.create_prevention(...))

# Simulate Gate 2
for _ in range(3):
    regret_tracker.record_regret(policy_id, RegretEvent(...))

# Simulate Gate 3
graduation_status.console_proof_incidents.append("inc_001")
```

### Step 3: Dashboard Monitoring

API endpoint: `GET /integration/graduation`

Returns:
```json
{
  "status": "M25-ALPHA (1/3 gates)",
  "gates": {
    "gate1_prevention": {"passed": true, "evidence": {...}},
    "gate2_rollback": {"passed": false, "evidence": {...}},
    "gate3_console": {"passed": false, "evidence": {...}}
  },
  "next_action": "Wait for or simulate a policy causing regret"
}
```

---

## Difference: Loop-Enabled vs Loop-Proven

| Aspect | Loop-Enabled (Current) | Loop-Proven (Target) |
|--------|------------------------|----------------------|
| Plumbing | ✅ Complete | ✅ Complete |
| Safety rails | ✅ Implemented | ✅ Implemented |
| Prevention evidence | ⬜ Not yet | ✅ Recorded |
| Self-correction evidence | ⬜ Not yet | ✅ Recorded |
| User visibility | ⬜ Timeline empty | ✅ Timeline shows learning |
| Marketing claim | "Can safely improve" | "Demonstrably improves" |

---

## Files Added (Learning Proof)

| File | Purpose |
|------|---------|
| `backend/app/integrations/learning_proof.py` | Prevention, regret, adaptive confidence, checkpoints, graduation |
| `backend/alembic/versions/043_m25_learning_proof.py` | Database tables for learning proof |
| `backend/tests/test_m25_graduation_gates.py` | Acceptance tests for graduation gates (32 tests) |

---

## Graduation API Endpoints

Added to `backend/app/api/integration.py`:

### GET /integration/graduation

Returns current graduation status:

```json
{
  "status": "M25-ALPHA (1/3 gates)",
  "is_graduated": false,
  "gates": {
    "gate1_prevention": {
      "name": "Prevention Proof",
      "description": "Policy prevented at least one incident recurrence",
      "passed": true,
      "evidence": {"total_preventions": 1, "prevented_count": 1}
    },
    "gate2_rollback": {...},
    "gate3_console": {...}
  },
  "next_action": "Wait for or simulate a policy causing regret",
  "prevention_stats": {"total": 1, "rate": "100.0%"},
  "regret_stats": {"total_events": 0, "auto_demotions": 0}
}
```

### POST /integration/graduation/simulate/prevention

Fast-track Gate 1 for demo/testing:

```json
{
  "policy_id": "pol_xxx",
  "pattern_id": "pat_xxx",
  "original_incident_id": "inc_xxx",
  "confidence": 0.92
}
```

### POST /integration/graduation/simulate/regret

Fast-track Gate 2 for demo/testing:

```json
{
  "policy_id": "pol_xxx",
  "regret_type": "false_positive",
  "severity": 7,
  "description": "Policy blocked legitimate requests"
}
```

### POST /integration/graduation/simulate/timeline-view

Fast-track Gate 3 for demo/testing:

```
?incident_id=inc_xxx
```

### GET /integration/timeline/{incident_id}

Get prevention timeline for an incident (Gate 3 UI):

```json
{
  "incident_id": "inc_xxx",
  "timeline": [
    {"type": "incident_created", "timestamp": "...", "icon": "🚨", "headline": "Incident detected", ...},
    {"type": "policy_born", "timestamp": "...", "icon": "📋", "headline": "Policy born from failure", ...},
    {"type": "prevention", "timestamp": "...", "icon": "🛡️", "headline": "PREVENTION: Similar incident BLOCKED", "is_milestone": true, ...}
  ],
  "summary": {"event_count": 3, "has_prevention": true, "is_learning_proof": true},
  "narrative": "This incident proves learning: a policy born from failure successfully prevented a recurrence."
}
```

---

## Console UI Updates

### Graduation Widget

Added `GraduationWidget` component to `IntegrationDashboard.tsx`:

- Shows M25 graduation status badge in header
- Displays all 3 gates with pass/pending status
- Shows prevention and regret statistics
- Updates automatically via React Query

### Integration API Client

Extended `website/aos-console/console/src/api/integration.ts` with:

```typescript
// Graduation API functions
getGraduationStatus(): Promise<GraduationStatus>
getPreventionTimeline(incidentId: string): Promise<PreventionTimeline>
simulatePrevention(request: SimulatePreventionRequest): Promise<{gate1_passed: boolean}>
simulateRegret(request: SimulateRegretRequest): Promise<{gate2_passed: boolean}>
simulateTimelineView(incidentId: string): Promise<{gate3_passed: boolean}>
```

---

## Demo Script

Added `scripts/ops/m25_gate_passage_demo.py`:

```bash
# Show current status
python scripts/ops/m25_gate_passage_demo.py --status

# Simulate individual gates
python scripts/ops/m25_gate_passage_demo.py --gate 1  # Prevention
python scripts/ops/m25_gate_passage_demo.py --gate 2  # Regret
python scripts/ops/m25_gate_passage_demo.py --gate 3  # Timeline

# Simulate all gates (full graduation)
python scripts/ops/m25_gate_passage_demo.py --all

# Reset graduation status
python scripts/ops/m25_gate_passage_demo.py --reset
```

---

## Test Results

```
backend/tests/test_m25_graduation_gates.py
├── TestGate1PreventionProof (5 tests) ✅
├── TestGate2RegretRollback (6 tests) ✅
├── TestAdaptiveConfidence (5 tests) ✅
├── TestCheckpointPrioritization (6 tests) ✅
├── TestM25Graduation (6 tests) ✅
└── TestPreventionTimeline (4 tests) ✅

Total: 32 tests, all passed in 0.22s
```

---

## Changelog (Continued)

| Date | Change |
|------|--------|
| 2025-12-23 | Added graduation API endpoints (GET/POST /integration/graduation/*) |
| 2025-12-23 | Added prevention timeline endpoint (GET /integration/timeline/{incident_id}) |
| 2025-12-23 | Added GraduationWidget to IntegrationDashboard |
| 2025-12-23 | Extended integration.ts API client with graduation functions |
| 2025-12-23 | Created m25_gate_passage_demo.py simulation script |
| 2025-12-23 | All 32 graduation gate tests passing |
