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
import { CONSOLE_ROOT } from "@/routing/consoleRoots";
import {
  getScaffoldingDomain,
  getAllScaffoldingDomains,
  getScaffoldingSubdomains,
  getScaffoldingTopics,
  hasScaffoldingDomain,
  type ScaffoldingDomain,
  type ScaffoldingTopic,
} from "./ui_plan_scaffolding";

// ============================================================================
// Route Resolution (Single Source of Truth)
// ============================================================================

/**
 * Resolve a relative route to an absolute route using CONSOLE_ROOT.
 *
 * This is the ONLY place where environment-aware route resolution happens.
 * Projection routes are environment-agnostic (e.g., "/activity").
 * This function adds the console root (e.g., "/precus" or "/cus").
 *
 * Examples:
 *   resolveRoute("/activity") → "/precus/activity" (preflight)
 *   resolveRoute("/activity") → "/cus/activity" (production)
 */
function resolveRoute(relativeRoute: string): string {
  // Handle legacy absolute routes (already have /cus or /precus)
  if (relativeRoute.startsWith('/cus/') || relativeRoute.startsWith('/precus/')) {
    // Transform to relative first, then resolve
    const stripped = relativeRoute.replace(/^\/(cus|precus)/, '');
    return `${CONSOLE_ROOT}${stripped}`;
  }

  // Normal case: relative route
  return `${CONSOLE_ROOT}${relativeRoute}`;
}

/**
 * Transform all routes in the projection to absolute routes.
 * Called once at load time.
 */
function resolveProjectionRoutes(projection: UIProjectionLock): UIProjectionLock {
  return {
    ...projection,
    domains: projection.domains.map(domain => ({
      ...domain,
      route: resolveRoute(domain.route),
      panels: domain.panels.map(panel => ({
        ...panel,
        route: resolveRoute(panel.route),
      })),
    })),
  };
}

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
    const rawData = (await response.json()) as UIProjectionLock;

    // Runtime validation
    validateProjection(rawData);

    // Resolve routes based on CONSOLE_ROOT (single point of transformation)
    const data = resolveProjectionRoutes(rawData);

    // Log route resolution for debugging
    preflightLogger.projection.loadStart();
    console.log(`[PROJECTION] Routes resolved with CONSOLE_ROOT: ${CONSOLE_ROOT}`);

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
// Scaffolding Fallback (UI-as-Constraint Doctrine)
// ============================================================================
// When projection is incomplete, the UI must still render structural scaffolding
// using ui_plan.yaml as fallback authority.
//
// RULE (CONSTITUTIONAL):
// If a domain/subdomain/topic exists in ui_plan.yaml but not in projection,
// the UI MUST render structural scaffolding, NOT fail or show placeholders.
//
// Reference: ARCHITECTURE_CONSTRAINTS_V1.yaml, UI_AS_CONSTRAINT_V1.md
// ============================================================================

/**
 * Convert scaffolding domain to Domain type with EMPTY structure.
 * Panels array is empty (panels require projection).
 * This is used when projection doesn't have the domain but ui_plan does.
 */
function scaffoldingToDomain(scaffolding: ScaffoldingDomain): Domain {
  return {
    domain: scaffolding.id,
    order: scaffolding.order,
    route: scaffolding.route,
    panels: [], // No panels without projection
    panel_count: 0,
    total_controls: 0,
    short_description: scaffolding.question, // Use the domain question
  };
}

/**
 * Check if projection has a domain.
 */
function projectionHasDomain(name: DomainName): boolean {
  if (!cachedProjection) return false;
  return cachedProjection.domains.some((d) => d.domain === name);
}

// ============================================================================
// Domain Accessors (with Scaffolding Fallback)
// ============================================================================

/**
 * Get all domains in display order.
 * Merges projection domains with scaffolding domains.
 * Scaffolding domains appear if not in projection.
 */
export function getDomains(): Domain[] {
  const projection = cachedProjection;
  const projectionDomains = projection ? [...projection.domains] : [];

  // Get all scaffolding domains not in projection
  // NOTE: Case-insensitive comparison - projection uses UPPERCASE, scaffolding uses Title Case
  const scaffoldingDomains = getAllScaffoldingDomains()
    .filter(s => !projectionDomains.some(p => p.domain.toUpperCase() === s.id.toUpperCase()))
    .map(scaffoldingToDomain);

  // Merge and sort by order
  return [...projectionDomains, ...scaffoldingDomains].sort((a, b) => a.order - b.order);
}

/**
 * Get a single domain by name.
 * Falls back to scaffolding if not in projection.
 */
