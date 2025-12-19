// WorkerStudioHome - Landing Page for Worker Studio
// Explains what workers are, how deterministic OS works, and provides quick access

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Factory,
  Play,
  Zap,
  Shield,
  RefreshCw,
  Target,
  Clock,
  GitBranch,
  Sparkles,
  ChevronRight,
  CheckCircle,
  Layers,
  Cpu,
  FileText,
  History,
} from 'lucide-react';
import { listWorkerRuns, getWorkerHealth } from '@/api/worker';
import clsx from 'clsx';

interface WorkerCard {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'available' | 'coming_soon' | 'beta';
  moats: string[];
}

const AVAILABLE_WORKERS: WorkerCard[] = [
  {
    id: 'business-builder',
    name: 'Business Builder',
    description: 'Generate complete landing pages, copy, positioning, and marketing assets from a brand strategy.',
    icon: <Sparkles className="w-6 h-6" />,
    status: 'available',
    moats: ['M9', 'M10', 'M15', 'M17', 'M18', 'M19', 'M20'],
  },
  {
    id: 'code-debugger',
    name: 'Code Debugger',
    description: 'Analyze codebases, identify bugs, and suggest fixes with full traceability.',
    icon: <Cpu className="w-6 h-6" />,
    status: 'coming_soon',
    moats: ['M9', 'M10', 'M17', 'M19'],
  },
  {
    id: 'repo-fixer',
    name: 'Repo Fixer',
    description: 'Automatically fix CI failures, dependency issues, and code quality problems.',
    icon: <GitBranch className="w-6 h-6" />,
    status: 'coming_soon',
    moats: ['M9', 'M10', 'M17', 'M18', 'M19'],
  },
  {
    id: 'research-analyst',
    name: 'Research Analyst',
    description: 'Deep research on markets, competitors, and trends with structured output.',
    icon: <FileText className="w-6 h-6" />,
    status: 'coming_soon',
    moats: ['M15', 'M17', 'M19'],
  },
];

