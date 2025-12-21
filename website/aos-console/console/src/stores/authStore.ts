import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  oauth_provider?: string;
  email_verified?: boolean;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  tenantId: string | null;
  user: User | null;
  isAuthenticated: boolean;
  onboardingComplete: boolean;
  onboardingStep: number;

  setTokens: (token: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  setTenant: (tenantId: string) => void;
  setOnboardingComplete: (complete: boolean) => void;
  setOnboardingStep: (step: number) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      tenantId: null,
      user: null,
      isAuthenticated: false,
      onboardingComplete: false,
      onboardingStep: 0,

      setTokens: (token, refreshToken) =>
        set({ token, refreshToken, isAuthenticated: true }),

      setUser: (user) => set({ user }),

      setTenant: (tenantId) => set({ tenantId }),

      setOnboardingComplete: (complete) => set({ onboardingComplete: complete }),

      setOnboardingStep: (step) => set({ onboardingStep: step }),

      logout: () =>
        set({
          token: null,
          refreshToken: null,
          tenantId: null,
          user: null,
          isAuthenticated: false,
          onboardingComplete: false,
          onboardingStep: 0,
        }),
    }),
    {
      name: 'aos-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        tenantId: state.tenantId,
        onboardingComplete: state.onboardingComplete,
        onboardingStep: state.onboardingStep,
      }),
    }
  )
);
