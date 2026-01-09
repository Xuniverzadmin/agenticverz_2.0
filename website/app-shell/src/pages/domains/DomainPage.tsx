/**
 * Domain Page Component
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime (navigation)
 *   Execution: async (projection load)
 * Role: Render a domain with subdomains and topics from L2.1 UI Projection Lock
 * Reference: L2.1 UI Projection Pipeline, PIN-352
 *
 * GOVERNANCE RULES (LOCKED):
 * - Header hierarchy: Domain → Subdomain → Short Description → Topic Tabs
 * - Topic tabs are horizontal, in main workspace
 * - Panels render ONLY under selected topic
 * - NO internal IDs in customer-facing header
 * - NO kebab menus
 */

import { useEffect, useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Shield,
  FileText,
  Loader2,
  AlertCircle,
  List,
  Grid3x3,
  Table,
  Layers,
  CreditCard,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  loadProjection,
  getDomain,
  getPanels,
  getSubdomainsForDomain,
  getPanelsForSubdomain,
  getNormalizedDomain,
  getNormalizedPanelsForSubdomain,
  type NormalizedPanel,
  type NormalizedDomain,
} from '@/contracts/ui_projection_loader';
import type { Domain, Panel, DomainName, RenderMode } from '@/contracts/ui_projection_types';
import { preflightLogger } from '@/lib/preflightLogger';
import { useRenderer, InspectorOnly } from '@/contexts/RendererContext';
import { SimulatedControl } from '@/components/simulation/SimulatedControl';
import { useSimulation } from '@/contexts/SimulationContext';
import { Beaker } from 'lucide-react';
import { PanelContent, hasPanelContent } from '@/components/panels/PanelContentRegistry';

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

// ============================================================================
// Helper: Get unique topics for a subdomain
// ============================================================================

function getTopicsForSubdomain(panels: NormalizedPanel[]): string[] {
  const topics = new Set<string>();
  for (const panel of panels) {
    if (panel.topic) {
      topics.add(panel.topic);
    }
  }
  return Array.from(topics).sort();
}

// ============================================================================
// Helper: Get panels for a specific topic
// ============================================================================

function getPanelsForTopic(panels: NormalizedPanel[], topic: string): NormalizedPanel[] {
  return panels.filter(p => p.topic === topic && p.enabled);
}

// ============================================================================
// Helper: Format label (remove underscores, title case)
// ============================================================================

