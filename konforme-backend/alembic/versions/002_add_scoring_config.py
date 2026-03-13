"""Add scoring_config column to accounts

Revision ID: 002_scoring_config
Revises: 001_countries
Create Date: 2026-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_scoring_config"
down_revision: Union[str, None] = "001_countries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "accounts" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("accounts")}
    if "scoring_config" not in existing_cols:
        with op.batch_alter_table("accounts") as batch_op:
            batch_op.add_column(sa.Column("scoring_config", sa.Text, nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "accounts" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("accounts")}
    if "scoring_config" in existing_cols:
        with op.batch_alter_table("accounts") as batch_op:
            batch_op.drop_column("scoring_config")
