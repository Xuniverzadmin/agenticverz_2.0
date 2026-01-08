import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { PUBLIC_ROUTES, ONBOARDING_ROUTES } from '@/routing';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login page, saving the current location
    return <Navigate to={PUBLIC_ROUTES.login} state={{ from: location }} replace />;
  }

  // If authenticated but onboarding not complete, redirect to onboarding
  if (!onboardingComplete) {
    return <Navigate to={ONBOARDING_ROUTES.connect} replace />;
  }

  return <>{children}</>;
}
