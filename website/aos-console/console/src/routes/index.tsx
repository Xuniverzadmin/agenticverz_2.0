import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { OnboardingRoute } from './OnboardingRoute';
import { Spinner } from '@/components/common';

// Lazy load pages
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const TracesPage = lazy(() => import('@/pages/traces/TracesPage'));
const RecoveryPage = lazy(() => import('@/pages/recovery/RecoveryPage'));
const CreditsPage = lazy(() => import('@/pages/credits/CreditsPage'));
const SBAInspectorPage = lazy(() => import('@/pages/sba/SBAInspectorPage'));
const WorkerStudioHomePage = lazy(() => import('@/pages/workers/WorkerStudioHome'));
const WorkerExecutionConsolePage = lazy(() => import('@/pages/workers/WorkerExecutionConsole'));
const FounderOpsConsolePage = lazy(() => import('@/pages/ops/FounderOpsConsole'));

// M28 DELETION (PIN-145): Removed SDK/demo/duplicate pages
// - DashboardPage: shell route, merged into /guard
// - SkillsPage: SDK concept, not customer value
// - JobSimulatorPage, JobRunnerPage: simulation tools → SDK/CLI
// - FailuresPage: duplicates /ops/incidents/patterns
// - BlackboardPage: legacy naming → /memory
// - MetricsPage: Grafana mirror, not product

// M25 Integration Loop pages
const IntegrationDashboard = lazy(() => import('@/pages/integration/IntegrationDashboard'));
const LoopStatusPage = lazy(() => import('@/pages/integration/LoopStatusPage'));

// Onboarding pages
const ConnectPage = lazy(() => import('@/pages/onboarding/ConnectPage'));
const SafetyPage = lazy(() => import('@/pages/onboarding/SafetyPage'));
const AlertsPage = lazy(() => import('@/pages/onboarding/AlertsPage'));
const VerifyPage = lazy(() => import('@/pages/onboarding/VerifyPage'));
const CompletePage = lazy(() => import('@/pages/onboarding/CompletePage'));

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

        {/* Onboarding routes (requires auth but not onboarding complete) */}
        <Route
          path="/onboarding/connect"
          element={
            <OnboardingRoute>
              <ConnectPage />
            </OnboardingRoute>
          }
        />
        <Route
          path="/onboarding/safety"
          element={
            <OnboardingRoute>
              <SafetyPage />
            </OnboardingRoute>
          }
        />
        <Route
          path="/onboarding/alerts"
          element={
            <OnboardingRoute>
              <AlertsPage />
            </OnboardingRoute>
          }
        />
        <Route
          path="/onboarding/verify"
          element={
            <OnboardingRoute>
              <VerifyPage />
            </OnboardingRoute>
          }
        />
        <Route
          path="/onboarding/complete"
          element={
            <OnboardingRoute>
              <CompletePage />
            </OnboardingRoute>
          }
        />

        {/* Standalone console entry points (handle their own auth) */}
        <Route path="/guard" element={<GuardConsoleEntry />} />
        <Route path="/guard/*" element={<GuardConsoleEntry />} />
        <Route path="/ops" element={<OpsConsoleEntry />} />
        <Route path="/ops/*" element={<OpsConsoleEntry />} />

        {/* Protected routes (main AOS console) - M28 streamlined */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* M28: Root redirects to /guard (unified console) */}
          <Route index element={<Navigate to="/guard" replace />} />

          {/* Execution - kept essential routes only */}
          <Route path="traces" element={<TracesPage />} />
          <Route path="traces/:runId" element={<TracesPage />} />
          <Route path="workers" element={<WorkerStudioHomePage />} />
          <Route path="workers/console" element={<WorkerExecutionConsolePage />} />

          {/* Reliability */}
          <Route path="recovery" element={<RecoveryPage />} />

          {/* M25 Integration Loop */}
          <Route path="integration" element={<IntegrationDashboard />} />
          <Route path="integration/loop/:incidentId" element={<LoopStatusPage />} />

          {/* Governance */}
          <Route path="sba" element={<SBAInspectorPage />} />

          {/* System */}
          <Route path="credits" element={<CreditsPage />} />

          {/* M28 DELETION (PIN-145): Removed routes
           * /dashboard - merged into /guard
           * /skills - SDK concept
           * /simulation - SDK/CLI tool
           * /replay - SDK/CLI tool
           * /failures - duplicates /ops/incidents/patterns
           * /memory - legacy naming
           * /metrics - Grafana mirror
           * /workers/history - duplication
           * Legacy redirects (/agents, /blackboard, /jobs/*, /messaging) - dead weight
           */}
        </Route>

        {/* Catch all - redirect to /guard (unified console) */}
        <Route path="*" element={<Navigate to="/guard" replace />} />
      </Routes>
    </Suspense>
  );
}
