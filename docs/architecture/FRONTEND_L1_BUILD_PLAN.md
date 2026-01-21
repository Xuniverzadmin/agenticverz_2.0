# Frontend L1 Build Plan — AI Governance Console

**Status:** ACTIVE
**Created:** 2026-01-20
**Target:** `preflight-console.agenticverz.com/precus/*`
**Phase:** Manual Build (AURORA bypassed)
**Reference:** `CUSTOMER_CONSOLE_V2_CONSTITUTION.md`, `BACKEND_DOMAIN_INVENTORY.md`

---

## Executive Summary

This plan defines the Layer 1 (L1 — Product Experience) build strategy for the AI Governance Console. Due to AURORA pipeline complexity, we are building the frontend **manually** with direct API integration and synthetic/real data testing via SDSR scenarios.

**Key Decisions:**
- **Manual Build:** No AURORA compiler dependency
- **Direct API Calls:** Frontend calls backend unified facades directly
- **SDSR Testing:** Synthetic scenarios for validation, real data for production
- **Progressive Enhancement:** Start with O1-O2 (list views), add O3-O5 later

---

## 1. Architecture Principles

### 1.1 Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | React 18 + TypeScript |
| Routing | React Router v6 |
| State | TanStack Query (React Query) |
| UI Components | Radix UI + Tailwind CSS |
| Build | Vite |
| API Client | Fetch + typed wrappers |

### 1.2 Directory Structure

```
website/app-shell/src/
├── api/                    # API client functions
│   ├── overview.ts
│   ├── activity.ts
│   ├── incidents.ts
│   ├── policies.ts
│   ├── logs.ts
│   ├── analytics.ts
│   ├── connectivity.ts
│   └── accounts.ts
├── components/
│   ├── layout/             # Shell, Sidebar, Header
│   ├── panels/             # Domain-specific panels
│   │   ├── overview/
│   │   ├── activity/
│   │   ├── incidents/
│   │   ├── policies/
│   │   ├── logs/
│   │   ├── analytics/
│   │   ├── connectivity/
│   │   └── accounts/
│   └── shared/             # Reusable components
├── pages/
│   └── precus/             # Preflight Console pages
│       ├── overview/
│       ├── activity/
│       ├── incidents/
│       ├── policies/
│       ├── logs/
│       ├── analytics/
│       ├── connectivity/
│       └── account/
├── hooks/                  # Custom hooks
├── types/                  # TypeScript types
└── lib/                    # Utilities
```

### 1.3 Routing Pattern

```
/precus                           → Overview (default)
/precus/overview                  → Overview > Summary > Highlights
/precus/activity                  → Activity > LLM Runs > Live (default)
/precus/activity/runs/live        → Activity > LLM Runs > Live
/precus/activity/runs/completed   → Activity > LLM Runs > Completed
/precus/activity/runs/signals     → Activity > LLM Runs > Signals
/precus/incidents                 → Incidents > Events > Active (default)
/precus/incidents/events/active   → Incidents > Events > Active
/precus/incidents/events/resolved → Incidents > Events > Resolved
/precus/incidents/events/history  → Incidents > Events > Historical
/precus/policies                  → Policies > Governance > Active (default)
/precus/policies/governance/active    → Active policies
/precus/policies/governance/lessons   → Lessons & proposals
/precus/policies/governance/library   → Policy library
/precus/policies/limits/controls      → Controls
/precus/policies/limits/violations    → Violations
/precus/logs                      → Logs > Records > LLM Runs (default)
/precus/logs/records/llm-runs     → LLM run logs
/precus/logs/records/system       → System logs
/precus/logs/records/audit        → Audit logs
/precus/analytics                 → Analytics > Insights > Cost (default)
/precus/analytics/insights/cost   → Cost intelligence
/precus/analytics/usage/policies  → Policy usage
/precus/analytics/usage/productivity → Productivity metrics
/precus/connectivity              → Connectivity > Integrations (default)
/precus/connectivity/integrations → SDK integration
/precus/connectivity/api          → API keys
/precus/account                   → Account > Profile (default)
/precus/account/profile           → Profile
/precus/account/billing           → Billing & invoices
/precus/account/team              → Team members (admin)
/precus/account/settings          → Account settings
```

---

## 2. Build Phases

### Phase 1: Shell & Navigation (Week 1)

**Goal:** Working shell with sidebar navigation across all domains.

| Task | Priority | Description |
|------|----------|-------------|
| 1.1 | P0 | Create `AppShell` with sidebar, header, content area |
| 1.2 | P0 | Implement sidebar with 8 domains (3 tiers) |
| 1.3 | P0 | Create route definitions for all domains |
| 1.4 | P0 | Add project selector in header |
| 1.5 | P1 | Add account dropdown (top-right) |
| 1.6 | P1 | Implement breadcrumb navigation |
| 1.7 | P2 | Add loading/error states |

