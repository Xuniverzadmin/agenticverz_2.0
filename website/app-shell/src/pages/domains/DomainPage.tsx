/**
 * Domain Page Component
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime (navigation)
 *   Execution: async (projection load)
 * Role: Render a domain with subdomains and topics from L2.1 UI Projection Lock
 * Reference: L2.1 UI Projection Pipeline, PIN-352, PIN-386
 *
 * GOVERNANCE RULES (LOCKED):
 * - Header hierarchy: Domain → Subdomain → Short Description → Topic Tabs
 * - Topic tabs are horizontal, in main workspace
 * - Panels render ONLY under selected topic
 * - NO internal IDs in customer-facing header
 * - NO kebab menus
 *
 * ORDERING GOVERNANCE (LOCKED):
 * The UI never decides "what comes first." It only reflects what the system
 * declares should be first. Ordering is semantic intent, not a UI concern.
 *
 * | Layer    | Order Source               | Sort Method                |
 * |----------|----------------------------|----------------------------|
 * | Domains  | domain.order (numeric)     | a.order - b.order          |
 * | Topics   | topic_display_order (num)  | a.display_order - b.display_order |
 * | Panels   | panel.order (alphanumeric) | String.localeCompare       |
 * | Controls | control.order (numeric)    | a.order - b.order          |
 *
 * FORBIDDEN:
 * - Alphabetical sorting (has zero semantic signal)
 * - Encoding order in IDs (IDs identify, not govern layout)
 * - Deriving order in React (order comes from AURORA_L2 compiler)
 *
 * BINDING AUTHORITY (PIN-386):
 * - binding_status === "BOUND" → controls enabled
 * - binding_status === "DRAFT" → controls disabled
 * - binding_status === "INFO" → no controls rendered
 * - binding_status === "UNBOUND" → panel hidden
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
  User,
  Plug,
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
  getTopicsForSubdomain as getScaffoldingTopicsForSubdomain,
  isDomainFromProjection,
  type NormalizedPanel,
  type NormalizedDomain,
  type ScaffoldingTopic,
} from '@/contracts/ui_projection_loader';
import type { PanelClass } from '@/contracts/ui_projection_types';
import type { Domain, Panel, DomainName, RenderMode } from '@/contracts/ui_projection_types';
import { preflightLogger } from '@/lib/preflightLogger';
import { useRenderer, InspectorOnly } from '@/contexts/RendererContext';
import { RealControl } from '@/components/controls/RealControl';
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
  Account: User,
  Connectivity: Plug,
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
// Topic with display order (LOCKED - ordering governance)
// ============================================================================
// UI sorts topics by display_order, NOT alphabetically.
// Alphabetical sorting answers "what comes first lexicographically?"
// But users care about "what should I look at first?"
// display_order is semantic intent from AURORA_L2, not a UI concern.
// ============================================================================

interface TopicWithOrder {
  topic: string;
  display_order: number;
}

// ============================================================================
// Helper: Get unique topics for a subdomain (sorted by display_order)
// ============================================================================

function getTopicsForSubdomain(panels: NormalizedPanel[]): TopicWithOrder[] {
  const topicMap = new Map<string, number>();

  for (const panel of panels) {
    if (panel.topic) {
      // Use the first panel's display_order for each topic
      // If not set, default to 0
      if (!topicMap.has(panel.topic)) {
        topicMap.set(panel.topic, panel.topic_display_order ?? 0);
      }
    }
  }

  // Convert to array and sort by display_order (numeric, ascending)
  // NEVER alphabetically - that has zero semantic signal
  return Array.from(topicMap.entries())
    .map(([topic, display_order]) => ({ topic, display_order }))
    .sort((a, b) => a.display_order - b.display_order);
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
//
// UI-AS-CONSTRAINT DOCTRINE (LOCKED - PIN-418)
// ============================================================================
// | State    | Label            | Dim Header? | Show Controls? | Message                                  |
// |----------|------------------|-------------|----------------|------------------------------------------|
// | EMPTY    | Empty            | yes         | no             | "This panel is planned but not yet defined" |
// | UNBOUND  | Awaiting Backend | yes         | no             | "Backend capability not connected"       |
// | DRAFT    | Preview          | no          | yes (disabled) | "Data not yet observed"                  |
// | BOUND    | (none)           | no          | yes            | (normal rendering)                       |
// | DEFERRED | On Hold          | yes         | no             | "This feature is deferred by governance" |
// ============================================================================
// ALL panels MUST render (enabled: true). State controls UX appearance.
// Panels MUST NOT be hidden. Empty state is a signal, not a failure.
// ============================================================================

interface FullPanelSurfaceProps {
  panel: NormalizedPanel;
}

function FullPanelSurface({ panel }: FullPanelSurfaceProps) {
  const RenderIcon = RENDER_MODE_ICONS[panel.render_mode] || List;
  const isAutoDescription = panel._normalization?.auto_description;
  const renderer = useRenderer();

  // HIL v1: Visual distinction for interpretation panels
  const isInterpretation = panel.panel_class === 'interpretation';

  // ============================================================================
  // UI-as-Constraint STATE → UX CONTRACT (LOCKED)
  // | State    | Label            | Dim Header? | Show Controls? | Message                                  |
  // |----------|------------------|-------------|----------------|------------------------------------------|
  // | EMPTY    | Empty            | yes         | no             | "This panel is planned but not yet defined" |
  // | UNBOUND  | Awaiting Backend | yes         | no             | "Backend capability not connected"       |
  // | DRAFT    | Preview          | no          | yes (disabled) | "Data not yet observed"                  |
  // | BOUND    | (none)           | no          | yes            | (normal)                                 |
  // | DEFERRED | On Hold          | yes         | no             | "This feature is deferred by governance" |
  // ============================================================================
  const bindingStatus = panel.binding_status ?? 'UNBOUND';
  const controlsEnabled = bindingStatus === 'BOUND';
  const isDraft = bindingStatus === 'DRAFT';
  const isEmptyState = ['EMPTY', 'UNBOUND', 'DEFERRED'].includes(bindingStatus);
  const shouldDimHeader = isEmptyState;

  // State label mapping
  const stateLabels: Record<string, string> = {
    EMPTY: 'Empty',
    UNBOUND: 'Awaiting Backend',
    DRAFT: 'Preview',
    DEFERRED: 'On Hold',
  };

  // Get action controls
  const actionControls = panel.controls?.filter(c => c.category === 'action') || [];

  // ============================================================================
  // DEV-ONLY: Console warning for DRAFT controls (helps backend teams diagnose)
  // This warning appears when action controls exist but are disabled due to
  // missing SDSR verification. Run SDSR scenario to move capability to OBSERVED.
  // ============================================================================
  if (import.meta.env.DEV && isDraft && actionControls.length > 0) {
    console.warn(
      `[AURORA_L2] Panel "${panel.panel_id}" has DRAFT binding status.\n` +
      `  → ${actionControls.length} action control(s) are DISABLED.\n` +
      `  → Controls: ${actionControls.map(c => c.type).join(', ')}\n` +
      `  → To enable: Run SDSR scenario that exercises these capabilities.\n` +
      `  → Reference: PIN-386 (SDSR → AURORA_L2 Observation Schema Contract)`
    );
  }

  return (
    <div className={cn(
      "bg-gray-800 border rounded-lg overflow-hidden",
      // HIL v1: Interpretation panels have subtle visual distinction
      isInterpretation
        ? "border-blue-700/50 border-l-2 border-l-blue-500"
        : "border-gray-700",
      // UI-as-Constraint: EMPTY/UNBOUND/DEFERRED states get subtle opacity
      isEmptyState && "opacity-75"
    )}>
      {/* Panel Header - NO button, NO click handler, NO menu */}
      <div className={cn(
        "px-5 py-4 border-b border-gray-700 flex items-center justify-between",
        // UI-as-Constraint: Dim header for EMPTY/UNBOUND/DEFERRED
        shouldDimHeader && "bg-gray-800/50"
      )}>
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            // HIL v1: Interpretation panels have blue-tinted icon background
            isInterpretation
              ? "bg-blue-900/30"
              : "bg-primary-900/30",
            // UI-as-Constraint: Dim icon for empty states
            shouldDimHeader && "opacity-60"
          )}>
            <RenderIcon size={20} className={cn(
              isInterpretation ? "text-blue-400" : "text-primary-400",
              shouldDimHeader && "opacity-60"
            )} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className={cn(
                "font-medium",
                shouldDimHeader ? "text-gray-400" : "text-gray-100"
              )}>{panel.panel_name}</h3>
              {/* UI-as-Constraint: State label badge */}
              {stateLabels[bindingStatus] && (
                <span className={cn(
                  "text-xs px-1.5 py-0.5 rounded font-medium",
                  bindingStatus === 'EMPTY' && "bg-gray-700/50 text-gray-500",
                  bindingStatus === 'UNBOUND' && "bg-amber-900/30 text-amber-500/70",
                  bindingStatus === 'DRAFT' && "bg-yellow-900/30 text-yellow-500",
                  bindingStatus === 'DEFERRED' && "bg-gray-700/50 text-gray-500"
                )}>
                  {stateLabels[bindingStatus]}
                </span>
              )}
              {/* HIL v1: Derived badge for interpretation panels */}
              {isInterpretation && !isEmptyState && (
                <span className="text-xs px-1.5 py-0.5 bg-blue-900/30 text-blue-400 rounded font-medium">
                  Derived
                </span>
              )}
            </div>
            {panel.short_description && (
              <div className="flex items-center gap-2 mt-0.5">
                <p className={cn(
                  "text-sm",
                  shouldDimHeader ? "text-gray-500" : "text-gray-400"
                )}>{panel.short_description}</p>
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

      {/* Controls Section - Real Actions (AURORA-bound) */}
      {/* UI-as-Constraint: No controls for EMPTY/UNBOUND/DEFERRED states */}
      {actionControls.length > 0 && !isEmptyState && (
        <div className="px-5 py-4 border-b border-gray-700 bg-gray-800/50">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
              Actions
              {/* DRAFT indicator: Controls exist but unverified by SDSR */}
              {isDraft && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-gray-700/50 text-gray-400 border border-gray-600/50">
                  AWAITING VERIFICATION
                </span>
              )}
              {/* BOUND indicator: System-verified controls */}
              {controlsEnabled && (
                <InspectorOnly>
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-green-900/50 text-green-400 border border-green-700/50">
                    VERIFIED
                  </span>
                  {/* SDSR observation metadata - makes truth inspectable */}
                  {panel.binding_metadata?.scenario_ids && panel.binding_metadata.scenario_ids.length > 0 && (
                    <span className="text-xs text-green-400/70 ml-2 font-mono">
                      {panel.binding_metadata.scenario_ids.join(', ')}
                      {panel.binding_metadata.observed_at && (
                        <span className="text-gray-500 ml-1">
                          @ {new Date(panel.binding_metadata.observed_at).toLocaleDateString()}
                        </span>
                      )}
                    </span>
                  )}
                </InspectorOnly>
              )}
            </h4>
            <InspectorOnly>
              <span className="text-xs text-gray-500">
                {actionControls.length} action{actionControls.length !== 1 ? 's' : ''} | {bindingStatus}
              </span>
            </InspectorOnly>
          </div>
          <div className="space-y-2">
            {actionControls.map((control, idx) => (
              <RealControl
                key={`${control.type}-${idx}`}
                control={control}
                panelId={panel.panel_id}
                showType={renderer.showControlTypes}
                disabled={!controlsEnabled}
              />
            ))}
          </div>
        </div>
      )}

      {/* Panel Content - SDSR data binding via PanelContentRegistry */}
      <div className="p-5">
        {/* UI-as-Constraint: Show state-specific message for non-BOUND panels */}
        {isEmptyState ? (
          <div className={cn(
            "border border-dashed rounded-lg p-8 text-center",
            bindingStatus === 'EMPTY' && "bg-gray-900/30 border-gray-700",
            bindingStatus === 'UNBOUND' && "bg-amber-900/10 border-amber-700/30",
            bindingStatus === 'DEFERRED' && "bg-gray-900/30 border-gray-700"
          )}>
            <p className={cn(
              "text-sm",
              bindingStatus === 'EMPTY' && "text-gray-500",
              bindingStatus === 'UNBOUND' && "text-amber-500/70",
              bindingStatus === 'DEFERRED' && "text-gray-500"
            )}>
              {panel.disabled_reason || 'Panel unavailable'}
            </p>
            <InspectorOnly>
              <p className="text-gray-600 text-xs mt-2 font-mono">
                state: {bindingStatus} | render_mode: {panel.render_mode}
              </p>
            </InspectorOnly>
          </div>
        ) : hasPanelContent(panel.panel_id) ? (
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
              {panel.disabled_reason || 'Content surface — awaiting backend binding'}
            </p>
            <InspectorOnly>
              <p className="text-gray-600 text-xs mt-2 font-mono">
                state: {bindingStatus} | render_mode: {panel.render_mode} | controls: {panel.control_count}
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
  topics: TopicWithOrder[];
  activeTopic: string | null;
  onSelectTopic: (topic: string) => void;
}

function TopicTabs({ topics, activeTopic, onSelectTopic }: TopicTabsProps) {
  if (topics.length === 0) return null;

  return (
    <div className="border-b border-gray-700">
      <div className="flex gap-1 overflow-x-auto">
        {/* Topics rendered in display_order (semantic intent, not alphabetical) */}
        {topics.map(({ topic, display_order }) => (
          <button
            key={topic}
            onClick={() => onSelectTopic(topic)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
              activeTopic === topic
                ? 'text-primary-400 border-primary-400 bg-primary-900/10'
                : 'text-gray-400 border-transparent hover:text-gray-200 hover:border-gray-600'
            )}
            title={`Order: ${display_order}`}
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
//
// HIL v1 (PIN-416, PIN-417): Panels are split by panel_class:
// - interpretation panels render first (Summary section)
// - execution panels render after (standard panels)
// - No reordering within each group
// - No hiding of execution panels
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

  // HIL v1: Split panels by class
  // interpretation panels are summaries/aggregations (render first)
  // execution panels are raw data/lists (render after)
  const interpretationPanels = panels.filter(
    (p) => p.panel_class === 'interpretation'
  );
  const executionPanels = panels.filter(
    (p) => (p.panel_class || 'execution') === 'execution'
  );

  return (
    <div className="space-y-6">
      {/* HIL v1: Interpretation Section (Summaries) */}
      {/* Renders above execution panels in visually distinct section */}
      {/* Empty section renders nothing (no conditional message) */}
      {interpretationPanels.length > 0 && (
        <div className="space-y-4">
          {/* Section label - subtle, not dominant */}
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="font-medium">Summary</span>
            <InspectorOnly>
              <span className="text-xs px-1.5 py-0.5 bg-blue-900/30 text-blue-400 rounded font-mono">
                HIL
              </span>
            </InspectorOnly>
          </div>
          {/* Interpretation panels - same rendering as execution */}
          <div className="space-y-4">
            {interpretationPanels.map((panel) => (
              <FullPanelSurface key={panel.panel_id} panel={panel} />
            ))}
          </div>
          {/* Divider between sections */}
          <div className="border-t border-gray-700/50" />
        </div>
      )}

      {/* Execution panels - standard rendering */}
      {/* Always renders (no conditional hiding) */}
      <div className="space-y-4">
        {executionPanels.map((panel) => (
          <FullPanelSurface key={panel.panel_id} panel={panel} />
        ))}
      </div>
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

          // Auto-select first topic (by display_order, not alphabetical)
          const topics = getTopicsForSubdomain(panels);
          if (topics.length > 0 && !activeTopic) {
            setActiveTopic(topics[0].topic);
          }
        } else if (subdomains.length > 0) {
          // Auto-select first subdomain if none specified
          const firstSubdomain = subdomains[0];
          setSearchParams({ subdomain: firstSubdomain });
          const panels = getNormalizedPanelsForSubdomain(domainName, firstSubdomain);
          setSubdomainPanels(panels.filter(p => p.enabled));

          const topics = getTopicsForSubdomain(panels);
          if (topics.length > 0) {
            setActiveTopic(topics[0].topic);
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
  // Falls back to scaffolding topics when panels are empty (UI-as-Constraint doctrine)
  const topics = useMemo((): TopicWithOrder[] => {
    // If we have panels, derive topics from them
    if (subdomainPanels.length > 0) {
      return getTopicsForSubdomain(subdomainPanels);
    }

    // Fallback: get topics from scaffolding (ui_plan authority)
    if (activeSubdomain) {
      const scaffoldingTopics = getScaffoldingTopicsForSubdomain(domainName, activeSubdomain);
      return scaffoldingTopics.map(t => ({
        topic: t.id,
        display_order: t.display_order,
      }));
    }

    return [];
  }, [subdomainPanels, activeSubdomain, domainName]);

  // Auto-select first topic when topics change (by display_order)
  useEffect(() => {
    const topicExists = topics.some(t => t.topic === activeTopic);
    if (topics.length > 0 && (!activeTopic || !topicExists)) {
      setActiveTopic(topics[0].topic);
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

export function AccountPage() {
  return <DomainPage domainName="Account" />;
}

export function ConnectivityPage() {
  return <DomainPage domainName="Connectivity" />;
}
