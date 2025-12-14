import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  PlayCircle,
  Database,
  Wallet,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Zap,
  GitBranch,
  AlertTriangle,
  RefreshCw,
  Target,
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
            ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400'
            : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
        )
      }
    >
      <Icon size={20} className="flex-shrink-0" />
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
}

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
  { icon: Cpu, label: 'Skills', href: '/skills' },
];

const EXECUTION_ITEMS = [
  { icon: Zap, label: 'Simulation', href: '/simulation' },
  { icon: GitBranch, label: 'Traces', href: '/traces' },
  { icon: PlayCircle, label: 'Replay', href: '/replay' },
];

const RELIABILITY_ITEMS = [
  { icon: AlertTriangle, label: 'Failures', href: '/failures' },
  { icon: RefreshCw, label: 'Recovery', href: '/recovery' },
];

const GOVERNANCE_ITEMS = [
  { icon: Target, label: 'SBA Inspector', href: '/sba' },
];

const DATA_ITEMS = [
  { icon: Database, label: 'Memory Pins', href: '/memory' },
];

const SYSTEM_ITEMS = [
  { icon: Wallet, label: 'Credits', href: '/credits' },
  { icon: BarChart3, label: 'Metrics', href: '/metrics' },
];

interface SidebarProps {
  collapsed: boolean;
}

export function Sidebar({ collapsed }: SidebarProps) {
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);

  return (
    <aside
      className={cn(
        'fixed left-0 top-16 h-[calc(100vh-4rem-2rem)] bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-200 z-10 flex flex-col',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      <nav className="flex-1 p-3 space-y-6 overflow-y-auto">
        {/* Main Navigation */}
        <div className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavItem key={item.href} {...item} collapsed={collapsed} />
          ))}
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

        {/* Data Section */}
        <div>
          {!collapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Data
            </div>
          )}
          <div className="space-y-1">
            {DATA_ITEMS.map((item) => (
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
        className="absolute -right-3 top-6 w-6 h-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full flex items-center justify-center shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
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
