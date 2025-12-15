# AOS Console Deployment & Implementation Runbook

**Version:** 1.0.0
**Created:** 2025-12-13
**Status:** Production-Ready Specification

---

## Part 1: URL Architecture — agenticverz.com

Agenticverz has three distinct layers:

1. **Marketing / Public Site**
2. **Documentation**
3. **AOS Console (Authenticated App)**

---

### 1.1 Public Site (Marketing Layer)

Everything here is public & SEO-indexable.

```
https://agenticverz.com/
https://agenticverz.com/agents
https://agenticverz.com/skills
https://agenticverz.com/aos
https://agenticverz.com/pricing
https://agenticverz.com/contact
https://agenticverz.com/about
```

#### AOS Product Landing

```
https://agenticverz.com/aos
https://agenticverz.com/aos/features
https://agenticverz.com/aos/architecture
https://agenticverz.com/aos/use-cases
```

---

### 1.2 Documentation Layer (Versioned)

Docs MUST be versioned to avoid breaking references.

```
https://agenticverz.com/docs/
https://agenticverz.com/docs/aos/latest
https://agenticverz.com/docs/aos/v1.0
https://agenticverz.com/docs/aos/v1.1
```

#### Key Documentation Endpoints

```
https://agenticverz.com/docs/aos/latest/overview
https://agenticverz.com/docs/aos/latest/agents
https://agenticverz.com/docs/aos/latest/jobs
https://agenticverz.com/docs/aos/latest/blackboard
https://agenticverz.com/docs/aos/latest/messaging
https://agenticverz.com/docs/aos/latest/credits
https://agenticverz.com/docs/aos/latest/audit
https://agenticverz.com/docs/aos/latest/api
```

---

### 1.3 AOS Console (Authenticated App)

This is the M13 UI console — the fully interactive control plane.

**Base URL:**
```
https://agenticverz.com/console
```

Everything in the console is a SPA (React), so further sections are client-side routes:

```
/console/dashboard
/console/agents
/console/jobs
/console/jobs/simulator
/console/jobs/runner/:jobId
/console/blackboard
/console/messaging
/console/credits
/console/audit
/console/metrics
/console/settings
```

#### Auth Endpoints (Frontend Routes)

```
/console/login
/console/logout
/console/register   (optional)
/console/forgot-password
```

#### API Endpoints (Backend)

```
/api/v1/agents
/api/v1/jobs
/api/v1/blackboard
/api/v1/messages
/api/v1/audit
/api/v1/credits
/api/v1/runtime
/api/v1/metrics
```

---

### 1.4 Static Assets & CDN

```
https://cdn.agenticverz.com/assets/*
https://cdn.agenticverz.com/ui/*
```

SDK Website (future):
```
https://sdk.agenticverz.com/
```

---

### 1.5 Admin Console (Internal Only)

Keep separate from customer console:

```
https://agenticverz.com/admin
```

---

### 1.6 URL Decision Matrix

| Layer          | URL            | Auth | SEO |
|----------------|----------------|------|-----|
| Marketing site | `/`            | No   | Yes |
| Documentation  | `/docs/...`    | No   | Yes |
| AOS Console    | `/console/...` | Yes  | No  |
| Admin platform | `/admin/...`   | Yes  | No  |

**This architecture is scalable for 5+ years.**

---

## Part 2: Developer Implementation Runbook

A ground-level runbook telling developers exactly how to build and deploy the console.

---

### Phase 0: Repo Setup

#### Option A: Dedicated Repo
```
agenticverz-aos-console/
```

#### Option B: Monorepo
```
apps/frontend-agenticverz-console
```

---

### Phase 1: Tech Stack Setup (1 Day)

#### 1. Initialize Vite + React + TypeScript

```bash
npm create vite@latest console --template react-ts
cd console
```

#### 2. Install Dependencies

```bash
# Core
npm i zustand react-router-dom @tanstack/react-query axios

# Styling
npm i tailwindcss postcss autoprefixer

# UI Components
npm i @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm i @radix-ui/react-tabs @radix-ui/react-tooltip
npm i lucide-react clsx

# Charts & Data
npm i recharts dayjs

# Code Editor (for JSON viewing)
npm i @monaco-editor/react
```

#### 3. Setup Tailwind

```bash
npx tailwindcss init -p
```

Add AOS design tokens to `tailwind.config.js`.

#### 4. Create Environment Files

