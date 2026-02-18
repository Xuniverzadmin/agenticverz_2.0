/**
 * RouteGuardAssertion — Runtime Route Validation (Dev/Preflight Only)
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: render
 *   Execution: sync
 * Role: Assert current pathname matches one of the 4 distinct console roots
 * Reference: PIN-352, Routing Authority Model
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (deliberate changes only)
 * Last Frozen: 2026-01-08
 *
 * USAGE:
 * Place at the top of your App component (inside Router):
 *
 *   <Router>
 *     <RouteGuardAssertion />
 *     <Routes>...</Routes>
 *   </Router>
 *
 * BEHAVIOR:
 * - In production: Does nothing (no-op)
 * - In dev/preflight: Logs warning if pathname violates routing authority
 * - Does NOT block render (advisory only)
 *
 * This gives early warning if hardcoded routes slip through.
 *
 * ROUTE AUTHORITY MODEL (4 DISTINCT CONSOLES):
 * ┌──────────────┬─────────────┬───────────┐
 * │ Console Kind │ Environment │ Root Path │
 * ├──────────────┼─────────────┼───────────┤
 * │ customer     │ preflight   │ /precus   │
 * ├──────────────┼─────────────┼───────────┤
 * │ customer     │ production  │ /cus      │
 * ├──────────────┼─────────────┼───────────┤
 * │ founder      │ preflight   │ /prefops  │
 * ├──────────────┼─────────────┼───────────┤
 * │ founder      │ production  │ /fops     │
 * └──────────────┴─────────────┴───────────┘
 */

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { IS_PREFLIGHT, IS_CUSTOMER_CONSOLE, IS_FOUNDER_CONSOLE } from './consoleContext';
import {
  CONSOLE_ROOT,
  CUSTOMER_ROOT,
  FOUNDER_ROOT,
  PRECUS_ROOT,
  CUS_ROOT,
  PREFOPS_ROOT,
  FOPS_ROOT,
} from './consoleRoots';

// Only active in development or preflight mode
const IS_DEV = import.meta.env.DEV;
const ASSERTION_ENABLED = IS_DEV || IS_PREFLIGHT;

// =============================================================================
// VALID CONSOLE ROOTS (4 DISTINCT - NO MIXING)
// =============================================================================

/**
 * The 4 valid console root paths.
 * Any path not starting with one of these (except exempt paths) is a violation.
 */
const VALID_CONSOLE_ROOTS = [
  PRECUS_ROOT,   // /precus (preflight customer)
  CUS_ROOT,      // /cus (production customer)
  PREFOPS_ROOT,  // /prefops (preflight founder)
  FOPS_ROOT,     // /fops (production founder)
] as const;

/**
 * Paths that are exempt from console root assertion.
 * These are public or system routes that don't belong to any console.
 */
const EXEMPT_PATHS = [
  '/login',
  '/onboarding',
  '/health',
  '/credits',  // Shared credits page
  '/stagetest', // Stagetest evidence console
  '/page',      // Stagetest scaffold pages
] as const;

// =============================================================================
// VALIDATION LOGIC
// =============================================================================

/**
 * Check if a path is exempt from console root validation
 */
function isExemptPath(pathname: string): boolean {
  return EXEMPT_PATHS.some(exempt => pathname.startsWith(exempt));
}

/**
 * Check if pathname starts with any valid console root
 */
function startsWithValidRoot(pathname: string): string | null {
  for (const root of VALID_CONSOLE_ROOTS) {
    if (pathname.startsWith(root)) {
      return root;
    }
  }
  return null;
}

/**
 * Get the expected console root based on current context
 */
function getExpectedRoot(): string {
  if (IS_CUSTOMER_CONSOLE) {
    return IS_PREFLIGHT ? PRECUS_ROOT : CUS_ROOT;
  }
  if (IS_FOUNDER_CONSOLE) {
    return IS_PREFLIGHT ? PREFOPS_ROOT : FOPS_ROOT;
  }
  // Fallback (should never happen)
  return CUS_ROOT;
}

