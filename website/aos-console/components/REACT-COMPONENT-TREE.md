# AOS Console React Component Tree

**Version:** 1.0.0
**Framework:** React 18 + TypeScript + Vite
**State:** Zustand + React Query
**Routing:** React Router v6
**Styling:** Tailwind CSS + CSS Modules
**Created:** 2025-12-13

---

## Folder Structure

```
aos-console/
├── public/
│   ├── favicon.ico
│   ├── logo.svg
│   └── manifest.json
├── src/
│   ├── main.tsx                    # App entry point
│   ├── App.tsx                     # Root component with providers
│   ├── vite-env.d.ts              # Vite type declarations
│   │
│   ├── api/                        # API layer
│   │   ├── client.ts              # Axios/fetch client config
│   │   ├── endpoints.ts           # API endpoint constants
│   │   ├── agents.ts              # Agents API functions
│   │   ├── jobs.ts                # Jobs API functions
│   │   ├── blackboard.ts          # Blackboard API functions
│   │   ├── messages.ts            # Messages API functions
│   │   ├── credits.ts             # Credits API functions
│   │   ├── metrics.ts             # Metrics API functions
│   │   ├── auth.ts                # Auth API functions
│   │   └── types.ts               # API response types
│   │
│   ├── components/                 # Reusable components
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx      # Main app shell
│   │   │   ├── Header.tsx         # Top navigation bar
│   │   │   ├── Sidebar.tsx        # Left navigation
│   │   │   ├── StatusBar.tsx      # Bottom status bar
│   │   │   ├── PageHeader.tsx     # Page title + actions
│   │   │   └── ContentArea.tsx    # Main content wrapper
│   │   │
│   │   ├── navigation/
│   │   │   ├── NavItem.tsx        # Single nav item
│   │   │   ├── NavGroup.tsx       # Collapsible nav group
│   │   │   ├── NavLinks.tsx       # Horizontal nav links
│   │   │   ├── UserMenu.tsx       # User dropdown menu
│   │   │   ├── NotificationBell.tsx
│   │   │   ├── CreditBadge.tsx
│   │   │   └── TenantSelector.tsx
│   │   │
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── TextArea.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Checkbox.tsx
│   │   │   ├── Radio.tsx
│   │   │   ├── Toggle.tsx
│   │   │   ├── Slider.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Avatar.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Drawer.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── Popover.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── TabGroup.tsx
│   │   │   ├── Divider.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorState.tsx
│   │   │   └── LoadingState.tsx
│   │   │
│   │   ├── data-display/
│   │   │   ├── DataTable.tsx      # Generic data table
│   │   │   ├── Pagination.tsx
│   │   │   ├── SortHeader.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── ProgressRing.tsx
│   │   │   ├── StatusIndicator.tsx
│   │   │   ├── TimeAgo.tsx
│   │   │   ├── Duration.tsx
│   │   │   ├── CreditAmount.tsx
│   │   │   └── JsonViewer.tsx
│   │   │
│   │   ├── charts/
│   │   │   ├── LineChart.tsx
│   │   │   ├── AreaChart.tsx
│   │   │   ├── BarChart.tsx
│   │   │   ├── PieChart.tsx
│   │   │   ├── DonutChart.tsx
│   │   │   ├── Histogram.tsx
│   │   │   ├── SparkLine.tsx
│   │   │   ├── Gauge.tsx
│   │   │   └── ChartTooltip.tsx
│   │   │
│   │   ├── forms/
│   │   │   ├── Form.tsx
│   │   │   ├── FormField.tsx
│   │   │   ├── FormLabel.tsx
│   │   │   ├── FormError.tsx
│   │   │   ├── JsonEditor.tsx
│   │   │   ├── CodeEditor.tsx
│   │   │   └── FileUpload.tsx
│   │   │
│   │   └── feedback/
│   │       ├── Toast.tsx
│   │       ├── ToastContainer.tsx
│   │       ├── Alert.tsx
│   │       ├── Banner.tsx
│   │       ├── ConfirmDialog.tsx
│   │       └── NotificationToast.tsx
│   │
│   ├── features/                   # Feature-specific components
│   │   ├── dashboard/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── WelcomeBanner.tsx
│   │   │   ├── MetricsRow.tsx
│   │   │   ├── ActiveJobsTable.tsx
│   │   │   ├── SystemHealthPanel.tsx
│   │   │   ├── ActivityFeed.tsx
│   │   │   ├── CreditUsageChart.tsx
│   │   │   └── QuickActions.tsx
│   │   │
│   │   ├── agents/
│   │   │   ├── AgentsPage.tsx
│   │   │   ├── AgentsTable.tsx
│   │   │   ├── AgentRow.tsx
│   │   │   ├── AgentDetailDrawer.tsx
│   │   │   ├── AgentCapabilities.tsx
│   │   │   ├── AgentStatusBadge.tsx
│   │   │   ├── AgentHeartbeatIndicator.tsx
│   │   │   ├── RegisterAgentModal.tsx
│   │   │   ├── BulkActionBar.tsx
│   │   │   └── AgentFilters.tsx
│   │   │
│   │   ├── jobs/
│   │   │   ├── simulator/
│   │   │   │   ├── JobSimulatorPage.tsx
│   │   │   │   ├── ConfigPanel.tsx
│   │   │   │   ├── AgentSelect.tsx
│   │   │   │   ├── ItemsEditor.tsx
│   │   │   │   ├── ParallelismSlider.tsx
│   │   │   │   ├── SimulationResults.tsx
│   │   │   │   ├── FeasibilityBadge.tsx
│   │   │   │   ├── CostBreakdown.tsx
│   │   │   │   ├── TimeEstimate.tsx
│   │   │   │   ├── BudgetCheck.tsx
│   │   │   │   ├── WarningsList.tsx
│   │   │   │   └── RisksList.tsx
│   │   │   │
│   │   │   ├── runner/
│   │   │   │   ├── JobRunnerPage.tsx
│   │   │   │   ├── JobConfigForm.tsx
│   │   │   │   ├── ActiveJobCard.tsx
│   │   │   │   ├── JobProgressBar.tsx
│   │   │   │   ├── ItemStatusSummary.tsx
│   │   │   │   ├── LiveFeed.tsx
│   │   │   │   ├── LiveFeedItem.tsx
│   │   │   │   ├── JobDetailModal.tsx
│   │   │   │   ├── ItemsTable.tsx
│   │   │   │   └── CancelJobDialog.tsx
│   │   │   │
│   │   │   ├── history/
│   │   │   │   ├── JobHistoryPage.tsx
│   │   │   │   ├── JobHistoryTable.tsx
│   │   │   │   ├── JobHistoryFilters.tsx
│   │   │   │   └── JobExportButton.tsx
│   │   │   │
│   │   │   └── shared/
│   │   │       ├── JobStatusBadge.tsx
│   │   │       ├── JobSummaryCard.tsx
│   │   │       └── JobTimeline.tsx
│   │   │
│   │   ├── blackboard/
│   │   │   ├── BlackboardPage.tsx
│   │   │   ├── KeyValueTable.tsx
│   │   │   ├── KeyRow.tsx
│   │   │   ├── KeyDetailPanel.tsx
│   │   │   ├── KeyMetadata.tsx
│   │   │   ├── ValueEditor.tsx
│   │   │   ├── KeyHistory.tsx
│   │   │   ├── AddKeyModal.tsx
│   │   │   ├── EditKeyModal.tsx
│   │   │   ├── PatternSelect.tsx
│   │   │   ├── TtlDisplay.tsx
│   │   │   └── LockIndicator.tsx
│   │   │
│   │   ├── messages/
│   │   │   ├── MessagesPage.tsx
│   │   │   ├── MessageFilters.tsx
│   │   │   ├── LatencyStatsRow.tsx
│   │   │   ├── MessageFlowGraph.tsx
│   │   │   ├── MessagesTable.tsx
│   │   │   ├── MessageRow.tsx
│   │   │   ├── MessageDetailDrawer.tsx
│   │   │   ├── MessagePayload.tsx
│   │   │   ├── SendMessageModal.tsx
│   │   │   └── MessageStatusBadge.tsx
│   │   │
│   │   ├── credits/
│   │   │   ├── CreditsPage.tsx
│   │   │   ├── BalanceOverview.tsx
│   │   │   ├── BalanceCard.tsx
│   │   │   ├── MonthlySpendCard.tsx
│   │   │   ├── LedgerTable.tsx
│   │   │   ├── LedgerRow.tsx
│   │   │   ├── LedgerFilters.tsx
│   │   │   ├── InvokeAuditTable.tsx
│   │   │   ├── InvokeAuditRow.tsx
│   │   │   ├── InvokeDetailModal.tsx
│   │   │   ├── UsageAnalytics.tsx
│   │   │   ├── UsageChart.tsx
│   │   │   ├── SkillBreakdownPie.tsx
│   │   │   ├── JobTypeBreakdownPie.tsx
│   │   │   └── AddCreditsModal.tsx
│   │   │
│   │   ├── metrics/
│   │   │   ├── MetricsPage.tsx
│   │   │   ├── TimeRangeSelector.tsx
│   │   │   ├── HealthStatusRow.tsx
│   │   │   ├── HealthStatusCard.tsx
│   │   │   ├── JobsMetricsChart.tsx
│   │   │   ├── ThroughputGauge.tsx
│   │   │   ├── CreditFlowSummary.tsx
│   │   │   ├── InvokeLatencyHistogram.tsx
│   │   │   ├── MessageLatencyChart.tsx
│   │   │   └── MetricRefreshIndicator.tsx
│   │   │
│   │   └── auth/
│   │       ├── LoginPage.tsx
│   │       ├── LoginForm.tsx
│   │       ├── SSOButton.tsx
│   │       ├── ForgotPasswordPage.tsx
│   │       ├── ResetPasswordPage.tsx
│   │       ├── RequestAccessPage.tsx
│   │       └── AuthGuard.tsx
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useAuth.ts             # Authentication hook
│   │   ├── useUser.ts             # Current user hook
│   │   ├── useTenant.ts           # Tenant context hook
│   │   ├── useAgents.ts           # Agents data hook
│   │   ├── useAgent.ts            # Single agent hook
│   │   ├── useJobs.ts             # Jobs list hook
│   │   ├── useJob.ts              # Single job hook
│   │   ├── useJobItems.ts         # Job items hook
│   │   ├── useBlackboard.ts       # Blackboard keys hook
│   │   ├── useBlackboardKey.ts    # Single key hook
│   │   ├── useMessages.ts         # Messages hook
│   │   ├── useCredits.ts          # Credit balance hook
│   │   ├── useLedger.ts           # Ledger entries hook
│   │   ├── useInvokeAudit.ts      # Invoke audit hook
│   │   ├── useMetrics.ts          # Metrics data hook
│   │   ├── useHealthStatus.ts     # Service health hook
│   │   ├── useWebSocket.ts        # WebSocket connection hook
│   │   ├── useRealtime.ts         # Real-time updates hook
│   │   ├── usePolling.ts          # Polling hook
│   │   ├── usePagination.ts       # Pagination state hook
│   │   ├── useFilters.ts          # Filter state hook
│   │   ├── useSort.ts             # Sort state hook
│   │   ├── useDebounce.ts         # Debounce hook
│   │   ├── useThrottle.ts         # Throttle hook
│   │   ├── useLocalStorage.ts     # Local storage hook
│   │   ├── useMediaQuery.ts       # Responsive hook
│   │   ├── useClickOutside.ts     # Click outside hook
│   │   ├── useKeyboard.ts         # Keyboard shortcuts hook
│   │   ├── useToast.ts            # Toast notifications hook
│   │   ├── useConfirm.ts          # Confirm dialog hook
│   │   └── useClipboard.ts        # Clipboard hook
│   │
│   ├── stores/                     # Zustand stores
│   │   ├── authStore.ts           # Auth state
│   │   ├── userStore.ts           # User preferences
│   │   ├── tenantStore.ts         # Active tenant
│   │   ├── uiStore.ts             # UI state (sidebar, modals)
│   │   ├── notificationStore.ts   # Notifications queue
│   │   ├── toastStore.ts          # Toast messages
│   │   └── realtimeStore.ts       # Real-time connection state
│   │
│   ├── routes/                     # Route definitions
│   │   ├── index.tsx              # Route tree
│   │   ├── ProtectedRoute.tsx     # Auth guard wrapper
│   │   └── routes.ts              # Route path constants
│   │
│   ├── lib/                        # Utilities
│   │   ├── utils.ts               # General utilities
│   │   ├── formatters.ts          # Date, number formatters
│   │   ├── validators.ts          # Form validators
│   │   ├── constants.ts           # App constants
│   │   ├── websocket.ts           # WebSocket client
│   │   └── classnames.ts          # Class name helper
│   │
│   ├── types/                      # TypeScript types
│   │   ├── agent.ts
│   │   ├── job.ts
│   │   ├── item.ts
│   │   ├── message.ts
│   │   ├── blackboard.ts
│   │   ├── credit.ts
│   │   ├── metric.ts
│   │   ├── user.ts
│   │   ├── tenant.ts
│   │   └── api.ts
│   │
│   └── styles/                     # Global styles
│       ├── globals.css            # Global CSS
│       ├── variables.css          # CSS custom properties
│       └── animations.css         # Animation keyframes
│
├── .env.example                    # Environment template
├── .env.production                 # Production config
├── index.html                      # HTML entry
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

---

## Route Definitions

```typescript
// src/routes/routes.ts