`.env.development`:
```
VITE_API_BASE=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

`.env.production`:
```
VITE_API_BASE=https://agenticverz.com/api/v1
VITE_WS_URL=wss://agenticverz.com/ws
```

---

### Phase 2: Routing Setup (0.5 Day)

Create route structure:

```typescript
// src/routes/index.tsx
const routes = [
  { path: '/console/login', element: <LoginPage /> },
  { path: '/console/forgot-password', element: <ForgotPasswordPage /> },
  {
    path: '/console',
    element: <ProtectedRoute><AppLayout /></ProtectedRoute>,
    children: [
      { index: true, element: <Navigate to="dashboard" /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'agents', element: <AgentsPage /> },
      { path: 'jobs', element: <JobsLayout />, children: [
        { index: true, element: <Navigate to="simulator" /> },
        { path: 'simulator', element: <JobSimulatorPage /> },
        { path: 'runner/:jobId', element: <JobRunnerPage /> },
        { path: 'history', element: <JobHistoryPage /> },
      ]},
      { path: 'blackboard', element: <BlackboardPage /> },
      { path: 'messaging', element: <MessagingPage /> },
      { path: 'credits', element: <CreditsPage /> },
      { path: 'audit', element: <AuditPage /> },
      { path: 'metrics', element: <MetricsPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
];
```

---

### Phase 3: API Client Layer (1-1.5 Days)

Create folder structure:

```
src/api/
├── client.ts          # Axios instance with interceptors
├── agents.ts          # Agent CRUD operations
├── jobs.ts            # Job creation, simulation, management
├── blackboard.ts      # Key-value operations
├── messaging.ts       # Message send/receive
├── credits.ts         # Balance, ledger, topup
├── audit.ts           # Invoke audit queries
├── metrics.ts         # Prometheus proxy
└── types.ts           # Shared response types
```

SSE/WebSocket handlers:

```
src/lib/
├── sse.ts             # SSE connection manager
├── websocket.ts       # WebSocket connection manager
└── events.ts          # Event type definitions
```

---

### Phase 4: State Stores (1 Day)

Use Zustand for global state:

```
src/stores/
├── authStore.ts       # Token, user, login/logout
├── uiStore.ts         # Sidebar, modals, theme
├── tenantStore.ts     # Active tenant selection
├── notificationStore.ts # Toast queue
└── realtimeStore.ts   # Connection status
```

---

### Phase 5: Page-by-Page Implementation (5 Days)

| Day | Pages | Components |
|-----|-------|------------|
| 1 | Dashboard | MetricsRow, ActiveJobsTable, HealthPanel, ActivityFeed |
| 2 | Agents Console | AgentsTable, AgentDetailDrawer, RegisterModal |
| 3 | Job Simulator + Runner | ConfigPanel, SimulationResults, LiveFeed, ProgressBar |
| 4 | Blackboard + Messaging | KeyValueTable, MessageFlowGraph, LatencyStats |
| 5 | Credits + Audit + Metrics | LedgerTable, InvokeAuditTable, Charts |

---

### Phase 6: Styling & Design System (1-2 Days)

Apply from UI-DESIGN-SYSTEM.md:

- Typography scale (Inter + JetBrains Mono)
- Color tokens (Primary, Secondary, Semantic)
- Card surfaces with shadows
- Button variants (primary, secondary, ghost, danger)
- Dark mode toggle with CSS custom properties

---

### Phase 7: Error Handling + Observability (1 Day)

Implement:

- Global error boundary with fallback UI
- Toast notifications (success, error, warning, info)
- SSE/WebSocket disconnect warning banner
- Retry logic with exponential backoff
- Request/response logging in development

---

### Phase 8: Build & Deploy (0.5-1 Day)

#### 1. Build Production Bundle

```bash
npm run build
```

#### 2. Upload to Server

```bash
rsync -avz dist/ root@server:/opt/agenticverz/apps/console/dist/
```

#### 3. Apache Configuration

```apache
<VirtualHost *:443>
  ServerName agenticverz.com

  # Marketing site
  DocumentRoot /opt/agenticverz/apps/site/dist

  # Console SPA
  Alias /console /opt/agenticverz/apps/console/dist
  <Directory /opt/agenticverz/apps/console/dist>
    Require all granted
    FallbackResource /console/index.html
  </Directory>

  # API Proxy
  ProxyPass /api/v1 http://127.0.0.1:8000/api/v1
  ProxyPassReverse /api/v1 http://127.0.0.1:8000/api/v1

  # WebSocket Proxy
  ProxyPass /ws ws://127.0.0.1:8000/ws
  ProxyPassReverse /ws ws://127.0.0.1:8000/ws

  # SSL
  SSLEngine on
  SSLCertificateFile /etc/letsencrypt/live/agenticverz.com/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/agenticverz.com/privkey.pem
</VirtualHost>
```

#### 4. Reload Apache

```bash
systemctl reload apache2
```

---

### Phase 9: Production Readiness Checklist

- [ ] SSE stable under high load (100+ concurrent connections)
- [ ] Dark mode renders correctly on all pages
- [ ] Navigation stable (no flash, no 404s)
- [ ] All pages handle empty states gracefully
- [ ] All pages handle error states with retry
- [ ] No localhost references in production build
- [ ] No unused components or dead code
- [ ] Bundle size < 500KB gzipped
- [ ] Lighthouse score > 90
- [ ] Smoke test: 10 simulated jobs, 50 agents

---

### Phase 10: Optional Enhancements

- Role-based access control (RBAC)
- Console activity log
- CSV export for job timelines and ledger
- Webhook tester UI
- Live agent topology map (D3.js)
- Keyboard shortcuts (Cmd+K command palette)

---

## Timeline Summary

| Phase | Duration | Description |
|-------|----------|-------------|
| 0 | 0.5 day | Repo setup |
| 1 | 1 day | Tech stack setup |
| 2 | 0.5 day | Routing setup |
| 3 | 1.5 days | API client layer |
| 4 | 1 day | State stores |
| 5 | 5 days | Page implementation |
| 6 | 2 days | Design system |
| 7 | 1 day | Error handling |
| 8 | 1 day | Build & deploy |
| 9 | 0.5 day | Checklist verification |
| **Total** | **~14 days** | Full implementation |

---

## Related Documents

- `wireframes/AOS-CONSOLE-WIREFRAMES.md` - Visual layouts
- `components/REACT-COMPONENT-TREE.md` - Component hierarchy
- `components/API-UI-MAPPING.md` - API integration reference
- `components/EVENT-MODEL-DEFINITIONS.md` - SSE/WebSocket events
- `design-system/UI-DESIGN-SYSTEM.md` - Design tokens
- `landing/WEBSITE-LANDING-STRUCTURE.md` - Marketing site

---

## Document Revision

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial runbook from product owner |
