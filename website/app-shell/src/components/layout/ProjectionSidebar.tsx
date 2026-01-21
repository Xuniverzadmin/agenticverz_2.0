/**
 * Projection-Driven Sidebar (v2 Wireframe)
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime (on mount)
 *   Execution: async (projection load)
 * Role: Render sidebar navigation from L2.1 UI Projection Lock
 * Reference: L2.1 UI Projection Pipeline, PIN-352, PIN-355, CUSTOMER_CONSOLE_V2_CONSTITUTION.md
 *
 * DESIGN DECISIONS (per v2 Constitution):
 * - Sidebar shows: Domain → Subdomain (nested)
 * - Topics are NOT in sidebar (they appear as tabs in main workspace)
 * - Section headers: CORE LENSES, INTELLIGENCE (no redundant headers for single-domain sections)
 * - Account is pinned to sidebar footer
 * - Subdomains are collapsible per domain
 */

import { useEffect, useState, useCallback } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
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
// Section Configuration (v2 Constitution - Domain Tiers)
// No redundant section headers for single-domain groups
// ============================================================================

interface SectionConfig {
  title: string | null; // null means no header (domain shown directly with icon)
  domains: DomainName[];
}

const SIDEBAR_SECTIONS: SectionConfig[] = [
  {
    title: 'CORE LENSES',
    domains: ['Overview', 'Activity', 'Incidents', 'Policies', 'Logs'],
  },
  {
    title: 'INTELLIGENCE',
    domains: ['Analytics'],
  },
  {
    title: null, // No header - Connectivity shown directly with icon
    domains: ['Connectivity'],
  },
];

// Account is handled separately (pinned to footer)
const ACCOUNT_DOMAIN: DomainName = 'Account';

// ============================================================================
// Subdomain Nav Item (Shown when domain is expanded)
// ============================================================================

interface SubdomainNavItemProps {
  subdomain: string;
  domainRoute: string;
}

function SubdomainNavItem({
  subdomain,
  domainRoute,
}: SubdomainNavItemProps) {
  const location = useLocation();

  // Format subdomain name for display
  const subdomainLabel = subdomain.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  // Subdomain route: domain route + subdomain slug
  const subdomainRoute = `${domainRoute}?subdomain=${encodeURIComponent(subdomain)}`;

  // Check if this subdomain is active
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
// Domain Item Component (with collapsible nested subdomains)
// ============================================================================

interface DomainItemProps {
  domain: Domain;
  collapsed: boolean; // sidebar collapsed (icons only)
}

function DomainItem({ domain, collapsed }: DomainItemProps) {
  const Icon = DOMAIN_ICONS[domain.domain] || LayoutDashboard;
  const subdomains = getSubdomainsForDomain(domain.domain);
  const location = useLocation();

  // Track whether subdomains are expanded (collapsed by default)
  const [subdomainsExpanded, setSubdomainsExpanded] = useState(false);

  // Check if current route is within this domain
  const isActive = location.pathname.startsWith(domain.route);

  // Auto-expand subdomains when domain is active
  useEffect(() => {
    if (isActive && subdomains.length > 0) {
      setSubdomainsExpanded(true);
    }
  }, [isActive, subdomains.length]);

  const handleDomainClick = () => {
    preflightLogger.nav.domainClick(domain.domain);
  };

  const toggleSubdomains = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setSubdomainsExpanded(!subdomainsExpanded);
  };

  if (collapsed) {
    // Sidebar collapsed mode: icon only
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

  const hasSubdomains = subdomains.length > 0;

  // Sidebar expanded mode: domain header + collapsible subdomains
  return (
    <div className="space-y-1">
      {/* Domain Header */}
      <div className="flex items-center">
        <NavLink
          to={domain.route}
          onClick={handleDomainClick}
          className={cn(
            'flex-1 flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            isActive
              ? 'bg-primary-900/20 text-primary-300'
              : 'text-gray-300 hover:bg-gray-700'
          )}
        >
          <Icon size={20} className="flex-shrink-0" />
          <span>{domain.domain}</span>
        </NavLink>
        {/* Collapse toggle for subdomains */}
        {hasSubdomains && (
          <button
            onClick={toggleSubdomains}
            className="p-1.5 rounded hover:bg-gray-700 text-gray-400 hover:text-gray-300 transition-colors"
            title={subdomainsExpanded ? 'Collapse subdomains' : 'Expand subdomains'}
          >
            <ChevronDown
              size={16}
              className={cn(
                'transition-transform duration-200',
                !subdomainsExpanded && '-rotate-90'
              )}
            />
          </button>
        )}
      </div>

      {/* Subdomains (Collapsible) */}
      {hasSubdomains && subdomainsExpanded && (
        <div className="ml-6 space-y-0.5 border-l border-gray-700 pl-2">
          {subdomains.map((subdomain) => (
            <SubdomainNavItem
              key={subdomain}
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
// Section Header Component
// ============================================================================

interface SectionHeaderProps {
  title: string | null;
  collapsed: boolean;
}

function SectionHeader({ title, collapsed }: SectionHeaderProps) {
  if (collapsed || !title) return null;

  return (
    <div className="px-3 pt-4 pb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
      {title}
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

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [domains, setDomains] = useState<Domain[]>([]);

  // Load projection on mount
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await loadProjection();
      const loadedDomains = getDomains();
      setDomains(loadedDomains);
      preflightLogger.sidebar.render(loadedDomains.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projection');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Helper to get domain by name
  const getDomainByName = (name: DomainName): Domain | undefined => {
    return domains.find(d => d.domain === name);
  };

  // Get Account domain for footer
  const accountDomain = getDomainByName(ACCOUNT_DOMAIN);

  return (
    <aside
      className={cn(
        'fixed left-0 top-16 h-[calc(100vh-4rem-2rem)] bg-gray-800 border-r border-gray-700 transition-all duration-200 z-10 flex flex-col',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Preflight Mode Indicator */}
      {!collapsed && import.meta.env.VITE_PREFLIGHT_MODE === 'true' && (
        <div className="px-3 py-2 bg-amber-900/20 border-b border-amber-700/30">
          <span className="text-xs text-amber-400 font-mono">PREFLIGHT</span>
        </div>
      )}

      {/* Main Navigation (Scrollable) */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {loading && <SidebarLoading collapsed={collapsed} />}

        {error && (
          <SidebarError
            collapsed={collapsed}
            error={error}
            onRetry={loadData}
          />
        )}

        {!loading && !error && (
          <>
            {/* Render sections with domain groups */}
            {SIDEBAR_SECTIONS.map((section, index) => {
              const sectionDomains = section.domains
                .map(name => getDomainByName(name))
                .filter((d): d is Domain => d !== undefined);

              if (sectionDomains.length === 0) return null;

              // Use title or first domain as key (handles null titles)
              const sectionKey = section.title || section.domains[0] || `section-${index}`;

              return (
                <div key={sectionKey}>
                  <SectionHeader title={section.title} collapsed={collapsed} />
                  <div className="space-y-1">
                    {sectionDomains.map((domain) => (
                      <DomainItem
                        key={domain.domain}
                        domain={domain}
                        collapsed={collapsed}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </>
        )}
      </nav>

      {/* Account Section (Pinned to Footer - per v2 Constitution) */}
      {!loading && !error && accountDomain && (
        <div className="border-t border-gray-700 p-3">
          {!collapsed && (
            <div className="px-3 pb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              ACCOUNT
            </div>
          )}
          <DomainItem domain={accountDomain} collapsed={collapsed} />
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
