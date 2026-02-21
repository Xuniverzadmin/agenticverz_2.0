/**
 * AuthTokenSync — Generic auth sync shim for API token attachment
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Token attachment interceptor contract (replaces ClerkAuthSync)
 * Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md
 *
 * SCAFFOLD: Defines the contract for attaching auth tokens to API calls.
 * When the full migration happens, this replaces ClerkAuthSync.tsx.
 *
 * The existing ClerkAuthSync remains in place as the active token
 * attachment mechanism. This file defines the provider-neutral contract.
 */

import type { AuthAdapter } from './types';

/**
 * Set up an Axios interceptor that attaches the access token from
 * the given auth adapter to every outgoing API request.
 *
 * TODO: Wire this into the app when replacing ClerkAuthSync:
 *   import { setupAuthTokenSync } from '@/auth/AuthTokenSync';
 *   import { apiClient } from '@/api/client';
 *
 *   // In App.tsx or HocAuthProvider:
 *   useEffect(() => {
 *     const cleanup = setupAuthTokenSync(apiClient, adapter);
 *     return cleanup;
 *   }, [adapter]);
 *
 * @param apiClient - Axios instance
 * @param adapter - Auth adapter providing getAccessToken()
 * @returns Cleanup function to remove the interceptor
 */
export function setupAuthTokenSync(
  apiClient: { interceptors: { request: { use: Function; eject: Function } } },
  adapter: AuthAdapter,
): () => void {
  const interceptorId = apiClient.interceptors.request.use(
    async (config: Record<string, unknown>) => {
      const token = await adapter.getAccessToken();
      if (token) {
        const headers = (config.headers || {}) as Record<string, string>;
        headers['Authorization'] = `Bearer ${token}`;
        config.headers = headers;
      }
      return config;
    },
    (error: unknown) => Promise.reject(error),
  );

  return () => {
    apiClient.interceptors.request.eject(interceptorId);
  };
}