export const ROUTES = {
  // Auth routes (public)
  LOGIN: '/login',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password/:token',
  REQUEST_ACCESS: '/request-access',

  // Dashboard
  DASHBOARD: '/',

  // Agents
  AGENTS: '/agents',
  AGENT_DETAIL: '/agents/:agentId',

  // Jobs
  JOBS: '/jobs',
  JOB_SIMULATOR: '/jobs/simulate',
  JOB_RUNNER: '/jobs/run',
  JOB_HISTORY: '/jobs/history',
  JOB_DETAIL: '/jobs/:jobId',

  // Blackboard
  BLACKBOARD: '/blackboard',
  BLACKBOARD_KEY: '/blackboard/:key',

  // Messages
  MESSAGES: '/messages',
  MESSAGE_DETAIL: '/messages/:messageId',

  // Credits
  CREDITS: '/credits',
  LEDGER: '/credits/ledger',
  INVOKE_AUDIT: '/credits/audit',
  USAGE_ANALYTICS: '/credits/analytics',

  // Metrics
  METRICS: '/metrics',

  // Settings (future)
  SETTINGS: '/settings',
  PROFILE: '/settings/profile',
  API_KEYS: '/settings/api-keys',
} as const;
```

```typescript
// src/routes/index.tsx

import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { AuthGuard } from '@/features/auth/AuthGuard';
import { ProtectedRoute } from './ProtectedRoute';

