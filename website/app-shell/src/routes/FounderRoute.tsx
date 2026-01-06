/**
 * FounderRoute - Authority-enforced route guard for Founder Console
 *
 * PIN-318: Phase 1.2 Authority Hardening
 *
 * All founder routes are under /fops/* namespace:
 * - /fops/ops/*        - Ops console
 * - /fops/traces/*     - Execution traces
 * - /fops/workers/*    - Worker management
 * - /fops/recovery     - Recovery candidates
 * - /fops/integration  - Learning pipeline
 * - /fops/timeline     - Decision timeline
 * - /fops/controls     - Kill-switch (FOUNDER-only)
 * - /fops/replay/*     - Replay viewer
 * - /fops/scenarios    - Cost simulation
 * - /fops/explorer     - Cross-tenant explorer
 * - /fops/sba          - SBA inspector
 *
 * This component enforces:
 * - Authentication (must be logged in)
 * - Audience check (must have aud="fops" token)
 * - Optional role check (FOUNDER or OPERATOR)
 *
 * If a customer token (aud="console") attempts to access a founder route,
 * they are redirected to /guard (not /login) to prevent route discovery.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore, TokenAudience } from '@/stores/authStore';

// Founder roles (mirrors backend FounderRole enum)
export type FounderRole = 'FOUNDER' | 'OPERATOR';

interface FounderRouteProps {
  children: React.ReactNode;
  /** Optional: Restrict to specific founder roles */
  allowedRoles?: FounderRole[];
}

export function FounderRoute({ children, allowedRoles }: FounderRouteProps) {
  const { isAuthenticated, onboardingComplete, audience, isFounder, user } = useAuthStore();
  const location = useLocation();

  // Check 1: Must be authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check 2: Must have completed onboarding
  if (!onboardingComplete) {
    return <Navigate to="/onboarding/connect" replace />;
  }

  // Check 3: Must have founder audience (aud="fops") or be marked as founder
  // PIN-318: Explicit audience check - customer tokens (aud="console") are denied
  if (audience !== 'fops' && !isFounder) {
    // Redirect to customer console, not login
    // This prevents route discovery (customer sees their console, not an error)
    return <Navigate to="/guard" replace />;
  }

  // Check 4: Optional role restriction
  if (allowedRoles && user?.role) {
    const userRole = user.role as FounderRole;
    if (!allowedRoles.includes(userRole)) {
      // User is founder but lacks required role
      // Redirect to main founder page (ops console)
      return <Navigate to="/fops/ops" replace />;
    }
  }

  return <>{children}</>;
}

/**
 * CustomerRoute - Authority-enforced route guard for Customer Console
 *
 * This is a convenience wrapper that explicitly marks routes as customer-only.
 * Currently equivalent to ProtectedRoute but with explicit audience documentation.
 */

// Customer roles (mirrors backend CustomerRole enum)
export type CustomerRole = 'OWNER' | 'ADMIN' | 'DEV' | 'VIEWER';

interface CustomerRouteProps {
  children: React.ReactNode;
  /** Optional: Restrict to specific customer roles */
  allowedRoles?: CustomerRole[];
}

export function CustomerRoute({ children, allowedRoles }: CustomerRouteProps) {
  const { isAuthenticated, onboardingComplete, audience, user } = useAuthStore();
  const location = useLocation();

  // Check 1: Must be authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check 2: Must have completed onboarding
  if (!onboardingComplete) {
    return <Navigate to="/onboarding/connect" replace />;
  }

  // Check 3: Audience check
  // Founders (aud="fops") CAN access customer routes (superuser access)
  // Customers (aud="console") can only access customer routes
  // This is intentional - founders may need to see customer view
  if (audience !== 'console' && audience !== 'fops') {
    // Unknown audience - redirect to login
    return <Navigate to="/login" replace />;
  }

  // Check 4: Optional role restriction (only for customer tokens)
  if (allowedRoles && user?.role && audience === 'console') {
    const userRole = user.role as CustomerRole;
    if (!allowedRoles.includes(userRole)) {
      // User lacks required role - redirect to overview
      return <Navigate to="/guard/overview" replace />;
    }
  }

  return <>{children}</>;
}
