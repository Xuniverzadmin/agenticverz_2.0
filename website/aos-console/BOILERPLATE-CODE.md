# AOS Console Boilerplate Code

**Version:** 1.0.0
**Created:** 2025-12-13
**Purpose:** Copy-paste ready code for every file

---

## Directory Structure

```
console/
├── public/
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── vite-env.d.ts
│   ├── index.css
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── agents.ts
│   │   ├── jobs.ts
│   │   ├── blackboard.ts
│   │   ├── messages.ts
│   │   ├── credits.ts
│   │   ├── metrics.ts
│   │   └── auth.ts
│   │
│   ├── lib/
│   │   ├── sse.ts
│   │   ├── websocket.ts
│   │   ├── utils.ts
│   │   └── constants.ts
│   │
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── tenantStore.ts
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useAgents.ts
│   │   ├── useJobs.ts
│   │   ├── useBlackboard.ts
│   │   ├── useCredits.ts
│   │   └── useWebSocket.ts
│   │
│   ├── types/
│   │   ├── agent.ts
│   │   ├── job.ts
│   │   ├── blackboard.ts
│   │   ├── message.ts
│   │   ├── credit.ts
│   │   └── events.ts
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── StatusBar.tsx
│   │   │
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── DataTable.tsx
│   │   │   └── Toast.tsx
│   │   │
│   │   └── charts/
│   │       ├── LineChart.tsx
│   │       ├── ProgressBar.tsx
│   │       └── Gauge.tsx
│   │
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── ForgotPasswordPage.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   └── DashboardPage.tsx
│   │   │
│   │   ├── agents/
│   │   │   └── AgentsPage.tsx
│   │   │
│   │   ├── jobs/
│   │   │   ├── JobSimulatorPage.tsx
│   │   │   ├── JobRunnerPage.tsx
│   │   │   └── JobHistoryPage.tsx
│   │   │
│   │   ├── blackboard/
│   │   │   └── BlackboardPage.tsx
│   │   │
│   │   ├── messaging/
│   │   │   └── MessagingPage.tsx
│   │   │
│   │   ├── credits/
│   │   │   └── CreditsPage.tsx
│   │   │
│   │   └── metrics/
│   │       └── MetricsPage.tsx
│   │
│   └── routes/
│       ├── index.tsx
│       └── ProtectedRoute.tsx
│
├── .env.development
├── .env.production
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
└── vite.config.ts
```

---

## Configuration Files

### package.json

```json
{
  "name": "aos-console",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.8.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.2",
    "clsx": "^2.0.0",
    "dayjs": "^1.11.10",
    "recharts": "^2.10.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.54.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  base: '/console/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
```

### postcss.config.js

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### index.html

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/console/logo.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AOS Console</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### .env.development

```
VITE_API_BASE=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

### .env.production

```
VITE_API_BASE=https://agenticverz.com/api/v1
VITE_WS_URL=wss://agenticverz.com/ws
```

---

## Entry Points

### src/main.tsx

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

### src/App.tsx

```typescript
import { BrowserRouter } from 'react-router-dom';
import { AppRoutes } from './routes';
import { Toaster } from './components/common/Toast';

export default function App() {
  return (
    <BrowserRouter basename="/console">
      <AppRoutes />
      <Toaster />
    </BrowserRouter>
  );
}
```

### src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f8fafc;
  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;
  --color-border: #e2e8f0;
}

[data-theme='dark'] {
  --color-bg-primary: #0f172a;
  --color-bg-secondary: #1e293b;
  --color-text-primary: #f8fafc;
  --color-text-secondary: #94a3b8;
  --color-border: #334155;
}

body {
  font-family: 'Inter', sans-serif;
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.font-mono {
  font-family: 'JetBrains Mono', monospace;
}
```

---

## API Layer

