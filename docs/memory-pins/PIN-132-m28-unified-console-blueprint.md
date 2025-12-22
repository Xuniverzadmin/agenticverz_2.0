# PIN-132: M28 Unified Console Blueprint

**Status:** SPECIFICATION
**Category:** Milestone / Console / UI Architecture
**Created:** 2025-12-22
**Related PINs:** PIN-128 (Master Plan), PIN-129 (M25), PIN-130 (M26), PIN-131 (M27)
**Milestone:** M28 Phase-4

---

## Executive Summary

M28 consolidates three separate consoles (Guard, Ops, Main) into one unified "Control Center" with four primary views (Cost, Incident, Self-Heal, Governance). Every event gets an `actor_id` (human/agent/system), enabling cross-view correlation and unified search.

**Duration:** 1.5 weeks (10 days)
**Risk:** Low (UI consolidation, not new backend)

---

## Current State Analysis

### Existing Consoles

| Console | Path | Purpose | Pages |
|---------|------|---------|-------|
| Guard Console | `/guard/*` | Incident investigation, KillSwitch | 12 pages |
| Ops Console | `/ops/*` | Founder intelligence, at-risk customers | 2 pages |
| Main Console | `/*` | Skills, Workers, Dashboard, SBA | 15+ pages |

### Current Navigation Structure

```
Guard Console (/guard):
├── Overview (GuardDashboard)
├── Live Activity
├── Incidents
├── Kill Switch
├── Logs
├── Settings
└── Account

Ops Console (/ops):
├── Founder Intelligence Dashboard
└── At-Risk Customers

Main Console (/):
├── Dashboard
├── Skills
├── Workers
│   ├── Studio
│   └── Execution
├── Simulation
├── Traces
├── Failures
├── Recovery
├── SBA Inspector
├── Memory Pins
├── Credits
└── Metrics
```

### Problems with Current Structure

1. **Fragmented UX** - Users must navigate between 3 different consoles
2. **No Cross-View Context** - Can't see incident impact on cost in same view
3. **No Actor Attribution** - Events lack human/agent/system attribution
4. **Duplicate Navigation** - Each console has its own layout/sidebar
5. **No Unified Search** - Must search each console separately

---

## M28 Design: Unified Control Center

### Core Concept

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AGENTICVERZ CONTROL CENTER                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │   COST   │ │ INCIDENT │ │SELF-HEAL │ │GOVERNANCE│      🔍 Unified Search │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │                        CURRENTLY SELECTED VIEW                      │    │
│  │                                                                     │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CROSS-CUTTING METRICS STRIP                                        │    │
│  │  💰 $4,847/$5,000  │  🚨 3 Incidents  │  🔧 12 Recoveries  │  📋 47 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Four Primary Views

| View | Icon | Color | Primary Focus | Secondary Focus |
|------|------|-------|---------------|-----------------|
| **COST** | 💰 | Green | Cost Dashboard (M26) | Budget alerts, projections |
| **INCIDENT** | 🚨 | Red | Guard Console (M22-23) | KillSwitch, live activity |
| **SELF-HEAL** | 🔧 | Blue | Recovery (M9-10) | Failure patterns, suggestions |
| **GOVERNANCE** | 📋 | Purple | SBA/Policy (M15-19) | CARE routing, rules |

---

## Architecture

### Component Hierarchy

```
ControlCenter (new)
├── ControlCenterLayout.tsx
│   ├── TopNavBar.tsx (4 view tabs + unified search)
│   ├── MetricsStrip.tsx (cross-cutting metrics)
│   └── ViewContainer.tsx
│
├── Views/
│   ├── CostView/ (M26 integration)
│   │   ├── CostDashboardPage.tsx
│   │   ├── FeatureTagsPage.tsx
│   │   ├── AnomaliesPage.tsx
│   │   ├── ProjectionsPage.tsx
│   │   └── BudgetAlertsPage.tsx
│   │
│   ├── IncidentView/ (Guard Console migration)
│   │   ├── IncidentOverview.tsx
│   │   ├── LiveActivity.tsx
│   │   ├── IncidentDetails.tsx
│   │   ├── KillSwitch.tsx
│   │   ├── Logs.tsx
│   │   └── Settings.tsx
│   │
│   ├── SelfHealView/ (Recovery migration)
│   │   ├── FailureCatalog.tsx
│   │   ├── RecoverySuggestions.tsx
│   │   ├── PatternViewer.tsx
│   │   └── AutoRecoveryConfig.tsx
│   │
│   └── GovernanceView/ (SBA/Policy migration)
│       ├── SBAInspector.tsx
│       ├── PolicyEditor.tsx
│       ├── CARERouting.tsx
│       └── AuditLog.tsx
│
├── Shared/
│   ├── UnifiedSearch.tsx
│   ├── ActorBadge.tsx
│   ├── CrossViewLink.tsx
│   └── ViewToViewDeepLink.tsx
│
└── stores/
    ├── controlCenterStore.ts (view state)
    └── actorStore.ts (actor context)
```

