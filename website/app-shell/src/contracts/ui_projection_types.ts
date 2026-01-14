/**
 * UI Projection Lock Types
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: build-time (type generation)
 *   Execution: static
 * Role: TypeScript types for ui_projection_lock.json consumption
 * Reference: L2.1 UI Projection Pipeline
 *
 * GOVERNANCE RULES:
 * - Renderer must consume ONLY this file's types
 * - No hardcoded domain/panel/control names allowed
 * - All fields are required (no optionals)
 * - Types generated from JSON schema, not invented
 */

// ============================================================================
// Control Types
// ============================================================================

export type ControlType =
  | "FILTER"
  | "SORT"
  | "SELECT_SINGLE"
  | "SELECT_MULTI"
  | "NAVIGATE"
  | "BULK_SELECT"
  | "DETAIL_VIEW"
  | "ACTION"
  | "DOWNLOAD"
  | "EXPAND"
  | "REFRESH"
  | "SEARCH"
  | "PAGINATION"
  | "TOGGLE"
  | "EDIT"
  | "DELETE"
  | "CREATE"
  | "APPROVE"
  | "REJECT"
  | "ARCHIVE"
  | "EXPORT"
  | "IMPORT"
  | "ACKNOWLEDGE"
  | "RESOLVE";

export type ControlCategory =
  | "data_control"
  | "selection"
  | "navigation"
  | "action"
  | "unknown";

// ============================================================================
// Binding Status (AURORA_L2 Authority Gate)
// ============================================================================
// LOCKED: This type defines the sole authority for enabling UI controls.
// See PIN-386: SDSR → AURORA_L2 Observation Schema Contract
//
// | Status | Meaning                          | UI Behavior              |
// |--------|----------------------------------|--------------------------|
// | INFO   | Display only (no actions)        | No controls rendered     |
// | DRAFT  | Actions exist but unverified     | Controls DISABLED        |
// | BOUND  | SDSR verified (OBSERVED/TRUSTED) | Controls ENABLED         |
// | UNBOUND| Capability deprecated/missing    | Panel hidden             |
// ============================================================================

export type BindingStatus = "INFO" | "DRAFT" | "BOUND" | "UNBOUND";

// ============================================================================
// HIL v1 Types (Human Interpretation Layer)
// ============================================================================
// LOCKED: This defines panel classification and provenance for interpretation.
// See PIN-416, PIN-417: HIL v1 Schema Extension
//
// | Class          | Meaning                          | Provenance Required |
// |----------------|----------------------------------|---------------------|
// | execution      | Raw data, lists, details         | NO                  |
// | interpretation | Summaries, aggregations          | YES                 |
// ============================================================================

export type PanelClass = "execution" | "interpretation";

export type AggregationType =
  | "COUNT"
  | "SUM"
  | "TREND"
  | "STATUS_BREAKDOWN"
  | "TOP_N"
  | "LATEST";

/**
 * Provenance declaration for interpretation panels.
 * Required when panel_class is "interpretation".
 * Defines where the aggregated data derives from.
 */
export interface Provenance {
  source_panels: string[];       // Panel IDs this interpretation derives from
  aggregation: AggregationType;  // How source data is aggregated
  endpoint: string;              // Backend endpoint for aggregated data
}

export interface Control {
  type: ControlType;
  order: number;
  icon: string;
  category: ControlCategory;
  enabled: boolean;
  visibility: Visibility;
}

// ============================================================================
// Panel Types
// ============================================================================

export type RenderMode = "FLAT" | "TREE" | "GRID" | "TABLE" | "CARD" | "LIST";

export type Visibility = "ALWAYS" | "CONDITIONAL" | "HIDDEN" | "ROLE_BASED";

export interface PanelPermissions {
  nav_required: boolean;
  filtering: boolean;
  read: boolean;
  write: boolean;
  activate: boolean;
}

export type ViewType = "DOMAIN_HOME" | "PANEL_VIEW";

// ============================================================================
// Content Block Types (Phase 3 - PIN-387)
// ============================================================================

export type ContentBlockType = "HEADER" | "DATA" | "CONTROLS" | "FOOTER";

export interface ContentBlock {
  type: ContentBlockType;
  order: number;
  visibility: Visibility;
  enabled: boolean;
  components: string[];
  render_mode?: RenderMode;  // Only on DATA blocks
}

// ============================================================================
// Binding Metadata (Phase 4 - SDSR Trace Finalization)
// ============================================================================

export interface ObservedEffect {
  entity: string;
  field: string;
  from: string;
  to: string;
}

export interface BindingMetadata {
  scenario_ids: string[];           // SDSR scenarios that observed capabilities
  observed_at: string | null;       // ISO timestamp of latest observation
  capability_ids: string[];         // List of capability IDs that were observed
  trace_count: number;              // Number of observation traces
  observed_effects: ObservedEffect[]; // State changes observed by SDSR
}