// Lazy load pages
const LoginPage = lazy(() => import('@/features/auth/LoginPage'));
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage'));
const AgentsPage = lazy(() => import('@/features/agents/AgentsPage'));
const JobSimulatorPage = lazy(() => import('@/features/jobs/simulator/JobSimulatorPage'));
const JobRunnerPage = lazy(() => import('@/features/jobs/runner/JobRunnerPage'));
const JobHistoryPage = lazy(() => import('@/features/jobs/history/JobHistoryPage'));
const BlackboardPage = lazy(() => import('@/features/blackboard/BlackboardPage'));
const MessagesPage = lazy(() => import('@/features/messages/MessagesPage'));
const CreditsPage = lazy(() => import('@/features/credits/CreditsPage'));
const MetricsPage = lazy(() => import('@/features/metrics/MetricsPage'));

const router = createBrowserRouter([
  // Public routes
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },

  // Protected routes
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'agents',
        element: <AgentsPage />,
      },
      {
        path: 'jobs/simulate',
        element: <JobSimulatorPage />,
      },
      {
        path: 'jobs/run',
        element: <JobRunnerPage />,
      },
      {
        path: 'jobs/history',
        element: <JobHistoryPage />,
      },
      {
        path: 'jobs/:jobId',
        element: <JobDetailPage />,
      },
      {
        path: 'blackboard',
        element: <BlackboardPage />,
      },
      {
        path: 'messages',
        element: <MessagesPage />,
      },
      {
        path: 'credits',
        element: <CreditsPage />,
      },
      {
        path: 'metrics',
        element: <MetricsPage />,
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
```

---

## Core Component Implementations

### AppLayout.tsx

```typescript
// src/components/layout/AppLayout.tsx

import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';
import { useUIStore } from '@/stores/uiStore';

export function AppLayout() {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className="app-layout">
      <Header />
      <div className="app-layout__body">
        <Sidebar collapsed={sidebarCollapsed} />
        <main className="app-layout__content">
          <Suspense fallback={<LoadingState />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
      <StatusBar />
    </div>
  );
}
```

### Header.tsx

```typescript
// src/components/layout/Header.tsx

import { Logo } from '@/components/common/Logo';
import { NavLinks } from '@/components/navigation/NavLinks';
import { NotificationBell } from '@/components/navigation/NotificationBell';
import { CreditBadge } from '@/components/navigation/CreditBadge';
import { UserMenu } from '@/components/navigation/UserMenu';
import { useCredits } from '@/hooks/useCredits';
import { useUser } from '@/hooks/useUser';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/' },
  { label: 'Agents', href: '/agents' },
  {
    label: 'Jobs',
    children: [
      { label: 'Simulator', href: '/jobs/simulate' },
      { label: 'Runner', href: '/jobs/run' },
      { label: 'History', href: '/jobs/history' },
    ]
  },
  { label: 'Blackboard', href: '/blackboard' },
  { label: 'Messages', href: '/messages' },
  { label: 'Credits', href: '/credits' },
];

