/**
 * ConsoleIsolationGuard — Hard Enforcement for Console Isolation
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: render (every route change)
 *   Execution: sync
 * Role: BLOCK navigation that escapes the current console's root
 * Reference: PIN-387, Runtime Console Isolation
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (deliberate changes only)
 * Last Frozen: 2026-01-11
 *
 * DIFFERENCE FROM RouteGuardAssertion:
 * - RouteGuardAssertion: Logs warnings (advisory)
 * - ConsoleIsolationGuard: Redirects or throws (enforcement)
 *
 * USAGE:
 * Place at the top of your protected layout:
 *
 *   <ConsoleIsolationGuard>
 *     <Routes>...</Routes>
 *   </ConsoleIsolationGuard>
 *
 * BEHAVIOR:
 * - If pathname doesn't start with CONSOLE_ROOT:
 *   1. Redirects to the correct console root
 *   2. Logs a console error for debugging
 * - This catches:
 *   - Stale links (e.g., bookmark to /precus/* in production)
 *   - Manual URL edits
 *   - NavLink misuse
 *   - Cross-console navigation attempts
 *
 * EXEMPT PATHS:
 * - /login (public)
 * - /onboarding/* (pre-auth)
 * - /health (system)
 * - / (root, will redirect)
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { IS_PREFLIGHT, IS_PRODUCTION } from './consoleContext';
import { CONSOLE_ROOT } from './consoleRoots';

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Paths that are exempt from console isolation.
 * These are public or system routes that don't belong to any console.
 */
const EXEMPT_PATHS = [
  '/login',
  '/onboarding',
  '/health',
  '/credits',
  '/',  // Root path (will redirect via router)
] as const;

/**
 * Whether to enforce isolation.
 * - Always enforce in production (safety)
 * - Enforce in preflight (catch issues early)
 */
const ENFORCEMENT_ENABLED = true; // Always enforce

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Check if a path is exempt from console isolation
 */
function isExemptPath(pathname: string): boolean {
  return EXEMPT_PATHS.some(exempt => pathname === exempt || pathname.startsWith(exempt + '/'));
}

/**
 * Check if pathname is within the current console's namespace
 */
function isWithinConsole(pathname: string): boolean {
  // Exempt paths are always within bounds
  if (isExemptPath(pathname)) {
    return true;
  }

  // Must start with CONSOLE_ROOT
  return pathname.startsWith(CONSOLE_ROOT) || pathname.startsWith(CONSOLE_ROOT + '/');
}

// ============================================================================
// COMPONENT
// ============================================================================

interface ConsoleIsolationGuardProps {
  children: ReactNode;
  /** If true, throws error instead of redirecting (for testing) */
  throwOnViolation?: boolean;
}

/**
 * ConsoleIsolationGuard Component
 *
 * Enforces console isolation by redirecting any navigation
 * that escapes the current console's root path.
 *
 * INVARIANT:
 * Within this guard, all paths MUST start with CONSOLE_ROOT
 * (e.g., /precus/* in preflight customer, /cus/* in production).
 *
 * This is the final line of defense against cross-console leakage.
 */
export function ConsoleIsolationGuard({
  children,
  throwOnViolation = false,
}: ConsoleIsolationGuardProps): ReactNode {
  const location = useLocation();
  const navigate = useNavigate();
  const hasLoggedViolation = useRef(false);

  useEffect(() => {
    if (!ENFORCEMENT_ENABLED) {
      return;
    }

    const isValid = isWithinConsole(location.pathname);

    if (!isValid) {
      // Log the violation
      if (!hasLoggedViolation.current) {
        console.error(
          '\n' +
          '╔═══════════════════════════════════════════════════════════════╗\n' +
          '║           CONSOLE ISOLATION VIOLATION (BLOCKED)               ║\n' +
          '╚═══════════════════════════════════════════════════════════════╝\n' +
          '\n' +
          `Attempted path:  ${location.pathname}\n` +
          `Expected root:   ${CONSOLE_ROOT}\n` +
          `Environment:     ${IS_PREFLIGHT ? 'preflight' : 'production'}\n` +
          '\n' +
          'This navigation was blocked because it escapes the console root.\n' +
          'Possible causes:\n' +
          '  - Stale bookmark from different environment\n' +
          '  - Manual URL edit\n' +
          '  - Hardcoded path in code (should use @/routing)\n' +
          '  - Cross-console NavLink\n' +
          '\n' +
          `Redirecting to: ${CONSOLE_ROOT}\n` +
          '\n' +
          'Reference: PIN-387, ConsoleIsolationGuard\n' +
          '═══════════════════════════════════════════════════════════════════\n'
        );
        hasLoggedViolation.current = true;
      }

      if (throwOnViolation) {
        throw new Error(
          `Console isolation violation: "${location.pathname}" does not start with "${CONSOLE_ROOT}"`
        );
      }

      // Redirect to console root
      navigate(CONSOLE_ROOT, { replace: true });
    } else {
      // Reset the violation flag when we're back in bounds
      hasLoggedViolation.current = false;
    }
  }, [location.pathname, navigate, throwOnViolation]);

  return <>{children}</>;
}

export default ConsoleIsolationGuard;
