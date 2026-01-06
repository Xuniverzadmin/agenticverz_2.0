import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface UIState {
  sidebarCollapsed: boolean;
  theme: Theme;
  activeModal: string | null;
  activeDrawer: string | null;

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: Theme) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
  openDrawer: (drawerId: string) => void;
  closeDrawer: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      theme: 'light',
      activeModal: null,
      activeDrawer: null,

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
    }),
    {
      name: 'aos-ui',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
      }),
    }
  )
);
