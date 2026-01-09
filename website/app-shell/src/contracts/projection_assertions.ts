/**
 * Projection Assertions - Compiler Safety for UI Projection
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: build time / runtime
 *   Execution: sync
 * Role: Validate projection structure and routes at compile/runtime
 * Reference: PIN-358 Task Group H
 *
 * GROUP H: Compiler Safety
 * - Validates route patterns against allowed console prefixes
 * - Rejects malformed projections early
 * - Provides type guards for safe access
 */

import type {
  UIProjectionLock,
  Domain,
  Panel,
  DomainName,
  RenderMode,
  Visibility,
  ViewType,
} from './ui_projection_types';

// ============================================================================
// Constants
// ============================================================================

/**
 * Valid console route prefixes.
 * Routes MUST start with one of these prefixes.
 */
export const VALID_ROUTE_PREFIXES = ['/precus/', '/cus/'] as const;
export type RoutePrefix = (typeof VALID_ROUTE_PREFIXES)[number];

/**
 * Valid domain names (frozen per constitution).
 */
export const VALID_DOMAIN_NAMES: readonly DomainName[] = [
  'Overview',
  'Activity',
  'Incidents',
  'Policies',
  'Logs',
] as const;

/**
 * Valid render modes.
 */
export const VALID_RENDER_MODES: readonly RenderMode[] = [
  'FLAT',
  'TREE',
  'GRID',
  'TABLE',
  'CARD',
  'LIST',
] as const;

/**
 * Valid order levels.
 */
export const VALID_ORDER_LEVELS = ['O1', 'O2', 'O3', 'O4', 'O5'] as const;
export type OrderLevel = (typeof VALID_ORDER_LEVELS)[number];

// ============================================================================
// Route Assertions
// ============================================================================

/**
 * Assert that a route has a valid console prefix.
 * @throws Error if route doesn't start with valid prefix
 */
export function assertValidRoutePrefix(route: string): void {
  const hasValidPrefix = VALID_ROUTE_PREFIXES.some((prefix) =>
    route.startsWith(prefix)
  );

  if (!hasValidPrefix) {
    throw new Error(
      `PROJECTION_ASSERTION_FAILED: Invalid route prefix "${route}". ` +
        `Routes must start with one of: ${VALID_ROUTE_PREFIXES.join(', ')}`
    );
  }
}

/**
 * Check if a route has a valid console prefix.
 * Non-throwing version of assertValidRoutePrefix.
 */
export function isValidRoutePrefix(route: string): boolean {
  return VALID_ROUTE_PREFIXES.some((prefix) => route.startsWith(prefix));
}

/**
 * Assert that a route matches expected pattern: /{prefix}/{domain}/{panel-id}
 */
export function assertValidRoutePattern(route: string): void {
  assertValidRoutePrefix(route);

  const parts = route.split('/').filter(Boolean);

  if (parts.length < 2) {
    throw new Error(
      `PROJECTION_ASSERTION_FAILED: Route "${route}" must have at least 2 segments ` +
        `(console prefix + domain). Got ${parts.length} segments.`
    );
  }
}

// ============================================================================
// Domain Assertions
// ============================================================================

/**
 * Assert that a domain name is valid.
 * @throws Error if domain name is not in VALID_DOMAIN_NAMES
 */
export function assertValidDomainName(name: string): asserts name is DomainName {
  if (!VALID_DOMAIN_NAMES.includes(name as DomainName)) {
    throw new Error(
      `PROJECTION_ASSERTION_FAILED: Invalid domain name "${name}". ` +
        `Valid domains are: ${VALID_DOMAIN_NAMES.join(', ')}`
    );
  }
}

/**
 * Check if a domain name is valid.
 */
export function isValidDomainName(name: string): name is DomainName {
  return VALID_DOMAIN_NAMES.includes(name as DomainName);
}

// ============================================================================
// Panel Assertions
// ============================================================================

/**
 * Assert that a panel has all required fields.
 */
