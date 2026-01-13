/**
 * ClerkAuthSync - Token forwarding ONLY
 *
 * RULE-AUTH-UI-001: Clerk is the auth store.
 * This component ONLY attaches Clerk tokens to API requests.
 * It does NOT:
 * - Store user info outside Clerk
 * - Cache tokens in Zustand/Redux/localStorage
 * - Derive "logged in" state outside Clerk
 *
 * For auth state, components must use Clerk hooks directly:
 * - useAuth() for isSignedIn, getToken
 * - useUser() for user info
 *
 * Reference: PIN-407, FRONTEND_AUTH_CONTRACT.md
 */

import { useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { apiClient } from '@/api/client';

export function ClerkAuthSync() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    // Set up Axios interceptor for Clerk token
    const interceptorId = apiClient.interceptors.request.use(
      async (config) => {
        if (isSignedIn) {
          try {
            const token = await getToken();
            if (token) {
              config.headers.Authorization = `Bearer ${token}`;
            }
          } catch (err) {
            console.error('Failed to get Clerk token:', err);
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Cleanup interceptor on unmount
    return () => {
      apiClient.interceptors.request.eject(interceptorId);
    };
  }, [getToken, isSignedIn]);

  // This component renders nothing - it only sets up the interceptor
  return null;
}

export default ClerkAuthSync;
