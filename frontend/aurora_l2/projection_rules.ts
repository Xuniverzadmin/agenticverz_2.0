/**
 * AURORA_L2 Projection Rules
 *
 * These rules are the "shock absorber" layer that applies compensating logic
 * to UNREVIEWED intents without modifying the source YAMLs.
 *
 * Reference: design/l2_1/AURORA_L2.md
 *
 * Key Constraints:
 * - All rules must be deterministic
 * - All rules must be reversible (reviewed intents can override)
 * - All rules must be overridable
 * - NO inferred semantics written back to intent YAMLs
 */

// =============================================================================
// Types
// =============================================================================

export interface CompiledIntent {
  panel_id: string;
  domain: string;
  subdomain: string;
  topic: string;
  topic_id: string;
  order_level: number;
  action_layer: string;
  panel_name: string;
  ranking_dimension: string | null;
  visible_by_default: boolean;
  nav_required: boolean;
  expansion_mode: "INLINE" | "COLLAPSIBLE" | "CONTEXTUAL" | "OVERLAY" | "NAVIGATE";
  read_enabled: boolean;
  download_enabled: boolean;
  write_enabled: boolean;
  write_action: string | null;
  replay_enabled: boolean;
  filtering_enabled: boolean;
  selection_mode: "SINGLE" | "MULTI" | null;
  activate_enabled: boolean;
  activate_actions: string[];
  confirmation_required: boolean;
  control_set: string[];
  notes: string | null;
  review_status: "UNREVIEWED" | "REVIEWED" | "APPROVED" | "DEPRECATED";
  migrated_from: string;
  migration_date: string;
  compiled_at: string;
  // Binding status from capability registry
  binding_status: "INFO" | "DRAFT" | "BOUND" | "UNBOUND";
}

export interface ProjectedPanel {
  panel_id: string;
  domain: string;
  subdomain: string;
  topic: string;
  order_level: number;
  panel_name: string;

  // Computed projection properties
  visible: boolean;
  expansion_mode: string;
  primary_action: string | null;
  secondary_actions: string[];
  controls: ProjectedControl[];
  warnings: string[];
  is_unreviewed: boolean;
  binding_status: "INFO" | "DRAFT" | "BOUND" | "UNBOUND";
}

export interface ProjectedControl {
  type: string;
  enabled: boolean;
  bound: boolean; // Whether backend binding exists
  label: string;
  affordance: "primary" | "secondary" | "disabled" | "hidden";
}

// =============================================================================
// Default Projection Rules for UNREVIEWED Intents
// =============================================================================

/**
 * Known bound controls (controls with working backend implementations)
 * Controls not in this list are marked as "unbound" and downgraded
 */
const KNOWN_BOUND_CONTROLS: Set<string> = new Set([
  "FILTER",
  "SORT",
  "SELECT_SINGLE",
  "SELECT_MULTI",
  "DOWNLOAD",
  "NAVIGATE",
  "APPROVE",
  "REJECT",
]);

/**
 * Controls that require binding verification before enabling
 * These are ACTION controls that may not have backend implementations
 */
const ACTION_CONTROLS_REQUIRING_VERIFICATION: Set<string> = new Set([
  "ACKNOWLEDGE",
  "RESOLVE",
  "ACTIVATE",
  "DEACTIVATE",
  "UPDATE_THRESHOLD",
  "UPDATE_LIMIT",
  "UPDATE_RULE",
  "ADD_NOTE",
]);

/**
 * Default expansion modes by order level
 * O1 (summary) = INLINE, O2 (list) = INLINE, O3+ = CONTEXTUAL
 */
function getDefaultExpansionMode(orderLevel: number): string {
  if (orderLevel <= 2) return "INLINE";
  if (orderLevel === 3) return "CONTEXTUAL";
  if (orderLevel === 4) return "OVERLAY";
  return "NAVIGATE"; // O5 (proof) always navigates
}