export function Header() {
  const { data: credits } = useCredits();
  const { data: user } = useUser();

  return (
    <header className="header">
      <div className="header__left">
        <Logo size="small" />
        <NavLinks items={NAV_ITEMS} />
      </div>
      <div className="header__right">
        <NotificationBell />
        <CreditBadge balance={credits?.balance ?? 0} />
        <UserMenu user={user} />
      </div>
    </header>
  );
}
```

### Sidebar.tsx

```typescript
// src/components/layout/Sidebar.tsx

import { NavItem } from '@/components/navigation/NavItem';
import { NavGroup } from '@/components/navigation/NavGroup';
import { TenantSelector } from '@/components/navigation/TenantSelector';
import { useTenant } from '@/hooks/useTenant';

const NAV_ITEMS = [
  { icon: 'dashboard', label: 'Dashboard', href: '/' },
  { icon: 'agents', label: 'Agents', href: '/agents' },
  {
    icon: 'jobs',
    label: 'Jobs',
    children: [
      { label: 'Simulator', href: '/jobs/simulate' },
      { label: 'Runner', href: '/jobs/run' },
      { label: 'History', href: '/jobs/history' },
    ]
  },
  { icon: 'blackboard', label: 'Blackboard', href: '/blackboard' },
  { icon: 'messages', label: 'Messages', href: '/messages' },
  { icon: 'credits', label: 'Credits', href: '/credits' },
  { icon: 'metrics', label: 'Metrics', href: '/metrics' },
];

