/**
 * @audience founder
 *
 * Replay API Client
 *
 * H1 Replay UX - READ-ONLY slice and timeline endpoints
 * Connects to /api/v1/replay/* backend endpoints
 *
 * Reference: Phase H1 - Replay UX Enablement
 */

import apiClient from './client';

// =============================================================================
// Types (matching backend response models)
// =============================================================================

export type ReplayCategory = 'input' | 'decision' | 'action' | 'side_effect';

export interface ReplayItem {
  id: string;
  timestamp: string;
  category: ReplayCategory;
  label: string;
  summary: string;
  data: Record<string, unknown>;
  duration_ms?: number;
  cost_cents?: number;
}

export interface ReplaySliceResponse {
  incident_id: string;
  incident_title: string;
  incident_severity: string;
  incident_status: string;
  window_start: string;
  window_end: string;
  window_seconds: number;
  inputs: ReplayItem[];
  decisions: ReplayItem[];
  actions: ReplayItem[];
  side_effects: ReplayItem[];
  timeline: ReplayItem[];
  total_items: number;
  page: number;
  page_size: number;
  has_more: boolean;
  is_immutable: boolean;
  replay_version: string;
}

export interface IncidentSummaryResponse {
  incident_id: string;
  title: string;
  severity: string;
  status: string;
  trigger_type: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  calls_affected: number;
  cost_delta_cents: number;
  has_replay_data: boolean;
}

export interface ReplayTimelineResponse {
  incident_id: string;
  incident_title: string;
  timeline_start: string;
  timeline_end: string;
  total_items: number;
  items: ReplayItem[];
  is_immutable: boolean;
  note: string;
}

export interface ReplayExplanation {
  item_id: string;
  item_type: 'proxy_call' | 'incident_event';
  category: string;
  timestamp: string;
  explanation: Record<string, unknown>;
  is_immutable: boolean;
}

export interface ReplaySliceParams {
  window?: number;       // Time window in seconds (default: 30)
  center_time?: string;  // Center time ISO8601 (default: incident start)
  page?: number;         // Page number (default: 1)
  page_size?: number;    // Items per page (default: 50)
}

// =============================================================================
// API Functions (READ-ONLY)
// =============================================================================

/**
 * Get time-windowed replay slice of an incident
 *
 * Returns grouped, immutable data for replay visualization:
 * - inputs: What the agent saw
 * - decisions: Policy evaluations
 * - actions: Actual executions
 * - side_effects: Cost tracking, notifications
 */
export async function getReplaySlice(
  incidentId: string,
  params: ReplaySliceParams = {}
): Promise<ReplaySliceResponse> {
  const response = await apiClient.get(`/api/v1/replay/${incidentId}/slice`, {
    params: {
      window: params.window ?? 30,
      center_time: params.center_time,
      page: params.page ?? 1,
      page_size: params.page_size ?? 50,
    },
  });
  return response.data;
}

/**
 * Get incident summary for replay context
 */
export async function getIncidentSummary(
  incidentId: string
): Promise<IncidentSummaryResponse> {
  const response = await apiClient.get(`/api/v1/replay/${incidentId}/summary`);
  return response.data;
}

/**
 * Get full timeline for an incident (unpaginated for scrubbing UI)
 */
export async function getReplayTimeline(
  incidentId: string,
  limit: number = 100
): Promise<ReplayTimelineResponse> {
  const response = await apiClient.get(`/api/v1/replay/${incidentId}/timeline`, {
    params: { limit },
  });
  return response.data;
}

/**
 * Get detailed explanation for a single replay item
 */
export async function getReplayExplanation(
  incidentId: string,
  itemId: string
): Promise<ReplayExplanation> {
  const response = await apiClient.get(
    `/api/v1/replay/${incidentId}/explain/${itemId}`
  );
  return response.data;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get category color class for styling
 */
export function getCategoryColor(category: ReplayCategory): string {
  switch (category) {
    case 'input':
      return 'text-blue-400 bg-blue-900/30';
    case 'decision':
      return 'text-yellow-400 bg-yellow-900/30';
    case 'action':
      return 'text-green-400 bg-green-900/30';
    case 'side_effect':
      return 'text-purple-400 bg-purple-900/30';
    default:
      return 'text-gray-400 bg-gray-900/30';
  }
}

/**
 * Get category icon name
 */
export function getCategoryIcon(category: ReplayCategory): string {
  switch (category) {
    case 'input':
      return 'eye';        // What the agent saw
    case 'decision':
      return 'git-branch'; // Why it decided
    case 'action':
      return 'play';       // What it executed
    case 'side_effect':
      return 'bell';       // Side effects
    default:
      return 'circle';
  }
}

/**
 * Get severity color class
 */
export function getSeverityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'text-red-500 bg-red-900/30';
    case 'high':
      return 'text-orange-500 bg-orange-900/30';
    case 'medium':
      return 'text-yellow-500 bg-yellow-900/30';
    case 'low':
      return 'text-green-500 bg-green-900/30';
    default:
      return 'text-gray-500 bg-gray-900/30';
  }
}

/**
 * Get status color class
 */
export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'open':
      return 'text-red-400';
    case 'acknowledged':
      return 'text-yellow-400';
    case 'resolved':
      return 'text-green-400';
    default:
      return 'text-gray-400';
  }
}

/**
 * Format duration in human readable form
 */
export function formatDuration(ms: number | undefined): string {
  if (!ms) return '-';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

/**
 * Format cost in dollars
 */
export function formatCost(cents: number | undefined): string {
  if (!cents) return '-';
  return `$${(cents / 100).toFixed(4)}`;
}

export default {
  getReplaySlice,
  getIncidentSummary,
  getReplayTimeline,
  getReplayExplanation,
  getCategoryColor,
  getCategoryIcon,
  getSeverityColor,
  getStatusColor,
  formatDuration,
  formatCost,
};