### Actor Attribution Model

Every event in the system gets an `actor_id` with type classification:

```typescript
// backend/app/models/actor.py

from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ActorType(str, Enum):
    HUMAN = "human"           # Real user action
    AGENT = "agent"           # AI agent action
    SYSTEM = "system"         # Automated/scheduled
    POLICY = "policy"         # Policy-triggered
    RECOVERY = "recovery"     # Self-healing action

class Actor(BaseModel):
    """Universal actor attribution for all events."""
    id: str                   # actor_human_xyz, actor_agent_abc, actor_system_001
    type: ActorType
    display_name: str         # "John Doe", "Content Generator Agent", "Daily Cleanup"
    tenant_id: str
    created_at: datetime

    # For human actors
    email: Optional[str] = None

    # For agent actors
    agent_id: Optional[str] = None
    strategy_id: Optional[str] = None

    # For system actors
    job_type: Optional[str] = None
    trigger: Optional[str] = None  # "cron", "webhook", "manual"

class ActorContext(BaseModel):
    """Context for actor attribution in events."""
    actor_id: str
    actor_type: ActorType
    action: str               # "created_incident", "blocked_request", "applied_recovery"
    target_type: str          # "incident", "policy", "agent"
    target_id: str
    metadata: dict = {}
```

### Database Migration (045)

```python
# backend/alembic/versions/045_m28_actor_attribution.py

"""M28: Actor attribution for unified console."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '045_m28_actor_attribution'
down_revision = '044_m27_cost_loop'
branch_labels = None
depends_on = None

def upgrade():
    # Actor registry table
    op.create_table(
        'actors',
        sa.Column('id', sa.String(64), primary_key=True),  # actor_human_xyz
        sa.Column('type', sa.String(20), nullable=False),  # human, agent, system, policy, recovery
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('agent_id', sa.String(64), nullable=True),
        sa.Column('strategy_id', sa.String(64), nullable=True),
        sa.Column('job_type', sa.String(64), nullable=True),
        sa.Column('trigger', sa.String(20), nullable=True),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Actor events table (unified event log)
    op.create_table(
        'actor_events',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('actor_id', sa.String(64), sa.ForeignKey('actors.id'), nullable=False, index=True),
        sa.Column('actor_type', sa.String(20), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('target_type', sa.String(64), nullable=False),
        sa.Column('target_id', sa.String(64), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    # Add actor_id to existing tables
    op.add_column('incidents', sa.Column('actor_id', sa.String(64), nullable=True))
    op.add_column('failure_patterns', sa.Column('actor_id', sa.String(64), nullable=True))
    op.add_column('recovery_candidates', sa.Column('actor_id', sa.String(64), nullable=True))
    op.add_column('policy_rules', sa.Column('actor_id', sa.String(64), nullable=True))
    op.add_column('integration_events', sa.Column('actor_id', sa.String(64), nullable=True))
    op.add_column('cost_records', sa.Column('actor_id', sa.String(64), nullable=True))
    op.add_column('cost_anomalies', sa.Column('actor_id', sa.String(64), nullable=True))

    # Cross-view search materialized view
    op.execute("""
        CREATE MATERIALIZED VIEW unified_search_index AS
        SELECT
            'incident' as entity_type,
            id as entity_id,
            tenant_id,
            actor_id,
            created_at,
            coalesce(call_id, '') || ' ' || coalesce(description, '') as search_text
        FROM incidents
        UNION ALL
        SELECT
            'failure_pattern' as entity_type,
            id as entity_id,
            tenant_id,
            actor_id,
            created_at,
            coalesce(pattern_type, '') || ' ' || coalesce(description, '') as search_text
        FROM failure_patterns
        UNION ALL
        SELECT
            'recovery' as entity_type,
            id as entity_id,
            tenant_id,
            actor_id,
            created_at,
            coalesce(suggestion, '') || ' ' || coalesce(status, '') as search_text
        FROM recovery_candidates
        UNION ALL
        SELECT
            'policy' as entity_type,
            id as entity_id,
            tenant_id,
            actor_id,
            created_at,
            coalesce(name, '') || ' ' || coalesce(rule_text, '') as search_text
        FROM policy_rules
        UNION ALL
        SELECT
            'cost_anomaly' as entity_type,
            id as entity_id,
            tenant_id,
            actor_id,
            created_at,
            coalesce(anomaly_type, '') || ' ' || coalesce(description, '') as search_text
        FROM cost_anomalies;

        CREATE INDEX idx_unified_search_tenant ON unified_search_index(tenant_id);
        CREATE INDEX idx_unified_search_actor ON unified_search_index(actor_id);
        CREATE INDEX idx_unified_search_text ON unified_search_index USING gin(to_tsvector('english', search_text));
    """)

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS unified_search_index")
    op.drop_column('cost_anomalies', 'actor_id')
    op.drop_column('cost_records', 'actor_id')
    op.drop_column('integration_events', 'actor_id')
    op.drop_column('policy_rules', 'actor_id')
    op.drop_column('recovery_candidates', 'actor_id')
    op.drop_column('failure_patterns', 'actor_id')
    op.drop_column('incidents', 'actor_id')
    op.drop_table('actor_events')
    op.drop_table('actors')
```