interface SidebarProps {
  collapsed?: boolean;
}

export function Sidebar({ collapsed = false }: SidebarProps) {
  const { tenants, currentTenant, setTenant } = useTenant();

  return (
    <aside className={cn('sidebar', { 'sidebar--collapsed': collapsed })}>
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) =>
          item.children ? (
            <NavGroup key={item.label} {...item} collapsed={collapsed} />
          ) : (
            <NavItem key={item.label} {...item} collapsed={collapsed} />
          )
        )}
      </nav>

      <div className="sidebar__footer">
        <TenantSelector
          tenants={tenants}
          current={currentTenant}
          onChange={setTenant}
          collapsed={collapsed}
        />
      </div>
    </aside>
  );
}
```

---

## Custom Hooks

### useAgents.ts

```typescript
// src/hooks/useAgents.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAgents, registerAgent, deregisterAgent } from '@/api/agents';
import type { Agent, AgentFilters } from '@/types/agent';

export function useAgents(filters?: AgentFilters) {
  return useQuery({
    queryKey: ['agents', filters],
    queryFn: () => getAgents(filters),
    refetchInterval: 30000, // Refresh every 30s
  });
}

export function useRegisterAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: registerAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useDeregisterAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deregisterAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
```

### useJob.ts

```typescript
// src/hooks/useJob.ts

