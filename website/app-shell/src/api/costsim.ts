/**
 * @audience shared
 *
 * Cost Simulation API Client
 * Cost projections and simulations
 */
import apiClient from './client';

export interface SimulationRequest {
  scenario?: string;
  steps: Array<{
    skill: string;
    params?: Record<string, unknown>;
    iterations?: number;
  }>;
  budget_cents?: number;
  resource_contract_id?: string;
}

export interface SimulationResult {
  feasible: boolean;
  estimated_cost_cents: number;
  estimated_duration_ms: number;
  step_estimates: Array<{
    skill_id: string;
    estimated_cost_cents: number;
    estimated_latency_ms: number;
  }>;
  warnings: string[];
  budget_sufficient: boolean;
  budget_remaining_cents?: number;
  divergence_risk?: number;
  incidents?: Array<{
    type: string;
    message: string;
    severity: 'low' | 'medium' | 'high';
  }>;
}

// Run Cost Simulation (V2)
export async function simulate(request: SimulationRequest): Promise<SimulationResult> {
  // Backend expects 'plan' not 'steps'
  const payload = {
    plan: request.steps.map(s => ({
      skill: s.skill,
      params: s.params || {},
      iterations: s.iterations,
    })),
    budget_cents: request.budget_cents,
  };
  const { data } = await apiClient.post('/costsim/v2/simulate', payload);

  // Map backend response to frontend format
  // Backend returns: v1_feasible, v1_cost_cents, v1_duration_ms
  // Frontend expects: feasible, estimated_cost_cents, estimated_duration_ms
  const budgetCents = request.budget_cents || 1000;
  const costCents = data.v1_cost_cents ?? data.estimated_cost_cents ?? 0;

  return {
    feasible: data.v1_feasible ?? data.feasible ?? false,
    estimated_cost_cents: costCents,
    estimated_duration_ms: data.v1_duration_ms ?? data.estimated_duration_ms ?? 0,
    step_estimates: data.step_estimates || request.steps.map(s => ({
      skill_id: s.skill,
      estimated_cost_cents: Math.round(costCents / request.steps.length),
      estimated_latency_ms: Math.round((data.v1_duration_ms || 500) / request.steps.length),
    })),
    warnings: data.warnings || [],
    budget_sufficient: costCents <= budgetCents,
    budget_remaining_cents: budgetCents - costCents,
    divergence_risk: data.drift_score ?? data.divergence_risk,
    incidents: data.incidents || [],
  };
}

// Get Sandbox Status
export async function getSandboxStatus() {
  try {
    const { data } = await apiClient.get('/costsim/v2/status');
    return data;
  } catch {
    return { status: 'unknown' };
  }
}

// Get Incidents
export async function getIncidents() {
  try {
    const { data } = await apiClient.get('/costsim/v2/incidents');
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

// Reset Circuit Breaker
export async function resetCircuitBreaker() {
  const { data } = await apiClient.post('/costsim/v2/reset');
  return data;
}

// Datasets
export async function getDatasets() {
  try {
    const { data } = await apiClient.get('/costsim/datasets');
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export async function getDataset(datasetId: string) {
  const { data } = await apiClient.get(`/costsim/datasets/${datasetId}`);
  return data;
}

export async function validateAgainstDataset(datasetId: string) {
  const { data } = await apiClient.post(`/costsim/datasets/${datasetId}/validate`);
  return data;
}

// Divergence Report
export async function getDivergenceReport() {
  try {
    const { data } = await apiClient.get('/costsim/divergence');
    return data;
  } catch {
    return { divergence: 0, details: [] };
  }
}

// Canary
export async function triggerCanaryRun() {
  const { data } = await apiClient.post('/costsim/canary/run');
  return data;
}

export async function getCanaryReports() {
  try {
    const { data } = await apiClient.get('/costsim/canary/reports');
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}
