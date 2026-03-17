"""Add email verification fields to accounts

Revision ID: 005_email_verification
Revises: 004_account_controls_campaigns
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005_email_verification"
down_revision: Union[str, None] = "004_account_controls_campaigns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("email_verified", sa.Boolean, server_default=sa.text("false"), nullable=False))
    op.add_column("accounts", sa.Column("email_verification_token", sa.String(36), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "email_verification_token")
    op.drop_column("accounts", "email_verified")
