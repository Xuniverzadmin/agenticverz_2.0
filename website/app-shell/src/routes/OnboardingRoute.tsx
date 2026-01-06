import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface OnboardingRouteProps {
  children: React.ReactNode;
}

export function OnboardingRoute({ children }: OnboardingRouteProps) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();
  const location = useLocation();

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Already completed onboarding - redirect to customer console
  // PIN-318: Fixed ghost route /dashboard → /guard
  if (onboardingComplete) {
    return <Navigate to="/guard" replace />;
  }

  return <>{children}</>;
}
