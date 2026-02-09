"""
Bootstrap (idempotent) minimal knowledge governance tables in a dev/staging DB.

Why this exists:
- Some local/dev databases can be schema-drifted relative to `alembic_version`.
- The knowledge lifecycle + governed retrieval tests intentionally skip when
  core tables are missing.

This script creates/patches ONLY the tables required for governed knowledge planes:
- policy_snapshots (+ threshold_snapshot_hash)
- retrieval_evidence
- knowledge_plane_registry
- runs.policy_snapshot_id (+ index)

It does NOT attempt to reconcile the database to `alembic head`.
Use Alembic in a clean DB when possible.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import text


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _ensure_tenants(conn) -> None:
    """
    Ensure the tenants table exists with the columns required by governance tests.

    Note: this is a *bootstrap* helper for drifted dev/staging DBs. It does not
    attempt to fully reconcile schema history with Alembic.
    """
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS tenants (
              id VARCHAR(64) PRIMARY KEY,
              name VARCHAR(255) NOT NULL,
              slug VARCHAR(100) NOT NULL UNIQUE,
              clerk_org_id VARCHAR(100) NULL UNIQUE,
              plan VARCHAR(50) NOT NULL DEFAULT 'free',
              billing_email VARCHAR(255) NULL,
              stripe_customer_id VARCHAR(100) NULL,
              max_workers INTEGER NOT NULL DEFAULT 3,
              max_runs_per_day INTEGER NOT NULL DEFAULT 100,
              max_concurrent_runs INTEGER NOT NULL DEFAULT 5,
              max_tokens_per_month BIGINT NOT NULL DEFAULT 1000000,
              max_api_keys INTEGER NOT NULL DEFAULT 5,
              runs_today INTEGER NOT NULL DEFAULT 0,
              runs_this_month INTEGER NOT NULL DEFAULT 0,
              tokens_this_month BIGINT NOT NULL DEFAULT 0,
              last_run_reset_at TIMESTAMP WITHOUT TIME ZONE NULL,
              status VARCHAR(50) NOT NULL DEFAULT 'active',
              suspended_reason TEXT NULL,
              onboarding_state INTEGER NOT NULL DEFAULT 0,
              created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
              updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
              is_synthetic BOOLEAN NOT NULL DEFAULT false,
              synthetic_scenario_id VARCHAR(100) NULL
            );
            """
        )
    )

    # Patch older variants (best-effort; no drops).
    conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'unknown';"))
    conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS slug VARCHAR(100) NOT NULL DEFAULT 'unknown';"))
    conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'active';"))
    conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now();"))
    conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now();"))


