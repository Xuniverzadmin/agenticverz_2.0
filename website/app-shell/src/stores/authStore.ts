/**
 * App State Store (formerly authStore)
 *
 * RULE-AUTH-UI-001: Clerk is the auth store
 * This store holds APP-SPECIFIC state only:
 * - tenantId: Current tenant context (used by API key fallback path)
 *
 * For AUTHENTICATION state, use Clerk hooks:
 * - useAuth() for isSignedIn, getToken
 * - useUser() for user info
 * - useClerk().signOut() for logout
 *
 * For AUTHORIZATION facts (actor_type, lifecycle), use:
 * - useSessionContext() from @/hooks/useSessionContext
 *
 * Reference: PIN-409, docs/architecture/FRONTEND_AUTH_CONTRACT.md
 *
 * DEPRECATION NOTICE (PIN-409):
 * =============================
 * The following fields are DEPRECATED and should NOT be used for
 * new code. They exist only for the transitional API key fallback:
 *
 * - audience: Use useSessionContext().isFounder / isCustomer instead
 * - isFounder: Use useSessionContext().isFounder instead
 * - token, refreshToken, user, isAuthenticated: Use Clerk hooks
 *
 * These fields will be removed once API key login is deprecated.
 * See AIConsoleApp.tsx for the deprecation plan.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// PIN-318: Authority Model - Token Audience
export type TokenAudience = 'console' | 'fops';

/** @deprecated Use Clerk useUser() instead */
interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  oauth_provider?: string;
  email_verified?: boolean;
}

interface AuthState {
  // === DEPRECATED (use Clerk instead) ===
  /** @deprecated Use Clerk getToken() instead */
  token: string | null;
  /** @deprecated No longer used */
  refreshToken: string | null;
  /** @deprecated Use Clerk useUser() instead */
  user: User | null;
  /** @deprecated Use Clerk useAuth().isSignedIn instead */
  isAuthenticated: boolean;
  /** @deprecated Use Clerk user metadata instead */
  onboardingComplete: boolean;
  /** @deprecated Use Clerk user metadata instead */
  onboardingStep: number;

  // === APP-SPECIFIC STATE (still valid) ===
  /** Current tenant ID for API calls */
  tenantId: string | null;
  /** Token audience for route guards (console/fops) */
  audience: TokenAudience | null;
  /** Founder status for route guards */
  isFounder: boolean;

  // === SETTERS ===
  /** @deprecated Only used for API key fallback path */
  setTokens: (token: string, refreshToken: string) => void;
  /** @deprecated Use Clerk useUser() instead */
  setUser: (user: User) => void;
  /** Set tenant ID for API calls */
  setTenant: (tenantId: string) => void;
  /** @deprecated Use Clerk user metadata instead */
  setOnboardingComplete: (complete: boolean) => void;
  /** @deprecated Use Clerk user metadata instead */
  setOnboardingStep: (step: number) => void;
  /** Set token audience for route guards */
  setAudience: (audience: TokenAudience) => void;
  /** Set founder status for route guards */
  setIsFounder: (isFounder: boolean) => void;
  /** @deprecated Use Clerk signOut() instead */
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
