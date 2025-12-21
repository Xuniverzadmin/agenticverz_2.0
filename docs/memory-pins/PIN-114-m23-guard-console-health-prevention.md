# PIN-114: M23 Guard Console - Health Detection & Prevention System

**Status:** COMPLETE
**Created:** 2025-12-21
**Milestone:** M23 AI Incident Console
**Category:** Frontend / Reliability

---

## Summary

Comprehensive health detection and prevention system for the Guard Console (Customer AI Safety Dashboard). Implements circuit breaker pattern, health monitoring, error boundaries, and graceful degradation to ensure the console remains functional even when backend services are unavailable.

---

## Components Implemented

### 1. Circuit Breaker Pattern (`/lib/healthCheck.ts`)

Prevents cascading failures by stopping requests to failing endpoints.

| Feature | Value | Description |
|---------|-------|-------------|
| Failure Threshold | 3 | Opens circuit after 3 consecutive failures |
| Recovery Timeout | 30s | Time before attempting recovery |
| Half-Open State | 1 request | Allows single test request to check recovery |
| Auto-Recovery | On success | Closes circuit on successful request |

```typescript
class CircuitBreaker {
  recordSuccess(endpoint: string): void;
  recordFailure(endpoint: string): void;
  canRequest(endpoint: string): boolean;
  getAllStates(): Record<string, CircuitState>;
}
```

### 2. Health Monitor (`/lib/healthCheck.ts`)

Real-time endpoint health tracking with periodic checks.

| Feature | Description |
|---------|-------------|
| Periodic Checks | Every 30 seconds |
| Response Time Tracking | Marks >2s as "degraded" |
| Critical vs Non-Critical | Status/Snapshot critical, Incidents non-critical |
| Real-time Updates | Subscribable health events |
| Overall Status | Computed from all endpoint states |

```typescript
class HealthMonitor {
  checkEndpoint(path: string): Promise<EndpointHealth>;
  checkAll(): Promise<SystemHealth>;
  startPeriodicCheck(intervalMs: number): void;
  subscribe(listener: (health: SystemHealth) => void): () => void;
}
```

### 3. Error Boundary (`/components/ErrorBoundary.tsx`)

React error boundary to catch rendering errors and prevent full app crashes.

- Catches React rendering errors
- Shows friendly error UI with error message
- "Try Again" button to retry rendering
- "Reload Page" button for full refresh
- Prevents full application crash

### 4. Health Indicator (`/components/HealthIndicator.tsx`)

Visual health status component displayed in the console header.

| Status | Color | Meaning |
|--------|-------|---------|
| All Systems Operational | Green | All endpoints < 2s |
| Degraded Performance | Yellow | Slow or partial failures |
| Service Disruption | Red | Critical endpoints down |

Features:
- Expandable details panel
- Per-endpoint health display
- Response times
- Circuit breaker states
- Manual refresh button

### 5. Fallback Data System (`GuardDashboard.tsx`)

Graceful degradation when APIs fail.

```typescript
const defaultStatus = {
  is_frozen: false,
  active_guardrails: ['max_cost_per_request', 'rate_limit_rpm', 'prompt_injection_block'],
  incidents_blocked_24h: 0,
};

const safeStatus = status || defaultStatus;
```

- Default values shown if API fails
- Yellow warning banner with "Retry" button
- Console remains usable with cached/default data

---

## File Locations

| File | Purpose | Size |
|------|---------|------|
| `website/aos-console/console/src/lib/healthCheck.ts` | Circuit breaker + health monitor | 8.5 KB |
| `website/aos-console/console/src/components/ErrorBoundary.tsx` | React error boundary | 3.2 KB |
| `website/aos-console/console/src/components/HealthIndicator.tsx` | Health status UI | 5.6 KB |
| `website/aos-console/console/src/pages/guard/GuardDashboard.tsx` | Main dashboard with prevention | 24.6 KB |
| `scripts/ops/guard_health_test.sh` | Health check test script | 4.2 KB |

---

## API Endpoints Monitored

| Endpoint | Critical | Purpose |
|----------|----------|---------|
| `/guard/status` | Yes | Protection status, guardrails |
| `/guard/snapshot/today` | Yes | Today's metrics |
| `/guard/incidents` | No | Incident history |

---

## Test Script

```bash
/root/agenticverz2.0/scripts/ops/guard_health_test.sh
```

Tests:
1. Endpoint health check (HTTP status + response time)
2. Circuit breaker simulation (404, 422 responses)
3. API response validation (required fields)
4. Demo incident seeding
5. Incidents list retrieval
6. Frontend files existence
7. Production deployment verification
8. Apache proxy configuration

---

## Console Access

**URL:** https://agenticverz.com/console/guard

**API Key:** `edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf`

**Tenant ID:** `tenant_demo`

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Guard Console UI                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Error     │  │   Health    │  │   Fallback Data     │  │
│  │  Boundary   │  │  Indicator  │  │   (Default Values)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Health Monitor                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  - Periodic checks (30s)                            │    │
│  │  - Response time tracking                           │    │
│  │  - Critical vs non-critical endpoints               │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                   Circuit Breaker                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  CLOSED ──(3 failures)──> OPEN ──(30s)──> HALF-OPEN │    │
│  │     ▲                                        │       │    │
│  │     └────────────(success)───────────────────┘       │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Guard API                                 │
│  /guard/status  /guard/snapshot  /guard/incidents           │
└─────────────────────────────────────────────────────────────┘
```

---

## Related PINs

- PIN-100: M23 AI Incident Console Production
- PIN-098: M22.1 UI Console Implementation
- PIN-099: SQLModel Row Extraction Patterns

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-21 | Initial implementation - circuit breaker, health monitor, error boundary |
| 2025-12-21 | Added HealthIndicator component with expandable details |
| 2025-12-21 | Created guard_health_test.sh script |
| 2025-12-21 | Deployed to production |
