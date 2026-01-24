# P1.1-3.1 Founder Console Boundary Specification

**Generated:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Objective

Prevent customers from stumbling into founder surfaces through:
1. URL manipulation
2. Browser history
3. Link discovery
4. API enumeration

---

## Target Architecture

### Domain Separation (Future)

| Console | Domain | Audience |
|---------|--------|----------|
| Customer Console | console.agenticverz.com | Customer |
| Founder Console | fops.agenticverz.com | Founder |
| Ops Console | ops.agenticverz.com | Operator |

### Path Separation (Current)

Until domain separation is implemented, path-based separation:

| Console | Path Prefix | Auth Requirement |
|---------|-------------|------------------|
| Customer Console | `/guard/*` | Customer audience token |
| Founder Console | `/fops/*` | Founder audience token + superuser |
| Ops Console | `/ops/*` | Operator/Founder token |

---

## Route Namespace Migration

### Frontend Routes

| Current Route | Target Route | Page |
|---------------|--------------|------|
| `/ops` | `/fops/ops` | OpsConsoleEntry |
| `/ops/*` | `/fops/ops/*` | OpsConsoleEntry |
| `/traces` | `/fops/traces` | TracesPage |
| `/traces/:runId` | `/fops/traces/:runId` | TraceDetailPage |
| `/workers` | `/fops/workers` | WorkerStudioHomePage |
| `/workers/console` | `/fops/workers/console` | WorkerExecutionConsolePage |
| `/recovery` | `/fops/recovery` | RecoveryPage |
| `/sba` | `/fops/sba` | SBAInspectorPage |
| `/integration` | `/fops/integration` | IntegrationDashboard |
| `/integration/loop/:id` | `/fops/integration/loop/:id` | LoopStatusPage |
| `/fdr/timeline` | `/fops/fdr/timeline` | FounderTimelinePage |
| `/fdr/controls` | `/fops/fdr/controls` | FounderControlsPage |
| `/fdr/replay` | `/fops/fdr/replay` | ReplayIndexPage |
| `/fdr/replay/:id` | `/fops/fdr/replay/:id` | ReplaySliceViewer |
| `/fdr/scenarios` | `/fops/fdr/scenarios` | ScenarioBuilderPage |
| `/fdr/explorer` | `/fops/fdr/explorer` | FounderExplorerPage |

### Backend API Routes

| Current Prefix | Target Prefix | API File |
|----------------|---------------|----------|
| `/ops/*` | `/fops/ops/*` | ops.py |
| `/ops/cost/*` | `/fops/ops/cost/*` | cost_ops.py |
| `/ops/actions/*` | `/fops/ops/actions/*` | founder_actions.py |
| `/fdr/timeline/*` | `/fops/fdr/timeline/*` | founder_timeline.py |
| `/explorer/*` | `/fops/explorer/*` | founder_explorer.py |
| `/replay/*` | `/fops/replay/*` | replay.py |
| `/scenarios/*` | `/fops/scenarios/*` | scenarios.py |
| `/traces/*` | `/fops/traces/*` | traces.py |
| `/integration/*` | `/fops/integration/*` | integration.py |

---

## Route Guard Requirements

### 1. Auth Audience Check

Every `/fops/*` route must verify:

```typescript
// Frontend guard
function FopsRoute({ children }) {
  const { user, audience } = useAuth();

  if (audience !== 'founder' && audience !== 'operator') {
    return <Navigate to="/guard" replace />;
  }

  if (!user?.is_superuser) {
    return <Navigate to="/guard" replace />;
  }

  return children;
}
```

### 2. Backend RBAC

Every `/fops/*` API must require:

```python
# Backend dependency
async def require_founder_access(
    actor: ActorContext = Depends(get_actor_context)
) -> ActorContext:
    if actor.audience not in ("founder", "operator"):
        raise HTTPException(status_code=403, detail="Founder access required")
    if not actor.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    return actor
```

### 3. OpenAPI Exclusion

Founder routes must not appear in customer OpenAPI spec:

```python
# Tag founder routes with hidden=True
router = APIRouter(
    prefix="/fops/ops",
    tags=["fops-ops"],
    include_in_schema=False  # Hide from public OpenAPI
)
```

---

## AppLayout Isolation

### Current Problem

AppLayout is shared between customer and founder pages. This means:
- Same sidebar navigation
- Same header
- Same route catch-all

### Solution: Separate Layouts

```
/guard/*     → CustomerLayout (AIConsoleApp)
/fops/*      → FounderLayout (FOPSConsoleApp)
/ops/*       → OpsLayout (OpsConsoleEntry)
/onboarding/* → OnboardingLayout
```

