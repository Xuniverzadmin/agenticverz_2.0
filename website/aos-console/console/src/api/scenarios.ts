/**
 * Scenarios API Client
 *
 * H2 Cost Simulation v1 - Scenario-based cost projections
 * Advisory only - no real budget changes
 *
 * Reference: Phase H2 - Cost Simulation v1
 */

import apiClient from './client';

// =============================================================================
// Types
// =============================================================================

export interface SimulationStepInput {
  skill: string;
  params?: Record<string, unknown>;
  iterations?: number;
}

export interface ScenarioCreate {
  name: string;
  description?: string;
  plan: SimulationStepInput[];
  budget_cents: number;
}

export interface Scenario {
  id: string;
  name: string;
  description?: string;
  plan: SimulationStepInput[];
  budget_cents: number;
  created_at: string;
  created_by: string;
  is_template: boolean;
}

export interface StepEstimate {
  step_index: number;
  skill_id: string;
  iterations: number;
  cost_cents: number;
  latency_ms: number;
  confidence: number;
}

export interface SimulationRisk {
  type: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
}

export interface SimulationResult {
  scenario_id?: string;
  scenario_name?: string;

  // Simulation results
  feasible: boolean;
  status: string;

  // Cost breakdown
  estimated_cost_cents: number;
  budget_cents: number;
  budget_remaining_cents: number;
  budget_utilization_pct: number;

  // Duration
  estimated_duration_ms: number;

  // Step breakdown
  step_estimates: StepEstimate[];

  // Quality
  confidence_score: number;

  // Warnings/risks
  warnings: string[];
  risks: SimulationRisk[];

  // Metadata
  simulation_timestamp: string;
  model_version: string;
  is_advisory: boolean;
  note: string;
}

export interface AdhocSimulationRequest {
  plan: SimulationStepInput[];
  budget_cents: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * List all available scenarios
 */
export async function listScenarios(includeTemplates = true): Promise<Scenario[]> {
  const response = await apiClient.get('/api/v1/scenarios', {
    params: { include_templates: includeTemplates },
  });
  return response.data;
}

/**
 * Create a new scenario
 */
export async function createScenario(scenario: ScenarioCreate): Promise<Scenario> {
  const response = await apiClient.post('/api/v1/scenarios', scenario);
  return response.data;
}

/**
 * Get a specific scenario by ID
 */
export async function getScenario(scenarioId: string): Promise<Scenario> {
  const response = await apiClient.get(`/api/v1/scenarios/${scenarioId}`);
  return response.data;
}

/**
 * Delete a scenario
 */
export async function deleteScenario(scenarioId: string): Promise<{ message: string; success: boolean }> {
  const response = await apiClient.delete(`/api/v1/scenarios/${scenarioId}`);
  return response.data;
}

/**
 * Run simulation for a saved scenario
 */
export async function simulateScenario(
  scenarioId: string,
  budgetOverride?: number
): Promise<SimulationResult> {
  const response = await apiClient.post(`/api/v1/scenarios/${scenarioId}/simulate`, null, {
    params: budgetOverride !== undefined ? { budget_override: budgetOverride } : undefined,
  });
  return response.data;
}

/**
 * Run ad-hoc simulation without saving scenario
 */
export async function simulateAdhoc(request: AdhocSimulationRequest): Promise<SimulationResult> {
  const response = await apiClient.post('/api/v1/scenarios/simulate-adhoc', request);
  return response.data;
}

/**
 * Get immutability information
 */
export async function getImmutabilityInfo(): Promise<{
  system: string;
  guarantees: string[];
  advisory_notice: string;
  reference: string;
}> {
  const response = await apiClient.get('/api/v1/scenarios/info/immutability');
  return response.data;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Format cost in dollars
 */
export function formatCost(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

/**
 * Format duration in human readable form
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

/**
 * Get status color for simulation result
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'feasible':
      return 'text-green-400';
    case 'budget_exceeded':
      return 'text-red-400';
    default:
      return 'text-yellow-400';
  }
}

/**
 * Get risk severity color
 */
export function getRiskSeverityColor(severity: string): string {
  switch (severity) {
    case 'high':
      return 'text-red-500 bg-red-900/30';
    case 'medium':
      return 'text-yellow-500 bg-yellow-900/30';
    case 'low':
      return 'text-blue-500 bg-blue-900/30';
    default:
      return 'text-gray-500 bg-gray-900/30';
  }
}

/**
 * Get utilization color class
 */
export function getUtilizationColor(pct: number): string {
  if (pct >= 90) return 'text-red-400';
  if (pct >= 70) return 'text-yellow-400';
  return 'text-green-400';
}

export default {
  listScenarios,
  createScenario,
  getScenario,
  deleteScenario,
  simulateScenario,
  simulateAdhoc,
  getImmutabilityInfo,
  formatCost,
  formatDuration,
  getStatusColor,
  getRiskSeverityColor,
  getUtilizationColor,
};
