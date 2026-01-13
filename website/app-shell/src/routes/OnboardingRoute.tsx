/**
 * OnboardingRoute - Clerk-based onboarding route protection
 *
 * RULE-AUTH-UI-001: Clerk is the auth store
 * - Use useAuth() for authentication state
 * - Use user metadata for onboarding status
 *
 * Reference: PIN-407, docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, useUser } from '@clerk/clerk-react';
import { PUBLIC_ROUTES, CUSTOMER_ROUTES } from '@/routing';

interface OnboardingRouteProps {
  children: React.ReactNode;
}

export function OnboardingRoute({ children }: OnboardingRouteProps) {
  const { isSignedIn, isLoaded } = useAuth();
  const { user } = useUser();
  const location = useLocation();

  // Wait for Clerk to load
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  // Not authenticated - redirect to login
  if (!isSignedIn) {
    return <Navigate to={PUBLIC_ROUTES.login} state={{ from: location }} replace />;
  }

  // Check onboarding status from Clerk user metadata
  // Treat as complete if metadata not set (graceful default)
  const onboardingComplete = user?.publicMetadata?.onboardingComplete !== false;

  // Already completed onboarding - redirect to customer console
  // PIN-352: Environment-aware routing via routing authority
  if (onboardingComplete) {
    return <Navigate to={CUSTOMER_ROUTES.root} replace />;
  }

  return <>{children}</>;
}
