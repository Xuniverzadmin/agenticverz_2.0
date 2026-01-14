// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: scheduler
//   Execution: async
// Role: Health check utility for backend connectivity
// Callers: App root, status components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Utilities

/**
 * Health Check & Circuit Breaker System
 *
 * Provides:
 * 1. Endpoint health monitoring
 * 2. Circuit breaker pattern (prevents cascading failures)
 * 3. Automatic recovery detection
 * 4. Health status dashboard data
 */

import { apiClient } from '@/api/client';

// ============== TYPES ==============

export interface EndpointHealth {
  endpoint: string;
  status: 'healthy' | 'degraded' | 'down';
  lastCheck: Date;
  lastSuccess: Date | null;
  lastError: string | null;
  responseTime: number;
  failureCount: number;
  successCount: number;
}

export interface CircuitState {
  state: 'closed' | 'open' | 'half-open';
  failures: number;
  lastFailure: Date | null;
  nextRetry: Date | null;
}

export interface SystemHealth {
  overall: 'healthy' | 'degraded' | 'down';
  endpoints: Record<string, EndpointHealth>;
  circuits: Record<string, CircuitState>;
  lastFullCheck: Date;
}

// Simplified health state for UI components
export interface HealthState {
  status: 'healthy' | 'degraded' | 'down';
  latency: number | null;
  lastCheck: Date | null;
  circuitOpen: boolean;
}

// Convert SystemHealth to simplified HealthState
export function toHealthState(system: SystemHealth): HealthState {
  const endpoints = Object.values(system.endpoints);
  const avgLatency = endpoints.length > 0
    ? endpoints.reduce((sum, ep) => sum + ep.responseTime, 0) / endpoints.length
    : null;
  const anyCircuitOpen = Object.values(system.circuits).some(c => c.state === 'open');

  return {
    status: system.overall,
    latency: avgLatency ? Math.round(avgLatency) : null,
    lastCheck: system.lastFullCheck,
    circuitOpen: anyCircuitOpen,
  };
}

// ============== CIRCUIT BREAKER ==============

const CIRCUIT_CONFIG = {
  failureThreshold: 3,      // Open circuit after 3 failures
  recoveryTimeout: 30000,   // Try again after 30 seconds
  halfOpenRequests: 1,      // Allow 1 request in half-open state
};

class CircuitBreaker {
  private circuits: Map<string, CircuitState> = new Map();

  getState(endpoint: string): CircuitState {
    if (!this.circuits.has(endpoint)) {
      this.circuits.set(endpoint, {
        state: 'closed',
        failures: 0,
        lastFailure: null,
        nextRetry: null,
      });
    }
    return this.circuits.get(endpoint)!;
  }

  recordSuccess(endpoint: string): void {
    const circuit = this.getState(endpoint);
    circuit.state = 'closed';
    circuit.failures = 0;
    circuit.lastFailure = null;
    circuit.nextRetry = null;
  }

  recordFailure(endpoint: string): void {
    const circuit = this.getState(endpoint);
    circuit.failures++;
    circuit.lastFailure = new Date();

    if (circuit.failures >= CIRCUIT_CONFIG.failureThreshold) {
      // Only log when circuit first opens, not on every failure
      const wasOpen = circuit.state === 'open';
      circuit.state = 'open';
      circuit.nextRetry = new Date(Date.now() + CIRCUIT_CONFIG.recoveryTimeout);
      if (!wasOpen) {
        console.debug(`[CircuitBreaker] Circuit OPEN for ${endpoint}`);
      }
    }
  }

  canRequest(endpoint: string): boolean {
    const circuit = this.getState(endpoint);

    if (circuit.state === 'closed') {
      return true;
    }

    if (circuit.state === 'open') {
      // Check if recovery timeout has passed
      if (circuit.nextRetry && new Date() >= circuit.nextRetry) {
        circuit.state = 'half-open';
        return true;
      }
      return false;
    }

    // half-open: allow one request
    return true;
  }

  getAllStates(): Record<string, CircuitState> {
    const states: Record<string, CircuitState> = {};
    this.circuits.forEach((state, endpoint) => {
      states[endpoint] = { ...state };
    });
    return states;
  }
}

export const circuitBreaker = new CircuitBreaker();

// ============== HEALTH MONITOR ==============

const GUARD_ENDPOINTS = [
  { path: '/guard/status', name: 'Status', critical: true },
  { path: '/guard/snapshot/today', name: 'Snapshot', critical: true },
  { path: '/guard/incidents', name: 'Incidents', critical: false },
];

class HealthMonitor {
  private health: Map<string, EndpointHealth> = new Map();
  private checkInterval: ReturnType<typeof setInterval> | null = null;
  private listeners: Set<(health: SystemHealth) => void> = new Set();

  constructor() {
    // Initialize health records
    GUARD_ENDPOINTS.forEach(ep => {
      this.health.set(ep.path, {
        endpoint: ep.path,
        status: 'healthy',
        lastCheck: new Date(),
        lastSuccess: null,
        lastError: null,
        responseTime: 0,
        failureCount: 0,
        successCount: 0,
      });
    });
  }

