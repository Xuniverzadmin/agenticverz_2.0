/**
 * UC UAT Client — Data Access for UAT Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Load UC operation manifest and scenario execution results
 * Reference: UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15
 * artifact_class: CODE
 *
 * Loads the manifest JSON (static artifact) and provides typed access
 * to UC mapping decisions, scenario results, and evidence data.
 */

// ============================================================================
// Types
// ============================================================================

export type DecisionType = 'ASSIGN' | 'SPLIT' | 'HOLD';
export type HoldStatus = 'EVIDENCE_PENDING' | 'NON_UC_SUPPORT' | 'REFACTOR_REQUIRED';
export type ScenarioStatus = 'PASS' | 'FAIL' | 'NOT_RUN';

export interface ManifestEntry {
  uc_id: string;
  operation_name: string;
  route_path: string;
  handler_file: string;
  engine_or_driver_files: string[];
  test_refs: string[];
  decision_type: DecisionType;
  hold_status?: HoldStatus;
}

export interface ScenarioResult {
  uc_id: string;
  test_id: string;
  test_name: string;
  status: ScenarioStatus;
  evidence: string;
  timestamp: string;
}

export interface UatState {
  manifest: ManifestEntry[];
  scenarios: ScenarioResult[];
  loading: boolean;
  error: string | null;
  filter: DecisionType | 'FAILED_LAST_RUN' | 'ALL';
}

// ============================================================================
// Manifest Loader (static JSON artifact)
// ============================================================================

const MANIFEST_PATH = '/api/v1/uat/manifest';
const SCENARIOS_PATH = '/api/v1/uat/scenarios';

/**
 * Load the UC operation manifest.
 * Falls back to embedded empty array if backend endpoint is unavailable.
 */
export async function fetchManifest(): Promise<ManifestEntry[]> {
  try {
    const res = await fetch(MANIFEST_PATH);
    if (!res.ok) {
      console.warn(`UAT manifest endpoint returned ${res.status}, using empty manifest`);
      return [];
    }
    return await res.json();
  } catch {
    console.warn('UAT manifest endpoint unavailable, using empty manifest');
    return [];
  }
}

/**
 * Load scenario execution results.
 * Returns empty array if endpoint is unavailable (scenarios run on-demand).
 */
export async function fetchScenarios(): Promise<ScenarioResult[]> {
  try {
    const res = await fetch(SCENARIOS_PATH);
    if (!res.ok) {
      return [];
    }
    return await res.json();
  } catch {
    return [];
  }
}

// ============================================================================
// Filters
// ============================================================================

export function filterEntries(
  entries: ManifestEntry[],
  scenarios: ScenarioResult[],
  filter: UatState['filter'],
): ManifestEntry[] {
  switch (filter) {
    case 'ASSIGN':
    case 'SPLIT':
    case 'HOLD':
      return entries.filter((e) => e.decision_type === filter);
    case 'FAILED_LAST_RUN': {
      const failedUcs = new Set(
        scenarios.filter((s) => s.status === 'FAIL').map((s) => s.uc_id),
      );
      return entries.filter((e) => failedUcs.has(e.uc_id));
    }
    case 'ALL':
    default:
      return entries;
  }
}

// ============================================================================
// Statistics
// ============================================================================

export interface UatStats {
  total: number;
  assign: number;
  split: number;
  hold: number;
  scenariosRun: number;
  scenariosPassed: number;
  scenariosFailed: number;
}

export function computeStats(
  entries: ManifestEntry[],
  scenarios: ScenarioResult[],
): UatStats {
  return {
    total: entries.length,
    assign: entries.filter((e) => e.decision_type === 'ASSIGN').length,
    split: entries.filter((e) => e.decision_type === 'SPLIT').length,
    hold: entries.filter((e) => e.decision_type === 'HOLD').length,
    scenariosRun: scenarios.length,
    scenariosPassed: scenarios.filter((s) => s.status === 'PASS').length,
    scenariosFailed: scenarios.filter((s) => s.status === 'FAIL').length,
  };
}
