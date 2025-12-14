// ActivityTab Component
// M16 - Shows live activity: costs, spending, retries, blockers

import { useQuery } from '@tanstack/react-query';
import { Spinner } from '@/components/common';
import type { SBAAgent } from '@/types/sba';
import { CostRiskOverview, type WorkerMetrics } from '../activity/CostRiskOverview';
import { SpendingTracker } from '../activity/SpendingTracker';
import { RetryLog, type RetryEntry } from '../activity/RetryLog';
import { IssuesBlockers, type Issue } from '../activity/IssuesBlockers';

interface ActivityTabProps {
  agent: SBAAgent;
}

// Mock API functions (replace with real API calls)
async function fetchWorkerMetrics(_agentId: string): Promise<WorkerMetrics[]> {
  // Simulated data - replace with actual API call
  return [
    { id: 'worker-1', name: 'Scraper Worker', cost: 'low', risk: 0.15, budget_used: 35 },
    { id: 'worker-2', name: 'Parser Worker', cost: 'medium', risk: 0.45, budget_used: 62 },
    { id: 'worker-3', name: 'Validator', cost: 'low', risk: 0.08, budget_used: 20 },
  ];
}

async function fetchSpendingData(_agentId: string): Promise<{
  actual: number[];
  projected: number[];
  budget_limit: number;
  anomalies: { index: number; reason: string }[];
}> {
  return {
    actual: [100, 250, 420, 580, 750, 920],
    projected: [100, 200, 300, 400, 500, 600],
    budget_limit: 1000,
    anomalies: [{ index: 3, reason: 'Retry spike' }],
  };
}

async function fetchRetries(_agentId: string): Promise<RetryEntry[]> {
  return [
    { time: '10:23:45', reason: 'API timeout', attempt: 1, outcome: 'success', risk_change: -0.05 },
    { time: '10:25:12', reason: 'Rate limit hit', attempt: 2, outcome: 'success', risk_change: 0.02 },
    { time: '10:28:33', reason: 'Connection reset', attempt: 1, outcome: 'failure', risk_change: 0.15 },
  ];
}

async function fetchBlockers(_agentId: string): Promise<Issue[]> {
  return [
    {
      type: 'api',
      message: 'External API returning 503',
      since: '5 min ago',
      action: 'Retry',
      details: 'api.example.com/data',
    },
  ];
}

export function ActivityTab({ agent }: ActivityTabProps) {
  const agentId = agent.agent_id;

  const { data: workers, isLoading: loadingWorkers } = useQuery({
    queryKey: ['agent-workers', agentId],
    queryFn: () => fetchWorkerMetrics(agentId),
    refetchInterval: 10000, // Refresh every 10s for live data
  });

  const { data: spending, isLoading: loadingSpending } = useQuery({
    queryKey: ['agent-spending', agentId],
    queryFn: () => fetchSpendingData(agentId),
    refetchInterval: 10000,
  });

  const { data: retries, isLoading: loadingRetries } = useQuery({
    queryKey: ['agent-retries', agentId],
    queryFn: () => fetchRetries(agentId),
    refetchInterval: 5000, // More frequent for retries
  });

  const { data: blockers, isLoading: loadingBlockers } = useQuery({
    queryKey: ['agent-blockers', agentId],
    queryFn: () => fetchBlockers(agentId),
    refetchInterval: 5000,
  });

  const isLoading = loadingWorkers || loadingSpending || loadingRetries || loadingBlockers;

  if (isLoading && !workers && !spending) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  const handleBlockerAction = (issue: Issue, action: string) => {
    console.log('Action:', action, 'on issue:', issue);
    // Implement retry/skip/escalate logic
  };

  return (
    <div className="space-y-4">
      {/* Cost & Risk Overview */}
      <CostRiskOverview
        workers={workers || []}
        onClick={(worker) => console.log('Show worker details:', worker)}
      />

      {/* Spending Tracker */}
      {spending && (
        <SpendingTracker
          actual={spending.actual}
          projected={spending.projected}
          budget_limit={spending.budget_limit}
          anomalies={spending.anomalies}
        />
      )}

      {/* Two columns for Retries and Issues */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RetryLog retries={retries || []} />
        <IssuesBlockers
          issues={blockers || []}
          onAction={handleBlockerAction}
        />
      </div>
    </div>
  );
}
