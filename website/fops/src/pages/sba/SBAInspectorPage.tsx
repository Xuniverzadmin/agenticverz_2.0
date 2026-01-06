// SBA Inspector Page
// M15.1.1 Strategy-Bound Agents UI

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  RefreshCw,
  Target,
  CheckCircle,
  XCircle,
  TrendingUp,
  Store,
  LayoutGrid,
  List,
  Search,
} from 'lucide-react';
import { Card, CardHeader, CardBody, Spinner, Button } from '@/components/common';
import { getFulfillmentAggregated, getAgentSBA, extractDomains } from '@/api/sba';
import type { SBAFilters, ViewMode, GroupByOption, SBAAgentWithFulfillment } from '@/types/sba';
import { cn } from '@/lib/utils';
import { FulfillmentHeatmap } from './components/FulfillmentHeatmap';
import { SBADetailModal } from './components/SBADetailModal';
import { SBAFiltersBar } from './components/SBAFilters';

export default function SBAInspectorPage() {
  // UI State
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [groupBy, setGroupBy] = useState<GroupByOption>('domain');
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [filters, setFilters] = useState<SBAFilters>({});

  // Data fetching
  const { data: fulfillmentData, isLoading, refetch } = useQuery({
    queryKey: ['sba-fulfillment', groupBy],
    queryFn: () => getFulfillmentAggregated(groupBy),
    refetchInterval: 30000,
  });

  const { data: selectedAgent, isLoading: isLoadingAgent } = useQuery({
    queryKey: ['sba-agent', selectedAgentId],
    queryFn: () => selectedAgentId ? getAgentSBA(selectedAgentId) : null,
    enabled: !!selectedAgentId,
  });

  // Derived data
  const agents = fulfillmentData?.agents || [];
  const summary = fulfillmentData?.summary || {
    total_agents: 0,
    validated_count: 0,
    avg_fulfillment: 0,
    marketplace_ready_count: 0,
    by_fulfillment_range: {},
  };
  const domains = useMemo(() => extractDomains(agents), [agents]);

  // Filter agents
  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      if (filters.agent_type && agent.agent_type !== filters.agent_type) return false;
      if (filters.sba_validated !== undefined && filters.sba_validated !== null) {
        if (agent.sba_validated !== filters.sba_validated) return false;
      }
      if (filters.domain && agent.domain !== filters.domain) return false;
      if (filters.search) {
        const search = filters.search.toLowerCase();
        const matches =
          agent.agent_id.toLowerCase().includes(search) ||
          (agent.agent_name || '').toLowerCase().includes(search);
        if (!matches) return false;
      }
      return true;
    });
  }, [agents, filters]);

  const validatedPercent = summary.total_agents > 0
    ? Math.round((summary.validated_count / summary.total_agents) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            SBA Inspector
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Strategy-Bound Agents with Strategy Cascade governance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={16} />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardBody>
            <div className="flex items-center gap-3">
              <Target className="size-8 text-blue-500" />
              <div>
                <p className="text-sm text-gray-500">Total Agents</p>
                <p className="text-2xl font-semibold">{summary.total_agents}</p>
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="flex items-center gap-3">
              <CheckCircle className="size-8 text-green-500" />
              <div>
                <p className="text-sm text-gray-500">Validated</p>
                <p className="text-2xl font-semibold text-green-600">
                  {summary.validated_count} <span className="text-sm text-gray-400">({validatedPercent}%)</span>
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="flex items-center gap-3">
              <TrendingUp className="size-8 text-purple-500" />
              <div>
                <p className="text-sm text-gray-500">Avg Fulfillment</p>
                <p className="text-2xl font-semibold text-purple-600">
                  {Math.round(summary.avg_fulfillment * 100)}%
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="flex items-center gap-3">
              <Store className="size-8 text-yellow-500" />
              <div>
                <p className="text-sm text-gray-500">Marketplace Ready</p>
                <p className="text-2xl font-semibold text-yellow-600">
                  {summary.marketplace_ready_count}
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Filters and View Toggle */}
      <Card>
        <CardBody>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <SBAFiltersBar
              filters={filters}
              onFilterChange={setFilters}
              domains={domains}
            />
            <div className="flex items-center gap-2">
              {viewMode === 'heatmap' && (
                <select
                  className="px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700"
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value as GroupByOption)}
                >
                  <option value="domain">Group by Domain</option>
                  <option value="agent_type">Group by Type</option>
                  <option value="orchestrator">Group by Orchestrator</option>
                </select>
              )}
              <div className="flex border rounded-lg overflow-hidden">
                <button
                  className={cn(
                    'px-3 py-2 flex items-center gap-1 text-sm',
                    viewMode === 'list'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                  onClick={() => setViewMode('list')}
                >
                  <List size={16} />
                  List
                </button>
                <button
                  className={cn(
                    'px-3 py-2 flex items-center gap-1 text-sm border-l',
                    viewMode === 'heatmap'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                  onClick={() => setViewMode('heatmap')}
                >
                  <LayoutGrid size={16} />
                  Heatmap
                </button>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Main Content */}
      <Card>
        <CardHeader title={`Agents (${filteredAgents.length})`}>
          <span className="text-sm font-normal text-gray-500">
            {viewMode === 'heatmap' ? 'Click a cell to view details' : 'Click a row to view Strategy Cascade'}
          </span>
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : filteredAgents.length > 0 ? (
            viewMode === 'list' ? (
              <AgentList agents={filteredAgents} onSelect={setSelectedAgentId} />
            ) : (
              <div className="p-4">
                <FulfillmentHeatmap
                  agents={filteredAgents}
                  groupBy={groupBy}
                  onCellClick={setSelectedAgentId}
                />
              </div>
            )
          ) : (
            <div className="px-4 py-12 text-center text-gray-500">
              <Target className="mx-auto mb-2 text-gray-400" size={32} />
              No agents found
            </div>
          )}
        </CardBody>
      </Card>

      {/* Detail Modal */}
      {selectedAgentId && (
        <SBADetailModal
          agent={selectedAgent}
          isLoading={isLoadingAgent}
          onClose={() => setSelectedAgentId(null)}
        />
      )}
    </div>
  );
}

