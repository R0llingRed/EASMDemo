"""web assets table

Revision ID: 0004_web_assets
Revises: 0003_scan_tasks
Create Date: 2026-01-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_web_assets"
down_revision = "0003_scan_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "web_asset",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column(
            "subdomain_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subdomain.id"),
            nullable=True,
        ),
        sa.Column(
            "ip_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_address.id"),
            nullable=True,
        ),
        sa.Column(
            "port_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("port.id"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("content_length", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("server", sa.String(length=255), nullable=True),
        sa.Column("technologies", sa.dialects.postgresql.JSONB(), server_default="[]"),
        sa.Column("fingerprints", sa.dialects.postgresql.JSONB(), server_default="[]"),
        sa.Column("headers", sa.dialects.postgresql.JSONB(), server_default="{}"),
        sa.Column("screenshot_path", sa.String(length=512), nullable=True),
        sa.Column("response_hash", sa.String(length=64), nullable=True),
        sa.Column("is_alive", sa.Boolean(), server_default="true"),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "url", name="uq_web_asset_key"),
    )
    op.create_index("ix_web_asset_project_id", "web_asset", ["project_id"])
    op.create_index("ix_web_asset_url", "web_asset", ["url"])


def downgrade() -> None:
    op.drop_index("ix_web_asset_url", table_name="web_asset")
    op.drop_index("ix_web_asset_project_id", table_name="web_asset")
    op.drop_table("web_asset")
