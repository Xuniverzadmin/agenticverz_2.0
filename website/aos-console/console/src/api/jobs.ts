import apiClient from './client';
import type { Job, JobItem, SimulationResult, CreateJobRequest, PaginatedResponse } from '@/types/job';

export async function getJobs(params?: {
  status?: string;
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<Job>> {
  try {
    // Use admin/failed-runs for job history
    const { data } = await apiClient.get('/admin/failed-runs', { params });
    const items = Array.isArray(data) ? data : (data?.items || []);
    return {
      items: items.map((r: Record<string, unknown>) => ({
        id: r.run_id || r.id,
        orchestrator_agent: r.agent_id || 'unknown',
        worker_agent: r.worker_id || 'unknown',
        task: r.task || r.action || 'unknown',
        status: r.status || 'unknown',
        parallelism: 1,
        total_items: r.total_items || 1,
        completed_items: r.completed_items || 0,
        failed_items: r.failed_items || (r.status === 'failed' ? 1 : 0),
        progress_percent: r.progress || 0,
        estimated_cost_cents: r.cost || 0,
        actual_cost_cents: r.actual_cost || 0,
        created_at: r.created_at,
        started_at: r.started_at,
        completed_at: r.completed_at,
      })),
      total: items.length,
      page: params?.page || 1,
      limit: params?.limit || 20,
    };
  } catch {
    return { items: [], total: 0, page: 1, limit: 20 };
  }
}

export async function getJob(jobId: string): Promise<Job> {
  // Try to get from traces
  const { data } = await apiClient.get(`/api/v1/traces/${jobId}`);
  return {
    id: data.run_id || data.id,
    orchestrator_agent: data.agent_id || 'unknown',
    worker_agent: data.worker_id || 'unknown',
    task: data.task || data.action || 'unknown',
    status: data.status || 'unknown',
    parallelism: 1,
    total_items: data.total_items || 1,
    completed_items: data.completed_items || 0,
    failed_items: data.failed_items || 0,
    progress_percent: data.progress || 0,
    estimated_cost_cents: data.cost || 0,
    actual_cost_cents: data.actual_cost || 0,
    created_at: data.created_at,
    started_at: data.started_at,
    completed_at: data.completed_at,
  };
}

export async function getJobItems(jobId: string, params?: {
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<JobItem>> {
  console.log('getJobItems called:', jobId, params);
  return { items: [], total: 0, page: 1, limit: 20 };
}

export async function simulateJob(request: CreateJobRequest): Promise<SimulationResult> {
  // Use runtime simulate endpoint - note: `plan` is an array of steps
  const { data } = await apiClient.post('/api/v1/runtime/simulate', {
    plan: request.items?.map((item) => ({
      skill: item.skill || 'llm_invoke',
      params: item.params || {},
    })) || [{ skill: 'llm_invoke', params: {} }],
    budget_cents: 1000,
  });

  return {
    feasible: data.feasible ?? true,
    estimated_cost_cents: data.estimated_cost_cents || 0,
    estimated_duration_ms: data.estimated_duration_ms || 0,
    skill_breakdown: data.step_estimates?.map((s: { skill_id: string; estimated_cost_cents: number; estimated_latency_ms: number }) => ({
      skill: s.skill_id,
      cost_cents: s.estimated_cost_cents,
      duration_ms: s.estimated_latency_ms,
    })) || [],
    warnings: data.warnings || [],
    budget_check: {
      available: data.budget_remaining_cents || 1000,
      required: data.estimated_cost_cents || 0,
      sufficient: data.budget_sufficient ?? true,
    },
  };
}

export async function createJob(request: CreateJobRequest): Promise<Job> {
  // Create a run via the costsim endpoint or direct agent run
  const { data } = await apiClient.post('/api/v1/costsim/v2/simulate', {
    scenario: request.task,
    steps: request.items?.map((item) => ({
      skill: item.skill || 'llm_invoke',
      params: item.params || {},
    })) || [],
  });

  return {
    id: data.run_id || data.id || 'new-' + Date.now(),
    orchestrator_agent: request.orchestrator_agent || 'system',
    worker_agent: request.worker_agent || 'worker',
    task: request.task,
    status: 'pending',
    parallelism: request.parallelism || 1,
    total_items: request.items?.length || 0,
    completed_items: 0,
    failed_items: 0,
    progress_percent: 0,
    estimated_cost_cents: data.estimated_cost_cents || 0,
    actual_cost_cents: 0,
    created_at: new Date().toISOString(),
  };
}

export async function cancelJob(jobId: string): Promise<{
  job_id: string;
  status: string;
  completed_items: number;
  cancelled_items: number;
  credits_refunded: number;
}> {
  console.log('cancelJob called:', jobId);
  return {
    job_id: jobId,
    status: 'cancelled',
    completed_items: 0,
    cancelled_items: 0,
    credits_refunded: 0,
  };
}

export async function claimJobItem(jobId: string): Promise<JobItem> {
  console.log('claimJobItem called:', jobId);
  throw new Error('Not implemented');
}

export async function completeJobItem(jobId: string, itemId: string, result: unknown): Promise<void> {
  console.log('completeJobItem called:', jobId, itemId, result);
}

export async function failJobItem(jobId: string, itemId: string, error: string): Promise<void> {
  console.log('failJobItem called:', jobId, itemId, error);
}
