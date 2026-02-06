"""0010_js_api_deep_analysis

Revision ID: 0010_js_api_deep_analysis
Revises: 0009
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0010_js_api_deep_analysis"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "js_asset",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("web_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("script_url", sa.String(length=2048), nullable=False),
        sa.Column("script_type", sa.String(length=20), nullable=False, server_default="external"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("scan_metadata", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["web_asset_id"], ["web_asset.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "script_url", "content_hash", name="uq_js_asset_key"),
    )
    op.create_index("ix_js_asset_project_id", "js_asset", ["project_id"])
    op.create_index("ix_js_asset_web_asset_id", "js_asset", ["web_asset_id"])
    op.create_index("ix_js_asset_content_hash", "js_asset", ["content_hash"])

    op.create_table(
        "api_endpoint",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("js_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("endpoint", sa.String(length=2048), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False, server_default="GET"),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="js_analysis"),
        sa.Column("requires_auth", sa.Boolean(), nullable=True),
        sa.Column("risk_tags", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("evidence", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["js_asset_id"], ["js_asset.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "endpoint", "method", name="uq_api_endpoint_key"),
    )
    op.create_index("ix_api_endpoint_project_id", "api_endpoint", ["project_id"])
    op.create_index("ix_api_endpoint_js_asset_id", "api_endpoint", ["js_asset_id"])
    op.create_index("ix_api_endpoint_method", "api_endpoint", ["method"])
    op.create_index("ix_api_endpoint_host", "api_endpoint", ["host"])

    op.create_table(
        "api_risk_finding",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["endpoint_id"], ["api_endpoint.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "endpoint_id", "rule_name", name="uq_api_risk_rule_key"),
    )
    op.create_index("ix_api_risk_finding_project_id", "api_risk_finding", ["project_id"])
    op.create_index("ix_api_risk_finding_endpoint_id", "api_risk_finding", ["endpoint_id"])
    op.create_index("ix_api_risk_finding_severity", "api_risk_finding", ["severity"])
    op.create_index("ix_api_risk_finding_status", "api_risk_finding", ["status"])


def downgrade() -> None:
    op.drop_index("ix_api_risk_finding_status", table_name="api_risk_finding")
    op.drop_index("ix_api_risk_finding_severity", table_name="api_risk_finding")
    op.drop_index("ix_api_risk_finding_endpoint_id", table_name="api_risk_finding")
    op.drop_index("ix_api_risk_finding_project_id", table_name="api_risk_finding")
    op.drop_table("api_risk_finding")

    op.drop_index("ix_api_endpoint_host", table_name="api_endpoint")
    op.drop_index("ix_api_endpoint_method", table_name="api_endpoint")
    op.drop_index("ix_api_endpoint_js_asset_id", table_name="api_endpoint")
    op.drop_index("ix_api_endpoint_project_id", table_name="api_endpoint")
    op.drop_table("api_endpoint")

    op.drop_index("ix_js_asset_content_hash", table_name="js_asset")
    op.drop_index("ix_js_asset_web_asset_id", table_name="js_asset")
    op.drop_index("ix_js_asset_project_id", table_name="js_asset")
    op.drop_table("js_asset")
