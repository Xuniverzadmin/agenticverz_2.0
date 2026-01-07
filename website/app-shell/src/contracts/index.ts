/**
 * UI Contract Module
 *
 * This module is the ONLY way to access L2.1 UI projection data.
 *
 * GOVERNANCE RULES:
 * - Import from this module, not from JSON files directly
 * - Do not hardcode domain/panel/control names
 * - Use the typed accessors provided
 */

// Types
export type {
  UIProjectionLock,
  Domain,
  Panel,
  Control,
  ControlType,
  ControlCategory,
  RenderMode,
  Visibility,
  DomainName,
  PanelPermissions,
  ProjectionMeta,
  ProjectionStatistics,
  ProjectionContract,
} from "./ui_projection_types";

// Type guards
export {
  isValidControlType,
  isValidRenderMode,
  isValidVisibility,
  isValidDomain,
} from "./ui_projection_types";

// Loader functions
export {
  loadProjection,
  getProjection,
  getDomains,
  getDomain,
  getDomainNames,
  getPanels,
  getPanel,
  getEnabledPanels,
  getControls,
  getControlsByCategory,
  hasControl,
  getStatistics,
} from "./ui_projection_loader";
