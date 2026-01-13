/**
 * ProtectedRoute - Clerk-based route protection
 *
 * RULE-AUTH-UI-001: Clerk is the auth store
 * - Use useAuth() for authentication state
 * - No dual auth systems
 *
 * Reference: PIN-407, docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, useUser } from '@clerk/clerk-react';
import { PUBLIC_ROUTES, ONBOARDING_ROUTES } from '@/routing';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
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

  if (!isSignedIn) {
    // Redirect to login page, saving the current location
    return <Navigate to={PUBLIC_ROUTES.login} state={{ from: location }} replace />;
  }

  // Check onboarding status from Clerk user metadata
  // Treat as complete if metadata not set (graceful default)
  const onboardingComplete = user?.publicMetadata?.onboardingComplete !== false;

  // If authenticated but onboarding not complete, redirect to onboarding
  if (!onboardingComplete) {
    return <Navigate to={ONBOARDING_ROUTES.connect} replace />;
  }

  return <>{children}</>;
}
