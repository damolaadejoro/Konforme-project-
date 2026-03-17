"""Add users table and migrate account auth data

Revision ID: 006_users_table
Revises: 005_email_verification
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006_users_table"
down_revision: Union[str, None] = "005_email_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), server_default="member", nullable=False),
        sa.Column("email_verified", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("email_verification_token", sa.String(36), nullable=True),
        sa.Column("invite_token", sa.String(36), nullable=True, unique=True),
        sa.Column("invite_accepted_at", sa.DateTime, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer, server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_account_id", "users", ["account_id"])

    # Migrate existing accounts to users (each account gets an owner user)
    # Uses gen_random_uuid() which is available in PostgreSQL 13+
    op.execute("""
        INSERT INTO users (id, account_id, name, email, password_hash, role, email_verified, email_verification_token, is_active, created_at, updated_at)
        SELECT
            gen_random_uuid()::text,
            id,
            name,
            email,
            password_hash,
            'owner',
            COALESCE(email_verified, false),
            email_verification_token,
            COALESCE(is_active, true),
            COALESCE(connected_at, now()),
            now()
        FROM accounts
    """)


def downgrade() -> None:
    op.drop_table("users")
