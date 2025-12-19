/**
 * Replay Page - Trust Builder
 *
 * Minimal UI. Customer can verify any call was processed correctly.
 *
 * Shows:
 * - Call ID (lookup)
 * - Original outcome
 * - Replay outcome
 * - Policy decision (same / different)
 * - Diff summary
 *
 * Purpose: Build trust by showing deterministic behavior.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { Badge } from '../../../components/common/Badge';
import { Spinner } from '../../../components/common/Spinner';
import { guardApi } from '../../../api/guard';

interface ReplayResult {
  call_id: string;
  original: {
    timestamp: string;
    model_id: string;
    policy_decisions: PolicyDecision[];
    response_hash: string;
    tokens_used: number;
    cost_cents: number;
  };
  replay: {
    timestamp: string;
    model_id: string;
    policy_decisions: PolicyDecision[];
    response_hash: string;
    tokens_used: number;
    cost_cents: number;
  };
  match_level: 'exact' | 'logical' | 'semantic' | 'mismatch';
  policy_match: boolean;
  model_drift_detected: boolean;
  details: Record<string, any>;
}

interface PolicyDecision {
  guardrail_id: string;
  guardrail_name: string;
  passed: boolean;
  action: string | null;
}

const MATCH_LEVEL_CONFIG = {
  exact: {
    label: 'Exact Match',
    description: 'Byte-for-byte identical response - Full determinism verified',
    badge: 'STRICT DETERMINISM VERIFIED',
    color: 'green',
    icon: '✓',
  },
  logical: {
    label: 'Logical Match',
    description: 'All policy decisions identical - Logical determinism verified',
    badge: 'LOGICAL DETERMINISM VERIFIED',
    color: 'green',
    icon: '≈',
  },
  semantic: {
    label: 'Semantic Match Only',
    description: 'Same meaning but different content - Policy decisions may vary',
    badge: 'SEMANTIC MATCH ONLY - REVIEW RECOMMENDED',
    color: 'yellow',
    icon: '~',
  },
  mismatch: {
    label: 'Mismatch Detected',
    description: 'Different outcome detected - Investigation required',
    badge: 'MISMATCH - INVESTIGATION REQUIRED',
    color: 'red',
    icon: '✗',
  },
};

export function ReplayPage() {
  const [callId, setCallId] = useState('');
  const [searchedCallId, setSearchedCallId] = useState<string | null>(null);

  // Fetch replay result when call ID is submitted
  const { data: replayResult, isLoading, error } = useQuery({
    queryKey: ['guard', 'replay', searchedCallId],
    queryFn: () => guardApi.replayCall(searchedCallId!),
    enabled: !!searchedCallId,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (callId.trim()) {
      setSearchedCallId(callId.trim());
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Replay Verification</h1>
        <p className="text-gray-600">
          Verify any API call was processed correctly. Enter a call ID to replay
          and compare outcomes.
        </p>
      </div>

      {/* Search Form */}
      <Card className="mb-8">
        <form onSubmit={handleSubmit} className="flex gap-4">
          <input
            type="text"
            value={callId}
            onChange={(e) => setCallId(e.target.value)}
            placeholder="Enter Call ID (e.g., call_abc123xyz)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <Button type="submit" disabled={!callId.trim() || isLoading}>
            {isLoading ? 'Replaying...' : 'Verify Call'}
          </Button>
        </form>
      </Card>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
          <span className="ml-4 text-gray-600">Replaying call...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <div className="text-center py-8">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h3 className="text-lg font-medium text-red-800 mb-2">Call Not Found</h3>
            <p className="text-red-600">
              Could not find a call with ID: {searchedCallId}
            </p>
          </div>
        </Card>
      )}

      {/* Replay Result */}
      {replayResult && !isLoading && (
        <ReplayResultView result={replayResult} />
      )}

      {/* Empty State */}
      {!searchedCallId && !isLoading && (
        <Card className="text-center py-12">
          <div className="text-gray-400 text-5xl mb-4">🔍</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Enter a Call ID</h3>
          <p className="text-gray-500">
            Find the call ID in your API response headers or logs.
          </p>
        </Card>
      )}
    </div>
  );
}