**Deliverables:**
- Navigable shell with all routes
- Empty page placeholders for each domain
- Consistent sidebar highlighting

### Phase 2: Core Lenses - O1 Views (Week 2)

**Goal:** Summary views for all 5 core lenses.

| Domain | O1 Panel | API Endpoint | Components |
|--------|----------|--------------|------------|
| Overview | Highlights | `/api/v1/overview/highlights` | `HighlightsCard`, `PulseIndicator` |
| Activity | Live Runs | `/api/v1/activity/runs/live` | `RunsListTable`, `RunStatusBadge` |
| Incidents | Active | `/api/v1/incidents/active` | `IncidentsListTable`, `SeverityBadge` |
| Policies | Active | `/api/v1/policies/active` | `PoliciesListTable`, `PolicyTypeBadge` |
| Logs | LLM Runs | `/api/v1/logs/llm-runs` | `LogsListTable`, `LogLevelBadge` |

**Tasks:**
| Task | Priority | Description |
|------|----------|-------------|
| 2.1 | P0 | Create API client functions for each domain |
| 2.2 | P0 | Create shared table component (`DataTable`) |
| 2.3 | P0 | Implement Overview > Highlights panel |
| 2.4 | P0 | Implement Activity > Live runs list |
| 2.5 | P0 | Implement Incidents > Active list |
| 2.6 | P0 | Implement Policies > Active list |
| 2.7 | P0 | Implement Logs > LLM Runs list |
| 2.8 | P1 | Add empty state UX for each panel |
| 2.9 | P1 | Add loading skeletons |

### Phase 3: Core Lenses - O2 Views (Week 3)

**Goal:** List views with filters and pagination.

| Domain | O2 Panel | Features |
|--------|----------|----------|
| Activity | Completed runs | Filters: status, date, model |
| Activity | Signals | Filters: type, severity |
| Incidents | Resolved | Filters: date, resolution type |
| Incidents | Historical | Filters: date range, pattern |
| Policies | Lessons | Filters: status (pending/accepted/deferred) |
| Policies | Limits | Filters: limit type |
| Logs | System | Filters: level, source |
| Logs | Audit | Filters: actor, action type |

**Tasks:**
| Task | Priority | Description |
|------|----------|-------------|
| 3.1 | P0 | Add filter bar component |
| 3.2 | P0 | Add pagination component |
| 3.3 | P0 | Implement Activity topic tabs (Live/Completed/Signals) |
| 3.4 | P0 | Implement Incidents topic tabs |
| 3.5 | P0 | Implement Policies subdomain tabs (Governance/Limits) |
| 3.6 | P0 | Implement Logs topic tabs |
| 3.7 | P1 | Add URL-synced filters |
| 3.8 | P1 | Add search functionality |

### Phase 4: Intelligence & Infrastructure Domains (Week 4)

**Goal:** Analytics, Connectivity, Account domains.

| Domain | Panels | Features |
|--------|--------|----------|
| Analytics | Cost Intelligence | Cost charts, trend lines, anomaly highlights |
| Analytics | Usage Statistics | Policy effectiveness, productivity metrics |
| Connectivity | Integrations | SDK status, setup wizard |
| Connectivity | API Keys | Key list, create/rotate/revoke actions |
| Account | Profile | Org info, edit form |
| Account | Billing | Usage summary, invoices list |
| Account | Team | Members list, invite flow (admin) |

**Tasks:**
| Task | Priority | Description |
|------|----------|-------------|
| 4.1 | P0 | Implement Analytics > Cost Intelligence |
| 4.2 | P0 | Implement Connectivity > API Keys |
| 4.3 | P0 | Implement Account > Profile |
| 4.4 | P1 | Implement Analytics > Usage Statistics |
| 4.5 | P1 | Implement Connectivity > Integrations |
| 4.6 | P1 | Implement Account > Billing |
| 4.7 | P2 | Implement Account > Team (admin flow) |

### Phase 5: O3 Detail Views (Week 5-6)

**Goal:** Detail pages for all domains.

| Domain | O3 View | Features |
|--------|---------|----------|
| Activity | Run Detail | Full trace, steps, cost breakdown |
| Incidents | Incident Detail | Timeline, root cause, related runs |
| Policies | Policy Detail | Rule definition, coverage, history |
| Logs | Log Detail | Full record, context, cross-links |

