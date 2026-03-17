"""Remove deprecated auth fields from accounts (now on users table)

Revision ID: 008_cleanup_account_auth
Revises: 007_completion_token
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008_cleanup_account_auth"
down_revision: Union[str, None] = "007_completion_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These columns are now on the users table
    op.drop_column("accounts", "password_hash")
    op.drop_column("accounts", "failed_login_attempts")
    op.drop_column("accounts", "locked_until")
    op.drop_column("accounts", "email_verification_token")


def downgrade() -> None:
    op.add_column("accounts", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("accounts", sa.Column("failed_login_attempts", sa.Integer, server_default="0"))
    op.add_column("accounts", sa.Column("locked_until", sa.DateTime, nullable=True))
    op.add_column("accounts", sa.Column("email_verification_token", sa.String(36), nullable=True))
