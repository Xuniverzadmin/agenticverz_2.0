/**
 * @audience customer
 *
 * Policy Proposals API Client - SDSR Real Data
 * Calls /api/v1/policy-proposals for real proposal data from backend
 * Reference: PIN-373 (Policy Domain Integration)
 */
import { apiClient } from './client';

export interface ProposalSummary {
  id: string;
  tenant_id: string;
  proposal_name: string;
  proposal_type: string;
  status: string;  // draft, approved, rejected
  rationale: string;
  created_at: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  effective_from: string | null;
  provenance_count: number;
}

export interface ProposalDetail extends ProposalSummary {
  proposed_rule: Record<string, unknown>;
  triggering_feedback_ids: string[];
  review_notes: string | null;
  versions: ProposalVersion[];
}

export interface ProposalVersion {
  id: string;
  proposal_id: string;
  version: number;
  rule_snapshot: Record<string, unknown>;
  created_at: string | null;
  created_by: string | null;
  change_reason: string | null;
}

export interface ProposalsResponse {
  items: ProposalSummary[];
  total: number;
  limit: number;
  offset: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

export interface ProposalsQueryParams {
  tenant_id?: string;
  status?: string;
  proposal_type?: string;
  limit?: number;
  offset?: number;
}

export interface ApproveRejectRequest {
  reviewed_by: string;
  review_notes?: string;
}

export interface ApprovalResponse {
  proposal_id: string;
  status: string;
  reviewed_by: string;
  reviewed_at: string | null;
  message: string;
}

/**
 * Fetch policy proposals from the backend
 * This uses the real /api/v1/policy-proposals endpoint
 */
export async function fetchProposals(params: ProposalsQueryParams = {}): Promise<ProposalsResponse> {
  const queryParams = new URLSearchParams();

  if (params.tenant_id !== undefined) {
    queryParams.set('tenant_id', params.tenant_id);
  }
  if (params.status !== undefined) {
    queryParams.set('status', params.status);
  }
  if (params.proposal_type !== undefined) {
    queryParams.set('proposal_type', params.proposal_type);
  }
  if (params.limit !== undefined) {
    queryParams.set('limit', params.limit.toString());
  }
  if (params.offset !== undefined) {
    queryParams.set('offset', params.offset.toString());
  }

  const url = `/api/v1/policy-proposals${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<ProposalsResponse>(url);
  return response.data;
}

/**
 * Fetch a single proposal by ID
 */
export async function fetchProposalDetail(proposalId: string): Promise<ProposalDetail> {
  const response = await apiClient.get<ProposalDetail>(`/api/v1/policy-proposals/${proposalId}`);
  return response.data;
}

/**
 * Approve a policy proposal
 */
export async function approveProposal(proposalId: string, request: ApproveRejectRequest): Promise<ApprovalResponse> {
  const response = await apiClient.post<ApprovalResponse>(`/api/v1/policy-proposals/${proposalId}/approve`, request);
  return response.data;
}

/**
 * Reject a policy proposal
 */
export async function rejectProposal(proposalId: string, request: ApproveRejectRequest): Promise<ApprovalResponse> {
  const response = await apiClient.post<ApprovalResponse>(`/api/v1/policy-proposals/${proposalId}/reject`, request);
  return response.data;
}
