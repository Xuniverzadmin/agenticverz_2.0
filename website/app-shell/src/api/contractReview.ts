/**
 * @audience founder
 *
 * Contract Review API Client - CRM Workflow
 *
 * Founder-only contract approval/rejection workflow.
 * This is the LAST human authority insertion point in the governance workflow.
 *
 * Key Constraints:
 * - Founder-scoped (FOPS token required)
 * - Only ELIGIBLE contracts appear in review queue
 * - APPROVE or REJECT only (no edit, no override)
 *
 * Reference: PIN-293 - CRM Contract Review Workflow
 */

import apiClient from './client';

// =============================================================================
// Types - Mirror backend DTOs from founder_contract_review_adapter.py
// =============================================================================

export interface ContractSummary {
  contract_id: string;
  title: string;
  status: string;
  risk_level: string;
  source: string;
  affected_capabilities: string[];
  confidence_score: number | null;
  created_at: string;
  expires_at: string | null;
  issue_type: string | null;
  severity: string | null;
}

export interface ContractDetail {
  // Identity
  contract_id: string;
  version: number;

  // Status
  status: string;
  status_reason: string | null;

  // Content
  title: string;
  description: string | null;
  proposed_changes: Record<string, unknown>;
  affected_capabilities: string[];
  risk_level: string;

  // Validator Summary
  validator_summary: {
    issue_type: string;
    severity: string;
    recommended_action: string;
    confidence_score: number;
    reason: string;
    analyzed_at: string | null;
  } | null;

  // Eligibility Summary
  eligibility_summary: {
    decision: string;
    reason: string;
    blocking_signals: string[];
    missing_prerequisites: string[];
    evaluated_at: string | null;
  } | null;

  // Confidence
  confidence_score: number | null;

  // Origin
  source: string;
  issue_id: string;
  created_by: string;

  // Timing
  created_at: string;
  expires_at: string | null;

  // Review state
  approved_by: string | null;
  approved_at: string | null;

  // History
  transition_count: number;
}

export interface ReviewQueueResponse {
  total: number;
  contracts: ContractSummary[];
  as_of: string;
}

export interface ReviewDecisionRequest {
  decision: 'APPROVE' | 'REJECT';
  comment?: string;
  activation_window_hours?: number;
}

export interface ReviewResult {
  contract_id: string;
  previous_status: string;
  new_status: string;
  reviewed_by: string;
  reviewed_at: string;
  comment: string | null;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get the contract review queue
 * FOUNDER ONLY - Returns contracts in ELIGIBLE status
 */
export async function getReviewQueue(): Promise<ReviewQueueResponse> {
  const response = await apiClient.get('/api/v1/founder/contracts/review-queue');
  return response.data;
}

/**
 * Get contract details for review
 * FOUNDER ONLY - Full context for APPROVE/REJECT decision
 */
export async function getContractDetail(contractId: string): Promise<ContractDetail> {
  const response = await apiClient.get(`/api/v1/founder/contracts/${contractId}`);
  return response.data;
}

/**
 * Submit a review decision for a contract
 * FOUNDER ONLY - APPROVE or REJECT (binary decision)
 */
export async function submitReview(
  contractId: string,
  decision: ReviewDecisionRequest
): Promise<ReviewResult> {
  const response = await apiClient.post(
    `/api/v1/founder/contracts/${contractId}/review`,
    decision
  );
  return response.data;
}

// =============================================================================
// Helper Functions - Display Formatting
// =============================================================================

/**
 * Get status badge color
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'ELIGIBLE':
      return 'text-blue-400 bg-blue-900/30';
    case 'APPROVED':
      return 'text-green-400 bg-green-900/30';
    case 'REJECTED':
      return 'text-red-400 bg-red-900/30';
    case 'ACTIVATED':
      return 'text-purple-400 bg-purple-900/30';
    case 'EXPIRED':
      return 'text-gray-400 bg-gray-900/30';
    default:
      return 'text-yellow-400 bg-yellow-900/30';
  }
}

/**
 * Get risk level color
 */
export function getRiskColor(riskLevel: string): string {
  switch (riskLevel) {
    case 'LOW':
      return 'text-green-400';
    case 'MEDIUM':
      return 'text-yellow-400';
    case 'HIGH':
      return 'text-orange-400';
    case 'CRITICAL':
      return 'text-red-400';
    default:
      return 'text-gray-400';
  }
}

/**
 * Get severity color
 */
export function getSeverityColor(severity: string | null): string {
  if (!severity) return 'text-gray-400';
  switch (severity.toUpperCase()) {
    case 'INFO':
      return 'text-blue-400';
    case 'WARNING':
      return 'text-yellow-400';
    case 'ERROR':
      return 'text-orange-400';
    case 'CRITICAL':
      return 'text-red-400';
    default:
      return 'text-gray-400';
  }
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return '-';
  return new Date(timestamp).toLocaleString();
}

/**
 * Check if contract is expiring soon (within 24 hours)
 */
export function isExpiringSoon(expiresAt: string | null): boolean {
  if (!expiresAt) return false;
  const expiry = new Date(expiresAt);
  const now = new Date();
  const hoursUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60);
  return hoursUntilExpiry > 0 && hoursUntilExpiry <= 24;
}

export default {
  getReviewQueue,
  getContractDetail,
  submitReview,
  getStatusColor,
  getRiskColor,
  getSeverityColor,
  formatTimestamp,
  isExpiringSoon,
};