/**
 * Determine control affordance based on binding status and review status
 *
 * 4-State Capability Lifecycle (CAPABILITY_STATUS_MODEL.yaml v2.0):
 *   DISCOVERED → DECLARED → OBSERVED → TRUSTED
 *
 * Binding status mapping:
 * - INFO:   No actions, just display (no controls)
 * - DRAFT:  DISCOVERED or DECLARED → disabled but visible (claim ≠ truth)
 * - BOUND:  OBSERVED or TRUSTED → enabled (system verified)
 * - UNBOUND: Missing/deprecated capabilities → hidden
 *
 * Core Invariant: Capabilities are not real because backend says so.
 *                 They are real only when the system demonstrates them.
 */
function getControlAffordance(
  control: string,
  isUnreviewed: boolean,
  bindingStatus: "INFO" | "DRAFT" | "BOUND" | "UNBOUND"
): "primary" | "secondary" | "disabled" | "hidden" {
  // UNBOUND panels hide action controls
  if (bindingStatus === "UNBOUND") {
    // Still show non-action controls
    if (!ACTION_CONTROLS_REQUIRING_VERIFICATION.has(control)) {
      return KNOWN_BOUND_CONTROLS.has(control) ? "secondary" : "hidden";
    }
    return "hidden";
  }

  // DRAFT panels disable action controls but keep them visible
  if (bindingStatus === "DRAFT") {
    if (ACTION_CONTROLS_REQUIRING_VERIFICATION.has(control)) {
      return "disabled"; // Show but disable with "Backend not verified" tooltip
    }
    // Non-action controls still work
    if (KNOWN_BOUND_CONTROLS.has(control)) {
      if (control === "APPROVE" || control === "REJECT") {
        return "disabled"; // Primary actions also disabled in DRAFT
      }
      return "secondary";
    }
  }

  // BOUND panels have full functionality
  if (bindingStatus === "BOUND") {
    if (control === "APPROVE" || control === "REJECT") {
      return "primary";
    }
    if (KNOWN_BOUND_CONTROLS.has(control) || ACTION_CONTROLS_REQUIRING_VERIFICATION.has(control)) {
      return "secondary";
    }
  }

  // Known bound controls get full treatment (for INFO panels)
  if (KNOWN_BOUND_CONTROLS.has(control)) {
    if (control === "APPROVE" || control === "REJECT") {
      return "primary";
    }
    return "secondary";
  }

  // Unverified action controls on UNREVIEWED intents (fallback)
  if (ACTION_CONTROLS_REQUIRING_VERIFICATION.has(control)) {
    if (isUnreviewed) {
      return "disabled"; // Show but disable
    }
    return "secondary"; // Reviewed intents can enable
  }

  // Unknown controls are hidden
  return "hidden";
}

/**
 * Apply projection rules to a single compiled intent
 */
export function projectIntent(intent: CompiledIntent): ProjectedPanel {
  const isUnreviewed = intent.review_status === "UNREVIEWED";
  const bindingStatus = intent.binding_status || "INFO";
  const warnings: string[] = [];

  // Add binding status warning for DRAFT panels
  // 4-State Model: DRAFT = DISCOVERED or DECLARED (not yet system-verified)
  if (bindingStatus === "DRAFT") {
    warnings.push("Awaiting system verification (DISCOVERED/DECLARED)");
  } else if (bindingStatus === "UNBOUND") {
    warnings.push("Backend binding missing or deprecated");
  }

  // Collect controls with binding status
  const controls: ProjectedControl[] = intent.control_set.map((ctrl) => {
    const bound = KNOWN_BOUND_CONTROLS.has(ctrl) || bindingStatus === "BOUND";
    const affordance = getControlAffordance(ctrl, isUnreviewed, bindingStatus);

    if (!bound && isUnreviewed) {
      warnings.push(`Control '${ctrl}' may not be wired (UNREVIEWED)`);
    }

    return {
      type: ctrl,
      enabled: affordance !== "disabled" && affordance !== "hidden",
      bound,
      label: ctrl.replace(/_/g, " "),
      affordance,
    };
  });

  // Determine primary action (if any)
  let primaryAction: string | null = null;
  const secondaryActions: string[] = [];

  for (const ctrl of controls) {
    if (ctrl.affordance === "primary" && !primaryAction) {
      primaryAction = ctrl.type;
    } else if (ctrl.affordance === "secondary" || ctrl.affordance === "primary") {
      secondaryActions.push(ctrl.type);
    }
  }

  // Apply expansion mode override for UNREVIEWED
  let expansionMode = intent.expansion_mode;
  if (isUnreviewed) {
    const defaultMode = getDefaultExpansionMode(intent.order_level);
    if (expansionMode !== defaultMode) {
      warnings.push(`Expansion mode normalized: ${expansionMode} → ${defaultMode}`);
      expansionMode = defaultMode;
    }
  }

  // Visibility rules
  let visible = intent.visible_by_default;
  if (intent.nav_required && intent.order_level > 2) {
    visible = false; // Deep panels require navigation
  }

  return {
    panel_id: intent.panel_id,
    domain: intent.domain,
    subdomain: intent.subdomain,
    topic: intent.topic,
    order_level: intent.order_level,
    panel_name: intent.panel_name,
    visible,
    expansion_mode: expansionMode,
    primary_action: primaryAction,
    secondary_actions: secondaryActions,
    controls,
    warnings,
    is_unreviewed: isUnreviewed,
    binding_status: bindingStatus,
  };
}

