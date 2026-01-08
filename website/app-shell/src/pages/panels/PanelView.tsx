/**
 * Panel View Component (Generic Execution Surface)
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime (navigation)
 *   Execution: async (projection load)
 * Role: Render a single panel from L2.1 UI Projection Lock
 * Reference: L2.1 UI Projection Pipeline, PIN-352, PIN-355, PIN-356
 *
 * GOVERNANCE RULES (Phase 3 - Minimal Execution Surface):
 * - NO hardcoded panel names
 * - NO data fetching - metadata only
 * - All content derived from ui_projection_lock.json
 * - Uses contracts/ui_projection_loader.ts exclusively
 * - Panel route comes from projection, not synthesized
 *
 * VIEW MODE LAYER (PIN-356):
 * - Same renderer, two faces (INSPECTOR vs CUSTOMER)
 * - Metadata visibility controlled by RendererContext
 * - Zero divergence between inspector and customer views
 */

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Shield,
  FileText,
  Loader2,
  AlertCircle,
  ArrowLeft,
  List,
  Grid3x3,
  Table,
  Layers,
  CreditCard,
  Lock,
  CheckCircle,
  XCircle,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  loadProjection,
  getDomains,
} from '@/contracts/ui_projection_loader';
import type { Panel, Control, DomainName, RenderMode } from '@/contracts/ui_projection_types';
import { preflightLogger } from '@/lib/preflightLogger';
import { useRenderer, InspectorOnly } from '@/contexts/RendererContext';

// ============================================================================
// Constants
// ============================================================================

const DOMAIN_ICONS: Record<DomainName, React.ElementType> = {
  Overview: LayoutDashboard,
  Activity: Activity,
  Incidents: AlertTriangle,
  Policies: Shield,
  Logs: FileText,
};

const RENDER_MODE_ICONS: Record<RenderMode, React.ElementType> = {
  FLAT: List,
  TREE: Layers,
  GRID: Grid3x3,
  TABLE: Table,
  CARD: CreditCard,
  LIST: List,
};

const CONTROL_CATEGORY_COLORS: Record<string, string> = {
  data_control: 'bg-blue-900/30 text-blue-400 border-blue-700',
  selection: 'bg-purple-900/30 text-purple-400 border-purple-700',
  navigation: 'bg-cyan-900/30 text-cyan-400 border-cyan-700',
  action: 'bg-green-900/30 text-green-400 border-green-700',
  unknown: 'bg-gray-700 text-gray-400 border-gray-600',
};

// ============================================================================
// Helper: Find panel by route
// ============================================================================

function findPanelByRoute(route: string): Panel | undefined {
  const domains = getDomains();
  for (const domain of domains) {
    for (const panel of domain.panels) {
      if (panel.route === route) {
        return panel;
      }
    }
  }
  return undefined;
}

function findDomainByPanelRoute(route: string): DomainName | undefined {
  const domains = getDomains();
  for (const domain of domains) {
    for (const panel of domain.panels) {
      if (panel.route === route) {
        return domain.domain;
      }
    }
  }
  return undefined;
}

// ============================================================================
// Control Item Component
// ============================================================================

interface ControlItemProps {
  control: Control;
  showType: boolean;
}