function formatLabel(str: string): string {
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ============================================================================
// REMOVED: PanelCard Component
// ============================================================================
// Per PIN-359: Topic tabs are content contexts, not navigation.
// ALL panels under a topic must render as FULL_PANEL_SURFACE.
// There is NO "card vs surface" decision inside topic context.
// Panel inference is KILLED - all panels are surfaces.
// ============================================================================

// ============================================================================
// Full Panel Surface Component (PIN-359: ALL panels render as surfaces)
// Topic tabs are content contexts - panels are already selected by topic.
// NO inference, NO card mode, NO click-to-expand inside topic context.
// ============================================================================

interface FullPanelSurfaceProps {
  panel: NormalizedPanel;
}

function FullPanelSurface({ panel }: FullPanelSurfaceProps) {
  const RenderIcon = RENDER_MODE_ICONS[panel.render_mode] || List;
  const isAutoDescription = panel._normalization?.auto_description;
  const simulation = useSimulation();
  const renderer = useRenderer();

  // Get action controls for simulation
  const actionControls = panel.controls?.filter(c => c.category === 'action') || [];

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
      {/* Panel Header - NO button, NO click handler, NO menu */}
      <div className="px-5 py-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-900/30 rounded-lg">
            <RenderIcon size={20} className="text-primary-400" />
          </div>
          <div>
            <h3 className="font-medium text-gray-100">{panel.panel_name}</h3>
            {panel.short_description && (
              <div className="flex items-center gap-2 mt-0.5">
                <p className="text-sm text-gray-400">{panel.short_description}</p>
                {isAutoDescription && (
                  <InspectorOnly>
                    <span className="text-xs px-1 py-0.5 bg-amber-900/30 text-amber-500 rounded font-mono">
                      AUTO
                    </span>
                  </InspectorOnly>
                )}
              </div>
            )}
          </div>
        </div>
        {/* Order badge - Inspector only */}
        <InspectorOnly>
          <span className="text-xs px-2 py-1 bg-emerald-900/30 text-emerald-400 rounded font-mono">
            {panel.order}
          </span>
        </InspectorOnly>
      </div>

      {/* Controls Section - Phase-2A.2 Simulation */}
      {actionControls.length > 0 && (
        <div className="px-5 py-4 border-b border-gray-700 bg-gray-800/50">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
              Actions
              {simulation.isSimulationEnabled && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-amber-900/50 text-amber-400 border border-amber-700/50">
                  <Beaker size={12} />
                  SIMULATION
                </span>
              )}
            </h4>
            <InspectorOnly>
              <span className="text-xs text-gray-500">
                {actionControls.length} action{actionControls.length !== 1 ? 's' : ''}
              </span>
            </InspectorOnly>
          </div>
          <div className="space-y-2">
            {actionControls.map((control, idx) => (
              <SimulatedControl
                key={`${control.type}-${idx}`}
                control={control}
                panelId={panel.panel_id}
                showType={renderer.showControlTypes}
              />
            ))}
          </div>
        </div>
      )}

      {/* Panel Content - SDSR data binding via PanelContentRegistry */}
      <div className="p-5">
        {hasPanelContent(panel.panel_id) ? (
          <>
            <PanelContent panel={panel} />
            <InspectorOnly>
              <div className="mt-3 pt-3 border-t border-gray-700/50">
                <span className="text-xs px-2 py-1 bg-green-900/30 text-green-400 rounded font-mono">
                  SDSR BOUND
                </span>
              </div>
            </InspectorOnly>
          </>
        ) : (
          <div className="bg-gray-900/50 border border-dashed border-gray-600 rounded-lg p-8 text-center">
            <p className="text-gray-500 text-sm">
              Content surface — awaiting backend binding
            </p>
            <InspectorOnly>
              <p className="text-gray-600 text-xs mt-2 font-mono">
                render_mode: {panel.render_mode} | controls: {panel.control_count}
              </p>
            </InspectorOnly>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Topic Tabs Component (Horizontal - Main Workspace)
// ============================================================================

interface TopicTabsProps {
  topics: string[];
  activeTopic: string | null;
  onSelectTopic: (topic: string) => void;
}

function TopicTabs({ topics, activeTopic, onSelectTopic }: TopicTabsProps) {
  if (topics.length === 0) return null;

  return (
    <div className="border-b border-gray-700">
      <div className="flex gap-1 overflow-x-auto">
        {topics.map((topic) => (
          <button
            key={topic}
            onClick={() => onSelectTopic(topic)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
              activeTopic === topic
                ? 'text-primary-400 border-primary-400 bg-primary-900/10'
                : 'text-gray-400 border-transparent hover:text-gray-200 hover:border-gray-600'
            )}
          >
            {formatLabel(topic)}
          </button>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Panels Grid (Under Selected Topic)
// PIN-359: ALL panels render as FULL_PANEL_SURFACE inside topic context.
// NO card mode. NO click-to-expand. NO inference.
// Topic tabs are content contexts - panels are already selected by topic.
// ============================================================================

interface PanelsGridProps {
  panels: NormalizedPanel[];
}

function PanelsGrid({ panels }: PanelsGridProps) {
  if (panels.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="text-gray-500">No panels in this topic.</p>
      </div>
    );
  }

  // PIN-359: ALL panels render as full surfaces - no O1 vs O2-O5 distinction
  // Topic context = surface mode. Panel inference is KILLED.
  return (
    <div className="space-y-4">
      {panels.map((panel) => (
        <FullPanelSurface key={panel.panel_id} panel={panel} />
      ))}
    </div>
  );
}

// ============================================================================
// Loading State
// ============================================================================

function DomainLoading() {
  return (
    <div className="flex items-center justify-center py-16">
      <Loader2 className="animate-spin text-gray-500 mr-3" size={24} />
      <span className="text-gray-400">Loading projection...</span>
    </div>
  );
}

// ============================================================================
// Error State
// ============================================================================

function DomainError({ error, onRetry }: { error: string; onRetry: () => void }) {
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

function DomainNotFound({ domainName }: { domainName: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <AlertCircle className="text-amber-500 mb-3" size={32} />
      <h3 className="text-lg font-medium text-amber-400 mb-2">Domain Not Found</h3>
      <p className="text-sm text-gray-400">
        The domain "{domainName}" is not defined in the projection lock.
      </p>
    </div>
  );
}

// ============================================================================
// Main Domain Page Component
// LOCKED: Header = Domain → Subdomain → Description → Topic Tabs
// Panels render ONLY under selected topic
// ============================================================================

interface DomainPageProps {
  domainName: DomainName;
}

export function DomainPage({ domainName }: DomainPageProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const renderer = useRenderer();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [domain, setDomain] = useState<NormalizedDomain | null>(null);
  const [subdomainPanels, setSubdomainPanels] = useState<NormalizedPanel[]>([]);

  // Get subdomain from URL (set by sidebar)
  const activeSubdomain = searchParams.get('subdomain');
  const [activeTopic, setActiveTopic] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      await loadProjection();
      // Use normalized domain (with placeholder descriptions in preflight)
      const loadedDomain = getNormalizedDomain(domainName);
      if (loadedDomain) {
        setDomain(loadedDomain);

        // Get subdomains for this domain
        const subdomains = getSubdomainsForDomain(domainName);

        // If subdomain is specified, load its panels (normalized)
        if (activeSubdomain && subdomains.includes(activeSubdomain)) {
          const panels = getNormalizedPanelsForSubdomain(domainName, activeSubdomain);
          setSubdomainPanels(panels.filter(p => p.enabled));

          // Auto-select first topic
          const topics = getTopicsForSubdomain(panels);
          if (topics.length > 0 && !activeTopic) {
            setActiveTopic(topics[0]);
          }
        } else if (subdomains.length > 0) {
          // Auto-select first subdomain if none specified
          const firstSubdomain = subdomains[0];
          setSearchParams({ subdomain: firstSubdomain });
          const panels = getNormalizedPanelsForSubdomain(domainName, firstSubdomain);
          setSubdomainPanels(panels.filter(p => p.enabled));

          const topics = getTopicsForSubdomain(panels);
          if (topics.length > 0) {
            setActiveTopic(topics[0]);
          }
        } else {
          setSubdomainPanels([]);
        }
      } else {
        setDomain(null);
        setSubdomainPanels([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projection');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [domainName, activeSubdomain]);

  // Get topics for current subdomain
  const topics = useMemo(() => {
    return getTopicsForSubdomain(subdomainPanels);
  }, [subdomainPanels]);

  // Auto-select first topic when topics change
  useEffect(() => {
    if (topics.length > 0 && (!activeTopic || !topics.includes(activeTopic))) {
      setActiveTopic(topics[0]);
    }
  }, [topics, activeTopic]);

  // Get panels for active topic
  const topicPanels = useMemo(() => {
    if (!activeTopic) return [];
    return getPanelsForTopic(subdomainPanels, activeTopic);
  }, [subdomainPanels, activeTopic]);

  const Icon = DOMAIN_ICONS[domainName] || LayoutDashboard;

  if (loading) {
    return <DomainLoading />;
  }

  if (error) {
    return <DomainError error={error} onRetry={loadData} />;
  }

  if (!domain) {
    return <DomainNotFound domainName={domainName} />;
  }

  return (
    <div className="space-y-6">
      {/* ================================================================
          HEADER HIERARCHY (LOCKED ORDER):
          1. Domain
          2. Subdomain
          3. Short description (if provided)
          4. Topic tabs
          ================================================================ */}

      {/* 1. Domain */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-900/30 rounded-lg">
          <Icon size={24} className="text-primary-400" />
        </div>
        <h1 className="text-2xl font-semibold text-gray-100">{domain.domain}</h1>
      </div>

      {/* 2. Subdomain */}
      {activeSubdomain && (
        <div className="text-lg font-medium text-gray-300">
          {formatLabel(activeSubdomain)}
        </div>
      )}

      {/* 3. Short Description (domain level) */}
      {domain.short_description && (
        <div className="flex items-center gap-2">
          <p className="text-sm text-gray-400">{domain.short_description}</p>
          {/* Auto-description marker - Inspector only */}
          {domain._normalization?.auto_description && (
            <InspectorOnly>
              <span className="text-xs px-1.5 py-0.5 bg-amber-900/30 text-amber-500 rounded font-mono">
                AUTO
              </span>
            </InspectorOnly>
          )}
        </div>
      )}

      {/* 4. Topic Tabs (Horizontal) */}
      <TopicTabs
        topics={topics}
        activeTopic={activeTopic}
        onSelectTopic={setActiveTopic}
      />

      {/* ================================================================
          PANELS (Render ONLY under selected topic)
          ================================================================ */}

      {activeTopic ? (
        <div className="space-y-4">
          <PanelsGrid panels={topicPanels} />
        </div>
      ) : (
        <div className="py-12 text-center">
          <p className="text-gray-500">Select a topic to view panels.</p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Domain Page Exports (one per domain for routing)
// ============================================================================

export function OverviewPage() {
  return <DomainPage domainName="Overview" />;
}

export function ActivityPage() {
  return <DomainPage domainName="Activity" />;
}

export function IncidentsPage() {
  return <DomainPage domainName="Incidents" />;
}

export function PoliciesPage() {
  return <DomainPage domainName="Policies" />;
}

export function LogsPage() {
  return <DomainPage domainName="Logs" />;
}
