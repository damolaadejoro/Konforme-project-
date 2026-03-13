"""Add country-specific NIS2 tables

Revision ID: 001_countries
Revises: None
Create Date: 2026-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_countries"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_existing_tables():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def _get_existing_columns(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    existing = _get_existing_tables()

    # --- countries ---
    if "countries" not in existing:
        op.create_table(
            "countries",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("code", sa.String(2), unique=True, nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("name_local", sa.String(100), nullable=True),
            sa.Column("transposition_status", sa.String(20), nullable=False, server_default="unknown"),
            sa.Column("transposition_law_name", sa.String(255), nullable=True),
            sa.Column("transposition_law_reference", sa.String(255), nullable=True),
            sa.Column("transposition_law_url", sa.Text, nullable=True),
            sa.Column("date_published", sa.Date, nullable=True),
            sa.Column("date_effective", sa.Date, nullable=True),
            sa.Column("competent_authority_name", sa.String(255), nullable=True),
            sa.Column("competent_authority_url", sa.Text, nullable=True),
            sa.Column("csirt_name", sa.String(255), nullable=True),
            sa.Column("csirt_url", sa.Text, nullable=True),
            sa.Column("research_confidence", sa.String(10), nullable=True),
            sa.Column("research_notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_countries_code", "countries", ["code"])

    # --- entity_tiers ---
    if "entity_tiers" not in existing:
        op.create_table(
            "entity_tiers",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("country_id", sa.String(36), sa.ForeignKey("countries.id", ondelete="CASCADE"), nullable=False),
            sa.Column("tier_key", sa.String(50), nullable=False),
            sa.Column("local_name", sa.String(255), nullable=True),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("sectors", sa.Text, server_default="[]"),
            sa.Column("size_thresholds", sa.Text, server_default="{}"),
            sa.Column("obligations", sa.Text, server_default="{}"),
            sa.Column("penalties", sa.Text, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("country_id", "tier_key", name="uq_entity_tiers_country_tier"),
        )
        op.create_index("ix_entity_tiers_country_id", "entity_tiers", ["country_id"])

    # --- country_controls ---
    if "country_controls" not in existing:
        op.create_table(
            "country_controls",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("country_id", sa.String(36), sa.ForeignKey("countries.id", ondelete="CASCADE"), nullable=False),
            sa.Column("control_id", sa.String(50), nullable=False),
            sa.Column("eu_article", sa.String(20), nullable=True),
            sa.Column("national_legal_reference", sa.String(255), nullable=True),
            sa.Column("national_specification", sa.Text, nullable=True),
            sa.Column("goes_beyond_eu", sa.Boolean, server_default=sa.text("0")),
            sa.Column("applies_to_tiers", sa.Text, server_default='["essential", "important"]'),
            sa.Column("additional_requirements", sa.Text, server_default="[]"),
            sa.Column("is_mandatory", sa.Boolean, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("country_id", "control_id", name="uq_country_controls_country_control"),
        )
        op.create_index("ix_country_controls_country_id", "country_controls", ["country_id"])

    # --- country_deadlines ---
    if "country_deadlines" not in existing:
        op.create_table(
            "country_deadlines",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("country_id", sa.String(36), sa.ForeignKey("countries.id", ondelete="CASCADE"), nullable=False),
            sa.Column("deadline_date", sa.Date, nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("applies_to_tiers", sa.Text, server_default="[]"),
            sa.Column("legal_reference", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_country_deadlines_country_id", "country_deadlines", ["country_id"])

    # --- country_assessment_questions ---
    if "country_assessment_questions" not in existing:
        op.create_table(
            "country_assessment_questions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("country_id", sa.String(36), sa.ForeignKey("countries.id", ondelete="CASCADE"), nullable=False),
            sa.Column("base_question_id", sa.String(50), nullable=True),
            sa.Column("question_text", sa.Text, nullable=False),
            sa.Column("help_text", sa.Text, nullable=True),
            sa.Column("eu_article", sa.String(20), nullable=True),
            sa.Column("national_legal_reference", sa.String(255), nullable=True),
            sa.Column("applies_to_tiers", sa.Text, server_default='["essential", "important"]'),
            sa.Column("domain", sa.String(100), nullable=True),
            sa.Column("weight", sa.Float, server_default="1.0"),
            sa.Column("is_additional", sa.Boolean, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("country_id", "base_question_id", name="uq_country_aq_country_question"),
        )
        op.create_index("ix_country_aq_country_id", "country_assessment_questions", ["country_id"])

    # --- Add country_id and entity_tier_id to accounts (skip if table doesn't exist yet) ---
    if "accounts" in existing:
        existing_cols = _get_existing_columns("accounts")
        with op.batch_alter_table("accounts") as batch_op:
            if "country_id" not in existing_cols:
                batch_op.add_column(sa.Column("country_id", sa.String(36), nullable=True))
                batch_op.create_foreign_key("fk_accounts_country_id", "countries", ["country_id"], ["id"])
            if "entity_tier_id" not in existing_cols:
                batch_op.add_column(sa.Column("entity_tier_id", sa.String(36), nullable=True))
                batch_op.create_foreign_key("fk_accounts_entity_tier_id", "entity_tiers", ["entity_tier_id"], ["id"])


def downgrade() -> None:
    existing = _get_existing_tables()

    # Remove columns from accounts (batch mode rebuilds the table, removing FKs automatically)
    if "accounts" in existing:
        existing_cols = _get_existing_columns("accounts")
        cols_to_drop = [c for c in ["entity_tier_id", "country_id"] if c in existing_cols]
        if cols_to_drop:
            with op.batch_alter_table("accounts") as batch_op:
                for col in cols_to_drop:
                    batch_op.drop_column(col)

    # Drop tables in reverse dependency order
    for table in ["country_assessment_questions", "country_deadlines", "country_controls", "entity_tiers", "countries"]:
        if table in existing:
            op.drop_table(table)
