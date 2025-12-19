/**
 * Policy Enforcement Audit - Operator Console
 *
 * Every policy action, traceable.
 * The operator's audit log - full transparency on enforcement.
 *
 * Features:
 * - Full policy enforcement history
 * - Filter by guardrail, action, tenant
 * - Call drilldown for any enforcement
 * - Export for compliance
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { Badge } from '../../../components/common/Badge';
import { Modal } from '../../../components/common/Modal';
import { Spinner } from '../../../components/common/Spinner';
import { operatorApi } from '../../../api/operator';

interface PolicyEnforcement {
  id: string;
  call_id: string;
  tenant_id: string;
  tenant_name: string;
  guardrail_id: string;
  guardrail_name: string;
  passed: boolean;
  action_taken: string | null;
  reason: string;
  confidence: number;
  latency_ms: number;
  created_at: string;
  request_context: {
    model: string;
    tokens_estimated: number;
    cost_estimated_cents: number;
  };
}

interface AuditFilters {
  guardrail_id: string | null;
  action: string | null;
  tenant_id: string | null;
  passed: boolean | null;
  date_from: string | null;
  date_to: string | null;
}

const ACTION_COLORS = {
  block: 'bg-red-100 text-red-800',
  throttle: 'bg-yellow-100 text-yellow-800',
  warn: 'bg-blue-100 text-blue-800',
  freeze: 'bg-purple-100 text-purple-800',
  null: 'bg-green-100 text-green-800',
};

export function PolicyAuditLog() {
  const [filters, setFilters] = useState<AuditFilters>({
    guardrail_id: null,
    action: null,
    tenant_id: null,
    passed: null,
    date_from: null,
    date_to: null,
  });
  const [selectedEnforcement, setSelectedEnforcement] = useState<PolicyEnforcement | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 50;

  // Fetch enforcement log
  const { data: enforcements, isLoading } = useQuery({
    queryKey: ['operator', 'audit', filters, page],
    queryFn: () => operatorApi.getPolicyEnforcementLog({
      ...filters,
      page,
      page_size: pageSize,
    }),
  });

  // Fetch guardrails for filter dropdown
  const { data: guardrails } = useQuery({
    queryKey: ['operator', 'guardrails'],
    queryFn: operatorApi.getGuardrailTypes,
  });

  // Export handler
  const handleExport = async () => {
    try {
      const blob = await operatorApi.exportAuditLog(filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `policy-audit-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const enforcementList = enforcements?.items ?? [];
  const totalPages = Math.ceil((enforcements?.total ?? 0) / pageSize);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Policy Enforcement Audit</h1>
          <p className="text-gray-500 mt-1">
            Every policy decision, fully traceable
          </p>
        </div>
        <Button variant="secondary" onClick={handleExport}>
          Export CSV
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap gap-4">
          {/* Guardrail Filter */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Guardrail</label>
            <select
              value={filters.guardrail_id ?? ''}
              onChange={(e) => setFilters(f => ({
                ...f,
                guardrail_id: e.target.value || null,
              }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Guardrails</option>
              {guardrails?.items?.map((g: { id: string; name: string }) => (
                <option key={g.id} value={g.id}>{g.name}</option>
              ))}
            </select>
          </div>

          {/* Action Filter */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Action</label>
            <select
              value={filters.action ?? ''}
              onChange={(e) => setFilters(f => ({
                ...f,
                action: e.target.value || null,
              }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Actions</option>
              <option value="block">Block</option>
              <option value="throttle">Throttle</option>
              <option value="warn">Warn</option>
              <option value="freeze">Freeze</option>
            </select>
          </div>

          {/* Passed/Failed Filter */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Result</label>
            <select
              value={filters.passed === null ? '' : filters.passed ? 'passed' : 'failed'}
              onChange={(e) => setFilters(f => ({
                ...f,
                passed: e.target.value === '' ? null : e.target.value === 'passed',
              }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Results</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed (Enforced)</option>
            </select>
          </div>

          {/* Tenant Filter */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Tenant ID</label>
            <input
              type="text"
              placeholder="Filter by tenant..."
              value={filters.tenant_id ?? ''}
              onChange={(e) => setFilters(f => ({
                ...f,
                tenant_id: e.target.value || null,
              }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-48"
            />
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">From</label>
            <input
              type="date"
              value={filters.date_from ?? ''}
              onChange={(e) => setFilters(f => ({
                ...f,
                date_from: e.target.value || null,
              }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">To</label>
            <input
              type="date"
              value={filters.date_to ?? ''}
              onChange={(e) => setFilters(f => ({
                ...f,
                date_to: e.target.value || null,
              }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          {/* Clear Filters */}
          <div className="flex items-end">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setFilters({
                guardrail_id: null,
                action: null,
                tenant_id: null,
                passed: null,
                date_from: null,
                date_to: null,
              })}
            >
              Clear
            </Button>
          </div>
        </div>
      </Card>

      {/* Results */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : enforcementList.length === 0 ? (
        <Card className="text-center py-12">
          <div className="text-gray-400 text-5xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900">No Enforcement Records</h3>
          <p className="text-gray-500">No policy enforcements match your filters</p>
        </Card>
      ) : (
        <>
          {/* Results Count */}
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              Showing {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, enforcements?.total ?? 0)} of {enforcements?.total ?? 0} records
            </span>
          </div>

          {/* Table */}
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b bg-gray-50">
                    <th className="p-3">Time</th>
                    <th className="p-3">Tenant</th>
                    <th className="p-3">Guardrail</th>
                    <th className="p-3">Result</th>
                    <th className="p-3">Action</th>
                    <th className="p-3">Confidence</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">Call ID</th>
                  </tr>
                </thead>
                <tbody>
                  {enforcementList.map((enforcement: PolicyEnforcement) => (
                    <tr
                      key={enforcement.id}
                      className="border-b last:border-0 hover:bg-gray-50 cursor-pointer"
                      onClick={() => setSelectedEnforcement(enforcement)}
                    >
                      <td className="p-3 text-gray-600">
                        {formatTime(new Date(enforcement.created_at))}
                      </td>
                      <td className="p-3">
                        <Link
                          to={`/operator/tenants/${enforcement.tenant_id}`}
                          className="text-blue-600 hover:text-blue-800"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {enforcement.tenant_name}
                        </Link>
                      </td>
                      <td className="p-3 font-medium text-gray-900">
                        {enforcement.guardrail_name}
                      </td>
                      <td className="p-3">
                        <Badge variant={enforcement.passed ? 'success' : 'error'}>
                          {enforcement.passed ? 'Passed' : 'Failed'}
                        </Badge>
                      </td>
                      <td className="p-3">
                        {enforcement.action_taken ? (
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            ACTION_COLORS[enforcement.action_taken as keyof typeof ACTION_COLORS] ?? 'bg-gray-100 text-gray-800'
                          }`}>
                            {enforcement.action_taken}
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="p-3 text-gray-600">
                        {(enforcement.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="p-3 text-gray-600">
                        {enforcement.latency_ms}ms
                      </td>
                      <td className="p-3 font-mono text-xs text-gray-500">
                        {enforcement.call_id.substring(0, 12)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-gray-500">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage(p => p + 1)}
            >
              Next
            </Button>
          </div>
        </>
      )}

      {/* Enforcement Detail Modal */}
      <Modal
        open={!!selectedEnforcement}
        onClose={() => setSelectedEnforcement(null)}
        title="Enforcement Details"
        size="lg"
      >
        {selectedEnforcement && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="flex items-center gap-4 pb-4 border-b">
              <Badge
                variant={selectedEnforcement.passed ? 'success' : 'error'}
                className="text-lg px-4 py-1"
              >
                {selectedEnforcement.passed ? 'PASSED' : 'FAILED'}
              </Badge>
              <div>
                <h3 className="font-bold text-gray-900">{selectedEnforcement.guardrail_name}</h3>
                <p className="text-sm text-gray-500">
                  {formatTime(new Date(selectedEnforcement.created_at))}
                </p>
              </div>
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <DetailItem label="Call ID" value={selectedEnforcement.call_id} mono />
              <DetailItem label="Tenant" value={`${selectedEnforcement.tenant_name} (${selectedEnforcement.tenant_id})`} />
              <DetailItem label="Guardrail ID" value={selectedEnforcement.guardrail_id} mono />
              <DetailItem label="Action Taken" value={selectedEnforcement.action_taken ?? 'None (passed)'} />
              <DetailItem label="Confidence" value={`${(selectedEnforcement.confidence * 100).toFixed(1)}%`} />
              <DetailItem label="Latency" value={`${selectedEnforcement.latency_ms}ms`} />
            </div>

            {/* Reason */}
            <div>
              <p className="text-sm text-gray-500 mb-1">Reason</p>
              <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">
                {selectedEnforcement.reason}
              </p>
            </div>

            {/* Request Context */}
            <div>
              <p className="text-sm text-gray-500 mb-2">Request Context</p>
              <div className="bg-gray-50 p-3 rounded-lg space-y-1 text-sm">
                <p><span className="text-gray-500">Model:</span> {selectedEnforcement.request_context.model}</p>
                <p><span className="text-gray-500">Tokens (est):</span> {selectedEnforcement.request_context.tokens_estimated.toLocaleString()}</p>
                <p><span className="text-gray-500">Cost (est):</span> ${(selectedEnforcement.request_context.cost_estimated_cents / 100).toFixed(4)}</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t">
              <Link
                to={`/operator/tenants/${selectedEnforcement.tenant_id}`}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                View Tenant
              </Link>
              <Link
                to={`/operator/replay?call=${selectedEnforcement.call_id}`}
                className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
              >
                Replay Call
              </Link>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// Detail Item
function DetailItem({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="text-gray-500">{label}</p>
      <p className={`text-gray-900 ${mono ? 'font-mono text-xs' : ''}`}>{value}</p>
    </div>
  );
}

// Helper function
function formatTime(date: Date): string {
  return date.toLocaleString();
}

export default PolicyAuditLog;