def _ensure_runs(conn) -> None:
    """
    Ensure the runs table exists with the columns required by knowledge e2e tests.

    We intentionally keep types loose (VARCHAR/TEXT) to tolerate drift while still
    matching ORM inserts for core governance tests.
    """
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS runs (
              id VARCHAR(64) PRIMARY KEY,
              agent_id VARCHAR(128) NOT NULL,
              actor_type VARCHAR(32) NOT NULL DEFAULT 'SYSTEM',
              actor_id VARCHAR(128) NULL,
              origin_system_id VARCHAR(128) NOT NULL DEFAULT 'legacy-migration',
              goal TEXT NOT NULL,
              status VARCHAR(32) NOT NULL DEFAULT 'queued',
              attempts INTEGER NOT NULL DEFAULT 0,
              max_attempts INTEGER NOT NULL DEFAULT 3,
              error_message TEXT NULL,
              plan_json TEXT NULL,
              tool_calls_json TEXT NULL,
              idempotency_key VARCHAR(128) NULL,
              parent_run_id VARCHAR(64) NULL,
              priority INTEGER NOT NULL DEFAULT 0,
              tenant_id VARCHAR(64) NULL,
              is_synthetic BOOLEAN NOT NULL DEFAULT false,
              synthetic_scenario_id VARCHAR(128) NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              started_at TIMESTAMPTZ NULL,
              completed_at TIMESTAMPTZ NULL,
              next_attempt_at TIMESTAMPTZ NULL,
              duration_ms DOUBLE PRECISION NULL,
              authorization_decision VARCHAR(30) NULL DEFAULT 'GRANTED',
              authorization_engine VARCHAR(64) NULL,
              authorization_context TEXT NULL,
              authorized_at TIMESTAMPTZ NULL,
              authorized_by VARCHAR(128) NULL,
              policy_snapshot_id VARCHAR(64) NULL,
              termination_reason VARCHAR(64) NULL,
              stopped_at_step INTEGER NULL,
              violation_policy_id VARCHAR(64) NULL,
              observability_status VARCHAR(32) NOT NULL DEFAULT 'FULL',
              observability_error TEXT NULL,
              state VARCHAR(32) NOT NULL DEFAULT 'LIVE',
              project_id VARCHAR(64) NULL,
              last_seen_at TIMESTAMPTZ NULL,
              source VARCHAR(32) NOT NULL DEFAULT 'agent',
              provider_type VARCHAR(32) NOT NULL DEFAULT 'anthropic',
              risk_level VARCHAR(32) NOT NULL DEFAULT 'NORMAL',
              latency_bucket VARCHAR(32) NOT NULL DEFAULT 'OK',
              evidence_health VARCHAR(32) NOT NULL DEFAULT 'FLOWING',
              integrity_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
              incident_count INTEGER NOT NULL DEFAULT 0,
              policy_draft_count INTEGER NOT NULL DEFAULT 0,
              policy_violation BOOLEAN NOT NULL DEFAULT false,
              input_tokens INTEGER NULL,
              output_tokens INTEGER NULL,
              estimated_cost_usd DOUBLE PRECISION NULL,
              expected_latency_ms INTEGER NULL
            );
            """
        )
    )

    # Normalize timestamp types to TIMESTAMPTZ if older DB used naive timestamps.
    conn.execute(
        text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'runs'
                      AND column_name = 'created_at'
                      AND data_type = 'timestamp without time zone'
                ) THEN
                    ALTER TABLE runs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
                END IF;
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'runs'
                      AND column_name = 'started_at'
                      AND data_type = 'timestamp without time zone'
                ) THEN
                    ALTER TABLE runs ALTER COLUMN started_at TYPE TIMESTAMPTZ USING started_at AT TIME ZONE 'UTC';
                END IF;
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'runs'
                      AND column_name = 'completed_at'
                      AND data_type = 'timestamp without time zone'
                ) THEN
                    ALTER TABLE runs ALTER COLUMN completed_at TYPE TIMESTAMPTZ USING completed_at AT TIME ZONE 'UTC';
                END IF;
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'runs'
                      AND column_name = 'next_attempt_at'
                      AND data_type = 'timestamp without time zone'
                ) THEN
                    ALTER TABLE runs ALTER COLUMN next_attempt_at TYPE TIMESTAMPTZ USING next_attempt_at AT TIME ZONE 'UTC';
                END IF;
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'runs'
                      AND column_name = 'authorized_at'
                      AND data_type = 'timestamp without time zone'
                ) THEN
                    ALTER TABLE runs ALTER COLUMN authorized_at TYPE TIMESTAMPTZ USING authorized_at AT TIME ZONE 'UTC';
                END IF;
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'runs'
                      AND column_name = 'last_seen_at'
                      AND data_type = 'timestamp without time zone'
                ) THEN
                    ALTER TABLE runs ALTER COLUMN last_seen_at TYPE TIMESTAMPTZ USING last_seen_at AT TIME ZONE 'UTC';
                END IF;
            END $$;
            """
        )
    )

    # Patch older variants (best-effort; no drops).
    for stmt in [
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS agent_id VARCHAR(128) NOT NULL DEFAULT 'unknown';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS actor_type VARCHAR(32) NOT NULL DEFAULT 'SYSTEM';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS actor_id VARCHAR(128) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS origin_system_id VARCHAR(128) NOT NULL DEFAULT 'legacy-migration';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS goal TEXT NOT NULL DEFAULT '';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'queued';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS error_message TEXT NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS plan_json TEXT NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS tool_calls_json TEXT NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS parent_run_id VARCHAR(64) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS is_synthetic BOOLEAN NOT NULL DEFAULT false;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS synthetic_scenario_id VARCHAR(128) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS duration_ms DOUBLE PRECISION NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS authorization_decision VARCHAR(30) NULL DEFAULT 'GRANTED';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS authorization_engine VARCHAR(64) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS authorization_context TEXT NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS authorized_at TIMESTAMPTZ NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS authorized_by VARCHAR(128) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS policy_snapshot_id VARCHAR(64) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS termination_reason VARCHAR(64) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS stopped_at_step INTEGER NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS violation_policy_id VARCHAR(64) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS observability_status VARCHAR(32) NOT NULL DEFAULT 'FULL';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS observability_error TEXT NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS state VARCHAR(32) NOT NULL DEFAULT 'LIVE';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS project_id VARCHAR(64) NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'agent';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS provider_type VARCHAR(32) NOT NULL DEFAULT 'anthropic';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS risk_level VARCHAR(32) NOT NULL DEFAULT 'NORMAL';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS latency_bucket VARCHAR(32) NOT NULL DEFAULT 'OK';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS evidence_health VARCHAR(32) NOT NULL DEFAULT 'FLOWING';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS integrity_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN';",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS incident_count INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS policy_draft_count INTEGER NOT NULL DEFAULT 0;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS policy_violation BOOLEAN NOT NULL DEFAULT false;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS input_tokens INTEGER NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS output_tokens INTEGER NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS estimated_cost_usd DOUBLE PRECISION NULL;",
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS expected_latency_ms INTEGER NULL;",
    ]:
        conn.execute(text(stmt))


