/**
 * useSessionContext Hook
 *
 * PIN-409: Provides verified session context from the backend.
 * RULE-AUTH-UI-001: Frontend reads authorization facts, never derives them.
 *
 * This hook replaces frontend-derived authorization facts (isFounder, audience)
 * with backend-verified context. Use this instead of checking authStore for
 * isFounder or audience.
 *
 * Usage:
 *   const { isFounder, isCustomer, tenantId, isLoading } = useSessionContext();
 *   if (isLoading) return <Loading />;
 *   if (isFounder) return <FounderView />;
 *
 * Reference: docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/clerk-react';
import { getSessionContext, type SessionContext } from '@/api/session';

/**
 * Session context with derived convenience properties.
 */
export interface UseSessionContextResult {
  /** Raw session context from backend */
  context: SessionContext | null;
  /** True if actor is a founder */
  isFounder: boolean;
  /** True if actor is a customer */
  isCustomer: boolean;
  /** True if actor is a machine (API key) */
  isMachine: boolean;
  /** Tenant ID for tenant-scoped actors */
  tenantId: string | null;
  /** Lifecycle state (ACTIVE, SUSPENDED, etc.) */
  lifecycleState: string | null;
  /** True if tenant is active (can perform operations) */
  isActive: boolean;
  /** True if session context is being loaded */
  isLoading: boolean;
  /** True if there was an error loading session context */
  isError: boolean;
  /** Error object if isError is true */
  error: Error | null;
  /** Refetch the session context */
  refetch: () => void;
}

/**
 * Hook to get verified session context from the backend.
 *
 * Only fetches when Clerk authentication is complete.
 * Caches the result with React Query.
 *
 * @returns Session context with convenience properties
 */
export function useSessionContext(): UseSessionContextResult {
  const { isSignedIn, isLoaded: clerkLoaded } = useAuth();

  // Only fetch session context if Clerk is loaded and user is signed in
  const enabled = clerkLoaded && isSignedIn;

  const {
    data: context,
    isLoading: queryLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['session', 'context'],
    queryFn: getSessionContext,
    enabled,
    staleTime: 30000, // Cache for 30 seconds
    retry: 2,
  });

  // Derive convenience properties from context
  const isFounder = context?.actor_type === 'founder';
  const isCustomer = context?.actor_type === 'customer';
  const isMachine = context?.actor_type === 'machine';
  const tenantId = context?.tenant_id ?? null;
  const lifecycleState = context?.lifecycle_state ?? null;
  const isActive = lifecycleState === 'ACTIVE';

  // Loading state: waiting for Clerk OR waiting for session context query
  const isLoading = !clerkLoaded || (enabled && queryLoading);

  return {
    context: context ?? null,
    isFounder,
    isCustomer,
    isMachine,
    tenantId,
    lifecycleState,
    isActive,
    isLoading,
    isError,
    error: error as Error | null,
    refetch,
  };
}

export default useSessionContext;
