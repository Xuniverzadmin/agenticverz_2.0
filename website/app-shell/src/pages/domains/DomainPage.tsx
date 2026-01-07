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
 * GOVERNANCE RULES:
 * - NO hardcoded panel names
 * - All content derived from ui_projection_lock.json
 * - Uses contracts/ui_projection_loader.ts exclusively
 */

import { useEffect, useState, useMemo } from 'react';
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Shield,
  FileText,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  List,
  Grid3x3,
  Table,
  Layers,
  CreditCard,
  FolderOpen,
  Tag,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  loadProjection,
  getDomain,
  getPanels,
} from '@/contracts/ui_projection_loader';
import type { Domain, Panel, DomainName, RenderMode } from '@/contracts/ui_projection_types';
import { preflightLogger } from '@/lib/preflightLogger';

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
// Types
// ============================================================================

interface SubdomainGroup {
  subdomain: string;
  topics: Map<string, Panel[]>;
  panelCount: number;
  enabledCount: number;
}

// ============================================================================
// Helper: Group panels by subdomain and topic
// ============================================================================

function groupPanelsBySubdomainAndTopic(panels: Panel[]): SubdomainGroup[] {
  const subdomainMap = new Map<string, Map<string, Panel[]>>();

  for (const panel of panels) {
    const subdomain = panel.subdomain || 'DEFAULT';
    const topic = panel.topic || 'GENERAL';

    if (!subdomainMap.has(subdomain)) {
      subdomainMap.set(subdomain, new Map());
    }

    const topicMap = subdomainMap.get(subdomain)!;
    if (!topicMap.has(topic)) {
      topicMap.set(topic, []);
    }
    topicMap.get(topic)!.push(panel);
  }

  // Convert to array and sort
  const result: SubdomainGroup[] = [];
  for (const [subdomain, topicMap] of subdomainMap) {
    const allPanels = Array.from(topicMap.values()).flat();
    result.push({
      subdomain,
      topics: topicMap,
      panelCount: allPanels.length,
      enabledCount: allPanels.filter(p => p.enabled).length,
    });
  }

  return result.sort((a, b) => a.subdomain.localeCompare(b.subdomain));
}

// ============================================================================
// Panel Card Component
// ============================================================================

interface PanelCardProps {
  panel: Panel;
  compact?: boolean;
}

