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
  // Permissions
  permissions: PanelPermissions;
}

// ============================================================================
// Domain Types
// ============================================================================

export type DomainName =
  | "Overview"
  | "Activity"
  | "Incidents"
  | "Policies"
  | "Logs";

export interface Domain {
  domain: DomainName;
  order: number;
  panels: Panel[];
  panel_count: number;
  total_controls: number;
}

// ============================================================================
// Projection Lock Types
// ============================================================================

export interface ProjectionMeta {
  type: "ui_projection_lock";
  version: string;
  generated_at: string;
  source: string;
  processing_stage: "LOCKED";
  frozen: true;
  editable: false;
}

export interface ProjectionStatistics {
  domain_count: number;
  panel_count: number;
  control_count: number;
}

export interface ProjectionContract {
  renderer_must_consume_only_this_file: true;
  no_optional_fields: true;
  explicit_ordering_everywhere: true;
  all_controls_have_type: true;
  all_panels_have_render_mode: true;
  all_items_have_visibility: true;
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
  ];
  return validDomains.includes(domain as DomainName);
}
