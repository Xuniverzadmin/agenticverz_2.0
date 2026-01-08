import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Bell, User, LogOut, Settings, ChevronDown, Monitor, Beaker, Users, Wrench } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/common/Button';
import { cn } from '@/lib/utils';
import { ProjectionBreadcrumb } from '@/navigation/ProjectionBreadcrumb';
import { ProjectSelector } from './ProjectSelector';
// PIN-323: Credits API quarantined - CAP-008 is SDK-only
// import { formatCredits } from '@/lib/utils';
// import { useQuery } from '@tanstack/react-query';
// import { getCreditBalance } from '@/api/credits';

// ============================================================================
// Console Definitions (Cross-Console Navigation)
// Reference: PIN-352, PIN-355
// ============================================================================

interface ConsoleDefinition {
  id: string;
  path: string;
  label: string;
  shortLabel: string;
  icon: React.ElementType;
  environment: 'preflight' | 'production';
  audience: 'customer' | 'founder';
  description: string;
}

const CONSOLES: ConsoleDefinition[] = [
  {
    id: 'precus',
    path: '/precus',
    label: 'Preflight Customer',
    shortLabel: 'PreCus',
    icon: Beaker,
    environment: 'preflight',
    audience: 'customer',
    description: 'L2.1 projection-driven UI preview',
  },
  {
    id: 'cus',
    path: '/cus',
    label: 'Customer Console',
    shortLabel: 'Customer',
    icon: Users,
    environment: 'production',
    audience: 'customer',
    description: 'Production customer console',
  },
  {
    id: 'prefops',
    path: '/prefops/ops',
    label: 'Preflight Founder',
    shortLabel: 'PreFops',
    icon: Beaker,
    environment: 'preflight',
    audience: 'founder',
    description: 'Founder ops preview',
  },
  {
    id: 'fops',
    path: '/fops/ops',
    label: 'Founder Console',
    shortLabel: 'Founder',
    icon: Wrench,
    environment: 'production',
    audience: 'founder',
    description: 'Production founder ops',
  },
];

function getActiveConsole(pathname: string): ConsoleDefinition | undefined {
  if (pathname.startsWith('/precus')) return CONSOLES.find(c => c.id === 'precus');
  if (pathname.startsWith('/cus')) return CONSOLES.find(c => c.id === 'cus');
  if (pathname.startsWith('/prefops')) return CONSOLES.find(c => c.id === 'prefops');
  if (pathname.startsWith('/fops')) return CONSOLES.find(c => c.id === 'fops');
  return undefined;
}

// ============================================================================
// Console Switcher Component
// ============================================================================