### src/api/client.ts

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE = import.meta.env.VITE_API_BASE;

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  const tenantId = useAuthStore.getState().tenantId;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }

  return config;
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest) {
      const { refreshToken, setTokens, logout } = useAuthStore.getState();

      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          setTokens(data.access_token, data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return apiClient(originalRequest);
        } catch {
          logout();
          window.location.href = '/console/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### src/api/agents.ts

```typescript
import apiClient from './client';
import type { Agent, AgentFilters, PaginatedResponse } from '@/types/agent';

export async function getAgents(filters?: AgentFilters): Promise<PaginatedResponse<Agent>> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.type) params.set('type', filters.type);
  if (filters?.search) params.set('search', filters.search);
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.limit) params.set('limit', String(filters.limit));

  const { data } = await apiClient.get(`/agents?${params}`);
  return data;
}

export async function getAgent(agentId: string): Promise<Agent> {
  const { data } = await apiClient.get(`/agents/${agentId}`);
  return data;
}

export async function registerAgent(payload: {
  agent_name: string;
  agent_type: 'orchestrator' | 'worker';
  capabilities: string[];
}): Promise<Agent> {
  const { data } = await apiClient.post('/agents/register', payload);
  return data;
}

export async function deregisterAgent(agentId: string): Promise<void> {
  await apiClient.delete(`/agents/${agentId}`);
}

export async function sendHeartbeat(agentId: string): Promise<void> {
  await apiClient.post(`/agents/${agentId}/heartbeat`);
}
```

### src/api/jobs.ts

```typescript
import apiClient from './client';
import type { Job, JobItem, SimulationResult, CreateJobRequest } from '@/types/job';

export async function getJobs(params?: {
  status?: string;
  page?: number;
  limit?: number;
}) {
  const { data } = await apiClient.get('/jobs', { params });
  return data;
}

export async function getJob(jobId: string): Promise<Job> {
  const { data } = await apiClient.get(`/jobs/${jobId}`);
  return data;
}

export async function getJobItems(jobId: string): Promise<JobItem[]> {
  const { data } = await apiClient.get(`/jobs/${jobId}/items`);
  return data;
}

export async function simulateJob(request: CreateJobRequest): Promise<SimulationResult> {
  const { data } = await apiClient.post('/jobs/simulate', request);
  return data;
}

export async function createJob(request: CreateJobRequest): Promise<Job> {
  const { data } = await apiClient.post('/jobs', request);
  return data;
}

export async function cancelJob(jobId: string): Promise<{
  job_id: string;
  status: string;
  completed_items: number;
  cancelled_items: number;
  credits_refunded: number;
}> {
  const { data } = await apiClient.post(`/jobs/${jobId}/cancel`);
  return data;
}
```

### src/api/blackboard.ts

```typescript
import apiClient from './client';
import type { BlackboardEntry } from '@/types/blackboard';

export async function getBlackboardKeys(params?: {
  pattern?: string;
  page?: number;
  limit?: number;
}) {
  const { data } = await apiClient.get('/blackboard', { params });
  return data;
}

export async function getBlackboardKey(key: string): Promise<BlackboardEntry> {
  const { data } = await apiClient.get(`/blackboard/${encodeURIComponent(key)}`);
  return data;
}

export async function setBlackboardKey(
  key: string,
  value: unknown,
  ttl_seconds?: number
): Promise<BlackboardEntry> {
  const { data } = await apiClient.put(`/blackboard/${encodeURIComponent(key)}`, {
    value,
    ttl_seconds,
  });
  return data;
}

export async function incrementBlackboardKey(
  key: string,
  amount: number
): Promise<{ new_value: number }> {
  const { data } = await apiClient.post(`/blackboard/${encodeURIComponent(key)}/increment`, {
    amount,
  });
  return data;
}

export async function deleteBlackboardKey(key: string): Promise<void> {
  await apiClient.delete(`/blackboard/${encodeURIComponent(key)}`);
}
```

### src/api/credits.ts

```typescript
import apiClient from './client';
import type { CreditBalance, LedgerEntry } from '@/types/credit';

export async function getCreditBalance(): Promise<CreditBalance> {
  const { data } = await apiClient.get('/credits/balance');
  return data;
}

export async function getLedger(params?: {
  type?: string;
  job_id?: string;
  page?: number;
  limit?: number;
}) {
  const { data } = await apiClient.get('/credits/ledger', { params });
  return data;
}

export async function getCreditUsage(params?: {
  range?: string;
  granularity?: string;
}) {
  const { data } = await apiClient.get('/credits/usage', { params });
  return data;
}
```

### src/api/auth.ts

```typescript
import apiClient from './client';

export async function login(email: string, password: string, remember = false) {
  const { data } = await apiClient.post('/auth/login', {
    email,
    password,
    remember,
  });
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout');
}

export async function refreshToken(refresh_token: string) {
  const { data } = await apiClient.post('/auth/refresh', { refresh_token });
  return data;
}

export async function getCurrentUser() {
  const { data } = await apiClient.get('/users/me');
  return data;
}
```

---

## Library / Utilities

### src/lib/sse.ts

```typescript
type EventHandler = (event: MessageEvent) => void;

export class SSEConnection {
  private eventSource: EventSource | null = null;
  private handlers: Map<string, EventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseDelay = 1000;

  connect(url: string, token: string) {
    const fullUrl = `${url}?token=${token}`;
    this.eventSource = new EventSource(fullUrl);

    this.eventSource.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.eventSource.onerror = () => {
      this.reconnect(url, token);
    };

    this.eventSource.onmessage = (event) => {
      const handlers = this.handlers.get('message') || [];
      handlers.forEach((handler) => handler(event));
    };
  }

  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);

    if (this.eventSource && eventType !== 'message') {
      this.eventSource.addEventListener(eventType, handler);
    }
  }

  off(eventType: string, handler: EventHandler) {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private reconnect(url: string, token: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('SSE: Max reconnection attempts reached');
      return;
    }

    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.reconnectAttempts),
      30000
    );

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(url, token);
    }, delay);
  }

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
    this.handlers.clear();
  }
}
```

### src/lib/websocket.ts

```typescript
type MessageHandler = (data: unknown) => void;

export class WebSocketConnection {
  private ws: WebSocket | null = null;
  private subscriptions: Set<string> = new Set();
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private token: string = '';

  connect(url: string, token: string) {
    this.token = token;
    const fullUrl = `${url}?token=${token}`;
    this.ws = new WebSocket(fullUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.subscriptions.forEach((channel) => this.subscribe(channel));
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      if (!event.wasClean) {
        this.reconnect(url);
      }
    };
  }

  subscribe(channel: string) {
    this.subscriptions.add(channel);
    this.send({ type: 'subscribe', channel });
  }

  unsubscribe(channel: string) {
    this.subscriptions.delete(channel);
    this.send({ type: 'unsubscribe', channel });
  }

  on(eventType: string, handler: MessageHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  private send(data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private handleMessage(message: { type: string; event?: unknown }) {
    if (message.type === 'event' && message.event) {
      const handlers = this.handlers.get('event') || [];
      handlers.forEach((handler) => handler(message.event));
    }
  }

  private reconnect(url: string) {
    if (this.reconnectAttempts >= 10) return;

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(url, this.token);
    }, delay);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}
```

### src/lib/utils.ts

```typescript
import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCredits(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

export function formatTimeAgo(date: string | Date): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
```

### src/lib/constants.ts

```typescript
export const API_BASE = import.meta.env.VITE_API_BASE;
export const WS_URL = import.meta.env.VITE_WS_URL;

export const REFRESH_INTERVALS = {
  FAST: 5000,    // 5 seconds
  NORMAL: 30000, // 30 seconds
  SLOW: 60000,   // 1 minute
} as const;

export const SKILL_COSTS: Record<string, number> = {
  agent_spawn: 5,
  agent_invoke: 10,
  blackboard_read: 1,
  blackboard_write: 1,
  blackboard_lock: 1,
  job_item: 2,
};

export const STATUS_COLORS = {
  active: 'text-green-500',
  idle: 'text-gray-500',
  stale: 'text-yellow-500',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  cancelled: 'text-gray-500',
  pending: 'text-yellow-500',
} as const;
```

---

## Stores

### src/stores/authStore.ts

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  tenantId: string | null;
  user: User | null;
  isAuthenticated: boolean;

  setTokens: (token: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  setTenant: (tenantId: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      tenantId: null,
      user: null,
      isAuthenticated: false,

      setTokens: (token, refreshToken) =>
        set({ token, refreshToken, isAuthenticated: true }),

      setUser: (user) => set({ user }),

      setTenant: (tenantId) => set({ tenantId }),

      logout: () =>
        set({
          token: null,
          refreshToken: null,
          tenantId: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'aos-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        tenantId: state.tenantId,
      }),
    }
  )
);
```

### src/stores/uiStore.ts

```typescript
import { create } from 'zustand';

interface UIState {
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  activeModal: string | null;

  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  theme: 'light',
  activeModal: null,

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setTheme: (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    set({ theme });
  },

  openModal: (modalId) => set({ activeModal: modalId }),
  closeModal: () => set({ activeModal: null }),
}));
```

---

## Types

### src/types/agent.ts

```typescript
export interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'worker';
  status: 'active' | 'idle' | 'stale';
  capabilities: string[];
  registered_at: string;
  last_heartbeat: string;
  heartbeat_age_seconds: number;
  current_jobs: string[];
  metadata: Record<string, unknown>;
}