export interface Panel {
  panel_id: string;
  panel_name: string;
  order: string;
  render_mode: RenderMode;
  visibility: Visibility;
  enabled: boolean;
  disabled_reason: string | null;
  controls: Control[];
  control_count: number;
  // Topic metadata for traceability
  topic: string | null;
  topic_id: string | null;
  subdomain: string | null;
  // Topic display order (LOCKED - ordering governance)
  // UI sorts topics by this value, NOT alphabetically.
  // If absent, defaults to 0 (first). Lower values appear first.
  topic_display_order: number;
  // Panel display order (Phase 2 - PIN-387)
  // Global sequential ordering across all domains (0 to N-1)
  panel_display_order: number;
  // Content blocks (Phase 3 - PIN-387)
  // Defines in-panel layout structure: HEADER, DATA, CONTROLS, FOOTER
  content_blocks: ContentBlock[];
  // Short description for customer-facing display (Group D)
  short_description: string | null;
  // Permissions
  permissions: PanelPermissions;
  // Navigation (Phase 1.1 - projection-driven routing)
  route: string;
  view_type: ViewType;
  // AURORA_L2 Binding Authority (LOCKED - PIN-386)
  // This field is the SOLE authority for enabling/disabling controls.
  // BOUND = controls enabled, DRAFT = controls disabled, INFO = no controls
  binding_status: BindingStatus;
  // Review status from intent pipeline
  review_status: string;
  // SDSR observation metadata (Phase 4 - populated when binding_status = BOUND)
  // Makes truth inspectable: which SDSR scenario verified this panel's capabilities
  binding_metadata?: BindingMetadata;
  // HIL v1: Panel classification (default: "execution")
  // "execution" = raw data panels, "interpretation" = summary/aggregation panels
  panel_class: PanelClass;
  // HIL v1: Provenance (only present on interpretation panels)
  // Declares what execution panels this interpretation derives from
  provenance?: Provenance;
}

// ============================================================================
// Domain Types
// ============================================================================

export type DomainName =
  | "Overview"
  | "Activity"
  | "Incidents"
  | "Policies"
  | "Logs"
  | "Account"
  | "Connectivity";

export interface Domain {
  domain: DomainName;
  order: number;
  panels: Panel[];
  panel_count: number;
  total_controls: number;
  // Short description for customer-facing display (Group D)
  short_description: string | null;
  // Navigation (Phase 1.1 - projection-driven routing)
  route: string;
}

// ============================================================================
// Projection Lock Types
// ============================================================================

export interface ProjectionMeta {
  type: "ui_projection_lock";
  version: string;
  generated_at: string;
  source: string;
  // Phase 0-1 additions (PIN-387)
  generator: string;
  generator_version: string;
  db_authority: "neon" | "local";
  source_of_truth: string;
  contract_version: string;
  processing_stage: "LOCKED" | "PHASE_2A1_APPLIED" | "PHASE_2A2_SIMULATED";
  frozen: true;
  editable: false;
  // Environment metadata (for promotion pipeline - PIN-388)
  environment: "preflight" | "production";
  approval_status: "EXPERIMENTAL" | "APPROVED";
  sdsr_verified: boolean;
  routes_relative: boolean;  // Routes are relative, resolved by frontend
}

export interface ProjectionStatistics {
  domain_count: number;
  panel_count: number;
  control_count: number;
  // Binding status counts
  bound_panels: number;
  draft_panels: number;
  info_panels: number;
  unbound_panels: number;
  // SDSR trace statistics (Phase 4 - PIN-387)
  sdsr_trace_count: number;
  panels_with_traces: number;
  unique_scenario_count: number;
  // HIL v1 statistics (PIN-416, PIN-417)
  execution_panels: number;
  interpretation_panels: number;
}

export interface ProjectionContract {
  renderer_must_consume_only_this_file: true;
  no_optional_fields: true;
  explicit_ordering_everywhere: true;
  all_controls_have_type: true;
  all_panels_have_render_mode: true;
  all_items_have_visibility: true;
  // Phase 1 additions
  binding_status_required: true;
  ordering_semantic: "numeric_only";
  // Phase 2 additions (PIN-387)
  panel_display_order_required: true;
  topic_display_order_required: true;
  // Phase 3 additions (PIN-387)
  content_blocks_required: true;
  // Phase 4 additions (PIN-387)
  binding_metadata_on_bound_panels: true;
  sdsr_trace_provenance: true;
  ui_must_not_infer: true;
  // HIL v1 additions (PIN-416, PIN-417)
  panel_class_required: true;
  provenance_on_interpretation_panels: true;
}

export interface UIProjectionLock {
  _meta: ProjectionMeta;
  _statistics: ProjectionStatistics;
  _contract: ProjectionContract;
  domains: Domain[];
}

// ============================================================================
// Type Guards
// ============================================================================

export function isValidControlType(type: string): type is ControlType {
  const validTypes: ControlType[] = [
    "FILTER",
    "SORT",
    "SELECT_SINGLE",
    "SELECT_MULTI",
    "NAVIGATE",
    "BULK_SELECT",
    "DETAIL_VIEW",
    "ACTION",
    "DOWNLOAD",
    "EXPAND",
    "REFRESH",
    "SEARCH",
    "PAGINATION",
    "TOGGLE",
    "EDIT",
    "DELETE",
    "CREATE",
    "APPROVE",
    "REJECT",
    "ARCHIVE",
    "EXPORT",
    "IMPORT",
    "ACKNOWLEDGE",
    "RESOLVE",
  ];
  return validTypes.includes(type as ControlType);
}

export function isValidRenderMode(mode: string): mode is RenderMode {
  const validModes: RenderMode[] = [
    "FLAT",
    "TREE",
    "GRID",
    "TABLE",
    "CARD",
    "LIST",
  ];
  return validModes.includes(mode as RenderMode);
}

export function isValidVisibility(vis: string): vis is Visibility {
  const validVisibilities: Visibility[] = [
    "ALWAYS",
    "CONDITIONAL",
    "HIDDEN",
    "ROLE_BASED",
  ];
  return validVisibilities.includes(vis as Visibility);
}

export function isValidDomain(domain: string): domain is DomainName {
  const validDomains: DomainName[] = [
    "Overview",
    "Activity",
    "Incidents",
    "Policies",
    "Logs",
    "Account",
    "Connectivity",
  ];
  return validDomains.includes(domain as DomainName);
}
