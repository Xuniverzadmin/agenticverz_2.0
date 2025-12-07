/**
 * AOS JavaScript/TypeScript SDK Client
 *
 * Usage:
 *   import { AOSClient } from '@agenticverz/aos-sdk';
 *   const client = new AOSClient({ apiKey: '...', baseUrl: 'http://localhost:8000' });
 *
 *   // Machine-native APIs
 *   const caps = await client.getCapabilities();
 *   const result = await client.simulate([{ skill: 'http_call', params: { url: '...' } }]);
 */

import type {
  AOSClientOptions,
  PlanStep,
  SimulateResult,
  QueryType,
  QueryResult,
  Skill,
  SkillDescriptor,
  Capabilities,
  ResourceContract,
  Run,
  MemoryResult,
} from "./types";

export class AOSError extends Error {
  statusCode?: number;
  response?: unknown;

  constructor(message: string, statusCode?: number, response?: unknown) {
    super(message);
    this.name = "AOSError";
    this.statusCode = statusCode;
    this.response = response;
  }
}

export class AOSClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private headers: Record<string, string>;

  /**
   * Create a new AOS client.
   *
   * @param options - Client configuration options
   *
   * @example
   * ```typescript
   * const client = new AOSClient({
   *   apiKey: 'your-api-key',
   *   baseUrl: 'http://localhost:8000'
   * });
   * ```
   */
  constructor(options: AOSClientOptions = {}) {
    this.baseUrl = (options.baseUrl || process.env.AOS_BASE_URL || "http://127.0.0.1:8000").replace(
      /\/+$/,
      ""
    );
    this.apiKey = options.apiKey || process.env.AOS_API_KEY;
    this.timeout = options.timeout || 30000;

    this.headers = {
      "Content-Type": "application/json",
    };
    if (this.apiKey) {
      this.headers["X-AOS-Key"] = this.apiKey;
    }
  }

  private url(path: string): string {
    return `${this.baseUrl}${path}`;
  }

  private async request<T>(
    method: string,
    path: string,
    options: { json?: unknown; params?: Record<string, string> } = {}
  ): Promise<T> {
    let url = this.url(path);

    if (options.params) {
      const searchParams = new URLSearchParams(options.params);
      url = `${url}?${searchParams.toString()}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers: this.headers,
        body: options.json ? JSON.stringify(options.json) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorBody: unknown;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new AOSError(`Request failed: ${response.status}`, response.status, errorBody);
      }

      if (response.status === 204 || response.headers.get("content-length") === "0") {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof AOSError) {
        throw error;
      }
      if ((error as Error).name === "AbortError") {
        throw new AOSError(`Request timeout after ${this.timeout}ms`);
      }
      throw new AOSError(`Request error: ${(error as Error).message}`);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // =========== Machine-Native APIs ===========

  /**
   * Simulate a plan before execution.
   *
   * Pre-execution validation to check if a plan is feasible given
   * current constraints (budget, rate limits, permissions).
   *
   * @param plan - List of steps with skill and params
   * @param budgetCents - Available budget in cents (default: 1000)
   * @param agentId - Optional agent ID for permission checking
   * @param tenantId - Optional tenant ID for isolation
   *
   * @example
   * ```typescript
   * const result = await client.simulate([
   *   { skill: 'http_call', params: { url: 'https://api.example.com' } },
   *   { skill: 'llm_invoke', params: { prompt: 'Summarize' } }
   * ]);
   * if (result.feasible) {
   *   console.log(`Plan OK, cost: ${result.estimated_cost_cents}c`);
   * }
   * ```
   */
  async simulate(
    plan: PlanStep[],
    budgetCents = 1000,
    agentId?: string,
    tenantId?: string
  ): Promise<SimulateResult> {
    const payload: Record<string, unknown> = {
      plan,
      budget_cents: budgetCents,
    };
    if (agentId) payload.agent_id = agentId;
    if (tenantId) payload.tenant_id = tenantId;

    return this.request<SimulateResult>("POST", "/api/v1/runtime/simulate", { json: payload });
  }

  /**
   * Query runtime state.
   *
   * @param queryType - Type of query to execute
   * @param params - Query-specific parameters
   * @param agentId - Optional agent ID for context
   * @param runId - Optional run ID for context
   *
   * Supported query types:
   * - remaining_budget_cents: Current budget remaining
   * - what_did_i_try_already: Previous execution attempts
   * - allowed_skills: List of available skills
   * - last_step_outcome: Most recent execution outcome
   * - skills_available_for_goal: Skills matching a goal
   */
  async query(
    queryType: QueryType,
    params?: Record<string, unknown>,
    agentId?: string,
    runId?: string
  ): Promise<QueryResult> {
    const payload: Record<string, unknown> = {
      query_type: queryType,
      params: params || {},
    };
    if (agentId) payload.agent_id = agentId;
    if (runId) payload.run_id = runId;

    return this.request<QueryResult>("POST", "/api/v1/runtime/query", { json: payload });
  }

  /**
   * List all available skills.
   *
   * @example
   * ```typescript
   * const { skills } = await client.listSkills();
   * for (const skill of skills) {
   *   console.log(`${skill.name}: ${skill.description}`);
   * }
   * ```
   */
  async listSkills(): Promise<{ skills: Skill[]; count: number }> {
    return this.request<{ skills: Skill[]; count: number }>("GET", "/api/v1/runtime/skills");
  }

  /**
   * Get detailed descriptor for a skill.
   *
   * @param skillId - The skill to describe (e.g., 'http_call', 'llm_invoke')
   */
  async describeSkill(skillId: string): Promise<SkillDescriptor> {
    return this.request<SkillDescriptor>("GET", `/api/v1/runtime/skills/${skillId}`);
  }

  /**
   * Get available capabilities for an agent/tenant.
   *
   * @param agentId - Optional agent ID
   * @param tenantId - Optional tenant ID
   *
   * @example
   * ```typescript
   * const caps = await client.getCapabilities();
   * console.log(`Budget: ${caps.budget_remaining_cents}c`);
   * console.log(`Skills: ${caps.skills_available.join(', ')}`);
   * ```
   */
  async getCapabilities(agentId?: string, tenantId?: string): Promise<Capabilities> {
    const params: Record<string, string> = {};
    if (agentId) params.agent_id = agentId;
    if (tenantId) params.tenant_id = tenantId;

    return this.request<Capabilities>("GET", "/api/v1/runtime/capabilities", {
      params: Object.keys(params).length > 0 ? params : undefined,
    });
  }

  /**
   * Get resource contract for a specific resource.
   *
   * @param resourceId - The resource to get contract for
   */
  async getResourceContract(resourceId: string): Promise<ResourceContract> {
    return this.request<ResourceContract>("GET", `/api/v1/runtime/resource-contract/${resourceId}`);
  }

  // =========== Agent Workflow APIs ===========

  /**
   * Create a new agent.
   *
   * @param name - Name for the agent
   * @returns Agent ID
   */
  async createAgent(name: string): Promise<string> {
    const data = await this.request<{ agent_id?: string; id?: string }>("POST", "/agents", {
      json: { name },
    });
    return data.agent_id || data.id || "";
  }

  /**
   * Post a goal for an agent to execute.
   *
   * @param agentId - Agent ID to execute the goal
   * @param goal - Goal description
   * @param forceSkill - Optional skill to force use
   * @returns Run ID for tracking execution
   */
  async postGoal(agentId: string, goal: string, forceSkill?: string): Promise<string> {
    const payload: Record<string, unknown> = { goal };
    if (forceSkill) payload.force_skill = forceSkill;

    const data = await this.request<{
      run_id?: string;
      run?: { id?: string };
      plan?: { plan_id?: string };
    }>("POST", `/agents/${agentId}/goals`, { json: payload });

    return data.run_id || data.run?.id || data.plan?.plan_id || "";
  }

  /**
   * Poll for run completion.
   *
   * @param agentId - Agent ID
   * @param runId - Run ID to poll
   * @param timeout - Maximum wait time in milliseconds (default: 30000)
   * @param interval - Poll interval in milliseconds (default: 500)
   * @returns Run result when completed
   * @throws Error if run doesn't complete within timeout
   */
  async pollRun(agentId: string, runId: string, timeout = 30000, interval = 500): Promise<Run> {
    const end = Date.now() + timeout;

    while (Date.now() < end) {
      try {
        const data = await this.request<Run & { run?: Run; plan?: { status?: string } }>(
          "GET",
          `/agents/${agentId}/runs/${runId}`
        );

        const status = data.status || data.run?.status || data.plan?.status;

        if (status === "succeeded" || status === "failed") {
          return data;
        }
      } catch {
        // Continue polling on error
      }

      await new Promise((resolve) => setTimeout(resolve, interval));
    }

    throw new AOSError(`Run ${runId} did not complete in ${timeout}ms`);
  }

  /**
   * Query agent memory.
   *
   * @param agentId - Agent ID
   * @param query - Search query
   * @param k - Number of results to return (default: 5)
   */
  async recall(agentId: string, query: string, k = 5): Promise<MemoryResult> {
    return this.request<MemoryResult>("GET", `/agents/${agentId}/recall`, {
      params: { query, k: String(k) },
    });
  }

  // =========== Run Management APIs ===========

  /**
   * Create a new run for an agent.
   *
   * @param agentId - Agent ID
   * @param goal - Goal description
   * @param plan - Optional pre-defined plan
   */
  async createRun(agentId: string, goal: string, plan?: PlanStep[]): Promise<Run> {
    const payload: Record<string, unknown> = {
      agent_id: agentId,
      goal,
    };
    if (plan) payload.plan = plan;

    return this.request<Run>("POST", "/api/v1/runs", { json: payload });
  }

  /**
   * Get run status and details.
   *
   * @param runId - Run ID
   */
  async getRun(runId: string): Promise<Run> {
    return this.request<Run>("GET", `/api/v1/runs/${runId}`);
  }
}

// Backwards compatibility alias
export const NovaClient = AOSClient;
