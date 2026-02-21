/**
 * Auth Adapter Types — Provider-neutral auth interface
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Type definitions for the auth adapter boundary
 * Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
 * capability_id: CAP-006
 *
 * These types define the contract between the app and any auth provider
 * (Clerk or HOC Identity). All components consume these types, never
 * provider-specific types directly.
 */

/** Auth state machine — deterministic states with clear redirect rules */
export type AuthState =
  | 'anonymous'        // Not authenticated → redirect to /login
  | 'authenticating'   // In progress → show loading, no redirect
  | 'authenticated'    // Active session → proceed
  | 'expired'          // Session expired → redirect to /login?reason=expired
  | 'unauthorized';    // Forbidden → redirect to /403

/** Authenticated user info (provider-neutral) */
export interface AuthUser {
  userId: string;
  email?: string;
  tenantId?: string;
  tier?: string;
  displayName?: string;
}

/** Return type of the useAuth() hook */
export interface UseAuthReturn {
  /** Current auth state */
  state: AuthState;
  /** Whether the user is authenticated */
  isAuthenticated: boolean;
  /** Whether auth state is still loading */
  isLoading: boolean;
  /** Authenticated user info (null when not authenticated) */
  user: AuthUser | null;
  /** Get current access token for API calls (handles refresh) */
  getAccessToken(): Promise<string | null>;
  /** Sign in with email + password */
  signIn(email: string, password: string): Promise<void>;
  /** Sign out and revoke session */
  signOut(): Promise<void>;
  /** Switch active tenant */
  switchTenant(tenantId: string): Promise<void>;
  /** Error message if auth failed */
  error?: string;
}

/** Auth adapter interface — implemented by each provider */
export interface AuthAdapter {
  /** Provider identifier */
  readonly providerType: 'clerk' | 'hoc_identity';
  /** Initialize the adapter (called once at mount) */
  initialize(): Promise<void>;
  /** Get current auth state */
  getState(): AuthState;
  /** Get current user */
  getUser(): AuthUser | null;
  /** Get access token */
  getAccessToken(): Promise<string | null>;
  /** Sign in */
  signIn(email: string, password: string): Promise<void>;
  /** Sign out */
  signOut(): Promise<void>;
  /** Switch tenant */
  switchTenant(tenantId: string): Promise<void>;
  /** Subscribe to state changes */
  onStateChange(callback: (state: AuthState) => void): () => void;
}
