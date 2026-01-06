# P1.2-2.2 Route Classifications

**Generated:** 2026-01-06
**Phase:** Phase 1.2 - Authority & Boundary Hardening
**Reference:** PIN-318

---

## Objective

Explicitly classify all routes by audience and role requirements.

---

## Frontend Route Classifications

### Customer Routes (`/guard/*`) - aud="console"

| Route | Component | Audience | Roles | Guard |
|-------|-----------|----------|-------|-------|
| `/guard` | AIConsoleApp | console | ALL | ProtectedRoute |
| `/guard/overview` | OverviewPage | console | ALL | ProtectedRoute |
| `/guard/activity` | ActivityPage | console | ALL | ProtectedRoute |
| `/guard/incidents` | IncidentsPage | console | ALL | ProtectedRoute |
| `/guard/incidents/:id` | IncidentDetailPage | console | ALL | ProtectedRoute |
| `/guard/policies` | PoliciesPage | console | ALL | ProtectedRoute |
| `/guard/logs` | LogsPage | console | ALL | ProtectedRoute |
| `/guard/integrations` | IntegrationsPage | console | ALL | ProtectedRoute |
| `/guard/keys` | KeysPage | console | OWNER, ADMIN | ProtectedRoute |
| `/guard/settings` | SettingsPage | console | OWNER, ADMIN | ProtectedRoute |
| `/guard/account` | AccountPage | console | OWNER, ADMIN | ProtectedRoute |

### Founder Routes - aud="fops"

| Route | Component | Audience | Roles | Guard | PIN-318 Status |
|-------|-----------|----------|-------|-------|----------------|
| `/traces` | TracesPage | fops | ALL | FounderRoute | HARDENED |
| `/traces/:runId` | TraceDetailPage | fops | ALL | FounderRoute | HARDENED |
| `/workers` | WorkerStudioHomePage | fops | ALL | FounderRoute | HARDENED |
| `/workers/console` | WorkerExecutionConsolePage | fops | ALL | FounderRoute | HARDENED |
| `/recovery` | RecoveryPage | fops | ALL | FounderRoute | HARDENED |
| `/integration` | IntegrationDashboard | fops | ALL | FounderRoute | HARDENED |
| `/integration/loop/:id` | LoopStatusPage | fops | ALL | FounderRoute | HARDENED |
| `/founder/timeline` | FounderTimelinePage | fops | ALL | FounderRoute | HARDENED |
| `/founder/controls` | FounderControlsPage | fops | FOUNDER | FounderRoute | HARDENED |
| `/founder/replay` | ReplayIndexPage | fops | ALL | FounderRoute | HARDENED |
| `/founder/replay/:id` | ReplaySliceViewer | fops | ALL | FounderRoute | HARDENED |
| `/founder/scenarios` | ScenarioBuilderPage | fops | ALL | FounderRoute | HARDENED |
| `/founder/explorer` | FounderExplorerPage | fops | ALL | FounderRoute | HARDENED |
| `/sba` | SBAInspectorPage | fops | ALL | FounderRoute | HARDENED |
| `/credits` | CreditsPage | fops | ALL | FounderRoute | HARDENED |

### Ops Routes (`/ops/*`) - aud="fops"

| Route | Component | Audience | Roles | Guard |
|-------|-----------|----------|-------|-------|
| `/ops` | OpsConsoleEntry | fops | ALL | FounderRoute |
| `/ops/*` | OpsConsoleEntry | fops | ALL | FounderRoute |

### Auth/Onboarding Routes - Public/Mixed

| Route | Component | Audience | Guard |
|-------|-----------|----------|-------|
| `/login` | LoginPage | public | None |
| `/onboarding/*` | OnboardingRoute | console | OnboardingRoute |
| `/` | Redirect | public | None |
| `/*` | Redirect | public | None (catch-all) |

---

## Backend API Classifications

### Customer APIs (`/api/v1/guard/*`) - aud="console"

| Endpoint | File | Auth | Tenant Isolation |
|----------|------|------|------------------|
| `/api/v1/guard/*` | guard/*.py | verify_console_token | YES |

### Founder APIs - aud="fops"

| Endpoint | File | Auth | PIN-318 Status |
|----------|------|------|----------------|
| `/api/v1/founder/timeline/*` | founder_timeline.py | verify_fops_token | HARDENED |
| `/api/v1/scenarios/*` | scenarios.py | verify_fops_token | HARDENED |
| `/api/v1/integration/*` | integration.py | verify_fops_token | HARDENED |
| `/api/v1/traces/*` | traces.py | JWT (tenant-isolated) | OK |
| `/api/v1/replay/*` | replay.py | require_replay_read | OK |
| `/api/v1/ops/*` | ops.py | verify_fops_token | HARDENED |
| `/api/v1/ops/cost/*` | cost_ops.py | verify_fops_token | OK |
| `/api/v1/ops/actions/*` | founder_actions.py | verify_fops_token | OK |
| `/api/v1/explorer/*` | founder_explorer.py | verify_fops_token | HARDENED |
| `/api/v1/recovery/*` | recovery.py | verify_fops_token | HARDENED |
| `/api/v1/workers/*` | workers.py | verify_api_key | OK (SDK auth) |

---

## Route Guard Summary

### FounderRoute (PIN-318)

**File:** `routes/FounderRoute.tsx`

**Checks:**
1. `isAuthenticated` - Must be logged in
2. `onboardingComplete` - Must have completed onboarding
3. `audience === 'fops' || isFounder` - Must have founder token
4. `allowedRoles` (optional) - Must have required founder role

**Behavior:**
- Missing auth → redirect to `/login`
- Missing onboarding → redirect to `/onboarding/connect`
- Wrong audience → redirect to `/guard` (prevents discovery)
- Wrong role → redirect to `/ops`

### ProtectedRoute

**File:** `routes/ProtectedRoute.tsx`

**Checks:**
1. `isAuthenticated` - Must be logged in
2. `onboardingComplete` - Must have completed onboarding

**Note:** ProtectedRoute does not check audience. Use FounderRoute for founder-only pages.

---

## Acceptance Criteria

- [x] All routes classified by audience
- [x] Founder routes use FounderRoute guard
- [x] Customer routes use ProtectedRoute guard
- [x] Backend APIs have matching auth middleware
- [x] No implicit trust paths remain

---

## Related Documents

- `routes/index.tsx` - Route configuration
- `routes/FounderRoute.tsx` - Founder guard (PIN-318)
- `P1_2_AUTHORITY_MODEL.md` - Authority model
- `P1_2_BACKEND_AUTH_AUDIT.md` - Backend auth audit
