import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// PIN-318: Authority Model - Token Audience
export type TokenAudience = 'console' | 'fops';

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
  // PIN-318: Authority Model additions
  audience: TokenAudience | null;
  isFounder: boolean;

  setTokens: (token: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  setTenant: (tenantId: string) => void;
  setOnboardingComplete: (complete: boolean) => void;
  setOnboardingStep: (step: number) => void;
  // PIN-318: Authority setters
  setAudience: (audience: TokenAudience) => void;
  setIsFounder: (isFounder: boolean) => void;
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
      // PIN-318: Authority Model defaults
      audience: null,
      isFounder: false,

      setTokens: (token, refreshToken) =>
        set({ token, refreshToken, isAuthenticated: true }),

      setUser: (user) => set({ user }),

      setTenant: (tenantId) => set({ tenantId }),

      setOnboardingComplete: (complete) => set({ onboardingComplete: complete }),

      setOnboardingStep: (step) => set({ onboardingStep: step }),

      // PIN-318: Authority setters
      setAudience: (audience) => set({ audience }),

      setIsFounder: (isFounder) => set({ isFounder }),

      logout: () =>
        set({
          token: null,
          refreshToken: null,
          tenantId: null,
          user: null,
          isAuthenticated: false,
          onboardingComplete: false,
          onboardingStep: 0,
          // PIN-318: Reset authority on logout
          audience: null,
          isFounder: false,
        }),
    }),
    {
      name: 'aos-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        tenantId: state.tenantId,
        // FIX: Persist user and isAuthenticated for session persistence (PIN-370)
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        onboardingComplete: state.onboardingComplete,
        onboardingStep: state.onboardingStep,
        // PIN-318: Persist authority
        audience: state.audience,
        isFounder: state.isFounder,
      }),
    }
  )
);
