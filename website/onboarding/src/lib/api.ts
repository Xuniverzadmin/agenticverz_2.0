/**
 * API Client with AUTH-001 Enforcement
 *
 * This module provides a guarded API client that enforces the AUTH-001 invariant:
 * "Tenant IDs never appear in authenticated URLs"
 *
 * Reference: docs/governance/AUTH_INVARIANTS.md
 */

import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '';

/**
 * AUTH-001 Guard: Rejects paths containing tenant IDs
 *
 * Forbidden patterns:
 * - /tenants/{uuid}/...
 * - /tenants/{tenant_id}/...
 *
 * Tenant identity must come from JWT claims, not URL paths.
 */
function assertNoTenantInPath(path: string): void {
  const tenantInUrlPattern = /\/tenants\/[a-f0-9-]+\//i;
  if (tenantInUrlPattern.test(path)) {
    throw new Error(
      `AUTH-001 VIOLATION: Tenant ID detected in URL path.\n` +
      `Path: ${path}\n` +
      `Tenant identity must come from JWT claims, not URL.\n` +
      `Reference: docs/governance/AUTH_INVARIANTS.md`
    );
  }
}

/**
 * Guarded API client that enforces AUTH-001
 */
export const api = {
  /**
   * GET request with AUTH-001 enforcement
   */
  async get<T = unknown>(
    path: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    assertNoTenantInPath(path);
    return axios.get<T>(`${API_BASE}${path}`, config);
  },

  /**
   * POST request with AUTH-001 enforcement
   */
  async post<T = unknown>(
    path: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    assertNoTenantInPath(path);
    return axios.post<T>(`${API_BASE}${path}`, data, config);
  },

  /**
   * PUT request with AUTH-001 enforcement
   */
  async put<T = unknown>(
    path: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    assertNoTenantInPath(path);
    return axios.put<T>(`${API_BASE}${path}`, data, config);
  },

  /**
   * DELETE request with AUTH-001 enforcement
   */
  async delete<T = unknown>(
    path: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    assertNoTenantInPath(path);
    return axios.delete<T>(`${API_BASE}${path}`, config);
  },

  /**
   * PATCH request with AUTH-001 enforcement
   */
  async patch<T = unknown>(
    path: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    assertNoTenantInPath(path);
    return axios.patch<T>(`${API_BASE}${path}`, data, config);
  },
};

export default api;
