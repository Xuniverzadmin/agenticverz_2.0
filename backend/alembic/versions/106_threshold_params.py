"""Add params JSONB column to limits table for threshold configuration

Revision ID: 106_threshold_params
Revises: 105_attribution_check_constraints
Create Date: 2026-01-18

PURPOSE:
    Adds a `params` JSONB column to the limits table to support
    customer-configurable execution thresholds for LLM runs.

SCHEMA CHANGE:
    limits.params JSONB NOT NULL DEFAULT '{}'

CANONICAL PARAM SCHEMA:
    {
        "max_execution_time_ms": number (1000-300000),
        "max_tokens": number (256-200000),
        "max_cost_usd": number (0-100),
        "failure_signal": boolean
    }

SAFE DEFAULTS:
    When params is empty {}, the LLMRunThresholdResolver uses:
    - max_execution_time_ms: 60000 (60s)
    - max_tokens: 8192
    - max_cost_usd: 1.00
    - failure_signal: true

REFERENCE:
    - Policies → Limits → Thresholds → Set Params panel
    - docs/architecture/limits/THRESHOLD_PARAMS_CONTRACT.md
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers
revision = "106_threshold_params"
down_revision = "105_attribution_check_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add params column with safe default
    op.add_column(
        "limits",
        sa.Column(
            "params",
            JSONB,
            nullable=False,
            server_default="{}",
            comment="Threshold configuration params (JSONB)"
        )
    )

    # Add index for efficient querying of threshold limits
    op.create_index(
        "idx_limits_category_threshold",
        "limits",
        ["tenant_id", "limit_category"],
        postgresql_where=sa.text("limit_category = 'THRESHOLD' AND status = 'ACTIVE'")
    )

    # Add index for scope-based resolution
    op.create_index(
        "idx_limits_scope_resolution",
        "limits",
        ["tenant_id", "scope", "scope_id", "limit_category"],
        postgresql_where=sa.text("status = 'ACTIVE'")
    )


def downgrade() -> None:
    op.drop_index("idx_limits_scope_resolution", table_name="limits")
    op.drop_index("idx_limits_category_threshold", table_name="limits")
    op.drop_column("limits", "params")
