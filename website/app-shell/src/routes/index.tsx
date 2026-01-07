/**
 * AOS App Shell Routes
 *
 * Phase 1.2 Frontend Realignment (PIN-317):
 *
 * ROUTE ARCHITECTURE:
 * - /guard/*      → CUSTOMER routes (AIConsoleApp)
 * - /fops/*       → FOUNDER routes (all founder pages)
 * - /onboarding/* → Pre-console setup flow
 *
 * NAMESPACE BOUNDARIES:
 * - Customer Console: /guard/* (guard/overview, guard/activity, etc.)
 * - Founder Console:  /fops/*  (fops/traces, fops/workers, fops/ops, etc.)
 * - Onboarding:       /onboarding/* (shared pre-console flow)
 *
 * ROUTE GUARDS:
 * - ProtectedRoute: Requires authentication + onboarding complete
 * - FounderRoute:   Requires audience="fops" (founder token)
 * - OnboardingRoute: Requires auth but NOT onboarding complete
 *
 * REDIRECT CONTRACT:
 * - Unauthenticated   → /login
 * - Authenticated but not onboarded → /onboarding/connect
 * - Authenticated + onboarded → /guard (customer) or /fops/* (founder)
 * - Customer token accessing /fops/* → /guard (silent, no error)
 * - Unknown routes → /guard
 *
 * See: docs/M28_ROUTE_OWNERSHIP.md for authoritative route ownership
 */

import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { OnboardingRoute } from './OnboardingRoute';
import { FounderRoute } from './FounderRoute';
import { Spinner } from '@/components/common';

// =============================================================================
// CUSTOMER PAGES (Target: console.agenticverz.com)
// =============================================================================
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const CreditsPage = lazy(() => import('@/pages/credits/CreditsPage'));

// =============================================================================
// L2.1 DOMAIN PAGES (Preflight: preflight-console.agenticverz.com)
// Projection-driven pages from ui_projection_lock.json
// Reference: PIN-352 (L2.1 UI Projection Pipeline)
// =============================================================================
const OverviewPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.OverviewPage })));
const ActivityPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.ActivityPage })));
const IncidentsPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.IncidentsPage })));
const PoliciesPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.PoliciesPage })));
const LogsPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.LogsPage })));

// =============================================================================
// FOUNDER PAGES (Target: fops.agenticverz.com) - Now in website/fops/
// =============================================================================
const TracesPage = lazy(() => import('@fops/pages/traces/TracesPage'));
const TraceDetailPage = lazy(() => import('@fops/pages/traces/TraceDetailPage'));
const RecoveryPage = lazy(() => import('@fops/pages/recovery/RecoveryPage'));
const SBAInspectorPage = lazy(() => import('@fops/pages/sba/SBAInspectorPage'));
const WorkerStudioHomePage = lazy(() => import('@fops/pages/workers/WorkerStudioHome'));
const WorkerExecutionConsolePage = lazy(() => import('@fops/pages/workers/WorkerExecutionConsole'));

// M28 DELETION (PIN-145): Removed SDK/demo/duplicate pages
// - DashboardPage, SkillsPage, JobSimulatorPage, FailuresPage, BlackboardPage, MetricsPage

// M25 Integration Loop (FOUNDER)
const IntegrationDashboard = lazy(() => import('@fops/pages/integration/IntegrationDashboard'));
const LoopStatusPage = lazy(() => import('@fops/pages/integration/LoopStatusPage'));

// Phase 5E-1: Founder Decision Timeline (FOUNDER)
const FounderTimelinePage = lazy(() => import('@fops/pages/founder/FounderTimelinePage'));

// Phase 5E-2: Kill-Switch Controls (FOUNDER)
const FounderControlsPage = lazy(() => import('@fops/pages/founder/FounderControlsPage'));

// Phase H1: Replay UX Enablement (FOUNDER - READ-ONLY)
const ReplayIndexPage = lazy(() => import('@fops/pages/founder/ReplayIndexPage'));
const ReplaySliceViewer = lazy(() => import('@fops/pages/founder/ReplaySliceViewer'));

// Phase H2: Cost Simulation v1 (FOUNDER - Advisory Only)
const ScenarioBuilderPage = lazy(() => import('@fops/pages/founder/ScenarioBuilderPage'));

// Phase H3: Founder Explorer (FOUNDER - READ-ONLY Cross-Tenant)
const FounderExplorerPage = lazy(() => import('@fops/pages/founder/FounderExplorerPage'));

// PIN-333: AUTO_EXECUTE Review Dashboard (FOUNDER - READ-ONLY Evidence)
const AutoExecuteReviewPage = lazy(() => import('@fops/pages/founder/AutoExecuteReviewPage'));

// Unified Founder Review Dashboard (AUTO_EXECUTE + Contract Review)
const FounderReviewPage = lazy(() => import('@fops/pages/founder/FounderReviewPage'));

// =============================================================================
// ONBOARDING PAGES (website/onboarding/)
//
// Responsibility: Pre-console tenant setup flow
// - /onboarding/connect  - API connection setup
// - /onboarding/safety   - Safety policy configuration
// - /onboarding/alerts   - Alert channel configuration
// - /onboarding/verify   - Final verification step
// - /onboarding/complete - Completion acknowledgment
//
// Guard: OnboardingRoute (requires auth, NOT completed onboarding)
// On complete: Redirects to /guard (customer console)
// =============================================================================
const ConnectPage = lazy(() => import('@onboarding/pages/ConnectPage'));
const SafetyPage = lazy(() => import('@onboarding/pages/SafetyPage'));
const AlertsPage = lazy(() => import('@onboarding/pages/AlertsPage'));
const VerifyPage = lazy(() => import('@onboarding/pages/VerifyPage'));
const CompletePage = lazy(() => import('@onboarding/pages/CompletePage'));

