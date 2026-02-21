/**
 * Auth Module — Public API
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Re-exports for the auth adapter boundary
 * Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
 *
 * Usage:
 *   import { useHocAuth, HocAuthProvider } from '@/auth';
 *   import { ClerkAuthAdapter } from '@/auth/adapters/ClerkAuthAdapter';
 *   import { HocIdentityAuthAdapter } from '@/auth/adapters/HocIdentityAuthAdapter';
 */

export { useHocAuth, HocAuthProvider } from './AuthContext';
export { setupAuthTokenSync } from './AuthTokenSync';
export type {
  AuthState,
  AuthUser,
  UseAuthReturn,
  AuthAdapter,
} from './types';
