/**
 * Stagetest Client — Data Access for Stagetest Evidence Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Fetch stagetest runs, cases, and API snapshots from /hoc/api/stagetest/*
 * artifact_class: CODE
 */

// ============================================================================
// Types
// ============================================================================

export type CaseStatus = 'PASS' | 'FAIL' | 'SKIPPED';

export interface Assertion {
  id: string;
  status: string;
  message: string;
}

export interface CaseSummary {
  case_id: string;
  uc_id: string;
  stage: string;
  operation_name: string;
  status: CaseStatus;
  determinism_hash: string;
}

export interface CaseDetail {
  run_id: string;
  case_id: string;
  uc_id: string;
  stage: string;
  operation_name: string;
  route_path: string;
  api_method: string;
  request_fields: Record<string, unknown>;
  response_fields: Record<string, unknown>;
  synthetic_input: Record<string, unknown>;
  observed_output: Record<string, unknown>;
  assertions: Assertion[];
  status: CaseStatus;
  determinism_hash: string;
  signature: string;
  evidence_files: string[];
}

export interface RunSummary {
  run_id: string;
  created_at: string;
  stages_executed: string[];
  total_cases: number;
  pass_count: number;
  fail_count: number;
  determinism_digest: string;
  artifact_version: string;
}

export interface ApiEndpoint {
  method: string;
  path: string;
  operation: string;
}

// ============================================================================
// API Fetch Functions
// ============================================================================

const BASE = '/hoc/api/stagetest';

export async function fetchRuns(): Promise<RunSummary[]> {
  try {
    const res = await fetch(`${BASE}/runs`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.runs ?? [];
  } catch {
    return [];
  }
}

export async function fetchRun(runId: string): Promise<RunSummary | null> {
  try {
    const res = await fetch(`${BASE}/runs/${runId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchCases(runId: string): Promise<CaseSummary[]> {
  try {
    const res = await fetch(`${BASE}/runs/${runId}/cases`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.cases ?? [];
  } catch {
    return [];
  }
}

export async function fetchCaseDetail(runId: string, caseId: string): Promise<CaseDetail | null> {
  try {
    const res = await fetch(`${BASE}/runs/${runId}/cases/${caseId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchApis(): Promise<ApiEndpoint[]> {
  try {
    const res = await fetch(`${BASE}/apis`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.endpoints ?? [];
  } catch {
    return [];
  }
}

// ============================================================================
// Helpers
// ============================================================================

export function statusColor(status: CaseStatus): string {
  switch (status) {
    case 'PASS': return '#22c55e';
    case 'FAIL': return '#ef4444';
    case 'SKIPPED': return '#9ca3af';
  }
}

export function truncateHash(hash: string, len = 12): string {
  return hash.length > len ? hash.slice(0, len) + '...' : hash;
}