---

## API Endpoints

### New Control Center APIs

```python
# backend/app/api/control_center.py

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/control-center", tags=["control-center"])

# ==================== Unified Search ====================

@router.get("/search")
async def unified_search(
    q: str = Query(..., min_length=2),
    entity_types: Optional[List[str]] = Query(None),  # incident, recovery, policy, cost_anomaly
    actor_types: Optional[List[str]] = Query(None),   # human, agent, system
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(50, le=200),
    tenant_id: str = Depends(get_tenant_id),
) -> SearchResults:
    """
    Unified search across all views.

    Returns results from incidents, recovery suggestions, policies,
    and cost anomalies with relevance scoring.
    """
    pass

# ==================== Cross-Cutting Metrics ====================

@router.get("/metrics/strip")
async def get_metrics_strip(
    tenant_id: str = Depends(get_tenant_id),
) -> MetricsStrip:
    """
    Cross-cutting metrics for top strip.

    Returns:
    - cost_current: Current month spend
    - cost_budget: Monthly budget
    - incidents_active: Open incidents count
    - recoveries_pending: Pending recovery suggestions
    - policies_active: Active policy rules count
    - health_score: Overall system health (0-100)
    """
    pass

# ==================== View State ====================

@router.get("/views/{view}/state")
async def get_view_state(
    view: str,  # cost, incident, selfheal, governance
    tenant_id: str = Depends(get_tenant_id),
) -> ViewState:
    """Get persisted view state (filters, sorting, etc.)."""
    pass

@router.put("/views/{view}/state")
async def save_view_state(
    view: str,
    state: ViewState,
    tenant_id: str = Depends(get_tenant_id),
) -> ViewState:
    """Save view state for persistence across sessions."""
    pass

# ==================== Cross-View Deep Links ====================

@router.get("/deeplink/{entity_type}/{entity_id}")
async def resolve_deeplink(
    entity_type: str,  # incident, pattern, recovery, policy, anomaly
    entity_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> DeepLinkResolution:
    """
    Resolve an entity to its view and path.

    Returns:
    - view: Which view to navigate to
    - path: Full path within that view
    - breadcrumb: Human-readable breadcrumb
    """
    pass

# ==================== Actor Context ====================

@router.get("/actors")
async def list_actors(
    actor_type: Optional[str] = None,
    limit: int = Query(50, le=200),
    tenant_id: str = Depends(get_tenant_id),
) -> List[Actor]:
    """List all actors (humans, agents, systems) for tenant."""
    pass

@router.get("/actors/{actor_id}/timeline")
async def get_actor_timeline(
    actor_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, le=500),
    tenant_id: str = Depends(get_tenant_id),
) -> ActorTimeline:
    """
    Get timeline of all actions by an actor across all views.

    Shows incidents created, recoveries applied, policies modified, etc.
    """
    pass

# ==================== Related Entities ====================

@router.get("/related/{entity_type}/{entity_id}")
async def get_related_entities(
    entity_type: str,
    entity_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> RelatedEntities:
    """
    Get entities related across views.

    Example: For incident X, return:
    - Pattern that matched this incident
    - Recovery suggestions generated
    - Policy rules triggered
    - Cost impact
    """
    pass
```

