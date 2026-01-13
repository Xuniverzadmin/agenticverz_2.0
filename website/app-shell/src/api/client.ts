/**
 * @audience shared
 *
 * Base API Client
 * Core axios instance used by all API clients
 *
 * RULE-AUTH-UI-001: Clerk is the auth store.
 * - Token attachment handled by ClerkAuthSync component
 * - This client only enforces AUTH-001 (no tenant in URL)
 * - No token storage or auth state management here
 *
 * Reference: docs/governance/AUTH_INVARIANTS.md, FRONTEND_AUTH_CONTRACT.md
 */
import axios, { InternalAxiosRequestConfig } from 'axios';

// Use relative URL in production (same origin), empty for same-origin requests
const API_BASE = import.meta.env.VITE_API_BASE || '';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '15000', 10);

/**
 * AUTH-001 Guard: Validates that customer API paths don't contain tenant IDs
 *
 * Scope: Customer Console authenticated endpoints (/api/v1/...)
 * Excluded:
 * - Operator endpoints (/operator/...) - operators need cross-tenant access
 * - Tenant management (/api/v1/tenants, /api/v1/tenants/switch) - administrative
 */
function assertAuth001Compliance(url: string | undefined): void {
  if (!url) return;

  // Only check customer API paths
  if (!url.startsWith('/api/v1/')) return;

  // Allowed tenant management paths (not data access)
  const allowedTenantPaths = [
    '/api/v1/tenants',        // List tenants
    '/api/v1/tenants/switch', // Switch tenant
  ];
  if (allowedTenantPaths.some(allowed => url === allowed || url.startsWith(allowed + '?'))) {
    return;
  }

  // Forbidden: /api/v1/tenants/{uuid}/... (tenant-scoped data in URL)
  const tenantDataPattern = /\/api\/v1\/tenants\/[a-f0-9-]+\//i;
  if (tenantDataPattern.test(url)) {
    console.error(
      `AUTH-001 VIOLATION: Tenant ID in customer API path\n` +
      `Path: ${url}\n` +
      `Tenant identity must come from JWT claims.\n` +
      `Reference: docs/governance/AUTH_INVARIANTS.md`
    );
    throw new Error(`AUTH-001 VIOLATION: Tenant ID not allowed in path: ${url}`);
  }
}

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - enforce AUTH-001 only
// Token attachment is handled by ClerkAuthSync component
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // AUTH-001: Validate no tenant-in-URL for customer endpoints
  assertAuth001Compliance(config.url);
  return config;
});

// Response interceptor - handle 401 by redirecting to login
// Clerk will handle re-authentication
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Redirect to login - Clerk will handle authentication
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