// Replay Result View
function ReplayResultView({ result }: { result: ReplayResult }) {
  const matchConfig = MATCH_LEVEL_CONFIG[result.match_level];

  return (
    <div className="space-y-6">
      {/* Match Status - The Most Important Element */}
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
        {/* Explicit Badge - GA Lock Item */}
        <div className={`inline-block px-4 py-2 rounded-full text-sm font-bold mb-3 ${
          matchConfig.color === 'green' ? 'bg-green-200 text-green-900' :
          matchConfig.color === 'yellow' ? 'bg-yellow-200 text-yellow-900' :
          'bg-red-200 text-red-900'
        }`}>
          {matchConfig.badge}
        </div>
        <p className={`${
          matchConfig.color === 'green' ? 'text-green-600' :
          matchConfig.color === 'yellow' ? 'text-yellow-600' :
          'text-red-600'
        }`}>
          {matchConfig.description}
        </p>
      </Card>

      {/* Comparison Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Original */}
        <Card>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Original Call</h3>
          <div className="space-y-3 text-sm">
            <ComparisonItem
              label="Time"
              value={new Date(result.original.timestamp).toLocaleString()}
            />
            <ComparisonItem
              label="Model"
              value={result.original.model_id}
            />
            <ComparisonItem
              label="Tokens"
              value={result.original.tokens_used.toString()}
            />
            <ComparisonItem
              label="Cost"
              value={`$${(result.original.cost_cents / 100).toFixed(4)}`}
            />
            <ComparisonItem
              label="Response Hash"
              value={result.original.response_hash.substring(0, 12) + '...'}
              mono
            />
          </div>
        </Card>

        {/* Replay */}
        <Card>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Replayed Call</h3>
          <div className="space-y-3 text-sm">
            <ComparisonItem
              label="Time"
              value={new Date(result.replay.timestamp).toLocaleString()}
            />
            <ComparisonItem
              label="Model"
              value={result.replay.model_id}
              highlight={result.model_drift_detected}
            />
            <ComparisonItem
              label="Tokens"
              value={result.replay.tokens_used.toString()}
            />
            <ComparisonItem
              label="Cost"
              value={`$${(result.replay.cost_cents / 100).toFixed(4)}`}
            />
            <ComparisonItem
              label="Response Hash"
              value={result.replay.response_hash.substring(0, 12) + '...'}
              mono
              highlight={result.original.response_hash !== result.replay.response_hash}
            />
          </div>
        </Card>
      </div>

      {/* Policy Decisions */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Policy Decisions</h3>
          <Badge variant={result.policy_match ? 'success' : 'error'}>
            {result.policy_match ? 'All Matched' : 'Differences Found'}
          </Badge>
        </div>

        <div className="space-y-2">
          {result.original.policy_decisions.map((original, index) => {
            const replay = result.replay.policy_decisions[index];
            const matches = original.passed === replay?.passed &&
                           original.action === replay?.action;

            return (
              <div
                key={original.guardrail_id}
                className={`flex items-center justify-between p-3 rounded-lg ${
                  matches ? 'bg-gray-50' : 'bg-yellow-50'
                }`}
              >
                <div>
                  <p className="font-medium text-gray-900">{original.guardrail_name}</p>
                  <p className="text-sm text-gray-500">{original.guardrail_id}</p>
                </div>
                <div className="flex items-center gap-4">
                  <PolicyBadge passed={original.passed} action={original.action} />
                  <span className="text-gray-400">→</span>
                  <PolicyBadge passed={replay?.passed} action={replay?.action} />
                  {!matches && (
                    <span className="text-yellow-600 text-sm font-medium">Changed</span>
                  )}
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
              <h4 className="font-medium text-yellow-800">Model Version Changed</h4>
              <p className="text-yellow-700 text-sm mt-1">
                The upstream model has been updated since the original call.
                Policy decisions remain consistent (logical determinism), but
                exact wording may differ.
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

// Comparison Item
function ComparisonItem({
  label,
  value,
  mono = false,
  highlight = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={`
        ${mono ? 'font-mono' : ''}
        ${highlight ? 'text-yellow-600 font-medium' : 'text-gray-900'}
      `}>
        {value}
      </span>
    </div>
  );
}

// Policy Badge
function PolicyBadge({
  passed,
  action,
}: {
  passed?: boolean;
  action?: string | null;
}) {
  if (passed === undefined) {
    return <Badge variant="default">N/A</Badge>;
  }

  if (passed) {
    return <Badge variant="success">Passed</Badge>;
  }

  return (
    <Badge variant="error">
      {action || 'Blocked'}
    </Badge>
  );
}

export default ReplayPage;