export interface AgentFilters {
  status?: 'active' | 'idle' | 'stale';
  type?: 'orchestrator' | 'worker';
  search?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
```

### src/types/job.ts

```typescript
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
  started_at: string | null;
  completed_at: string | null;
}

export interface JobItem {
  id: string;
  job_id: string;
  status: 'pending' | 'claimed' | 'completed' | 'failed';
  worker_id: string | null;
  result: unknown;
  error: string | null;
  duration_ms: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface CreateJobRequest {
  orchestrator_agent: string;
  worker_agent: string;
  task: string;
  items: Array<{ id: string; [key: string]: unknown }>;
  parallelism: number;
  max_retries?: number;
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

### src/types/credit.ts

```typescript
export interface CreditBalance {
  balance: number;
  reserved: number;
  available: number;
  last_updated: string;
}

export interface LedgerEntry {
  id: string;
  type: 'reserve' | 'charge' | 'refund' | 'topup';
  amount: number;
  balance_after: number;
  job_id: string | null;
  skill: string | null;
  description: string;
  created_at: string;
}
```

---

## Routes

### src/routes/index.tsx

```typescript
import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { Spinner } from '@/components/common/Spinner';

const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const AgentsPage = lazy(() => import('@/pages/agents/AgentsPage'));
const JobSimulatorPage = lazy(() => import('@/pages/jobs/JobSimulatorPage'));
const JobRunnerPage = lazy(() => import('@/pages/jobs/JobRunnerPage'));
const BlackboardPage = lazy(() => import('@/pages/blackboard/BlackboardPage'));
const MessagingPage = lazy(() => import('@/pages/messaging/MessagingPage'));
const CreditsPage = lazy(() => import('@/pages/credits/CreditsPage'));
const MetricsPage = lazy(() => import('@/pages/metrics/MetricsPage'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen">
      <Spinner size="lg" />
    </div>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="jobs">
            <Route index element={<Navigate to="simulator" replace />} />
            <Route path="simulator" element={<JobSimulatorPage />} />
            <Route path="runner/:jobId" element={<JobRunnerPage />} />
          </Route>
          <Route path="blackboard" element={<BlackboardPage />} />
          <Route path="messaging" element={<MessagingPage />} />
          <Route path="credits" element={<CreditsPage />} />
          <Route path="metrics" element={<MetricsPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
```

### src/routes/ProtectedRoute.tsx

```typescript
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

---

## Layout Components

### src/components/layout/AppLayout.tsx

```typescript
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';

export function AppLayout() {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar collapsed={sidebarCollapsed} />
        <main
          className={cn(
            'flex-1 overflow-auto p-6 transition-all',
            sidebarCollapsed ? 'ml-16' : 'ml-60'
          )}
        >
          <Outlet />
        </main>
      </div>
      <StatusBar />
    </div>
  );
}
```

### src/components/layout/Header.tsx

```typescript
import { Bell, User, Moon, Sun } from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/common/Button';

export function Header() {
  const { theme, setTheme } = useUIStore();
  const user = useAuthStore((state) => state.user);

  return (
    <header className="h-16 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <img src="/console/logo.svg" alt="AOS" className="h-8" />
        <span className="font-semibold text-lg">AOS Console</span>
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </Button>

        <Button variant="ghost" size="sm">
          <Bell size={18} />
        </Button>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-white">
            <User size={16} />
          </div>
          <span className="text-sm font-medium">{user?.name || 'User'}</span>
        </div>
      </div>
    </header>
  );
}
```

### src/components/layout/Sidebar.tsx

```typescript
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  PlayCircle,
  Database,
  MessageSquare,
  Wallet,
  BarChart3,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
  { icon: Users, label: 'Agents', href: '/agents' },
  { icon: PlayCircle, label: 'Jobs', href: '/jobs/simulator' },
  { icon: Database, label: 'Blackboard', href: '/blackboard' },
  { icon: MessageSquare, label: 'Messages', href: '/messaging' },
  { icon: Wallet, label: 'Credits', href: '/credits' },
  { icon: BarChart3, label: 'Metrics', href: '/metrics' },
];