/**
 * Validate pathname against the 4-console routing authority model.
 *
 * Rules:
 * 1. Exempt paths are always valid
 * 2. Root path '/' is valid (will redirect)
 * 3. Path must start with one of the 4 valid console roots
 * 4. Path should match the expected root for the current context
 */
function validatePathname(pathname: string): { valid: boolean; message?: string } {
  // Rule 1: Exempt paths are always valid
  if (isExemptPath(pathname)) {
    return { valid: true };
  }

  // Rule 2: Root path is valid (will redirect)
  if (pathname === '/') {
    return { valid: true };
  }

  // Rule 3: Check if path starts with any valid console root
  const matchedRoot = startsWithValidRoot(pathname);

  if (!matchedRoot) {
    return {
      valid: false,
      message: `Path "${pathname}" does not start with a valid console root.\n` +
        `Valid roots: ${VALID_CONSOLE_ROOTS.join(', ')}`,
    };
  }

  // Rule 4: Check if path matches the expected root for current context
  const expectedRoot = getExpectedRoot();

  if (matchedRoot !== expectedRoot) {
    // This is a cross-console navigation - might be intentional
    // Log as warning but don't block (could be legitimate cross-console link)
    return {
      valid: true, // Allow but log
      message: `Cross-console navigation detected.\n` +
        `Current context expects "${expectedRoot}" but path uses "${matchedRoot}".\n` +
        `This may be intentional (cross-console link) or a bug.`,
    };
  }

  return { valid: true };
}

// =============================================================================
// COMPONENT
// =============================================================================

/**
 * RouteGuardAssertion Component
 *
 * Renders nothing but validates routing authority at runtime.
 * Only active in dev/preflight mode.
 *
 * INVARIANTS:
 * - All paths must start with one of 4 valid console roots
 * - /precus/* for preflight customer (L2.1 projections)
 * - /cus/* for production customer (AIConsoleApp)
 * - /prefops/* for preflight founder
 * - /fops/* for production founder
 * - NO mixing or leaking between console namespaces
 */
export function RouteGuardAssertion(): null {
  const location = useLocation();

  useEffect(() => {
    if (!ASSERTION_ENABLED) {
      return;
    }

    const result = validatePathname(location.pathname);

    if (!result.valid && result.message) {
      // Log error for violations
      console.error(
        '\n' +
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n' +
        '🚫 ROUTING AUTHORITY VIOLATION\n' +
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n' +
        result.message + '\n' +
        '\n' +
        'Context:\n' +
        `  - Pathname: ${location.pathname}\n` +
        `  - IS_PREFLIGHT: ${IS_PREFLIGHT}\n` +
        `  - IS_CUSTOMER_CONSOLE: ${IS_CUSTOMER_CONSOLE}\n` +
        `  - IS_FOUNDER_CONSOLE: ${IS_FOUNDER_CONSOLE}\n` +
        `  - Expected root: ${getExpectedRoot()}\n` +
        '\n' +
        'Valid Console Roots:\n' +
        `  - /precus   (preflight customer)\n` +
        `  - /cus      (production customer)\n` +
        `  - /prefops  (preflight founder)\n` +
        `  - /fops     (production founder)\n` +
        '\n' +
        'Fix: Use @/routing imports, not hardcoded paths.\n' +
        'Reference: PIN-352, src/routing/ROUTING_AUTHORITY_LOCK.md\n' +
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
      );
    } else if (result.message) {
      // Log warning for cross-console navigation (valid but noteworthy)
      console.warn(
        '\n' +
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n' +
        '⚠️  CROSS-CONSOLE NAVIGATION\n' +
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n' +
        result.message + '\n' +
        `  - Pathname: ${location.pathname}\n` +
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
      );
    }
  }, [location.pathname]);

  // Render nothing - this is purely for side effects
  return null;
}

export default RouteGuardAssertion;
