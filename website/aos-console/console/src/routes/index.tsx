/**
 * AOS Console Routes
 *
 * M28 Route Migration Plan (PIN-147):
 *
 * TARGET ARCHITECTURE:
 * - console.agenticverz.com → CUSTOMER routes (guard/*, billing, keys)
 * - fops.agenticverz.com    → FOUNDER routes (ops/*, traces, workers, sba)
 *
 * CURRENT STATE:
 * - Single domain with path-based routing
 * - /guard/* → Customer Console (AIConsoleApp)
 * - /ops/*   → Founder Console (OpsConsoleEntry)
 *
 * See: docs/M28_ROUTE_OWNERSHIP.md for authoritative route ownership
 */

import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { OnboardingRoute } from './OnboardingRoute';
import { Spinner } from '@/components/common';

// =============================================================================
// CUSTOMER PAGES (Target: console.agenticverz.com)
// =============================================================================
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const CreditsPage = lazy(() => import('@/pages/credits/CreditsPage'));

// =============================================================================
// FOUNDER PAGES (Target: fops.agenticverz.com)
// =============================================================================
const TracesPage = lazy(() => import('@/pages/traces/TracesPage'));
const TraceDetailPage = lazy(() => import('@/pages/traces/TraceDetailPage'));
const RecoveryPage = lazy(() => import('@/pages/recovery/RecoveryPage'));
const SBAInspectorPage = lazy(() => import('@/pages/sba/SBAInspectorPage'));
const WorkerStudioHomePage = lazy(() => import('@/pages/workers/WorkerStudioHome'));
const WorkerExecutionConsolePage = lazy(() => import('@/pages/workers/WorkerExecutionConsole'));

// M28 DELETION (PIN-145): Removed SDK/demo/duplicate pages
// - DashboardPage, SkillsPage, JobSimulatorPage, FailuresPage, BlackboardPage, MetricsPage

// M25 Integration Loop (FOUNDER)
const IntegrationDashboard = lazy(() => import('@/pages/integration/IntegrationDashboard'));
const LoopStatusPage = lazy(() => import('@/pages/integration/LoopStatusPage'));

// Phase 5E-1: Founder Decision Timeline (FOUNDER)
const FounderTimelinePage = lazy(() => import('@/pages/founder/FounderTimelinePage'));

// Phase 5E-2: Kill-Switch Controls (FOUNDER)
const FounderControlsPage = lazy(() => import('@/pages/founder/FounderControlsPage'));

// =============================================================================
// ONBOARDING PAGES (Shared - pre-console assignment)
// =============================================================================
const ConnectPage = lazy(() => import('@/pages/onboarding/ConnectPage'));
const SafetyPage = lazy(() => import('@/pages/onboarding/SafetyPage'));
const AlertsPage = lazy(() => import('@/pages/onboarding/AlertsPage'));
const VerifyPage = lazy(() => import('@/pages/onboarding/VerifyPage'));
const CompletePage = lazy(() => import('@/pages/onboarding/CompletePage'));

// =============================================================================
// CONSOLE ENTRY POINTS (Standalone - handle their own auth)
// =============================================================================
// CUSTOMER: /guard/* → console.agenticverz.com (future)
const AIConsoleApp = lazy(() => import('@ai-console/app/AIConsoleApp'));
// FOUNDER: /ops/* → fops.agenticverz.com (future)
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

        {/* =================================================================
         * CUSTOMER CONSOLE (Target: console.agenticverz.com)
         * Owner: CUSTOMER | See: docs/M28_ROUTE_OWNERSHIP.md
         * ================================================================= */}
        <Route path="/guard" element={<AIConsoleApp />} />
        <Route path="/guard/*" element={<AIConsoleApp />} />

        {/* =================================================================
         * FOUNDER OPS CONSOLE (Target: fops.agenticverz.com)
         * Owner: FOUNDER | See: docs/M28_ROUTE_OWNERSHIP.md
         * ================================================================= */}
        <Route path="/ops" element={<OpsConsoleEntry />} />
        <Route path="/ops/*" element={<OpsConsoleEntry />} />

        {/* Protected routes (FOUNDER pages still in transition) */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* M28: Root redirects to /guard (Customer Console) */}
          <Route index element={<Navigate to="/guard" replace />} />

          {/* =========================================================
           * FOUNDER ROUTES (Target: fops.agenticverz.com)
           * These routes will migrate to the founder domain
           * ========================================================= */}

          {/* Execution (FOUNDER) */}
          <Route path="traces" element={<TracesPage />} />
          <Route path="traces/:runId" element={<TraceDetailPage />} />
          <Route path="workers" element={<WorkerStudioHomePage />} />
          <Route path="workers/console" element={<WorkerExecutionConsolePage />} />

          {/* Reliability (FOUNDER) */}
          <Route path="recovery" element={<RecoveryPage />} />

          {/* M25 Integration Loop (FOUNDER) */}
          <Route path="integration" element={<IntegrationDashboard />} />
          <Route path="integration/loop/:incidentId" element={<LoopStatusPage />} />

          {/* Phase 5E-1: Founder Decision Timeline (FOUNDER) */}
          <Route path="founder/timeline" element={<FounderTimelinePage />} />

          {/* Phase 5E-2: Kill-Switch Controls (FOUNDER) */}
          <Route path="founder/controls" element={<FounderControlsPage />} />

          {/* Governance (FOUNDER) */}
          <Route path="sba" element={<SBAInspectorPage />} />

          {/* =========================================================
           * CUSTOMER ROUTES (Target: console.agenticverz.com)
           * ========================================================= */}

          {/* Billing (CUSTOMER) */}
          <Route path="credits" element={<CreditsPage />} />

          {/* M28 DELETION (PIN-145): Routes permanently removed
           * See docs/M28_ROUTE_OWNERSHIP.md for DELETE list
           */}
        </Route>

        {/* Catch all - redirect to /guard (unified console) */}
        <Route path="*" element={<Navigate to="/guard" replace />} />
      </Routes>
    </Suspense>
  );
}
