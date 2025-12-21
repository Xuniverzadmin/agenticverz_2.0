import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { Spinner } from '@/components/common';

// Lazy load pages
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const SkillsPage = lazy(() => import('@/pages/skills/SkillsPage'));
const JobSimulatorPage = lazy(() => import('@/pages/jobs/JobSimulatorPage'));
const JobRunnerPage = lazy(() => import('@/pages/jobs/JobRunnerPage'));
const TracesPage = lazy(() => import('@/pages/traces/TracesPage'));
const FailuresPage = lazy(() => import('@/pages/failures/FailuresPage'));
const RecoveryPage = lazy(() => import('@/pages/recovery/RecoveryPage'));
const BlackboardPage = lazy(() => import('@/pages/blackboard/BlackboardPage'));
const CreditsPage = lazy(() => import('@/pages/credits/CreditsPage'));
const MetricsPage = lazy(() => import('@/pages/metrics/MetricsPage'));
const SBAInspectorPage = lazy(() => import('@/pages/sba/SBAInspectorPage'));
const WorkerStudioHomePage = lazy(() => import('@/pages/workers/WorkerStudioHome'));
const WorkerExecutionConsolePage = lazy(() => import('@/pages/workers/WorkerExecutionConsole'));
const FounderOpsConsolePage = lazy(() => import('@/pages/ops/FounderOpsConsole'));

// Standalone console entry points (handle their own auth)
const GuardConsoleEntry = lazy(() => import('@/pages/guard/GuardConsoleEntry'));
const OpsConsoleEntry = lazy(() => import('@/pages/ops/OpsConsoleEntry'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <Spinner size="lg" />
    </div>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Standalone console entry points (handle their own auth) */}
        <Route path="/guard" element={<GuardConsoleEntry />} />
        <Route path="/guard/*" element={<GuardConsoleEntry />} />
        <Route path="/ops" element={<OpsConsoleEntry />} />
        <Route path="/ops/*" element={<OpsConsoleEntry />} />

        {/* Protected routes (main AOS console) */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="skills" element={<SkillsPage />} />

          {/* Execution */}
          <Route path="simulation" element={<JobSimulatorPage />} />
          <Route path="traces" element={<TracesPage />} />
          <Route path="traces/:runId" element={<TracesPage />} />
          <Route path="replay" element={<JobRunnerPage />} />
          <Route path="workers" element={<WorkerStudioHomePage />} />
          <Route path="workers/console" element={<WorkerExecutionConsolePage />} />
          <Route path="workers/history" element={<WorkerStudioHomePage />} />

          {/* Reliability */}
          <Route path="failures" element={<FailuresPage />} />
          <Route path="recovery" element={<RecoveryPage />} />

          {/* Data */}
          <Route path="memory" element={<BlackboardPage />} />

          {/* Governance */}
          <Route path="sba" element={<SBAInspectorPage />} />

          {/* Note: /ops is now a standalone console entry - see public routes above */}

          {/* System */}
          <Route path="credits" element={<CreditsPage />} />
          <Route path="metrics" element={<MetricsPage />} />

          {/* Legacy redirects */}
          <Route path="agents" element={<Navigate to="/skills" replace />} />
          <Route path="blackboard" element={<Navigate to="/memory" replace />} />
          <Route path="jobs/*" element={<Navigate to="/simulation" replace />} />
          <Route path="messaging" element={<Navigate to="/dashboard" replace />} />
        </Route>

        {/* Catch all - redirect to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}