export function assertValidPanel(panel: unknown): asserts panel is Panel {
  if (!panel || typeof panel !== 'object') {
    throw new Error('PROJECTION_ASSERTION_FAILED: Panel must be an object');
  }

  const p = panel as Record<string, unknown>;

  const requiredFields = [
    'panel_id',
    'panel_name',
    'order',
    'render_mode',
    'visibility',
    'enabled',
    'controls',
    'control_count',
    'permissions',
    'route',
    'view_type',
  ];

  for (const field of requiredFields) {
    if (!(field in p)) {
      throw new Error(
        `PROJECTION_ASSERTION_FAILED: Panel missing required field "${field}"`
      );
    }
  }

  // Validate specific field values
  if (typeof p.panel_id !== 'string' || p.panel_id.length === 0) {
    throw new Error(
      'PROJECTION_ASSERTION_FAILED: Panel panel_id must be a non-empty string'
    );
  }

  if (typeof p.route !== 'string') {
    throw new Error('PROJECTION_ASSERTION_FAILED: Panel route must be a string');
  }

  assertValidRoutePrefix(p.route as string);

  if (!VALID_RENDER_MODES.includes(p.render_mode as RenderMode)) {
    throw new Error(
      `PROJECTION_ASSERTION_FAILED: Invalid render_mode "${p.render_mode}". ` +
        `Valid modes are: ${VALID_RENDER_MODES.join(', ')}`
    );
  }
}

/**
 * Assert that a panel order is valid.
 */
export function assertValidOrder(order: string): asserts order is OrderLevel {
  if (!VALID_ORDER_LEVELS.includes(order as OrderLevel)) {
    throw new Error(
      `PROJECTION_ASSERTION_FAILED: Invalid order "${order}". ` +
        `Valid orders are: ${VALID_ORDER_LEVELS.join(', ')}`
    );
  }
}

/**
 * Check if an order is valid.
 */
export function isValidOrder(order: string): order is OrderLevel {
  return VALID_ORDER_LEVELS.includes(order as OrderLevel);
}

// ============================================================================
// Projection Assertions
// ============================================================================

/**
 * Validate entire projection structure.
 * @throws Error if projection is malformed
 */
export function assertValidProjection(projection: unknown): asserts projection is UIProjectionLock {
  if (!projection || typeof projection !== 'object') {
    throw new Error('PROJECTION_ASSERTION_FAILED: Projection must be an object');
  }

  const p = projection as Record<string, unknown>;

  // Check version (in _meta.version per L2.1 schema)
  const meta = p._meta as Record<string, unknown> | undefined;
  if (!meta || typeof meta.version !== 'string') {
    throw new Error('PROJECTION_ASSERTION_FAILED: Projection must have _meta.version string');
  }

  // Check domains array
  if (!Array.isArray(p.domains)) {
    throw new Error('PROJECTION_ASSERTION_FAILED: Projection must have domains array');
  }

  if (p.domains.length === 0) {
    throw new Error('PROJECTION_ASSERTION_FAILED: Projection domains array cannot be empty');
  }

  // Validate each domain
  for (const domain of p.domains) {
    assertValidDomain(domain);
  }
}

/**
 * Validate domain structure.
 */
export function assertValidDomain(domain: unknown): asserts domain is Domain {
  if (!domain || typeof domain !== 'object') {
    throw new Error('PROJECTION_ASSERTION_FAILED: Domain must be an object');
  }

  const d = domain as Record<string, unknown>;

  // Check required fields
  if (typeof d.domain !== 'string') {
    throw new Error('PROJECTION_ASSERTION_FAILED: Domain must have domain name');
  }

  assertValidDomainName(d.domain);

  if (typeof d.route !== 'string') {
    throw new Error('PROJECTION_ASSERTION_FAILED: Domain must have route');
  }

  assertValidRoutePrefix(d.route);

  if (!Array.isArray(d.panels)) {
    throw new Error('PROJECTION_ASSERTION_FAILED: Domain must have panels array');
  }

  // Validate each panel
  for (const panel of d.panels) {
    assertValidPanel(panel);
  }
}

// ============================================================================
// Validation Summary
// ============================================================================

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  panelCount: number;
  domainCount: number;
}

/**
 * Validate projection and return detailed results without throwing.
 */
export function validateProjection(projection: unknown): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    errors: [],
    warnings: [],
    panelCount: 0,
    domainCount: 0,
  };

  try {
    assertValidProjection(projection);
    const p = projection as UIProjectionLock;
    result.domainCount = p.domains.length;
    result.panelCount = p.domains.reduce((sum, d) => sum + d.panels.length, 0);
  } catch (err) {
    result.valid = false;
    result.errors.push(err instanceof Error ? err.message : String(err));
  }

  return result;
}

// ============================================================================
// Exports
// ============================================================================

export type { OrderLevel };
