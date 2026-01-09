import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

/**
 * View Mode for L2.1 Projection Renderer
 * - DEVELOPER: Full metadata visibility (Inspector mode)
 * - CUSTOMER: Clean UX, no developer metadata
 *
 * Reference: PIN-356, PIN-359
 * Rule: Same route, same data, different render mode
 */
type ViewMode = 'DEVELOPER' | 'CUSTOMER';

interface UIState {
  sidebarCollapsed: boolean;
  theme: Theme;
  activeModal: string | null;
  activeDrawer: string | null;
  viewMode: ViewMode;

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: Theme) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
  openDrawer: (drawerId: string) => void;
  closeDrawer: () => void;
  setViewMode: (mode: ViewMode) => void;
  toggleViewMode: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      theme: 'light',
      activeModal: null,
      activeDrawer: null,
      viewMode: 'DEVELOPER',

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      setTheme: (theme) => {
        const resolvedTheme =
          theme === 'system'
            ? window.matchMedia('(prefers-color-scheme: dark)').matches
              ? 'dark'
              : 'light'
            : theme;
        document.documentElement.setAttribute('data-theme', resolvedTheme);
        set({ theme });
      },

      openModal: (modalId) => set({ activeModal: modalId }),
      closeModal: () => set({ activeModal: null }),

      openDrawer: (drawerId) => set({ activeDrawer: drawerId }),
      closeDrawer: () => set({ activeDrawer: null }),

      setViewMode: (mode) => set({ viewMode: mode }),
      toggleViewMode: () =>
        set((state) => ({
          viewMode: state.viewMode === 'DEVELOPER' ? 'CUSTOMER' : 'DEVELOPER',
        })),
    }),
    {
      name: 'aos-ui',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
        viewMode: state.viewMode,
      }),
    }
  )
);