function ConsoleSwitcher() {
  const location = useLocation();
  const activeConsole = getActiveConsole(location.pathname);

  if (!activeConsole) return null;

  const ActiveIcon = activeConsole.icon;

  // Fix 1: Filter consoles by audience - no cross-pipeline entries
  // Customer pipeline only sees customer consoles, founder only sees founder
  const availableConsoles = CONSOLES.filter(
    (c) => c.audience === activeConsole.audience
  );

  // Fix 3: Console switch = hard reload (different pipeline/runtime context)
  const handleConsoleSwitch = (consolePath: string) => {
    if (consolePath !== location.pathname) {
      window.location.href = consolePath;
    }
  };

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors focus:outline-none',
          activeConsole.environment === 'preflight'
            ? 'bg-amber-900/30 text-amber-400 hover:bg-amber-900/50'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        )}>
          <ActiveIcon size={16} />
          <span className="text-sm font-medium">{activeConsole.shortLabel}</span>
          {activeConsole.environment === 'preflight' && (
            <span className="text-xs px-1.5 py-0.5 bg-amber-800/50 rounded font-mono">PRE</span>
          )}
          <ChevronDown size={14} className="ml-1" />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="min-w-[220px] bg-gray-800 rounded-lg shadow-lg border border-gray-700 py-2 z-50"
          sideOffset={8}
          align="start"
        >
          <div className="px-3 py-1.5 mb-1">
            <span className="text-xs text-gray-500 uppercase tracking-wider">
              {activeConsole.audience === 'customer' ? 'Customer Consoles' : 'Founder Consoles'}
            </span>
          </div>

          {availableConsoles.map((console) => {
            const Icon = console.icon;
            const isActive = console.id === activeConsole.id;

            return (
              <DropdownMenu.Item
                key={console.id}
                className={cn(
                  'flex items-start gap-3 px-3 py-2 text-sm outline-none cursor-pointer',
                  isActive
                    ? 'bg-primary-900/30 text-primary-300'
                    : 'text-gray-300 hover:bg-gray-700'
                )}
                onClick={() => handleConsoleSwitch(console.path)}
              >
                <Icon size={18} className={cn(
                  'mt-0.5 flex-shrink-0',
                  isActive ? 'text-primary-400' : 'text-gray-500'
                )} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{console.label}</span>
                    {console.environment === 'preflight' && (
                      <span className="text-xs px-1 py-0.5 bg-amber-900/50 text-amber-400 rounded font-mono">
                        PRE
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 line-clamp-1">{console.description}</span>
                </div>
                {isActive && (
                  <span className="w-2 h-2 mt-2 rounded-full bg-primary-400" />
                )}
              </DropdownMenu.Item>
            );
          })}

          <DropdownMenu.Separator className="h-px bg-gray-700 my-2" />

          <div className="px-3 py-1 text-xs text-gray-500">
            <span className="font-mono">Route: {location.pathname}</span>
          </div>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

export function Header() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  // PIN-323: Credits query disabled - capability quarantined
  // const { data: credits } = useQuery({
  //   queryKey: ['credits-balance'],
  //   queryFn: getCreditBalance,
  //   refetchInterval: 60000,
  // });
  const credits = null; // Placeholder until credits capability is resolved

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b border-gray-700 bg-gray-800 px-6 flex items-center justify-between z-20">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AOS</span>
          </div>
          <span className="font-semibold text-lg text-gray-100">
            Console
          </span>
        </div>

        {/* Console Switcher - Cross-Console Navigation */}
        <div className="h-6 w-px bg-gray-600 mx-2" />
        <ConsoleSwitcher />

        {/* Project Selector - Global scope (NOT L2.1) */}
        <div className="h-6 w-px bg-gray-600 mx-2" />
        <ProjectSelector />

        {/* Breadcrumb - Projection-derived navigation context */}
        <div className="h-6 w-px bg-gray-600 mx-2" />
        <ProjectionBreadcrumb />
      </div>

      <div className="flex items-center gap-4">
        {/* Credits Badge */}
        {credits && (
          <div className="px-3 py-1.5 bg-gray-700 rounded-lg">
            <span className="text-sm font-medium text-gray-300">
              {formatCredits(credits.balance)} credits
            </span>
          </div>
        )}

        {/* Notifications */}
        <Button variant="ghost" size="sm">
          <Bell size={18} />
        </Button>

        {/* User Menu */}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button className="flex items-center gap-2 focus:outline-none">
              <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-white">
                <User size={16} />
              </div>
              <span className="text-sm font-medium text-gray-300">
                {user?.name || 'User'}
              </span>
            </button>
          </DropdownMenu.Trigger>

          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="min-w-[180px] bg-gray-800 rounded-lg shadow-lg border border-gray-700 py-1 z-50"
              sideOffset={8}
              align="end"
            >
              <DropdownMenu.Item
                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 cursor-pointer outline-none"
                onClick={() => navigate('/settings')}
              >
                <Settings size={16} />
                Settings
              </DropdownMenu.Item>
              <DropdownMenu.Separator className="h-px bg-gray-700 my-1" />
              <DropdownMenu.Item
                className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-900/20 cursor-pointer outline-none"
                onClick={handleLogout}
              >
                <LogOut size={16} />
                Sign out
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </header>
  );
}
