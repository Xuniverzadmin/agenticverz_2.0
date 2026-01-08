/**
 * Routes — Centralized Route Definitions
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: build-time (derived from consoleRoots)
 *   Execution: sync
 * Role: Single source of truth for ALL route paths
 * Reference: PIN-352, Routing Authority Model
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (deliberate changes only)
 * Last Frozen: 2026-01-08
 *
 * INVARIANTS:
 * - ALL routes in the application MUST be imported from here
 * - NO string literals for paths allowed in components
 * - Routes are derived from CONSOLE_ROOT and DOMAIN_ROOTS
 * - CI will fail if hardcoded paths are detected
 */

import {
  CONSOLE_ROOT,
  CUSTOMER_ROOT,
  FOUNDER_ROOT,
  PRECUS_ROOT,
  CUS_ROOT,
  PREFOPS_ROOT,
  FOPS_ROOT,
  DOMAIN_ROOTS,
  SECONDARY_ROOTS,
  FOUNDER_DOMAIN_ROOTS,
} from './consoleRoots';
import { IS_PREFLIGHT, IS_CUSTOMER_CONSOLE } from './consoleContext';

// =============================================================================
// ROUTE HELPERS
// =============================================================================

/**
 * Build a route path relative to the console root
 */
export function route(path: string): string {
  if (path.startsWith('/')) {
    return path;
  }
  return `${CONSOLE_ROOT}/${path}`;
}

/**
 * Build a customer console route
 */
export function customerRoute(path: string): string {
  return `${CUSTOMER_ROOT}/${path}`;
}

/**
 * Build a founder console route
 */
export function founderRoute(path: string): string {
  return `${FOUNDER_ROOT}/${path}`;
}

// =============================================================================
// PUBLIC ROUTES (No Auth Required)
// =============================================================================

export const PUBLIC_ROUTES = {
  login: '/login',
} as const;

// =============================================================================
// ONBOARDING ROUTES
// =============================================================================

export const ONBOARDING_ROUTES = {
  connect: '/onboarding/connect',
  safety: '/onboarding/safety',
  alerts: '/onboarding/alerts',
  verify: '/onboarding/verify',
  complete: '/onboarding/complete',
} as const;

// =============================================================================
// CUSTOMER CONSOLE ROUTES (4 distinct: /precus for preflight, /cus for prod)
// =============================================================================

export const CUSTOMER_ROUTES = {
  // Console root (environment-aware: /precus or /cus)
  root: CUSTOMER_ROOT,

  // Explicit roots for cross-environment navigation
  precusRoot: PRECUS_ROOT,    // /precus
  cusRoot: CUS_ROOT,          // /cus

  // L2.1 Domain routes
  overview: DOMAIN_ROOTS.overview,
  activity: DOMAIN_ROOTS.activity,
  incidents: DOMAIN_ROOTS.incidents,
  policies: DOMAIN_ROOTS.policies,
  logs: DOMAIN_ROOTS.logs,

  // Dynamic routes (with ID parameters)
  incidentDetail: (id: string) => `${DOMAIN_ROOTS.incidents}/${id}`,
  activityDetail: (id: string) => `${DOMAIN_ROOTS.activity}/${id}`,
  policyDetail: (id: string) => `${DOMAIN_ROOTS.policies}/${id}`,

  // Secondary navigation
  keys: SECONDARY_ROOTS.keys,
  integrations: SECONDARY_ROOTS.integrations,
  settings: SECONDARY_ROOTS.settings,
  account: SECONDARY_ROOTS.account,

  // Billing
  credits: IS_PREFLIGHT ? '/credits' : '/cus/credits',
} as const;

// =============================================================================
// FOUNDER CONSOLE ROUTES (4 distinct: /prefops for preflight, /fops for prod)
// =============================================================================

export const FOUNDER_ROUTES = {
  // Console root (environment-aware: /prefops or /fops)
  root: FOUNDER_ROOT,

  // Explicit roots for cross-environment navigation
  prefopsRoot: PREFOPS_ROOT,  // /prefops
  fopsRoot: FOPS_ROOT,        // /fops

  // Ops Console
  ops: FOUNDER_DOMAIN_ROOTS.ops,

  // Execution
  traces: FOUNDER_DOMAIN_ROOTS.traces,
  traceDetail: (runId: string) => `${FOUNDER_DOMAIN_ROOTS.traces}/${runId}`,
  workers: FOUNDER_DOMAIN_ROOTS.workers,
  workersConsole: `${FOUNDER_DOMAIN_ROOTS.workers}/console`,

  // Reliability
  recovery: FOUNDER_DOMAIN_ROOTS.recovery,

  // Integration
  integration: FOUNDER_DOMAIN_ROOTS.integration,
  integrationLoop: (incidentId: string) => `${FOUNDER_DOMAIN_ROOTS.integration}/loop/${incidentId}`,

  // Founder Tools
  timeline: FOUNDER_DOMAIN_ROOTS.timeline,
  controls: FOUNDER_DOMAIN_ROOTS.controls,
  replay: FOUNDER_DOMAIN_ROOTS.replay,
  replaySlice: (incidentId: string) => `${FOUNDER_DOMAIN_ROOTS.replay}/${incidentId}`,
  scenarios: FOUNDER_DOMAIN_ROOTS.scenarios,
  explorer: FOUNDER_DOMAIN_ROOTS.explorer,
  review: FOUNDER_DOMAIN_ROOTS.review,
  reviewAutoExecute: `${FOUNDER_DOMAIN_ROOTS.review}/auto-execute`,

  // Governance
  sba: FOUNDER_DOMAIN_ROOTS.sba,
} as const;

// =============================================================================
// NAVIGATION HELPERS
// =============================================================================

/**
 * Get the default route after authentication
 * - If onboarding not complete: onboarding
 * - If customer console: CUSTOMER_ROUTES.root
 * - If founder console: FOUNDER_ROUTES.root
 */
export function getPostAuthRoute(onboardingComplete: boolean): string {
  if (!onboardingComplete) {
    return ONBOARDING_ROUTES.connect;
  }
  return IS_CUSTOMER_CONSOLE ? CUSTOMER_ROUTES.root : FOUNDER_ROUTES.root;
}

/**
 * Get the root route for the current console
 */
export function getConsoleRoot(): string {
  return CONSOLE_ROOT;
}

/**
 * Get the catch-all redirect target
 * Used for unknown routes or 404s
 */
export function getCatchAllRoute(): string {
  return IS_CUSTOMER_CONSOLE ? CUSTOMER_ROUTES.overview : FOUNDER_ROUTES.ops;
}

// =============================================================================
// RE-EXPORTS (For convenience)
// =============================================================================

export {
  CONSOLE_ROOT,
  CUSTOMER_ROOT,
  FOUNDER_ROOT,
  // 4 distinct console roots
  PRECUS_ROOT,
  CUS_ROOT,
  PREFOPS_ROOT,
  FOPS_ROOT,
  // Domain roots
  DOMAIN_ROOTS,
  SECONDARY_ROOTS,
  FOUNDER_DOMAIN_ROOTS,
} from './consoleRoots';

export {
  IS_PREFLIGHT,
  IS_PRODUCTION,
  CONSOLE_KIND,
  IS_CUSTOMER_CONSOLE,
  IS_FOUNDER_CONSOLE,
  ENVIRONMENT_ID,
} from './consoleContext';
