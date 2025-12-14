// ActivityTab Component
// M16 - Shows live activity: costs, spending, retries, blockers

import { useQuery } from '@tanstack/react-query';
import { Spinner } from '@/components/common';
import type { SBAAgent } from '@/types/sba';
import {
  getActivityCosts,
  getActivitySpending,
  getActivityRetries,
  getActivityBlockers,
  type WorkerMetrics,
  type RetryEntry,
  type BlockerEntry,
} from '@/api/sba';
import { CostRiskOverview } from '../activity/CostRiskOverview';
import { SpendingTracker } from '../activity/SpendingTracker';
import { RetryLog } from '../activity/RetryLog';
import { IssuesBlockers, type Issue } from '../activity/IssuesBlockers';

interface ActivityTabProps {
  agent: SBAAgent;
}

// Transform API BlockerEntry to UI Issue type
function transformBlockers(blockers: BlockerEntry[]): Issue[] {
  return blockers.map((b) => ({
    type: b.type as Issue['type'],
    message: b.message,
    since: b.since,
    action: b.action,
    details: b.details,
  }));
}

export function ActivityTab({ agent }: ActivityTabProps) {
  const agentId = agent.agent_id;

  const { data: costsData, isLoading: loadingCosts } = useQuery({
    queryKey: ['agent-activity-costs', agentId],
    queryFn: () => getActivityCosts(agentId),
    refetchInterval: 10000, // Refresh every 10s for live data
  });

  const { data: spendingData, isLoading: loadingSpending } = useQuery({
    queryKey: ['agent-activity-spending', agentId],
    queryFn: () => getActivitySpending(agentId, '24h'),
    refetchInterval: 10000,
  });

  const { data: retriesData, isLoading: loadingRetries } = useQuery({
    queryKey: ['agent-activity-retries', agentId],
    queryFn: () => getActivityRetries(agentId),
    refetchInterval: 5000, // More frequent for retries
  });

  const { data: blockersData, isLoading: loadingBlockers } = useQuery({
    queryKey: ['agent-activity-blockers', agentId],
    queryFn: () => getActivityBlockers(agentId),
    refetchInterval: 5000,
  });

  const isLoading = loadingCosts || loadingSpending || loadingRetries || loadingBlockers;

  if (isLoading && !costsData && !spendingData) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  const workers: WorkerMetrics[] = costsData?.workers || [];
  const retries: RetryEntry[] = retriesData?.retries || [];
  const blockers: Issue[] = blockersData ? transformBlockers(blockersData.blockers) : [];

  const handleBlockerAction = (issue: Issue, action: string) => {
    console.log('Action:', action, 'on issue:', issue);
    // Implement retry/skip/escalate logic
  };

  return (
    <div className="space-y-4">
      {/* Cost & Risk Overview */}
      <CostRiskOverview
        workers={workers}
        onClick={(worker) => console.log('Show worker details:', worker)}
      />

      {/* Spending Tracker */}
      {spendingData && spendingData.actual.length > 0 && (
        <SpendingTracker
          actual={spendingData.actual}
          projected={spendingData.projected}
          budget_limit={spendingData.budget_limit}
          anomalies={spendingData.anomalies}
        />
      )}

      {/* Two columns for Retries and Issues */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RetryLog retries={retries} />
        <IssuesBlockers
          issues={blockers}
          onAction={handleBlockerAction}
        />
      </div>
    </div>
  );
}
