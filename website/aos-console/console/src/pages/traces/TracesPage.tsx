import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { GitBranch, Search, RefreshCw, Eye, GitCompare } from 'lucide-react';
import { Card, CardHeader, CardBody, Spinner, StatusBadge, Button, Input } from '@/components/common';
import { getTraces, compareTraces, type Trace } from '@/api/traces';
import { truncateId } from '@/lib/utils';
import { cn } from '@/lib/utils';

export default function TracesPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [compareMode, setCompareMode] = useState(false);
  const [selectedTraces, setSelectedTraces] = useState<string[]>([]);

  const { data: traces, isLoading, refetch } = useQuery({
    queryKey: ['traces', statusFilter],
    queryFn: () => getTraces({ limit: 50, status: statusFilter || undefined }),
    refetchInterval: 30000,
  });

  const { data: comparison, isLoading: comparing } = useQuery({
    queryKey: ['trace-comparison', selectedTraces],
    queryFn: () => selectedTraces.length === 2 ? compareTraces(selectedTraces[0], selectedTraces[1]) : null,
    enabled: selectedTraces.length === 2,
  });

  const traceList = Array.isArray(traces) ? traces : [];
  const filteredTraces = traceList.filter((trace: Trace) =>
    !search || trace.run_id.toLowerCase().includes(search.toLowerCase())
  );

  const toggleTraceSelection = (runId: string) => {
    if (selectedTraces.includes(runId)) {
      setSelectedTraces(selectedTraces.filter(id => id !== runId));
    } else if (selectedTraces.length < 2) {
      setSelectedTraces([...selectedTraces, runId]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Execution Traces
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Deterministic execution traces with hash verification
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={compareMode ? 'primary' : 'outline'}
            size="sm"
            onClick={() => {
              setCompareMode(!compareMode);
              setSelectedTraces([]);
            }}
          >
            <GitCompare size={16} className="mr-1" />
            {compareMode ? 'Exit Compare' : 'Compare Mode'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw size={16} />
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardBody>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px] relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search by Run ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
              />
            </div>
            <select
              className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Compare Results */}
      {compareMode && selectedTraces.length === 2 && (
        <Card>
          <CardHeader title="Comparison Result" />
          <CardBody>
            {comparing ? (
              <div className="flex justify-center py-4"><Spinner /></div>
            ) : comparison ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <span className={cn(
                    'px-3 py-1 rounded-full text-sm font-medium',
                    comparison.identical ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                  )}>
                    {comparison.identical ? 'Deterministic Match' : 'Differences Found'}
                  </span>
                </div>
                {comparison.differences && comparison.differences.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Differences:</p>
                    {comparison.differences.map((diff: { field: string; trace1: unknown; trace2: unknown }, i: number) => (
                      <div key={i} className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-sm font-mono">
                        <span className="text-gray-500">{diff.field}:</span>
                        <span className="text-red-500 ml-2">{String(diff.trace1)}</span>
                        <span className="text-gray-400 mx-2">vs</span>
                        <span className="text-green-500">{String(diff.trace2)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500">Select two traces to compare</p>
            )}
          </CardBody>
        </Card>
      )}

      {/* Traces Table */}
      <Card>
        <CardHeader title={`Traces (${filteredTraces.length})`}>
          {compareMode && (
            <span className="text-sm text-gray-500">
              Selected: {selectedTraces.length}/2
            </span>
          )}
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-8"><Spinner size="lg" /></div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  {compareMode && (
                    <th className="px-4 py-3 w-12"></th>
                  )}
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Run ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Root Hash
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Steps
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredTraces.map((trace: Trace) => (
                  <tr
                    key={trace.run_id}
                    className={cn(
                      'hover:bg-gray-50 dark:hover:bg-gray-700/50',
                      compareMode && selectedTraces.includes(trace.run_id) && 'bg-blue-50 dark:bg-blue-900/20'
                    )}
                  >
                    {compareMode && (
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedTraces.includes(trace.run_id)}
                          onChange={() => toggleTraceSelection(trace.run_id)}
                          disabled={!selectedTraces.includes(trace.run_id) && selectedTraces.length >= 2}
                          className="rounded"
                        />
                      </td>
                    )}
                    <td className="px-4 py-3">
                      <span className="font-mono text-sm">{truncateId(trace.run_id)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs text-gray-500">
                        {trace.root_hash ? truncateId(trace.root_hash) : '--'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={trace.status} />
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {trace.steps?.length || 0}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(trace.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/console/traces/${trace.run_id}`}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <Eye size={16} />
                      </Link>
                    </td>
                  </tr>
                ))}
                {!filteredTraces.length && (
                  <tr>
                    <td colSpan={compareMode ? 7 : 6} className="px-4 py-8 text-center text-gray-500">
                      <GitBranch className="mx-auto mb-2 text-gray-400" size={32} />
                      No traces found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