**Tasks:**
| Task | Priority | Description |
|------|----------|-------------|
| 5.1 | P0 | Implement Run Detail page |
| 5.2 | P0 | Implement Incident Detail page |
| 5.3 | P0 | Implement Policy Detail page |
| 5.4 | P1 | Implement Log Detail page |
| 5.5 | P1 | Add cross-domain links |
| 5.6 | P2 | Add O4 context panels (sidebar) |

---

## 3. Component Library

### 3.1 Layout Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `AppShell` | Main application shell | `components/layout/AppShell.tsx` |
| `Sidebar` | Domain navigation | `components/layout/Sidebar.tsx` |
| `Header` | Project selector, account | `components/layout/Header.tsx` |
| `ContentArea` | Main content wrapper | `components/layout/ContentArea.tsx` |
| `Breadcrumb` | Navigation breadcrumbs | `components/layout/Breadcrumb.tsx` |

### 3.2 Shared Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `DataTable` | Sortable, filterable table | `components/shared/DataTable.tsx` |
| `FilterBar` | Filter controls | `components/shared/FilterBar.tsx` |
| `Pagination` | Page navigation | `components/shared/Pagination.tsx` |
| `EmptyState` | No data placeholder | `components/shared/EmptyState.tsx` |
| `LoadingSkeleton` | Loading placeholder | `components/shared/LoadingSkeleton.tsx` |
| `StatusBadge` | Status indicator | `components/shared/StatusBadge.tsx` |
| `MetricCard` | Metric display card | `components/shared/MetricCard.tsx` |
| `TimelineView` | Event timeline | `components/shared/TimelineView.tsx` |

### 3.3 Domain Panels

| Panel | Domain | Location |
|-------|--------|----------|
| `HighlightsPanel` | Overview | `components/panels/overview/HighlightsPanel.tsx` |
| `DecisionsPanel` | Overview | `components/panels/overview/DecisionsPanel.tsx` |
| `LiveRunsPanel` | Activity | `components/panels/activity/LiveRunsPanel.tsx` |
| `CompletedRunsPanel` | Activity | `components/panels/activity/CompletedRunsPanel.tsx` |
| `SignalsPanel` | Activity | `components/panels/activity/SignalsPanel.tsx` |
| `ActiveIncidentsPanel` | Incidents | `components/panels/incidents/ActiveIncidentsPanel.tsx` |
| `ResolvedIncidentsPanel` | Incidents | `components/panels/incidents/ResolvedIncidentsPanel.tsx` |
| `ActivePoliciesPanel` | Policies | `components/panels/policies/ActivePoliciesPanel.tsx` |
| `LessonsPanel` | Policies | `components/panels/policies/LessonsPanel.tsx` |
| `ControlsPanel` | Policies | `components/panels/policies/ControlsPanel.tsx` |
| `LlmRunLogsPanel` | Logs | `components/panels/logs/LlmRunLogsPanel.tsx` |
| `SystemLogsPanel` | Logs | `components/panels/logs/SystemLogsPanel.tsx` |
| `AuditLogsPanel` | Logs | `components/panels/logs/AuditLogsPanel.tsx` |
| `CostIntelligencePanel` | Analytics | `components/panels/analytics/CostIntelligencePanel.tsx` |
| `ApiKeysPanel` | Connectivity | `components/panels/connectivity/ApiKeysPanel.tsx` |
| `ProfilePanel` | Account | `components/panels/account/ProfilePanel.tsx` |
| `BillingPanel` | Account | `components/panels/account/BillingPanel.tsx` |

---

## 4. API Integration

### 4.1 API Client Pattern

```typescript
// api/client.ts
const API_BASE = '/api/v1';

export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.json());
  }

  const data = await response.json();
  return data.data; // Unwrap envelope
}
```

### 4.2 Domain API Functions

```typescript
// api/activity.ts
export const activityApi = {
  getLiveRuns: () => fetchApi<Run[]>('/activity/runs/live'),
  getCompletedRuns: (filters: RunFilters) =>
    fetchApi<PaginatedResponse<Run>>('/activity/runs/completed', {
      params: filters
    }),
  getRunDetail: (id: string) => fetchApi<RunDetail>(`/activity/runs/${id}`),
  getSignals: () => fetchApi<Signal[]>('/activity/signals'),
};

// Similar for other domains...
```

### 4.3 React Query Integration

```typescript
// hooks/useActivity.ts
export function useLiveRuns() {
  return useQuery({
    queryKey: ['activity', 'runs', 'live'],
    queryFn: activityApi.getLiveRuns,
    refetchInterval: 5000, // Poll every 5s for live data
  });
}

export function useCompletedRuns(filters: RunFilters) {
  return useQuery({
    queryKey: ['activity', 'runs', 'completed', filters],
    queryFn: () => activityApi.getCompletedRuns(filters),
  });
}
```

