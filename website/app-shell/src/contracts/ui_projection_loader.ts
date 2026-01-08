/**
 * UI Projection Loader
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime (lazy load)
 *   Execution: async
 * Role: Single source of truth for UI projection data
 * Reference: L2.1 UI Projection Pipeline
 *
 * GOVERNANCE RULES:
 * - This is the ONLY way to access UI projection data
 * - No direct JSON imports allowed elsewhere
 * - No hardcoded domain/panel/control names
 * - Runtime validation on load
 */

import type {
  UIProjectionLock,
  Domain,
  Panel,
  Control,
  DomainName,
  ControlType,
} from "./ui_projection_types";
import { preflightLogger } from "@/lib/preflightLogger";
import {
  assertValidProjection,
  validateProjection as validateProjectionStructure,
  type ValidationResult,
} from "./projection_assertions";

// ============================================================================
// Loader State
// ============================================================================

let cachedProjection: UIProjectionLock | null = null;
let loadError: Error | null = null;

// ============================================================================
// Core Loader
// ============================================================================

/**
 * Load and validate the UI projection lock.
 * Returns cached data on subsequent calls.
 */
export async function loadProjection(): Promise<UIProjectionLock> {
  if (cachedProjection) {
    preflightLogger.projection.cached();
    return cachedProjection;
  }

  if (loadError) {
    throw loadError;
  }

  try {
    preflightLogger.projection.loadStart();

    // Fetch from public URL (works in both dev and production)
    const projectionUrl =
      import.meta.env.VITE_PROJECTION_URL || "/projection/ui_projection_lock.json";

    preflightLogger.api.request(projectionUrl);
    const response = await fetch(projectionUrl);

    if (!response.ok) {
      const error = new Error(`Failed to load projection: ${response.status}`);
      preflightLogger.api.error(projectionUrl, error);
      throw error;
    }

    preflightLogger.api.success(projectionUrl, response.status);
    const data = (await response.json()) as UIProjectionLock;

    // Runtime validation
    validateProjection(data);

    cachedProjection = data;

    preflightLogger.projection.loadSuccess({
      domains: data._statistics.domain_count,
      panels: data._statistics.panel_count,
      controls: data._statistics.control_count,
    });

    return data;
  } catch (error) {
    loadError = error instanceof Error ? error : new Error(String(error));
    preflightLogger.projection.loadError(loadError);
    throw loadError;
  }
}

/**
 * Get projection synchronously (throws if not loaded).
 * Use loadProjection() first.
 */
export function getProjection(): UIProjectionLock {
  if (!cachedProjection) {
    throw new Error(
      "Projection not loaded. Call loadProjection() first."
    );
  }
  return cachedProjection;
}

/**
 * Check if projection is loaded (for conditional rendering).
 */
export function isProjectionLoaded(): boolean {
  return cachedProjection !== null;
}

// ============================================================================
// Domain Accessors
// ============================================================================

/**
 * Get all domains in display order.
 */
export function getDomains(): Domain[] {
  const projection = getProjection();
  return [...projection.domains].sort((a, b) => a.order - b.order);
}

/**
 * Get a single domain by name.
 */
export function getDomain(name: DomainName): Domain | undefined {
  const projection = getProjection();
  return projection.domains.find((d) => d.domain === name);
}

/**
 * Get domain names in display order.
 */
export function getDomainNames(): DomainName[] {
  return getDomains().map((d) => d.domain);
}

// ============================================================================
// Panel Accessors
// ============================================================================

/**
 * Get all panels for a domain in display order.
 */
export function getPanels(domain: DomainName): Panel[] {
  const d = getDomain(domain);
  if (!d) return [];
  return [...d.panels].sort((a, b) =>
    String(a.order).localeCompare(String(b.order))
  );
}

/**
 * Get a single panel by ID.
 */
export function getPanel(panelId: string): Panel | undefined {
  const projection = getProjection();
  for (const domain of projection.domains) {
    const panel = domain.panels.find((p) => p.panel_id === panelId);
    if (panel) return panel;
  }
  return undefined;
}

/**
 * Get all enabled panels for a domain.
 */
export function getEnabledPanels(domain: DomainName): Panel[] {
  return getPanels(domain).filter((p) => p.enabled);
}

// ============================================================================
// Control Accessors
// ============================================================================

/**
 * Get all controls for a panel in display order.
 */
