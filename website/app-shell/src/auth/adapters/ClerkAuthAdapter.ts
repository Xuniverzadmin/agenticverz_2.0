/**
 * ClerkAuthAdapter — Wraps existing Clerk hooks as an AuthAdapter
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Clerk implementation of the AuthAdapter interface
 * Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
 * capability_id: CAP-006
 *
 * SCAFFOLD: This adapter wraps the existing Clerk integration to
 * prove the adapter boundary works. It does NOT replace the current
 * Clerk setup — the existing ClerkProvider + ClerkAuthSync remain
 * in place as the default path.
 *
 * When the full migration happens, components will switch from
 * Clerk's useAuth() to useHocAuth(), and this adapter will bridge
 * the transition.
 */

import type { AuthAdapter, AuthState, AuthUser } from '../types';

type StateChangeCallback = (state: AuthState) => void;

/**
 * Clerk adapter for the auth boundary.
 *
 * TODO: Wire to actual Clerk hooks when HocAuthProvider replaces ClerkProvider.
 * For now this is a structural placeholder that proves the adapter interface.
 */
export class ClerkAuthAdapter implements AuthAdapter {
  readonly providerType = 'clerk' as const;

  private _stateCallbacks: StateChangeCallback[] = [];
  private _state: AuthState = 'anonymous';
  private _user: AuthUser | null = null;

  async initialize(): Promise<void> {
    // TODO: Subscribe to Clerk session changes and map to AuthState.
    // In the full implementation, this would:
    // 1. Check Clerk.session for existing session
    // 2. Map session state to AuthState
    // 3. Set up session change listener
    this._state = 'anonymous';
  }

  getState(): AuthState {
    return this._state;
  }

  getUser(): AuthUser | null {
    return this._user;
  }

  async getAccessToken(): Promise<string | null> {
    // TODO: Delegate to Clerk's getToken() method.
    // In the full implementation:
    //   const { getToken } = useAuth();
    //   return await getToken();
    return null;
  }

  async signIn(_email: string, _password: string): Promise<void> {
    // TODO: Delegate to Clerk's signIn.create() method.
    // In the full implementation, this would call:
    //   signIn.create({ identifier: email, password });
    //   setActive({ session: result.createdSessionId });
    throw new Error('ClerkAuthAdapter.signIn() not yet wired — use existing LoginPage');
  }

  async signOut(): Promise<void> {
    // TODO: Delegate to Clerk's signOut() method.
    // In the full implementation:
    //   const { signOut } = useClerk();
    //   await signOut();
    throw new Error('ClerkAuthAdapter.signOut() not yet wired — use existing Header signOut');
  }

  async switchTenant(_tenantId: string): Promise<void> {
    // TODO: Clerk org switching (if supported) or redirect
    throw new Error('ClerkAuthAdapter.switchTenant() not supported');
  }

  onStateChange(callback: StateChangeCallback): () => void {
    this._stateCallbacks.push(callback);
    return () => {
      this._stateCallbacks = this._stateCallbacks.filter((cb) => cb !== callback);
    };
  }
}
