"""merge_onboarding_state

Revision ID: 67c9bc65b616
Revises: 080_trace_archival_columns, 081_tenant_onboarding_state
Create Date: 2026-01-12 12:41:51.030938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67c9bc65b616'
down_revision: Union[str, None] = ('080_trace_archival_columns', '081_tenant_onboarding_state')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
