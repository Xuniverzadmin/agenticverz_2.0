/**
 * AOS App Shell Routes
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Route tree definition for all 4 console surfaces
 * Reference: PIN-352, Routing Authority Model
 *
 * INFRASTRUCTURE: FROZEN
 * Owner: platform
 * Churn: low (new pages only, deliberate changes)
 * Last Frozen: 2026-01-08
 *
 * ROUTE ARCHITECTURE (COMPLETELY SEPARATED - NO MIXING):
 * ┌──────────────┬─────────────┬───────────┬─────────────────────────────┐
 * │ Console Kind │ Environment │ Root Path │ Layout/Entry                │
 * ├──────────────┼─────────────┼───────────┼─────────────────────────────┤
 * │ customer     │ preflight   │ /precus   │ PreCusLayout (L2.1 UI)      │
 * ├──────────────┼─────────────┼───────────┼─────────────────────────────┤
 * │ customer     │ production  │ /cus      │ AIConsoleApp                │
 * ├──────────────┼─────────────┼───────────┼─────────────────────────────┤
 * │ founder      │ preflight   │ /prefops  │ FounderRoute (standalone)   │
 * ├──────────────┼─────────────┼───────────┼─────────────────────────────┤
 * │ founder      │ production  │ /fops     │ FounderRoute (standalone)   │
 * └──────────────┴─────────────┴───────────┴─────────────────────────────┘
 *
 * INVARIANTS:
 * - 4 distinct console namespaces, NO mixing or leaking
 * - Each console has its own route group
 * - FounderRoute guard on ALL /prefops/* and /fops/* routes
 * - PreCusLayout for /precus/* (L2.1 projection-driven UI)
 * - AIConsoleApp for /cus/* (production customer)
 *
 * See: src/routing/ROUTING_AUTHORITY_LOCK.md
 */

import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { OnboardingRoute } from './OnboardingRoute';
import { FounderRoute } from './FounderRoute';
import { Spinner } from '@/components/common';
import { getCatchAllRoute } from '@/routing';

// =============================================================================
// SHARED PAGES
// =============================================================================
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const CreditsPage = lazy(() => import('@/pages/credits/CreditsPage'));

// =============================================================================
// PRECUS: PREFLIGHT CUSTOMER CONSOLE (/precus/*)
// L2.1 projection-driven pages
// =============================================================================
const PreCusLayout = lazy(() => import('@/components/layout/PreCusLayout'));
const OverviewPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.OverviewPage })));
const ActivityPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.ActivityPage })));
const IncidentsPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.IncidentsPage })));
const PoliciesPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.PoliciesPage })));
const LogsPage = lazy(() => import('@/pages/domains/DomainPage').then(m => ({ default: m.LogsPage })));

// =============================================================================
// CUS: PRODUCTION CUSTOMER CONSOLE (/cus/*)
// =============================================================================
const AIConsoleApp = lazy(() => import('@ai-console/app/AIConsoleApp'));

// =============================================================================
// PREFOPS & FOPS: FOUNDER CONSOLES (/prefops/* and /fops/*)
// Same pages, different namespaces
// =============================================================================
const OpsConsoleEntry = lazy(() => import('@fops/pages/ops/OpsConsoleEntry'));
const TracesPage = lazy(() => import('@fops/pages/traces/TracesPage'));
const TraceDetailPage = lazy(() => import('@fops/pages/traces/TraceDetailPage'));
const RecoveryPage = lazy(() => import('@fops/pages/recovery/RecoveryPage'));
const SBAInspectorPage = lazy(() => import('@fops/pages/sba/SBAInspectorPage'));
const WorkerStudioHomePage = lazy(() => import('@fops/pages/workers/WorkerStudioHome'));
const WorkerExecutionConsolePage = lazy(() => import('@fops/pages/workers/WorkerExecutionConsole'));
const IntegrationDashboard = lazy(() => import('@fops/pages/integration/IntegrationDashboard'));
const LoopStatusPage = lazy(() => import('@fops/pages/integration/LoopStatusPage'));
const FounderTimelinePage = lazy(() => import('@fops/pages/founder/FounderTimelinePage'));
const FounderControlsPage = lazy(() => import('@fops/pages/founder/FounderControlsPage'));
const ReplayIndexPage = lazy(() => import('@fops/pages/founder/ReplayIndexPage'));
const ReplaySliceViewer = lazy(() => import('@fops/pages/founder/ReplaySliceViewer'));
const ScenarioBuilderPage = lazy(() => import('@fops/pages/founder/ScenarioBuilderPage'));
const FounderExplorerPage = lazy(() => import('@fops/pages/founder/FounderExplorerPage'));
const AutoExecuteReviewPage = lazy(() => import('@fops/pages/founder/AutoExecuteReviewPage'));
const FounderReviewPage = lazy(() => import('@fops/pages/founder/FounderReviewPage'));

// =============================================================================
// ONBOARDING PAGES
// =============================================================================
const ConnectPage = lazy(() => import('@onboarding/pages/ConnectPage'));
const SafetyPage = lazy(() => import('@onboarding/pages/SafetyPage'));
const AlertsPage = lazy(() => import('@onboarding/pages/AlertsPage'));
const VerifyPage = lazy(() => import('@onboarding/pages/VerifyPage'));
const CompletePage = lazy(() => import('@onboarding/pages/CompletePage'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <Spinner size="lg" />
    </div>
  );
}

