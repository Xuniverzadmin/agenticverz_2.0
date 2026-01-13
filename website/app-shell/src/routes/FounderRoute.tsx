/**
 * FounderRoute - Authority-enforced route guard for Founder Console
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Auth guard for founder console routes (/prefops/* and /fops/*)
 * Reference: PIN-352, Routing Authority Model; PIN-318
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (deliberate changes only)
 * Last Frozen: 2026-01-08
 *
 * All founder routes are under /prefops/* (preflight) or /fops/* (production):
 * - ops/*        - Ops console
 * - traces/*     - Execution traces
 * - workers/*    - Worker management
 * - recovery     - Recovery candidates
 * - integration  - Learning pipeline
 * - timeline     - Decision timeline
 * - controls     - Kill-switch (FOUNDER-only)
 * - replay/*     - Replay viewer
 * - scenarios    - Cost simulation
 * - explorer     - Cross-tenant explorer
 * - review       - Founder review
 * - sba          - SBA inspector
 *
 * This component enforces:
 * - Authentication (must be logged in)
 * - Audience check (must have aud="fops" token)
 * - Optional role check (FOUNDER or OPERATOR)
 *
 * If a customer token (aud="console") attempts to access a founder route,
 * they are redirected to customer console (not /login) to prevent route discovery.
 */

/**
 * FounderRoute - Backend-verified founder route protection
 *
 * RULE-AUTH-UI-001: Clerk is the auth store; backend is authority on actor_type
 * - Use useAuth() for authentication state
 * - Use useSessionContext() for verified actor_type (customer/founder)
 * - Frontend reads authorization facts, never derives them
 *
 * Reference: PIN-409, docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, useUser } from '@clerk/clerk-react';
import { useSessionContext } from '@/hooks/useSessionContext';
import {
  PUBLIC_ROUTES,
  ONBOARDING_ROUTES,
  CUSTOMER_ROUTES,
  FOUNDER_ROUTES,
} from '@/routing';

// Founder roles (mirrors backend FounderRole enum)
export type FounderRole = 'FOUNDER' | 'OPERATOR';

interface FounderRouteProps {
  children: React.ReactNode;
  /** Optional: Restrict to specific founder roles */
  allowedRoles?: FounderRole[];
}

export function FounderRoute({ children, allowedRoles }: FounderRouteProps) {
  const { isSignedIn, isLoaded } = useAuth();
  const { user: clerkUser } = useUser();
  // PIN-409: Get verified actor_type from backend session context
  const { isFounder, isLoading: sessionLoading } = useSessionContext();
  const location = useLocation();

  // Wait for Clerk to load
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  // Check 1: Must be authenticated
  if (!isSignedIn) {
    return <Navigate to={PUBLIC_ROUTES.login} state={{ from: location }} replace />;
  }

  // Wait for session context to load
  if (sessionLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-gray-400">Verifying access...</div>
      </div>
    );
  }

  // Check 2: Must have completed onboarding
  // Use Clerk user metadata (treat as complete if not set)
  const onboardingComplete = clerkUser?.publicMetadata?.onboardingComplete !== false;
  if (!onboardingComplete) {
    return <Navigate to={ONBOARDING_ROUTES.connect} replace />;
  }

  // Check 3: Must be a founder (verified by backend)
  // PIN-409: actor_type from backend is the authority, not frontend-derived audience
  if (!isFounder) {
    // Redirect to customer console, not login
    // This prevents route discovery (customer sees their console, not an error)
    return <Navigate to={CUSTOMER_ROUTES.root} replace />;
  }

  // Check 4: Optional role restriction
  const userRole = (clerkUser?.publicMetadata?.role as FounderRole) || undefined;
  if (allowedRoles && userRole) {
    if (!allowedRoles.includes(userRole)) {
      // User is founder but lacks required role
      // Redirect to main founder page (ops console)
      return <Navigate to={FOUNDER_ROUTES.ops} replace />;
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
  const { isSignedIn, isLoaded } = useAuth();
  const { user: clerkUser } = useUser();
  // PIN-409: Get verified actor_type from backend session context
  const { isCustomer, isFounder, isLoading: sessionLoading } = useSessionContext();
  const location = useLocation();

  // Wait for Clerk to load
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  // Check 1: Must be authenticated
  if (!isSignedIn) {
    return <Navigate to={PUBLIC_ROUTES.login} state={{ from: location }} replace />;
  }

  // Wait for session context to load
  if (sessionLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-gray-400">Verifying access...</div>
      </div>
    );
  }

  // Check 2: Must have completed onboarding
  // Use Clerk user metadata (treat as complete if not set)
  const onboardingComplete = clerkUser?.publicMetadata?.onboardingComplete !== false;
  if (!onboardingComplete) {
    return <Navigate to={ONBOARDING_ROUTES.connect} replace />;
  }

  // Check 3: Must be a customer or founder (founders have superuser access)
  // PIN-409: actor_type from backend is the authority
  if (!isCustomer && !isFounder) {
    // Unknown actor type (e.g., machine) - redirect to login
    return <Navigate to={PUBLIC_ROUTES.login} replace />;
  }

  // Check 4: Optional role restriction (only for customers)
  const userRole = (clerkUser?.publicMetadata?.role as CustomerRole) || undefined;
  if (allowedRoles && userRole && isCustomer) {
    if (!allowedRoles.includes(userRole)) {
      // User lacks required role - redirect to overview
      return <Navigate to={CUSTOMER_ROUTES.overview} replace />;
    }
  }

  return <>{children}</>;
}
