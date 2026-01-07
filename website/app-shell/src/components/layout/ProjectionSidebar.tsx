/**
 * Projection-Driven Sidebar
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime (on mount)
 *   Execution: async (projection load)
 * Role: Render sidebar navigation from L2.1 UI Projection Lock
 * Reference: L2.1 UI Projection Pipeline, PIN-352
 *
 * GOVERNANCE RULES:
 * - NO hardcoded domain/panel names
 * - All navigation derived from ui_projection_lock.json
 * - Uses contracts/ui_projection_loader.ts exclusively
 */

import { useEffect, useState, useCallback } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Shield,
  FileText,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';
import {
  loadProjection,
  getDomains,
  getEnabledPanels,
} from '@/contracts/ui_projection_loader';
import type { Domain, Panel, DomainName } from '@/contracts/ui_projection_types';
import { preflightLogger } from '@/lib/preflightLogger';

// ============================================================================
// Domain Icon Mapping
// ============================================================================

const DOMAIN_ICONS: Record<DomainName, React.ElementType> = {
  Overview: LayoutDashboard,
  Activity: Activity,
  Incidents: AlertTriangle,
  Policies: Shield,
  Logs: FileText,
};

// Domain route prefixes
const DOMAIN_ROUTES: Record<DomainName, string> = {
  Overview: '/overview',
  Activity: '/activity',
  Incidents: '/incidents',
  Policies: '/policies',
  Logs: '/logs',
};

// ============================================================================
// Domain Section Component
// ============================================================================

interface DomainSectionProps {
  domain: Domain;
  collapsed: boolean;
  expanded: boolean;
  onToggle: () => void;
}

