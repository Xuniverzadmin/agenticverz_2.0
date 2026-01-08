/**
 * RendererContext - View Mode Layer for Projection Renderer
 *
 * Provides a single renderer with two faces:
 * - INSPECTOR: Full metadata visibility for developer triage (PreCus)
 * - CUSTOMER: Clean UX with suppressed internals (Customer Console)
 *
 * This enables:
 * - Same projection, same routing, same controls
 * - Different visibility rules for metadata and chrome
 * - Zero divergence between inspector and customer views
 * - Safe promotion semantics (inspector → customer)
 *
 * Reference: PIN-356
 */

import React, { createContext, useContext, ReactNode } from 'react';

// ============================================================================
// Types
// ============================================================================

export type RendererMode =
  | 'INSPECTOR'   // PreCus - full metadata for developer triage
  | 'CUSTOMER';   // Customer Console - clean UX, suppressed internals

export interface RendererContextValue {
  mode: RendererMode;

  // Visibility flags
  showMetadata: boolean;        // Panel info, topic info blocks
  showPermissions: boolean;     // Permissions matrix
  showControlTypes: boolean;    // Control type labels (data_control, selection)
  showInternalIDs: boolean;     // Topic IDs, internal identifiers
  showRenderMode: boolean;      // Render mode indicator
  showDisabledReasons: boolean; // Why controls are disabled (always show user-relevant)
  showDebugBanner: boolean;     // Development/debug banners
  showRouteInfo: boolean;       // Route path display
  showOrderInfo: boolean;       // Order (O1-O5) indicators
}

// ============================================================================
// Mode Presets
// ============================================================================

export const INSPECTOR_MODE: RendererContextValue = {
  mode: 'INSPECTOR',
  showMetadata: true,
  showPermissions: true,
  showControlTypes: true,
  showInternalIDs: true,
  showRenderMode: true,
  showDisabledReasons: true,
  showDebugBanner: true,
  showRouteInfo: true,
  showOrderInfo: true,
};

export const CUSTOMER_MODE: RendererContextValue = {
  mode: 'CUSTOMER',
  showMetadata: false,
  showPermissions: false,
  showControlTypes: false,
  showInternalIDs: false,
  showRenderMode: false,
  showDisabledReasons: false, // Only show user-relevant disabled reasons
  showDebugBanner: false,
  showRouteInfo: false,
  showOrderInfo: false,
};

// Future modes (not implemented yet):
// export const FOUNDER_INSPECTOR_MODE: RendererContextValue = { ... };
// export const SUPPORT_DEBUG_MODE: RendererContextValue = { ... };

// ============================================================================
// Context
// ============================================================================

const RendererContext = createContext<RendererContextValue | null>(null);

// ============================================================================
// Provider
// ============================================================================

interface RendererProviderProps {
  value: RendererContextValue;
  children: ReactNode;
}

export function RendererProvider({ value, children }: RendererProviderProps) {
  return (
    <RendererContext.Provider value={value}>
      {children}
    </RendererContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useRenderer(): RendererContextValue {
  const context = useContext(RendererContext);

  if (!context) {
    // Default to INSPECTOR mode if no provider (safe fallback for development)
    console.warn('[RendererContext] No provider found, defaulting to INSPECTOR mode');
    return INSPECTOR_MODE;
  }

  return context;
}

// ============================================================================
// Utility: Check if in Inspector Mode
// ============================================================================

export function useIsInspectorMode(): boolean {
  const { mode } = useRenderer();
  return mode === 'INSPECTOR';
}

// ============================================================================
// Conditional Render Helper
// ============================================================================

interface InspectorOnlyProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Renders children only in INSPECTOR mode.
 * Use for metadata blocks that should be hidden in customer view.
 */
export function InspectorOnly({ children, fallback = null }: InspectorOnlyProps) {
  const { mode } = useRenderer();
  return mode === 'INSPECTOR' ? <>{children}</> : <>{fallback}</>;
}

/**
 * Renders children only in CUSTOMER mode.
 * Use for customer-specific UX elements.
 */
export function CustomerOnly({ children, fallback = null }: InspectorOnlyProps) {
  const { mode } = useRenderer();
  return mode === 'CUSTOMER' ? <>{children}</> : <>{fallback}</>;
}