Each layout:
- Has its own sidebar navigation
- Has its own header
- Does NOT share routes with other layouts
- Does NOT import pages from other consoles

### Route Structure After Migration

```typescript
// routes/index.tsx
<Routes>
  {/* Public */}
  <Route path="/login" element={<LoginPage />} />

  {/* Onboarding */}
  <Route path="/onboarding/*" element={<OnboardingLayout />}>
    ...
  </Route>

  {/* Customer Console - console.agenticverz.com */}
  <Route path="/guard/*" element={<CustomerLayout />}>
    <Route path="overview" element={<OverviewPage />} />
    <Route path="activity" element={<ActivityPage />} />
    <Route path="incidents" element={<IncidentsPage />} />
    ...
  </Route>

  {/* Founder Console - fops.agenticverz.com */}
  <Route path="/fops/*" element={<FounderRoute><FounderLayout /></FounderRoute>}>
    <Route path="ops" element={<OpsConsoleEntry />} />
    <Route path="traces" element={<TracesPage />} />
    <Route path="workers" element={<WorkerStudioHomePage />} />
    ...
  </Route>

  {/* Catch-all: Customer console */}
  <Route path="*" element={<Navigate to="/guard" replace />} />
</Routes>
```

---

## Discovery Prevention

### 1. No Cross-Console Links

Customer Console must NOT contain:
- Links to `/fops/*`
- Links to `/ops/*`
- Links to `/fdr/*`
- Links to `/traces/*`
- Links to `/workers/*`

### 2. No Shared Navigation

Sidebar items must be console-specific:

```typescript
// CustomerLayout sidebar
const customerNavItems = [
  { path: '/guard/overview', label: 'Overview' },
  { path: '/guard/activity', label: 'Activity' },
  { path: '/guard/incidents', label: 'Incidents' },
  { path: '/guard/policies', label: 'Policies' },
  { path: '/guard/logs', label: 'Logs' },
];

// FounderLayout sidebar
const founderNavItems = [
  { path: '/fops/ops', label: 'Operations' },
  { path: '/fops/traces', label: 'Traces' },
  { path: '/fops/workers', label: 'Workers' },
  { path: '/fops/fdr/timeline', label: 'Timeline' },
  { path: '/fops/fdr/explorer', label: 'Explorer' },
];
```

### 3. API Route Hiding

Customer-visible APIs must not expose founder endpoints:

```yaml
# OpenAPI spec for console.agenticverz.com
paths:
  /guard/overview:
    get: ...
  /guard/incidents:
    get: ...
  # NO /fops/* paths
  # NO /ops/* paths
  # NO /fdr/* paths
```

### 4. 404 for Wrong Audience

If a customer hits `/fops/*`:
- Do NOT redirect to `/guard`
- Return 404 (not 403)
- Reveal nothing about the route's existence

```typescript
// Route not found for wrong audience
if (!hasAccess && isFopsRoute) {
  return <NotFound />; // Generic 404, not "Access Denied"
}
```

---

## Verification Checklist

| Check | Status |
|-------|--------|
| All founder routes under `/fops/*` | Pending |
| All founder APIs under `/fops/*` | Pending |
| FounderRoute guard implemented | Pending |
| Backend RBAC for `/fops/*` | Pending |
| OpenAPI excludes `/fops/*` for customers | Pending |
| AppLayout split into console-specific layouts | Pending |
| No cross-console links exist | Pending |
| 404 returned for wrong audience | Pending |

---

## Implementation Order

1. **Backend First:** Migrate API prefixes to `/fops/*`
2. **RBAC:** Add founder access requirements
3. **Frontend Routes:** Migrate routes to `/fops/*`
4. **Frontend Guards:** Add FounderRoute wrapper
5. **Layout Split:** Separate AppLayout per console
6. **Discovery:** Audit and remove cross-console links
7. **OpenAPI:** Configure per-audience specs

---

## Acceptance Criteria

- [ ] All 17 founder pages accessible only via `/fops/*`
- [ ] All 9 founder APIs accessible only via `/fops/*`
- [ ] Customer token cannot access `/fops/*` routes
- [ ] Customer OpenAPI does not expose `/fops/*` paths
- [ ] Browser history at customer console shows no `/fops/*` URLs
- [ ] Catch-all route returns 404 (not redirect) for `/fops/*` without auth

---

## Related Documents

- P1_1_FRONTEND_LEGACY_INVENTORY.md - Frontend route inventory
- P1_1_BACKEND_LEGACY_SUPPORT.md - Backend API inventory
- P1_1_LEGACY_DECISIONS.md - Classification decisions
- RBAC_AUTHORITY_SEPARATION_DESIGN.md - Auth architecture