### API Response Models

```python
# backend/app/models/control_center.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MetricsStrip(BaseModel):
    cost_current_cents: int
    cost_budget_cents: int
    cost_percentage: float
    incidents_active: int
    incidents_blocked_today: int
    recoveries_pending: int
    recoveries_applied_today: int
    policies_active: int
    policies_triggered_today: int
    health_score: int  # 0-100

class SearchResult(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    snippet: str
    actor_id: Optional[str]
    actor_type: Optional[str]
    actor_name: Optional[str]
    created_at: datetime
    view: str  # cost, incident, selfheal, governance
    path: str  # /cost/anomalies/anom_123

class SearchResults(BaseModel):
    query: str
    total: int
    results: List[SearchResult]
    facets: dict  # { entity_type: count, actor_type: count }

class DeepLinkResolution(BaseModel):
    entity_type: str
    entity_id: str
    view: str
    path: str
    breadcrumb: List[str]  # ["Incidents", "INC-123", "Timeline"]

class RelatedEntities(BaseModel):
    source: dict  # The entity we're querying about
    patterns: List[dict]
    recoveries: List[dict]
    policies: List[dict]
    cost_impact: Optional[dict]
    loop_events: List[dict]  # From M25 integration loop
```

---

## Frontend Implementation

### Control Center Layout

```tsx
// website/aos-console/console/src/components/ControlCenter/ControlCenterLayout.tsx

import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { TopNavBar } from './TopNavBar';
import { MetricsStrip } from './MetricsStrip';
import { ViewContainer } from './ViewContainer';
import { useMetricsStrip } from '@/hooks/useControlCenter';

type ViewType = 'cost' | 'incident' | 'selfheal' | 'governance';

export function ControlCenterLayout() {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentView = (searchParams.get('view') as ViewType) || 'incident';
  const { data: metrics, isLoading } = useMetricsStrip();

  const handleViewChange = (view: ViewType) => {
    setSearchParams({ view });
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Top Navigation with View Tabs */}
      <TopNavBar
        currentView={currentView}
        onViewChange={handleViewChange}
      />

      {/* Cross-Cutting Metrics Strip */}
      <MetricsStrip metrics={metrics} isLoading={isLoading} />

      {/* View Container */}
      <ViewContainer view={currentView} />
    </div>
  );
}
```

### Top Navigation Bar

```tsx
// website/aos-console/console/src/components/ControlCenter/TopNavBar.tsx

import { Search, DollarSign, AlertTriangle, Wrench, Shield } from 'lucide-react';
import { UnifiedSearch } from './UnifiedSearch';
import { cn } from '@/lib/utils';

const VIEWS = [
  { id: 'cost', label: 'Cost', icon: DollarSign, color: 'text-green-400' },
  { id: 'incident', label: 'Incident', icon: AlertTriangle, color: 'text-red-400' },
  { id: 'selfheal', label: 'Self-Heal', icon: Wrench, color: 'text-blue-400' },
  { id: 'governance', label: 'Governance', icon: Shield, color: 'text-purple-400' },
] as const;

interface TopNavBarProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

export function TopNavBar({ currentView, onViewChange }: TopNavBarProps) {
  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg" />
          <span className="text-lg font-semibold text-white">Control Center</span>
        </div>

        {/* View Tabs */}
        <nav className="flex items-center gap-1">
          {VIEWS.map(({ id, label, icon: Icon, color }) => (
            <button
              key={id}
              onClick={() => onViewChange(id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
                currentView === id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              )}
            >
              <Icon size={18} className={currentView === id ? color : ''} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        {/* Unified Search */}
        <UnifiedSearch />
      </div>
    </header>
  );
}
```

