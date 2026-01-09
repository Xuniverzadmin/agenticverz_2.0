# PIN-371: SDSR to UI Pipeline Integration

**Status:** COMPLETE
**Created:** 2026-01-09
**Category:** Architecture / Pipeline Integration
**Related PINs:** PIN-370 (SDSR), PIN-318 (Authority Model)

---

## Summary

Documents the complete data flow from SDSR backend pipeline to UI rendering in the Customer Console. This PIN captures the architectural linkage between synthetic data injection, API layer, React Query data binding, and panel rendering.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SDSR → UI PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   BACKEND    │    │     API      │    │   FRONTEND   │                   │
│  │   PIPELINE   │───▶│    LAYER     │───▶│   PIPELINE   │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ Incident     │    │ /api/v1/     │    │ React Query  │                   │
│  │ Engine       │    │ incidents    │    │ + Registry   │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ Canonical    │    │ JSON         │    │ DomainPage   │                   │
│  │ incidents    │    │ Response     │    │ Panels       │                   │
│  │ table        │    │              │    │              │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Backend Pipeline (L4/L5)

### 1.1 Incident Engine (L4 Domain Logic)

**File:** `backend/app/services/incident_engine.py`

The Incident Engine is the authoritative source for incident creation. It implements:

```python
class IncidentEngine:
    def create_incident_for_failed_run(
        self,
        run_id: str,
        tenant_id: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        # Creates incident in canonical 'incidents' table
```

**Normalization Contract:**
- `severity`: Always UPPERCASE (CRITICAL, HIGH, MEDIUM, LOW)
- `status`: Always UPPERCASE (OPEN, ACKNOWLEDGED, RESOLVED, CLOSED)
- `category`: Always UPPERCASE (EXECUTION_FAILURE, BUDGET_EXCEEDED, etc.)

### 1.2 Worker Integration (L5)

**File:** `backend/app/worker/runner.py`

Incidents are created automatically on run failure:

```python
def _create_incident_for_failure(self, error_message: Optional[str] = None):
    """Create incident when run fails. SDSR Cross-Domain Propagation (PIN-370)"""
    incident_engine = get_incident_engine()
    incident_id = incident_engine.check_and_create_incident(
        run_id=self.run_id,
        status='failed',
        error_message=error_message,
        tenant_id=self.tenant_id,
        agent_id=self.agent_id,
        is_synthetic=self.is_synthetic,
        synthetic_scenario_id=self.synthetic_scenario_id,
    )
```

### 1.3 Canonical Database Table (L6)

**Table:** `incidents` (consolidated from PIN-370)

```sql
CREATE TABLE incidents (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT,           -- CRITICAL, HIGH, MEDIUM, LOW
    status TEXT,             -- OPEN, ACKNOWLEDGED, RESOLVED, CLOSED
    trigger_type TEXT,
    started_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    -- SDSR columns (PIN-370)
    source_run_id TEXT,      -- Links to originating run
    source_type TEXT,        -- 'run', 'killswitch', 'policy', 'manual'
    category TEXT,           -- EXECUTION_FAILURE, POLICY_VIOLATION, etc.
    description TEXT,
    error_code TEXT,
    error_message TEXT,
    impact_scope TEXT,
    affected_agent_id TEXT,
    affected_count INTEGER DEFAULT 1,
    is_synthetic BOOLEAN DEFAULT false,
    synthetic_scenario_id TEXT
);
```

---

## Layer 2: API Layer (L2)

### 2.1 Incidents API Endpoints

**File:** `backend/app/api/incidents.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/incidents` | GET | List incidents with pagination |
| `/api/v1/incidents/metrics` | GET | Summary metrics (counts by severity) |
| `/api/v1/incidents/{id}` | GET | Single incident detail |
| `/api/v1/incidents/by-run/{run_id}` | GET | Incidents linked to a run |
| `/api/v1/incidents/trigger` | POST | **[DEPRECATED]** Manual trigger |

