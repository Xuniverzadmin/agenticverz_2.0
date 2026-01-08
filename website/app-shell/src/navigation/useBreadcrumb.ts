/**
 * useBreadcrumb - Projection-Derived Breadcrumb Hook
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: route change
 *   Execution: sync
 * Role: Derive breadcrumb from current route + projection navigation map
 * Reference: PIN-358 Task Group B
 *
 * BREADCRUMB FORMAT:
 *   Domain › Subdomain? › Topic? › Panel › Entity?
 *
 * RULES:
 * - Breadcrumb is DERIVED, not declared
 * - No L2.1 changes required
 * - No projection changes required
 * - All labels come from projection
 */

import { useMemo } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { getDomains, isProjectionLoaded } from '@/contracts/ui_projection_loader';
import type { Domain, Panel, DomainName } from '@/contracts/ui_projection_types';

// ============================================================================
// Types
// ============================================================================

export interface BreadcrumbSegment {
  label: string;
  path: string;
  type: 'domain' | 'subdomain' | 'topic' | 'panel' | 'entity';
  id?: string;  // Internal ID for dev display
  isActive: boolean;  // True if this is the current page
}

export interface BreadcrumbState {
  segments: BreadcrumbSegment[];
  domain: DomainName | null;
  subdomain: string | null;
  topic: string | null;
  panel: string | null;
  entity: string | null;
  isLoaded: boolean;
}

// ============================================================================
// Route Parsing
// ============================================================================

interface ParsedRoute {
  consoleRoot: string;  // 'precus' | 'cus' | 'prefops' | 'fops'
  domainSlug: string | null;
  panelSlug: string | null;
  entityId: string | null;
}

function parseRoute(pathname: string): ParsedRoute {
  // Expected formats:
  // /precus                        → domain home redirect
  // /precus/:domain                → domain home
  // /precus/:domain/:panel         → panel view
  // /precus/:domain/:panel/:entity → entity detail (O3+)

  const segments = pathname.split('/').filter(Boolean);

  return {
    consoleRoot: segments[0] || '',
    domainSlug: segments[1] || null,
    panelSlug: segments[2] || null,
    entityId: segments[3] || null,
  };
}

// ============================================================================
// Projection Lookup
// ============================================================================

function findDomainBySlug(slug: string): Domain | undefined {
  const domains = getDomains();
  // Match by lowercase domain name
  return domains.find(d => d.domain.toLowerCase() === slug.toLowerCase());
}

function findPanelBySlug(domain: Domain, panelSlug: string): Panel | undefined {
  // Match by route ending with /:domain/:panel
  const routePattern = `/${domain.domain.toLowerCase()}/${panelSlug}`;
  return domain.panels.find(p => p.route.toLowerCase().endsWith(routePattern));
}

function findPanelByRoute(fullRoute: string): { domain: Domain; panel: Panel } | undefined {
  const domains = getDomains();
  for (const domain of domains) {
    for (const panel of domain.panels) {
      if (panel.route === fullRoute) {
        return { domain, panel };
      }
    }
  }
  return undefined;
}

// ============================================================================
// Breadcrumb Builder
// ============================================================================

function buildBreadcrumb(
  parsedRoute: ParsedRoute,
  pathname: string
): BreadcrumbState {
  const segments: BreadcrumbSegment[] = [];
  let currentDomain: DomainName | null = null;
  let currentSubdomain: string | null = null;
  let currentTopic: string | null = null;
  let currentPanel: string | null = null;
  let currentEntity: string | null = parsedRoute.entityId;

  // Check if projection is loaded
  if (!isProjectionLoaded()) {
    return {
      segments: [],
      domain: null,
      subdomain: null,
      topic: null,
      panel: null,
      entity: null,
      isLoaded: false,
    };
  }

  const { consoleRoot, domainSlug, panelSlug, entityId } = parsedRoute;

  // 1. Find Domain
  if (domainSlug) {
    const domain = findDomainBySlug(domainSlug);
    if (domain) {
      currentDomain = domain.domain;

      // Domain segment (always clickable except if it's the current page)
      const domainPath = `/${consoleRoot}/${domainSlug}`;
      const isDomainActive = !panelSlug && !entityId;

      segments.push({
        label: domain.domain,
        path: domainPath,
        type: 'domain',
        isActive: isDomainActive,
      });

      // 2. Find Panel (if panelSlug provided)
      if (panelSlug) {
        const panel = findPanelBySlug(domain, panelSlug);
        if (panel) {
          currentPanel = panel.panel_name;

          // Add subdomain if present and different from domain
          if (panel.subdomain && panel.subdomain !== domain.domain) {
            currentSubdomain = panel.subdomain;
            // Subdomain is informational only - not a separate route level currently
            // We could make this clickable if subdomain routes exist
            segments.push({
              label: panel.subdomain,
              path: domainPath, // Links back to domain for now
              type: 'subdomain',
              isActive: false,
            });
          }

          // Add topic if present
          if (panel.topic) {
            currentTopic = panel.topic;
            segments.push({
              label: panel.topic,
              path: domainPath, // Links back to domain for now
              type: 'topic',
              id: panel.topic_id || undefined,
              isActive: false,
            });
          }

          // Panel segment
          const panelPath = panel.route;
          const isPanelActive = !entityId;

          segments.push({
            label: panel.panel_name,
            path: panelPath,
            type: 'panel',
            id: panel.panel_id,
            isActive: isPanelActive,
          });

          // 3. Entity (if provided - O3+ depth)
          if (entityId) {
            currentEntity = entityId;
            segments.push({
              label: entityId,
              path: `${panelPath}/${entityId}`,
              type: 'entity',
              id: entityId,
              isActive: true,
            });
          }
        } else {
          // Panel not found in projection - show as unknown
          segments.push({
            label: panelSlug,
            path: pathname,
            type: 'panel',
            isActive: true,
          });
        }
      }
    } else {
      // Domain not found - show as-is
      segments.push({
        label: domainSlug,
        path: pathname,
        type: 'domain',
        isActive: true,
      });
    }
  }

  return {
    segments,
    domain: currentDomain,
    subdomain: currentSubdomain,
    topic: currentTopic,
    panel: currentPanel,
    entity: currentEntity,
    isLoaded: true,
  };
}

// ============================================================================
// Hook
// ============================================================================

/**
 * useBreadcrumb - Returns projection-derived breadcrumb state
 *
 * @returns BreadcrumbState with segments and current context
 */
export function useBreadcrumb(): BreadcrumbState {
  const location = useLocation();

  return useMemo(() => {
    const parsedRoute = parseRoute(location.pathname);
    return buildBreadcrumb(parsedRoute, location.pathname);
  }, [location.pathname]);
}

// ============================================================================
// Utility: Format Breadcrumb for Display
// ============================================================================

/**
 * Format breadcrumb segments as a simple string (for debugging)
 */
export function formatBreadcrumb(state: BreadcrumbState): string {
  if (!state.isLoaded || state.segments.length === 0) {
    return '';
  }
  return state.segments.map(s => s.label).join(' › ');
}
