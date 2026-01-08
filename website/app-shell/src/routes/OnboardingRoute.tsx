import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { PUBLIC_ROUTES, CUSTOMER_ROUTES } from '@/routing';

interface OnboardingRouteProps {
  children: React.ReactNode;
}

export function OnboardingRoute({ children }: OnboardingRouteProps) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();
  const location = useLocation();

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return <Navigate to={PUBLIC_ROUTES.login} state={{ from: location }} replace />;
  }

  // Already completed onboarding - redirect to customer console
  // PIN-352: Environment-aware routing via routing authority
  if (onboardingComplete) {
    return <Navigate to={CUSTOMER_ROUTES.root} replace />;
  }

  return <>{children}</>;
}
