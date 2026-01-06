import { NavLink } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  GitBranch,
  AlertTriangle,
  RefreshCw,
  Target,
  Factory,
  Radar,
  Clock,
  Power,
  Link2,
  Wallet,
  Play,
  Calculator,
  Compass,
} from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  href: string;
  collapsed: boolean;
}

function NavItem({ icon: Icon, label, href, collapsed }: NavItemProps) {
  return (
    <NavLink
      to={href}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary-900/30 text-primary-400'
            : 'text-gray-300 hover:bg-gray-700'
        )
      }
    >
      <Icon size={20} className="flex-shrink-0" />
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
}

// =============================================================================
// NAVIGATION STRUCTURE
// M28: Founder routes (ops/*), Customer routes (guard/*)
// Phase 5E: Founder control surfaces (timeline, controls)
// =============================================================================

const MAIN_NAV = [
  { icon: Radar, label: 'Ops Console', href: '/ops' },
  { icon: Link2, label: 'Guard Console', href: '/guard' },
];

const FOUNDER_ITEMS = [
  { icon: Clock, label: 'Timeline', href: '/founder/timeline' },
  { icon: Power, label: 'Controls', href: '/founder/controls' },
  { icon: Play, label: 'Replay', href: '/founder/replay' },
  { icon: Calculator, label: 'Scenarios', href: '/founder/scenarios' },
  { icon: Compass, label: 'Explorer', href: '/founder/explorer' },
];

const EXECUTION_ITEMS = [
  { icon: Factory, label: 'Workers', href: '/workers' },
  { icon: GitBranch, label: 'Traces', href: '/traces' },
];

const RELIABILITY_ITEMS = [
  { icon: RefreshCw, label: 'Recovery', href: '/recovery' },
  { icon: AlertTriangle, label: 'Integration', href: '/integration' },
];

const GOVERNANCE_ITEMS = [
  { icon: Target, label: 'SBA Inspector', href: '/sba' },
];

const SYSTEM_ITEMS = [
  { icon: Wallet, label: 'Credits', href: '/credits' },
];

interface SidebarProps {
  collapsed: boolean;
}

export function Sidebar({ collapsed }: SidebarProps) {
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);

  return (
    <aside
      className={cn(
        'fixed left-0 top-16 h-[calc(100vh-4rem-2rem)] bg-gray-800 border-r border-gray-700 transition-all duration-200 z-10 flex flex-col',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      <nav className="flex-1 p-3 space-y-6 overflow-y-auto">
        {/* Main Consoles */}
        <div className="space-y-1">
          {MAIN_NAV.map((item) => (
            <NavItem key={item.href} {...item} collapsed={collapsed} />
          ))}
        </div>

        {/* Founder Section (Phase 5E) */}
        <div>
          {!collapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Founder
            </div>
          )}
          <div className="space-y-1">
            {FOUNDER_ITEMS.map((item) => (
              <NavItem key={item.href} {...item} collapsed={collapsed} />
            ))}
          </div>
        </div>

        {/* Execution Section */}
        <div>
          {!collapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Execution
            </div>
          )}
          <div className="space-y-1">
            {EXECUTION_ITEMS.map((item) => (
              <NavItem key={item.href} {...item} collapsed={collapsed} />
            ))}
          </div>
        </div>

        {/* Reliability Section */}
        <div>
          {!collapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Reliability
            </div>
          )}
          <div className="space-y-1">
            {RELIABILITY_ITEMS.map((item) => (
              <NavItem key={item.href} {...item} collapsed={collapsed} />
            ))}
          </div>
        </div>

        {/* Governance Section */}
        <div>
          {!collapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Governance
            </div>
          )}
          <div className="space-y-1">
            {GOVERNANCE_ITEMS.map((item) => (
              <NavItem key={item.href} {...item} collapsed={collapsed} />
            ))}
          </div>
        </div>

        {/* System Section */}
        <div>
          {!collapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              System
            </div>
          )}
          <div className="space-y-1">
            {SYSTEM_ITEMS.map((item) => (
              <NavItem key={item.href} {...item} collapsed={collapsed} />
            ))}
          </div>
        </div>
      </nav>

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