### 2.2 Response Models

```python
class IncidentSummary(BaseModel):
    id: str
    source_run_id: Optional[str]
    source_type: str
    category: str
    severity: str           # Normalized to UPPERCASE
    status: str             # Normalized to UPPERCASE
    title: str
    description: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    tenant_id: str
    affected_agent_id: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    is_synthetic: bool
    synthetic_scenario_id: Optional[str]

class IncidentsMetricsResponse(BaseModel):
    total_open: int
    total_resolved: int
    by_severity: IncidentCountBySeverity  # critical, high, medium, low
```

### 2.3 Auth Bypass for SDSR

**Files:**
- `backend/app/api/gateway_config.py`
- `backend/app/auth/rbac_middleware.py`

```python
public_paths = [
    "/api/v1/incidents",
    "/api/v1/incidents/",
    # ... other paths
]
```

---

## Layer 3: Frontend Pipeline (L1)

### 3.1 API Client Layer

**File:** `website/app-shell/src/api/incidents.ts`

```typescript
export async function fetchIncidents(params?: {
  status?: string;
  severity?: string;
  include_synthetic?: boolean;
  page?: number;
  per_page?: number;
}): Promise<IncidentsResponse> {
  const response = await apiClient.get('/api/v1/incidents', { params });
  return response.data;
}

export async function fetchIncidentsMetrics(
  includeSynthetic: boolean = true
): Promise<IncidentsMetricsResponse> {
  const response = await apiClient.get('/api/v1/incidents/metrics', {
    params: { include_synthetic: includeSynthetic }
  });
  return response.data;
}
```

### 3.2 React Query Data Binding

**File:** `website/app-shell/src/main.tsx`

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15000,           // Data stale after 15s
      retry: 1,
      refetchOnWindowFocus: true, // Auto-refresh on tab focus
      refetchOnMount: true,       // Refresh on component mount
    },
  },
});
```

### 3.3 Panel Content Registry

**File:** `website/app-shell/src/components/panels/PanelContentRegistry.tsx`

Each incident panel is registered with React Query hooks:

```typescript
// Panel: INC-AI-OI-O1 (Open Incidents Summary)
function OpenIncidentsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'metrics'],
    queryFn: () => fetchIncidentsMetrics(true),
    refetchInterval: 30000,  // Refresh every 30s
    staleTime: 10000,
  });

  // Renders: count + severity badges
}

// Panel: INC-AI-OI-O2 (Open Incidents List)
function OpenIncidentsList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'open', 'list'],
    queryFn: () => fetchIncidents({
      status: 'OPEN',
      include_synthetic: true,
      per_page: 10
    }),
    refetchInterval: 15000,  // More frequent refresh
    staleTime: 5000,
  });

  // Renders: list of incident items
}
```

### 3.4 Panel ID Registry

| Panel ID | Component | Query Key | Refresh |
|----------|-----------|-----------|---------|
| `INC-AI-OI-O1` | OpenIncidentsSummary | `['incidents', 'metrics']` | 30s |
| `INC-AI-OI-O2` | OpenIncidentsList | `['incidents', 'open', 'list']` | 15s |
| `INC-AI-ID-O1` | IncidentSummaryPanel | `['incidents', 'all']` | 30s |
| `INC-HI-RI-O1` | ResolvedIncidentsSummary | `['incidents', 'resolved', 'metrics']` | 30s |
| `INC-HI-RI-O2` | ResolvedIncidentsList | `['incidents', 'resolved', 'list']` | 30s |

### 3.5 DomainPage Rendering

**File:** `website/app-shell/src/pages/domains/DomainPage.tsx`

```typescript
// Route: /precus/incidents
export function IncidentsPage() {
  return <DomainPage domainName="Incidents" />;
}
```

The DomainPage:
1. Loads projection from `ui_projection_lock.json`
2. Extracts Incidents domain configuration
3. Renders subdomain tabs (ACTIVE_INCIDENTS, HISTORICAL_INCIDENTS)
4. For each panel, calls `PanelContentRegistry` to get data-bound content

---

## Data Flow Sequence

```
1. TRIGGER: Run fails in worker
   └── runner.py: _update_run(status='failed')

