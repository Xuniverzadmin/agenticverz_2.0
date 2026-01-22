# Layer: L6 — Platform (Database Migration)
# Product: system-wide
# Reference: GAP-169 (T4 Knowledge Migration)
"""Add knowledge_planes and related tables for T4 governance

Revision ID: 118_w2_knowledge_planes
Revises: 117_w2_budget_envelopes
Create Date: 2026-01-21

Reference: GAP-169 (T4 Knowledge Migration), GAP_IMPLEMENTATION_PLAN_V2.md

This migration creates the knowledge_planes table for T4 (Domain Engines) tier.
Knowledge planes represent tenant-specific knowledge graphs that organize and
index content from multiple sources.

Purpose:
- Persist knowledge plane definitions and status
- Track knowledge sources and their ingestion state
- Store indexing metadata and statistics
- Support lifecycle state transitions
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY

# revision identifiers
revision = "118_w2_knowledge_planes"
down_revision = "117_w2_budget_envelopes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Create knowledge_planes table (GAP-169)
    # =========================================================================
    op.create_table(
        "knowledge_planes",
        # Primary key
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plane_id", sa.String(64), nullable=False, unique=True, index=True),
        # Identity
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Status (lifecycle)
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="draft",
            comment="Lifecycle status: draft, pending_verify, verified, ingesting, indexed, classified, pending_activate, active, pending_deactivate, deactivated, archived, purged, error",
        ),
        sa.Column(
            "status_reason",
            sa.Text(),
            nullable=True,
            comment="Reason for current status (especially for error states)",
        ),
        sa.Column(
            "last_transition_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="When the last status transition occurred",
        ),
        # Configuration
        sa.Column(
            "embedding_model",
            sa.String(64),
            nullable=False,
            server_default="text-embedding-ada-002",
        ),
        sa.Column(
            "embedding_dimension",
            sa.Integer(),
            nullable=False,
            server_default="1536",
        ),
        sa.Column(
            "chunk_size",
            sa.Integer(),
            nullable=False,
            server_default="512",
            comment="Default chunk size for text splitting",
        ),
        sa.Column(
            "chunk_overlap",
            sa.Integer(),
            nullable=False,
            server_default="50",
            comment="Overlap between chunks",
        ),
        # Vector store reference
        sa.Column(
            "vector_connector_id",
            sa.String(64),
            nullable=True,
            comment="ID of the vector connector used for storage",
        ),
        sa.Column(
            "vector_collection_name",
            sa.String(128),
            nullable=True,
            comment="Name of the collection in vector store",
        ),
        # Statistics
        sa.Column(
            "node_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "document_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_tokens",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_bytes",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        # Indexing metadata
        sa.Column(
            "last_indexed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "indexing_started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "indexing_duration_ms",
            sa.Integer(),
            nullable=True,
        ),
        # Classification metadata (GAP-161)
        sa.Column(
            "sensitivity_level",
            sa.String(32),
            nullable=True,
            comment="Sensitivity: public, internal, confidential, restricted",
        ),
        sa.Column(
            "pii_detected",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "classification_metadata",
            JSONB,
            nullable=True,
            comment="Classification details including PII types found",
        ),
        # Tags and metadata
        sa.Column("tags", JSONB, nullable=True, server_default="[]"),
        sa.Column("metadata", JSONB, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
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
        "ix_knowledge_planes_tenant_name",
        "knowledge_planes",
        ["tenant_id", "name"],
        unique=True,
    )
    op.create_index(
        "ix_knowledge_planes_status",
        "knowledge_planes",
        ["status"],
    )
    op.create_index(
        "ix_knowledge_planes_tenant_status",
        "knowledge_planes",
        ["tenant_id", "status"],
    )

    # Create check constraints
    op.create_check_constraint(
        "ck_knowledge_planes_status",
        "knowledge_planes",
        """status IN (
            'draft', 'pending_verify', 'verified', 'ingesting', 'indexed',
            'classified', 'pending_activate', 'active', 'pending_deactivate',
            'deactivated', 'archived', 'purged', 'error'
        )""",
    )
    op.create_check_constraint(
        "ck_knowledge_planes_sensitivity",
        "knowledge_planes",
        "sensitivity_level IS NULL OR sensitivity_level IN ('public', 'internal', 'confidential', 'restricted')",
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE knowledge_planes IS
        'T4 knowledge plane definitions (GAP-169). Represents tenant knowledge graphs with lifecycle management.';
    """)

    # =========================================================================
    # Create knowledge_sources table for tracking data sources
    # =========================================================================
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column(
            "plane_id",
            sa.String(64),
            sa.ForeignKey("knowledge_planes.plane_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Source definition
        sa.Column(
            "source_type",
            sa.String(32),
            nullable=False,
            comment="Type: http, sql, file, vector, manual",
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Configuration
        sa.Column(
            "connector_id",
            sa.String(64),
            nullable=True,
            comment="ID of the connector used for this source",
        ),
        sa.Column(
            "config",
            JSONB,
            nullable=True,
            comment="Source-specific configuration",
        ),
        sa.Column(
            "credential_id",
            sa.String(64),
            nullable=True,
            comment="Reference to credential vault",
        ),
        # Ingestion state
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
            comment="Status: pending, ingesting, ingested, error, disabled",
        ),
        sa.Column(
            "last_ingested_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        # Statistics
        sa.Column(
            "document_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "bytes_ingested",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        # Schedule
        sa.Column(
            "sync_schedule",
            sa.String(64),
            nullable=True,
            comment="Cron expression for sync schedule",
        ),
        sa.Column(
            "next_sync_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
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
        "ix_knowledge_sources_plane_status",
        "knowledge_sources",
        ["plane_id", "status"],
    )

    # Create check constraints
    op.create_check_constraint(
        "ck_knowledge_sources_type",
        "knowledge_sources",
        "source_type IN ('http', 'sql', 'file', 'vector', 'manual', 's3', 'gcs')",
    )
    op.create_check_constraint(
        "ck_knowledge_sources_status",
        "knowledge_sources",
        "status IN ('pending', 'ingesting', 'ingested', 'error', 'disabled')",
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE knowledge_sources IS
        'Data sources for knowledge planes (GAP-169). Tracks ingestion state and configuration per source.';
    """)

    # =========================================================================
    # Create knowledge_lifecycle_transitions for audit trail
    # =========================================================================
    op.create_table(
        "knowledge_lifecycle_transitions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("transition_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column(
            "plane_id",
            sa.String(64),
            sa.ForeignKey("knowledge_planes.plane_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Transition details
        sa.Column("from_status", sa.String(32), nullable=False),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("trigger", sa.String(64), nullable=False, comment="What triggered the transition"),
        sa.Column("actor_id", sa.String(100), nullable=True),
        sa.Column("actor_type", sa.String(32), nullable=False, server_default="system"),
        # Execution details
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        # Evidence
        sa.Column("evidence", JSONB, nullable=True),
        # Timestamps
        sa.Column(
            "started_at",
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
        "ix_knowledge_lifecycle_plane_started",
        "knowledge_lifecycle_transitions",
        ["plane_id", sa.text("started_at DESC")],
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE knowledge_lifecycle_transitions IS
        'Audit trail for knowledge plane lifecycle transitions (GAP-169). Immutable record of all status changes.';
    """)

    # Create immutability trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_lifecycle_transition_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'knowledge_lifecycle_transitions is immutable. UPDATE and DELETE are forbidden. (GAP-169)';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER lifecycle_transitions_immutable
            BEFORE UPDATE OR DELETE ON knowledge_lifecycle_transitions
            FOR EACH ROW
            EXECUTE FUNCTION prevent_lifecycle_transition_mutation();
    """)


def downgrade() -> None:
    # Drop knowledge_lifecycle_transitions
    op.execute("DROP TRIGGER IF EXISTS lifecycle_transitions_immutable ON knowledge_lifecycle_transitions;")
    op.execute("DROP FUNCTION IF EXISTS prevent_lifecycle_transition_mutation();")
    op.drop_index("ix_knowledge_lifecycle_plane_started", table_name="knowledge_lifecycle_transitions")
    op.drop_table("knowledge_lifecycle_transitions")

    # Drop knowledge_sources
    op.drop_constraint("ck_knowledge_sources_status", "knowledge_sources", type_="check")
    op.drop_constraint("ck_knowledge_sources_type", "knowledge_sources", type_="check")
    op.drop_index("ix_knowledge_sources_plane_status", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")

    # Drop knowledge_planes
    op.drop_constraint("ck_knowledge_planes_sensitivity", "knowledge_planes", type_="check")
    op.drop_constraint("ck_knowledge_planes_status", "knowledge_planes", type_="check")
    op.drop_index("ix_knowledge_planes_tenant_status", table_name="knowledge_planes")
    op.drop_index("ix_knowledge_planes_status", table_name="knowledge_planes")
    op.drop_index("ix_knowledge_planes_tenant_name", table_name="knowledge_planes")
    op.drop_table("knowledge_planes")