import { useQuery } from '@tanstack/react-query';
import { getJob, getJobItems } from '@/api/jobs';
import { useWebSocket } from './useWebSocket';

export function useJob(jobId: string) {
  const query = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId),
    refetchInterval: (data) =>
      data?.status === 'running' ? 5000 : false,
  });

  // Subscribe to real-time updates
  useWebSocket(`jobs/${jobId}`, {
    onMessage: (event) => {
      if (event.type === 'job_update') {
        query.refetch();
      }
    },
    enabled: query.data?.status === 'running',
  });

  return query;
}

export function useJobItems(jobId: string) {
  return useQuery({
    queryKey: ['job-items', jobId],
    queryFn: () => getJobItems(jobId),
  });
}
```

### useBlackboard.ts

```typescript
// src/hooks/useBlackboard.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getBlackboardKeys,
  getBlackboardKey,
  setBlackboardKey,
  incrementBlackboardKey,
  deleteBlackboardKey,
} from '@/api/blackboard';

export function useBlackboard(pattern?: string, page = 1, limit = 25) {
  return useQuery({
    queryKey: ['blackboard', pattern, page, limit],
    queryFn: () => getBlackboardKeys({ pattern, page, limit }),
  });
}

export function useBlackboardKey(key: string) {
  return useQuery({
    queryKey: ['blackboard-key', key],
    queryFn: () => getBlackboardKey(key),
    enabled: !!key,
  });
}

export function useSetBlackboardKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ key, value, ttl }: { key: string; value: any; ttl?: number }) =>
      setBlackboardKey(key, value, ttl),
    onSuccess: (_, { key }) => {
      queryClient.invalidateQueries({ queryKey: ['blackboard'] });
      queryClient.invalidateQueries({ queryKey: ['blackboard-key', key] });
    },
  });
}

export function useIncrementBlackboardKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ key, amount }: { key: string; amount: number }) =>
      incrementBlackboardKey(key, amount),
    onSuccess: (_, { key }) => {
      queryClient.invalidateQueries({ queryKey: ['blackboard-key', key] });
    },
  });
}
```

### useWebSocket.ts

```typescript
// src/hooks/useWebSocket.ts

import { useEffect, useRef, useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';

interface WebSocketOptions {
  onMessage?: (event: MessageEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  enabled?: boolean;
}

export function useWebSocket(path: string, options: WebSocketOptions = {}) {
  const { onMessage, onOpen, onClose, onError, enabled = true } = options;
  const wsRef = useRef<WebSocket | null>(null);
  const { token } = useAuthStore();

  const connect = useCallback(() => {
    if (!enabled) return;

    const ws = new WebSocket(
      `wss://agenticverz.com/ws/${path}?token=${token}`
    );

    ws.onopen = () => onOpen?.();
    ws.onclose = () => onClose?.();
    ws.onerror = (e) => onError?.(e);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      onMessage?.(data);
    };

    wsRef.current = ws;
  }, [path, token, enabled, onMessage, onOpen, onClose, onError]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const send = useCallback((data: any) => {
    wsRef.current?.send(JSON.stringify(data));
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { send, disconnect, reconnect: connect };
}
```

---

## Zustand Stores

### authStore.ts

```typescript
// src/stores/authStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setTokens: (token: string, refreshToken: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      isAuthenticated: false,

      setTokens: (token, refreshToken) => set({
        token,
        refreshToken,
        isAuthenticated: true,
      }),

      clearAuth: () => set({
        token: null,
        refreshToken: null,
        isAuthenticated: false,
      }),
    }),
    {
      name: 'aos-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
```

### uiStore.ts

```typescript
// src/stores/uiStore.ts

import { create } from 'zustand';

interface UIState {
  sidebarCollapsed: boolean;
  activeModal: string | null;
  activeDrawer: string | null;

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
  openDrawer: (drawerId: string) => void;
  closeDrawer: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  activeModal: null,
  activeDrawer: null,

  toggleSidebar: () => set((state) => ({
    sidebarCollapsed: !state.sidebarCollapsed
  })),

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  openModal: (modalId) => set({ activeModal: modalId }),
  closeModal: () => set({ activeModal: null }),

  openDrawer: (drawerId) => set({ activeDrawer: drawerId }),
  closeDrawer: () => set({ activeDrawer: null }),
}));
```

### tenantStore.ts

```typescript
// src/stores/tenantStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Tenant } from '@/types/tenant';

interface TenantState {
  tenants: Tenant[];
  currentTenantId: string | null;
  setTenants: (tenants: Tenant[]) => void;
  setCurrentTenant: (tenantId: string) => void;
  getCurrentTenant: () => Tenant | null;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set, get) => ({
      tenants: [],
      currentTenantId: null,

      setTenants: (tenants) => set({
        tenants,
        currentTenantId: tenants[0]?.id ?? null,
      }),

      setCurrentTenant: (tenantId) => set({ currentTenantId: tenantId }),

      getCurrentTenant: () => {
        const { tenants, currentTenantId } = get();
        return tenants.find((t) => t.id === currentTenantId) ?? null;
      },
    }),
    {
      name: 'aos-tenant',
      partialize: (state) => ({ currentTenantId: state.currentTenantId }),
    }
  )
);
```

---

## API Client

```typescript
// src/api/client.ts

