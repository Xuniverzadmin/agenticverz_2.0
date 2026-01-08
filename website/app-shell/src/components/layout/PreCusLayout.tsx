/**
 * PreCusLayout — Preflight Customer Console Layout
 *
 * Layer: L1 — Product Experience (UI)
 * Product: customer-console (preflight)
 * Temporal:
 *   Trigger: render
 *   Execution: sync
 * Role: Layout shell for /precus/* routes with L2.1 projection sidebar
 * Reference: PIN-352, Routing Authority Model
 *
 * INVARIANTS:
 * - This layout is ONLY for /precus/* routes (preflight customer console)
 * - Always uses ProjectionSidebar (L2.1 projection-driven navigation)
 * - Never used for /cus/*, /prefops/*, or /fops/* routes
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

/**
 * PreCusLayout — Preflight Customer Console Layout
 *
 * Renders the L2.1 projection-driven UI for preflight customer console.
 * Uses ProjectionSidebar exclusively (no conditional - this IS the preflight layout).
 */
export function PreCusLayout() {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);

  return (
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
  );
}

export default PreCusLayout;