function PanelCard({ panel, compact = false }: PanelCardProps) {
  const RenderIcon = RENDER_MODE_ICONS[panel.render_mode] || List;

  if (compact) {
    return (
      <div className={cn(
        'flex items-center justify-between px-3 py-2 rounded border transition-colors',
        panel.enabled
          ? 'bg-gray-800 border-gray-700 hover:border-gray-600'
          : 'bg-gray-900/50 border-gray-800 opacity-60'
      )}>
        <div className="flex items-center gap-2">
          <RenderIcon size={14} className="text-gray-500" />
          <span className="text-sm text-gray-200">{panel.panel_name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-mono">{panel.render_mode}</span>
          {panel.enabled ? (
            <span className="w-2 h-2 rounded-full bg-green-500" title="Enabled" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-gray-600" title="Disabled" />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      'bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors',
      !panel.enabled && 'opacity-60'
    )}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <RenderIcon size={16} className="text-gray-500" />
          <h4 className="font-medium text-gray-100">{panel.panel_name}</h4>
        </div>
        <span className={cn(
          'text-xs px-2 py-0.5 rounded',
          panel.enabled
            ? 'bg-green-900/30 text-green-400'
            : 'bg-gray-700 text-gray-500'
        )}>
          {panel.enabled ? 'Enabled' : 'Disabled'}
        </span>
      </div>

      <div className="space-y-1.5 text-sm">
        <div className="flex items-center justify-between text-gray-400">
          <span>ID</span>
          <span className="font-mono text-xs text-gray-500">{panel.panel_id}</span>
        </div>
        <div className="flex items-center justify-between text-gray-400">
          <span>Render</span>
          <span className="font-mono text-gray-300">{panel.render_mode}</span>
        </div>
        <div className="flex items-center justify-between text-gray-400">
          <span>Controls</span>
          <span className="font-mono text-gray-300">{panel.control_count}</span>
        </div>
      </div>

      {/* Control Types */}
      {panel.controls.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="flex flex-wrap gap-1">
            {panel.controls.slice(0, 4).map((control, idx) => (
              <span
                key={idx}
                className="text-xs px-1.5 py-0.5 bg-gray-700 text-gray-400 rounded"
              >
                {control.type}
              </span>
            ))}
            {panel.controls.length > 4 && (
              <span className="text-xs px-1.5 py-0.5 text-gray-500">
                +{panel.controls.length - 4}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Topic Section Component
// ============================================================================

interface TopicSectionProps {
  topic: string;
  panels: Panel[];
}

function TopicSection({ topic, panels }: TopicSectionProps) {
  const [expanded, setExpanded] = useState(true);
  const enabledCount = panels.filter(p => p.enabled).length;

  const handleToggle = () => {
    const newExpanded = !expanded;
    setExpanded(newExpanded);
    preflightLogger.domain.topicExpand(topic);
  };

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800/50 hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Tag size={14} className="text-gray-500" />
          <span className="font-medium text-gray-200">{topic.replace(/_/g, ' ')}</span>
          <span className="text-xs text-gray-500">
            ({enabledCount}/{panels.length} enabled)
          </span>
        </div>
        {expanded ? (
          <ChevronDown size={16} className="text-gray-500" />
        ) : (
          <ChevronRight size={16} className="text-gray-500" />
        )}
      </button>

      {expanded && (
        <div className="p-3 space-y-2 bg-gray-900/30">
          {panels.map((panel) => (
            <PanelCard key={panel.panel_id} panel={panel} compact />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Subdomain Section Component
// ============================================================================

interface SubdomainSectionProps {
  group: SubdomainGroup;
}

function SubdomainSection({ group }: SubdomainSectionProps) {
  const [expanded, setExpanded] = useState(true);
  const topics = Array.from(group.topics.entries()).sort((a, b) => a[0].localeCompare(b[0]));

  const handleToggle = () => {
    const newExpanded = !expanded;
    setExpanded(newExpanded);
    preflightLogger.domain.subdomainExpand(group.subdomain);
  };

  return (
    <div className="border border-gray-600 rounded-xl overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-5 py-4 bg-gray-800 hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center gap-3">
          <FolderOpen size={18} className="text-primary-400" />
          <span className="font-semibold text-gray-100">{group.subdomain.replace(/_/g, ' ')}</span>
          <span className="text-sm text-gray-400">
            {group.enabledCount}/{group.panelCount} panels • {topics.length} topics
          </span>
        </div>
        {expanded ? (
          <ChevronDown size={18} className="text-gray-400" />
        ) : (
          <ChevronRight size={18} className="text-gray-400" />
        )}
      </button>

      {expanded && (
        <div className="p-4 space-y-3 bg-gray-850">
          {topics.map(([topic, panels]) => (
            <TopicSection key={topic} topic={topic} panels={panels} />
          ))}
        </div>
      )}
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
// ============================================================================

interface DomainPageProps {
  domainName: DomainName;
}

export function DomainPage({ domainName }: DomainPageProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [domain, setDomain] = useState<Domain | null>(null);
  const [panels, setPanels] = useState<Panel[]>([]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      await loadProjection();
      const loadedDomain = getDomain(domainName);
      if (loadedDomain) {
        setDomain(loadedDomain);
        setPanels(getPanels(domainName)); // Get ALL panels, not just enabled
      } else {
        setDomain(null);
        setPanels([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projection');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [domainName]);

  // Group panels by subdomain and topic
  const subdomainGroups = useMemo(() => {
    const groups = groupPanelsBySubdomainAndTopic(panels);
    if (domain) {
      preflightLogger.domain.render(domain.domain, groups.length, panels.length);
    }
    return groups;
  }, [panels, domain]);

  const Icon = DOMAIN_ICONS[domainName] || LayoutDashboard;
  const enabledPanels = panels.filter(p => p.enabled);

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
      {/* Domain Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-900/30 rounded-lg">
            <Icon size={24} className="text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-gray-100">{domain.domain}</h1>
            <p className="text-sm text-gray-400">
              {subdomainGroups.length} subdomains • {panels.length} panels • {domain.total_controls} controls
            </p>
          </div>
        </div>

        {/* Preflight Badge */}
        {import.meta.env.VITE_PREFLIGHT_MODE === 'true' && (
          <span className="px-3 py-1 bg-amber-900/30 text-amber-400 text-sm font-mono rounded">
            PREFLIGHT
          </span>
        )}
      </div>

      {/* Domain Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-semibold text-gray-100">{subdomainGroups.length}</div>
          <div className="text-sm text-gray-400">Subdomains</div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-semibold text-gray-100">{panels.length}</div>
          <div className="text-sm text-gray-400">Total Panels</div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-semibold text-green-400">{enabledPanels.length}</div>
          <div className="text-sm text-gray-400">Enabled</div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-semibold text-gray-100">{domain.total_controls}</div>
          <div className="text-sm text-gray-400">Controls</div>
        </div>
      </div>

      {/* Subdomains */}
      <div className="space-y-4">
        <h2 className="text-lg font-medium text-gray-200">Subdomains & Topics</h2>
        {subdomainGroups.length === 0 ? (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
            <p className="text-gray-400">No panels in this domain.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {subdomainGroups.map((group) => (
              <SubdomainSection key={group.subdomain} group={group} />
            ))}
          </div>
        )}
      </div>

      {/* Projection Source (dev info) */}
      <div className="text-xs text-gray-500 border-t border-gray-800 pt-4">
        <span className="font-mono">Source: ui_projection_lock.json</span>
        <span className="mx-2">•</span>
        <span className="font-mono">Order: {domain.order}</span>
      </div>
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