def _ensure_policy_snapshots(conn) -> None:
    # Table
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS policy_snapshots (
              id SERIAL PRIMARY KEY,
              snapshot_id VARCHAR(64) NOT NULL UNIQUE,
              tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
              policies_json TEXT NOT NULL,
              thresholds_json TEXT NOT NULL,
              content_hash VARCHAR(64) NOT NULL,
              threshold_snapshot_hash VARCHAR(64) NULL,
              policy_count INTEGER NOT NULL DEFAULT 0,
              policy_version VARCHAR(128) NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
    )

    # Columns (patch older drift)
    conn.execute(
        text(
            "ALTER TABLE policy_snapshots "
            "ADD COLUMN IF NOT EXISTS threshold_snapshot_hash VARCHAR(64) NULL;"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE policy_snapshots "
            "ADD COLUMN IF NOT EXISTS policy_version VARCHAR(128) NULL;"
        )
    )

    # Indexes
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_policy_snapshots_tenant_created "
            "ON policy_snapshots (tenant_id, created_at DESC);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_policy_snapshots_threshold_hash "
            "ON policy_snapshots (threshold_snapshot_hash);"
        )
    )

    # Immutability trigger
    conn.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION reject_policy_snapshot_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'policy_snapshots is immutable: UPDATE and DELETE are forbidden';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    conn.execute(text("DROP TRIGGER IF EXISTS policy_snapshots_immutable ON policy_snapshots;"))
    conn.execute(
        text(
            """
            CREATE TRIGGER policy_snapshots_immutable
            BEFORE UPDATE OR DELETE ON policy_snapshots
            FOR EACH ROW
            EXECUTE FUNCTION reject_policy_snapshot_mutation();
            """
        )
    )

    # Backfill threshold hash for existing rows (if any)
    conn.execute(
        text(
            """
            UPDATE policy_snapshots
            SET threshold_snapshot_hash = encode(sha256(thresholds_json::bytea), 'hex')
            WHERE threshold_snapshot_hash IS NULL;
            """
        )
    )


