/**
 * @audience founder
 *
 * Worker API Client for Business Builder Worker v0.2
 */
import axios from 'axios';
import type {
  WorkerRunRequest,
  WorkerRunResponse,
  BrandRequest,
} from '@/types/worker';

// === DEBUG LOGGING ===
const DEBUG = true;
const log = (area: string, message: string, data?: unknown) => {
  if (DEBUG) {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
    console.log(`%c[${timestamp}] [WORKER-API] [${area}]`, 'color: #6366f1; font-weight: bold', message, data ?? '');
  }
};

// Use relative URL in production (same origin), localhost for dev
const API_BASE = import.meta.env.VITE_API_URL || '';
const WORKER_BASE = `${API_BASE}/api/v1/workers/business-builder`;

log('INIT', `API_BASE="${API_BASE}", WORKER_BASE="${WORKER_BASE}"`);

// Get auth token from localStorage
function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('aos_token');
  log('AUTH', `Token from localStorage: ${token ? token.slice(0, 8) + '...' : 'NOT SET'}`);
  if (token) {
    // Backend expects X-AOS-Key header for simple API key auth
    return { 'X-AOS-Key': token };
  }
  log('AUTH', '⚠️ NO TOKEN - requests will fail with 422');
  return {};
}

/**
 * Start a worker run with real-time event streaming.
 * Returns immediately with run_id - use SSE to get real-time updates.
 */
export async function startWorkerRun(request: WorkerRunRequest): Promise<WorkerRunResponse> {
  const url = `${WORKER_BASE}/run-streaming`;
  const headers = getAuthHeader();
  log('START-RUN', `POST ${url}`, { task: request.task, headers: Object.keys(headers) });

  try {
    const response = await axios.post<WorkerRunResponse>(url, request, { headers });
    log('START-RUN', `✅ Success - run_id: ${response.data.run_id}`, response.data);
    return response.data;
  } catch (error: unknown) {
    const axiosError = error as { response?: { status: number; data: unknown }; message: string };
    log('START-RUN', `❌ FAILED - ${axiosError.response?.status || 'network error'}`, axiosError.response?.data || axiosError.message);
    throw error;
  }
}

/**
 * Start a worker run without streaming (sync or async).
 */
export async function runWorker(request: WorkerRunRequest): Promise<WorkerRunResponse> {
  const response = await axios.post<WorkerRunResponse>(
    `${WORKER_BASE}/run`,
    request,
    { headers: getAuthHeader() }
  );
  return response.data;
}

/**
 * Get details of a specific run.
 */
export async function getWorkerRun(runId: string): Promise<WorkerRunResponse> {
  const response = await axios.get<WorkerRunResponse>(
    `${WORKER_BASE}/runs/${runId}`,
    { headers: getAuthHeader() }
  );
  return response.data;
}

/**
 * List recent worker runs.
 */
export async function listWorkerRuns(limit = 20): Promise<{
  runs: Array<{
    run_id: string;
    task: string;
    status: string;
    success: boolean | null;
    created_at: string;
    total_latency_ms: number | null;
  }>;
  total: number;
}> {
  const url = `${WORKER_BASE}/runs`;
  const headers = getAuthHeader();
  log('LIST-RUNS', `GET ${url}?limit=${limit}`, { headers: Object.keys(headers) });

  try {
    const response = await axios.get(url, { params: { limit }, headers });
    log('LIST-RUNS', `✅ Got ${response.data.runs?.length || 0} runs`, response.data);
    return response.data;
  } catch (error: unknown) {
    const axiosError = error as { response?: { status: number; data: unknown }; message: string };
    log('LIST-RUNS', `❌ FAILED - ${axiosError.response?.status || 'network error'}`, axiosError.response?.data || axiosError.message);
    throw error;
  }
}

/**
 * Replay a previous execution.
 */
export async function replayWorkerRun(replayToken: Record<string, unknown>): Promise<WorkerRunResponse> {
  const response = await axios.post<WorkerRunResponse>(
    `${WORKER_BASE}/replay`,
    { replay_token: replayToken },
    { headers: getAuthHeader() }
  );
  return response.data;
}

/**
 * Validate a brand schema without executing.
 */
export async function validateBrand(brand: BrandRequest): Promise<{
  valid: boolean;
  errors: string[];
  warnings: string[];
  policy_rules_generated: number;
  drift_anchors_count: number;
}> {
  const response = await axios.post(`${WORKER_BASE}/validate-brand`, brand, {
    headers: getAuthHeader(),
  });
  return response.data;
}

/**
 * Get worker health status.
 */
export async function getWorkerHealth(): Promise<{
  status: string;
  version: string;
  moats: Record<string, string>;
  runs_in_memory: number;
}> {
  const response = await axios.get(`${WORKER_BASE}/health`);
  return response.data;
}

/**
 * Get all events for a run (non-streaming).
 */
export async function getRunEvents(runId: string): Promise<{
  run_id: string;
  events: Array<{
    type: string;
    timestamp: string;
    run_id: string;
    data: Record<string, unknown>;
  }>;
  count: number;
}> {
  const response = await axios.get(`${WORKER_BASE}/events/${runId}`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

/**
 * Delete a run from storage.
 */
export async function deleteWorkerRun(runId: string): Promise<{ deleted: boolean; run_id: string }> {
  const response = await axios.delete(`${WORKER_BASE}/runs/${runId}`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

/**
 * Get the SSE stream URL for a run.
 */
export function getStreamUrl(runId: string): string {
  const url = `${WORKER_BASE}/stream/${runId}`;
  log('SSE-URL', `Generated stream URL: ${url}`);
  return url;
}

/**
 * Create an EventSource for streaming run events.
 */
export function createEventSource(runId: string): EventSource {
  const url = getStreamUrl(runId);
  log('SSE-CREATE', `Creating EventSource for ${url}`);
  return new EventSource(url);
}
