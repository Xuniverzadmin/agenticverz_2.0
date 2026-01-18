"""invitations_and_support_tickets

Revision ID: ce967f70c95d
Revises: 103_cus_integrations
Create Date: 2026-01-18 08:19:36.092997

PURPOSE:
    Creates tables for the Account domain user management and support features:
    - invitations: Token-based user invitations to tenants
    - support_tickets: Customer support tickets feeding into CRM workflow
    - Adds preferences_json column to users table

REFERENCE:
    - docs/architecture/accounts/ACCOUNTS_SECTION_AUDIT.md
    - docs/governance/part2/PART2_CRM_WORKFLOW_CHARTER.md
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce967f70c95d'
down_revision: Union[str, None] = '103_cus_integrations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add preferences_json column to users table
    op.add_column(
        'users',
        sa.Column('preferences_json', sa.String(), nullable=True)
    )

    # Create invitations table
    op.create_table(
        'invitations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('invited_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_invitations_tenant_id', 'invitations', ['tenant_id'])
    op.create_index('ix_invitations_email', 'invitations', ['email'])
    op.create_index('ix_invitations_token_hash', 'invitations', ['token_hash'])

    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=4000), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.Column('resolution', sa.String(length=4000), nullable=True),
        sa.Column('issue_event_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_support_tickets_tenant_id', 'support_tickets', ['tenant_id'])
    op.create_index('ix_support_tickets_user_id', 'support_tickets', ['user_id'])
    op.create_index('ix_support_tickets_status', 'support_tickets', ['status'])


def downgrade() -> None:
    # Drop support_tickets table
    op.drop_index('ix_support_tickets_status', table_name='support_tickets')
    op.drop_index('ix_support_tickets_user_id', table_name='support_tickets')
    op.drop_index('ix_support_tickets_tenant_id', table_name='support_tickets')
    op.drop_table('support_tickets')

    # Drop invitations table
    op.drop_index('ix_invitations_token_hash', table_name='invitations')
    op.drop_index('ix_invitations_email', table_name='invitations')
    op.drop_index('ix_invitations_tenant_id', table_name='invitations')
    op.drop_table('invitations')

    # Remove preferences_json column from users
    op.drop_column('users', 'preferences_json')