function DomainSection({ domain, collapsed, expanded, onToggle }: DomainSectionProps) {
  const Icon = DOMAIN_ICONS[domain.domain] || LayoutDashboard;
  const basePath = DOMAIN_ROUTES[domain.domain] || `/${domain.domain.toLowerCase()}`;
  const panels = getEnabledPanels(domain.domain);
  const location = useLocation();

  // Check if current route is within this domain
  const isActive = location.pathname.startsWith(basePath);

  const handleDomainClick = () => {
    preflightLogger.nav.domainClick(domain.domain);
  };

  if (collapsed) {
    // Collapsed mode: just show icon linking to domain root
    return (
      <NavLink
        to={basePath}
        onClick={handleDomainClick}
        className={cn(
          'flex items-center justify-center p-2 rounded-lg transition-colors',
          isActive
            ? 'bg-primary-900/30 text-primary-400'
            : 'text-gray-300 hover:bg-gray-700'
        )}
        title={domain.domain}
      >
        <Icon size={20} />
      </NavLink>
    );
  }

  // Expanded mode: show domain with collapsible panels
  return (
    <div className="space-y-1">
      {/* Domain Header */}
      <button
        onClick={onToggle}
        className={cn(
          'flex items-center justify-between w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary-900/20 text-primary-300'
            : 'text-gray-300 hover:bg-gray-700'
        )}
      >
        <div className="flex items-center gap-3">
          <Icon size={20} className="flex-shrink-0" />
          <span>{domain.domain}</span>
        </div>
        {panels.length > 0 && (
          <span className="text-gray-500">
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </span>
        )}
      </button>

      {/* Panel List (when expanded) */}
      {expanded && panels.length > 0 && (
        <div className="ml-8 space-y-0.5">
          {panels.map((panel) => (
            <PanelNavItem
              key={panel.panel_id}
              panel={panel}
              basePath={basePath}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Panel Nav Item Component
// ============================================================================

interface PanelNavItemProps {
  panel: Panel;
  basePath: string;
}

function PanelNavItem({ panel, basePath }: PanelNavItemProps) {
  // Create route from panel_id (e.g., "overview_system_health" -> "/overview/system-health")
  const panelSlug = panel.panel_id
    .replace(/^[a-z]+_/, '') // Remove domain prefix
    .replace(/_/g, '-'); // Underscores to dashes
  const panelPath = `${basePath}/${panelSlug}`;

  const handleClick = () => {
    preflightLogger.nav.panelClick(panel.panel_id, panel.panel_name);
  };

  return (
    <NavLink
      to={panelPath}
      onClick={handleClick}
      className={({ isActive }) =>
        cn(
          'block px-3 py-1.5 rounded text-sm transition-colors',
          isActive
            ? 'bg-primary-900/20 text-primary-400'
            : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
        )
      }
    >
      {panel.panel_name}
    </NavLink>
  );
}

// ============================================================================
// Loading State
// ============================================================================

function SidebarLoading({ collapsed }: { collapsed: boolean }) {
  return (
    <div className={cn(
      'flex items-center justify-center py-8',
      collapsed ? 'px-2' : 'px-4'
    )}>
      <Loader2 className="animate-spin text-gray-500" size={collapsed ? 20 : 24} />
      {!collapsed && (
        <span className="ml-2 text-sm text-gray-500">Loading...</span>
      )}
    </div>
  );
}

// ============================================================================
// Error State
// ============================================================================

function SidebarError({ collapsed, error, onRetry }: {
  collapsed: boolean;
  error: string;
  onRetry: () => void;
}) {
  return (
    <div className={cn(
      'flex flex-col items-center justify-center py-8 text-center',
      collapsed ? 'px-2' : 'px-4'
    )}>
      <AlertCircle className="text-red-500 mb-2" size={collapsed ? 20 : 24} />
      {!collapsed && (
        <>
          <span className="text-sm text-red-400 mb-2">Failed to load</span>
          <button
            onClick={onRetry}
            className="text-xs text-primary-400 hover:text-primary-300"
          >
            Retry
          </button>
        </>
      )}
    </div>
  );
}

// ============================================================================
// Main Sidebar Component
// ============================================================================

interface ProjectionSidebarProps {
  collapsed: boolean;
}

export function ProjectionSidebar({ collapsed }: ProjectionSidebarProps) {
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const location = useLocation();

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [expandedDomains, setExpandedDomains] = useState<Set<DomainName>>(new Set());

  // Load projection on mount
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await loadProjection();
      const loadedDomains = getDomains();
      setDomains(loadedDomains);
      preflightLogger.sidebar.render(loadedDomains.length);

      // Auto-expand domain based on current route
      const currentDomain = loadedDomains.find((d) =>
        location.pathname.startsWith(DOMAIN_ROUTES[d.domain])
      );
      if (currentDomain) {
        setExpandedDomains(new Set([currentDomain.domain]));
        preflightLogger.sidebar.expand(currentDomain.domain);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projection');
    } finally {
      setLoading(false);
    }
  }, [location.pathname]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Toggle domain expansion
  const toggleDomain = (domain: DomainName) => {
    setExpandedDomains((prev) => {
      const next = new Set(prev);
      if (next.has(domain)) {
        next.delete(domain);
        preflightLogger.sidebar.collapse(domain);
      } else {
        next.add(domain);
        preflightLogger.sidebar.expand(domain);
      }
      return next;
    });
  };

  return (
    <aside
      className={cn(
        'fixed left-0 top-16 h-[calc(100vh-4rem-2rem)] bg-gray-800 border-r border-gray-700 transition-all duration-200 z-10 flex flex-col',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Projection Source Indicator (dev only) */}
      {!collapsed && import.meta.env.VITE_PREFLIGHT_MODE === 'true' && (
        <div className="px-3 py-2 bg-amber-900/20 border-b border-amber-700/30">
          <span className="text-xs text-amber-400 font-mono">PREFLIGHT</span>
        </div>
      )}

      <nav className="flex-1 p-3 space-y-2 overflow-y-auto">
        {loading && <SidebarLoading collapsed={collapsed} />}

        {error && (
          <SidebarError
            collapsed={collapsed}
            error={error}
            onRetry={loadData}
          />
        )}

        {!loading && !error && domains.map((domain) => (
          <DomainSection
            key={domain.domain}
            domain={domain}
            collapsed={collapsed}
            expanded={expandedDomains.has(domain.domain)}
            onToggle={() => toggleDomain(domain.domain)}
          />
        ))}
      </nav>

      {/* Statistics Footer */}
      {!collapsed && !loading && !error && (
        <div className="px-3 py-2 border-t border-gray-700 text-xs text-gray-500">
          <span>{domains.length} domains • </span>
          <span>{domains.reduce((sum, d) => sum + d.panel_count, 0)} panels</span>
        </div>
      )}

      {/* Collapse Button */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-6 w-6 h-6 bg-gray-800 border border-gray-700 rounded-full flex items-center justify-center shadow-sm hover:bg-gray-700 transition-colors"
      >
        {collapsed ? (
          <ChevronRight size={14} className="text-gray-500" />
        ) : (
          <ChevronLeft size={14} className="text-gray-500" />
        )}
      </button>
    </aside>
  );
}
