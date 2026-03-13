"""Add account_controls, control_campaigns, campaign_tasks tables

Revision ID: 004_account_controls_campaigns
Revises: 003_cloud_credentials
Create Date: 2026-03-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004_account_controls_campaigns"
down_revision: Union[str, None] = "003_cloud_credentials"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account_controls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), server_default="Not Started", nullable=False),
        sa.Column("owner", sa.String(200), server_default="", nullable=False),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, server_default="", nullable=False),
        sa.Column("is_country_specific", sa.Boolean, server_default="0", nullable=False),
        sa.Column("last_updated", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_id", "control_id", name="uq_account_controls_account_control"),
    )
    op.create_index("ix_account_controls_account_id", "account_controls", ["account_id"])

    op.create_table(
        "control_campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_id", sa.String(100), nullable=False),
        sa.Column("control_name", sa.String(300), server_default="", nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("deadline", sa.String(30), nullable=False),
        sa.Column("policy_content", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_control_campaigns_account_id", "control_campaigns", ["account_id"])

    op.create_table(
        "campaign_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("campaign_id", sa.String(36), sa.ForeignKey("control_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_id", sa.String(100), nullable=False),
        sa.Column("employee_name", sa.String(200), nullable=False),
        sa.Column("employee_email", sa.String(300), nullable=False),
        sa.Column("department", sa.String(200), server_default="", nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("sent_date", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("completed_date", sa.DateTime, nullable=True),
        sa.Column("deadline", sa.String(30), nullable=False),
        sa.Column("score", sa.Integer, nullable=True),
    )
    op.create_index("ix_campaign_tasks_campaign_id", "campaign_tasks", ["campaign_id"])


def downgrade() -> None:
    op.drop_table("campaign_tasks")
    op.drop_table("control_campaigns")
    op.drop_table("account_controls")
