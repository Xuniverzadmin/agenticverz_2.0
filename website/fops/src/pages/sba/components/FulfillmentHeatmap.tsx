// Fulfillment Heatmap Component
// M15.1.1 Strategy-Bound Agents UI

import { useMemo } from 'react';
import { Store } from 'lucide-react';
import type { SBAAgentWithFulfillment, GroupByOption } from '@/types/sba';
import { cn } from '@/lib/utils';

interface FulfillmentHeatmapProps {
  agents: SBAAgentWithFulfillment[];
  groupBy: GroupByOption;
  onCellClick: (agentId: string) => void;
}

export function FulfillmentHeatmap({ agents, groupBy, onCellClick }: FulfillmentHeatmapProps) {
  // Group agents by the selected criteria
  const groups = useMemo(() => {
    const grouped: Record<string, SBAAgentWithFulfillment[]> = {};
    agents.forEach((agent) => {
      const key = groupBy === 'domain' ? agent.domain :
                  groupBy === 'agent_type' ? agent.agent_type :
                  agent.orchestrator;
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(agent);
    });
    // Sort groups by name
    return Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b));
  }, [agents, groupBy]);

  if (agents.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No agents to display
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Legend */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs">
          <span className="text-gray-500">Fulfillment:</span>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-red-600" />
            <span className="text-gray-600 dark:text-gray-400">0-20%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-orange-500" />
            <span className="text-gray-600 dark:text-gray-400">20-40%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-yellow-500" />
            <span className="text-gray-600 dark:text-gray-400">40-60%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-lime-500" />
            <span className="text-gray-600 dark:text-gray-400">60-80%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-green-500" />
            <span className="text-gray-600 dark:text-gray-400">80-100%</span>
          </div>
          <div className="flex items-center gap-1 ml-2 pl-2 border-l">
            <div className="w-4 h-4 rounded bg-green-500 ring-2 ring-yellow-400" />
            <span className="text-gray-600 dark:text-gray-400">Marketplace Ready</span>
          </div>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="space-y-4">
        {groups.map(([groupName, groupAgents]) => (
          <div key={groupName}>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
              <span className="capitalize">{groupName}</span>
              <span className="text-xs text-gray-400">({groupAgents.length} agents)</span>
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {groupAgents.map((agent) => (
                <HeatmapCell
                  key={agent.agent_id}
                  agent={agent}
                  onClick={() => onCellClick(agent.agent_id)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Heatmap Cell Component
// ============================================================================

interface HeatmapCellProps {
  agent: SBAAgentWithFulfillment;
  onClick: () => void;
}

function HeatmapCell({ agent, onClick }: HeatmapCellProps) {
  const fulfillment = agent.fulfillment_metric;
  const percent = Math.round(fulfillment * 100);

  // Color based on fulfillment
  const colorClass =
    fulfillment < 0.2 ? 'bg-red-600 hover:bg-red-500' :
    fulfillment < 0.4 ? 'bg-orange-500 hover:bg-orange-400' :
    fulfillment < 0.6 ? 'bg-yellow-500 hover:bg-yellow-400' :
    fulfillment < 0.8 ? 'bg-lime-500 hover:bg-lime-400' :
    'bg-green-500 hover:bg-green-400';

  return (
    <button
      className={cn(
        'w-10 h-10 rounded flex items-center justify-center text-white text-xs font-medium transition-all',
        colorClass,
        agent.marketplace_ready && 'ring-2 ring-yellow-400 ring-offset-1',
        !agent.sba_validated && 'opacity-60'
      )}
      onClick={onClick}
      title={`${agent.agent_name || agent.agent_id}\nFulfillment: ${percent}%\n${agent.marketplace_ready ? 'Marketplace Ready' : ''}`}
    >
      {agent.marketplace_ready ? (
        <Store size={14} />
      ) : (
        <span>{percent}</span>
      )}
    </button>
  );
}

// ============================================================================
// Fulfillment History Chart Component
// ============================================================================

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { FulfillmentHistoryEntry } from '@/types/sba';

interface FulfillmentHistoryChartProps {
  history: FulfillmentHistoryEntry[];
  className?: string;
}

export function FulfillmentHistoryChart({ history, className }: FulfillmentHistoryChartProps) {
  if (!history || history.length === 0) {
    return (
      <div className={cn('text-center text-gray-500 py-4 text-sm', className)}>
        No fulfillment history available
      </div>
    );
  }

  // Format data for chart
  const data = history.map((entry, i) => ({
    index: i + 1,
    value: Math.round(entry.new_metric * 100),
    reason: entry.reason || 'Update',
    timestamp: new Date(entry.timestamp).toLocaleDateString(),
  }));

  return (
    <div className={cn('h-40', className)}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="index"
            tick={{ fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload?.[0]) return null;
              const item = payload[0].payload;
              return (
                <div className="bg-white dark:bg-gray-800 p-2 rounded shadow-lg border text-xs">
                  <div className="font-medium">{item.value}%</div>
                  <div className="text-gray-500">{item.reason}</div>
                  <div className="text-gray-400">{item.timestamp}</div>
                </div>
              );
            }}
          />
          <ReferenceLine
            y={80}
            stroke="#eab308"
            strokeDasharray="3 3"
            label={{ value: 'Marketplace', position: 'right', fontSize: 10, fill: '#eab308' }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
