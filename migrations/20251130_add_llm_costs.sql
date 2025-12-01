-- migrations/20251130_add_llm_costs.sql
-- Phase 2D: LLM cost tracking and budget enforcement
BEGIN;

-- Ensure budget columns exist on agents (idempotent)
ALTER TABLE agents
  ADD COLUMN IF NOT EXISTS budget_cents BIGINT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS spent_cents BIGINT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS budget_alert_threshold FLOAT DEFAULT 0.8;

-- Ensure idempotency and tenant columns exist on runs (idempotent)
ALTER TABLE runs
  ADD COLUMN IF NOT EXISTS idempotency_key TEXT NULL,
  ADD COLUMN IF NOT EXISTS tenant_id TEXT NULL;

-- Create unique index on idempotency_key (per tenant)
CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_idempotency_key
  ON runs (idempotency_key, tenant_id)
  WHERE idempotency_key IS NOT NULL;

-- LLM cost tracking table
CREATE TABLE IF NOT EXISTS llm_costs (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  run_id TEXT REFERENCES runs(id) ON DELETE SET NULL,
  agent_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
  tenant_id TEXT,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  input_tokens BIGINT DEFAULT 0,
  output_tokens BIGINT DEFAULT 0,
  cost_cents BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for llm_costs
CREATE INDEX IF NOT EXISTS idx_llm_costs_run_id ON llm_costs (run_id);
CREATE INDEX IF NOT EXISTS idx_llm_costs_agent_id ON llm_costs (agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_costs_tenant_id ON llm_costs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_llm_costs_created_at ON llm_costs (created_at);
CREATE INDEX IF NOT EXISTS idx_llm_costs_provider_model ON llm_costs (provider, model);

-- Add comment for documentation
COMMENT ON TABLE llm_costs IS 'Tracks LLM API costs per run for budget enforcement and auditing';

COMMIT;
