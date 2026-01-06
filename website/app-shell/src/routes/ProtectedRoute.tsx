import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login page, saving the current location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If authenticated but onboarding not complete, redirect to onboarding
  if (!onboardingComplete) {
    return <Navigate to="/onboarding/connect" replace />;
  }

  return <>{children}</>;
}