export function getControls(panelId: string): Control[] {
  const panel = getPanel(panelId);
  if (!panel) return [];
  return [...panel.controls].sort((a, b) => a.order - b.order);
}

/**
 * Get controls by category for a panel.
 */
export function getControlsByCategory(
  panelId: string,
  category: Control["category"]
): Control[] {
  return getControls(panelId).filter((c) => c.category === category);
}

/**
 * Check if a panel has a specific control type.
 */
export function hasControl(panelId: string, controlType: ControlType): boolean {
  return getControls(panelId).some((c) => c.type === controlType);
}

// ============================================================================
// Statistics
// ============================================================================

/**
 * Get projection statistics.
 */
export function getStatistics(): {
  domains: number;
  panels: number;
  controls: number;
} {
  const projection = getProjection();
  return {
    domains: projection._statistics.domain_count,
    panels: projection._statistics.panel_count,
    controls: projection._statistics.control_count,
  };
}

// ============================================================================
// Validation
// ============================================================================

function validateProjection(data: unknown): asserts data is UIProjectionLock {
  if (!data || typeof data !== "object") {
    throw new Error("Invalid projection: not an object");
  }

  const projection = data as Record<string, unknown>;

  // Check meta
  if (!projection._meta || typeof projection._meta !== "object") {
    throw new Error("Invalid projection: missing _meta");
  }

  const meta = projection._meta as Record<string, unknown>;
  if (meta.type !== "ui_projection_lock") {
    throw new Error(
      `Invalid projection: expected type 'ui_projection_lock', got '${meta.type}'`
    );
  }

  if (meta.processing_stage !== "LOCKED") {
    throw new Error(
      `Invalid projection: expected stage 'LOCKED', got '${meta.processing_stage}'`
    );
  }

  // Check contract
  if (!projection._contract || typeof projection._contract !== "object") {
    throw new Error("Invalid projection: missing _contract");
  }

  const contract = projection._contract as Record<string, unknown>;
  if (!contract.renderer_must_consume_only_this_file) {
    throw new Error("Invalid projection: contract violation");
  }

  // Check domains
  if (!Array.isArray(projection.domains)) {
    throw new Error("Invalid projection: domains must be an array");
  }

  if (projection.domains.length === 0) {
    throw new Error("Invalid projection: domains array is empty");
  }

  // Group H: Additional structure validation using assertions
  const validationResult = validateProjectionStructure(data);
  if (!validationResult.valid) {
    preflightLogger.projection.loadError(new Error(`Validation warnings: ${validationResult.errors.join(', ')}`));
  }
}

// ============================================================================
// Context Accessor (Group C - Domain/Subdomain Context)
// ============================================================================

export interface DomainContext {
  domain: DomainName | null;
  subdomain: string | null;
  topic: string | null;
  topicId: string | null;
  order: string | null;
  panelId: string | null;
  panelName: string | null;
}

/**
 * Get domain context from a panel ID.
 * Returns domain, subdomain, and topic info for the panel.
 */
export function getDomainContextForPanel(panelId: string): DomainContext {
  const projection = getProjection();

  for (const domain of projection.domains) {
    const panel = domain.panels.find((p) => p.panel_id === panelId);
    if (panel) {
      return {
        domain: domain.domain,
        subdomain: panel.subdomain,
        topic: panel.topic,
        topicId: panel.topic_id,
        order: panel.order,
        panelId: panel.panel_id,
        panelName: panel.panel_name,
      };
    }
  }

  return {
    domain: null,
    subdomain: null,
    topic: null,
    topicId: null,
    order: null,
    panelId: null,
    panelName: null,
  };
}

/**
 * Get domain context from a route path.
 * Parses route to extract domain and optionally panel info.
 */
export function getDomainContextForRoute(pathname: string): DomainContext {
  const projection = getProjection();

  // Parse route: /precus/{domain}/{panel-id}
  const parts = pathname.split('/').filter(Boolean);

  // Check if this is a precus or cus route
  if (parts[0] !== 'precus' && parts[0] !== 'cus') {
    return {
      domain: null,
      subdomain: null,
      topic: null,
      topicId: null,
      order: null,
      panelId: null,
      panelName: null,
    };
  }

  // Find domain from route
  const domainSlug = parts[1]?.toLowerCase();
  const domain = projection.domains.find(
    (d) => d.domain.toLowerCase() === domainSlug
  );

  if (!domain) {
    return {
      domain: null,
      subdomain: null,
      topic: null,
      topicId: null,
      order: null,
      panelId: null,
      panelName: null,
    };
  }

  // If we have a panel ID in the route
  const panelSlug = parts[2]?.toLowerCase();
  if (panelSlug) {
    const panel = domain.panels.find(
      (p) => p.panel_id.toLowerCase() === panelSlug
    );
    if (panel) {
      return {
        domain: domain.domain,
        subdomain: panel.subdomain,
        topic: panel.topic,
        topicId: panel.topic_id,
        order: panel.order,
        panelId: panel.panel_id,
        panelName: panel.panel_name,
      };
    }
  }

  // Domain only (no specific panel)
  return {
    domain: domain.domain,
    subdomain: null,
    topic: null,
    topicId: null,
    order: null,
    panelId: null,
    panelName: null,
  };
}