function ControlItem({ control, showType }: ControlItemProps) {
  const colorClass = CONTROL_CATEGORY_COLORS[control.category] || CONTROL_CATEGORY_COLORS.unknown;

  return (
    <div className={cn(
      'flex items-center justify-between px-4 py-3 rounded-lg border transition-colors',
      colorClass
    )}>
      <div className="flex items-center gap-3">
        <span className="text-sm font-mono">{control.type}</span>
        {showType && (
          <span className="text-xs opacity-70">({control.category})</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        {showType && (
          <span className="text-xs opacity-70">Order: {control.order}</span>
        )}
        {control.enabled ? (
          <CheckCircle size={14} className="text-green-400" />
        ) : (
          <XCircle size={14} className="text-gray-500" />
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Permissions Display (Inspector Only)
// ============================================================================

interface PermissionsDisplayProps {
  permissions: Panel['permissions'];
}

function PermissionsDisplay({ permissions }: PermissionsDisplayProps) {
  const items = [
    { key: 'nav_required', label: 'Navigation Required', value: permissions.nav_required },
    { key: 'filtering', label: 'Filtering', value: permissions.filtering },
    { key: 'read', label: 'Read', value: permissions.read },
    { key: 'write', label: 'Write', value: permissions.write },
    { key: 'activate', label: 'Activate', value: permissions.activate },
  ];

  return (
    <div className="grid grid-cols-5 gap-2">
      {items.map((item) => (
        <div
          key={item.key}
          className={cn(
            'px-3 py-2 rounded text-center text-xs border',
            item.value
              ? 'bg-green-900/20 border-green-700/50 text-green-400'
              : 'bg-gray-800 border-gray-700 text-gray-500'
          )}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// Loading State
// ============================================================================

function PanelLoading() {
  return (
    <div className="flex items-center justify-center py-16">
      <Loader2 className="animate-spin text-gray-500 mr-3" size={24} />
      <span className="text-gray-400">Loading panel...</span>
    </div>
  );
}

// ============================================================================
// Error State
// ============================================================================

function PanelError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <AlertCircle className="text-red-500 mb-3" size={32} />
      <h3 className="text-lg font-medium text-red-400 mb-2">Failed to load</h3>
      <p className="text-sm text-gray-400 mb-4">{error}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-500"
      >
        Retry
      </button>
    </div>
  );
}

// ============================================================================
// Not Found State
// ============================================================================

function PanelNotFound({ route, domainRoute }: { route: string; domainRoute: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <AlertCircle className="text-amber-500 mb-3" size={32} />
      <h3 className="text-lg font-medium text-amber-400 mb-2">Panel Not Found</h3>
      <p className="text-sm text-gray-400 mb-4">
        No panel found at route "{route}" in the projection lock.
      </p>
      <Link
        to={domainRoute}
        className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 flex items-center gap-2"
      >
        <ArrowLeft size={16} />
        Back to Domain
      </Link>
    </div>
  );
}

// ============================================================================
// Main Panel View Component
// ============================================================================

export default function PanelView() {
  const { domain: domainSlug, panelSlug } = useParams<{ domain: string; panelSlug: string }>();
  const renderer = useRenderer();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [panel, setPanel] = useState<Panel | null>(null);
  const [domainName, setDomainName] = useState<DomainName | undefined>(undefined);

  // Construct the expected route from params
  const expectedRoute = `/precus/${domainSlug}/${panelSlug}`;
  const domainRoute = `/precus/${domainSlug}`;

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      await loadProjection();

      // Find panel by route
      const foundPanel = findPanelByRoute(expectedRoute);
      const foundDomain = findDomainByPanelRoute(expectedRoute);

      setPanel(foundPanel || null);
      setDomainName(foundDomain);

      if (foundPanel) {
        preflightLogger.panel.render(foundPanel.panel_id, foundPanel.panel_name);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projection');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [expectedRoute]);

  const DomainIcon = domainName ? DOMAIN_ICONS[domainName] : LayoutDashboard;
  const RenderIcon = panel ? RENDER_MODE_ICONS[panel.render_mode] : List;

  if (loading) {
    return <PanelLoading />;
  }

  if (error) {
    return <PanelError error={error} onRetry={loadData} />;
  }

  if (!panel) {
    return <PanelNotFound route={expectedRoute} domainRoute={domainRoute} />;
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Link to={domainRoute} className="hover:text-gray-200 flex items-center gap-1">
          <DomainIcon size={14} />
          <span>{domainName}</span>
        </Link>
        <span>/</span>
        <span className="text-gray-200">{panel.panel_name}</span>
      </div>

      {/* Panel Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className={cn(
            'p-3 rounded-lg',
            panel.enabled ? 'bg-primary-900/30' : 'bg-gray-800'
          )}>
            <RenderIcon size={28} className={panel.enabled ? 'text-primary-400' : 'text-gray-500'} />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-gray-100">{panel.panel_name}</h1>
            {/* Short Description - Customer mode: prominent, Inspector mode: with panel ID */}
            {panel.short_description && renderer.mode === 'CUSTOMER' && (
              <p className="text-sm text-gray-400 mt-1">{panel.short_description}</p>
            )}
            {/* Panel ID + Description - Inspector only */}
            {renderer.showInternalIDs && (
              <div className="flex items-center gap-3 mt-1">
                <p className="text-sm text-gray-500 font-mono">{panel.panel_id}</p>
                {panel.short_description && (
                  <p className="text-sm text-gray-500">— {panel.short_description}</p>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Enabled/Disabled Badge */}
          <span className={cn(
            'px-3 py-1.5 rounded text-sm font-medium',
            panel.enabled
              ? 'bg-green-900/30 text-green-400'
              : 'bg-red-900/30 text-red-400'
          )}>
            {panel.enabled ? 'Enabled' : 'Disabled'}
          </span>

          {/* Debug Banner - Inspector only */}
          {renderer.showDebugBanner && import.meta.env.VITE_PREFLIGHT_MODE === 'true' && (
            <span className="px-3 py-1.5 bg-amber-900/30 text-amber-400 text-sm font-mono rounded">
              PREFLIGHT
            </span>
          )}

          {/* Mode Badge - Inspector only */}
          {renderer.showDebugBanner && (
            <span className="px-2 py-1 bg-blue-900/30 text-blue-400 text-xs font-mono rounded border border-blue-700/50">
              {renderer.mode}
            </span>
          )}
        </div>
      </div>

      {/* Disabled Reason - Show in inspector, or customer-relevant messages in customer mode */}
      {!panel.enabled && panel.disabled_reason && (renderer.showDisabledReasons || renderer.mode === 'CUSTOMER') && (
        <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4 flex items-start gap-3">
          <Lock size={20} className="text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-red-400">
              {renderer.mode === 'CUSTOMER' ? 'Not Available' : 'Disabled Reason'}
            </h3>
            <p className="text-sm text-gray-300 mt-1">{panel.disabled_reason}</p>
          </div>
        </div>
      )}

      {/* Panel Metadata - Inspector Only */}
      <InspectorOnly>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-3">
            <h3 className="font-medium text-gray-200 flex items-center gap-2">
              <Info size={14} className="text-blue-400" />
              Panel Info
            </h3>
            <div className="space-y-2 text-sm">
              {renderer.showRenderMode && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Render Mode</span>
                  <span className="text-gray-200 font-mono">{panel.render_mode}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-400">Visibility</span>
                <span className="text-gray-200 font-mono">{panel.visibility}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">View Type</span>
                <span className="text-gray-200 font-mono">{panel.view_type}</span>
              </div>
              {renderer.showOrderInfo && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Order</span>
                  <span className="text-gray-200 font-mono">{panel.order}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-3">
            <h3 className="font-medium text-gray-200 flex items-center gap-2">
              <Layers size={14} className="text-purple-400" />
              Topic Info
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Subdomain</span>
                <span className="text-gray-200">{panel.subdomain || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Topic</span>
                <span className="text-gray-200">{panel.topic || '—'}</span>
              </div>
              {renderer.showInternalIDs && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Topic ID</span>
                  <span className="text-gray-200 font-mono text-xs">{panel.topic_id || '—'}</span>
                </div>
              )}
              {renderer.showRouteInfo && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Route</span>
                  <span className="text-gray-200 font-mono text-xs">{panel.route}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </InspectorOnly>

      {/* Permissions - Inspector Only */}
      {renderer.showPermissions && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-3">
          <h3 className="font-medium text-gray-200 flex items-center gap-2">
            <Shield size={14} className="text-green-400" />
            Permissions
          </h3>
          <PermissionsDisplay permissions={panel.permissions} />
        </div>
      )}

      {/* Controls */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-gray-200">
            Controls {renderer.showMetadata && `(${panel.control_count})`}
          </h3>
          {renderer.showMetadata && (
            <span className="text-xs text-gray-500">
              {panel.controls.filter(c => c.enabled).length} enabled
            </span>
          )}
        </div>

        {panel.controls.length === 0 ? (
          <p className="text-gray-500 text-sm py-4 text-center">No controls defined</p>
        ) : (
          <div className="space-y-2">
            {panel.controls.map((control, idx) => (
              <ControlItem
                key={`${control.type}-${idx}`}
                control={control}
                showType={renderer.showControlTypes}
              />
            ))}
          </div>
        )}
      </div>

      {/* Data Placeholder - Different messaging for each mode */}
      <div className="bg-gray-900/50 border border-dashed border-gray-700 rounded-lg p-8 text-center">
        {renderer.mode === 'INSPECTOR' ? (
          <>
            <p className="text-gray-500 text-sm">
              Data execution surface placeholder — no backend wired
            </p>
            <p className="text-gray-600 text-xs mt-2 font-mono">
              render_mode: {panel.render_mode} | controls: {panel.control_count}
            </p>
          </>
        ) : (
          <p className="text-gray-500 text-sm">
            Coming soon
          </p>
        )}
      </div>

      {/* Projection Source (Inspector only) */}
      {renderer.showMetadata && (
        <div className="text-xs text-gray-500 border-t border-gray-800 pt-4">
          <span className="font-mono">Source: ui_projection_lock.json</span>
          <span className="mx-2">|</span>
          <span className="font-mono">Route: {panel.route}</span>
          <span className="mx-2">|</span>
          <span className="font-mono">Mode: {renderer.mode}</span>
        </div>
      )}
    </div>
  );
}