### Metrics Strip Component

```tsx
// website/aos-console/console/src/components/ControlCenter/MetricsStrip.tsx

import { DollarSign, AlertTriangle, Wrench, Shield, Activity } from 'lucide-react';
import { formatCurrency, formatNumber } from '@/lib/format';

interface MetricsStripProps {
  metrics: {
    cost_current_cents: number;
    cost_budget_cents: number;
    cost_percentage: number;
    incidents_active: number;
    incidents_blocked_today: number;
    recoveries_pending: number;
    recoveries_applied_today: number;
    policies_active: number;
    policies_triggered_today: number;
    health_score: number;
  } | null;
  isLoading: boolean;
}

export function MetricsStrip({ metrics, isLoading }: MetricsStripProps) {
  if (isLoading || !metrics) {
    return <div className="h-12 bg-gray-800/50 animate-pulse" />;
  }

  return (
    <div className="bg-gray-800/70 border-b border-gray-700 px-6 py-2">
      <div className="flex items-center justify-between text-sm">
        {/* Cost */}
        <div className="flex items-center gap-2">
          <DollarSign size={16} className="text-green-400" />
          <span className="text-gray-400">Cost:</span>
          <span className="text-white font-medium">
            {formatCurrency(metrics.cost_current_cents / 100)}
          </span>
          <span className="text-gray-500">/</span>
          <span className="text-gray-400">
            {formatCurrency(metrics.cost_budget_cents / 100)}
          </span>
          <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full',
                metrics.cost_percentage > 90 ? 'bg-red-500' :
                metrics.cost_percentage > 75 ? 'bg-yellow-500' : 'bg-green-500'
              )}
              style={{ width: `${Math.min(metrics.cost_percentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Incidents */}
        <div className="flex items-center gap-2">
          <AlertTriangle size={16} className="text-red-400" />
          <span className="text-white font-medium">{metrics.incidents_active}</span>
          <span className="text-gray-400">active</span>
          <span className="text-green-400">+{metrics.incidents_blocked_today} blocked</span>
        </div>

        {/* Recoveries */}
        <div className="flex items-center gap-2">
          <Wrench size={16} className="text-blue-400" />
          <span className="text-white font-medium">{metrics.recoveries_pending}</span>
          <span className="text-gray-400">pending</span>
          <span className="text-blue-400">+{metrics.recoveries_applied_today} applied</span>
        </div>

        {/* Policies */}
        <div className="flex items-center gap-2">
          <Shield size={16} className="text-purple-400" />
          <span className="text-white font-medium">{metrics.policies_active}</span>
          <span className="text-gray-400">policies</span>
          <span className="text-purple-400">+{metrics.policies_triggered_today} triggered</span>
        </div>

        {/* Health Score */}
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-cyan-400" />
          <span className="text-gray-400">Health:</span>
          <span className={cn(
            'font-bold',
            metrics.health_score >= 90 ? 'text-green-400' :
            metrics.health_score >= 70 ? 'text-yellow-400' : 'text-red-400'
          )}>
            {metrics.health_score}%
          </span>
        </div>
      </div>
    </div>
  );
}
```

### Unified Search Component

```tsx
// website/aos-console/console/src/components/ControlCenter/UnifiedSearch.tsx

import { useState, useRef, useEffect } from 'react';
import { Search, X, ExternalLink } from 'lucide-react';
import { useUnifiedSearch } from '@/hooks/useControlCenter';
import { useDebounce } from '@/hooks/useDebounce';
import { ActorBadge } from './ActorBadge';
import { useNavigate } from 'react-router-dom';

