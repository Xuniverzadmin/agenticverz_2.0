/**
 * PreCusLayout — Preflight Customer Console Layout
 *
 * Layer: L1 — Product Experience (UI)
 * Product: customer-console (preflight)
 * Temporal:
 *   Trigger: render
 *   Execution: sync
 * Role: Layout shell for /precus/* routes with L2.1 projection sidebar
 * Reference: PIN-352, PIN-356, PIN-359, Routing Authority Model
 *
 * VIEW MODE TOGGLE (PIN-359):
 * - DEVELOPER mode: Full metadata visibility for developer triage
 * - CUSTOMER mode: Clean UX, no developer metadata
 * - Same route, same data, different render mode
 * - Toggle in Header, NOT a route change
 *
 * INVARIANTS:
 * - This layout is ONLY for /precus/* routes (preflight customer console)
 * - Always uses ProjectionSidebar (L2.1 projection-driven navigation)
 * - Never used for /cus/*, /prefops/*, or /fops/* routes
 * - View mode toggle keeps URL at /precus/...
 *
 * ROUTE AUTHORITY:
 * ┌──────────────┬─────────────┬───────────┬─────────────────────────────┐
 * │ Console Kind │ Environment │ Root Path │ Layout/Entry                │
 * ├──────────────┼─────────────┼───────────┼─────────────────────────────┤
 * │ customer     │ preflight   │ /precus   │ PreCusLayout (this file)    │
 * │ customer     │ production  │ /cus      │ AIConsoleApp                │
 * └──────────────┴─────────────┴───────────┴─────────────────────────────┘
 */

import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { ProjectionSidebar } from './ProjectionSidebar';
import { StatusBar } from './StatusBar';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';
import { RendererProvider, INSPECTOR_MODE, CUSTOMER_MODE } from '@/contexts/RendererContext';
import { ProjectProvider } from '@/contexts/ProjectContext';
import { ConsoleIsolationGuard } from '@/routing';

/**
 * PreCusLayout — Preflight Customer Console Layout
 *
 * Renders the L2.1 projection-driven UI for preflight customer console.
 * Uses ProjectionSidebar exclusively (no conditional - this IS the preflight layout).
 *
 * PIN-359: View mode toggle
 * - DEVELOPER = INSPECTOR_MODE (full metadata)
 * - CUSTOMER = CUSTOMER_MODE (clean UX)
 * - Same route (/precus/*), different render mode
 */
export function PreCusLayout() {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);
  const viewMode = useUIStore((state) => state.viewMode);

  // PIN-359: Map viewMode to renderer mode
  // DEVELOPER → INSPECTOR_MODE (full metadata)
  // CUSTOMER → CUSTOMER_MODE (clean UX)
  const rendererMode = viewMode === 'DEVELOPER' ? INSPECTOR_MODE : CUSTOMER_MODE;

  return (
    <ConsoleIsolationGuard>
      <ProjectProvider>
        <RendererProvider value={rendererMode}>
          <div className="flex flex-col h-screen bg-gray-900">
            <Header />
            <div className="flex flex-1 overflow-hidden">
              {/* L2.1 Projection Sidebar - always used in PreCusLayout */}
              <ProjectionSidebar collapsed={sidebarCollapsed} />
              <main
                className={cn(
                  'flex-1 overflow-auto p-6 transition-all duration-200',
                  sidebarCollapsed ? 'ml-16' : 'ml-60'
                )}
              >
                <Outlet />
              </main>
            </div>
            <StatusBar />
          </div>
        </RendererProvider>
      </ProjectProvider>
    </ConsoleIsolationGuard>
  );
}

export default PreCusLayout;
