/**
 * Routing Module — Public API
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Single export point for ALL routing-related values
 * Reference: PIN-352, Routing Authority Model
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (deliberate changes only)
 * Last Frozen: 2026-01-08
 *
 * This is the ONLY import point for routing-related values.
 * All components MUST import from '@/routing' (not individual files).
 */

// Context
export {
  IS_PREFLIGHT,
  IS_PRODUCTION,
  CONSOLE_KIND,
  IS_CUSTOMER_CONSOLE,
  IS_FOUNDER_CONSOLE,
  ENVIRONMENT_LABEL,
  CONSOLE_LABEL,
  ENVIRONMENT_ID,
} from './consoleContext';

// Roots (4 distinct consoles)
export {
  CONSOLE_ROOT,
  CUSTOMER_ROOT,
  FOUNDER_ROOT,
  // Explicit console roots
  PRECUS_ROOT,      // /precus (preflight customer)
  CUS_ROOT,         // /cus (production customer)
  PREFOPS_ROOT,     // /prefops (preflight founder)
  FOPS_ROOT,        // /fops (production founder)
  // Domain roots
  DOMAIN_ROOTS,
  SECONDARY_ROOTS,
  FOUNDER_DOMAIN_ROOTS,
} from './consoleRoots';

// Routes
export {
  PUBLIC_ROUTES,
  ONBOARDING_ROUTES,
  CUSTOMER_ROUTES,
  FOUNDER_ROUTES,
  route,
  customerRoute,
  founderRoute,
  getPostAuthRoute,
  getConsoleRoot,
  getCatchAllRoute,
} from './routes';

// Types
export type { ConsoleKind } from './consoleContext';
export type { DomainKey, SecondaryKey } from './consoleRoots';

// Runtime Assertion (dev/preflight only)
export { RouteGuardAssertion } from './RouteGuardAssertion';

// Console Isolation Guard (hard enforcement)
export { ConsoleIsolationGuard } from './ConsoleIsolationGuard';
