"""Add cloud_credentials table and provider columns to scans

Revision ID: 003_cloud_credentials
Revises: 002_scoring_config
Create Date: 2026-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_cloud_credentials"
down_revision: Union[str, None] = "002_scoring_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_existing_tables():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def _get_existing_columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    existing = _get_existing_tables()

    if "cloud_credentials" not in existing:
        op.create_table(
            "cloud_credentials",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False),
            sa.Column("provider", sa.String(20), nullable=False),
            sa.Column("alias", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("added_at", sa.DateTime(timezone=True)),
            # AWS fields
            sa.Column("aws_access_key_id", sa.String(512), nullable=True),
            sa.Column("aws_secret_access_key", sa.String(512), nullable=True),
            sa.Column("aws_session_token", sa.Text(), nullable=True),
            sa.Column("aws_region", sa.String(50), nullable=True),
            sa.Column("aws_account_id", sa.String(20), nullable=True),
            # Azure fields
            sa.Column("azure_tenant_id", sa.String(512), nullable=True),
            sa.Column("azure_client_id", sa.String(512), nullable=True),
            sa.Column("azure_client_secret", sa.String(512), nullable=True),
            sa.Column("azure_subscription_id", sa.String(512), nullable=True),
        )
        op.create_index("ix_cloud_credentials_account_id", "cloud_credentials", ["account_id"])

    if "scans" in existing:
        existing_cols = _get_existing_columns("scans")
        with op.batch_alter_table("scans") as batch_op:
            if "provider" not in existing_cols:
                batch_op.add_column(sa.Column("provider", sa.String(20), server_default="aws"))
            if "cloud_credential_id" not in existing_cols:
                batch_op.add_column(
                    sa.Column("cloud_credential_id", sa.String(36), nullable=True)
                )


def downgrade() -> None:
    existing = _get_existing_tables()

    if "scans" in existing:
        existing_cols = _get_existing_columns("scans")
        with op.batch_alter_table("scans") as batch_op:
            if "cloud_credential_id" in existing_cols:
                batch_op.drop_column("cloud_credential_id")
            if "provider" in existing_cols:
                batch_op.drop_column("provider")

    if "cloud_credentials" in existing:
        op.drop_table("cloud_credentials")