/**
 * Helper to render founder routes for a given prefix
 * Used for both /prefops/* and /fops/*
 */
function renderFounderRoutes(prefix: string) {
  return (
    <>
      <Route path={`${prefix}/ops`} element={<FounderRoute><OpsConsoleEntry /></FounderRoute>} />
      <Route path={`${prefix}/ops/*`} element={<FounderRoute><OpsConsoleEntry /></FounderRoute>} />
      <Route path={`${prefix}/traces`} element={<FounderRoute><TracesPage /></FounderRoute>} />
      <Route path={`${prefix}/traces/:runId`} element={<FounderRoute><TraceDetailPage /></FounderRoute>} />
      <Route path={`${prefix}/workers`} element={<FounderRoute><WorkerStudioHomePage /></FounderRoute>} />
      <Route path={`${prefix}/workers/console`} element={<FounderRoute><WorkerExecutionConsolePage /></FounderRoute>} />
      <Route path={`${prefix}/recovery`} element={<FounderRoute><RecoveryPage /></FounderRoute>} />
      <Route path={`${prefix}/integration`} element={<FounderRoute><IntegrationDashboard /></FounderRoute>} />
      <Route path={`${prefix}/integration/loop/:incidentId`} element={<FounderRoute><LoopStatusPage /></FounderRoute>} />
      <Route path={`${prefix}/timeline`} element={<FounderRoute><FounderTimelinePage /></FounderRoute>} />
      <Route path={`${prefix}/controls`} element={<FounderRoute allowedRoles={['FOUNDER']}><FounderControlsPage /></FounderRoute>} />
      <Route path={`${prefix}/replay`} element={<FounderRoute><ReplayIndexPage /></FounderRoute>} />
      <Route path={`${prefix}/replay/:incidentId`} element={<FounderRoute><ReplaySliceViewer /></FounderRoute>} />
      <Route path={`${prefix}/scenarios`} element={<FounderRoute><ScenarioBuilderPage /></FounderRoute>} />
      <Route path={`${prefix}/explorer`} element={<FounderRoute><FounderExplorerPage /></FounderRoute>} />
      <Route path={`${prefix}/review`} element={<FounderRoute><FounderReviewPage /></FounderRoute>} />
      <Route path={`${prefix}/review/auto-execute`} element={<FounderRoute><AutoExecuteReviewPage /></FounderRoute>} />
      <Route path={`${prefix}/sba`} element={<FounderRoute><SBAInspectorPage /></FounderRoute>} />
    </>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* ===============================================================
         * PUBLIC ROUTES
         * =============================================================== */}
        <Route path="/login" element={<LoginPage />} />

        {/* ===============================================================
         * ONBOARDING ROUTES
         * Requires auth but NOT onboarding complete
         * =============================================================== */}
        <Route path="/onboarding/connect" element={<OnboardingRoute><ConnectPage /></OnboardingRoute>} />
        <Route path="/onboarding/safety" element={<OnboardingRoute><SafetyPage /></OnboardingRoute>} />
        <Route path="/onboarding/alerts" element={<OnboardingRoute><AlertsPage /></OnboardingRoute>} />
        <Route path="/onboarding/verify" element={<OnboardingRoute><VerifyPage /></OnboardingRoute>} />
        <Route path="/onboarding/complete" element={<OnboardingRoute><CompletePage /></OnboardingRoute>} />

        {/* ===============================================================
         * CONSOLE 1: PRECUS - PREFLIGHT CUSTOMER (/precus/*)
         * L2.1 projection-driven UI
         * Layout: PreCusLayout
         * =============================================================== */}
        <Route
          path="/precus"
          element={
            <ProtectedRoute>
              <PreCusLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/precus/overview" replace />} />
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
          <Route path="credits" element={<CreditsPage />} />
          <Route path="*" element={<Navigate to="/precus/overview" replace />} />
        </Route>

        {/* ===============================================================
         * CONSOLE 2: CUS - PRODUCTION CUSTOMER (/cus/*)
         * AIConsoleApp handles all routing internally
         * =============================================================== */}
        <Route path="/cus" element={<AIConsoleApp />} />
        <Route path="/cus/*" element={<AIConsoleApp />} />

        {/* ===============================================================
         * CONSOLE 3: PREFOPS - PREFLIGHT FOUNDER (/prefops/*)
         * Same pages as FOPS, different namespace
         * All routes wrapped with FounderRoute guard
         * =============================================================== */}
        {renderFounderRoutes('/prefops')}

        {/* ===============================================================
         * CONSOLE 4: FOPS - PRODUCTION FOUNDER (/fops/*)
         * Production founder console
         * All routes wrapped with FounderRoute guard
         * =============================================================== */}
        {renderFounderRoutes('/fops')}

        {/* ===============================================================
         * ROOT & CATCH-ALL
         * Environment-aware redirect via routing authority
         * =============================================================== */}
        <Route index element={<Navigate to={getCatchAllRoute()} replace />} />
        <Route path="*" element={<Navigate to={getCatchAllRoute()} replace />} />
      </Routes>
    </Suspense>
  );
}