export function getDomain(name: DomainName): Domain | undefined {
  // Try projection first
  if (cachedProjection) {
    const projDomain = cachedProjection.domains.find((d) => d.domain === name);
    if (projDomain) return projDomain;
  }

  // Fallback to scaffolding
  const scaffolding = getScaffoldingDomain(name);
  if (scaffolding) {
    return scaffoldingToDomain(scaffolding);
  }

  return undefined;
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
// HIL v1: Panel Classification Accessors
// ============================================================================

/**
 * Get execution panels for a domain (raw data, lists, details).
 * These are panels with panel_class="execution" (default).
 */
export function getExecutionPanels(domain: DomainName): Panel[] {
  return getEnabledPanels(domain).filter(
    (p) => (p.panel_class || "execution") === "execution"
  );
}

/**
 * Get interpretation panels for a domain (summaries, aggregations).
 * These are panels with panel_class="interpretation".
 */
export function getInterpretationPanels(domain: DomainName): Panel[] {
  return getEnabledPanels(domain).filter(
    (p) => p.panel_class === "interpretation"
  );
}

/**
 * Get panels grouped by class for a domain.
 * Returns { interpretation: Panel[], execution: Panel[] }
 */
export function getPanelsByClass(domain: DomainName): {
  interpretation: Panel[];
  execution: Panel[];
} {
  const panels = getEnabledPanels(domain);
  return {
    interpretation: panels.filter((p) => p.panel_class === "interpretation"),
    execution: panels.filter((p) => (p.panel_class || "execution") === "execution"),
  };
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

  // Accept LOCKED and Phase-2A stages (affordance surfacing, simulation)
  const validStages = ["LOCKED", "PHASE_2A1_APPLIED", "PHASE_2A2_SIMULATED"];
  if (!validStages.includes(meta.processing_stage)) {
    throw new Error(
      `Invalid projection: expected stage in [${validStages.join(", ")}], got '${meta.processing_stage}'`
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
 * Falls back to scaffolding if projection doesn't have the domain or subdomains.
 */
export function getSubdomainsForDomain(domainName: DomainName): string[] {
  // Try projection first
  if (projectionHasDomain(domainName)) {
    const domain = cachedProjection!.domains.find((d) => d.domain === domainName);
    if (domain && domain.panels.length > 0) {
      const subdomains = new Set<string>();
      for (const panel of domain.panels) {
        if (panel.subdomain) {
          subdomains.add(panel.subdomain);
        }
      }
      if (subdomains.size > 0) {
        return Array.from(subdomains);
      }
    }
  }

  // Fallback to scaffolding
  return getScaffoldingSubdomains(domainName);
}

/**
 * Get all topics for a subdomain within a domain.
 * Uses scaffolding as the source (topics are structural, not data).
 */
export function getTopicsForSubdomain(
  domainName: DomainName,
  subdomain: string
): ScaffoldingTopic[] {
  return getScaffoldingTopics(domainName, subdomain);
}

/**
 * Check if a domain has scaffolding (exists in ui_plan).
 */
export function domainHasScaffolding(domainName: DomainName): boolean {
  return hasScaffoldingDomain(domainName);
}

/**
 * Check if domain is from projection (has actual panels) or scaffolding only.
 */
export function isDomainFromProjection(domainName: DomainName): boolean {
  return projectionHasDomain(domainName);
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
// Panel/Domain Accessors (No Placeholder Generation - PIN-415)
// ============================================================================
// DELETED: generatePlaceholderDescription() - violated truth-grade principles
// DELETED: normalizePanel() with fake descriptions - simulation removed
// DELETED: normalizeDomain() with fake descriptions - simulation removed
//
// If short_description is missing in projection, it is MISSING.
// The UI must show the truth, not fabricate descriptions.
// Reference: PIN-415 (Hard Delete Order)
// ============================================================================

// Type aliases for backward compatibility (no transformation)
export type NormalizedPanel = Panel;
export type NormalizedDomain = Domain;

/**
 * Get panel as-is. No description injection.
 * If short_description is missing, it remains missing.
 */
export function normalizePanel(panel: Panel): Panel {
  // NO FAKE DATA - return panel unchanged
  return panel;
}

/**
 * Get domain as-is. No description injection.
 * If short_description is missing, it remains missing.
 */
export function normalizeDomain(domain: Domain): Domain {
  // NO FAKE DATA - return domain unchanged
  return domain;
}

/**
 * Get panels for a subdomain as-is.
 */
export function getNormalizedPanelsForSubdomain(
  domainName: DomainName,
  subdomain: string
): Panel[] {
  return getPanelsForSubdomain(domainName, subdomain);
}

/**
 * Get domain as-is.
 */
export function getNormalizedDomain(name: DomainName): Domain | undefined {
  return getDomain(name);
}

// ============================================================================
// Exports
// ============================================================================

export type {
  UIProjectionLock,
  Domain,
  Panel,
  Control,
  BindingStatus,
  // HIL v1 types
  PanelClass,
  AggregationType,
  Provenance,
} from "./ui_projection_types";

// Re-export scaffolding types for DomainPage topic rendering
export type { ScaffoldingTopic, ScaffoldingDomain } from "./ui_plan_scaffolding";