// ============================================================================
// Agent List Component
// ============================================================================

interface AgentListProps {
  agents: SBAAgentWithFulfillment[];
  onSelect: (agentId: string) => void;
}

function AgentList({ agents, onSelect }: AgentListProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-800 text-xs uppercase">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Agent</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Type</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Domain</th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">Orchestrator</th>
            <th className="px-4 py-3 text-center font-medium text-gray-500">Validated</th>
            <th className="px-4 py-3 text-center font-medium text-gray-500">Fulfillment</th>
            <th className="px-4 py-3 text-center font-medium text-gray-500">Marketplace</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {agents.map((agent) => (
            <tr
              key={agent.agent_id}
              className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
              onClick={() => onSelect(agent.agent_id)}
            >
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {agent.agent_name || agent.agent_id}
                  </p>
                  {agent.agent_name && (
                    <p className="text-xs text-gray-500">{agent.agent_id}</p>
                  )}
                </div>
              </td>
              <td className="px-4 py-3">
                <span className={cn(
                  'text-xs px-2 py-1 rounded-full',
                  agent.agent_type === 'orchestrator' && 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
                  agent.agent_type === 'worker' && 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
                  agent.agent_type === 'aggregator' && 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
                )}>
                  {agent.agent_type}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {agent.domain}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {agent.orchestrator}
              </td>
              <td className="px-4 py-3 text-center">
                {agent.sba_validated ? (
                  <CheckCircle className="inline size-5 text-green-500" />
                ) : (
                  <XCircle className="inline size-5 text-red-400" />
                )}
              </td>
              <td className="px-4 py-3 text-center">
                <FulfillmentBadge value={agent.fulfillment_metric} />
              </td>
              <td className="px-4 py-3 text-center">
                {agent.marketplace_ready ? (
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                    <Store size={12} />
                    Ready
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================================
// Fulfillment Badge Component
// ============================================================================

function FulfillmentBadge({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const colorClass =
    value < 0.2 ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
    value < 0.4 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' :
    value < 0.6 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
    value < 0.8 ? 'bg-lime-100 text-lime-700 dark:bg-lime-900 dark:text-lime-300' :
    'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';

  return (
    <span className={cn('text-xs px-2 py-1 rounded-full font-medium', colorClass)}>
      {percent}%
    </span>
  );
}
