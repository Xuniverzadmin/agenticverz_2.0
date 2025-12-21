"""M24: Customer Onboarding - OAuth & Email Verification

Adds OAuth provider support and email verification fields to users table.

Columns added to users:
- oauth_provider: Provider name (google, azure, email)
- oauth_provider_id: Provider's user ID
- email_verified: Email verification status
- email_verified_at: When email was verified

Revision ID: 040_m24_onboarding
Revises: 039_m23_user_tracking
Create Date: 2024-12-21
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "040_m24_onboarding"
down_revision = "039_m23_user_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add OAuth/email verification columns to users table
    # Check if users table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "users" in inspector.get_table_names():
        existing_columns = [col["name"] for col in inspector.get_columns("users")]

        if "oauth_provider" not in existing_columns:
            op.add_column(
                "users",
                sa.Column(
                    "oauth_provider", sa.String(50), nullable=True, comment="OAuth provider: google, azure, email"
                ),
            )

        if "oauth_provider_id" not in existing_columns:
            op.add_column(
                "users",
                sa.Column("oauth_provider_id", sa.String(255), nullable=True, comment="OAuth provider's user ID"),
            )

        if "email_verified" not in existing_columns:
            op.add_column(
                "users",
                sa.Column(
                    "email_verified",
                    sa.Boolean(),
                    nullable=False,
                    server_default="false",
                    comment="Whether email has been verified",
                ),
            )

        if "email_verified_at" not in existing_columns:
            op.add_column(
                "users",
                sa.Column(
                    "email_verified_at", sa.DateTime(timezone=True), nullable=True, comment="When email was verified"
                ),
            )

        # Create index for oauth provider lookup
        try:
            op.create_index(
                "ix_users_oauth_provider",
                "users",
                ["oauth_provider", "oauth_provider_id"],
                unique=False,
            )
        except Exception:
            pass  # Index may already exist


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "users" in inspector.get_table_names():
        existing_columns = [col["name"] for col in inspector.get_columns("users")]

        # Drop index first
        try:
            op.drop_index("ix_users_oauth_provider", table_name="users")
        except Exception:
            pass

        # Drop columns
        if "email_verified_at" in existing_columns:
            op.drop_column("users", "email_verified_at")

        if "email_verified" in existing_columns:
            op.drop_column("users", "email_verified")

        if "oauth_provider_id" in existing_columns:
            op.drop_column("users", "oauth_provider_id")

        if "oauth_provider" in existing_columns:
            op.drop_column("users", "oauth_provider")