def _ensure_runs_policy_snapshot_column(conn) -> None:
    conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS policy_snapshot_id VARCHAR(64) NULL;"))
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_runs_policy_snapshot_id "
            "ON runs (policy_snapshot_id);"
        )
    )


def _ensure_retrieval_evidence(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS retrieval_evidence (
              id VARCHAR(36) PRIMARY KEY,
              tenant_id VARCHAR(100) NOT NULL,
              run_id VARCHAR(100) NOT NULL,
              plane_id VARCHAR(100) NOT NULL,
              connector_id VARCHAR(100) NOT NULL,
              action VARCHAR(50) NOT NULL,
              query_hash VARCHAR(64) NOT NULL,
              doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
              token_count INTEGER NOT NULL DEFAULT 0,
              policy_snapshot_id VARCHAR(100) NULL,
              requested_at TIMESTAMPTZ NOT NULL,
              completed_at TIMESTAMPTZ NULL,
              duration_ms INTEGER NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
    )

    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_retrieval_evidence_tenant_run "
            "ON retrieval_evidence (tenant_id, run_id);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_retrieval_evidence_query_hash "
            "ON retrieval_evidence (query_hash);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_retrieval_evidence_requested_at "
            "ON retrieval_evidence (requested_at);"
        )
    )

    conn.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION prevent_retrieval_evidence_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'retrieval_evidence is immutable. UPDATE and DELETE are forbidden. (GAP-058)';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    conn.execute(text("DROP TRIGGER IF EXISTS retrieval_evidence_immutable ON retrieval_evidence;"))
    conn.execute(
        text(
            """
            CREATE TRIGGER retrieval_evidence_immutable
            BEFORE UPDATE OR DELETE ON retrieval_evidence
            FOR EACH ROW
            EXECUTE FUNCTION prevent_retrieval_evidence_mutation();
            """
        )
    )
    conn.execute(
        text(
            """
            COMMENT ON TABLE retrieval_evidence IS
            'Immutable audit log for mediated data access (GAP-058). Every access through the mediation layer creates one record. SOC2 compliance.';
            """
        )
    )


def _ensure_knowledge_plane_registry(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS knowledge_plane_registry (
              plane_id VARCHAR(64) PRIMARY KEY,
              tenant_id VARCHAR(64) NOT NULL,
              plane_type VARCHAR(64) NOT NULL,
              plane_name VARCHAR(128) NOT NULL,
              lifecycle_state_value INTEGER NOT NULL DEFAULT 100,
              connector_type VARCHAR(64) NOT NULL,
              connector_id VARCHAR(64) NOT NULL,
              config JSONB NOT NULL DEFAULT '{}'::jsonb,
              created_by VARCHAR(64) NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              CONSTRAINT uq_kp_registry_tenant_type_name UNIQUE (tenant_id, plane_type, plane_name)
            );
            """
        )
    )

    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kp_registry_tenant_id ON knowledge_plane_registry (tenant_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kp_registry_plane_type ON knowledge_plane_registry (plane_type);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kp_registry_plane_name ON knowledge_plane_registry (plane_name);"))
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_kp_registry_lifecycle_state_value "
            "ON knowledge_plane_registry (lifecycle_state_value);"
        )
    )

    # Add check constraint if missing.
    conn.execute(
        text(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_kp_registry_state_value'
              ) THEN
                ALTER TABLE knowledge_plane_registry
                ADD CONSTRAINT ck_kp_registry_state_value
                CHECK (lifecycle_state_value IN (100,110,120,130,140,150,160,200,300,310,320,400,500));
              END IF;
            END $$;
            """
        )
    )


def main() -> int:
    _require_env("DATABASE_URL")

    from app.db import get_engine

    engine = get_engine()
    with engine.begin() as conn:
        _ensure_tenants(conn)
        _ensure_runs(conn)
        _ensure_policy_snapshots(conn)
        _ensure_runs_policy_snapshot_column(conn)
        _ensure_retrieval_evidence(conn)
        _ensure_knowledge_plane_registry(conn)

    print("bootstrap_knowledge_governance_tables: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
