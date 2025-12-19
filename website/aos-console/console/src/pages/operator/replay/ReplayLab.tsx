/**
 * Replay Lab - Operator Console
 *
 * Debug replay issues and model drift.
 * The operator's debugging workbench.
 *
 * Features:
 * - Search any call by ID
 * - Compare original vs replay
 * - Detect model drift
 * - Policy decision diff
 * - Batch replay for regression testing
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { Badge } from '../../../components/common/Badge';
import { Spinner } from '../../../components/common/Spinner';
import { operatorApi } from '../../../api/operator';

interface ReplayResult {
  call_id: string;
  tenant_id: string;
  tenant_name: string;
  original: CallSnapshot;
  replay: CallSnapshot;
  match_level: 'exact' | 'logical' | 'semantic' | 'mismatch';
  policy_match: boolean;
  model_drift_detected: boolean;
  content_match: boolean;
  details: Record<string, any>;
}

interface CallSnapshot {
  timestamp: string;
  model_id: string;
  model_version: string | null;
  temperature: number | null;
  policy_decisions: PolicyDecision[];
  response_hash: string;
  tokens_used: number;
  cost_cents: number;
  latency_ms: number;
}

interface PolicyDecision {
  guardrail_id: string;
  guardrail_name: string;
  passed: boolean;
  action: string | null;
  reason: string;
  confidence: number;
}

interface BatchReplayResult {
  total: number;
  completed: number;
  exact_matches: number;
  logical_matches: number;
  semantic_matches: number;
  mismatches: number;
  model_drift_count: number;
  policy_drift_count: number;
  failures: {
    call_id: string;
    error: string;
  }[];
}

const MATCH_CONFIG = {
  exact: { label: 'Exact Match', color: 'green', icon: '✓', description: 'Byte-for-byte identical' },
  logical: { label: 'Logical Match', color: 'green', icon: '≈', description: 'Same policy decisions' },
  semantic: { label: 'Semantic Match', color: 'yellow', icon: '~', description: 'Similar meaning' },
  mismatch: { label: 'Mismatch', color: 'red', icon: '✗', description: 'Different outcome' },
};

export function ReplayLab() {
  const [searchParams] = useSearchParams();
  const initialCallId = searchParams.get('call') ?? '';

  const [callId, setCallId] = useState(initialCallId);
  const [searchedCallId, setSearchedCallId] = useState<string | null>(initialCallId || null);
  const [batchMode, setBatchMode] = useState(false);
  const [batchConfig, setBatchConfig] = useState({
    tenant_id: '',
    sample_size: 100,
    time_range_hours: 24,
  });

  // Single call replay
  const { data: replayResult, isLoading, error } = useQuery({
    queryKey: ['operator', 'replay', searchedCallId],
    queryFn: () => operatorApi.replayCall(searchedCallId!),
    enabled: !!searchedCallId && !batchMode,
  });

  // Batch replay mutation
  const batchReplayMutation = useMutation({
    mutationFn: operatorApi.batchReplay,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (callId.trim()) {
      setSearchedCallId(callId.trim());
      setBatchMode(false);
    }
  };

  const handleBatchReplay = () => {
    batchReplayMutation.mutate(batchConfig);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Replay Lab</h1>
          <p className="text-gray-500 mt-1">
            Debug replay issues and detect model drift
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setBatchMode(false)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              !batchMode ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Single Call
          </button>
          <button
            onClick={() => setBatchMode(true)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              batchMode ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Batch Mode
          </button>
        </div>
      </div>

      {/* Single Call Mode */}
      {!batchMode && (
        <>
          {/* Search Form */}
          <Card>
            <form onSubmit={handleSearch} className="flex gap-4">
              <input
                type="text"
                value={callId}
                onChange={(e) => setCallId(e.target.value)}
                placeholder="Enter Call ID (e.g., call_abc123xyz)"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <Button type="submit" disabled={!callId.trim() || isLoading}>
                {isLoading ? 'Replaying...' : 'Replay Call'}
              </Button>
            </form>
          </Card>

          {/* Loading */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
              <span className="ml-4 text-gray-600">Executing replay...</span>
            </div>
          )}

          {/* Error */}
          {error && (
            <Card className="bg-red-50 border-red-200">
              <div className="text-center py-8">
                <div className="text-red-500 text-4xl mb-4">⚠️</div>
                <h3 className="text-lg font-medium text-red-800">Replay Failed</h3>
                <p className="text-red-600">
                  Could not replay call: {searchedCallId}
                </p>
              </div>
            </Card>
          )}

          {/* Results */}
          {replayResult && !isLoading && (
            <ReplayResultView result={replayResult} />
          )}

          {/* Empty State */}
          {!searchedCallId && !isLoading && (
            <Card className="text-center py-12">
              <div className="text-gray-400 text-5xl mb-4">🔬</div>
              <h3 className="text-lg font-medium text-gray-900">Enter a Call ID</h3>
              <p className="text-gray-500">
                Replay any call to verify determinism and detect drift
              </p>
            </Card>
          )}
        </>
      )}

      {/* Batch Mode */}
      {batchMode && (
        <>
          {/* Batch Config */}
          <Card>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Batch Replay Configuration</h3>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm text-gray-500 mb-1">Tenant ID (optional)</label>
                <input
                  type="text"
                  value={batchConfig.tenant_id}
                  onChange={(e) => setBatchConfig(c => ({ ...c, tenant_id: e.target.value }))}
                  placeholder="All tenants if empty"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-1">Sample Size</label>
                <select
                  value={batchConfig.sample_size}
                  onChange={(e) => setBatchConfig(c => ({ ...c, sample_size: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="10">10 calls</option>
                  <option value="50">50 calls</option>
                  <option value="100">100 calls</option>
                  <option value="500">500 calls</option>
                  <option value="1000">1000 calls</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-500 mb-1">Time Range</label>
                <select
                  value={batchConfig.time_range_hours}
                  onChange={(e) => setBatchConfig(c => ({ ...c, time_range_hours: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="1">Last 1 hour</option>
                  <option value="6">Last 6 hours</option>
                  <option value="24">Last 24 hours</option>
                  <option value="168">Last 7 days</option>
                </select>
              </div>
            </div>
            <Button
              onClick={handleBatchReplay}
              disabled={batchReplayMutation.isPending}
            >
              {batchReplayMutation.isPending ? 'Running Batch Replay...' : 'Start Batch Replay'}
            </Button>
          </Card>

          {/* Batch Results */}
          {batchReplayMutation.isPending && (
            <Card className="text-center py-12">
              <Spinner size="lg" />
              <p className="mt-4 text-gray-600">
                Running batch replay... This may take a few minutes.
              </p>
            </Card>
          )}

          {batchReplayMutation.data && (
            <BatchResultsView result={batchReplayMutation.data} />
          )}

          {/* Batch Empty State */}
          {!batchReplayMutation.data && !batchReplayMutation.isPending && (
            <Card className="text-center py-12">
              <div className="text-gray-400 text-5xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900">Batch Replay</h3>
              <p className="text-gray-500">
                Test determinism across many calls at once
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

// Single Replay Result View
function ReplayResultView({ result }: { result: ReplayResult }) {
  const matchConfig = MATCH_CONFIG[result.match_level];

  return (
    <div className="space-y-6">
      {/* Match Status */}
      <Card className={`text-center py-8 ${
        matchConfig.color === 'green' ? 'bg-green-50 border-green-200' :
        matchConfig.color === 'yellow' ? 'bg-yellow-50 border-yellow-200' :
        'bg-red-50 border-red-200'
      }`}>
        <div className={`text-6xl mb-4 ${
          matchConfig.color === 'green' ? 'text-green-500' :
          matchConfig.color === 'yellow' ? 'text-yellow-500' :
          'text-red-500'
        }`}>
          {matchConfig.icon}
        </div>
        <h2 className={`text-2xl font-bold mb-2 ${
          matchConfig.color === 'green' ? 'text-green-800' :
          matchConfig.color === 'yellow' ? 'text-yellow-800' :
          'text-red-800'
        }`}>
          {matchConfig.label}
        </h2>
        <p className="text-gray-600">{matchConfig.description}</p>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Policy Match"
          value={result.policy_match ? 'Yes' : 'No'}
          good={result.policy_match}
        />
        <StatCard
          label="Content Match"
          value={result.content_match ? 'Yes' : 'No'}
          good={result.content_match}
        />
        <StatCard
          label="Model Drift"
          value={result.model_drift_detected ? 'Detected' : 'None'}
          good={!result.model_drift_detected}
        />
        <StatCard
          label="Tenant"
          value={result.tenant_name}
        />
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-2 gap-6">
        <CallSnapshotCard title="Original Call" snapshot={result.original} />
        <CallSnapshotCard title="Replayed Call" snapshot={result.replay} />
      </div>

      {/* Policy Decision Comparison */}
      <Card>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Policy Decision Comparison</h3>
        <div className="space-y-2">
          {result.original.policy_decisions.map((original, index) => {
            const replay = result.replay.policy_decisions[index];
            const matches = original.passed === replay?.passed && original.action === replay?.action;

            return (
              <div
                key={original.guardrail_id}
                className={`p-3 rounded-lg ${matches ? 'bg-gray-50' : 'bg-red-50'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{original.guardrail_name}</span>
                  {!matches && <Badge variant="danger">MISMATCH</Badge>}
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Original</p>
                    <p className={original.passed ? 'text-green-600' : 'text-red-600'}>
                      {original.passed ? 'Passed' : `Failed: ${original.action}`}
                      <span className="text-gray-400 ml-2">({(original.confidence * 100).toFixed(0)}%)</span>
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Replay</p>
                    <p className={replay?.passed ? 'text-green-600' : 'text-red-600'}>
                      {replay?.passed ? 'Passed' : `Failed: ${replay?.action}`}
                      <span className="text-gray-400 ml-2">({((replay?.confidence ?? 0) * 100).toFixed(0)}%)</span>
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Model Drift Warning */}
      {result.model_drift_detected && (
        <Card className="bg-yellow-50 border-yellow-200">
          <div className="flex items-start gap-3">
            <span className="text-yellow-500 text-xl">⚠️</span>
            <div>
              <h4 className="font-medium text-yellow-800">Model Drift Detected</h4>
              <p className="text-yellow-700 text-sm mt-1">
                The model version has changed between original and replay.
              </p>
              <div className="mt-2 text-sm text-yellow-800">
                <p>Original: {result.original.model_id} @ {result.original.model_version ?? 'unknown'}</p>
                <p>Replay: {result.replay.model_id} @ {result.replay.model_version ?? 'unknown'}</p>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

// Call Snapshot Card
function CallSnapshotCard({ title, snapshot }: { title: string; snapshot: CallSnapshot }) {
  return (
    <Card>
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Time</span>
          <span>{new Date(snapshot.timestamp).toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Model</span>
          <span className="font-mono text-xs">{snapshot.model_id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Version</span>
          <span className="font-mono text-xs">{snapshot.model_version ?? 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Temperature</span>
          <span>{snapshot.temperature ?? 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Tokens</span>
          <span>{snapshot.tokens_used.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Cost</span>
          <span>${(snapshot.cost_cents / 100).toFixed(4)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Latency</span>
          <span>{snapshot.latency_ms}ms</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Response Hash</span>
          <span className="font-mono text-xs">{snapshot.response_hash.substring(0, 16)}...</span>
        </div>
      </div>
    </Card>
  );
}

// Batch Results View
function BatchResultsView({ result }: { result: BatchReplayResult }) {
  const successRate = ((result.exact_matches + result.logical_matches) / result.completed * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card className="text-center py-8">
        <h2 className="text-4xl font-bold text-gray-900">{successRate}%</h2>
        <p className="text-gray-500 mt-2">Determinism Rate</p>
        <p className="text-sm text-gray-400 mt-1">
          {result.completed} of {result.total} calls completed
        </p>
      </Card>

      {/* Breakdown */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Exact Matches" value={result.exact_matches.toString()} good={true} />
        <StatCard label="Logical Matches" value={result.logical_matches.toString()} good={true} />
        <StatCard label="Semantic Matches" value={result.semantic_matches.toString()} />
        <StatCard label="Mismatches" value={result.mismatches.toString()} good={result.mismatches === 0} />
      </div>

      {/* Drift Detection */}
      <div className="grid grid-cols-2 gap-4">
        <Card className={result.model_drift_count > 0 ? 'ring-2 ring-yellow-500' : ''}>
          <p className="text-sm text-gray-500">Model Drift Detected</p>
          <p className={`text-2xl font-bold ${result.model_drift_count > 0 ? 'text-yellow-600' : 'text-gray-900'}`}>
            {result.model_drift_count}
          </p>
        </Card>
        <Card className={result.policy_drift_count > 0 ? 'ring-2 ring-red-500' : ''}>
          <p className="text-sm text-gray-500">Policy Drift Detected</p>
          <p className={`text-2xl font-bold ${result.policy_drift_count > 0 ? 'text-red-600' : 'text-gray-900'}`}>
            {result.policy_drift_count}
          </p>
        </Card>
      </div>

      {/* Failures */}
      {result.failures.length > 0 && (
        <Card>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Failed Replays</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {result.failures.map((failure) => (
              <div key={failure.call_id} className="flex items-center justify-between p-2 bg-red-50 rounded">
                <span className="font-mono text-xs text-gray-600">{failure.call_id}</span>
                <span className="text-sm text-red-600">{failure.error}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// Stat Card
function StatCard({
  label,
  value,
  good,
}: {
  label: string;
  value: string;
  good?: boolean;
}) {
  return (
    <Card className={good === false ? 'ring-2 ring-red-500' : good === true ? 'ring-2 ring-green-500' : ''}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${
        good === false ? 'text-red-600' :
        good === true ? 'text-green-600' :
        'text-gray-900'
      }`}>
        {value}
      </p>
    </Card>
  );
}

export default ReplayLab;
