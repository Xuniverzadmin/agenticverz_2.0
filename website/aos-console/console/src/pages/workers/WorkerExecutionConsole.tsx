// WorkerExecutionConsole - Real-Time Worker Execution UI (Enhanced)
// 5-pane layout with artifact preview, worker selector, run history, replay, and export

import { useState, useCallback, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';

// === DEBUG LOGGING ===
const DEBUG = true;
const log = (area: string, message: string, data?: unknown) => {
  if (DEBUG) {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
    console.log(`%c[${timestamp}] [CONSOLE-UI] [${area}]`, 'color: #f59e0b; font-weight: bold', message, data ?? '');
  }
};
import {
  Play,
  Square,
  RotateCcw,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Hash,
  Download,
  History,
  ChevronDown,
  Sun,
  Moon,
  Sparkles,
  RefreshCw,
  FileJson,
  FileText,
  File,
  ArrowLeft,
} from 'lucide-react';
import { useWorkerStream } from '@/hooks/useWorkerStream';
import { startWorkerRun, validateBrand, listWorkerRuns, getRunEvents, replayWorkerRun } from '@/api/worker';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { LiveLogStream } from './components/LiveLogStream';
import { RoutingDashboard } from './components/RoutingDashboard';
import { FailuresRecoveryPanel } from './components/FailuresRecoveryPanel';
import { ArtifactPreview } from './components/ArtifactPreview';
import type { BrandRequest, RunHistoryItem, WorkerDefinition } from '@/types/worker';
import clsx from 'clsx';

// Available workers
const WORKERS: WorkerDefinition[] = [
  {
    id: 'business-builder',
    name: 'Business Builder',
    description: 'Generate landing pages, copy, positioning',
    status: 'available',
    moats: ['M9', 'M10', 'M15', 'M17', 'M18', 'M19', 'M20'],
  },
  {
    id: 'code-debugger',
    name: 'Code Debugger',
    description: 'Analyze and fix code issues',
    status: 'coming_soon',
    moats: ['M9', 'M10', 'M17', 'M19'],
  },
  {
    id: 'repo-fixer',
    name: 'Repo Fixer',
    description: 'Fix CI failures and dependencies',
    status: 'coming_soon',
    moats: ['M9', 'M10', 'M17', 'M18', 'M19'],
  },
];

// Default brand for demo
// NOTE: tone.primary must be: casual, neutral, professional, formal, luxury
// NOTE: target_audience must be: b2c_consumer, b2c_prosumer, b2b_smb, b2b_enterprise, b2b_developer
const DEFAULT_BRAND: BrandRequest = {
  company_name: 'TechStartup AI',
  mission: 'Making AI accessible to every business through simple powerful tools',
  value_proposition: 'AI-powered solutions that save businesses time and money while being easy to use',
  tagline: 'AI Made Simple',
  target_audience: ['b2b_smb'],
  tone: {
    primary: 'professional',
    avoid: [],
  },
  visual: {
    primary_color: '#6366f1',
    secondary_color: '#8b5cf6',
  },
};

// Export formats
type ExportFormat = 'json' | 'txt' | 'csv';

export function WorkerExecutionConsole() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialWorker = searchParams.get('worker') || 'business-builder';
  const replayId = searchParams.get('replay');

  const [selectedWorker, setSelectedWorker] = useState(initialWorker);
  const [workerDropdownOpen, setWorkerDropdownOpen] = useState(false);
  const [task, setTask] = useState(
    'Create a landing page hero section with compelling copy and a clear CTA'
  );
  const [brandJson, setBrandJson] = useState(JSON.stringify(DEFAULT_BRAND, null, 2));
  const [runId, setRunId] = useState<string | null>(replayId);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  } | null>(null);

  // Run history
  const [runHistory, setRunHistory] = useState<RunHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Layout & Theme
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.classList.contains('dark');
    }
    return false;
  });
  const [artifactExpanded, setArtifactExpanded] = useState(false);
  const [showBrandEditor, setShowBrandEditor] = useState(false);

  log('INIT', `Component mount - runId: ${runId}, replayId: ${replayId}`);

  // Track if run completed to ignore SSE close errors
  const runCompletedRef = useRef(false);

  const { state, isConnected, reset } = useWorkerStream(runId, {
    onComplete: (success) => {
      log('CALLBACK', `onComplete called - success: ${success}`);
      console.log('Worker completed:', success);
      runCompletedRef.current = true; // Mark as completed
      loadRunHistory(); // Refresh history
    },
    onError: (err) => {
      log('CALLBACK', '❌ onError called', err);
      // Don't show error if run already completed (SSE close after success is expected)
      if (runCompletedRef.current) {
        log('CALLBACK', 'Ignoring SSE close error - run already completed');
        return;
      }
      console.error('Stream error:', err);
      setError('Connection lost. Please try again.');
    },
  });

  // Log state changes
  useEffect(() => {
    log('STATE-CHANGE', `state.status: ${state.status}, logs: ${state.logs.length}, stages: ${state.stages.filter(s => s.status !== 'pending').length}/8`);
  }, [state.status, state.logs.length, state.stages]);

  const currentStageIndex = state.stages.findIndex(
    (s) => s.status === 'running' || s.status === 'pending'
  );

  // Load run history
  const loadRunHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const data = await listWorkerRuns(10);
      setRunHistory(data.runs);
    } catch (e) {
      console.error('Failed to load run history:', e);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    loadRunHistory();
  }, [loadRunHistory]);

  // Handle replay from URL param
  useEffect(() => {
    if (replayId && replayId !== runId) {
      setRunId(replayId);
    }
  }, [replayId, runId]);

  // Toggle dark mode
  const toggleDarkMode = useCallback(() => {
    setDarkMode((prev) => {
      const newMode = !prev;
      if (newMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return newMode;
    });
  }, []);

  const handleValidate = useCallback(async () => {
    setError(null);
    setValidationResult(null);
    try {
      const brand = JSON.parse(brandJson) as BrandRequest;
      const result = await validateBrand(brand);
      setValidationResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid JSON');
    }
  }, [brandJson]);

  const handleStart = useCallback(async () => {
    log('ACTION', '▶️ handleStart called', { task: task.slice(0, 50) });
    setIsStarting(true);
    setError(null);
    runCompletedRef.current = false; // Reset for new run
    reset();

    try {
      const brand = JSON.parse(brandJson) as BrandRequest;
      log('ACTION', '📤 Calling startWorkerRun API', { task, brandCompanyName: brand.company_name });

      const response = await startWorkerRun({
        task,
        brand,
        stream: true,
      });

      log('ACTION', `✅ Got run_id: ${response.run_id} - setting state`);
      setRunId(response.run_id);
      setSearchParams({ worker: selectedWorker });
      log('ACTION', '🔄 runId state updated - SSE hook should connect now');
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : 'Failed to start worker';
      log('ACTION', `❌ startWorkerRun failed: ${errMsg}`, e);
      setError(errMsg);
      setIsStarting(false);
    }
  }, [task, brandJson, reset, selectedWorker, setSearchParams]);

  const handleReplay = useCallback(async (historyRunId: string) => {
    setShowHistory(false);
    setRunId(historyRunId);
    setSearchParams({ worker: selectedWorker, replay: historyRunId });
  }, [selectedWorker, setSearchParams]);

  const handleReplayWithToken = useCallback(async () => {
    if (!state.replayToken) return;

    setIsStarting(true);
    setError(null);
    reset();

    try {
      const response = await replayWorkerRun(state.replayToken);
      setRunId(response.run_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to replay');
      setIsStarting(false);
    }
  }, [state.replayToken, reset]);

  const handleStop = useCallback(() => {
    reset();
    setRunId(null);
    setIsStarting(false);
    setSearchParams({ worker: selectedWorker });
  }, [reset, selectedWorker, setSearchParams]);

  const handleReset = useCallback(() => {
    reset();
    setRunId(null);
    setError(null);
    setIsStarting(false);
    setValidationResult(null);
    setSearchParams({ worker: selectedWorker });
  }, [reset, selectedWorker, setSearchParams]);

  // Export trace
  const handleExport = useCallback((format: ExportFormat) => {
    const exportData = {
      run_id: state.runId,
      task: state.task,
      status: state.status,
      stages: state.stages,
      logs: state.logs,
      routingDecisions: state.routingDecisions,
      policyEvents: state.policyEvents,
      driftEvents: state.driftEvents,
      artifacts: state.artifacts,
      recoveries: state.recoveries,
      totalTokens: state.totalTokens,
      totalLatency: state.totalLatency,
      exportedAt: new Date().toISOString(),
    };

    let content: string;
    let mimeType: string;
    let extension: string;

    switch (format) {
      case 'json':
        content = JSON.stringify(exportData, null, 2);
        mimeType = 'application/json';
        extension = 'json';
        break;
      case 'txt':
        content = formatTraceAsTxt(exportData);
        mimeType = 'text/plain';
        extension = 'txt';
        break;
      case 'csv':
        content = formatTraceAsCsv(exportData);
        mimeType = 'text/csv';
        extension = 'csv';
        break;
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `worker-trace-${state.runId || 'unknown'}.${extension}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [state]);

  const isRunning = state.status === 'running';
  const isCompleted = state.status === 'completed';
  const isFailed = state.status === 'failed';
  const currentWorker = WORKERS.find((w) => w.id === selectedWorker) || WORKERS[0];

  return (
    <div className={clsx('h-screen flex flex-col', darkMode ? 'dark' : '')}>
      <div className="h-full flex flex-col bg-gray-100 dark:bg-gray-900">
        {/* Top Bar */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Left: Worker Selector & Title */}
            <div className="flex items-center gap-4">
              <a
                href="/workers"
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <ArrowLeft className="w-5 h-5" />
              </a>

              {/* Worker Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setWorkerDropdownOpen(!workerDropdownOpen)}
                  disabled={isRunning}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg font-medium hover:bg-purple-100 dark:hover:bg-purple-900/50 disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  {currentWorker.name}
                  <ChevronDown className="w-4 h-4" />
                </button>
                {workerDropdownOpen && (
                  <div className="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                    {WORKERS.map((worker) => (
                      <button
                        key={worker.id}
                        onClick={() => {
                          if (worker.status === 'available') {
                            setSelectedWorker(worker.id);
                            setSearchParams({ worker: worker.id });
                          }
                          setWorkerDropdownOpen(false);
                        }}
                        disabled={worker.status !== 'available'}
                        className={clsx(
                          'w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg',
                          worker.status !== 'available' && 'opacity-50 cursor-not-allowed'
                        )}
                      >
                        <div className="font-medium text-gray-900 dark:text-white">
                          {worker.name}
                          {worker.status === 'coming_soon' && (
                            <span className="ml-2 text-xs text-gray-500">(Coming Soon)</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {worker.description}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">
                  Execution Console
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Real-Time Worker Monitor
                </p>
              </div>
            </div>

            {/* Right: Status & Controls */}
            <div className="flex items-center gap-4">
              {/* Connection Status */}
              {isConnected && (
                <span className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  Live
                </span>
              )}

              {/* Run Status */}
              <div
                className={clsx(
                  'px-3 py-1 rounded-full text-sm font-medium',
                  state.status === 'idle' && 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
                  state.status === 'running' && 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
                  state.status === 'completed' && 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
                  state.status === 'failed' && 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                )}
              >
                {state.status === 'idle' && 'Ready'}
                {state.status === 'running' && 'Running'}
                {state.status === 'completed' && 'Completed'}
                {state.status === 'failed' && 'Failed'}
              </div>

              {/* History Button */}
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg relative"
              >
                <History className="w-5 h-5" />
                {runHistory.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-purple-500 text-white text-xs rounded-full flex items-center justify-center">
                    {runHistory.length}
                  </span>
                )}
              </button>

              {/* Dark Mode Toggle */}
              <button
                onClick={toggleDarkMode}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Run History Dropdown */}
          {showHistory && (
            <div className="absolute right-4 top-16 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 max-h-96 overflow-hidden">
              <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <span className="font-medium text-gray-900 dark:text-white">Run History</span>
                <button
                  onClick={loadRunHistory}
                  className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  <RefreshCw className={clsx('w-4 h-4', loadingHistory && 'animate-spin')} />
                </button>
              </div>
              <div className="overflow-y-auto max-h-80">
                {runHistory.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">No previous runs</div>
                ) : (
                  runHistory.map((run) => (
                    <button
                      key={run.run_id}
                      onClick={() => handleReplay(run.run_id)}
                      className="w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-0"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {run.success === true && <CheckCircle className="w-4 h-4 text-green-500" />}
                          {run.success === false && <XCircle className="w-4 h-4 text-red-500" />}
                          {run.success === null && <Clock className="w-4 h-4 text-yellow-500" />}
                          <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-48">
                            {run.task}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {run.total_latency_ms ? `${(run.total_latency_ms / 1000).toFixed(1)}s` : '-'}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(run.created_at).toLocaleString()}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Task Input Row */}
          <div className="mt-3 flex items-start gap-3">
            <div className="flex-1">
              <textarea
                value={task}
                onChange={(e) => setTask(e.target.value)}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 text-sm"
                rows={2}
                placeholder="Describe what you want the worker to create..."
              />
            </div>

            <button
              onClick={() => setShowBrandEditor(!showBrandEditor)}
              className="px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              Brand Config
            </button>

            {/* Action Buttons */}
            {!isRunning && !isCompleted && !isFailed && (
              <button
                onClick={handleStart}
                disabled={isStarting || !task.trim()}
                className="flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isStarting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {isStarting ? 'Starting...' : 'Run'}
              </button>
            )}

            {isRunning && (
              <button
                onClick={handleStop}
                className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
              >
                <Square className="w-4 h-4" />
                Stop
              </button>
            )}

            {(isCompleted || isFailed) && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  <RotateCcw className="w-4 h-4" />
                  New
                </button>
                {state.replayToken && (
                  <button
                    onClick={handleReplayWithToken}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    title="Replay this exact execution (M4 Golden Replay)"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Replay
                  </button>
                )}
                {/* Export Dropdown */}
                <div className="relative group">
                  <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                  <div className="absolute top-full right-0 mt-1 w-40 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                    <button
                      onClick={() => handleExport('json')}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 rounded-t-lg"
                    >
                      <FileJson className="w-4 h-4" />
                      JSON
                    </button>
                    <button
                      onClick={() => handleExport('txt')}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
                    >
                      <FileText className="w-4 h-4" />
                      Text
                    </button>
                    <button
                      onClick={() => handleExport('csv')}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 rounded-b-lg"
                    >
                      <File className="w-4 h-4" />
                      CSV
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Brand Editor (collapsible) */}
          {showBrandEditor && (
            <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Brand JSON</span>
                <button
                  onClick={handleValidate}
                  disabled={isRunning}
                  className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-500"
                >
                  Validate
                </button>
              </div>
              <textarea
                value={brandJson}
                onChange={(e) => setBrandJson(e.target.value)}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-xs resize-none focus:ring-2 focus:ring-purple-500"
                rows={6}
              />
              {validationResult && (
                <div className={clsx(
                  'mt-2 p-2 rounded text-sm',
                  validationResult.valid
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                    : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                )}>
                  {validationResult.valid ? 'Valid brand schema' : `Errors: ${validationResult.errors.join(', ')}`}
                </div>
              )}
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Stats when running or completed */}
          {(isRunning || isCompleted) && (
            <div className="mt-3 flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
              {state.runId && (
                <span className="flex items-center gap-1">
                  <Hash className="w-4 h-4" />
                  {state.runId.slice(0, 8)}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Zap className="w-4 h-4" />
                {state.totalTokens.toLocaleString()} tokens
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {(state.totalLatency / 1000).toFixed(1)}s
              </span>
              <span className="flex items-center gap-1">
                Stages: {state.stages.filter(s => s.status === 'completed' || s.status === 'recovered').length}/{state.stages.length}
              </span>
            </div>
          )}
        </div>

        {/* 5-Pane Grid Layout */}
        <div className="flex-1 grid grid-cols-3 grid-rows-2 gap-1 p-1 min-h-0">
          {/* Top Left - Execution Timeline */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
            <ExecutionTimeline
              stages={state.stages}
              currentStageIndex={currentStageIndex === -1 ? state.stages.length : currentStageIndex}
            />
          </div>

          {/* Top Center - Live Log Stream */}
          <div className="rounded-lg shadow-sm overflow-hidden">
            <LiveLogStream logs={state.logs} autoScroll={true} />
          </div>

          {/* Top Right - Artifact Preview (WOW moment) */}
          <div className="rounded-lg shadow-sm overflow-hidden row-span-2">
            <ArtifactPreview
              artifacts={state.artifacts}
              artifactContents={state.artifactContents}
              isExpanded={artifactExpanded}
              onToggleExpand={() => setArtifactExpanded(!artifactExpanded)}
            />
          </div>

          {/* Bottom Left - Routing Dashboard */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
            <RoutingDashboard
              routingDecisions={state.routingDecisions}
              driftEvents={state.driftEvents}
              artifacts={state.artifacts}
            />
          </div>

          {/* Bottom Center - Failures & Recovery Panel */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
            <FailuresRecoveryPanel
              policyEvents={state.policyEvents}
              driftEvents={state.driftEvents}
              recoveries={state.recoveries}
              logs={state.logs}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper functions for export
function formatTraceAsTxt(data: Record<string, unknown>): string {
  const lines: string[] = [
    '═══════════════════════════════════════════════════════════════',
    '                    WORKER EXECUTION TRACE',
    '═══════════════════════════════════════════════════════════════',
    '',
    `Run ID: ${data.run_id}`,
    `Task: ${data.task}`,
    `Status: ${data.status}`,
    `Total Tokens: ${data.totalTokens}`,
    `Total Latency: ${data.totalLatency}ms`,
    `Exported At: ${data.exportedAt}`,
    '',
    '───────────────────────────────────────────────────────────────',
    '                         STAGES',
    '───────────────────────────────────────────────────────────────',
  ];

  const stages = data.stages as Array<{ id: string; name: string; status: string; duration_ms?: number }>;
  stages.forEach((stage, i) => {
    lines.push(`${i + 1}. ${stage.name} [${stage.status}] ${stage.duration_ms ? `(${stage.duration_ms}ms)` : ''}`);
  });

  lines.push('');
  lines.push('───────────────────────────────────────────────────────────────');
  lines.push('                          LOGS');
  lines.push('───────────────────────────────────────────────────────────────');

  const logs = data.logs as Array<{ level: string; agent: string; message: string }>;
  logs.forEach((log) => {
    lines.push(`[${log.level.toUpperCase()}] [${log.agent}] ${log.message}`);
  });

  return lines.join('\n');
}

function formatTraceAsCsv(data: Record<string, unknown>): string {
  const logs = data.logs as Array<{ level: string; agent: string; message: string; stage_id: string }>;
  const lines = ['level,agent,stage,message'];
  logs.forEach((log) => {
    lines.push(`"${log.level}","${log.agent}","${log.stage_id}","${log.message.replace(/"/g, '""')}"`);
  });
  return lines.join('\n');
}

export default WorkerExecutionConsole;
