/**
 * AURORA_L2 Projection Builder
 *
 * This is the "shock absorber" layer that transforms compiled intents
 * into UI-ready projections.
 *
 * Reference: design/l2_1/AURORA_L2.md
 *
 * Architecture:
 *   SQL Intent Store (backend) → API fetch → projection_builder → React Context → PanelContentRegistry
 *
 * Key Constraints:
 * - All compensating logic happens HERE, not in intent YAMLs
 * - UNREVIEWED intents are normalized in projection only
 * - Projection rules are deterministic and reversible
 * - No inferred semantics written back to source
 */

import {
  CompiledIntent,
  ProjectedPanel,
  ProjectedDomain,
  projectIntent,
  groupPanels,
  sortByWeight,
} from "./projection_rules";

// =============================================================================
// Types
// =============================================================================

export interface UIProjection {
  version: string;
  generated_at: string;
  domains: ProjectedDomain[];
  panel_count: number;
  unreviewed_count: number;
  warnings: string[];
  metadata: {
    source: "AURORA_L2";
    rules_version: string;
    backward_compatible: boolean;
  };
}

// =============================================================================
// Projection Builder
// =============================================================================

/**
 * Build UI projection from compiled intents
 *
 * This is the main entry point for transforming intent data into UI structure.
 */
export function buildProjection(intents: CompiledIntent[]): UIProjection {
  const generated_at = new Date().toISOString();
  const allWarnings: string[] = [];

  // Step 1: Project each intent
  const projectedPanels: ProjectedPanel[] = intents.map((intent) => {
    const projected = projectIntent(intent);

    // Collect warnings
    allWarnings.push(...projected.warnings.map((w) => `${intent.panel_id}: ${w}`));

    return projected;
  });

  // Step 2: Group into hierarchy
  const domains = groupPanels(projectedPanels);

  // Step 3: Sort panels within each topic by weight
  for (const domain of domains) {
    for (const subdomain of domain.subdomains) {
      for (const topic of subdomain.topics) {
        topic.panels = sortByWeight(topic.panels);
      }
    }
  }

  // Step 4: Count stats
  const unreviewed_count = projectedPanels.filter((p) => p.is_unreviewed).length;

  return {
    version: "1.0.0",
    generated_at,
    domains,
    panel_count: projectedPanels.length,
    unreviewed_count,
    warnings: allWarnings,
    metadata: {
      source: "AURORA_L2",
      rules_version: "1.0.0",
      backward_compatible: true, // Output matches legacy ui_projection_lock.json format
    },
  };
}

// =============================================================================
// Legacy Compatibility Layer
// =============================================================================

/**
 * Convert AURORA_L2 projection to legacy ui_projection_lock.json format
 *
 * This ensures backward compatibility with existing PanelContentRegistry.tsx
 */
export interface LegacyProjection {
  domains: LegacyDomain[];
  controls: LegacyControl[];
  metadata: {
    generated_by: string;
    generated_at: string;
  };
}

interface LegacyDomain {
  name: string;
  subdomains: LegacySubdomain[];
}

interface LegacySubdomain {
  name: string;
  topics: LegacyTopic[];
}

interface LegacyTopic {
  name: string;
  topic_id: string;
  panels: LegacyPanel[];
}

interface LegacyPanel {
  panel_id: string;
  panel_name: string;
  order: string; // "O1", "O2", etc.
  visible_by_default: boolean;
  controls: string[];
}

interface LegacyControl {
  panel_id: string;
  control_type: string;
  enabled: boolean;
}

export function toLegacyFormat(projection: UIProjection): LegacyProjection {
  const controls: LegacyControl[] = [];

  const domains: LegacyDomain[] = projection.domains.map((domain) => ({
    name: domain.domain,
    subdomains: domain.subdomains.map((subdomain) => ({
      name: subdomain.subdomain,
      topics: subdomain.topics.map((topic) => ({
        name: topic.topic,
        topic_id: topic.topic_id,
        panels: topic.panels.map((panel) => {
          // Collect controls for this panel
          for (const ctrl of panel.controls) {
            controls.push({
              panel_id: panel.panel_id,
              control_type: ctrl.type,
              enabled: ctrl.enabled,
            });
          }

          return {
            panel_id: panel.panel_id,
            panel_name: panel.panel_name,
            order: `O${panel.order_level}`,
            visible_by_default: panel.visible,
            controls: panel.controls.filter((c) => c.enabled).map((c) => c.type),
          };
        }),
      })),
    })),
  }));

  return {
    domains,
    controls,
    metadata: {
      generated_by: "AURORA_L2 Projection Builder",
      generated_at: projection.generated_at,
    },
  };
}

// =============================================================================
// API Integration (placeholder for future implementation)
// =============================================================================

/**
 * Fetch compiled intents from backend API
 *
 * TODO: Implement once /api/v1/aurora-l2/intents endpoint exists
 */
export async function fetchIntents(): Promise<CompiledIntent[]> {
  // Placeholder - will fetch from backend
  throw new Error("Not implemented: fetchIntents requires backend endpoint");
}

/**
 * Load intents from static JSON file (for development/migration)
 */
export async function loadIntentsFromFile(path: string): Promise<CompiledIntent[]> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load intents: ${response.statusText}`);
  }
  return response.json();
}

// =============================================================================
// Export
// =============================================================================

export {
  CompiledIntent,
  ProjectedPanel,
  ProjectedDomain,
  projectIntent,
  groupPanels,
} from "./projection_rules";
