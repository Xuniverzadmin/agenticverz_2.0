/**
 * @audience shared
 *
 * Auth API Client
 * Authentication and token management
 */
import apiClient from './client';

export async function login(email: string, password: string, remember = false) {
  const { data } = await apiClient.post('/api/v1/auth/login', {
    email,
    password,
    remember,
  });
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/v1/auth/logout');
}

export async function refreshToken(refresh_token: string) {
  const { data } = await apiClient.post('/api/v1/auth/refresh', { refresh_token });
  return data;
}

export async function getCurrentUser() {
  const { data } = await apiClient.get('/api/v1/users/me');
  return data;
}

export async function getTenants() {
  const { data } = await apiClient.get('/api/v1/tenants');
  return data;
}

export async function switchTenant(tenantId: string) {
  const { data } = await apiClient.post('/api/v1/tenants/switch', { tenant_id: tenantId });
  return data;
}