2. INCIDENT CREATION: Automatic via engine
   └── runner.py: _create_incident_for_failure()
   └── incident_engine.py: create_incident_for_failed_run()
   └── INSERT INTO incidents (is_synthetic=true, ...)

3. API AVAILABILITY: Immediate
   └── GET /api/v1/incidents → returns new incident
   └── GET /api/v1/incidents/metrics → updated counts

4. UI REFRESH: Automatic via React Query
   └── refetchInterval triggers after 15-30s
   └── OR user returns to tab (refetchOnWindowFocus)
   └── OR component mounts (refetchOnMount)

5. PANEL RENDER: Data-driven
   └── useQuery returns fresh data
   └── OpenIncidentsSummary shows updated count
   └── OpenIncidentsList shows new incident row
```

---

## Fixes Applied (2026-01-09)

### Fix 1: Metrics Query Wrong Table

**Bug:** `/api/v1/incidents/metrics` was querying `sdsr_incidents` (dropped table)

**Fix:** Updated to query canonical `incidents` table with case-insensitive matching

```python
# Before
text(f"SELECT COUNT(*) FROM sdsr_incidents WHERE ...")

# After
text(f"SELECT COUNT(*) FROM incidents WHERE UPPER(status) NOT IN ('RESOLVED', 'CLOSED')")
```

### Fix 2: Auth Persistence

**Bug:** `user` and `isAuthenticated` not persisted to localStorage

**Fix:** Added to zustand persist config in `authStore.ts`

```typescript
partialize: (state) => ({
  token: state.token,
  user: state.user,              // ADDED
  isAuthenticated: state.isAuthenticated,  // ADDED
  // ...
}),
```

### Fix 3: Auto-Refresh Disabled

**Bug:** `refetchOnWindowFocus: false` prevented automatic data refresh

**Fix:** Enabled in `main.tsx`

```typescript
refetchOnWindowFocus: true,  // ENABLED
refetchOnMount: true,        // ADDED
staleTime: 15000,            // REDUCED from 30000
```

---

## Verification

### API Test

```bash
# Incidents list
curl -s "http://localhost:8000/api/v1/incidents?per_page=5"

# Metrics
curl -s "http://localhost:8000/api/v1/incidents/metrics"
# Returns: {"total_open":40,"total_resolved":5,"by_severity":{"critical":2,"high":23,"medium":4,"low":0}}
```

### UI Test

1. Navigate to: `https://preflight-console.agenticverz.com/precus/incidents`
2. Verify: Open Incidents Summary shows count (40)
3. Verify: Severity badges show (2 CRITICAL, 23 HIGH)
4. Hard refresh: Should stay logged in
5. Switch tabs and return: Data should auto-refresh

---

## Reference Files

| Layer | File | Purpose |
|-------|------|---------|
| L4 | `backend/app/services/incident_engine.py` | Domain logic, incident creation |
| L5 | `backend/app/worker/runner.py` | Worker integration, auto-creation |
| L6 | `backend/alembic/versions/075_consolidate_incidents_table.py` | Schema migration |
| L2 | `backend/app/api/incidents.py` | REST API endpoints |
| L1 | `website/app-shell/src/api/incidents.ts` | API client |
| L1 | `website/app-shell/src/components/panels/PanelContentRegistry.tsx` | Panel data binding |
| L1 | `website/app-shell/src/pages/domains/DomainPage.tsx` | Domain page renderer |
| L1 | `website/app-shell/src/stores/authStore.ts` | Auth persistence |
| L1 | `website/app-shell/src/main.tsx` | React Query config |
| Config | `website/app-shell/public/projection/ui_projection_lock.json` | Panel definitions |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-09 | Initial creation documenting SDSR → UI pipeline integration |
