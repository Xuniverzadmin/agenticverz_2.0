import apiClient from './client';
import type { Message, MessageStats, PaginatedResponse } from '@/types/message';

export async function getMessages(params?: {
  from?: string;
  to?: string;
  status?: string;
  type?: string;
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<Message>> {
  const { data } = await apiClient.get('/api/v1/messages', { params });
  return data;
}

export async function getMessage(messageId: string): Promise<Message> {
  const { data } = await apiClient.get(`/api/v1/messages/${messageId}`);
  return data;
}

export async function getMessageStats(range?: string): Promise<MessageStats> {
  const { data } = await apiClient.get('/api/v1/messages/stats', { params: { range } });
  return data;
}

export async function getMessageFlow(range?: string) {
  const { data } = await apiClient.get('/api/v1/messages/flow', { params: { range } });
  return data;
}

export async function getAgentInbox(agentId: string, params?: {
  status?: string;
  limit?: number;
}): Promise<Message[]> {
  const { data } = await apiClient.get(`/agents/${agentId}/messages`, { params });
  return data;
}
