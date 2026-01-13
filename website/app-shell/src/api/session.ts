/**
 * @audience shared
 *
 * Session Context API
 * Backend-verified session context for authorization facts
 *
 * PIN-409: Frontend reads authorization facts from backend, never derives them.
 * RULE-AUTH-UI-001: Frontend never decides 'who I am' beyond signed-in vs not.
 *
 * Reference: docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */
import apiClient from './client';

/**
 * Session context from the backend.
 *
 * This replaces frontend-derived authorization facts (isFounder, audience).
 * The backend is the single source of truth for actor type and capabilities.
 */
export interface SessionContext {
  /** Actor type: customer, founder, or machine */
  actor_type: 'customer' | 'founder' | 'machine';
  /** Tenant ID for tenant-scoped actors (null for founders) */
  tenant_id: string | null;
  /** Capabilities/scopes for machine clients (empty for humans) */
  capabilities: string[];
  /** Tenant lifecycle state (ACTIVE, SUSPENDED, TERMINATED, ARCHIVED) */
  lifecycle_state: string | null;
  /** Onboarding state (CREATED, IDENTITY_VERIFIED, ..., COMPLETE) */
  onboarding_state: string | null;
}

/**
 * Get verified session context from the backend.
 *
 * This should be called after Clerk authentication is complete.
 * The backend verifies the JWT and returns authorization facts.
 *
 * @throws If not authenticated or backend unreachable
 */
export async function getSessionContext(): Promise<SessionContext> {
  const { data } = await apiClient.get<SessionContext>('/api/v1/session/context');
  return data;
}
