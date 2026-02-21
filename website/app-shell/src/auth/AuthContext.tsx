/**
 * AuthContext — Provider-neutral auth React context
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: React context + provider wrapping the auth adapter boundary
 * Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
 * capability_id: CAP-006
 *
 * This context provides the useAuth() hook to all components.
 * The actual auth behavior is delegated to an AuthAdapter implementation
 * (Clerk or HOC Identity), selected at build time via VITE_AUTH_PROVIDER.
 *
 * SCAFFOLD: Currently a passthrough — Clerk adapter wraps existing
 * Clerk hooks. HOC Identity adapter returns scaffold stubs.
 */

import { createContext, useContext, useMemo, type ReactNode } from 'react';
import type { UseAuthReturn, AuthAdapter } from './types';

// =============================================================================
// Context
// =============================================================================

const AuthContext = createContext<UseAuthReturn | null>(null);

// =============================================================================
// useAuth() hook — the public API
// =============================================================================

/**
 * Provider-neutral auth hook.
 *
 * Components use this instead of Clerk's useAuth() directly.
 * During scaffold phase, this delegates to the Clerk adapter which
 * wraps the existing Clerk hooks.
 *
 * Usage:
 *   const { isAuthenticated, user, getAccessToken, signOut } = useAuth();
 */
export function useHocAuth(): UseAuthReturn {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useHocAuth() must be used within <HocAuthProvider>');
  }
  return ctx;
}

// =============================================================================
// HocAuthProvider — wraps children with auth context
// =============================================================================

interface HocAuthProviderProps {
  adapter: AuthAdapter;
  children: ReactNode;
}

/**
 * HocAuthProvider — Wraps children with the auth adapter context.
 *
 * Usage in App.tsx (future):
 *   <HocAuthProvider adapter={clerkAdapter}>
 *     <AppRoutes />
 *   </HocAuthProvider>
 *
 * SCAFFOLD: Not yet wired into App.tsx. The existing ClerkProvider +
 * ClerkAuthSync remain in place as the default path.
 */
export function HocAuthProvider({ adapter, children }: HocAuthProviderProps) {
  const value: UseAuthReturn = useMemo(
    () => ({
      state: adapter.getState(),
      isAuthenticated: adapter.getState() === 'authenticated',
      isLoading: adapter.getState() === 'authenticating',
      user: adapter.getUser(),
      getAccessToken: () => adapter.getAccessToken(),
      signIn: (email: string, password: string) => adapter.signIn(email, password),
      signOut: () => adapter.signOut(),
      switchTenant: (tenantId: string) => adapter.switchTenant(tenantId),
    }),
    [adapter],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