interface SidebarProps {
  collapsed: boolean;
}

export function Sidebar({ collapsed }: SidebarProps) {
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);

  return (
    <aside
      className={cn(
        'fixed left-0 top-16 h-[calc(100vh-4rem-2rem)] bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all z-10',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      <nav className="p-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
              )
            }
          >
            <item.icon size={20} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-6 w-6 h-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full flex items-center justify-center"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </aside>
  );
}
```

### src/components/layout/StatusBar.tsx

```typescript
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { cn } from '@/lib/utils';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    api: { status: string };
    database: { status: string };
    redis: { status: string };
  };
}

export function StatusBar() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthStatus>('/health');
      return data;
    },
    refetchInterval: 30000,
  });

  const services = health?.services || {};

  return (
    <footer className="h-8 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 flex items-center justify-between text-xs">
      <div className="flex items-center gap-4">
        <StatusDot label="API" status={services.api?.status} />
        <StatusDot label="DB" status={services.database?.status} />
        <StatusDot label="Redis" status={services.redis?.status} />
      </div>
      <div className="text-gray-500">
        v1.0.0 • {new Date().toISOString().slice(0, 19)} UTC
      </div>
    </footer>
  );
}

function StatusDot({ label, status }: { label: string; status?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={cn(
          'w-2 h-2 rounded-full',
          status === 'healthy' && 'bg-green-500',
          status === 'degraded' && 'bg-yellow-500',
          status === 'unhealthy' && 'bg-red-500',
          !status && 'bg-gray-400'
        )}
      />
      <span className="text-gray-600 dark:text-gray-400">{label}</span>
    </div>
  );
}
```

---

## Common Components

### src/components/common/Button.tsx

```typescript
import { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { Spinner } from './Spinner';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
          {
            'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500':
              variant === 'primary',
            'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-200':
              variant === 'secondary',
            'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700':
              variant === 'ghost',
            'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500':
              variant === 'danger',
          },
          {
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2 text-sm': size === 'md',
            'px-5 py-2.5 text-base': size === 'lg',
          },
          'disabled:opacity-50 disabled:cursor-not-allowed',
          className
        )}
        {...props}
      >
        {loading && <Spinner size="sm" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

### src/components/common/Card.tsx

```typescript
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm',
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 border-b border-gray-200 dark:border-gray-700',
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardBody({ children, className }: CardProps) {
  return <div className={cn('p-4', className)}>{children}</div>;
}
```

### src/components/common/Spinner.tsx

```typescript
import { cn } from '@/lib/utils';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-gray-300 border-t-primary-600',
        {
          'w-4 h-4': size === 'sm',
          'w-6 h-6': size === 'md',
          'w-8 h-8': size === 'lg',
        },
        className
      )}
    />
  );
}
```

### src/components/common/Badge.tsx

```typescript
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
        {
          'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300':
            variant === 'default',
          'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300':
            variant === 'success',
          'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300':
            variant === 'warning',
          'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300':
            variant === 'error',
          'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300':
            variant === 'info',
        },
        className
      )}
    >
      {children}
    </span>
  );
}
```

### src/components/common/Toast.tsx

```typescript
import { create } from 'zustand';
import { cn } from '@/lib/utils';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface ToastStore {
  toasts: Toast[];
  add: (toast: Omit<Toast, 'id'>) => void;
  remove: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  add: (toast) => {
    const id = Math.random().toString(36).slice(2);
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 5000);
  },
  remove: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export function toast(type: Toast['type'], message: string) {
  useToastStore.getState().add({ type, message });
}

export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);
  const remove = useToastStore((state) => state.remove);

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg min-w-[300px]',
            t.type === 'success' && 'bg-green-600 text-white',
            t.type === 'error' && 'bg-red-600 text-white',
            t.type === 'info' && 'bg-blue-600 text-white'
          )}
        >
          {t.type === 'success' && <CheckCircle size={18} />}
          {t.type === 'error' && <AlertCircle size={18} />}
          {t.type === 'info' && <Info size={18} />}
          <span className="flex-1 text-sm">{t.message}</span>
          <button onClick={() => remove(t.id)}>
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

## Sample Page Implementation

### src/pages/dashboard/DashboardPage.tsx

```typescript
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardBody } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Spinner } from '@/components/common/Spinner';
import apiClient from '@/api/client';
import { formatCredits, formatTimeAgo } from '@/lib/utils';

