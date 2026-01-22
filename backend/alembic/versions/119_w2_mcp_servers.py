# Layer: L6 — Platform (Database Migration)
# Product: system-wide
# Reference: GAP-170 (T4 MCP Migration)
"""Add mcp_servers and mcp_tools tables for T4 MCP control plane

Revision ID: 119_w2_mcp_servers
Revises: 118_w2_knowledge_planes
Create Date: 2026-01-21

Reference: GAP-170 (T4 MCP Migration), GAP_IMPLEMENTATION_PLAN_V2.md

This migration creates tables for the Model Context Protocol (MCP) control plane:
- mcp_servers: Registered external MCP servers
- mcp_tools: Tools exposed by MCP servers
- mcp_tool_invocations: Audit trail of tool invocations

Purpose:
- Register and manage external MCP servers
- Discover and catalog available tools
- Policy-gate tool access
- Audit all tool invocations for compliance
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "119_w2_mcp_servers"
down_revision = "118_w2_knowledge_planes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Create mcp_servers table (GAP-170)
    # =========================================================================
    op.create_table(
        "mcp_servers",
        # Primary key
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("server_id", sa.String(64), nullable=False, unique=True, index=True),
        # Identity
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Connection
        sa.Column(
            "url",
            sa.String(512),
            nullable=False,
            comment="Server URL (http/https/stdio)",
        ),
        sa.Column(
            "transport",
            sa.String(32),
            nullable=False,
            server_default="http",
            comment="Transport: http, https, stdio, sse",
        ),
        sa.Column(
            "auth_type",
            sa.String(32),
            nullable=True,
            comment="Auth type: none, api_key, oauth, bearer",
        ),
        sa.Column(
            "credential_id",
            sa.String(64),
            nullable=True,
            comment="Reference to credential vault",
        ),
        # Status
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
            comment="Status: pending, active, degraded, offline, disabled",
        ),
        sa.Column(
            "last_health_check_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "health_check_failures",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        # Capabilities
        sa.Column(
            "capabilities",
            JSONB,
            nullable=False,
            server_default="[]",
            comment="List of capabilities: tools, resources, prompts",
        ),
        sa.Column(
            "protocol_version",
            sa.String(16),
            nullable=True,
            comment="MCP protocol version",
        ),
        # Discovery
        sa.Column(
            "tool_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "resource_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_discovery_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        # Policy
        sa.Column(
            "requires_approval",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether tool invocations require approval",
        ),
        sa.Column(
            "default_policy_id",
            sa.String(64),
            nullable=True,
            comment="Default policy for tool invocations",
        ),
        # Rate limiting
        sa.Column(
            "rate_limit_requests",
            sa.Integer(),
            nullable=True,
            comment="Max requests per minute",
        ),
        sa.Column(
            "rate_limit_window_seconds",
            sa.Integer(),
            nullable=True,
            server_default="60",
        ),
        # Metadata
        sa.Column("tags", JSONB, nullable=True, server_default="[]"),
        sa.Column("metadata", JSONB, nullable=True),
        # Timestamps
        sa.Column(
            "registered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create indexes
    op.create_index(
        "ix_mcp_servers_tenant_name",
        "mcp_servers",
        ["tenant_id", "name"],
        unique=True,
    )
    op.create_index(
        "ix_mcp_servers_status",
        "mcp_servers",
        ["status"],
    )
    op.create_index(
        "ix_mcp_servers_tenant_status",
        "mcp_servers",
        ["tenant_id", "status"],
    )

    # Create check constraints
    op.create_check_constraint(
        "ck_mcp_servers_transport",
        "mcp_servers",
        "transport IN ('http', 'https', 'stdio', 'sse', 'websocket')",
    )
    op.create_check_constraint(
        "ck_mcp_servers_status",
        "mcp_servers",
        "status IN ('pending', 'active', 'degraded', 'offline', 'disabled', 'error')",
    )
    op.create_check_constraint(
        "ck_mcp_servers_auth_type",
        "mcp_servers",
        "auth_type IS NULL OR auth_type IN ('none', 'api_key', 'oauth', 'bearer', 'basic')",
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE mcp_servers IS
        'Registered MCP servers (GAP-170). Manages external tool servers with discovery, health checking, and policy gating.';
    """)

    # =========================================================================
    # Create mcp_tools table
    # =========================================================================
    op.create_table(
        "mcp_tools",
        # Primary key
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tool_id", sa.String(64), nullable=False, unique=True, index=True),
        # Identity
        sa.Column(
            "server_id",
            sa.String(64),
            sa.ForeignKey("mcp_servers.server_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Tool definition
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Schema
        sa.Column(
            "input_schema",
            JSONB,
            nullable=False,
            comment="JSON Schema for tool inputs",
        ),
        sa.Column(
            "output_schema",
            JSONB,
            nullable=True,
            comment="JSON Schema for tool outputs (if known)",
        ),
        # Policy
        sa.Column(
            "requires_policy",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether invocation requires policy check",
        ),
        sa.Column(
            "policy_id",
            sa.String(64),
            nullable=True,
            comment="Specific policy for this tool",
        ),
        sa.Column(
            "risk_level",
            sa.String(16),
            nullable=False,
            server_default="medium",
            comment="Risk level: low, medium, high, critical",
        ),
        # Status
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        # Usage tracking
        sa.Column(
            "invocation_count",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_invoked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "failure_count",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        # Metadata
        sa.Column("metadata", JSONB, nullable=True),
        # Timestamps
        sa.Column(
            "discovered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create indexes
    op.create_index(
        "ix_mcp_tools_server_name",
        "mcp_tools",
        ["server_id", "name"],
        unique=True,
    )
    op.create_index(
        "ix_mcp_tools_tenant",
        "mcp_tools",
        ["tenant_id"],
    )
    op.create_index(
        "ix_mcp_tools_enabled",
        "mcp_tools",
        ["enabled", "server_id"],
    )

    # Create check constraints
    op.create_check_constraint(
        "ck_mcp_tools_risk_level",
        "mcp_tools",
        "risk_level IN ('low', 'medium', 'high', 'critical')",
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE mcp_tools IS
        'Tools exposed by MCP servers (GAP-170). Discovered via MCP protocol with policy and risk tagging.';
    """)

    # =========================================================================
    # Create mcp_tool_invocations for audit trail
    # =========================================================================
    op.create_table(
        "mcp_tool_invocations",
        # Primary key
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("invocation_id", sa.String(64), nullable=False, unique=True, index=True),
        # References
        sa.Column(
            "tool_id",
            sa.String(64),
            sa.ForeignKey("mcp_tools.tool_id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("server_id", sa.String(64), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Context
        sa.Column("run_id", sa.String(100), nullable=True, index=True),
        sa.Column("step_index", sa.Integer(), nullable=True),
        sa.Column("actor_id", sa.String(100), nullable=True),
        sa.Column("actor_type", sa.String(32), nullable=False, server_default="machine"),
        # Invocation details
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column(
            "input_hash",
            sa.String(64),
            nullable=False,
            comment="SHA256 of input (for deduplication)",
        ),
        sa.Column(
            "input_preview",
            sa.Text(),
            nullable=True,
            comment="Truncated input for debugging",
        ),
        # Policy
        sa.Column("policy_id", sa.String(64), nullable=True),
        sa.Column("policy_snapshot_id", sa.String(64), nullable=True),
        sa.Column(
            "policy_decision",
            sa.String(32),
            nullable=False,
            server_default="allowed",
            comment="Policy decision: allowed, blocked, flagged",
        ),
        sa.Column("policy_reason", sa.Text(), nullable=True),
        # Result
        sa.Column(
            "outcome",
            sa.String(32),
            nullable=False,
            comment="Outcome: success, failure, timeout, blocked",
        ),
        sa.Column("output_hash", sa.String(64), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timing
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        # Timestamps
        sa.Column(
            "invoked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create indexes
    op.create_index(
        "ix_mcp_tool_invocations_tenant_invoked",
        "mcp_tool_invocations",
        ["tenant_id", sa.text("invoked_at DESC")],
    )
    op.create_index(
        "ix_mcp_tool_invocations_run",
        "mcp_tool_invocations",
        ["run_id"],
        postgresql_where=sa.text("run_id IS NOT NULL"),
    )
    op.create_index(
        "ix_mcp_tool_invocations_outcome",
        "mcp_tool_invocations",
        ["outcome"],
        postgresql_where=sa.text("outcome IN ('failure', 'blocked')"),
    )

    # Create check constraints
    op.create_check_constraint(
        "ck_mcp_tool_invocations_policy_decision",
        "mcp_tool_invocations",
        "policy_decision IN ('allowed', 'blocked', 'flagged', 'pending')",
    )
    op.create_check_constraint(
        "ck_mcp_tool_invocations_outcome",
        "mcp_tool_invocations",
        "outcome IN ('success', 'failure', 'timeout', 'blocked', 'pending')",
    )
    op.create_check_constraint(
        "ck_mcp_tool_invocations_actor_type",
        "mcp_tool_invocations",
        "actor_type IN ('human', 'machine', 'system')",
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE mcp_tool_invocations IS
        'Audit trail of MCP tool invocations (GAP-170). Immutable record for compliance and debugging.';
    """)

    # Create immutability trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_mcp_invocation_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'mcp_tool_invocations is immutable. UPDATE and DELETE are forbidden. (GAP-170)';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER mcp_tool_invocations_immutable
            BEFORE UPDATE OR DELETE ON mcp_tool_invocations
            FOR EACH ROW
            EXECUTE FUNCTION prevent_mcp_invocation_mutation();
    """)


def downgrade() -> None:
    # Drop mcp_tool_invocations
    op.execute("DROP TRIGGER IF EXISTS mcp_tool_invocations_immutable ON mcp_tool_invocations;")
    op.execute("DROP FUNCTION IF EXISTS prevent_mcp_invocation_mutation();")
    op.drop_constraint("ck_mcp_tool_invocations_actor_type", "mcp_tool_invocations", type_="check")
    op.drop_constraint("ck_mcp_tool_invocations_outcome", "mcp_tool_invocations", type_="check")
    op.drop_constraint("ck_mcp_tool_invocations_policy_decision", "mcp_tool_invocations", type_="check")
    op.drop_index("ix_mcp_tool_invocations_outcome", table_name="mcp_tool_invocations")
    op.drop_index("ix_mcp_tool_invocations_run", table_name="mcp_tool_invocations")
    op.drop_index("ix_mcp_tool_invocations_tenant_invoked", table_name="mcp_tool_invocations")
    op.drop_table("mcp_tool_invocations")

    # Drop mcp_tools
    op.drop_constraint("ck_mcp_tools_risk_level", "mcp_tools", type_="check")
    op.drop_index("ix_mcp_tools_enabled", table_name="mcp_tools")
    op.drop_index("ix_mcp_tools_tenant", table_name="mcp_tools")
    op.drop_index("ix_mcp_tools_server_name", table_name="mcp_tools")
    op.drop_table("mcp_tools")

    # Drop mcp_servers
    op.drop_constraint("ck_mcp_servers_auth_type", "mcp_servers", type_="check")
    op.drop_constraint("ck_mcp_servers_status", "mcp_servers", type_="check")
    op.drop_constraint("ck_mcp_servers_transport", "mcp_servers", type_="check")
    op.drop_index("ix_mcp_servers_tenant_status", table_name="mcp_servers")
    op.drop_index("ix_mcp_servers_status", table_name="mcp_servers")
    op.drop_index("ix_mcp_servers_tenant_name", table_name="mcp_servers")
    op.drop_table("mcp_servers")