const MOAT_BADGES: Record<string, { label: string; color: string }> = {
  M4: { label: 'Golden Replay', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' },
  M9: { label: 'Failure Catalog', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300' },
  M10: { label: 'Recovery Engine', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
  M15: { label: 'SBA', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' },
  M17: { label: 'CARE Routing', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' },
  M18: { label: 'Drift Detection', color: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300' },
  M19: { label: 'Policy Layer', color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300' },
  M20: { label: 'Live Governance', color: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300' },
};

const FEATURES = [
  {
    icon: <Target className="w-5 h-5" />,
    title: 'Deterministic Execution',
    description: 'Every run produces identical results with the same inputs. Replay any execution perfectly.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Policy Governance',
    description: 'Constitutional rules enforce brand guidelines, safety constraints, and quality standards.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Auto-Recovery',
    description: 'Failures are detected, cataloged, and recovered automatically without human intervention.',
  },
  {
    icon: <Zap className="w-5 h-5" />,
    title: 'Complexity-Aware Routing',
    description: 'Tasks are routed to the optimal agent based on complexity, drift, and historical performance.',
  },
];

export function WorkerStudioHome() {
  const navigate = useNavigate();
  const [recentRuns, setRecentRuns] = useState<Array<{
    run_id: string;
    task: string;
    status: string;
    success: boolean | null;
    created_at: string;
    total_latency_ms: number | null;
  }>>([]);
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    version: string;
    runs_in_memory: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [runsData, health] = await Promise.all([
          listWorkerRuns(5).catch(() => ({ runs: [], total: 0 })),
          getWorkerHealth().catch(() => null),
        ]);
        setRecentRuns(runsData.runs);
        setHealthStatus(health);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleRunWorker = (workerId: string) => {
    navigate(`/workers/console?worker=${workerId}`);
  };

  const handleViewRun = (runId: string) => {
    navigate(`/workers/console?replay=${runId}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
              <Factory className="w-10 h-10 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Worker Studio
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Run deterministic AI workers that produce <strong>predictable, auditable, recoverable</strong> results.
            Every execution is replayable. Every failure is recoverable.
          </p>
        </div>

        {/* What Makes This Different */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 mb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
            The Machine-Native Difference
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feature, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Workers Grid */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Available Workers
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {AVAILABLE_WORKERS.map((worker) => (
              <div
                key={worker.id}
                className={clsx(
                  'bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden border-2 transition-all',
                  worker.status === 'available'
                    ? 'border-purple-200 dark:border-purple-800 hover:border-purple-400 dark:hover:border-purple-600 hover:shadow-lg cursor-pointer'
                    : 'border-gray-200 dark:border-gray-700 opacity-75'
                )}
                onClick={() => worker.status === 'available' && handleRunWorker(worker.id)}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={clsx(
                        'p-2 rounded-lg',
                        worker.status === 'available'
                          ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-500'
                      )}>
                        {worker.icon}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {worker.name}
                        </h3>
                        <span className={clsx(
                          'text-xs font-medium px-2 py-0.5 rounded-full',
                          worker.status === 'available' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
                          worker.status === 'coming_soon' && 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
                          worker.status === 'beta' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                        )}>
                          {worker.status === 'available' ? 'Available' : worker.status === 'beta' ? 'Beta' : 'Coming Soon'}
                        </span>
                      </div>
                    </div>
                    {worker.status === 'available' && (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {worker.description}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {worker.moats.map((moat) => (
                      <span
                        key={moat}
                        className={clsx('px-2 py-0.5 text-xs font-medium rounded', MOAT_BADGES[moat]?.color)}
                      >
                        {MOAT_BADGES[moat]?.label || moat}
                      </span>
                    ))}
                  </div>
                </div>
                {worker.status === 'available' && (
                  <div className="px-6 py-3 bg-purple-50 dark:bg-purple-900/20 border-t border-purple-100 dark:border-purple-800">
                    <button className="flex items-center gap-2 text-purple-600 dark:text-purple-400 font-medium text-sm hover:text-purple-700 dark:hover:text-purple-300">
                      <Play className="w-4 h-4" />
                      Run Worker
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Recent Runs & System Status */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Recent Runs */}
          <div className="md:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <History className="w-5 h-5 text-gray-500" />
                Recent Runs
              </h2>
              <button
                onClick={() => navigate('/workers/history')}
                className="text-sm text-purple-600 dark:text-purple-400 hover:underline"
              >
                View All
              </button>
            </div>
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading...</div>
            ) : recentRuns.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">No runs yet</p>
                <button
                  onClick={() => handleRunWorker('business-builder')}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  <Play className="w-4 h-4" />
                  Start Your First Run
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {recentRuns.map((run) => (
                  <div
                    key={run.run_id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                    onClick={() => handleViewRun(run.run_id)}
                  >
                    <div className="flex items-center gap-3">
                      {run.success === true && <CheckCircle className="w-5 h-5 text-green-500" />}
                      {run.success === false && <RefreshCw className="w-5 h-5 text-red-500" />}
                      {run.success === null && <Clock className="w-5 h-5 text-yellow-500" />}
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-xs">
                          {run.task}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(run.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {run.total_latency_ms && (
                        <span className="text-xs text-gray-500">
                          {(run.total_latency_ms / 1000).toFixed(1)}s
                        </span>
                      )}
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* System Status */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <Layers className="w-5 h-5 text-gray-500" />
              System Status
            </h2>
            {healthStatus ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Status</span>
                  <span className={clsx(
                    'px-2 py-0.5 text-xs font-medium rounded-full',
                    healthStatus.status === 'healthy'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                  )}>
                    {healthStatus.status}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Version</span>
                  <span className="text-sm font-mono text-gray-900 dark:text-white">
                    {healthStatus.version}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Active Runs</span>
                  <span className="text-sm font-mono text-gray-900 dark:text-white">
                    {healthStatus.runs_in_memory}
                  </span>
                </div>
                <hr className="border-gray-200 dark:border-gray-700" />
                <div className="text-xs text-gray-500">
                  <p className="font-medium mb-2">Integrated Moats:</p>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(MOAT_BADGES).map((moat) => (
                      <span key={moat} className={clsx('px-1.5 py-0.5 rounded text-xs', MOAT_BADGES[moat].color)}>
                        {moat}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Unable to connect to worker service
              </div>
            )}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-center gap-4 p-4 bg-gradient-to-r from-purple-100 to-indigo-100 dark:from-purple-900/30 dark:to-indigo-900/30 rounded-2xl">
            <div className="text-left">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Ready to see deterministic AI in action?
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Run the Business Builder Worker and watch every moat operate in real-time.
              </p>
            </div>
            <button
              onClick={() => handleRunWorker('business-builder')}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 shadow-lg hover:shadow-xl transition-all"
            >
              <Play className="w-5 h-5" />
              Launch Worker Console
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WorkerStudioHome;