// =============================================================================
// Grouping Rules (Collapse Noisy Sections)
// =============================================================================

export interface ProjectedDomain {
  domain: string;
  subdomains: ProjectedSubdomain[];
  panel_count: number;
}

export interface ProjectedSubdomain {
  subdomain: string;
  topics: ProjectedTopic[];
  panel_count: number;
}

export interface ProjectedTopic {
  topic: string;
  topic_id: string;
  panels: ProjectedPanel[];
  collapsed: boolean; // Whether to show collapsed by default
}

/**
 * Group panels into domain → subdomain → topic hierarchy
 */
export function groupPanels(panels: ProjectedPanel[]): ProjectedDomain[] {
  const domainMap = new Map<string, Map<string, Map<string, ProjectedPanel[]>>>();

  for (const panel of panels) {
    if (!domainMap.has(panel.domain)) {
      domainMap.set(panel.domain, new Map());
    }
    const subdomainMap = domainMap.get(panel.domain)!;

    if (!subdomainMap.has(panel.subdomain)) {
      subdomainMap.set(panel.subdomain, new Map());
    }
    const topicMap = subdomainMap.get(panel.subdomain)!;

    if (!topicMap.has(panel.topic)) {
      topicMap.set(panel.topic, []);
    }
    topicMap.get(panel.topic)!.push(panel);
  }

  // Convert to structured output
  const result: ProjectedDomain[] = [];

  for (const [domain, subdomainMap] of domainMap) {
    const subdomains: ProjectedSubdomain[] = [];

    for (const [subdomain, topicMap] of subdomainMap) {
      const topics: ProjectedTopic[] = [];

      for (const [topic, topicPanels] of topicMap) {
        // Sort panels by order level
        topicPanels.sort((a, b) => a.order_level - b.order_level);

        // Collapse rule: topics with >3 panels collapse by default
        const collapsed = topicPanels.length > 3;

        topics.push({
          topic,
          topic_id: topicPanels[0]?.panel_id.replace(/-O\d$/, "") || "",
          panels: topicPanels,
          collapsed,
        });
      }

      subdomains.push({
        subdomain,
        topics,
        panel_count: topics.reduce((sum, t) => sum + t.panels.length, 0),
      });
    }

    result.push({
      domain,
      subdomains,
      panel_count: subdomains.reduce((sum, s) => sum + s.panel_count, 0),
    });
  }

  return result;
}

// =============================================================================
// Visual Hierarchy Heuristics
// =============================================================================

/**
 * Determine visual weight of a panel (for layout decisions)
 */
export function getPanelWeight(panel: ProjectedPanel): number {
  let weight = 0;

  // Higher order = less weight (detail views are secondary)
  weight += (5 - panel.order_level) * 10;

  // Panels with primary actions get more weight
  if (panel.primary_action) weight += 20;

  // Visible by default = more weight
  if (panel.visible) weight += 15;

  // UNREVIEWED panels get slightly less weight
  if (panel.is_unreviewed) weight -= 5;

  return weight;
}

/**
 * Sort panels within a topic by visual weight
 */
export function sortByWeight(panels: ProjectedPanel[]): ProjectedPanel[] {
  return [...panels].sort((a, b) => getPanelWeight(b) - getPanelWeight(a));
}