/**
 * Get all unique subdomains for a domain.
 */
export function getSubdomainsForDomain(domainName: DomainName): string[] {
  const domain = getDomain(domainName);
  if (!domain) return [];

  const subdomains = new Set<string>();
  for (const panel of domain.panels) {
    if (panel.subdomain) {
      subdomains.add(panel.subdomain);
    }
  }
  return Array.from(subdomains);
}

/**
 * Get panels for a specific subdomain within a domain.
 */
export function getPanelsForSubdomain(
  domainName: DomainName,
  subdomain: string
): Panel[] {
  const domain = getDomain(domainName);
  if (!domain) return [];

  return domain.panels
    .filter((p) => p.subdomain === subdomain)
    .sort((a, b) => String(a.order).localeCompare(String(b.order)));
}

// ============================================================================
// Preflight Normalizer (TODO-1: Temporary Description Injection)
// Only active in PREFLIGHT mode. Never in production.
// ============================================================================

const IS_PREFLIGHT = import.meta.env.VITE_PREFLIGHT_MODE === 'true';

export interface NormalizedPanel extends Panel {
  _normalization?: {
    auto_description: boolean;
  };
}

export interface NormalizedDomain extends Omit<Domain, 'panels'> {
  panels: NormalizedPanel[];
  _normalization?: {
    auto_description: boolean;
  };
}

/**
 * Generate a placeholder description for preflight validation.
 * RULE: Only in preflight. Never in production.
 */
function generatePlaceholderDescription(label: string, type: 'domain' | 'subdomain' | 'panel'): string {
  const cleanLabel = label.replace(/_/g, ' ').toLowerCase();
  switch (type) {
    case 'domain':
      return `Provides an overview of ${cleanLabel} across your system.`;
    case 'subdomain':
      return `Manages ${cleanLabel} configuration and monitoring.`;
    case 'panel':
      return `Displays ${cleanLabel} data and controls.`;
    default:
      return `Overview of ${cleanLabel}.`;
  }
}

/**
 * Normalize a panel with placeholder description if missing (preflight only).
 */
export function normalizePanel(panel: Panel): NormalizedPanel {
  if (!IS_PREFLIGHT || panel.short_description) {
    return panel;
  }

  return {
    ...panel,
    short_description: generatePlaceholderDescription(panel.panel_name, 'panel'),
    _normalization: {
      auto_description: true,
    },
  };
}

/**
 * Normalize a domain with placeholder description if missing (preflight only).
 */
export function normalizeDomain(domain: Domain): NormalizedDomain {
  const normalizedPanels = domain.panels.map(normalizePanel);

  if (!IS_PREFLIGHT || domain.short_description) {
    return {
      ...domain,
      panels: normalizedPanels,
    };
  }

  return {
    ...domain,
    panels: normalizedPanels,
    short_description: generatePlaceholderDescription(domain.domain, 'domain'),
    _normalization: {
      auto_description: true,
    },
  };
}

/**
 * Get normalized panels for a subdomain (with placeholder descriptions in preflight).
 */
export function getNormalizedPanelsForSubdomain(
  domainName: DomainName,
  subdomain: string
): NormalizedPanel[] {
  const panels = getPanelsForSubdomain(domainName, subdomain);
  return panels.map(normalizePanel);
}

/**
 * Get normalized domain (with placeholder descriptions in preflight).
 */
export function getNormalizedDomain(name: DomainName): NormalizedDomain | undefined {
  const domain = getDomain(name);
  if (!domain) return undefined;
  return normalizeDomain(domain);
}

// ============================================================================
// Exports
// ============================================================================

export type { UIProjectionLock, Domain, Panel, Control, DomainContext };