export function UnifiedSearch() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const { data: results, isLoading } = useUnifiedSearch(debouncedQuery);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Keyboard shortcut: Cmd+K or Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
        setQuery('');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleResultClick = (result: SearchResult) => {
    navigate(`/${result.view}${result.path}`);
    setIsOpen(false);
    setQuery('');
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
      >
        <Search size={16} />
        <span className="text-sm">Search...</span>
        <kbd className="ml-4 text-xs bg-gray-600 px-1.5 py-0.5 rounded">⌘K</kbd>
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/50">
          <div className="w-full max-w-2xl bg-gray-800 rounded-xl shadow-2xl border border-gray-700">
            {/* Search Input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-700">
              <Search size={20} className="text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search incidents, recoveries, policies, anomalies..."
                className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none"
                autoFocus
              />
              {query && (
                <button onClick={() => setQuery('')}>
                  <X size={18} className="text-gray-400 hover:text-white" />
                </button>
              )}
            </div>

            {/* Results */}
            <div className="max-h-96 overflow-y-auto">
              {isLoading ? (
                <div className="p-4 text-center text-gray-400">Searching...</div>
              ) : results?.results.length === 0 ? (
                <div className="p-4 text-center text-gray-400">
                  No results for "{query}"
                </div>
              ) : (
                <ul className="py-2">
                  {results?.results.map((result) => (
                    <li key={`${result.entity_type}-${result.entity_id}`}>
                      <button
                        onClick={() => handleResultClick(result)}
                        className="w-full px-4 py-3 hover:bg-gray-700/50 flex items-start gap-3 text-left"
                      >
                        <ViewIcon view={result.view} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-white truncate">
                              {result.title}
                            </span>
                            {result.actor_id && (
                              <ActorBadge
                                type={result.actor_type}
                                name={result.actor_name}
                                size="sm"
                              />
                            )}
                          </div>
                          <p className="text-sm text-gray-400 truncate">
                            {result.snippet}
                          </p>
                        </div>
                        <ExternalLink size={16} className="text-gray-500 flex-shrink-0" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Facets */}
            {results?.facets && (
              <div className="px-4 py-2 border-t border-gray-700 flex gap-4 text-xs text-gray-500">
                <span>Incidents: {results.facets.incident || 0}</span>
                <span>Recoveries: {results.facets.recovery || 0}</span>
                <span>Policies: {results.facets.policy || 0}</span>
                <span>Anomalies: {results.facets.cost_anomaly || 0}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

### Actor Badge Component

```tsx
// website/aos-console/console/src/components/ControlCenter/ActorBadge.tsx

import { User, Bot, Cpu, Shield, Wrench } from 'lucide-react';
import { cn } from '@/lib/utils';

const ACTOR_CONFIG = {
  human: { icon: User, color: 'bg-blue-500/20 text-blue-400', label: 'Human' },
  agent: { icon: Bot, color: 'bg-purple-500/20 text-purple-400', label: 'Agent' },
  system: { icon: Cpu, color: 'bg-gray-500/20 text-gray-400', label: 'System' },
  policy: { icon: Shield, color: 'bg-yellow-500/20 text-yellow-400', label: 'Policy' },
  recovery: { icon: Wrench, color: 'bg-green-500/20 text-green-400', label: 'Recovery' },
};

interface ActorBadgeProps {
  type: string;
  name?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function ActorBadge({ type, name, size = 'md', showLabel = false }: ActorBadgeProps) {
  const config = ACTOR_CONFIG[type as keyof typeof ACTOR_CONFIG] || ACTOR_CONFIG.system;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs gap-1',
    md: 'px-2 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  };

  const iconSizes = { sm: 12, md: 14, lg: 18 };

  return (
    <span className={cn(
      'inline-flex items-center rounded-full font-medium',
      config.color,
      sizeClasses[size]
    )}>
      <Icon size={iconSizes[size]} />
      {(showLabel || name) && (
        <span>{name || config.label}</span>
      )}
    </span>
  );
}
```

### Cross-View Deep Link Component

```tsx
// website/aos-console/console/src/components/ControlCenter/CrossViewLink.tsx

import { ExternalLink } from 'lucide-react';
import { useDeepLink } from '@/hooks/useControlCenter';
import { Link } from 'react-router-dom';

interface CrossViewLinkProps {
  entityType: string;
  entityId: string;
  children?: React.ReactNode;
  className?: string;
}

export function CrossViewLink({
  entityType,
  entityId,
  children,
  className
}: CrossViewLinkProps) {
  const { data: deepLink, isLoading } = useDeepLink(entityType, entityId);

  if (isLoading || !deepLink) {
    return <span className={className}>{children || entityId}</span>;
  }

  return (
    <Link
      to={`/${deepLink.view}${deepLink.path}`}
      className={cn(
        'inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline',
        className
      )}
    >
      {children || deepLink.breadcrumb.join(' → ')}
      <ExternalLink size={12} />
    </Link>
  );
}
```

---

## View-to-View Navigation

### Deep Link Resolution

| From View | Entity | Navigates To |
|-----------|--------|--------------|
| Incident | Pattern Match | Self-Heal → Pattern Viewer |
| Incident | Cost Impact | Cost → Anomaly Details |
| Self-Heal | Policy Created | Governance → Policy Editor |
| Self-Heal | Cost Recovery | Cost → Projections |
| Governance | Incident Triggered | Incident → Details |
| Governance | Routing Change | Self-Heal → CARE Config |
| Cost | Budget Alert | Governance → Budget Policy |
| Cost | Anomaly Incident | Incident → Details |

### URL Structure

```
/control-center?view=cost
/control-center?view=cost&tab=anomalies&id=anom_123
/control-center?view=incident&id=inc_456
/control-center?view=selfheal&tab=recovery&id=rec_789
/control-center?view=governance&tab=policies&id=pol_012
```

---

## Implementation Plan

### Phase 1: Foundation (Days 1-3)

| Task | Priority | Effort |
|------|----------|--------|
| Create ControlCenterLayout component | P0 | 4h |
| Create TopNavBar with view tabs | P0 | 3h |
| Create MetricsStrip component | P0 | 3h |
| Add `/control-center` route | P0 | 1h |
| Create controlCenterStore (Zustand) | P0 | 2h |
| Migration 045 (actor attribution) | P0 | 4h |
| Actor model and service | P0 | 4h |

**Deliverable:** Basic 4-tab layout with metrics strip

### Phase 2: View Migration (Days 4-6)

| Task | Priority | Effort |
|------|----------|--------|
| Migrate Guard Console → IncidentView | P0 | 6h |
| Migrate Failures/Recovery → SelfHealView | P0 | 4h |
| Migrate SBA/Policy → GovernanceView | P0 | 4h |
| Create CostView shell (M26 integration) | P0 | 4h |
| Update routes to use new structure | P0 | 2h |
| Remove old Guard Console standalone routes | P1 | 2h |

**Deliverable:** All views accessible from unified console

### Phase 3: Cross-View Features (Days 7-8)

| Task | Priority | Effort |
|------|----------|--------|
| UnifiedSearch component | P0 | 6h |
| `/control-center/search` API | P0 | 4h |
| CrossViewLink component | P0 | 3h |
| DeepLink resolution API | P0 | 3h |
| Related entities API | P1 | 4h |
| Actor timeline API | P1 | 4h |

**Deliverable:** Search and cross-view navigation working

### Phase 4: Actor Attribution (Days 9-10)

| Task | Priority | Effort |
|------|----------|--------|
| ActorBadge component | P0 | 2h |
| Add actor_id to all event creation | P0 | 6h |
| Actor context in request middleware | P0 | 3h |
| Backfill existing events with system actor | P1 | 2h |
| Actor filter in unified search | P1 | 2h |
| Actor timeline page | P2 | 4h |

**Deliverable:** All events attributed to actors

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_m28_control_center.py

import pytest
from app.api.control_center import router
from app.models.control_center import MetricsStrip, SearchResults

class TestControlCenterAPI:
    """Tests for Control Center API endpoints."""

    async def test_metrics_strip_returns_all_fields(self, client, tenant_id):
        """Metrics strip returns all 10 required fields."""
        response = await client.get(
            "/control-center/metrics/strip",
            headers={"X-Tenant-ID": tenant_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert "cost_current_cents" in data
        assert "cost_budget_cents" in data
        assert "incidents_active" in data
        assert "recoveries_pending" in data
        assert "policies_active" in data
        assert "health_score" in data

    async def test_unified_search_returns_results(self, client, tenant_id):
        """Unified search returns results from all views."""
        response = await client.get(
            "/control-center/search?q=error",
            headers={"X-Tenant-ID": tenant_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "facets" in data

    async def test_deeplink_resolution(self, client, tenant_id, incident_id):
        """Deep link resolves to correct view and path."""
        response = await client.get(
            f"/control-center/deeplink/incident/{incident_id}",
            headers={"X-Tenant-ID": tenant_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["view"] == "incident"
        assert incident_id in data["path"]

class TestActorAttribution:
    """Tests for actor attribution system."""

    async def test_actor_created_for_human(self, client, user_id):
        """Human actions create human actor."""
        # Create incident via API (human action)
        response = await client.post("/incidents", json={...})
        assert response.status_code == 201

        # Verify actor attribution
        incident_id = response.json()["id"]
        incident = await get_incident(incident_id)
        assert incident.actor_id is not None
        actor = await get_actor(incident.actor_id)
        assert actor.type == "human"

    async def test_actor_created_for_agent(self, client, agent_id):
        """Agent actions create agent actor."""
        # Trigger agent action
        # ... verify actor attribution

    async def test_actor_created_for_system(self):
        """Scheduled jobs create system actor."""
        # Run scheduled job
        # ... verify actor attribution
```

### E2E Tests

```typescript
// website/aos-console/console/tests/e2e/control-center.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Control Center', () => {
  test('can navigate between views', async ({ page }) => {
    await page.goto('/control-center');

    // Default to incident view
    await expect(page.locator('[data-view="incident"]')).toHaveClass(/active/);

    // Click cost tab
    await page.click('[data-view="cost"]');
    await expect(page).toHaveURL(/view=cost/);

    // Click self-heal tab
    await page.click('[data-view="selfheal"]');
    await expect(page).toHaveURL(/view=selfheal/);
  });

  test('unified search finds results', async ({ page }) => {
    await page.goto('/control-center');

    // Open search with keyboard shortcut
    await page.keyboard.press('Meta+k');
    await expect(page.locator('[data-testid="unified-search"]')).toBeVisible();

    // Type search query
    await page.fill('[data-testid="search-input"]', 'error');

    // Wait for results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
  });

  test('cross-view links navigate correctly', async ({ page }) => {
    await page.goto('/control-center?view=incident&id=inc_123');

    // Click on related pattern
    await page.click('[data-testid="related-pattern-link"]');

    // Should navigate to self-heal view
    await expect(page).toHaveURL(/view=selfheal/);
  });
});
```

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| View switch latency | <200ms | React profiler |
| Unified search latency | <500ms | API timing |
| Metrics strip refresh | <300ms | API timing |
| Deep link resolution | <100ms | API timing |
| All events have actor_id | 100% | Database query |
| Cross-view links work | All 8 types | E2E tests |

---

## Migration Strategy

### Phase A: Parallel Deployment

1. Deploy Control Center at `/control-center`
2. Keep existing consoles running at `/guard`, `/ops`
3. Add "Try new Control Center" banner to old consoles

### Phase B: Feature Parity Verification

1. Run both consoles in production for 1 week
2. Verify all functionality works in Control Center
3. Collect user feedback

### Phase C: Redirect

1. Add redirect from `/guard` → `/control-center?view=incident`
2. Add redirect from `/ops` → `/control-center?view=cost`
3. Keep old URLs working with redirects

### Phase D: Cleanup

1. Remove old Guard Console standalone code
2. Remove old Ops Console standalone code
3. Archive old route configurations

---

## Rollback Plan

If issues arise:

1. **Immediate:** Redirect `/control-center` back to `/guard`
2. **Actor attribution issues:** Make `actor_id` nullable, default to `system`
3. **Search performance:** Disable materialized view, fall back to individual queries
4. **View migration issues:** Revert to standalone consoles via feature flag

---

## Related Documentation

- PIN-128: Master Plan M25-M30 (source specification)
- PIN-129: M25 Pillar Integration (loop architecture)
- PIN-130: M26 Cost Intelligence (cost view source)
- PIN-131: M27 Cost Loop Integration (cost→loop wiring)
- PIN-095: AI Incident Console Strategy (incident view source)
- PIN-111: Founder Ops Console UI (ops view source)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Initial creation - M28 Unified Console Blueprint |
