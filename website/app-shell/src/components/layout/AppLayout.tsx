import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ProjectionSidebar } from './ProjectionSidebar';
import { StatusBar } from './StatusBar';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';

// Use projection sidebar in preflight mode
const useProjectionSidebar = import.meta.env.VITE_PREFLIGHT_MODE === 'true';

export function AppLayout() {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        {useProjectionSidebar ? (
          <ProjectionSidebar collapsed={sidebarCollapsed} />
        ) : (
          <Sidebar collapsed={sidebarCollapsed} />
        )}
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