// =============================================================================
// CONSOLE ENTRY POINTS (Standalone - handle their own auth)
// =============================================================================
// CUSTOMER: /guard/* → console.agenticverz.com (future)
const AIConsoleApp = lazy(() => import('@ai-console/app/AIConsoleApp'));
// FOUNDER: /ops/* → fops.agenticverz.com (future)
const OpsConsoleEntry = lazy(() => import('@fops/pages/ops/OpsConsoleEntry'));

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
         * FOUNDER CONSOLE (Target: fops.agenticverz.com)
         * Owner: FOUNDER | See: docs/M28_ROUTE_OWNERSHIP.md
         * All founder routes now under /fops/* namespace
         * ================================================================= */}

        {/* FOUNDER OPS CONSOLE - Standalone entry point */}
        <Route path="/fops/ops" element={<FounderRoute><OpsConsoleEntry /></FounderRoute>} />
        <Route path="/fops/ops/*" element={<FounderRoute><OpsConsoleEntry /></FounderRoute>} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* M28: Root redirects based on environment
           * - Preflight: /overview (L2.1 projection-driven UI)
           * - Production: /guard (Customer Console)
           */}
          <Route index element={
            <Navigate to={import.meta.env.VITE_PREFLIGHT_MODE === 'true' ? '/overview' : '/guard'} replace />
          } />

          {/* =========================================================
           * FOUNDER ROUTES (/fops/*)
           * PIN-318: All founder routes wrapped with FounderRoute
           * All routes under /fops/* namespace for boundary isolation
           * ========================================================= */}

          {/* Execution (FOUNDER) */}
          <Route path="fops/traces" element={<FounderRoute><TracesPage /></FounderRoute>} />
          <Route path="fops/traces/:runId" element={<FounderRoute><TraceDetailPage /></FounderRoute>} />
          <Route path="fops/workers" element={<FounderRoute><WorkerStudioHomePage /></FounderRoute>} />
          <Route path="fops/workers/console" element={<FounderRoute><WorkerExecutionConsolePage /></FounderRoute>} />

          {/* Reliability (FOUNDER) */}
          <Route path="fops/recovery" element={<FounderRoute><RecoveryPage /></FounderRoute>} />

          {/* M25 Integration Loop (FOUNDER) */}
          <Route path="fops/integration" element={<FounderRoute><IntegrationDashboard /></FounderRoute>} />
          <Route path="fops/integration/loop/:incidentId" element={<FounderRoute><LoopStatusPage /></FounderRoute>} />

          {/* Phase 5E-1: Founder Decision Timeline (FOUNDER) */}
          <Route path="fops/timeline" element={<FounderRoute><FounderTimelinePage /></FounderRoute>} />

          {/* Phase 5E-2: Kill-Switch Controls (FOUNDER-ONLY, not OPERATOR) */}
          <Route path="fops/controls" element={<FounderRoute allowedRoles={['FOUNDER']}><FounderControlsPage /></FounderRoute>} />

          {/* Phase H1: Replay UX Enablement (FOUNDER - READ-ONLY) */}
          <Route path="fops/replay" element={<FounderRoute><ReplayIndexPage /></FounderRoute>} />
          <Route path="fops/replay/:incidentId" element={<FounderRoute><ReplaySliceViewer /></FounderRoute>} />

          {/* Phase H2: Cost Simulation v1 (FOUNDER - Advisory Only) */}
          <Route path="fops/scenarios" element={<FounderRoute><ScenarioBuilderPage /></FounderRoute>} />

          {/* Phase H3: Founder Explorer (FOUNDER - READ-ONLY Cross-Tenant) */}
          <Route path="fops/explorer" element={<FounderRoute><FounderExplorerPage /></FounderRoute>} />

          {/* Unified Founder Review Dashboard (AUTO_EXECUTE + Contract Review) */}
          <Route path="fops/review" element={<FounderRoute><FounderReviewPage /></FounderRoute>} />

          {/* PIN-333: AUTO_EXECUTE Review Dashboard (FOUNDER - READ-ONLY Evidence) */}
          <Route path="fops/review/auto-execute" element={<FounderRoute><AutoExecuteReviewPage /></FounderRoute>} />

          {/* Governance (FOUNDER) */}
          <Route path="fops/sba" element={<FounderRoute><SBAInspectorPage /></FounderRoute>} />

          {/* =========================================================
           * CUSTOMER ROUTES (Target: console.agenticverz.com)
           * ========================================================= */}

          {/* =========================================================
           * L2.1 DOMAIN ROUTES (Preflight: preflight-console.agenticverz.com)
           * Projection-driven UI from ui_projection_lock.json
           * Reference: PIN-352
           * ========================================================= */}
          <Route path="overview" element={<OverviewPage />} />
          <Route path="overview/*" element={<OverviewPage />} />
          <Route path="activity" element={<ActivityPage />} />
          <Route path="activity/*" element={<ActivityPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="incidents/*" element={<IncidentsPage />} />
          <Route path="policies" element={<PoliciesPage />} />
          <Route path="policies/*" element={<PoliciesPage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="logs/*" element={<LogsPage />} />

          {/* Billing (CUSTOMER) */}
          <Route path="credits" element={<CreditsPage />} />

          {/* M28 DELETION (PIN-145): Routes permanently removed
           * See docs/M28_ROUTE_OWNERSHIP.md for DELETE list
           */}
        </Route>

        {/* Catch all - redirect based on environment */}
        <Route path="*" element={
          <Navigate to={import.meta.env.VITE_PREFLIGHT_MODE === 'true' ? '/overview' : '/guard'} replace />
        } />
      </Routes>
    </Suspense>
  );
}