  async checkEndpoint(path: string, tenantId: string): Promise<EndpointHealth> {
    // NO FALLBACK - tenant ID is required
    if (!tenantId) {
      throw new Error('[HealthMonitor] tenant ID is required. Cannot check endpoint without valid tenant.');
    }
    const health = this.health.get(path) || {
      endpoint: path,
      status: 'healthy' as const,
      lastCheck: new Date(),
      lastSuccess: null,
      lastError: null,
      responseTime: 0,
      failureCount: 0,
      successCount: 0,
    };

    const start = performance.now();

    try {
      const response = await apiClient.get(path, {
        params: { tenant_id: tenantId },
        timeout: 5000,
      });

      const responseTime = performance.now() - start;

      health.status = responseTime > 2000 ? 'degraded' : 'healthy';
      health.lastCheck = new Date();
      health.lastSuccess = new Date();
      health.lastError = null;
      health.responseTime = responseTime;
      health.successCount++;
      health.failureCount = 0;

      circuitBreaker.recordSuccess(path);

    } catch (error: any) {
      health.status = 'down';
      health.lastCheck = new Date();
      health.lastError = error?.response?.status
        ? `HTTP ${error.response.status}`
        : error?.message || 'Unknown error';
      health.responseTime = performance.now() - start;
      health.failureCount++;

      circuitBreaker.recordFailure(path);
    }

    this.health.set(path, health);
    return health;
  }

  async checkAll(tenantId: string): Promise<SystemHealth> {
    // NO FALLBACK - tenant ID is required
    if (!tenantId) {
      throw new Error('[HealthMonitor] tenant ID is required. Cannot check endpoints without valid tenant.');
    }
    const results = await Promise.all(
      GUARD_ENDPOINTS.map(ep => this.checkEndpoint(ep.path, tenantId))
    );

    const endpoints: Record<string, EndpointHealth> = {};
    results.forEach(h => { endpoints[h.endpoint] = h; });

    // Determine overall health
    const criticalDown = GUARD_ENDPOINTS
      .filter(ep => ep.critical)
      .some(ep => endpoints[ep.path]?.status === 'down');

    const anyDown = results.some(h => h.status === 'down');
    const anyDegraded = results.some(h => h.status === 'degraded');

    let overall: 'healthy' | 'degraded' | 'down';
    if (criticalDown) {
      overall = 'down';
    } else if (anyDown || anyDegraded) {
      overall = 'degraded';
    } else {
      overall = 'healthy';
    }

    const systemHealth: SystemHealth = {
      overall,
      endpoints,
      circuits: circuitBreaker.getAllStates(),
      lastFullCheck: new Date(),
    };

    // Notify listeners
    this.listeners.forEach(listener => listener(systemHealth));

    return systemHealth;
  }

  startPeriodicCheck(intervalMs: number = 30000, tenantId: string): void {
    // NO FALLBACK - tenant ID is required
    if (!tenantId) {
      console.warn('[HealthMonitor] Cannot start periodic check without tenant ID');
      return;
    }
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }

    // Initial check
    this.checkAll(tenantId);

    // Periodic checks
    this.checkInterval = setInterval(() => {
      this.checkAll(tenantId);
    }, intervalMs);
  }

  stopPeriodicCheck(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }

  subscribe(listener: (health: SystemHealth) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getHealth(): SystemHealth {
    const endpoints: Record<string, EndpointHealth> = {};
    this.health.forEach((h, path) => { endpoints[path] = h; });

    const anyDown = Array.from(this.health.values()).some(h => h.status === 'down');
    const anyDegraded = Array.from(this.health.values()).some(h => h.status === 'degraded');

    return {
      overall: anyDown ? 'down' : anyDegraded ? 'degraded' : 'healthy',
      endpoints,
      circuits: circuitBreaker.getAllStates(),
      lastFullCheck: new Date(),
    };
  }
}

export const healthMonitor = new HealthMonitor();

// ============== SAFE API WRAPPER ==============

export async function safeApiCall<T>(
  endpoint: string,
  fn: () => Promise<T>,
  fallback: T
): Promise<{ data: T; fromCache: boolean; error?: string }> {
  // Check circuit breaker - silent fallback when circuit is open
  if (!circuitBreaker.canRequest(endpoint)) {
    return { data: fallback, fromCache: true, error: 'Circuit breaker open' };
  }

  try {
    const data = await fn();
    circuitBreaker.recordSuccess(endpoint);
    return { data, fromCache: false };
  } catch (error: any) {
    circuitBreaker.recordFailure(endpoint);
    const errorMsg = error?.response?.status
      ? `HTTP ${error.response.status}`
      : error?.message || 'Unknown error';
    return { data: fallback, fromCache: true, error: errorMsg };
  }
}

// ============== EXPORTS ==============

export default {
  circuitBreaker,
  healthMonitor,
  safeApiCall,
  toHealthState,
};
