"""project and asset entity

Revision ID: 0002_assets
Revises: 0001_init
Create Date: 2026-01-29
"""

import sqlalchemy as sa
from alembic import op


revision = "0002_assets"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_project_name", "project", ["name"], unique=True)

    op.create_table(
        "asset_entity",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=2048), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("project_id", "asset_type", "value", name="uq_asset_entity_key"),
    )
    op.create_index("ix_asset_entity_project_id", "asset_entity", ["project_id"])
    op.create_index("ix_asset_entity_asset_type", "asset_entity", ["asset_type"])


def downgrade() -> None:
    op.drop_index("ix_asset_entity_asset_type", table_name="asset_entity")
    op.drop_index("ix_asset_entity_project_id", table_name="asset_entity")
    op.drop_table("asset_entity")
    op.drop_index("ix_project_name", table_name="project")
    op.drop_table("project")
