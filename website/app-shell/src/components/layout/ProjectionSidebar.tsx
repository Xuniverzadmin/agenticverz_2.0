/**
 * Projection-Driven Sidebar
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime (on mount)
 *   Execution: async (projection load)
 * Role: Render sidebar navigation from L2.1 UI Projection Lock
 * Reference: L2.1 UI Projection Pipeline, PIN-352, PIN-355
 *
 * GOVERNANCE RULES (LOCKED):
 * - Sidebar renders STRUCTURE, not content
 * - Sidebar shows ONLY: Domain → Subdomain
 * - NO topics in sidebar
 * - NO panels in sidebar
 * - Topics and Panels belong in main workspace only
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
  BarChart2,
  Loader2,
  AlertCircle,
  User,
  Plug,
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';
import {
  loadProjection,
  getDomains,
  getSubdomainsForDomain,
} from '@/contracts/ui_projection_loader';
import type { Domain, DomainName } from '@/contracts/ui_projection_types';
import { preflightLogger } from '@/lib/preflightLogger';

// ============================================================================
// Domain Icon Mapping (visual only, not routing)
// ============================================================================

const DOMAIN_ICONS: Record<DomainName, React.ElementType> = {
  Overview: LayoutDashboard,
  Activity: Activity,
  Incidents: AlertTriangle,
  Policies: Shield,
  Logs: FileText,
  Analytics: BarChart2,
  Account: User,
  Connectivity: Plug,
};

// ============================================================================
// Subdomain Nav Item (Structure Only - No Panels)
// LOCKED: Sidebar stops at Domain → Subdomain. No deeper.
// ============================================================================

interface SubdomainNavItemProps {
  domainName: DomainName;
  subdomain: string;
  domainRoute: string;
}

function SubdomainNavItem({
  domainName,
  subdomain,
  domainRoute,
}: SubdomainNavItemProps) {
  const location = useLocation();

  // Format subdomain name for display
  const subdomainLabel = subdomain.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  // Subdomain route: domain route + subdomain slug
  const subdomainRoute = `${domainRoute}?subdomain=${encodeURIComponent(subdomain)}`;

  // Check if this subdomain is active (domain route matches and subdomain param matches)
  const searchParams = new URLSearchParams(location.search);
  const activeSubdomain = searchParams.get('subdomain');
  const isActive = location.pathname.startsWith(domainRoute) && activeSubdomain === subdomain;

  return (
    <NavLink
      to={subdomainRoute}
      className={cn(
        'block px-2 py-1.5 rounded text-sm transition-colors',
        isActive
          ? 'bg-gray-700/50 text-gray-200'
          : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700/30'
      )}
    >
      <span className="truncate">{subdomainLabel}</span>
    </NavLink>
  );
}

// ============================================================================
// Domain Section Component (Structure Only)
// LOCKED: Shows Domain → Subdomain. No topics. No panels.
// ============================================================================

interface DomainSectionProps {
  domain: Domain;
  collapsed: boolean;
  expanded: boolean;
  onToggle: () => void;
}

function DomainSection({
  domain,
  collapsed,
  expanded,
  onToggle,
}: DomainSectionProps) {
  const Icon = DOMAIN_ICONS[domain.domain] || LayoutDashboard;
  const subdomains = getSubdomainsForDomain(domain.domain);
  const location = useLocation();

  // Check if current route is within this domain (using projection route)
  const isActive = location.pathname.startsWith(domain.route);

  const handleDomainClick = () => {
    preflightLogger.nav.domainClick(domain.domain);
  };

  if (collapsed) {
    // Collapsed mode: icon linking to domain route (from projection)
    return (
      <NavLink
        to={domain.route}
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

  // Expanded mode: domain header + subdomain list (NO panels)
  return (
    <div className="space-y-1">
      {/* Domain Header - NavLink to domain route */}
      <div className="flex items-center">
        <NavLink
          to={domain.route}
          onClick={handleDomainClick}
          className={cn(
            'flex-1 flex items-center gap-3 px-3 py-2 rounded-l-lg text-sm font-medium transition-colors',
            isActive
              ? 'bg-primary-900/20 text-primary-300'
              : 'text-gray-300 hover:bg-gray-700'
          )}
        >
          <Icon size={20} className="flex-shrink-0" />
          <span>{domain.domain}</span>
        </NavLink>

        {/* Expand/Collapse button for subdomains */}
        {subdomains.length > 0 && (
          <button
            onClick={onToggle}
            className={cn(
              'px-2 py-2 rounded-r-lg transition-colors',
              isActive
                ? 'bg-primary-900/20 text-primary-300 hover:bg-primary-900/30'
                : 'text-gray-500 hover:bg-gray-700 hover:text-gray-300'
            )}
            title={expanded ? 'Collapse subdomains' : 'Expand subdomains'}
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        )}
      </div>

      {/* Subdomain List (Structure Only - No Panels) */}
      {expanded && subdomains.length > 0 && (
        <div className="ml-6 space-y-0.5 border-l border-gray-700 pl-2">
          {subdomains.map((subdomain) => (
            <SubdomainNavItem
              key={subdomain}
              domainName={domain.domain}
              subdomain={subdomain}
              domainRoute={domain.route}
            />
          ))}
        </div>
      )}
    </div>
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

  // State (Structure Only - No panel/topic state needed)
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

      // Auto-expand domain based on current route (using projection routes)
      const currentDomain = loadedDomains.find((d) =>
        location.pathname.startsWith(d.route)
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

  // Toggle domain expansion (shows/hides subdomains)
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

      {/* Statistics Footer (Structure Only) */}
      {!collapsed && !loading && !error && (
        <div className="px-3 py-2 border-t border-gray-700 text-xs text-gray-500">
          <span>{domains.length} domains</span>
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
