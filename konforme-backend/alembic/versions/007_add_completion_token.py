"""Add completion_token to campaign_tasks

Revision ID: 007_completion_token
Revises: 006_users_table
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007_completion_token"
down_revision: Union[str, None] = "006_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("campaign_tasks", sa.Column("completion_token", sa.String(36), nullable=True))
    op.create_unique_constraint("uq_campaign_tasks_completion_token", "campaign_tasks", ["completion_token"])


def downgrade() -> None:
    op.drop_constraint("uq_campaign_tasks_completion_token", "campaign_tasks")
    op.drop_column("campaign_tasks", "completion_token")
