/**
 * HocIdentityAuthAdapter — In-house auth adapter scaffold
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: HOC Identity implementation of the AuthAdapter interface (scaffold)
 * Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
 *
 * SCAFFOLD: All methods throw NotImplementedError or return defaults.
 * Will be implemented when POST /hoc/api/auth/login and related
 * endpoints are functional.
 *
 * Token lifecycle (V1 design):
 * - Access token: 5-15 min, stored in memory only
 * - Refresh token: ~7 days, HttpOnly Secure SameSite cookie
 * - Refresh rotation: new refresh token issued per use
 */

import type { AuthAdapter, AuthState, AuthUser } from '../types';

type StateChangeCallback = (state: AuthState) => void;

/**
 * HOC Identity auth adapter (scaffold).
 *
 * TODO: Implement when backend endpoints are functional:
 * 1. signIn → POST /hoc/api/auth/login
 * 2. signOut → POST /hoc/api/auth/logout
 * 3. getAccessToken → memory token + POST /hoc/api/auth/refresh
 * 4. switchTenant → POST /hoc/api/auth/switch-tenant
 */
export class HocIdentityAuthAdapter implements AuthAdapter {
  readonly providerType = 'hoc_identity' as const;

  private _stateCallbacks: StateChangeCallback[] = [];
  private _state: AuthState = 'anonymous';
  private _user: AuthUser | null = null;
  private _accessToken: string | null = null;

  async initialize(): Promise<void> {
    // TODO: Check for existing session via refresh cookie.
    // 1. Attempt POST /hoc/api/auth/refresh (cookie-based)
    // 2. If successful, set state to 'authenticated' and store access token
    // 3. If failed, set state to 'anonymous'
    this._state = 'anonymous';
    this._user = null;
    this._accessToken = null;
  }

  getState(): AuthState {
    return this._state;
  }

  getUser(): AuthUser | null {
    return this._user;
  }

  async getAccessToken(): Promise<string | null> {
    // TODO: Return in-memory access token.
    // If expired, attempt refresh via POST /hoc/api/auth/refresh.
    // If refresh fails, transition to 'expired' state.
    return this._accessToken;
  }

  async signIn(_email: string, _password: string): Promise<void> {
    // TODO: Implement login flow:
    // 1. POST /hoc/api/auth/login { email, password }
    // 2. Store access_token in memory (this._accessToken)
    // 3. Refresh token set as HttpOnly cookie by backend
    // 4. Decode access token for user info
    // 5. Set state to 'authenticated'
    // 6. Notify state change listeners
    throw new Error('HocIdentityAuthAdapter.signIn() not yet implemented');
  }

  async signOut(): Promise<void> {
    // TODO: Implement logout flow:
    // 1. POST /hoc/api/auth/logout (with CSRF)
    // 2. Clear access token from memory
    // 3. Backend clears refresh cookie
    // 4. Set state to 'anonymous'
    // 5. Notify state change listeners
    throw new Error('HocIdentityAuthAdapter.signOut() not yet implemented');
  }

  async switchTenant(_tenantId: string): Promise<void> {
    // TODO: Implement tenant switch:
    // 1. POST /hoc/api/auth/switch-tenant { tenant_id, csrf_token }
    // 2. Receive new access + refresh tokens
    // 3. Update in-memory token and user info
    // 4. Notify state change listeners
    throw new Error('HocIdentityAuthAdapter.switchTenant() not yet implemented');
  }

  onStateChange(callback: StateChangeCallback): () => void {
    this._stateCallbacks.push(callback);
    return () => {
      this._stateCallbacks = this._stateCallbacks.filter((cb) => cb !== callback);
    };
  }

  /** Notify all listeners of state change */
  private _notifyStateChange(): void {
    for (const cb of this._stateCallbacks) {
      cb(this._state);
    }
  }
}
