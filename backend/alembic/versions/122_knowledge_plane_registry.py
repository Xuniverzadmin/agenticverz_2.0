# Layer: L6 — Platform (Database Migration)
# Product: system-wide
# Reference: docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md
"""Add knowledge_plane_registry table (canonical governed plane SSOT)

Revision ID: 122_knowledge_plane_registry
Revises: 121_canary_reports
Create Date: 2026-02-08

This migration introduces a minimal, canonical SSOT for governed knowledge planes:
- immutable plane_id
- unique (tenant_id, plane_type, plane_name)
- lifecycle_state_value (GAP-089 ordered IntEnum value)
- connector binding by reference (no secrets)

This table is distinct from legacy/index-runtime "knowledge_planes" (118_w2_knowledge_planes).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "122_knowledge_plane_registry"
down_revision = "121_canary_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_plane_registry",
        sa.Column("plane_id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("plane_type", sa.String(64), nullable=False),
        sa.Column("plane_name", sa.String(128), nullable=False),
        sa.Column(
            "lifecycle_state_value",
            sa.Integer(),
            nullable=False,
            server_default="100",  # KnowledgePlaneLifecycleState.DRAFT.value
        ),
        sa.Column("connector_type", sa.String(64), nullable=False),
        sa.Column("connector_id", sa.String(64), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "plane_type", "plane_name", name="uq_kp_registry_tenant_type_name"),
    )

    op.create_index("ix_kp_registry_tenant_id", "knowledge_plane_registry", ["tenant_id"])
    op.create_index("ix_kp_registry_plane_type", "knowledge_plane_registry", ["plane_type"])
    op.create_index("ix_kp_registry_plane_name", "knowledge_plane_registry", ["plane_name"])
    op.create_index("ix_kp_registry_lifecycle_state_value", "knowledge_plane_registry", ["lifecycle_state_value"])

    # GAP-089 ordered state values (minimal guardrail).
    op.create_check_constraint(
        "ck_kp_registry_state_value",
        "knowledge_plane_registry",
        "lifecycle_state_value IN (100,110,120,130,140,150,160,200,300,310,320,400,500)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_kp_registry_state_value", "knowledge_plane_registry", type_="check")
    op.drop_index("ix_kp_registry_lifecycle_state_value", table_name="knowledge_plane_registry")
    op.drop_index("ix_kp_registry_plane_name", table_name="knowledge_plane_registry")
    op.drop_index("ix_kp_registry_plane_type", table_name="knowledge_plane_registry")
    op.drop_index("ix_kp_registry_tenant_id", table_name="knowledge_plane_registry")
    op.drop_table("knowledge_plane_registry")