---

## 5. Testing Strategy

### 5.1 Synthetic Data Testing (SDSR)

Use SDSR scenarios to inject synthetic data for testing.

**Scenario Types:**
| Scenario | Purpose | Data Injected |
|----------|---------|---------------|
| `basic_run_flow.yaml` | Happy path run | 1 completed run |
| `failed_run_incident.yaml` | Failure flow | 1 failed run + incident |
| `policy_violation.yaml` | Limit breach | 1 violation |
| `multi_domain_propagation.yaml` | Cross-domain | Run → Incident → Policy → Logs |

**Test Execution:**
```bash
# Inject synthetic scenario
python backend/scripts/sdsr/inject_synthetic.py \
  --scenario backend/scripts/sdsr/scenarios/basic_run_flow.yaml \
  --wait

# Verify frontend displays data
# (manual or Playwright tests)

# Cleanup
python backend/scripts/sdsr/cleanup_synthetic.py \
  --scenario-id <id>
```

### 5.2 Real Data Testing

After synthetic validation, test with real LLM runs:

1. Configure test tenant with API key
2. Execute real LLM runs via SDK
3. Verify data propagation through all domains
4. Check cost calculation accuracy

### 5.3 Frontend Tests

| Test Type | Tool | Coverage |
|-----------|------|----------|
| Unit | Vitest | Components, hooks |
| Integration | Playwright | User flows |
| Visual | Chromatic | Component snapshots |

---

## 6. Deployment

### 6.1 Build Commands

```bash
# Development
cd website/app-shell
npm run dev

# Production build
npm run build

# Deploy to preflight
cp -r dist/* dist-preflight/
sudo systemctl reload apache2
```

### 6.2 Environment Variables

```env
VITE_API_BASE_URL=/api/v1
VITE_AUTH_DOMAIN=clerk.agenticverz.com
VITE_CONSOLE_TYPE=preflight
```

### 6.3 Apache Configuration

Already configured:
- `preflight-console.agenticverz.com.conf` → `dist-preflight/`
- SPA fallback to `index.html`
- Cache-busting headers

---

## 7. Success Criteria

### Phase 1 Complete When:
- [ ] All 8 domains navigable from sidebar
- [ ] Breadcrumbs work correctly
- [ ] Project selector functional
- [ ] Account dropdown functional

### Phase 2-3 Complete When:
- [ ] O1 summary views for all core lenses
- [ ] O2 list views with filters
- [ ] Empty states render correctly
- [ ] Loading states work

### Phase 4 Complete When:
- [ ] Analytics domain functional
- [ ] Connectivity domain functional
- [ ] Account domain functional

### Phase 5 Complete When:
- [ ] O3 detail views for Activity, Incidents, Policies
- [ ] Cross-domain links work
- [ ] SDSR scenarios pass

### Full Build Complete When:
- [ ] All domains at O1-O3 depth
- [ ] Synthetic data tests pass
- [ ] Real data tests pass
- [ ] Performance acceptable (<3s load)

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backend API gaps | High | Use BACKEND_DOMAIN_INVENTORY.md; flag gaps early |
| Auth integration issues | High | Test with stub tokens first; integrate Clerk last |
| Performance with large datasets | Medium | Implement pagination from start; add virtualization |
| SDSR scenario failures | Medium | Fix scenarios or backend; don't work around |

---

## 9. Projection Architecture

The frontend navigation structure is driven by the **V2 Constitution** projection, not the AURORA pipeline.

**Key Files:**
| File | Role |
|------|------|
| `design/v2_constitution/ui_projection_lock.json` | Authoritative source |
| `src/contracts/ui_plan_scaffolding.ts` | TypeScript fallback |
| `public/projection/ui_projection_lock.json` | Runtime projection |

**Rule:** V2 Constitution is truth. AURORA pipeline is deprecated.

**Full documentation:** `docs/architecture/FRONTEND_PROJECTION_ARCHITECTURE.md`

---

## 10. References

| Document | Purpose |
|----------|---------|
| `CUSTOMER_CONSOLE_V2_CONSTITUTION.md` | Domain definitions |
| `FRONTEND_PROJECTION_ARCHITECTURE.md` | Projection source & decoupling |
| `BACKEND_DOMAIN_INVENTORY.md` | API mapping |
| `design/l2_1/INTENT_LEDGER.md` | Panel IDs |
| `docs/architecture/auth/AUTH_CONSOLE_CONTRACT.md` | Auth patterns |
| `docs/governance/SDSR_E2E_TESTING_PROTOCOL.md` | Testing protocol |

---

**This plan is the execution guide for the AI Governance Console frontend build.**

**Build manually. Test with SDSR. Deploy progressively.**
