import { useNavigate } from 'react-router-dom';
import { Bell, User, LogOut, Settings } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/common/Button';
import { formatCredits } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { getCreditBalance } from '@/api/credits';

export function Header() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const { data: credits } = useQuery({
    queryKey: ['credits-balance'],
    queryFn: getCreditBalance,
    refetchInterval: 60000,
  });

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
