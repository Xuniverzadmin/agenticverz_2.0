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

  // Already completed onboarding - redirect to dashboard
  if (onboardingComplete) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
