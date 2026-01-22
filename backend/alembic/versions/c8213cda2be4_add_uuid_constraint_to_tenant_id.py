"""add_uuid_constraint_to_tenant_id

Revision ID: c8213cda2be4
Revises: 119_w2_mcp_servers
Create Date: 2026-01-21 18:21:24.434216

PURPOSE:
    Adds CHECK constraints to enforce valid UUID format on tenant_id columns.
    This prevents non-UUID tenant identifiers from being stored, ensuring
    the tenant resolver contract is enforced at the database level.

REFERENCE:
    - docs/architecture/DEMO_TENANT.md
    - app/auth/tenant_resolver.py

INVARIANT:
    Tenant identity must be a valid UUID. No string identifiers like
    'demo-tenant' or 'sdsr-tenant-e2e-004' are allowed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8213cda2be4'
down_revision: Union[str, None] = '119_w2_mcp_servers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# UUID regex pattern for PostgreSQL
# Matches: 11111111-1111-1111-1111-111111111111
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

# Tables with tenant_id columns that need UUID enforcement
TABLES_WITH_TENANT_ID = [
    'api_keys',
    'cus_integrations',
    'cus_llm_usage',
    'cus_usage_daily',
]


def upgrade() -> None:
    """Add CHECK constraints to enforce UUID format on tenant_id columns.

    NOTE: This migration will FAIL if there are existing rows with non-UUID
    tenant_id values. Run the cleanup SQL first:
    scripts/migrations/fix_demo_tenant_uuid.sql
    """
    for table in TABLES_WITH_TENANT_ID:
        constraint_name = f'{table}_tenant_id_uuid_check'

        # Add CHECK constraint to enforce UUID format
        op.execute(sa.text(f'''
            ALTER TABLE {table}
            ADD CONSTRAINT {constraint_name}
            CHECK (tenant_id ~ '{UUID_PATTERN}')
        '''))


def downgrade() -> None:
    """Remove UUID CHECK constraints from tenant_id columns."""
    for table in TABLES_WITH_TENANT_ID:
        constraint_name = f'{table}_tenant_id_uuid_check'

        op.execute(sa.text(f'''
            ALTER TABLE {table}
            DROP CONSTRAINT IF EXISTS {constraint_name}
        '''))
