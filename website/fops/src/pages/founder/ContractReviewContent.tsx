/**
 * ContractReviewContent - CRM Contract Review
 *
 * Founder contract approval/rejection workflow.
 * This is the LAST human authority insertion point in the governance workflow.
 *
 * Key Constraints:
 * - Founder-scoped (FOPS token required)
 * - Only ELIGIBLE contracts appear in review queue
 * - APPROVE or REJECT only (no edit, no override)
 *
 * Reference: PIN-293 - CRM Contract Review Workflow
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronRight,
  Clock,
  Shield,
  FileText,
  X,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import {
  getReviewQueue,
  getContractDetail,
  submitReview,
  getStatusColor,
  getRiskColor,
  getSeverityColor,
  formatTimestamp,
  isExpiringSoon,
  type ContractSummary,
  type ContractDetail,
  type ReviewDecisionRequest,
} from '@/api/contractReview';

// =============================================================================
// Constants
// =============================================================================

const POLL_INTERVAL_MS = 30000;

// =============================================================================
// Sub-components
// =============================================================================

function QueueStats({ contracts }: { contracts: ContractSummary[] }) {
  const byRisk = {
    CRITICAL: contracts.filter((c) => c.risk_level === 'CRITICAL').length,
    HIGH: contracts.filter((c) => c.risk_level === 'HIGH').length,
    MEDIUM: contracts.filter((c) => c.risk_level === 'MEDIUM').length,
    LOW: contracts.filter((c) => c.risk_level === 'LOW').length,
  };

  const expiringSoon = contracts.filter((c) => isExpiringSoon(c.expires_at)).length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <FileCheck className="h-4 w-4 text-blue-400" />
          <span className="text-sm text-gray-400">Pending Review</span>
        </div>
        <div className="text-2xl font-bold text-white">{contracts.length}</div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="h-4 w-4 text-red-400" />
          <span className="text-sm text-gray-400">Critical</span>
        </div>
        <div className="text-2xl font-bold text-red-400">{byRisk.CRITICAL}</div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <AlertCircle className="h-4 w-4 text-orange-400" />
          <span className="text-sm text-gray-400">High Risk</span>
        </div>
        <div className="text-2xl font-bold text-orange-400">{byRisk.HIGH}</div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="h-4 w-4 text-yellow-400" />
          <span className="text-sm text-gray-400">Medium Risk</span>
        </div>
        <div className="text-2xl font-bold text-yellow-400">{byRisk.MEDIUM}</div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="h-4 w-4 text-purple-400" />
          <span className="text-sm text-gray-400">Expiring Soon</span>
        </div>
        <div className="text-2xl font-bold text-purple-400">{expiringSoon}</div>
      </div>
    </div>
  );
}

function ContractTable({
  contracts,
  onSelectContract,
  isLoading,
}: {
  contracts: ContractSummary[];
  onSelectContract: (contract: ContractSummary) => void;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-400" />
      </div>
    );
  }

  if (contracts.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
        <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
        <p className="text-gray-400">No contracts pending review</p>
        <p className="text-sm text-gray-500 mt-2">
          All eligible contracts have been processed
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-2 p-3 bg-gray-900/50 border-b border-gray-700 text-sm font-medium text-gray-400">
        <div className="col-span-3">Title</div>
        <div className="col-span-2">Source</div>
        <div className="col-span-1 text-center">Risk</div>
        <div className="col-span-2 text-center">Confidence</div>
        <div className="col-span-2">Created</div>
        <div className="col-span-1">Expires</div>
        <div className="col-span-1" />
      </div>

      {/* Table Rows */}
      {contracts.map((contract) => (
        <button
          key={contract.contract_id}
          onClick={() => onSelectContract(contract)}
          className="w-full grid grid-cols-12 gap-2 p-3 border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors text-left group"
        >
          <div className="col-span-3">
            <div className="text-sm text-white font-medium truncate">{contract.title}</div>
            {contract.issue_type && (
              <div className={`text-xs ${getSeverityColor(contract.severity)}`}>
                {contract.issue_type}
              </div>
            )}
          </div>
          <div className="col-span-2 text-sm text-gray-400">
            {contract.source}
          </div>
          <div className="col-span-1 text-center">
            <span className={`text-sm font-medium ${getRiskColor(contract.risk_level)}`}>
              {contract.risk_level}
            </span>
          </div>
          <div className="col-span-2 text-center">
            {contract.confidence_score !== null ? (
              <span className="font-mono text-sm text-gray-300">
                {(contract.confidence_score * 100).toFixed(0)}%
              </span>
            ) : (
              <span className="text-gray-500">-</span>
            )}
          </div>
          <div className="col-span-2 text-sm text-gray-400">
            {formatTimestamp(contract.created_at)}
          </div>
          <div className="col-span-1">
            {contract.expires_at ? (
              <span className={isExpiringSoon(contract.expires_at) ? 'text-orange-400' : 'text-gray-400'}>
                {new Date(contract.expires_at).toLocaleDateString()}
              </span>
            ) : (
              <span className="text-gray-500">-</span>
            )}
          </div>
          <div className="col-span-1 flex justify-end">
            <ChevronRight className="h-4 w-4 text-gray-600 group-hover:text-primary-400 transition-colors" />
          </div>
        </button>
      ))}
    </div>
  );
}