export default function DashboardPage() {
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics-summary'],
    queryFn: async () => {
      const { data } = await apiClient.get('/metrics/summary?range=24h');
      return data;
    },
    refetchInterval: 30000,
  });

  const { data: jobs } = useQuery({
    queryKey: ['active-jobs'],
    queryFn: async () => {
      const { data } = await apiClient.get('/jobs?status=running&limit=5');
      return data;
    },
    refetchInterval: 30000,
  });

  const { data: credits } = useQuery({
    queryKey: ['credits-balance'],
    queryFn: async () => {
      const { data } = await apiClient.get('/credits/balance');
      return data;
    },
    refetchInterval: 60000,
  });

  if (metricsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Jobs"
          value={metrics?.active_jobs || 0}
          trend={metrics?.trends?.active_jobs_change}
        />
        <MetricCard
          title="Completed Today"
          value={metrics?.completed_today || 0}
          trend={metrics?.trends?.completed_change}
        />
        <MetricCard
          title="Failed Today"
          value={metrics?.failed_today || 0}
          trend={metrics?.trends?.failed_change}
          invertTrend
        />
        <MetricCard
          title="Credits Balance"
          value={formatCredits(credits?.balance || 0)}
          trend={metrics?.trends?.credits_change}
        />
      </div>

      {/* Active Jobs Table */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold">Active Jobs</h2>
        </CardHeader>
        <CardBody className="p-0">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Job ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Progress
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Started
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {jobs?.items?.map((job: any) => (
                <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-4 py-3 font-mono text-sm">{job.id.slice(0, 12)}</td>
                  <td className="px-4 py-3">
                    <Badge variant={job.status === 'running' ? 'info' : 'default'}>
                      {job.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-500 rounded-full"
                          style={{ width: `${job.progress_percent || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500">
                        {job.completed_items}/{job.total_items}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatTimeAgo(job.started_at)}
                  </td>
                </tr>
              ))}
              {!jobs?.items?.length && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                    No active jobs
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}

function MetricCard({
  title,
  value,
  trend,
  invertTrend = false,
}: {
  title: string;
  value: string | number;
  trend?: number;
  invertTrend?: boolean;
}) {
  const isPositive = invertTrend ? (trend || 0) < 0 : (trend || 0) > 0;

  return (
    <Card>
      <CardBody>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
        {trend !== undefined && (
          <p
            className={`text-sm mt-1 ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {trend > 0 ? '+' : ''}
            {trend}%
          </p>
        )}
      </CardBody>
    </Card>
  );
}
```

---

## Document Revision

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial boilerplate code |
