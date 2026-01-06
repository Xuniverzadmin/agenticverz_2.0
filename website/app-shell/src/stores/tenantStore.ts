import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Tenant {
  id: string;
  name: string;
  plan: string;
}

interface TenantState {
  tenants: Tenant[];
  currentTenantId: string | null;

  setTenants: (tenants: Tenant[]) => void;
  setCurrentTenant: (tenantId: string) => void;
  getCurrentTenant: () => Tenant | null;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set, get) => ({
      tenants: [],
      currentTenantId: null,

      setTenants: (tenants) =>
        set({
          tenants,
          currentTenantId: tenants[0]?.id ?? null,
        }),

      setCurrentTenant: (tenantId) => set({ currentTenantId: tenantId }),

      getCurrentTenant: () => {
        const { tenants, currentTenantId } = get();
        return tenants.find((t) => t.id === currentTenantId) ?? null;
      },
    }),
    {
      name: 'aos-tenant',
      partialize: (state) => ({ currentTenantId: state.currentTenantId }),
    }
  )
);