function ContractDrawer({
  contractId,
  onClose,
  onReviewComplete,
}: {
  contractId: string;
  onClose: () => void;
  onReviewComplete: () => void;
}) {
  const [decision, setDecision] = useState<'APPROVE' | 'REJECT' | null>(null);
  const [comment, setComment] = useState('');
  const [activationHours, setActivationHours] = useState(24);
  const queryClient = useQueryClient();

  // Fetch contract detail
  const { data: contract, isLoading } = useQuery({
    queryKey: ['contractDetail', contractId],
    queryFn: () => getContractDetail(contractId),
  });

  // Submit review mutation
  const reviewMutation = useMutation({
    mutationFn: (request: ReviewDecisionRequest) => submitReview(contractId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contractReviewQueue'] });
      onReviewComplete();
      onClose();
    },
  });

  const handleSubmit = () => {
    if (!decision) return;

    reviewMutation.mutate({
      decision,
      comment: comment || undefined,
      activation_window_hours: decision === 'APPROVE' ? activationHours : undefined,
    });
  };

  if (isLoading) {
    return (
      <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-gray-800 border-l border-gray-700 shadow-xl z-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-400" />
      </div>
    );
  }

  if (!contract) {
    return null;
  }

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-gray-800 border-l border-gray-700 shadow-xl z-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Contract Review</h2>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-700 rounded transition-colors"
        >
          <X className="h-5 w-5 text-gray-400" />
        </button>
      </div>

      <div className="p-4 space-y-6">
        {/* Contract Header */}
        <div className="bg-gray-900/50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">{contract.title}</h3>
          {contract.description && (
            <p className="text-sm text-gray-400 mb-4">{contract.description}</p>
          )}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs text-gray-500 mb-1">Status</div>
              <span className={`px-2 py-1 rounded text-sm ${getStatusColor(contract.status)}`}>
                {contract.status}
              </span>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Risk Level</div>
              <span className={`font-medium ${getRiskColor(contract.risk_level)}`}>
                {contract.risk_level}
              </span>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Source</div>
              <span className="text-gray-300">{contract.source}</span>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Confidence</div>
              <span className="text-gray-300">
                {contract.confidence_score !== null
                  ? `${(contract.confidence_score * 100).toFixed(0)}%`
                  : '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Affected Capabilities */}
        {contract.affected_capabilities.length > 0 && (
          <div className="bg-gray-900/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Affected Capabilities</h4>
            <div className="flex flex-wrap gap-2">
              {contract.affected_capabilities.map((cap) => (
                <span
                  key={cap}
                  className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300"
                >
                  {cap}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Validator Summary */}
        {contract.validator_summary && (
          <div className="bg-gray-900/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Machine Analysis</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Issue Type</span>
                <span className="text-gray-300">{contract.validator_summary.issue_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Severity</span>
                <span className={getSeverityColor(contract.validator_summary.severity)}>
                  {contract.validator_summary.severity}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Recommended Action</span>
                <span className="text-gray-300">{contract.validator_summary.recommended_action}</span>
              </div>
              {contract.validator_summary.reason && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Reason</div>
                  <p className="text-gray-400">{contract.validator_summary.reason}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Eligibility Summary */}
        {contract.eligibility_summary && (
          <div className="bg-gray-900/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Eligibility</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Decision</span>
                <span className="text-green-400">{contract.eligibility_summary.decision}</span>
              </div>
              {contract.eligibility_summary.reason && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Reason</div>
                  <p className="text-gray-400">{contract.eligibility_summary.reason}</p>
                </div>
              )}
              {contract.eligibility_summary.blocking_signals.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Blocking Signals</div>
                  <div className="flex flex-wrap gap-1">
                    {contract.eligibility_summary.blocking_signals.map((sig, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-red-900/30 text-red-400 text-xs rounded">
                        {sig}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Proposed Changes */}
        {Object.keys(contract.proposed_changes).length > 0 && (
          <div className="bg-gray-900/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Proposed Changes</h4>
            <pre className="text-xs text-gray-400 bg-gray-950 p-3 rounded overflow-x-auto">
              {JSON.stringify(contract.proposed_changes, null, 2)}
            </pre>
          </div>
        )}

        {/* Review Decision */}
        <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-blue-400 mb-4">Your Decision</h4>

          {/* Decision Buttons */}
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => setDecision('APPROVE')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                decision === 'APPROVE'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-green-900/50 hover:text-green-400'
              }`}
            >
              <CheckCircle className="h-5 w-5" />
              APPROVE
            </button>
            <button
              onClick={() => setDecision('REJECT')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                decision === 'REJECT'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-red-900/50 hover:text-red-400'
              }`}
            >
              <XCircle className="h-5 w-5" />
              REJECT
            </button>
          </div>

          {/* Activation Window (for APPROVE) */}
          {decision === 'APPROVE' && (
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">
                Activation Window (hours)
              </label>
              <input
                type="number"
                min="1"
                max="168"
                value={activationHours}
                onChange={(e) => setActivationHours(parseInt(e.target.value) || 24)}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          )}

          {/* Comment */}
          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-1">
              Comment {decision === 'REJECT' && '(recommended for rejections)'}
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Optional comment explaining your decision..."
              rows={3}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={!decision || reviewMutation.isPending}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
              decision
                ? decision === 'APPROVE'
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}
          >
            {reviewMutation.isPending ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Submitting...
              </>
            ) : (
              <>Submit Review</>
            )}
          </button>

          {/* Error Message */}
          {reviewMutation.isError && (
            <div className="mt-4 p-3 bg-red-900/20 border border-red-800 rounded text-sm text-red-400">
              Failed to submit review. Please try again.
            </div>
          )}
        </div>

        {/* Authority Notice */}
        <div className="bg-amber-900/20 border border-amber-800 rounded-lg p-3 text-sm text-amber-400">
          <strong>AUTHORITY GATE:</strong> This is the last human authority insertion point.
          Your decision will transition the contract to APPROVED or REJECTED status.
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function ContractReviewContent() {
  const [selectedContractId, setSelectedContractId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch review queue
  const {
    data: queueData,
    isLoading,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['contractReviewQueue'],
    queryFn: getReviewQueue,
    staleTime: 10000,
    refetchInterval: POLL_INTERVAL_MS,
  });

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleReviewComplete = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['contractReviewQueue'] });
  }, [queryClient]);

  const contracts = queueData?.contracts || [];

  return (
    <>
      {/* Queue Stats */}
      <QueueStats contracts={contracts} />

      {/* Refresh Bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-400">
          {queueData?.as_of && (
            <>Last updated: {formatTimestamp(queueData.as_of)}</>
          )}
        </div>
        <button
          onClick={handleRefresh}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Contract Table */}
      <ContractTable
        contracts={contracts}
        onSelectContract={(c) => setSelectedContractId(c.contract_id)}
        isLoading={isLoading}
      />

      {/* Contract Review Drawer */}
      {selectedContractId && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setSelectedContractId(null)}
          />
          <ContractDrawer
            contractId={selectedContractId}
            onClose={() => setSelectedContractId(null)}
            onReviewComplete={handleReviewComplete}
          />
        </>
      )}
    </>
  );
}