import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE_URL = 'https://agenticverz.com/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const { token } = useAuthStore.getState();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const { refreshToken, setTokens, clearAuth } = useAuthStore.getState();

      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          setTokens(data.access_token, data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;

          return apiClient(originalRequest);
        } catch {
          clearAuth();
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);
```

---

## TypeScript Types

```typescript
// src/types/agent.ts

export interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'worker';
  status: 'active' | 'idle' | 'stale';
  capabilities: string[];
  registered_at: string;
  last_heartbeat: string;
  current_jobs: string[];
  metadata: Record<string, any>;
}

export interface AgentFilters {
  status?: Agent['status'];
  type?: Agent['type'];
  search?: string;
  page?: number;
  limit?: number;
}
```

```typescript
// src/types/job.ts

export interface Job {
  id: string;
  orchestrator_agent: string;
  worker_agent: string;
  task: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  parallelism: number;
  total_items: number;
  completed_items: number;
  failed_items: number;
  credits_reserved: number;
  credits_spent: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface JobItem {
  id: string;
  job_id: string;
  status: 'pending' | 'claimed' | 'completed' | 'failed';
  worker_id?: string;
  result?: any;
  error?: string;
  duration_ms?: number;
  created_at: string;
  claimed_at?: string;
  completed_at?: string;
}

export interface SimulationResult {
  feasible: boolean;
  estimated_credits: number;
  estimated_duration_seconds: number;
  budget_check: {
    sufficient: boolean;
    balance: number;
    required: number;
  };
  warnings: string[];
  risks: string[];
}
```

```typescript
// src/types/credit.ts

export interface CreditBalance {
  balance: number;
  reserved: number;
  available: number;
}

export interface LedgerEntry {
  id: string;
  tenant_id: string;
  type: 'reserve' | 'charge' | 'refund' | 'topup';
  amount: number;
  balance_after: number;
  job_id?: string;
  skill?: string;
  description?: string;
  created_at: string;
}

export interface InvokeAudit {
  invoke_id: string;
  caller_agent: string;
  target_agent: string;
  action: string;
  status: 'success' | 'failed' | 'timeout';
  duration_ms: number;
  credits_charged: number;
  started_at: string;
  completed_at?: string;
  error?: string;
}
```

---

## Package Dependencies

```json
{
  "name": "aos-console",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.8.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "clsx": "^2.0.0",
    "date-fns": "^2.30.0",
    "recharts": "^2.10.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-popover": "^1.0.7",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "lucide-react": "^0.294.0",
    "react-hot-toast": "^2.4.1",
    "@monaco-editor/react": "^4.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.54.0",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.2.2",
    "vite": "^5.0.0",
    "vitest": "^0.34.6"
  }
}
```

---

## Document Revision

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial component tree with full structure |
